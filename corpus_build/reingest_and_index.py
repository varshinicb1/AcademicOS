"""Replay ingest from offset 0 and index, then verify the totals land exactly.

The previous ingest reused the stored cursor (10000) left by the earlier full
run, so it only read the tail of the new pack: 36 of the 884 rewritten chunks
landed. The route already supports `?offset=0` precisely for replaying a
corrupted cursor, so the fix is a full re-read rather than a Worker change.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"
EXPECTED_TOTAL = 12499
EXPECTED_PENDING = 884


def call(path: str, method: str = "GET", payload: dict | None = None,
         timeout: int = 600) -> dict:
    body = Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\call.json")
    args = ["curl.exe", "-sS", "-m", str(timeout), "-X", method,
            f"{WORKER}{path}", "-H", "Content-Type: application/json",
            "-H", "User-Agent: AcademicOS-corpus-indexer/1.0"]
    if payload is not None:
        body.write_text(json.dumps(payload), encoding="utf-8")
        args += ["--data-binary", f"@{body}"]
    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"curl failed: {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"non-JSON: {proc.stdout[:300]}") from exc


def health() -> dict:
    return call("/health")["corpus"]


def main() -> None:
    print("=== replaying ingest from offset 0 ===")
    start = time.time()
    while True:
        res = call("/ingest?max=6000&offset=0", "POST", {})
        print(f"[{time.time() - start:6.1f}s] processed={res.get('processed_this_call')} "
              f"resumed_from={res.get('resumed_from')} offset={res.get('offset')} "
              f"reached_end={res.get('reached_end')} "
              f"malformed={res.get('malformed')} failures={len(res.get('failures', []))}")
        if res.get("reached_end"):
            break
        time.sleep(1)

    c = health()
    print(f"\nafter replay: total={c['total']} vectorized={c['vectorized']} "
          f"pending={c['pending']} decoded={c['decoded_chunks']} "
          f"chapters={c['chapters']}")
    if c["total"] != EXPECTED_TOTAL:
        print(f"MISMATCH total: expected {EXPECTED_TOTAL} got {c['total']}")
        return
    if c["pending"] != EXPECTED_PENDING:
        print(f"MISMATCH pending: expected {EXPECTED_PENDING} got {c['pending']}")
        return
    print("totals match; indexing pending chunks")

    print("\n=== indexing ===")
    start = time.time()
    while True:
        res = call("/index?max=1000&batch=100", "POST", {})
        run = res.get("run", {})
        print(f"[{time.time() - start:6.1f}s] "
              f"indexed_this_call={res.get('indexed_this_call')} "
              f"indexed={run.get('indexed_chunks')}/{run.get('total_chunks')} "
              f"failed={run.get('failed_chunks')} "
              f"elapsed={res.get('call_elapsed_ms')}ms "
              f"rate={res.get('chunk_rate_per_s')}/s "
              f"err={str(run.get('last_error'))[:60]}")
        if res.get("pending") == 0 or not res.get("indexed_this_call"):
            break
        time.sleep(1)

    c = health()
    print(f"\nfinal: {json.dumps(c, indent=1)}")
    full = call("/health")
    print(f"vectors={full['index']['vector_count_reported']} "
          f"agrees={full['vector_count_agrees']}")


if __name__ == "__main__":
    main()
