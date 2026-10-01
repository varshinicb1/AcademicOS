"""Exercise the real reset route with the 38 chapter IDs from the manifest.

The route was already proven on one chapter by hand, but this time the caller
passes real IDs and a real body, so the failure modes that matter are different:
Cloudflare rejecting the request before the Worker is reached (403/1010 on
Python's default agent), PowerShell corrupting the JSON body, and the route
silently reporting success while deleting nothing.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"
MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
BODY = Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\reset_38.json")


def call(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    """Use curl.exe, not urllib: the edge 403s Python-urllib's default agent."""
    args = ["curl.exe", "-sS", "-m", "120", "-X", method,
            f"{WORKER}{path}", "-H", "Content-Type: application/json",
            "-H", "User-Agent: AcademicOS-corpus-indexer/1.0"]
    if payload is not None:
        # Body from a file: inline non-ASCII JSON does not survive PowerShell.
        BODY.write_text(json.dumps(payload), encoding="utf-8")
        args += ["--data-binary", f"@{BODY}"]
    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"curl failed: {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"non-JSON response: {proc.stdout[:400]}") from exc


def main() -> None:
    ids = sorted({m["label"] for m in
                  json.loads(MANIFEST.read_text(encoding="utf-8"))})
    print(f"resetting {len(ids)} chapters")

    before = call("/health")
    print(f"before: total={before['corpus']['total']} "
          f"vectorized={before['corpus']['vectorized']} "
          f"pending={before['corpus']['pending']} "
          f"decoded={before['corpus']['decoded_chunks']}")

    res = call("/reset-chapters", "POST", {"chapters": ids})
    print("\nreset response:")
    for key, value in res.items():
        print(f"  {key}: {value}")

    after = call("/health")
    print(f"\nafter: total={after['corpus']['total']} "
          f"vectorized={after['corpus']['vectorized']} "
          f"pending={after['corpus']['pending']} "
          f"decoded={after['corpus']['decoded_chunks']} "
          f"vectors={after['index']['vector_count_reported']} "
          f"agrees={after['vector_count_agrees']}")

    expected = 884
    print(f"\nexpected pending after reset: {expected}")
    print(f"actual   pending after reset: {after['corpus']['pending']}")
    if after["corpus"]["pending"] != expected:
        print("MISMATCH: the removed set is not the 38 rewritten chapters")
    if after["corpus"]["decoded_chunks"] != 0:
        print(f"decoded_chunks should be 0, got "
              f"{after['corpus']['decoded_chunks']}")


if __name__ == "__main__":
    main()
