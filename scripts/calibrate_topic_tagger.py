"""Fit the topic tagger's confidence model and pick its thresholds on the gold set.

The tagger's raw scores are cosine similarities; they say which node is best,
not how likely the best is right. This turns them into a probability per level
(a logistic model on best score, margin over the runner-up, whether there
was a runner-up, and for the chapter how well the whole Exemplar chapter --
or the pooled existing chapterIds -- matched it, and which of the two the
prior came from), and picks for each level the lowest confidence whose
accepted tags are at least SELECT_AT (93%) right -- a tag below it goes to
the review queue, not onto the question.

Why 93% and not the 90% bar. The thresholds are chosen on OUT-OF-FOLD
confidences (5 folds, seed 703): each gold item's confidence comes from a model
that never saw it. That makes the confidences honest, not the choice of cut:
scanning every cut and keeping the one that accepts the most tags while still
at 90% lands on the boundary by construction, and measured on the same numbers
it reads 90% whatever the truth is. Nested cross-validation showed it: with
each fold's cuts chosen on the other four folds alone, the 90% rule scored
138/154 = 0.896 on chapters. Choosing at 93% leaves the margin that selection
eats. The heuristic constants in the tagger were tuned on this gold set too,
which no refolding undoes; ``_tag_audit.json`` (subtopic) and
``_tag_audit_chapter_topic.json`` are held-out checks of the written tags.

What to quote. The NESTED estimate (``gold.nested``): each fold's cuts chosen
on the other folds (their own out-of-fold confidences, 4 inner folds), then
scored on the fold with a model that never saw it -- it measures the whole
procedure, choice of cut included -- with its Wilson 95% lower bound. The
out-of-fold numbers at the chosen cuts are >= 93% by construction and say
little. The model that is written is refitted on every item, and its in-sample
numbers are written alongside -- they are what `tests/test_topic_tagger.py`
re-measures, and they flatter the tagger most.

Gold: ``academicos-data/syllabus/taxonomy/_tag_gold.json`` (labelled by an AI
reviewer, not a teacher): 328 questions drawn at random, counted at every
level, and 61 audit items drawn from the subtopic tags the tagger wrote,
counted at the subtopic level only (``levels``). The audit was added because
the random sample held too few accepted subtopics (11/12 right) to measure
them, and the tags it let through were 24/30 and 34/40 right when checked.
``_tag_audit.json`` is a further, held-out check of the written tags; nothing
here reads it.

Run:  python scripts/calibrate_topic_tagger.py [--check]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.syllabus import tagger as tg  # noqa: E402

TAXONOMY = REPO / "academicos-data" / "syllabus" / "taxonomy"
GOLD = TAXONOMY / "_tag_gold.json"
OUT = TAXONOMY / "_tagger_model.json"
BANKS = {
    "exemplar": REPO / "academicos-data" / "corpus" / "ncert-exemplar" / "questions.json",
    "cbe": REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    "board": REPO / "academicos-data" / "syllabus" / "questions.json",
}
TARGET = 0.90          # the bar an accepted tag must clear
SELECT_AT = 0.93       # the precision a threshold is chosen at: TARGET plus a margin
# A threshold must be shown on at least this many accepted gold tags. Without
# it the subtopic level "passed" on 1 or 2 out-of-fold tags -- a 100% that
# says nothing -- and would have accepted subtopics across the bank on that.
MIN_SUPPORT = 10
FOLDS = 5
SEED = 703
L2 = 1.0


def fit_logistic(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """L2-regularised logistic regression by Newton's method, returned as
    weights on the RAW features (bias first).

    The features are standardised before fitting and the weights mapped back:
    cosine scores and margins live around 0.01-0.3, and an L2 penalty on the
    raw scale shrank the margin -- on the gold set the single best separator of
    right from wrong topics -- almost to nothing."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    A = np.hstack([np.ones((len(Z), 1)), Z])
    w = np.zeros(A.shape[1])
    reg = np.full(A.shape[1], L2)
    reg[0] = 0.0
    for _ in range(100):
        p = 1.0 / (1.0 + np.exp(-A @ w))
        grad = A.T @ (p - y) + reg * w
        H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(reg) + 1e-9 * np.eye(A.shape[1])
        step = np.linalg.solve(H, grad)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    raw = w[1:] / sd
    return np.concatenate([[w[0] - float(raw @ mu)], raw])


