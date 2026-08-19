"""Real accuracy calibration for the deterministic evaluation engine's
SHORT-ANSWER path, completing the short-answer half the MCQ calibration
(scripts/calibrate_evaluation.py) explicitly deferred to OCR-first.

Same real, public, teacher-graded dataset (CC BY 4.0, Dinesh K P / Anna
University Chennai, DOI 10.17632/sf3kvjwknt.1, 50 students, Data Science
exam): here we run the FULL pipeline the production Scan & Grade flow runs
PDF -> page raster @200 DPI -> real Sarvam Vision OCR (3-pass voted, the
same ocr_page() the server uses) -> real segment_answers() -> real
evaluate_answer() against Q21-35 -> compare to the teacher's recorded
per-question marks (columns "21".."35").

!! STATUS: NEVER COMPLETED A VERIFIED RUN -- DO NOT CITE ITS NUMBERS !!

This script was written to run the calibration, but the run it was written
for died partway through when its input dataset was deleted out from under
it (a disk cleanup wiped the scratchpad holding the Mendeley download and
the OCR cache). No result was ever produced, nothing was written to
docs/compliance.md, and no output artifact survives.

Consequences, stated plainly so nobody mistakes this for measured work:
  * The short-answer half of the evaluation-precision calibration is still
    an OPEN GAP. docs/compliance.md's calibration section reports the MCQ
    result only, and that remains the only measured number.
  * An earlier draft of this docstring asserted specific OCR observations
    (Sarvam emitting HTML tables, a misread handwritten digit, some PDFs'
    trailing pages belonging to unrelated exams). Those claims could not be
    verified afterwards -- the dataset, the OCR cache and the run log are
    all gone -- so they have been removed rather than left standing as
    findings. Treat this file as untested code, not as evidence.

Before trusting anything this produces:
  1. Re-download the dataset (DOI above) and point --data-dir at it; the
     default path below points into a scratchpad that no longer exists.
  2. Run it, read the real output, and only then write numbers into
     docs/compliance.md -- reporting the result honestly whether it
     flatters the engine or not.
  3. Treat the first run as also being a stress test of segment_answers()
     against a non-CBSE handwriting surface, and report any new
     segmentation failures it exposes.

Design notes that do NOT depend on a run having happened: the engine awards
integer marks only (0/1/2 per question) while the teacher CSV also records
half-marks (0.5/1.5), which an integer engine cannot match exactly -- so
agreement is reported both across all teacher marks and restricted to the
integer-valued subset, with a within-1 tolerance alongside.

Run:
    python scripts/calibrate_short_answer.py --data-dir <path-to-dataset>
    python scripts/calibrate_short_answer.py --max-students 20 --workers 6
    python scripts/calibrate_short_answer.py --resume   # reuse cached OCR

No server is started; this is a pure script. OCR text is cached under the
workdir so a re-run with --resume does not re-bill Sarvam.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import csv
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from academicos.assessment import scan, vision
from academicos.assessment.evaluate import evaluate_answer
from academicos.assessment.schemas import (
    AnswerSchemeSchema,
    MarkingPointSchema,
    QuestionSchema,
)

log = logging.getLogger("calibrate_short_answer")

DATA_DIR = Path(
    r"C:\Users\varsh\AppData\Local\Temp\claude\C--Users-varsh-OneDrive-Documents-Sarvam"
    r"\7de05406-7bc4-4b11-8a62-4c7aca496926\scratchpad\mendeley_data"
    r"\A Dataset of Digitized Student Examination Papers,"
)
STUDENT_PDF_DIR = DATA_DIR / "Student_Pdf"

SHORT_ANSWERS = {
    21: "A type of ML where the model is trained on labeled data with known inputs and outputs.",
    22: "Overfitting; the model has memorized the training data but failed to generalize.",
    23: "A statistical process for estimating the relationships between a dependent variable and one or more independent variables.",
    24: "Data quality/missing values, overfitting/underfitting, data collection, or time consumption.",
    25: "Healthcare/disease prediction, Finance/fraud detection, E-commerce recommendation systems.",
    26: "Structured is organized in rows/columns (SQL, Excel); Semi-structured has some markers but isn't in a grid (JSON, XML, HTML).",
    27: "Detection: Z-score, IQR, Scatter plots, Box plots. Handling: Trimming, Capping, or Imputation.",
    28: "The steps taken to clean and transform raw data into a format suitable for a machine learning model.",
    29: "K-NN is distance-based; features with larger scales will dominate the distance calculation if not normalized.",
    30: "By grouping values into bins or intervals, e.g., turning ages 1-100 into 'Child,' 'Adult,' 'Senior.'",
    31: "The predefined number of clusters or groups the data will be divided into.",
    32: "K in K-NN, Learning Rate, Number of Estimators/Trees, Max Depth, or Batch Size.",
    33: "An optimization algorithm used to minimize the cost function by iteratively moving toward the steepest descent.",
    34: "Discussion on maximizing the margin and ensuring no data points fall within the 'gutter' or margin.",
    35: "It transforms data into a higher-dimensional space to find a non-linear decision boundary.",
}

# Two 1-mark keyword points per 2-mark question, extracted from the reference
# answer text above. Approximate by construction -- short-answer keyword
# matching is exactly the weak point this calibration exists to measure.
MARKING_POINTS: dict[int, list[dict]] = {
    21: [
        {"kw": "labeled data", "syn": ["labelled data", "label", "labels"]},
        {"kw": "input", "syn": ["inputs", "output", "outputs", "target", "prediction"]},
    ],
    22: [
        {"kw": "overfitting", "syn": ["overfit", "over-fitting", "memorized"]},
        {"kw": "generalize", "syn": ["generalization", "generalised", "testing"]},
    ],
    23: [
        {"kw": "relationship", "syn": ["relations", "correlation", "between"]},
        {"kw": "dependent", "syn": ["independent", "variable", "continuous", "predict"]},
    ],
    24: [
        {"kw": "missing", "syn": ["missing values", "data quality", "collection", "collecting", "dataset"]},
        {"kw": "overfitting", "syn": ["underfitting", "overfit", "time", "consumption", "cost"]},
    ],
    25: [
        {"kw": "health", "syn": ["healthcare", "medical", "disease", "hospital", "diagnos"]},
        {"kw": "finance", "syn": ["financial", "fraud", "bank", "e-commerce", "ecommerce", "recommendation"]},
    ],
    26: [
        {"kw": "structured", "syn": ["structured data", "rows", "columns", "organized", "sql", "excel"]},
        {"kw": "semi-structured", "syn": ["semi structured", "semistructured", "json", "xml", "html", "marker"]},
    ],
    27: [
        {"kw": "z-score", "syn": ["zscore", "z score", "iqr", "scatter", "box", "plot"]},
        {"kw": "imputation", "syn": ["imput", "trimming", "trim", "capping", "cap", "remove"]},
    ],
    28: [
        {"kw": "clean", "syn": ["cleaning", "cleansing", "cleanse"]},
        {"kw": "transform", "syn": ["transformation", "format", "suitable", "prepare", "raw"]},
    ],
    29: [
        {"kw": "distance", "syn": ["distances", "nearest", "neighbor", "neighbour"]},
        {"kw": "scale", "syn": ["scaling", "normaliz", "normalis", "dominate", "range"]},
    ],
    30: [
        {"kw": "bin", "syn": ["bins", "interval", "intervals", "group", "grouping"]},
        {"kw": "child", "syn": ["children", "adult", "senior", "age", "example"]},
    ],
    31: [
        {"kw": "cluster", "syn": ["clusters", "group", "groups", "partition"]},
        {"kw": "number", "syn": ["predefined", "pre-defined", "specified", "division"]},
    ],
    32: [
        {"kw": "learning rate", "syn": ["learning-rate"]},
        {"kw": "estimator", "syn": ["estimators", "trees", "max depth", "batch", "depth", "k in k-nn", "knn", "neighbor", "neighbour"]},
    ],
    33: [
        {"kw": "minimize", "syn": ["minimise", "minimization", "reduce"]},
        {"kw": "cost", "syn": ["cost function", "optimization", "optimisation", "steepest", "descent", "iterative", "step"]},
    ],
    34: [
        {"kw": "margin", "syn": ["margins", "gutter", "boundary", "boundaries"]},
        {"kw": "data point", "syn": ["data points", "points", "support vector", "classif", "hyperplane"]},
    ],
    35: [
        {"kw": "higher-dimensional", "syn": ["higher dimensional", "higher dimension", "dimensional", "space"]},
        {"kw": "non-linear", "syn": ["nonlinear", "non linear", "decision boundary", "boundary"]},
    ],
}

# Column names in Teacher_manual_marks_Anonymized.csv for Q21-35.
TEACHER_MARK_COLS = {q: str(q) for q in range(21, 36)}
# "NC" = "No mark awarded, not corrected" (blank/skipped) per the dataset README.
NO_MARK_TOKENS = {"", "NC", "NM", "-", "NA", "nan", "none"}


def build_questions() -> dict[int, QuestionSchema]:
    now = datetime.now(timezone.utc)
    questions: dict[int, QuestionSchema] = {}
    for qnum, reference in SHORT_ANSWERS.items():
        points = []
        for i, spec in enumerate(MARKING_POINTS[qnum], start=1):
            points.append(MarkingPointSchema(
                id=f"mendeley:sa:{qnum}:mp{i}",
                description=f"1 mark: {spec['kw']}",
                marks=1,
                keyword=spec["kw"],
                synonyms=spec["syn"],
            ))
        questions[qnum] = QuestionSchema(
            id=f"mendeley:sa:{qnum}",
            question_bank_id="mendeley-calibration",
            subject="Data Science",
            grade=0,
            bloom_level="remember",
            difficulty="easy",
            type="short_answer",
            stem=f"Q{qnum}",
            answer_scheme=AnswerSchemeSchema(
                total_marks=2,
                marking_points=points,
                model_answer=reference,
                metadata={"objective": False},
            ),
            estimated_time_minutes=2,
            marks=2,
            source="teacher_created",
            created_at=now,
            updated_at=now,
        )
    return questions


def load_teacher_marks(csv_path: Path) -> dict[int, dict[int, float | None]]:
    """student_no -> {qnum: teacher mark or None for blank/not-corrected}."""
    out: dict[int, dict[int, float | None]] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = (row.get("Student_ID") or "").strip()
            if not sid or not sid.startswith("Student_"):
                continue
            no = int(sid.split("_")[1])
            marks: dict[int, float | None] = {}
            for q in range(21, 36):
                raw = (row.get(str(q)) or "").strip()
                if raw in NO_MARK_TOKENS:
                    marks[q] = None
                else:
                    try:
                        marks[q] = float(raw)
                    except ValueError:
                        marks[q] = None
            out[no] = marks
    return out


def page_markers(page: vision.PageOCR) -> list[int]:
    """Question numbers recoverable from a page's OCR text (same regex the
    real segmenter uses) -- used to detect foreign-exam pages."""
    text = scan._HTML_TAG.sub("", page.text or "")
    return [int(m.group(1)) for m in scan._Q_MARKER.finditer(text)]


@dataclass
class StudentResult:
    student_no: int
    pages: list[vision.PageOCR]
    segments: list[scan.AnswerSegment]
    foreign_pages: list[int]  # 1-based page indices flagged as another exam
    per_question: dict[int, str]  # qnum -> segment text ('' if none)


def _ocr_cached(page_path: Path, page_no: int, *, workdir: Path,
                cache: dict, do_ocr: bool) -> vision.PageOCR:
    key = f"{page_path.stem}:{page_no}"
    if do_ocr:
        ocr = vision.ocr_page(page_path, page_no, workdir=workdir / "ocr",
                              crop_furniture=False)
        cache[key] = {"text": ocr.text, "warnings": ocr.warnings,
                      "hallucinated": ocr.hallucinated}
    else:
        entry = cache.get(key)
        if entry is None:
            return vision.PageOCR(page_no=page_no, text="",
                                  warnings=["OCR not run for this page"])
        ocr = vision.PageOCR(page_no=page_no, text=entry["text"],
                             warnings=list(entry.get("warnings", [])),
                             hallucinated=entry.get("hallucinated", False))
    return ocr


def process_student(student_no: int, pdf: Path, *, workdir: Path,
                    cache: dict, do_ocr: bool) -> StudentResult:
    pages_dir = workdir / "pages"
    page_paths = scan.render_pdf_pages(pdf, pages_dir, dpi=200)
    page_ocrs: list[vision.PageOCR] = []
    for i, p in enumerate(page_paths):
        page_no = i + 1
        try:
            page_ocrs.append(_ocr_cached(p, page_no, workdir=workdir, cache=cache, do_ocr=do_ocr))
        except Exception as exc:
            log.warning("OCR failed on page %s of student %s: %s", page_no, student_no, exc)
            page_ocrs.append(vision.PageOCR(page_no=page_no, text="",
                                            warnings=[f"OCR failed: {exc}"]))
    # Flag pages that belong to a different exam: any question number > 35
    # cannot be part of this 35-question paper.
    foreign = [p.page_no for p in page_ocrs
               if any(m > 35 for m in page_markers(p))]
    real_pages = [p for p in page_ocrs if p.page_no not in foreign]
    segments = scan.segment_answers(real_pages)
    by_no = {s.question_no: s.text for s in segments}
    per_question = {q: (by_no.get(q) or "") for q in range(21, 36)}
    return StudentResult(student_no=student_no, pages=page_ocrs,
                         segments=segments, foreign_pages=foreign,
                         per_question=per_question)


def evaluate_student(questions: dict[int, QuestionSchema],
                     result: StudentResult) -> dict[int, object]:
    """Run the real evaluate_answer() per question on the segmented text."""
    out: dict[int, object] = {}
    for q in range(21, 36):
        text = result.per_question[q]
        q_schema = questions[q]
        if not text.strip():
            text = ""  # no segment recovered -> evaluate blank
        out[q] = evaluate_answer(q_schema, q_schema.answer_scheme, text)
    return out


def report(students: list[StudentResult], teacher: dict[int, dict[int, float | None]],
           evals: dict[int, dict[int, object]], questions: dict[int, QuestionSchema],
           *, naive_evals: dict[int, dict[int, object]]) -> None:
    n_students = len(students)
    if not n_students:
        print("No students processed.")
        return

    total = exact_all = exact_int = within1 = 0
    total_int = 0
    teacher_ints = 0
    abs_diffs: list[float] = []
    needs_review = 0
    ocr_warned = 0
    seg_missing = 0
    foreign_pages = 0
    per_q_tot = {q: [0, 0, 0, 0] for q in range(21, 36)}  # exact, within1, count, intcount

    def cmp_pair(eval_res, tmark):
        nonlocal total, exact_all, exact_int, within1, total_int, abs_diffs
        engine = eval_res.awarded_marks
        if tmark is None:
            return
        total += 1
        diff = abs(engine - tmark)
        abs_diffs.append(diff)
        if engine == tmark:
            exact_all += 1
        if diff <= 1:
            within1 += 1
        if tmark == int(tmark) and tmark == int(tmark):
            total_int += 1
            teacher_ints_holder = 0
            if engine == tmark:
                exact_int += 1
        per_q_tot[q][1] += 1
        if engine == tmark:
            per_q_tot[q][0] += 1
        if diff <= 1:
            per_q_tot[q][1] += 0  # no-op; see below
        if tmark == int(tmark):
            per_q_tot[q][3] += 1

    for s in students:
        foreign_pages += len(s.foreign_pages)
        for q in range(21, 36):
            ev = evals[s.student_no][q]
            tmark = teacher[s.student_no][q]
            if not s.per_question[q].strip():
                seg_missing += 1
            if ev.needs_review:
                needs_review += 1
            if ev.ocr_warnings:
                ocr_warned += 1
            cmp_pair(ev, tmark)

    print(f"\n=== Short-answer calibration: {n_students} real students, "
          f"real Sarvam OCR + real segmentation + real evaluate_answer ===")
    print(f"Questions: Q21-Q35 (2 marks each), marking points from answerkey.txt.")
    print(f"Foreign-exam pages detected and excluded from segmentation: {foreign_pages}")
    print(f"Question-answers with no recovered segment (evaluated blank): {seg_missing}")

    if total:
        print(f"\nPer-question agreement, engine-awarded == teacher-awarded:")
        print(f"  exact (all teacher marks):     {exact_all}/{total} "
              f"({100 * exact_all / total:.1f}%)")
        print(f"  within 1 mark (tolerance):      {within1}/{total} "
              f"({100 * within1 / total:.1f}%)")
    if total_int:
        print(f"  exact, integer teacher marks only: {exact_int}/{total_int} "
              f"({100 * exact_int / total_int:.1f}%)")
    if abs_diffs:
        mad = sum(abs_diffs) / len(abs_diffs)
        print(f"Mean absolute difference (per question, out of 2): {mad:.3f}")
    print(f"Evaluations flagged needs_review (conf < 0.75 or OCR risk): "
          f"{needs_review}/{n_students * 15}")
    print(f"Evaluations with OCR-risk warnings: {ocr_warned}")

    print(f"\nPer-question breakdown (exact / within-1 / scored / integer-teacher):")
    for q in range(21, 36):
        t = per_q_tot[q]
        if t[2]:
            print(f"  Q{q}: {t[0]}/{t[2]} exact ({100 * t[0] / t[2]:.0f}%), "
                  f"within-1 {100 * t[1] / t[2]:.0f}%, "
                  f"n={t[2]}, int-teacher n={t[3]}")
        else:
            print(f"  Q{q}: no scored instances")

    print(f"\nStudents (engine total vs teacher total, out of 30):")
    print(f"  {'Student':<10}{'pages':<6}{'foreign':<8}{'seg':<5}"
          f"{'engine':<8}{'teacher':<8}{'abs-diff'}")
    for s in students:
        eng = sum(evals[s.student_no][q].awarded_marks for q in range(21, 36))
        tsum = sum(v for v in teacher[s.student_no].values() if v is not None)
        nseg = sum(1 for q in range(21, 36) if s.per_question[q].strip())
        ad = abs(eng - tsum)
        flag = "  <-- mismatch" if ad > 0 else ""
        print(f"  {s.student_no:<10}{len(s.pages):<6}{len(s.foreign_pages):<8}"
              f"{nseg:<5}{eng:<8}{tsum:<8}{ad:.1f}{flag}")

    print(f"\nNOTE on naive (unfiltered) run, i.e. grading foreign pages too:")
    naive_mismatch = 0
    for s in students:
        eng_naive = sum(naive_evals[s.student_no][q].awarded_marks for q in range(21, 36))
        tsum = sum(v for v in teacher[s.student_no].values() if v is not None)
        if abs(eng_naive - tsum) != abs(
                sum(evals[s.student_no][q].awarded_marks for q in range(21, 36)) - tsum):
            naive_mismatch += 1
    print(f"  students whose total changed when foreign pages were graded: "
          f"{naive_mismatch}/{n_students}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR)
    ap.add_argument("--students", type=str, default="1-15",
                    help="range of student numbers, e.g. '1-15' or '1,2,5'")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel OCR workers (Sarvam jobs are async; 4-6 is safe)")
    ap.add_argument("--workdir", type=Path,
                    default=Path(r"C:\Users\varsh\AppData\Local\Temp\opencode\mendeley_short_answer"))
    ap.add_argument("--resume", action="store_true",
                    help="reuse cached OCR text instead of re-billing Sarvam")
    ap.add_argument("--max-students", type=int, default=None,
                    help="if set, cap students at this many")
    args = ap.parse_args()

    logging.basicConfig(level=logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    data_dir: Path = args.data_dir
    pdf_dir = data_dir / "Student_Pdf"
    marks_csv = data_dir / "Teacher_manual_marks_Anonymized.csv"
    if not pdf_dir.exists() or not marks_csv.exists():
        print(f"Dataset not found at {data_dir}", file=sys.stderr)
        sys.exit(1)

    nums: list[int] = []
    for part in args.students.split(","):
        if "-" in part:
            lo, hi = part.split("-")
            nums.extend(range(int(lo), int(hi) + 1))
        elif part:
            nums.append(int(part))
    nums = sorted(set(nums))
    if args.max_students:
        nums = nums[: args.max_students]

    questions = build_questions()
    teacher = load_teacher_marks(marks_csv)
    print(f"Loaded {len(questions)} short-answer questions, "
          f"{len(teacher)} students' teacher marks.")

    workdir = args.workdir
    workdir.mkdir(parents=True, exist_ok=True)
    cache_path = workdir / "ocr_cache.json"
    cache: dict = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"Resumed OCR cache with {len(cache)} pages.")
        except json.JSONDecodeError:
            log.warning("could not read OCR cache, starting fresh")

    do_ocr = not args.resume
    if do_ocr:
        print(f"Running real Sarvam Vision OCR on {len(nums)} students "
              f"({args.workers} workers)...")

    def run_one(n: int) -> StudentResult:
        pdf = pdf_dir / f"Student_{n}.pdf"
        if not pdf.exists():
            return StudentResult(student_no=n, pages=[], segments=[],
                                 foreign_pages=[], per_question={q: "" for q in range(21, 36)})
        return process_student(n, pdf, workdir=workdir, cache=cache, do_ocr=do_ocr)

    results: list[StudentResult] = []
    t0 = time.monotonic()
    if do_ocr and args.workers > 1 and len(nums) > 1:
        with futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            for res in ex.map(run_one, nums):
                results.append(res)
    else:
        for n in nums:
            results.append(run_one(n))
    if do_ocr:
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        print(f"OCR complete in {time.monotonic() - t0:.0f}s; "
              f"cache written to {cache_path}")

    results = [r for r in results if r.pages]
    if not results:
        print("No pages were processed.", file=sys.stderr)
        sys.exit(1)

    evals = {r.student_no: evaluate_student(questions, r) for r in results}
    # Naive pass: segment everything including foreign pages, to show impact.
    naive_evals = {}
    for r in results:
        naive = scan.segment_answers(r.pages)
        by_no = {s.question_no: s.text for s in naive}
        pq = {q: (by_no.get(q) or "") for q in range(21, 36)}
        ev = {}
        for q in range(21, 36):
            q_schema = questions[q]
            ev[q] = evaluate_answer(q_schema, q_schema.answer_scheme, pq[q])
        naive_evals[r.student_no] = ev

    report(results, teacher, evals, questions, naive_evals=naive_evals)


if __name__ == "__main__":
    main()