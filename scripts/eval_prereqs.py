"""Evaluate CurriculumEstimator.vote_prerequisites against the EKG-Dataset
gold standards (ACE paper, MEKG files).

The NCERT graph has ~zero vocabulary overlap with the CS/ML/logic gold
concepts, so this harness runs the estimator on a Wikipedia corpus built
from the gold concepts' own articles (section text + internal hyperlinks) -
the same setup the Alatrash et al. paper used for its Biology evaluation.
This tests the *algorithm* (criteria + weighted voting), not the corpus.

Usage: python eval_prereqs.py [dataset_filter]
"""
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from academicos.graph.curriculum import (CRITERION_WEIGHTS, PREREQ_STOP,
                                         TEXT_SPAN_VERBS,
                                         CurriculumEstimator)
from academicos.graph.prereq_edges import confidence_from_votes
from academicos.graph.store import GraphStore

# Overridable so this doesn't depend on one machine's temp layout -- the
# EKG-Dataset gold-standard files (ACE paper MEKG files) are NOT vendored
# in this repo; point EVAL_EKG_DATASET at wherever you've fetched them.
# Default lives alongside the other vendored research datasets
# (docs/research/vendor/hipporag, .../self-rag) for consistency, though
# nothing currently populates it -- this script errors clearly on a missing
# directory rather than assuming a stale personal temp path exists.
EKG = os.environ.get('EVAL_EKG_DATASET', str(ROOT / 'docs' / 'research' / 'vendor' / 'EKG-Dataset'))
CACHE = os.environ.get('EVAL_WIKI_CACHE', str(ROOT / '.cache' / 'eval_prereqs' / 'wiki_cache.json'))
TMP = os.environ.get('EVAL_TMP', str(ROOT / '.cache' / 'eval_prereqs' / 'tmp'))
os.makedirs(TMP, exist_ok=True)
os.makedirs(os.path.dirname(CACHE), exist_ok=True)
API = 'https://en.wikipedia.org/w/api.php'
HEADERS = {'User-Agent': 'AcademicOS-eval/1.0 (research prototype)'}

# concept name (normalized) -> Wikipedia article title when the obvious
# mapping is wrong or ambiguous.
ALIASES = {
    'graph': 'Graph (discrete mathematics)',
    'tree': 'Tree (data structure)',
    'heap': 'Heap (data structure)',
    'stack': 'Stack (abstract data type)',
    'queue': 'Queue (abstract data type)',
    'recursion': 'Recursion (computer science)',
    'pointer': 'Pointer (computer programming)',
    'hash table': 'Hash table',
    'b tree': 'B-tree',
    'binary search': 'Binary search',
    'linked list': 'Linked list',
    'sorting algorithm': 'Sorting algorithm',
    'depth first search': 'Depth-first search',
    'breadth first search': 'Breadth-first search',
    'graph representation': 'Graph (discrete mathematics)',
}

_SENT_RE = re.compile(r'(?<=[.!?])\s+')


def norm_concept(s: str) -> str:
    return s.strip().lower().replace('_', ' ').replace('.txt', '')


