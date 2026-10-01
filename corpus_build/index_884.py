"""Index the 884 pending chunks in small batches.

The previous attempt issued /index?max=1000 and the process stopped producing
output: 884 chunks at ~0.14 s each is a few minutes of Workers CPU, which
crosses the paid-plan CPU limit for a single request. max=100 with batch=50 keeps
each call short enough to return, and the loop resumes from D1's own counter so
a killed call loses nothing but the current batch.

Reports progress from the Worker's /health counters, not from what this script
believes it sent, so an interrupted run still tells the truth on the next call.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"
LOG = Path(r"D:\wt\tagfix\corpus_build\index_884.log")


def call(path: str, method: str = "GET", timeout: int = 240) -> dict:
    proc = subprocess.run(
        ["curl.exe", "-sS", "-m", str(timeout), "-X", method, f"{WORKER}{path}",
         "-H", "Content-Type: application/json",
         "-H", "User-Agent: AcademicOS-corpus-indexer/1.0"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"curl rc={proc.returncode}: {proc.stderr[:200]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"non-JSON: {proc.stdout[:200]}") from exc


def main() -> None:
    start_total = call("/health")["corpus"]["pending"]
    print(f"pending at start: {start_total}", flush=True)
    lines = []
    if start_total == 0:
        print("nothing to do")
        return

    t0 = time.time()
    done = 0
    call_no = 0
    while True:
        call_no += 1
        try:
            res = call("/index?max=100&batch=50", "POST")
        except RuntimeError as exc:
            # A timeout kills the request but the Worker may still have finished
            # the batch, so re-read /health and continue rather than aborting.
            c = call("/health")["corpus"]
            line = (f"[{time.time() - t0:7.1f}s] call {call_no} error: {exc} "
                    f"| pending now {c['pending']} vectorized {c['vectorized']}")
            print(line, flush=True)
            lines.append(line)
            if c["pending"] == 0:
                break
            if c["pending"] == start_total and done == 0 and call_no > 20:
                print("no progress after 20 attempts; stopping")
                break
            time.sleep(2)
            continue

        run = res.get("run", {})
        c = call("/health")["corpus"]
        done = c["vectorized"]
        line = (f"[{time.time() - t0:7.1f}s] call {call_no:>3} "
                f"indexed_this={res.get('indexed_this_call')} "
                f"vectorized={c['vectorized']} pending={c['pending']} "
                f"failed={run.get('failed_chunks')} "
                f"call_ms={res.get('call_elapsed_ms')} rate={res.get('chunk_rate_per_s')} "
                f"err={str(run.get('last_error'))[:70]}")
        print(line, flush=True)
        lines.append(line)

        if run.get("failed_chunks"):
            print("ABORT: index reported failures")
            break
        if c["pending"] == 0:
            break
        if not res.get("indexed_this_call") and call_no > 5:
            print("no chunks indexed in recent calls; stopping to inspect")
            break

    c = call("/health")["corpus"]
    print(f"\nfinal corpus: {json.dumps(c, indent=1)}")
    print(f"newly vectorized: {c['vectorized'] - (c['total'] - c['pending']) - c['pending']}"
          if False else f"pending left: {c['pending']}")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"log: {LOG}")


if __name__ == "__main__":
    main()