FEATURES = {"chapter": ("best", "margin", "heading", "prior", "hasPrior", "idPrior"),
            "topic": ("best", "margin", "heading", "single"),
            # no "single": the topic-level candidate means a subtopic always
            # has a runner-up, so the feature is constant
            "subtopic": ("best", "margin", "heading")}


def as_coef(level: str, w: np.ndarray) -> dict:
    return {"bias": float(w[0]), **{k: float(x) for k, x in zip(FEATURES[level], w[1:])}}


def row(level: str, f: dict) -> list[float]:
    return [float(f[k]) for k in FEATURES[level]]


def training_sets(rows: list[dict]) -> dict:
    """Per level, (index into rows, features, right?) -- a level is trained only
    on items whose levels above it were right, since its probability is
    conditional on them."""
    sets = {lv: [] for lv in tg.LEVELS}
    for i, r in enumerate(rows):
        tag, j = r["tag"], r["judged"]
        levels = tg.gold_levels(r["item"])
        if "chapter" in levels:
            sets["chapter"].append((i, row("chapter", tag.features["chapter"]), j["chapter"]))
        if "topic" in levels and j["chapter"] and tag.features["topic"] is not None:
            sets["topic"].append((i, row("topic", tag.features["topic"]), j["topic"]))
        if j["topic"] and tag.features["subtopic"] is not None:
            sets["subtopic"].append((i, row("subtopic", tag.features["subtopic"]), j["subtopics"][0]))
    return sets


def fit_all(sets: dict, keep=None) -> dict:
    coef = {}
    for lv, data in sets.items():
        data = [d for d in data if keep is None or d[0] in keep]
        X = np.array([d[1] for d in data], dtype=float)
        y = np.array([1.0 if d[2] else 0.0 for d in data])
        coef[lv] = as_coef(lv, fit_logistic(X, y))
    return coef


def confidences(tag: tg.TagResult, coef: dict) -> dict:
    conf, running = {}, 1.0
    for lv in tg.LEVELS:
        if tag.features[lv] is None:
            conf[lv] = None
            continue
        running *= tg.level_probability(coef[lv], tag.features[lv])
        conf[lv] = running
    return conf


def wilson_lower(right: int, n: int, z: float = 1.96) -> float:
    """Wilson score lower bound (95% by default) of a precision right/n."""
    if n == 0:
        return 0.0
    p = right / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - spread) / (1 + z * z / n)


def _counted(rows: list[dict], i: int, lv: str) -> tuple[int, int]:
    """(right, tags) that gold row i adds at level lv when accepted there."""
    if lv not in tg.gold_levels(rows[i]["item"]):
        return 0, 0
    j = rows[i]["judged"]
    if lv == "subtopic":
        return sum(j["subtopics"]), len(j["subtopics"])
    return int(j[lv]), 1


