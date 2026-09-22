"""Index the textbook text under every heading of the taxonomy trees.

The topic tagger matches a question against the words the book uses under
each heading, not against the heading alone: "A Lakh Varieties!" shares no
word with a question about the place value of 7 in 7,20,000, but the two pages
printed under that heading share many. So for every node of the Mathematics,
Science and Social Science trees (classes 6-10) this records the term counts
of the lines printed between that heading and the next one.

Spans. A chapter's own span is its text before its first topic; a topic's is
its text before its first subtopic; a subtopic's runs to the next subtopic or
topic. The tagger sums them back up (a topic's document is its own span plus
its subtopics'), so nothing is counted twice and nothing is stored twice.

End matter. A chapter's closing "Summary" / "What you have learnt" / "Let us
enhance our learning" / "In a nutshell" / "Keywords" restates every topic of
the chapter. Printed after the last heading, it would count as the last
topic's (or subtopic's) text and pull every question towards it, so it is
counted in the chapter's own span instead.

Where a heading's line cannot be found on the page the tree gives, the span
starts at the top of that page and the node is listed in ``unlocated`` --
counted, not hidden.

Output: ``academicos-data/syllabus/taxonomy/_node_text.json`` -- term counts,
never the text itself.

Run:  python scripts/build_taxonomy_text.py [--check] [--root DIR] [--cache DIR]

``--cache`` is a directory of the per-PDF line JSON that
``scripts/build_taxonomy.py --cache`` writes; it is only read here. A PDF with
no cached lines is read afresh.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.syllabus.tag_text import TOKENIZER_VERSION, tokens  # noqa: E402

DEFAULT_ROOT = REPO.parent / "ncert-dataset" / "textbooks"
TAXONOMY = REPO / "academicos-data" / "syllabus" / "taxonomy"
OUT = TAXONOMY / "_node_text.json"
SUBJECTS = ("Mathematics", "Science", "Social_Science")
GRADES = range(6, 11)


END_MATTER = re.compile(r"^(summary|what you have learnt|let us enhance our learning|"
                        r"in a nutshell|keywords|key words)\b", re.I)

# "2.1.2 ", "(a) ", "A. " -- printed before a heading the tree names without it
_LEADING_NUMBER = re.compile(r"^(?:\d+(?:\.\d+)*\.?|\(?[a-zA-Z]\)|[A-Z]\.)\s+")


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def load_lines(source_file: str, root: Path, cache: Path | None) -> list[dict]:
    stem = Path(source_file).stem
    if cache is not None:
        slot = cache / f"{stem}.json"
        if slot.exists():
            return json.loads(slot.read_text(encoding="utf-8"))["lines"]
    from academicos.syllabus import textbook_headings as th
    return [ln.to_dict() for ln in th.read_lines(root / source_file)]


def locate(lines: list[dict], name: str, page: int, start: int) -> int | None:
    """Index of the line a heading is printed on, at or after ``start``.

    A heading that wraps puts only its first words on the line, so a line
    matches when it and the heading share their first characters either way
    round (at least 8 of them).
    """
    key = _norm(name)
    for pg in (page, page + 1):
        for i in range(start, len(lines)):
            ln = lines[i]
            if ln["page"] != pg:
                continue
            text = ln["text"].strip()
            text = _LEADING_NUMBER.sub("", text)
            t = _norm(text)
            if len(t) < 3:
                continue
            if t.startswith(key[:24]) or (len(t) >= 8 and key.startswith(t)):
                return i
    return None


def index_tree(tree: dict, root: Path, cache: Path | None, unlocated: list) -> dict:
    nodes: dict[str, dict] = {}
    files: dict[str, list[dict]] = {}
    for ch in tree["chapters"]:
        src = ch.get("source_file")
        pages = ch.get("pages")
        if not src or not pages:
            unlocated.append({"id": ch["id"], "why": "chapter has no page range"})
            nodes[ch["id"]] = {}
            continue
        if src not in files:
            files[src] = load_lines(src, root, cache)
        lines = [ln for ln in files[src] if pages[0] <= ln["page"] <= pages[1]]
        # (line index, node id) for every heading in reading order
        marks: list[tuple[int, str]] = []
        cursor = 0
        for tp in ch["topics"]:
            for node in [tp] + tp["subtopics"]:
                at = locate(lines, node["name"], node["page"], cursor)
                if at is None:
                    at = next((i for i, ln in enumerate(lines) if ln["page"] >= node["page"]),
                              len(lines))
                    at = max(at, cursor)
                    unlocated.append({"id": node["id"], "page": node["page"]})
                marks.append((at, node["id"]))
                cursor = at
        last = marks[-1][0] if marks else 0
        end = next((i for i in range(last + 1, len(lines))
                    if len(lines[i]["text"].strip()) < 40
                    and END_MATTER.match(lines[i]["text"].strip())), len(lines))
        bounds = [0] + [m[0] for m in marks] + [end]
        owners = [ch["id"]] + [m[1] for m in marks]
        for k, owner in enumerate(owners):
            text = " ".join(ln["text"] for ln in lines[bounds[k]:bounds[k + 1]])
            if k == 0:
                text += " " + " ".join(ln["text"] for ln in lines[end:])
            nodes[owner] = dict(collections.Counter(tokens(text)).most_common())
    return nodes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--cache", type=Path, default=None)
    args = ap.parse_args()

    out: dict[str, dict] = {}
    unlocated: list = []
    for subject in SUBJECTS:
        for grade in GRADES:
            path = TAXONOMY / f"{subject}_{grade}.json"
            if not path.exists():
                continue
            tree = json.loads(path.read_text(encoding="utf-8"))
            before = len(unlocated)
            nodes = index_tree(tree, args.root, args.cache, unlocated)
            out.update(nodes)
            empty = sum(1 for v in nodes.values() if not v)
            print(f"{subject}_{grade:<3} nodes {len(nodes):4d}  unlocated "
                  f"{len(unlocated) - before:3d}  empty {empty:3d}")
    print(f"nodes {len(out)}  unlocated headings {len(unlocated)}")
    if args.check:
        return 0
    OUT.write_text(json.dumps({
        "notice": ("Term counts of the NCERT textbook lines printed under each taxonomy "
                   "heading, for the topic tagger. Counts only, no text."),
        "builtFrom": "ncert-dataset/textbooks (read-only), scripts/build_taxonomy_text.py",
        "tokenizer": TOKENIZER_VERSION,
        "unlocated": unlocated,
        "nodes": out,
    }, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
