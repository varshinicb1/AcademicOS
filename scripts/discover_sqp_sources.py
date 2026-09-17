"""Discover what CBSE actually publishes for Sample Question Papers + Marking Schemes.

The CBE item banks solved questions-and-answers in one document. SQP+MS is
published as an explicitly PAIRED artefact -- a question paper and its marking
scheme as two files -- which is why it is the target: the link between a
question and its answer is authority-provided rather than inferred, which is
exactly what the relink work could not establish for board papers.

This script discovers rather than guesses. CBSE's filenames and index pages have
changed across years, and a wrong URL silently yields nothing, so every
candidate page is probed and its PDF links reported.

Run:  python scripts/discover_sqp_sources.py
"""
from __future__ import annotations

import collections
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; AcademicOS corpus research)"}

# Index pages CBSE has used. Probed, not assumed.
CANDIDATES = [
    "https://cbseacademic.nic.in/SQP_CLASSX_2024-25.html",
    "https://cbseacademic.nic.in/SQP_CLASSXII_2024-25.html",
    "https://cbseacademic.nic.in/SQP_CLASSX_2023-24.html",
    "https://cbseacademic.nic.in/SQP_CLASSXII_2023-24.html",
    "https://cbseacademic.nic.in/SQP_CLASSX_2025-26.html",
    "https://cbseacademic.nic.in/SQP_CLASSXII_2025-26.html",
    "https://cbseacademic.nic.in/Assessment_SQP.html",
    "https://cbseacademic.nic.in/cbe/assessment.html",
    "https://cbseacademic.nic.in/SQP.html",
]

HREF = re.compile(r'href\s*=\s*["\']([^"\']+\.pdf)["\']', re.I)
TEXT = re.compile(r">([^<]{3,120})<")


def fetch(url: str) -> str | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                    timeout=25) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"    ({type(exc).__name__}: {exc})")
        return None


def main() -> int:
    print("== probing CBSE index pages ==")
    found: dict[str, list[str]] = {}
    for url in CANDIDATES:
        print(f"\n  {url}")
        html = fetch(url)
        if html is None:
            continue
        links = sorted(set(HREF.findall(html)))
        if not links:
            print(f"    reachable, {len(html):,} bytes, but no .pdf links")
            continue
        found[url] = links
        print(f"    reachable, {len(links)} pdf links")

    if not found:
        print("\nno index page yielded pdf links")
        return 1

    print()
    print("== all pdf links discovered ==")
    all_links = sorted({l for links in found.values() for l in links})

    # Classify: a marking scheme is the pair of a question paper. Both must be
    # present for a paper to be useful, so they are counted together.
    sqp = [l for l in all_links if re.search(r"sqp", l, re.I)]
    ms = [l for l in all_links if re.search(r"(^|[/_\-])ms[_\-.]|marking", l, re.I)]
    other = [l for l in all_links if l not in sqp and l not in ms]

    print(f"  sample question papers : {len(sqp)}")
    for l in sqp[:24]:
        print(f"      {l}")
    print(f"  marking schemes        : {len(ms)}")
    for l in ms[:24]:
        print(f"      {l}")
    print(f"  other pdfs             : {len(other)}")
    for l in other[:14]:
        print(f"      {l}")

    # Which subjects appear? This answers "does this add Social Science?"
    print()
    print("== subjects implied by the discovered filenames ==")
    words = collections.Counter()
    for l in all_links:
        for w in re.findall(r"[A-Za-z]{4,}", l.split("/")[-1]):
            words[w.lower()] += 1
    interesting = [w for w in ("social", "science", "hindi", "english", "maths",
                               "mathematics", "sanskrit", "history", "geography",
                               "economics", "physics", "chemistry", "biology")
                   if words.get(w)]
    print(f"  {', '.join(interesting) if interesting else 'none recognised'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