def load_gold() -> dict[str, list[tuple[str, str, int]]]:
    # MEKG files: 'a b label'. ACE example MEKGs use first_is_prereq
    # (label 1 => a is prereq of b). DSA/metacademy use second_is_prereq
    # (label 1 => b is prereq of a) — verified via pedagogic anchors:
    # 'backpropagation gradient_descent 1' => gradient descent is prereq,
    # 'convolutional_neural_network backpropagation 1' => backprop prereq.
    # Example MEKGs verified first_is_prereq:
    # 'propositional_logic first_order_logic 1', 'random_variable multivariate_distribution 1'.
    GOLD_DIRECTION = {
        'DSA_gold_standard_MEKG.txt': 'second_is_prereq',
        'metacademy_gold_standard_MEKG.txt': 'second_is_prereq',
    }
    if not os.path.isdir(EKG):
        raise FileNotFoundError(
            f"EKG-Dataset gold standard not found at {EKG!r}. This dataset "
            "(ACE paper MEKG files) is not vendored in this repo -- fetch it "
            "and point EVAL_EKG_DATASET at its location.")
    datasets = {}
    for f in sorted(os.listdir(EKG)):
        if not f.endswith('.txt') or 'gold_standard' not in f and 'MEKG' not in f:
            continue
        path = os.path.join(EKG, f)
        head = open(path, encoding='utf-8', errors='replace').read(2000)
        sep = ';' if ';' in head else None
        pairs = []
        for line in open(path, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line:
                continue
            if sep:
                a, b, lab = (x.strip() for x in line.split(';')[:3])
            else:
                a, b, lab = line.split()
            pairs.append((norm_concept(a), norm_concept(b), int(lab)))
        if GOLD_DIRECTION.get(f) == 'second_is_prereq':
            # reinterpret label as 'a is prereq of b' convention
            pairs = [(b, a, lab) for a, b, lab in pairs]
        datasets[f] = pairs
    return datasets


# ---------- Wikipedia corpus ----------

def _strip_templates(txt: str) -> str:
    out = []
    depth = 0
    for ch in txt:
        if ch == '{':
            depth += 1
            if depth == 1:
                continue
        elif ch == '}':
            if depth:
                depth -= 1
                continue
            if depth == 0:
                continue
        if depth == 0:
            out.append(ch)
    return ''.join(out)


_LINK_RE = re.compile(r'\[\[([^\[\]|]+)(?:\|[^\[\]]*)?\]\]')
_TBL_RE = re.compile(r'^\{\|.*$', re.M)


def _clean_wikitext(wt: str) -> str:
    wt = wt.replace('{{Infobox', ' ')  # keep body
    wt = _strip_templates(wt)
    wt = re.sub(r'<!--.*?-->', ' ', wt, flags=re.S)
    wt = re.sub(r'<ref[^/]*>.*?</ref>', ' ', wt, flags=re.S)
    wt = re.sub(r'</?ref[^>]*>', ' ', wt)
    wt = re.sub(r'</?math[^>]*>.*?</math>', ' ', wt, flags=re.S)
    wt = _TBL_RE.sub(' ', wt)
    wt = re.sub(r'\[\[Category:[^\[\]]*\]\]', ' ', wt)
    wt = re.sub(r'\[\[(File|Image):[^\[\]]*\]\]', ' ', wt)
    wt = re.sub(r"'''|''", '', wt)
    wt = re.sub(r'<[^>]+>', ' ', wt)
    wt = wt.replace('&nbsp;', ' ').replace('&amp;', '&')
    return wt


def _sections(wt: str) -> list[tuple[str, str]]:
    """[(heading, text)] — sections split on == headings; intro first."""
    parts = re.split(r'(?m)^={2,6}\s*(.*?)\s*={2,6}\s*$', wt)
    out = []
    intro = parts[0].strip()
    if intro:
        out.append(('', intro))
    for i in range(1, len(parts) - 1, 2):
        heading, body = parts[i].strip(), parts[i + 1].strip()
        if body:
            out.append((heading, body))
    return out


def _internal_links(wt: str) -> list[str]:
    links = []
    for m in _LINK_RE.finditer(wt):
        target = m.group(1).split(':', 1)[-1].split('#')[0].strip().lower()
        target = target.replace('_', ' ')
        if target and not target.startswith(('file ', 'image ', 'category ', 'template ')):
            links.append(target)
    return links


def _api_get(params, tries=4):
    for attempt in range(tries):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            if r.status_code != 200:
                time.sleep(1.5 * (attempt + 1))
                continue
            return r.json()
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    return None


def resolve_and_fetch(concept: str) -> tuple[str | None, str | None]:
    """Return (article title, wikitext) for the concept's article."""
    title = ALIASES.get(concept)
    if title is None:
        data = _api_get({'action': 'query', 'list': 'search',
                         'srsearch': concept, 'srlimit': 1, 'format': 'json'})
        hits = (data or {}).get('query', {}).get('search', [])
        if not hits:
            return None, None
        title = hits[0]['title']
    data = _api_get({'action': 'parse', 'page': title, 'prop': 'wikitext',
                     'format': 'json', 'redirects': 1})
    if not data or 'error' in data:
        return None, None
    return title, data['parse']['wikitext']['*']


def build_corpus(concepts: list[str]) -> dict[str, dict]:
    """concept -> {'title', 'wt', 'links'} with disk cache."""
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding='utf-8'))
        except Exception:
            cache = {}
    need = [c for c in concepts if c not in cache]
    for c in need:
        title, wt = resolve_and_fetch(c)
        if wt is not None:
            cache[c] = {'title': title, 'wt': wt}
        time.sleep(0.3)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
    return cache


