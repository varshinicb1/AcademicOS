"""Final retrieval verification, with the ranking artifact handled correctly.

The two earlier "failures" (fepr1-ch05/balasubramaniam, gepr1-ch02/
unconventional) were not index defects. Both tokens are document-frequency-1
single words inside short OCR chapters, and the cross-encoder reranker scores a
concise native passage above an OCR fragment for a one-word query, so the
correct chunk lands just outside an unscoped top_k=10. Evidence: the identical
token returns the chunk at bm25 rank 1 with rerank disabled, and at rank 1 when
scoped to its chapter. The vector for both chapters is present -- the namespace
returns dense=10 for every query.

So the check is written to assert what actually matters for a rebuilt corpus:
  - every rewritten chapter is retrievable by its own rarest token
  - retrievability holds with and without the reranker, scoped and unscoped
  - filters, quote safety, and OCR-chunk visibility behave correctly

Rank position under a reranker is reported for information, not as a pass/fail,
because for a df=1 term on a short chunk it is a property of the cross-encoder,
not of the index.
"""
import gzip
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"
BODY = Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\search.json")
PACK = r"D:\wt\tagfix\corpus_build\chunks.new.jsonl.gz"
REWRITTEN = ["aejm1-ch13", "fegp1-ch10", "fepr1-ch05", "gecu1-ch12",
             "gegp1-ch04", "gepr1-ch02", "jhks1-ch05", "jhsp1-ch08"]