def pick_thresholds(rows: list[dict], conf: list[dict], idx=None,
                    select_at: float = SELECT_AT) -> tuple[dict, dict]:
    """Lowest threshold per level whose accepted tags are >= ``select_at``
    (SELECT_AT, not the TARGET bar: see the module docstring) right on at
    least MIN_SUPPORT tags of the rows ``idx`` (default all), level by level (a topic can only be accepted under
    an accepted chapter). A gold item counts only at its `tg.gold_levels`; a
    subtopic-only audit item still has to clear the chapter and topic
    thresholds to be counted at the subtopic. A level where no threshold does gets 1.01: nothing
    at that level is accepted, everything goes to review."""
    thresholds, measured = {}, {}
    alive = set(range(len(rows)) if idx is None else idx)
    for lv in tg.LEVELS:
        cands = sorted({conf[i][lv] for i in alive if conf[i][lv] is not None}, reverse=True)
        best = (1.01, 0, 0)
        for t in cands:
            right = tags = 0
            for i in alive:
                c = conf[i][lv]
                if c is None or c < t:
                    continue
                r, n = _counted(rows, i, lv)
                right += r
                tags += n
            if tags >= MIN_SUPPORT and right / tags >= select_at and tags >= best[2]:
                best = (t, right, tags)
        thresholds[lv] = round(best[0] - 1e-9, 6) if best[2] else 1.01
        measured[lv] = {"right": best[1], "tags": best[2],
                        "precision": round(best[1] / best[2], 4) if best[2] else None}
        alive = {i for i in alive if conf[i][lv] is not None and conf[i][lv] >= thresholds[lv]}
    return thresholds, measured


def score_thresholds(rows: list[dict], conf: list[dict], idx, thresholds: dict) -> dict:
    """[right, tags] per level of the rows ``idx`` accepted under ``thresholds``,
    level by level as `pick_thresholds` counts them."""
    out = {lv: [0, 0] for lv in tg.LEVELS}
    alive = set(idx)
    for lv in tg.LEVELS:
        alive = {i for i in alive if conf[i][lv] is not None and conf[i][lv] >= thresholds[lv]}
        for i in alive:
            r, n = _counted(rows, i, lv)
            out[lv][0] += r
            out[lv][1] += n
    return out


def nested_estimate(rows: list[dict], sets: dict, folds: list[set], oof: list[dict]) -> dict:
    """Precision of the whole procedure -- the choice of cut included -- per level.

    For each outer fold: the other folds get confidences from models fitted
    without each of them in turn (the 4 other folds are the inner folds), the
    cuts are chosen on those alone, and they are applied to the outer fold's
    out-of-fold confidences. The outer folds' counts are pooled."""
    everything = set(range(len(rows)))
    total = {lv: [0, 0] for lv in tg.LEVELS}
    for k, held in enumerate(folds):
        train = everything - held
        inner: list[dict] = [None] * len(rows)
        for j, fold in enumerate(folds):
            if j == k:
                continue
            coef = fit_all(sets, keep=train - fold)
            for i in fold:
                inner[i] = confidences(rows[i]["tag"], coef)
        cuts, _ = pick_thresholds(rows, inner, idx=train)
        for lv, (r, n) in score_thresholds(rows, oof, held, cuts).items():
            total[lv][0] += r
            total[lv][1] += n
    return {lv: {"right": r, "tags": n, "precision": round(r / n, 4) if n else None,
                 "wilsonLower95": round(wilson_lower(r, n), 4)}
            for lv, (r, n) in total.items()}


