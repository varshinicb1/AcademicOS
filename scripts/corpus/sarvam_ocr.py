"""OCR legacy-font NCERT chapters with Sarvam Vision (Document AI digitise).

Why this exists
---------------
38 of the 572 chapters are set in legacy KrutiDev/Walkman fonts. Their embedded
text layer is not Unicode, so we decode it character-by-character with a lookup
table. That recovers the words but not the *shaping*: matras land in the wrong
place, so the output is good enough to retrieve and topic-match and useless to
quote. Those chunks are tagged `text_quality: decoded-legacy-font` and
`quote_exact: false`, which blocks question generation that quotes its evidence.

Sarvam Vision runs real OCR, so it produces correctly shaped Devanagari. This
script re-OCRs only the legacy chapters, which is the cheap subset:

    38 chapters / 496 pages / 50 jobs  ->  Rs 248
    all 572 chapters / 9,610 pages     ->  Rs 4,805  (not worth it; the
                                          native-text-layer chapters already
                                          parse at head_rec 0.771)

Constraints that shape the design
---------------------------------
* 10 pages per job, hard. Longer PDFs are split with pypdf.
* 10 requests/minute on EVERY plan, and upgrading does not raise it. So this
  throttles to a token bucket rather than discovering the limit with 429s.
* Billing is per page and real money, so it supports --dry-run, prints the cost
  before spending, caches by PDF content hash, and resumes by skipping chapters
  whose output already exists.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

import requests
from pypdf import PdfReader, PdfWriter

API = "https://api.sarvam.ai/doc-ai/v1/job"
MAX_PAGES_PER_JOB = 10
REQS_PER_MIN = 10
RATE_PER_SEC = REQS_PER_MIN / 60.0
COST_PER_PAGE_RS = 0.5
TERMINAL = {"completed", "partially_completed", "failed", "rejected"}


class Throttle:
    """Token bucket for the 10 req/min cap, shared across job create and poll."""

    def __init__(self, per_sec: float) -> None:
        self.min_interval = 1.0 / per_sec
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self.last = time.monotonic()


class SarvamError(RuntimeError):
    pass


def _headers(key: str) -> dict:
    return {"api-subscription-key": key, "User-Agent": "AcademicOS-sarvam-ocr/1.0"}


def _raise_for_status(resp: requests.Response) -> None:
    if resp.ok:
        return
    # 402/403 mean the key lacks the Document AI entitlement, which is a
    # different problem from a bad request and should not be retried.
    if resp.status_code in (402, 403):
        raise SarvamError(
            f"entitlement/billing error {resp.status_code}: {resp.text[:300]}"
        )
    if resp.status_code == 400:
        raise SarvamError(f"bad request (often >10 pages): {resp.text[:300]}")
    resp.raise_for_status()


def pdf_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:16]


def split_pdf(path: Path, max_pages: int) -> list[bytes]:
    """Return <=max_pages-sized PDF byte blobs, preserving order."""
    reader = PdfReader(str(path))
    total = len(reader.pages)
    if total <= max_pages:
        return [path.read_bytes()]
    out: list[bytes] = []
    for start in range(0, total, max_pages):
        writer = PdfWriter()
        for page in reader.pages[start : start + max_pages]:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        out.append(buf.getvalue())
    return out


def create_job(
    session: requests.Session, key: str, pdf_bytes: bytes, filename: str, language: str,
    throttle: Throttle,
) -> dict:
    throttle.wait()
    resp = session.post(
        f"{API}/digitise",
        headers=_headers(key),
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        data={"language": language, "output_format": "md"},
        timeout=180,
    )
    _raise_for_status(resp)
    return resp.json()


def poll_job(
    session: requests.Session, key: str, job_id: str, throttle: Throttle,
    max_wait: int = 600,
) -> dict:
    deadline = time.monotonic() + max_wait
    delay = 5.0
    while time.monotonic() < deadline:
        throttle.wait()
        resp = session.get(f"{API}/{job_id}/status", headers=_headers(key), timeout=60)
        _raise_for_status(resp)
        st = resp.json()
        status = str(st.get("status", "")).lower()
        if status in TERMINAL:
            return st
        usage = st.get("usage") or {}
        print(
            f"      status={status} pages={usage.get('pages_processed')}/"
            f"{usage.get('pages_total')}",
            flush=True,
        )
        time.sleep(delay)
        delay = min(delay * 1.3, 20.0)
    raise SarvamError(f"job {job_id} did not finish within {max_wait}s")


def fetch_markdown(session: requests.Session, key: str, job_id: str) -> str:
    resp = session.get(f"{API}/{job_id}/download-url", headers=_headers(key), timeout=60)
    _raise_for_status(resp)
    url = resp.json()["url"]
    resp = session.get(url, timeout=300)
    _raise_for_status(resp)

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        # The archive holds the primary output plus metadata/page_NNN.json and a
        # manifest; take the .md and ignore the rest.
        names = [n for n in zf.namelist() if n.lower().endswith(".md")]
        if not names:
            raise SarvamError(f"no markdown in archive for job {job_id}")
        names.sort(key=lambda n: (n.count("/"), len(n)))
        raw = zf.read(names[0]).decode("utf-8", errors="replace")
    return strip_embedded_images(raw)


# Sarvam emits every figure as an inline base64 data URI, which is ~98k chars per
# page and drowns the ~900 chars of actual text. For a text corpus the images are
# payload we do not want; stripping them took one 9-page chapter from 882k chars
# to 8.7k. Provenance that needs geometry should ask for output_format=json,
# which returns per-block bounding boxes instead of inline images.
_IMAGE_DATA_URI = re.compile(r"!\[[^\]]*\]\(\s*data:[^)]*\)", re.S)


def strip_embedded_images(md: str) -> str:
    out = _IMAGE_DATA_URI.sub("", md)
    out = re.sub(r"[ \t]+\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def ocr_pdf(
    session: requests.Session, key: str, path: Path, out_dir: Path, language: str,
    throttle: Throttle, label: str,
) -> dict:
    sha = pdf_sha(path)
    out_path = out_dir / f"{label}.md"
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  {label}: cached, skipping", flush=True)
        return {"label": label, "status": "cached", "out": str(out_path)}

    blobs = split_pdf(path, MAX_PAGES_PER_JOB)
    parts: list[str] = []
    pages_ok = 0
    failures: list[str] = []
    for i, blob in enumerate(blobs, 1):
        try:
            job = create_job(session, key, blob, f"{label}-p{i}.pdf", language, throttle)
            st = poll_job(session, key, job["job_id"], throttle)
            status = str(st.get("status", "")).lower()
            if status not in ("completed", "partially_completed"):
                failures.append(f"job{i}:{status}")
                continue
            parts.append(fetch_markdown(session, key, job["job_id"]))
            usage = st.get("usage") or {}
            pages_ok += int(usage.get("pages_succeeded") or 0) or len(blob) and 0
        except Exception as err:  # noqa: BLE001 - report, do not abort the batch
            failures.append(f"job{i}:{str(err)[:120]}")
            print(f"      ! job{i} failed: {str(err)[:160]}", flush=True)

    if not parts:
        return {"label": label, "status": "failed", "failures": failures}

    out_path.write_text("\n\n".join(parts), encoding="utf-8")
    return {
        "label": label,
        "status": "partial" if failures else "ok",
        "out": str(out_path),
        "sha": sha,
        "chars": sum(len(p) for p in parts),
        "failures": failures,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, help="single PDF to OCR")
    ap.add_argument("--label", help="output label for --pdf")
    ap.add_argument("--manifest", type=Path, help="JSON list of {pdf,label,language}")
    ap.add_argument("--out", type=Path, required=True, help="output directory")
    ap.add_argument("--language", default="hi-IN")
    ap.add_argument("--dry-run", action="store_true", help="size the job, spend nothing")
    ap.add_argument("--max-jobs", type=int, default=0, help="stop after N OCR jobs")
    args = ap.parse_args()

    key = os.environ.get("SARVAM_API_KEY", "")
    if not key and not args.dry_run:
        print("SARVAM_API_KEY is not set", file=sys.stderr)
        return 2

    if args.manifest:
        items = json.loads(args.manifest.read_text(encoding="utf-8"))
    elif args.pdf:
        items = [{"pdf": str(args.pdf), "label": args.label or args.pdf.stem,
                  "language": args.language}]
    else:
        ap.error("need --pdf or --manifest")

    # Size the whole batch first: billing is real and the 10-page cap makes the
    # job count, not the chapter count, the number that decides cost.
    plan, total_pages = [], 0
    for it in items:
        p = Path(it["pdf"])
        if not p.exists():
            print(f"  ! missing {p}", file=sys.stderr)
            continue
        n = len(PdfReader(str(p)).pages)
        jobs = -(-n // MAX_PAGES_PER_JOB)
        plan.append((it, n, jobs))
        total_pages += n

    print(f"chapters={len(plan)} pages={total_pages} jobs={sum(j for _, _, j in plan)}")
    print(f"estimated cost = Rs {total_pages * COST_PER_PAGE_RS:.2f} "
          f"(at Rs {COST_PER_PAGE_RS}/page)")
    print(f"submit floor at {REQS_PER_MIN} req/min = "
          f"{sum(j for _, _, j in plan) / REQS_PER_MIN:.1f} min")
    if args.dry_run:
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    throttle = Throttle(RATE_PER_SEC)
    start = time.time()
    results, spent_jobs = [], 0

    for idx, (it, n_pages, jobs) in enumerate(plan, 1):
        if args.max_jobs and spent_jobs >= args.max_jobs:
            print(f"stopping: --max-jobs {args.max_jobs} reached", flush=True)
            break
        print(f"[{time.time() - start:7.1f}s] {idx}/{len(plan)} {it['label']} "
              f"({n_pages}p, {jobs} job(s))", flush=True)
        res = ocr_pdf(session, key, Path(it["pdf"]), args.out,
                      it.get("language", args.language), throttle, it["label"])
        spent_jobs += jobs
        results.append(res)
        print(f"      -> {res['status']} {res.get('chars', 0)} chars"
              f"  (elapsed {time.time() - start:.1f}s)", flush=True)

    (args.out / "ocr_report.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    print(f"\ndone: {ok}/{len(results)} chapters in {time.time() - start:.1f}s")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