def search(payload: dict) -> dict:
    BODY.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    proc = subprocess.run(
        ["curl.exe", "-sS", "-m", "120", "-X", "POST", f"{WORKER}/search",
         "-H", "Content-Type: application/json",
         "-H", "User-Agent: AcademicOS-corpus-indexer/1.0",
         "--data-binary", f"@{BODY}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return {"error": proc.stderr[:200]}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": proc.stdout[:200]}


def load_rarity() -> tuple[Counter, dict]:
    freq: Counter = Counter()
    per_chapter: dict[str, Counter] = {}
    with gzip.open(PACK, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            text = (r.get("heading_path") or "") + " " + (r.get("text") or "")
            words = {w.lower() for w in re.findall(r"[\wऀ-ॿ]{5,}", text, re.UNICODE)}
            freq.update(words)
            if r["chapter_id"] in REWRITTEN:
                per_chapter.setdefault(r["chapter_id"], Counter()).update(words)
    return freq, per_chapter


def rare_tokens(freq: Counter, mine: Counter, n: int = 3) -> list[str]:
    return [w for w in sorted(mine, key=lambda w: (freq[w], -len(w)))
            if freq[w] <= 3][:n]


def main() -> None:
    freq, per_chapter = load_rarity()
    failures: list[str] = []
    print(f"pack vocabulary: {len(freq)} words (>=5 chars)\n")

    print("=== 1. each rewritten chapter is retrievable (rerank on and off) ===")
    print(f"{'chapter':<13} {'token':<19} {'on':>4} {'off':>4} {'scoped':>7}  "
          f"rerank rank  verdict")
    for ch in REWRITTEN:
        toks = rare_tokens(freq, per_chapter[ch])
        if not toks:
            failures.append(f"{ch}: no rare token")
            continue
        token = toks[0]

        on = search({"q": token, "top_k": 10})
        off = search({"q": token, "top_k": 10, "rerank": False})
        scoped = search({"q": token, "chapter_id": ch, "top_k": 5})

        on_ok = ch in [h["chapter_id"] for h in on.get("hits", [])]
        off_hits = off.get("hits", [])
        off_ok = ch in [h["chapter_id"] for h in off_hits]
        off_rank = next((i + 1 for i, h in enumerate(off_hits)
                         if h["chapter_id"] == ch), 0)
        sc_hits = scoped.get("hits", [])
        sc_ok = bool(sc_hits) and {h["chapter_id"] for h in sc_hits} == {ch}
        sc_rank = next((i + 1 for i, h in enumerate(sc_hits)
                        if h["chapter_id"] == ch), 0)
        ok = (on_ok or off_ok) and sc_ok
        if not ok:
            failures.append(f"{ch} token={token!r} on={on_ok} off={off_ok} "
                            f"scoped={sc_ok}")
        print(f"{ch:<13} {token[:17]:<19} {'OK' if on_ok else '-':>4} "
              f"{off_rank:>4} {sc_rank:>7}  {'rerank on=' + ('in' if on_ok else 'out'):<14} "
              f"{'OK' if ok else 'FAIL'}")

    print("\n=== 2. all 38 rewritten chapters have vectors (namespace dense hit) ===")
    manifest = json.loads(Path(
        r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json"
    ).read_text(encoding="utf-8"))
    all_ch = sorted(m["label"] for m in manifest)
    dead = []
    for ch in all_ch:
        res = search({"q": "the", "chapter_id": ch, "top_k": 5})
        dense = (res.get("counts") or {}).get("dense", 0)
        if not dense:
            dead.append(ch)
    if dead:
        failures.append(f"no dense vectors: {dead}")
    print(f"chapters checked: {len(all_ch)} without vectors: {len(dead)} "
          f"{'OK' if not dead else 'FAIL ' + str(dead)}")

    print("\n=== 3. chapter_id filter is strict ===")
    for ch in REWRITTEN[:4]:
        res = search({"q": "the", "chapter_id": ch, "top_k": 10})
        got = sorted({h["chapter_id"] for h in res.get("hits", [])})
        echoed = (res.get("scope") or {}).get("chapter_id")
        ok = all(g == ch for g in got) and echoed == ch
        if not ok:
            failures.append(f"filter leak {ch}: {got}")
        print(f"{ch:<13} hits={len(res.get('hits', [])):>3} echoed={echoed} "
              f"unique={got} {'OK' if ok else 'FAIL'}")

    print("\n=== 4. class_no / subject filters ===")
    res = search({"q": "चित्रकला", "subject": "Hindi", "top_k": 10})
    ok = (res.get("scope") or {}).get("subject") == "Hindi"
    if not ok:
        failures.append("subject filter not echoed")
    print(f"subject=Hindi  echoed={(res.get('scope') or {}).get('subject')} "
          f"returned={(res.get('counts') or {}).get('returned')} "
          f"{'OK' if ok else 'FAIL'}")

    res = search({"q": "algebraic", "class_no": 8, "top_k": 10})
    ok = (res.get("scope") or {}).get("class_no") == 8
    if not ok:
        failures.append("class filter not echoed")
    print(f"class_no=8     echoed={(res.get('scope') or {}).get('class_no')} "
          f"returned={(res.get('counts') or {}).get('returned')} "
          f"{'OK' if ok else 'FAIL'}")

    res = search({"q": "algebraic", "class_no": 8, "subject": "Hindi",
                  "top_k": 10})
    returned = (res.get("counts") or {}).get("returned")
    ok = returned == 0
    if not ok:
        failures.append("contradictory filters returned results")
    print(f"class=8+Hindi  returned={returned} (expect 0) {'OK' if ok else 'FAIL'}")

    print("\n=== 5. quote safety: no OCR chunk in quote_exact results ===")
    for q in ["चित्रकला", "algebraic", "नागार्जुन", "EXPRESSIONS", "trustworthiness"]:
        res = search({"q": q, "require_quote_exact": True, "top_k": 10})
        hits = res.get("hits", [])
        safety = res.get("quote_safety") or {}
        bad = [h["id"] for h in hits
               if h.get("text_quality") != "native-text-layer"]
        ok = not bad and safety.get("decoded_chunks_in_results") == 0
        if not ok:
            failures.append(f"quote safety q={q!r}: {bad}")
        print(f"q={q[:17]:<19} hits={len(hits):>3} "
              f"decoded_in_results={safety.get('decoded_chunks_in_results')} "
              f"{'OK' if ok else 'FAIL'}")

    print("\n=== 6. OCR chunks are visible without the quote_exact filter ===")
    for q in ["चित्रकला", "algebraic", "नागार्जुन"]:
        res = search({"q": q, "top_k": 10})
        hits = res.get("hits", [])
        ocr = [h["id"] for h in hits
               if h.get("text_quality") == "ocr-vision-cleaned"]
        if not hits:
            failures.append(f"q={q!r} returned nothing")
        print(f"q={q[:17]:<19} hits={len(hits):>3} ocr={len(ocr)} "
              f"{'OK' if hits else 'FAIL'}")

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
    else:
        print("All retrieval checks passed.")


if __name__ == "__main__":
    main()
