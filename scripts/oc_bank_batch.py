"""Write class 9-10 questions chapter by chapter, with an opencode session answering the prompts.

    python scripts/oc_bank_batch.py                  # every chapter in PLAN, in order
    python scripts/oc_bank_batch.py --only jess2:1   # one chapter
    python scripts/oc_bank_batch.py --limit 3        # the next three not yet done

Per chapter, three steps (docs/handover-grade9-10.md):

  1. `gen_cbse_chapter.py --bridge` writes the chapter's prompts, one per call, to
     <work>/<book>-<NN>/p###.json;
  2. one opencode session reads <work>/BRIEF.md and writes r###.json beside each
     prompt. The session is killed if it passes --timeout-min, or if its log and its
     answers stop growing for --stall-min (a free model was seen to sit silent for
     22 minutes), then started once more: it only answers what has no r file yet;
  3. `gen_cbse_chapter.py --bridge --out` runs every answer through the same validator
     as any provider -- plus the evidence quotes and figure check -- and writes the
     chapter's own file, academicos-data/corpus/ai-cbse-9-10/<book>-<NN>.json.

It is resumable (a chapter whose file exists is skipped), runs one opencode process at
a time, and never touches the served bank: nothing here is served until a reviewer
approves it (REQUIREMENTS QB-5). Progress is appended to <work>/progress.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OUT_DIR = ROOT / "academicos-data" / "corpus" / "ai-cbse-9-10"
MANIFEST = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\manifest.json")
OPENCODE = Path(r"C:\nvm4w\nodejs\node_modules\opencode-ai\bin\opencode.exe")
MODEL = "opencode-go/space-bunny-free"

# Priority order: what the school cannot yet generate a paper for. Social Science and
# English first (their English-language books extract cleanly), Hindi last, after the
# extraction check below.
PLAN = ["jess1", "jess2", "jess3", "jess4", "iest1", "jeff1", "jefp1", "iebe1",
        "ihga1", "jhks1", "jhkr1", "jhsp1", "jhsy1"]


def chapters_of(book: str) -> list[int]:
    for b in json.loads(MANIFEST.read_text(encoding="utf-8")):
        if b["code"] == book:
            return sorted(f["number"] for f in b["files"])
    raise SystemExit(f"{book} is not in the textbook manifest")


def log(work: Path, **row) -> None:
    row["at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with (work / "progress.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(" ".join(f"{k}={v}" for k, v in row.items()), flush=True)


def gen(args: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(ROOT / "src")}
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_cbse_chapter.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=cwd, env=env)


def text_is_usable(prompt_file: Path, language: str) -> str | None:
    """Why the extracted chapter text should not be set questions from, or None."""
    user = json.loads(prompt_file.read_text(encoding="utf-8"))["user"]
    letters = [c for c in user if c.isalpha()]
    if len(letters) < 400:
        return f"only {len(letters)} letters of text"
    if "\ufffd" in user:
        return "replacement characters in the text"
    if language == "hi":
        devanagari = sum(1 for c in letters if "\u0900" <= c <= "\u097f")
        if devanagari / len(letters) < 0.4:
            return f"only {devanagari / len(letters):.0%} Devanagari: the extraction is not Hindi text"
    return None


def kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def answer(work: Path, folder: str, model: str, timeout_min: int, stall_min: int) -> int:
    """One opencode session over the folder's unanswered prompts. Returns the answers now there."""
    d = work / folder
    log_path = work / f"oc-{folder}.log"
    msg = f"Read BRIEF.md in this folder and do the job it describes for every prompt file in {folder}/."
    with log_path.open("ab") as out:
        proc = subprocess.Popen([str(OPENCODE), "run", "--dir", str(work), "-m", model, "--auto", msg],
                                stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    started = last_change = time.time()
    seen = (-1, -1)
    try:
        while proc.poll() is None:
            time.sleep(20)
            now = (len(list(d.glob("r*.json"))), log_path.stat().st_size)
            if now != seen:
                seen, last_change = now, time.time()
            if time.time() - started > timeout_min * 60:
                log(work, folder=folder, event="timeout", minutes=timeout_min)
                break
            if time.time() - last_change > stall_min * 60:
                log(work, folder=folder, event="stalled", minutes=stall_min)
                break
    finally:
        if proc.poll() is None:
            kill_tree(proc.pid)
    return len(list(d.glob("r*.json")))


def claim(work: Path, folder: str, lane: str) -> bool:
    """Take a chapter for this lane. A claim is a file made atomically, so two lanes never take
    the same chapter; a lane's own earlier claim (a restart) is still its own."""
    (work / "claims").mkdir(exist_ok=True)
    path = work / "claims" / f"{folder}.claim"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return path.read_text(encoding="utf-8").strip() == lane
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(lane)
    return True


def one_chapter(book: str, number: int, args, language: str) -> str:
    work = Path(args.work)
    folder = f"{book}-{number:02d}"
    out_file = OUT_DIR / f"{folder}.json"
    if out_file.exists() and not args.reingest:
        return "done-before"
    prep = gen(["--book", book, "--chapter", str(number), "--marks", str(args.marks),
                "--per-call", "3", "--bridge", str(work), "--check"])
    prompts = sorted((work / folder).glob("p*.json"))
    if not prompts:
        log(work, folder=folder, event="no-prompts", detail=(prep.stderr or prep.stdout)[-300:])
        return "failed"
    reason = text_is_usable(prompts[0], language)
    if reason:
        log(work, folder=folder, event="skipped", reason=reason)
        return "skipped"
    for attempt in (1, 2):
        have = len(list((work / folder).glob("r*.json")))
        if have >= len(prompts):
            break
        log(work, folder=folder, event="opencode", attempt=attempt, prompts=len(prompts), answered=have)
        answer(work, folder, args.model, args.timeout_min, args.stall_min)
    answered = len(list((work / folder).glob("r*.json")))
    if answered == 0:
        log(work, folder=folder, event="no-answers")
        return "failed"
    if answered < len(prompts):
        # A chapter with some calls unanswered is not done: its file would stand for the whole chapter
        # and its missing sections would never be retried. The answers so far stay on disk; the next
        # run asks the model only for the rest.
        log(work, folder=folder, event="incomplete", prompts=len(prompts), answered=answered)
        return "incomplete"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = gen(["--book", book, "--chapter", str(number), "--marks", str(args.marks), "--per-call", "3",
                "--bridge", str(work), "--model", args.model, "--out", str(out_file)])
    m = re.search(r"ch\d+\s+kept\s+(\d+)\s+refused\s+(\d+)", done.stdout)
    kept, refused = (int(m[1]), int(m[2])) if m else (0, 0)
    log(work, folder=folder, event="ingested", prompts=len(prompts), answered=answered, kept=kept, refused=refused)
    if kept == 0 and out_file.exists():
        out_file.unlink()          # nothing usable: leave the chapter to be retried, not recorded as done
        return "failed"
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=r"D:\acos-wt\_ocwork", help="prompts, answers, logs (outside the repo)")
    ap.add_argument("--only", help="book:chapter, e.g. jess2:1")
    ap.add_argument("--limit", type=int, help="stop after this many chapters were attempted")
    ap.add_argument("--marks", type=int, default=20, help="marks of paper covered per chapter")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--timeout-min", type=int, default=35)
    ap.add_argument("--stall-min", type=int, default=12)
    ap.add_argument("--lane", default="main",
                    help="a name for this driver; two lanes (one with --reverse) can run at once")
    ap.add_argument("--reverse", action="store_true",
                    help="take the plan's chapters from the end, so a second lane meets the first in the middle")
    ap.add_argument("--reingest", action="store_true",
                    help="validate and rewrite chapters already done, from the answers on disk "
                         "(after a change to the validator or the record format); no model is called "
                         "for a chapter whose prompts all have answers")
    args = ap.parse_args()
    work = Path(args.work)
    if not OPENCODE.is_file() or not (work / "BRIEF.md").is_file():
        raise SystemExit(f"needs {OPENCODE} and {work / 'BRIEF.md'}")
    lock = work / ("oc_bank_batch.lock" if args.lane == "main" else f"oc_bank_batch.{args.lane}.lock")
    if lock.exists():
        raise SystemExit(f"{lock} exists: another batch is running (delete it if that is not so)")
    lock.write_text(str(os.getpid()))
    attempted = 0
    try:
        from academicos.corpus import textbook as tb      # noqa: F401  (fails early if the env is wrong)
        books = {b["code"]: b for b in json.loads(MANIFEST.read_text(encoding="utf-8"))}
        todo = []
        for book in PLAN:
            for n in chapters_of(book):
                todo.append((book, n))
        if args.only:
            b, n = args.only.split(":")
            todo = [(b, int(n))]
        elif args.reverse:
            todo.reverse()
        for book, number in todo:
            if args.limit and attempted >= args.limit:
                break
            if (OUT_DIR / f"{book}-{number:02d}.json").exists() and not args.reingest:
                continue
            if not claim(work, f"{book}-{number:02d}", args.lane):
                continue            # the other lane has it
            attempted += 1
            result = one_chapter(book, number, args, books[book].get("language") or "en")
            log(work, folder=f"{book}-{number:02d}", event="result", result=result)
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
