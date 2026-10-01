"""Verify the cleaned corpus against the manifest, and sample real Hindi.

Two checks that must both pass before any of this is chunked:

  1. Every book now matches the language the manifest claims. Before stripping,
     the six English books measured 21-37% Devanagari because Vision narrated
     English pages in Hindi, so the manifest looked wrong. After stripping they
     should read as English and the Hindi books as Hindi. If a book still
     disagrees, the label is the thing under suspicion, not the text.
  2. The Hindi books still contain real Hindi prose. A 25-31% reduction on the
     art books is only safe if what remains is textbook text and not the ash of
     an over-eager rule.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\wt\tagfix\corpus_build")

from strip_narration import (NARRATION_OPENER, NO_TEXT_TAIL,  # noqa: E402
                             NEVER_REMOVE, body_words)

CLEAN = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr_clean")
DEVA = re.compile(r"[ऀ-ॿ]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
DEV_WORD = re.compile(r"[ऀ-ॿ]{2,}")
HINDI = ["jhkr1", "jhks1", "jhsp1", "jhsy1"]
ENGLISH = ["aejm1", "fegp1", "fepr1", "gecu1", "gegp1", "gepr1"]


def measure(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    body = re.sub(r"^#.*$", "", text, flags=re.M)
    latin = len(LATIN_WORD.findall(body))
    dev = len(DEV_WORD.findall(body))
    return {
        "chars": len(text),
        "words": body_words(text),
        "latin": latin,
        "dev": dev,
        "latin_share": latin / (latin + dev) if (latin + dev) else 0.0,
    }


def leftover_narration(path: Path) -> list[str]:
    hits = []
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if NEVER_REMOVE.search(line):
            continue
        if NARRATION_OPENER.match(line) or NO_TEXT_TAIL.search(line):
            hits.append(f"  L{i}: {line.strip()[:110]}")
    return hits


def main() -> None:
    failures = 0

    print("=== Hindi books (expect high Devanagari, little Latin) ===")
    print(f"{'file':<16} {'chars':>8} {'words':>7} {'latin':>7} {'dev':>7} {'dev%':>6} "
          f"{'left':>5}")
    for path in sorted(CLEAN.glob("*.md")):
        if not any(path.stem.startswith(h) for h in HINDI):
            continue
        m = measure(path)
        left = leftover_narration(path)
        dev_pct = m["dev"] / (m["dev"] + m["latin"]) if (m["dev"] + m["latin"]) else 0
        flag = ""
        if dev_pct < 0.80:
            flag = "  <-- too little Hindi"
            failures += 1
        print(f"{path.stem:<16} {m['chars']:>8} {m['words']:>7} {m['latin']:>7} "
              f"{m['dev']:>7} {dev_pct:>5.0%} {len(left):>5}{flag}")
        for hit in left[:3]:
            print(hit)

    print("\n=== English books (expect high Latin) ===")
    print(f"{'file':<16} {'chars':>8} {'words':>7} {'latin':>7} {'dev':>7} {'latin%':>7} "
          f"{'left':>5}")
    for path in sorted(CLEAN.glob("*.md")):
        if not any(path.stem.startswith(e) for e in ENGLISH):
            continue
        m = measure(path)
        left = leftover_narration(path)
        flag = ""
        if m["latin_share"] < 0.75:
            flag = "  <-- too little English"
            failures += 1
        print(f"{path.stem:<16} {m['chars']:>8} {m['words']:>7} {m['latin']:>7} "
              f"{m['dev']:>7} {m['latin_share']:>6.0%} {len(left):>5}{flag}")
        for hit in left[:3]:
            print(hit)

    print("\n=== real Hindi prose sample (jhks1-ch05, 31% removed) ===")
    body = [l.strip() for l in (CLEAN / "jhks1-ch05.md").read_text(
        encoding="utf-8", errors="replace").splitlines()
        if len(DEVA.findall(l)) > 12 and len(l.strip()) > 40]
    for line in body[:6]:
        print(f"  {line[:150]}")

    print("\n=== real English prose sample (gegp1-ch04) ===")
    body = [l.strip() for l in (CLEAN / "gegp1-ch04.md").read_text(
        encoding="utf-8", errors="replace").splitlines()
        if len(LATIN_WORD.findall(l)) > 5 and len(l.strip()) > 40]
    for line in body[:6]:
        print(f"  {line[:150]}")

    print()
    print("FAILURES:" if failures else "All language checks passed.")
    if failures:
        print(f"  {failures} file(s) disagree with their manifest language")


if __name__ == "__main__":
    main()
