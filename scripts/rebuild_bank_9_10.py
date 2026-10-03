"""Rebuild the class 9-10 served bank from the generated chapters, then prove every paper it serves.

    python scripts/rebuild_bank_9_10.py                 # collect -> merge -> enrich -> verify every preset
    python scripts/rebuild_bank_9_10.py --no-verify     # the bank only
    python scripts/rebuild_bank_9_10.py --exams annual  # verify one exam type
    python scripts/rebuild_bank_9_10.py --report out.json

The model-written chapters (academicos-data/corpus/ai-cbse-9-10/<book>-<NN>[-pass].json) come from
scripts/oc_bank_batch.py (docs/opencode-bank-brief.md). This runs the rest, in order, and stops at the
first step that fails:

  1. collect_ai_910.py          every chapter file -> one ai-cbse-9-10/questions.json
  2. merge_question_banks.py    the gates (bank_merge.compose): only a question whose key is quoted from
                                the book is served; everything else is listed in _merge_excluded.json
  3. enrich_question_bank.py    fills the served records' asset fields and stamps the scheme verifier
  4. verify_papers.py --pdf     the real route makes every CBSE preset for classes 9 and 10, all five
                                subjects, four exam types, with no gaps allowed, and each paper (and its
                                printed and answer-key PDFs) is held to its template

Exit 0 only when step 4 verified every paper. The served bank files it rewrote are the data to commit.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, *args: str) -> int:
    started = time.time()
    print(f"\n== {label}", flush=True)
    code = subprocess.run([sys.executable, *args], cwd=ROOT).returncode
    print(f"== {label}: {'ok' if code == 0 else f'FAILED ({code})'} in {time.time() - started:.0f}s", flush=True)
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-verify", action="store_true", help="stop after the served bank is written")
    ap.add_argument("--exams", default="unit_test,periodic,half_yearly,annual")
    ap.add_argument("--report", type=Path, help="write the verification report (JSON) here")
    args = ap.parse_args()

    scripts = ROOT / "scripts"
    for label, script in (("collect the generated chapters", "collect_ai_910.py"),
                          ("merge the served bank", "merge_question_banks.py"),
                          ("enrich the served bank", "enrich_question_bank.py")):
        code = run(label, str(scripts / script))
        if code:
            return code
    if args.no_verify:
        return 0
    verify = [str(scripts / "verify_papers.py"), "--pdf", "--exams", args.exams]
    if args.report:
        verify += ["--json", str(args.report)]
    return run("verify every class 9-10 paper", *verify)


if __name__ == "__main__":
    sys.exit(main())