# ---------- index / graph construction ----------

def build_index(concepts, corpus) -> str:
    idx_db = os.path.join(TMP, 'index_wiki.sqlite')
    if os.path.exists(idx_db):
        os.remove(idx_db)
    conn = sqlite3.connect(idx_db)
    conn.execute("CREATE VIRTUAL TABLE chunks USING fts5("
                 "id UNINDEXED, document_id UNINDEXED, page UNINDEXED,"
                 " heading, text, tokenize = 'unicode61 remove_diacritics 2')")
    rowid = 0
    for c in concepts:
        entry = corpus.get(c) or {}
        if not entry.get('wt'):
            continue
        for page, (heading, body) in enumerate(_sections(entry['wt'])):
            text = _clean_wikitext(body)
            if len(text.strip()) < 20:
                continue
            conn.execute("INSERT INTO chunks VALUES (?,?,?,?,?)",
                         (f'{c}#{page}', c, page, heading, text))
            rowid += 1
    conn.commit()
    conn.close()
    print(f'  index: {rowid} chunks')
    return idx_db


def build_graph(concepts, corpus) -> tuple[str, list[str]]:
    """Nodes + two edge sources: text 'requires' triples (sentence order +
    TEXT_SPAN_VERBS) and Wikipedia hyperlink edges ('links')."""
    graph_db = os.path.join(TMP, 'graph_wiki.sqlite')
    if os.path.exists(graph_db):
        os.remove(graph_db)
    conn = sqlite3.connect(graph_db)
    conn.executescript("""
        CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT NOT NULL,
            label TEXT NOT NULL, attributes TEXT, status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER DEFAULT 1, valid_from TEXT, valid_until TEXT,
            provenance TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE edges (id TEXT PRIMARY KEY, source TEXT NOT NULL,
            target TEXT NOT NULL, type TEXT NOT NULL, attributes TEXT,
            weight REAL DEFAULT 1.0, status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER DEFAULT 1, valid_from TEXT, valid_until TEXT,
            provenance TEXT, created_at TEXT, updated_at TEXT);
    """)
    label_pat = {c: re.compile(r'\b' + re.escape(c) + r'\b') for c in concepts}
    resolved = [c for c in concepts if (corpus.get(c) or {}).get('wt')]
    edges = set()
    sentences: dict[tuple[str, str], list[str]] = {}

    # text triples: sentence with >= 2 concept labels and a strong verb
    for c in resolved:
        entry = corpus[c]
        for _, (heading, body) in enumerate(_sections(entry['wt'])):
            text = _clean_wikitext(body)
            for sent in _SENT_RE.split(text):
                present = [lc for lc in resolved if label_pat[lc].search(sent)]
                if len(present) < 2:
                    continue
                words = set(re.findall(r"[a-z0-9']+", sent.lower()))
                if not (words & TEXT_SPAN_VERBS):
                    continue
                pos = sorted(present, key=lambda lc: sent.lower().find(lc))
                src, tgt = pos[0], pos[1]
                edges.add((src, tgt))
                sentences.setdefault((src, tgt), []).append(sent.strip())
    # hyperlink edges: article A links to article B
    rev_title = {ALIASES[c].lower(): c for c in resolved if c in ALIASES}
    title_index = {c: c for c in resolved}
    for c in resolved:
        t_title = (corpus[c].get('title') or '').lower()
        if t_title:
            title_index.setdefault(t_title, c)
        for t in _internal_links(corpus[c]['wt']):
            tgt = title_index.get(t) or rev_title.get(t)
            if tgt and tgt != c:
                edges.add((c, tgt))
                sentences.setdefault((c, tgt), [])
    for c in resolved:
        conn.execute("INSERT INTO nodes (id, type, label) VALUES (?,?,?)",
                     (f'wiki:concept:{c}', 'Concept', c))
    for (src, tgt) in edges:
        attrs = {'predicates': ['requires']} if sentences.get((src, tgt)) else {'predicates': ['links']}
        prov = {'span_text': '; '.join(sentences[(src, tgt)][:2])} if sentences.get((src, tgt)) else None
        conn.execute("INSERT INTO edges (id, source, target, type, attributes, provenance)"
                     " VALUES (?,?,?,?,?,?)",
                     (f'{src}->{tgt}', f'wiki:concept:{src}', f'wiki:concept:{tgt}',
                      'RELATED_TO', json.dumps(attrs), json.dumps(prov) if prov else None))
    conn.commit()
    conn.close()
    print(f'  graph: {len(resolved)} nodes, {len(edges)} edges')
    return graph_db, resolved


