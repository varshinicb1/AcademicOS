"""Drive the corpus-rag Worker through ingest and indexing.

The Worker does a bounded slice per call because 12,570 embeddings do not fit in
one request. This script is the loop, and it exists mainly to report honestly:
the earlier seeding attempt died part-way and left nothing behind to say how far
it had reached. Progress therefore comes from the Worker's own D1 counters, not
from what this process believes it sent, so a crash and restart tells the truth.

Usage:
    python index_corpus.py --phase all
    python index_corpus.py --phase index --ingest-max 4000 --index-max 2000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"


def call(path: str, method: str = "GET", payload: dict | None = None, timeout: int = 300) -> dict:
    url = f"{WORKER}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            # Cloudflare's edge answers Python-urllib's default agent with 403
            # before the Worker is ever reached, which reads as an app failure.
            "User-Agent": "AcademicOS-corpus-indexer/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def alive(pid: int) -> bool:
    if os.name == "nt":
        # Windows has no signal 0; ask the kernel for a process handle instead.
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return code.value == STILL_ACTIVE
            return False
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def report(label: str, payload: dict, start: float, done: int, total: int) -> None:
    """Print one progress line.

    `done` and `total` are passed in rather than read out of the payload, because
    the two phases make progress on different counters. During ingest the work is
    records consumed from the 12,570-line pack, and `vectorized` is legitimately
    zero for the whole run -- reading it as progress reported "0/4000 0.0%" while
    four thousand rows were already inserted. During indexing the count that
    matters is `vectorized`.
    """
    elapsed = time.time() - start
    pct = round(done / total * 100, 1) if total else 0.0
    failures = payload.get("failures") or []
    failed = payload.get("failed_this_call", payload.get("malformed", 0))
    print(
        f"[{elapsed:7.1f}s pid={os.getpid()} alive={alive(os.getpid())}] {label}"
        f"  {done}/{total}  {pct}%"
        f"  last_error={payload.get('last_error') or '-'}"
        f"  failed={failed}"
        f"  offset={payload.get('offset', '-')}",
        flush=True,
    )
    for line in failures[:5]:
        print(f"    ! {line}", flush=True)
    if not payload.get("ok", True):
        print(f"    !! {label} reported failure: {json.dumps(payload)[:400]}", flush=True)


def main() -> int:
    global WORKER

    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", default=WORKER)
    ap.add_argument("--phase", choices=["ingest", "index", "all"], default="all")
    ap.add_argument("--ingest-max", type=int, default=4000)
    ap.add_argument("--index-max", type=int, default=2000)
    ap.add_argument("--embed-batch", type=int, default=50)
    ap.add_argument("--max-calls", type=int, default=200, help="circuit breaker")
    ap.add_argument(
        "--pack-total",
        type=int,
        default=12570,
        help="lines in chunks.v1.jsonl.gz, so ingest progress is a real percentage",
    )
    args = ap.parse_args()

    WORKER = args.worker

    start = time.time()
    health = call("/health")
    corpus = health.get("corpus", {})
    print(
        f"start: pack={health.get('pack')} corpus={corpus.get('total', 0)} chunks "
        f"across {corpus.get('chapters', 0)} chapters "
        f"(decoded={corpus.get('decoded_chunks', 0)}) pack_total={args.pack_total}",
        flush=True,
    )

    try:
        if args.phase in ("ingest", "all"):
            for n in range(args.max_calls):
                payload = call(f"/ingest?max={args.ingest_max}", method="POST")
                report(
                    f"ingest[{n + 1}]", payload, start,
                    done=payload.get("offset", 0), total=args.pack_total,
                )
                if not payload.get("ok", True):
                    print("ingest aborted: the Worker reported a bad record", flush=True)
                    return 1
                if payload.get("reached_end"):
                    print(f"ingest complete at {time.time() - start:.1f}s", flush=True)
                    break
            else:
                print(f"ingest hit the {args.max_calls}-call breaker", flush=True)
                return 1

        if args.phase in ("index", "all"):
            for n in range(args.max_calls):
                payload = call(
                    f"/index?max={args.index_max}&batch={args.embed_batch}", method="POST"
                )
                report(
                    f"index[{n + 1}]", payload, start,
                    done=payload.get("vectorized", 0), total=args.pack_total,
                )
                if payload.get("message") == "nothing pending":
                    print(f"indexing complete at {time.time() - start:.1f}s", flush=True)
                    break
            else:
                print(f"index hit the {args.max_calls}-call breaker", flush=True)
                return 1
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        print(f"transport failure at {time.time() - start:.1f}s: {err}", file=sys.stderr)
        return 2

    final = call("/health")
    print(json.dumps(final, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
