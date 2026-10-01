"""Poll Vectorize until its reported count reaches the D1 total.

The 884 upserts did land: the reported count has moved off 11615, which is
exactly the post-reset figure. Vectorize applies writes asynchronously, so the
counter lags and `vector_count_agrees` stays false for a while after a correct
run. Polling here is the only way to tell propagation from a real failure, and
it stops as soon as the counts agree rather than sleeping a fixed amount.
"""
import json
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"


def health() -> dict:
    proc = subprocess.run(
        ["curl.exe", "-sS", "-m", "60", f"{WORKER}/health",
         "-H", "User-Agent: AcademicOS-corpus-indexer/1.0"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(proc.stdout)


def main() -> None:
    t0 = time.time()
    prev = None
    stalls = 0
    while time.time() - t0 < 2400:
        h = health()
        c = h["corpus"]
        v = h["index"]["vector_count_reported"]
        elapsed = time.time() - t0
        delta = "" if prev is None else f" (+{v - prev})"
        print(f"[{elapsed:6.0f}s] d1_total={c['total']} d1_vectorized={c['vectorized']} "
              f"vectors={v} gap={c['vectorized'] - v} agrees={h['vector_count_agrees']}{delta}",
              flush=True)
        if v == prev:
            stalls += 1
            # Propagation is bursty; only a long flat run means it has stopped.
            if stalls >= 6:
                print("count unchanged for 6 polls; stopping")
                return
        else:
            stalls = 0
        prev = v
        if h["vector_count_agrees"]:
            print("\nvector_count_agrees=true: D1 and Vectorize are consistent")
            return
        time.sleep(20)
    print("\npolling window elapsed before the counts agreed")


if __name__ == "__main__":
    main()