# ---------- evaluation ----------

def _auc(pairs):
    """pairs: list of (score, gold_label). AUC via rank sum."""
    if not pairs:
        return 0.0
    pos = [(s, 1) for s, g in pairs if g == 1]
    neg = [(s, 0) for s, g in pairs if g == 0]
    if not pos or not neg:
        return 0.0
    ranks = sorted([(s, g) for s, g in pairs], key=lambda x: x[0])
    total_rank = 0.0
    n = len(ranks)
    for i, (_, g) in enumerate(ranks):
        if g == 1:
            total_rank += i + 1
    auc = (total_rank - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    return auc


def evaluate(dataset_name, gold_pairs, theta=0.28):
    concepts = sorted({a for a, _, _ in gold_pairs} | {b for _, b, _ in gold_pairs})
    print(f'\n=== {dataset_name}: {len(concepts)} concepts, {len(gold_pairs)} pairs')
    corpus = build_corpus(concepts)
    resolved = [c for c in concepts if (corpus.get(c) or {}).get('wt')]
    unresolved = [c for c in concepts if not (corpus.get(c) or {}).get('wt')]
    if unresolved:
        print(f'  unresolved: {unresolved}')
    if len(resolved) < 3:
        print('  too few resolved concepts; skipping')
        return None

    idx_db = build_index(resolved, corpus)
    graph_db, resolved = build_graph(resolved, corpus)
    est = CurriculumEstimator(idx_db)
    store = GraphStore(Path(graph_db))

    # gold pair matrix restricted to resolved concepts
    res_set = set(resolved)
    gold = {(a, b): lab for a, b, lab in gold_pairs if a in res_set and b in res_set and a != b}
    if not gold:
        print('  no evaluable pairs')
        return None
    n_pos = sum(1 for v in gold.values() if v == 1)

    variants = {
        'full5': {'criteria': ('TemO', 'CMH', 'IOLR', 'BERTropy', 'Text')},
        'full6': {'criteria': ('TemO', 'CMH', 'IOLR', 'BERTropy', 'Text', 'HL-A')},
        'iolr+text': {'criteria': ('IOLR', 'Text')},
        'iolr+text+HL-A': {'criteria': ('IOLR', 'Text', 'HL-A')},
    }
    for vname, vk in variants.items():
        # harvest scores for every pair that received any vote
        vlog: list = []
        est.vote_prerequisites(resolved, graph=store, theta=1.01, min_criteria=1,
                               min_cooccur=1, prereq_candidates=None,
                               strong_criteria=('IOLR', 'Text'), iolr_all_edges=True,
                               criteria=vk['criteria'], vote_log=vlog)
        scored = {}
        for a, b, votes, s in vlog:
            if s is None or not votes:
                continue
            va = sum(CRITERION_WEIGHTS[c] for c, v in votes.items() if v > 0)
            vb = sum(CRITERION_WEIGHTS[c] for c, v in votes.items() if v < 0)
            active_weight = sum(CRITERION_WEIGHTS[c] for c in vk['criteria'])
            conf = confidence_from_votes(va, vb, active_weight)
            if (a, b) in gold:
                scored[(a, b)] = (votes, s, conf)
            if (b, a) in gold:
                scored[(b, a)] = ({c: -v for c, v in votes.items()}, -s, conf)
        print(f'  [{vname}] pairs with votes: {len(scored)} / {len(gold)}')

        for cn in vk['criteria'] + ('combined', 'confidence'):
            auc_pairs = []
            for (a, b), (votes, s, conf) in scored.items():
                sc = s if cn == 'combined' else conf if cn == 'confidence' else votes.get(cn)
                if sc is not None:
                    auc_pairs.append((sc, gold[(a, b)]))
            print(f'  AUC[{cn:9s}] = {_auc(auc_pairs):.3f}   (n={len(auc_pairs)})')

        # thresholded strong-set mirrors production defaults: variants that
        # include HL-A may be unlocked by it (prod default strong tuple).
        strong = ('IOLR', 'Text', 'HL-A') if 'HL-A' in vk['criteria'] else ('IOLR', 'Text')
        results = []
        for t in (0.18, 0.28, 0.40):
            pred = est.vote_prerequisites(
                resolved, graph=store, theta=t, min_criteria=2, min_cooccur=1,
                prereq_candidates=None, strong_criteria=strong,
                iolr_all_edges=True, criteria=vk['criteria'])
            edges = {(p, l) for l, lst in pred.items() for p, _, _ in lst}
            tp = sum(1 for e in edges if gold.get(e) == 1)
            p = tp / len(edges) if edges else 0.0
            r = tp / n_pos if n_pos else 0.0
            f1 = 2 * p * r / (p + r) if p + r else 0.0
            corr = sum(1 for e in gold if e not in edges and gold[e] == 0)
            acc = (tp + corr) / len(gold)
            results.append((t, len(edges), p, r, f1, acc))
            print(f'  theta={t:.2f}: edges={len(edges):4d}  P={p:.3f}  R={r:.3f}  '
                  f'F1={f1:.3f}  acc={acc:.3f}')
            # confidence re-rank on the same predicted edges: does the
            # participation-weighted margin separate hits from false alarms?
            scored_pairs = {(a, b): conf for (a, b), (_, _, conf) in scored.items()}
            for ct in (0.30, 0.40, 0.50):
                conf_edges = [e for e in edges if scored_pairs.get(e, 0.0) >= ct]
                ctp = sum(1 for e in conf_edges if gold.get(e) == 1)
                cp = ctp / len(conf_edges) if conf_edges else 0.0
                cr = ctp / n_pos if n_pos else 0.0
                cf1 = 2 * cp * cr / (cp + cr) if cp + cr else 0.0
                print(f'      conf>={ct:.2f}: edges={len(conf_edges):4d}  '
                      f'P={cp:.3f}  R={cr:.3f}  F1={cf1:.3f}')
    est.close()
    store.close()
    return results


if __name__ == '__main__':
    datasets = load_gold()
    filt = sys.argv[1] if len(sys.argv) > 1 else None
    for name, pairs in datasets.items():
        if filt and filt.lower() not in name.lower():
            continue
        evaluate(name, pairs)
    print('\ndone')
