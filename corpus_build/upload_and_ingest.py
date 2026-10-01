"""Upload the new pack to R2 and run ingest until the 38 chapters are back.

After a successful reset the Worker holds 11,615 chunks and is missing the 884
chunks for the 38 rewritten chapters. Ingest re-reads the pack and upserts; the
existing UPSERT_CHUNK clause keeps `vectorized=1` for chunks whose embed_text is
unchanged, so only the genuinely new text costs an embedding.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKER = "https://corpus-rag.cbvarshini1.workers.dev"
NEW = Path(r"D:\wt\tagfix\corpus_build\chunks.new.jsonl.gz")
R2_BUCKET = "academicos-qgen"
R2_KEY = "corpus/chunks.v1.jsonl.gz"


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
        raise SystemExit(f"non-JSON: {proc.stdout[:400]}") from exc


def main() -> None:
    print("uploading pack to R2...")
    proc = subprocess.run(
        # The file is passed with --file, not positionally: as a positional it is
        # parsed as the object path and the command prints usage instead.
        ["npx.cmd", "wrangler", "r2", "object", "put", f"{R2_BUCKET}/{R2_KEY}",
         "--file", str(NEW), "--remote", "--content-type", "application/gzip"],
        cwd=r"D:\wt\tagfix\workers\corpus-rag",
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(proc.stdout.strip() or proc.stderr.strip()[:600])
    if proc.returncode != 0:
        raise SystemExit("upload failed")

    expected_total = 12499
    expected_new = 884
    start = time.time()

    while True:
        res = call("/ingest", "POST", {"max": 2000})
        corpus = res.get("corpus", res)
        print(f"[{time.time() - start:6.1f}s] ingested={res.get('ingested')} "
              f"total={corpus.get('total')} "
              f"vectorized={corpus.get('vectorized')} "
              f"pending={corpus.get('pending')} "
              f"offset={res.get('next_offset') or res.get('offset')} "
              f"malformed={res.get('malformed')}")
        if corpus.get("total", 0) >= expected_total:
            break
        if not res.get("ingested"):
            break
        time.sleep(1)

    health = call("/health")
    print("\nhealth after ingest:")
    print(json.dumps(health["corpus"], indent=1))
    print(f"pending expected {expected_new}, got "
          f"{health['corpus']['pending']}")


if __name__ == "__main__":
    main()
