"""Compare the new pack against the live one before overwriting anything.

The 38 rewritten chapters should have dropped from 955 decoded chunks to 884
ocr-vision-cleaned chunks, because narration was 19.8% of their characters and
the Hindi narration was also pulling Devanagari into the six English books. The
other 534 chapters must be byte-identical, so any difference outside the 38 is a
regression in the chunker or an accidental corpus edit and must stop the upload.
"""
import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OLD = Path(r"D:\wt\tagfix\corpus_build\chunks.jsonl.gz")
NEW = Path(r"D:\wt\tagfix\corpus_build\chunks.new.jsonl.gz")
MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
REWRITTEN = {m["label"] for m in json.loads(MANIFEST.read_text(encoding="utf-8"))}


def load(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def embed_text(rec: dict) -> str:
    """The text that is actually embedded, so content changes are visible."""
    return "\n".join(str(rec.get(k) or "") for k in ("heading_path", "text"))


def main() -> None:
    old = load(OLD)
    new = load(NEW)
    print(f"old chunks: {len(old)}")
    print(f"new chunks: {len(new)}")
    print(f"delta     : {len(new) - len(old):+d}")

    old_by = defaultdict(list)
    new_by = defaultdict(list)
    for r in old:
        old_by[r["chapter_id"]].append(r)
    for r in new:
        new_by[r["chapter_id"]].append(r)

    all_ch = set(old_by) | set(new_by)
    changed, unexpected = [], []
    for ch in sorted(all_ch):
        o, n = old_by.get(ch, []), new_by.get(ch, [])
        if len(o) != len(n) or [embed_text(x) for x in o] != [embed_text(x) for x in n]:
            changed.append((ch, len(o), len(n)))
            if ch not in REWRITTEN:
                unexpected.append(ch)

    print(f"\nchapters with changed content: {len(changed)}")
    for ch, a, b in changed:
        tag = "" if ch in REWRITTEN else "   <-- UNEXPECTED"
        print(f"  {ch:<14} {a:>3} -> {b:>3}{tag}")

    if unexpected:
        print(f"\nFAIL: {len(unexpected)} chapter(s) changed but were not rewritten")
        return

    # Confirm every rewritten chapter is now marked ocr-vision-cleaned and that
    # the six English books no longer carry the Hindi narration.
    print("\nrewritten chapter quality/language check:")
    for ch in sorted(REWRITTEN):
        recs = new_by.get(ch, [])
        if not recs:
            print(f"  {ch:<14} MISSING FROM NEW PACK")
            continue
        q = {r.get("text_quality") for r in recs}
        lang = {r.get("language") for r in recs}
        quote = {r.get("quote_exact") for r in recs}
        print(f"  {ch:<14} chunks={len(recs):>3} quality={sorted(q)} "
              f"lang={sorted(lang)} quote_exact={sorted(quote)}")

    # Any leftover Vision narration in the new pack would now be embedded and
    # retrievable, so check the text directly.
    NARRATION = re.compile(
        r"(this\s+(?:image|picture|diagram)\s+(?:contains|shows|depicts)"
        r"|यह\s+(?:चित्र|छवि|तस्वीर)\s+(?:एक|दो))", re.I)
    leaks = defaultdict(int)
    for r in new:
        if NARRATION.search(r.get("text") or ""):
            leaks[r["chapter_id"]] += 1
    print(f"\nnarration leaks in new pack: {sum(leaks.values())} across "
          f"{len(leaks)} chapters")
    for ch, n in sorted(leaks.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {ch:<14} {n}")

    digest = hashlib.sha256(NEW.read_bytes()).hexdigest().upper()
    print(f"\nnew pack: {NEW.stat().st_size} bytes")
    print(f"sha256 : {digest}")


if __name__ == "__main__":
    main()
