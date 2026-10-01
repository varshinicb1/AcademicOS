"""Push the single changed chunk (fepr1-ch05:015) to the live Worker.

The rebuilt pack differs from the live pack in exactly one chunk, so this does
not need a chapter reset. It uploads the pack, replays ingest from offset 0,
and relies on the worker's UPSERT_CHUNK rule:

    vectorized = CASE WHEN chunks.embed_text = excluded.embed_text
                      THEN chunks.vectorized ELSE 0 END

so 12,498 unchanged chunks keep their vectors and only the one chunk whose text
actually changed costs an embedding. That is verified, not assumed: the script
asserts the pending count is exactly 1 after the replay and aborts otherwise,
because a larger pending count would mean the diff was wrong.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"
PACK = Path(r"D:\wt\tagfix\corpus_build\chunks.final.jsonl.gz")
R2_BUCKET = "academicos-qgen"
R2_KEY = "corpus/chunks.v1.jsonl.gz"
CWD = r"D:\wt\tagfix\workers\corpus-rag"
TMP = Path(r"C:\Users\varsh\AppData\Local\Temp\opencode")
EXPECTED_TOTAL = 12499
EXPECTED_PENDING = 1


def call(path, method="GET", payload=None, timeout=900):
    body = TMP / "call.json"
    args = ["curl.exe", "-sS", "-m", str(timeout), "-X", method, f"{WORKER}{path}",
            "-H", "Content-Type: application/json",
            "-H", "User-Agent: AcademicOS-corpus-indexer/1.0"]
    if payload is not None:
        body.write_text(json.dumps(payload), encoding="utf-8")
        args += ["--data-binary", f"@{body}"]
    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"curl failed on {path}: {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"non-JSON from {path}: {proc.stdout[:400]}") from exc


def main():
    start = time.time()

    def elapsed():
        return f"{time.time() - start:7.1f}s"

    before = call("/health")
    print(f"[{elapsed()}] before: {json.dumps(before.get('corpus', before))}")

    print(f"[{elapsed()}] uploading {PACK.name} to R2 {R2_BUCKET}/{R2_KEY} ...")
    proc = subprocess.run(
        ["npx.cmd", "wrangler", "r2", "object", "put", f"{R2_BUCKET}/{R2_KEY}",
         "--file", str(PACK), "--remote", "--content-type", "application/gzip"],
        cwd=CWD, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or proc.stderr).strip()
    print(f"[{elapsed()}] {out.splitlines()[-1] if out else '(no output)'}")
    if proc.returncode != 0:
        raise SystemExit("R2 upload failed")

    # Replay from the top: the cursor is a record number and the upsert is
    # idempotent, so a full re-read is the safe way to pick up a changed record.
    total_ingested = 0
    while True:
        res = call("/ingest?offset=0&max=4000", "POST")
        corpus = res.get("corpus", res)
        got = res.get("ingested", 0)
        total_ingested += got
        pct = 100.0 * total_ingested / EXPECTED_TOTAL
        print(f"[{elapsed()}] ingest: +{got} (total {total_ingested}/{EXPECTED_TOTAL} = {pct:5.1f}%) "
              f"malformed={res.get('malformed')} failures={res.get('failures')}")
        if not got:
            break

    health = call("/health")
    corpus = health.get("corpus", health)
    print(f"[{elapsed()}] after replay: {json.dumps(corpus)}")

    if corpus.get("pending") != EXPECTED_PENDING:
        raise SystemExit(
            f"ABORT: expected exactly {EXPECTED_PENDING} pending chunk, got "
            f"{corpus.get('pending')}. The pack diff was not the single chunk it "
            f"claimed to be; not indexing."
        )
    print(f"[{elapsed()}] pending={corpus['pending']} as expected - indexing")

    res = call("/index", "POST", {"max": 100, "batch": 25})
    print(f"[{elapsed()}] index: {json.dumps(res)}")

    # Vectorize is eventually consistent, so poll rather than assume.
    for attempt in range(1, 13):
        health = call("/health")
        corpus = health.get("corpus", health)
        print(f"[{elapsed()}] poll {attempt:>2}: total={corpus.get('total')} "
              f"vectorized={corpus.get('vectorized')} pending={corpus.get('pending')}")
        if corpus.get("pending") == 0 and corpus.get("vectorized") == corpus.get("total"):
            break
        time.sleep(5)

    print(f"\n[{elapsed()}] FINAL: {json.dumps(corpus)}")
    ok = (corpus.get("total") == EXPECTED_TOTAL
          and corpus.get("pending") == 0
          and corpus.get("vectorized") == corpus.get("total"))
    print(f"[{elapsed()}] {'OK' if ok else 'MISMATCH - investigate'}")


if __name__ == "__main__":
    main()