def make_folds(rows: list[dict]) -> list[set]:
    """Seeded folds, dealt separately to the random sample (batches 1-2) and
    to the subtopic-only audit items (batch 3): adding audit items then leaves
    the random sample's folds, and so its chapter and topic estimates, as they
    were."""
    folds = [set() for _ in range(FOLDS)]
    for full in (True, False):
        order = [i for i, r in enumerate(rows)
                 if (tuple(tg.gold_levels(r["item"])) == tg.LEVELS) == full]
        random.Random(SEED).shuffle(order)
        for k in range(FOLDS):
            folds[k].update(order[k::FOLDS])
    return folds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args(argv)

    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    items = gold["items"]
    banks = {k: json.loads(p.read_text(encoding="utf-8"))["questions"] for k, p in BANKS.items()}
    raw_tagger = tg.TopicTagger(model={}, thresholds={})
    wanted = {it["id"] for it in items}
    tags = {}
    for name, records in banks.items():
        for rec, tag in zip(records, raw_tagger.tag_records(records)):
            if rec.get("id") in wanted and tag is not None:
                tags[rec["id"]] = tag
    rows = [{"item": it, "tag": tags[it["id"]], "judged": tg.judge(tags[it["id"]], it)}
            for it in items]
    sets = training_sets(rows)

    # out-of-fold confidences
    folds = make_folds(rows)
    oof: list[dict] = [None] * len(rows)
    for k, held in enumerate(folds):
        coef = fit_all(sets, keep=set(range(len(rows))) - held)
        for i in held:
            oof[i] = confidences(rows[i]["tag"], coef)
    thresholds, oof_measured = pick_thresholds(rows, oof)
    nested = nested_estimate(rows, sets, folds, oof)

    final = fit_all(sets)
    model = {"method": tg.TAG_METHOD,
             "features": {lv: list(f) for lv, f in FEATURES.items()},
             "coefficients": final, "thresholds": thresholds}
    tagger = tg.TopicTagger(model=model)
    in_sample = tg.score_against_gold(tagger, items, banks)

    # conditional accuracy of the raw picks, for the report
    cond = {}
    for lv in tg.LEVELS:
        data = sets[lv]
        cond[lv] = {"right": sum(1 for d in data if d[2]), "of": len(data)}

    print(f"gold items {len(items)}  (labelled by an AI reviewer, not a teacher)")
    for lv in tg.LEVELS:
        r = in_sample["raw"][lv]
        print(f"raw {lv:9s} end-to-end {r['right']:3d}/{r['of']:3d}  "
              f"given the level above right {cond[lv]['right']:3d}/{cond[lv]['of']:3d}")
    print(f"thresholds chosen at {SELECT_AT} out-of-fold; the bar is {TARGET}")
    for lv in tg.LEVELS:
        n, o, s = nested[lv], oof_measured[lv], in_sample["accepted"][lv]
        print(f"accepted {lv:9s} threshold {thresholds[lv]:.4f}  nested "
              f"{n['right']}/{n['tags']} = {n['precision']} (Wilson 95% lower "
              f"{n['wilsonLower95']})  out-of-fold {o['right']}/{o['tags']} = "
              f"{o['precision']}  in-sample {s['right']}/{s['tags']} = {s['precision']}")
    bad = [lv for lv in tg.LEVELS
           if (in_sample["accepted"][lv]["tags"] and in_sample["accepted"][lv]["precision"] < TARGET)
           or (nested[lv]["tags"] and nested[lv]["precision"] < TARGET)]
    for lv in tg.LEVELS:
        if thresholds[lv] > 1:
            print(f"{lv}: no threshold reaches {SELECT_AT} on {MIN_SUPPORT}+ gold tags -- "
                  f"nothing is accepted at this level")
    if bad:
        print(f"in-sample or nested precision below {TARGET} at {bad}: refusing to write",
              file=sys.stderr)
        return 3
    if args.check:
        return 0
    OUT.write_text(json.dumps({
        "notice": ("Confidence model and thresholds of academicos.syllabus.tagger, fitted by "
                   "scripts/calibrate_topic_tagger.py on _tag_gold.json (AI-reviewer labels, "
                   "not a teacher's). Thresholds are chosen at selectAt out-of-fold, a "
                   "margin over the target bar. Quote the nested numbers (the choice of cut "
                   "included); outOfFold is >= selectAt by construction; inSample flatters."),
        "method": tg.TAG_METHOD,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "target": TARGET,
        "selectAt": SELECT_AT,
        "minSupport": MIN_SUPPORT,
        "features": {lv: list(f) for lv, f in FEATURES.items()},
        "coefficients": final,
        "thresholds": thresholds,
        "trainedOn": {lv: {"items": len(sets[lv]), "right": cond[lv]["right"]}
                      for lv in tg.LEVELS},
        "gold": {"items": len(items), "folds": FOLDS, "seed": SEED,
                 "nested": {"accepted": nested},
                 "outOfFold": {"accepted": oof_measured},
                 "inSample": in_sample},
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
