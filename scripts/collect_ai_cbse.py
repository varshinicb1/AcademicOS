"""Pull the worker's raw completions from R2, validate them, and write a bank.

The worker only generates. It stores what came back and stops; the judgement is
here, in Python, where the validator has tests -- because the failures that matter
(false premise, distractor ladder, a stem naming its own source) are exactly the
ones a worker that silently dropped would never surface.

Run:  python scripts/collect_ai_cbse.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from academicos.corpus import cbse_blueprint as bp     # noqa: E402
from academicos.corpus import cbse_generate as cg      # noqa: E402

BUCKET = "academicos-qgen"
DEFAULT_OUT = ROOT / "academicos-data" / "corpus" / "ai-cbse" / "questions.json"
WORKTREE_TMP = Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\qgen-raw")


def _wrangler() -> list[str]:
    """How to invoke wrangler on this machine.

    `wrangler` is an npm shim: a `.cmd` and a shell script, neither of which
    `subprocess` will exec by bare name on Windows. Resolving the `.cmd` once here
    is cheaper than discovering it inside a traceback.
    """
    if sys.platform == "win32":
        for name in ("wrangler.cmd", "npx.cmd"):
            found = shutil.which(name)
            if found:
                return [found] + (["-y", "wrangler"] if name == "npx.cmd" else [])
    return [shutil.which("wrangler") or "wrangler"]


WRANGLER = _wrangler()


def _run_wrangler(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    # wrangler writes UTF-8 (box-drawing characters in its own banners, and
    # Devanagari if an object name ever carries it). Without this, decoding
    # cp1252 raises UnicodeDecodeError in a reader thread and the run dies with
    # a traceback that says nothing about the real problem.
    return subprocess.run(WRANGLER + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          cwd=str(ROOT), timeout=timeout)


def fetch_raw(dest: Path, manifest: Path) -> list[str]:
    """Fetch every stored completion named by the manifest. Free; no AI call.

    The keys come from the local manifest rather than from `r2 object list`,
    because wrangler has no such subcommand -- it offers only get, put and
    delete. The manifest is the same file the worker reads, so it is the
    authoritative list of what was asked for, and comparing the count that comes
    back against the count that went out is how a silently missing object gets
    noticed.
    """
    dest.mkdir(parents=True, exist_ok=True)
    entries = json.loads(manifest.read_text(encoding="utf-8")).get("entries") or []
    keys = [e["raw"] for e in entries if e.get("raw")]
    missing: list[str] = []
    for key in keys:
        local = dest / Path(key).name
        if not local.is_file():
            _run_wrangler(["r2", "object", "get", f"{BUCKET}/{key}",
                           f"--file={local}", "--remote"], timeout=300)
        if not local.is_file():
            missing.append(key)
    if missing:
        print(f"warning: {len(missing)} of {len(keys)} objects did not come back, "
              f"starting with {missing[0]}")
    return sorted(dest.glob("*.json"))


CORPUS = ROOT / "academicos-data" / "corpus"


def _tokens(text: str) -> frozenset[str]:
    """A question's content words, for spotting one that says the same thing as
    another in different words."""
    import re
    import unicodedata

    s = unicodedata.normalize("NFKC", str(text or "")).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return frozenset(w for w in s.split() if len(w) > 2 and w not in STOPWORDS)


STOPWORDS = frozenset("""
the a an and or of to in is are was were be been for with from by on at as
that this these those it its his her their our your my what which who whom whose
find state write show prove that_ given also into than then when where how why
""".split())


def load_existing(threshold: float = 0.72) -> tuple[list[frozenset[str]], int]:
    """Content words of every question already in the bank, across all corpora.

    Generating a question the bank already holds is not a free repeat: it spends a
    daily neuron, it counts against the quota the whole run is rationed by, and it
    dilutes the one thing a paid bank is for. The existing corpora are around 9,300
    questions, so the overlap is not theoretical.

    Compared on content-word sets with a Jaccard threshold rather than on exact
    stems, because "the HCF of 12, 15 and 20" and "Find the HCF of 12, 15 and 20"
    are the same question with a different opening word.
    """
    import re
    import unicodedata

    seen: list[frozenset[str]] = []
    total = 0
    for path in sorted(CORPUS.glob("*/questions.json")):
        if path.name == "questions.json" and path.parent.name == "ai-cbse":
            continue
        try:
            questions = json.loads(path.read_text(encoding="utf-8")).get("questions") or []
        except (OSError, ValueError):
            continue
        for question in questions:
            stem = (question.get("stem") or question.get("content", {}).get("question_text")
                    or "")
            words = _tokens(stem)
            if len(words) >= 3:
                seen.append(words)
                total += 1
    return seen, total


def _is_duplicate(words: frozenset[str], seen: list[frozenset[str]],
                  threshold: float = 0.72) -> bool:
    if not words:
        return False
    # A cheap length filter first: two sets within 20% of each other in size cannot
    # clear the threshold, so most comparisons stop without building a union.
    for other in seen:
        if abs(len(other) - len(words)) > len(words) * (1 - threshold) / threshold:
            continue
        union = len(words | other)
        if union and len(words & other) / union >= threshold:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--manifest", type=Path,
                    default=Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\cbse-jobs\manifest.json"))
    ap.add_argument("--threshold", type=float, default=0.72,
                    help="Jaccard overlap above which a question counts as a repeat")
    ap.add_argument("--keep", action="store_true",
                    help="keep refusals, do not print the first question")
    args = ap.parse_args()

    paths = fetch_raw(WORKTREE_TMP, args.manifest)
    if not paths:
        print("no raw completions found in R2; run the worker first")
        return 2

    # The worker stores a completion and the job's shape -- code, chapter, section,
    # type, marks -- but not the subject, grade or chapter id, because it never
    # needed them. Those live in the prompt objects, which are on this disk, so the
    # two are joined on the file name. Without the join every record would carry
    # subject "?" and an empty chapterIds, and nothing downstream could resolve a
    # single one of them.
    existing, existing_total = load_existing()
    manifest = args.manifest
    prompts: dict[str, dict] = {}
    prompt_dir = manifest.parent / "prompts"
    for path in sorted(prompt_dir.glob("*.json")):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        prompts[path.stem] = job

    kept: list[dict] = []
    refused: list[dict] = []
    unreadable = 0
    unjoined = 0
    duplicates = 0
    models: dict[str, int] = {}

    for path in paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            unreadable += 1
            continue
        models[raw.get("model") or "?"] = models.get(raw.get("model") or "?", 0) + 1
        job = prompts.get(path.stem)
        if not job:
            unjoined += 1
            refused.append({"file": path.name, "reason": "no-prompt-for-result"})
            continue
        meta = dict(job)
        meta.update({k: raw[k] for k in ("model", "neurons", "ok") if k in raw})
        qtype = meta.get("qtype")
        marks = meta.get("marks")

        # Rebuild the section the job was for from the blueprint, so the marks and
        # type are checked against the paper rather than against the request.
        section = None
        for candidate in bp.for_paper(meta.get("subject") or "Mathematics",
                                      int(meta.get("grade") or 10)).sections:
            if candidate.qtype == qtype and candidate.marks == marks:
                section = candidate
                break
        if section is None:
            refused.append({"file": path.name, "reason": "no-section-for-type-marks",
                            "qtype": qtype, "marks": marks})
            continue

        payload = raw.get("raw")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError:
                payload = None
        if meta.get("schemaError"):
            refused.append({"file": path.name, "reason": "schema-not-met",
                            "detail": meta["schemaError"]})
            continue
        if not isinstance(payload, dict):
            refused.append({"file": path.name, "reason": "unreadable-response"})
            continue

        for item in payload.get("questions") or []:
            item = cg.parse_item(item)
            reason = cg.validate(item, section)
            if reason:
                refused.append({"file": path.name, "reason": reason,
                                "section": section.key, "qtype": section.qtype,
                                "stem": (item.get("stem") or "")[:140]})
                continue
            if _is_duplicate(_tokens(item.get("stem") or ""), existing,
                             args.threshold):
                duplicates += 1
                refused.append({"file": path.name, "reason": "already-in-bank",
                                "stem": (item.get("stem") or "")[:140]})
                continue
            kept.append(cg.to_record(
                item, section, _stub(meta), meta.get("topic") or "",
                chapter_id=meta.get("chapterId") or "",
                topic_id="", model=meta.get("model", "?")))

    # Ids must be unique or the merge dedupes real questions against each other.
    # The model supplies the position within a call and two sections of the same
    # chapter both return position 1, so the id is rebuilt from the file name and
    # the item's index within that file -- both of which are ours, not the model's.
    seen: set[str] = set()
    for index, record in enumerate(kept):
        base = record["id"]
        if base in seen:
            base = f"{base}-{index}"
        seen.add(base)
        record["id"] = base

    keys = cg.audit_key_distribution(kept)
    rebalanced = cg.rebalance_keys(kept)
    # Ids must be unique or the merge dedupes real questions against each other.
    # The model supplies the position within a call and two sections of the same
    # chapter both return position 1, so the id is rebuilt from the file name and
    # the item's index within that file -- both of which are ours, not the model's.
    seen: set[str] = set()
    for index, record in enumerate(kept):
        base = record["id"]
        if base in seen:
            base = f"{base}-{index}"
        seen.add(base)
        record["id"] = base

    keys = cg.audit_key_distribution(kept)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    dupes = len(kept) - len(seen)
    args.out.write_text(json.dumps(
        {"questions": kept, "refusals": refused,
         "meta": {"source": f"cloudflare workers ai ({BUCKET})",
                  "models": models, "keyDistribution": keys,
                  "keyRebalanced": rebalanced,
                  "completions": len(paths)}},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by_section: dict[str, int] = {}
    for q in kept:
        key = q["provenance"]["section"]
        by_section[key] = by_section.get(key, 0) + 1

    print(f"pulled {len(paths)} completions ({unreadable} unreadable, "
          f"{unjoined} unjoined)")
    print(f"checked against {existing_total} existing questions")
    print(f"kept {len(kept)}, refused {len(refused)} "
          f"({duplicates} already in the bank)")
    print("by section: " + (", ".join(f"{k} {v}" for k, v in sorted(by_section.items()))
                            or "none"))
    print(f"models: {models}")
    if rebalanced["rotated"]:
        print(f"key rebalanced: rotated {rebalanced['rotated']} of "
              f"{rebalanced['mcqs']} MCQs")
    if keys["total"]:
        spread = "  ".join(f"{k} {keys['counts'][k]}" for k in sorted(keys["counts"]))
        print(f"key position: {spread}" + ("   <- STILL BIASED" if keys["biased"] else ""))
    if refused:
        reasons: dict[str, int] = {}
        for r in refused:
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
        print("refusals: " + ", ".join(f"{v} {k}" for k, v in
                                       sorted(reasons.items(), key=lambda kv: -kv[1])))
    print(f"wrote {args.out} ({dupes} ids made unique)")
    if kept and not args.keep:
        print("\nfirst question:")
        print(json.dumps(kept[0], ensure_ascii=False, indent=2)[:700])
    return 0


def _stub(raw: dict):
    """The little of `Chapter` that `to_record` actually reads."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _C:
        book_code: str
        subject: str
        grade: int
        language: str
        number: int
        title: str
        pages: tuple

        @property
        def page_numbers(self):
            return tuple(range(1, 1 + len(self.pages)))

    pages = tuple((1, "x") for _ in range(1))
    return _C(book_code=raw.get("code", "?"), subject=raw.get("subject", "?"),
              grade=raw.get("grade", 0), language=raw.get("language", "en"),
              number=raw.get("chapter", 0),
              title=raw.get("chapterName", ""), pages=pages)


if __name__ == "__main__":
    raise SystemExit(main())
