"""Prove the reset -> re-ingest -> re-index loop on one chapter.

The OCR rebuild depends on this working: chapters are reset so their old
vectors cannot survive as stale hits, then come back from the pack and are
re-embedded. If any step here is wrong the rebuild silently corrupts search,
so it is checked end to end on the cheapest real chapter (7 chunks) before
touching all 38.
"""
import json
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://corpus-rag.cbvarshini1.workers.dev"
CH = "aejm1-ch13"


def call(path, method="GET", payload=None, tries=3):
    url = f"{BASE}{path}"
    data = None
    # Cloudflare answers urllib's default agent with 403/1010, so send a normal
    # one. Same endpoint, same request body; only the agent differs.
    headers = {"User-Agent": "curl/8.4.0"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}"
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        print(f"    (attempt {attempt + 1} failed: {last})")
    raise SystemExit(f"request failed: {path} -> {last}")


def health():
    h = call("/health")
    c = h["corpus"]
    return {
        "total": c.get("total"),
        "vectorized": c.get("vectorized"),
        "chapters": c.get("chapters"),
        "decoded": c.get("decoded_chunks"),
        "vec_reported": h["index"].get("vector_count_reported"),
        "agrees": h.get("vector_count_agrees"),
    }


def present():
    h = call("/health")
    return h["corpus"].get("chapters"), h["corpus"].get("total")


def drain_ingest():
    """Re-ingest the whole pack. Safe to repeat: the upsert preserves
    `vectorized` for every chunk whose embed_text is unchanged."""
    offset, rounds = 0, 0
    while True:
        rounds += 1
        ing = call(f"/ingest?offset={offset}&max=6000", "POST")
        offset = ing.get("next_offset", 0)
        print(f"        ingest round {rounds}: processed={ing.get('processed_this_call')} "
              f"offset={offset} drained={ing.get('drained')} "
              f"reached_end={ing.get('reached_end')} malformed={ing.get('malformed')}")
        assert ing.get("malformed") == 0, f"malformed records: {ing.get('malformed_detail')}"
        if ing.get("drained") or not offset or rounds > 20:
            return ing
        offset = ing.get("offset", offset)


def index_all(max_chunks=4000):
    total, rounds = 0, 0
    while True:
        rounds += 1
        idx = call(f"/index?max={max_chunks}&batch=100", "POST")
        got = idx.get("indexed_this_call", 0)
        total += got
        print(f"        index round {rounds}: indexed={got} call_ms={idx.get('call_elapsed_ms')} "
              f"run_ms={idx.get('run_elapsed_ms')} rate={idx.get('chunk_rate_per_s')}/s "
              f"pending={idx.get('pending')} failed={idx.get('failed_this_call')}")
        if not got or rounds > 20:
            return idx


# A previous aborted run can leave the probe chapter deleted, so restore before
# measuring. Without this the script reports a smaller corpus as the baseline and
# every later assertion is comparing against the wrong numbers.
print("STEP 0a  restore probe chapter if a previous run left it deleted")
drain_ingest()
index_all()
before = health()
print("        ", before)
assert before["total"] == 12570, f"corpus is not whole: {before}"
assert before["agrees"], f"D1 and Vectorize disagree before the test: {before}"

print("\nSTEP 0b  baseline")
print("        ", before)

print(f"\nSTEP 1  reset {CH}")
r = call("/reset-chapters", "POST", {"chapters": [CH]})
for k in ("ok", "rows_removed", "vectors_deleted", "driver_changes", "rows_remaining", "vector_errors"):
    print(f"        {k} = {r[k]}")
assert r["rows_removed"] > 0, "reset deleted nothing, test is not exercising the path"
assert r["vectors_deleted"] == r["rows_removed"], "D1 and Vectorize disagree on removal"
assert r["rows_remaining"] == 0, "rows survived the reset"

mid = health()
print("        after reset:", mid)
assert mid["total"] == before["total"] - r["rows_removed"], "total did not drop by rows_removed"
assert mid["vectorized"] == before["vectorized"] - r["rows_removed"], "vectorized did not drop"

print("\nSTEP 2  re-ingest from offset 0 (upsert must preserve every other chapter)")
drain_ingest()

after_ingest = health()
print("        after ingest:", after_ingest)
assert after_ingest["total"] == before["total"], "total not restored"
assert after_ingest["vectorized"] == before["vectorized"] - r["rows_removed"], (
    "re-ingest re-marked other chapters as pending; the vectorized guard is not holding"
)

print("\nSTEP 3  re-index (should embed ONLY the reset chapter)")
idx = call("/index?max=200&batch=100", "POST")
print(f"        indexed_this_call={idx.get('indexed_this_call')} "
      f"call_ms={idx.get('call_elapsed_ms')} rate={idx.get('chunk_rate_per_s')}/s "
      f"failed={idx.get('failed_this_call')}")
embedded = idx.get("indexed_this_call", 0)
assert embedded == r["rows_removed"], (
    f"expected exactly {r['rows_removed']} re-embeds, got {embedded}"
)

print("\nSTEP 4  final health")
final = health()
print("        ", final)
assert final["vectorized"] == before["vectorized"], "vectorized not fully restored"
assert final["total"] == before["total"], "total not fully restored"

print("\nSTEP 5  the chapter is searchable again, and global search is intact")
# `aejm1-ch13` is a legacy decoded chapter, so its "words" are mojibake and the
# same garbage tokens occur in other decoded chapters. Scoping to the chapter is
# what makes this a test of the rebuilt vectors rather than of the corpus.
scoped = call("/search", "POST",
              {"q": "चपबजनतम", "topK": 10, "chapter_id": CH, "require_quote_exact": False})
scoped_ids = [h["id"] for h in scoped.get("hits", [])]
print(f"        scoped to {CH}: {len(scoped_ids)} hits {scoped_ids[:4]}")
assert any(i.startswith(CH) for i in scoped_ids), (
    f"reset chapter is not retrievable after the rebuild loop: {scoped_ids}"
)

native = call("/search", "POST",
              {"q": "photosynthesis", "topK": 5, "require_quote_exact": True})
native_ids = [h["id"] for h in native.get("hits", [])]
print(f"        global native search: {len(native_ids)} hits {native_ids[:4]}")
print(f"        quote_safety: {native.get('quote_safety')}")
assert native_ids, "global search returned nothing; the re-ingest broke retrieval"

print("\nALL CHECKS PASSED")


