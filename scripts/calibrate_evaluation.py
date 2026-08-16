"""Real accuracy calibration for the deterministic evaluation engine
(src/academicos/assessment/evaluate.py -- the same module the Dart port in
frontend/lib/core/local_engine/answer_evaluation.dart mirrors), run against
a real, public, teacher-graded dataset:

  "A Dataset of Digitized Student Examination Papers, Answer Keys, and
  Manual Evaluations for Automated Grading Research" -- Dinesh K P,
  Anna University, Chennai. CC BY 4.0. https://doi.org/10.17632/sf3kvjwknt.1

This is NOT a CBSE Class X Science/Maths dataset -- it's a university Data
Science exam. It calibrates the *mechanism* (does the objective-question
scoring engine agree with a real human grader on real student responses),
not CBSE-specific subject accuracy. Don't cite this as a CBSE accuracy
number; cite it as evidence the scoring pipeline itself is sound.

MCQ path only: the CSV gives each student's selected option letter and the
teacher's recorded aggregate MCQ mark, both real, no OCR needed. The
short-answer path (Q21-35) needs OCR text extraction from the raw PDFs
first -- not attempted here; see the bottom of this file for what that
would take.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from academicos.assessment.evaluate import evaluate_answer
from academicos.assessment.schemas import AnswerSchemeSchema, MarkingPointSchema, QuestionSchema
from datetime import datetime, timezone

DATA_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"C:\Users\varsh\AppData\Local\Temp\claude\C--Users-varsh-OneDrive-Documents-Sarvam"
    r"\7de05406-7bc4-4b11-8a62-4c7aca496926\scratchpad\mendeley_data"
    r"\A Dataset of Digitized Student Examination Papers,"
)


def load_mcq_key(answerkey_path: Path) -> dict[int, str]:
    key = {}
    with open(answerkey_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Type"] == "MCQ":
                key[int(row["Question_Number"])] = row["Correct_Answer"].strip()
    return key


def build_mcq_question(qnum: int, correct: str) -> QuestionSchema:
    now = datetime.now(timezone.utc)
    return QuestionSchema(
        id=f"mendeley:mcq:{qnum}",
        question_bank_id="mendeley-calibration",
        subject="Data Science",
        grade=0,
        bloom_level="remember",
        difficulty="easy",
        type="mcq",
        stem=f"MCQ {qnum}",
        answer_scheme=AnswerSchemeSchema(
            total_marks=1,
            marking_points=[MarkingPointSchema(
                id=f"mendeley:mcq:{qnum}:mp1", description=f"Correct option {correct}",
                marks=1, keyword=correct,
            )],
            metadata={"objective": True, "correctOption": correct},
        ),
        estimated_time_minutes=1,
        marks=1,
        source="teacher_created",
        created_at=now, updated_at=now,
    )


def main() -> None:
    answerkey = DATA_DIR / "answerkey.txt"
    marks_csv = DATA_DIR / "Teacher_manual_marks_Anonymized.csv"
    if not answerkey.exists() or not marks_csv.exists():
        print(f"Dataset not found at {DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    mcq_key = load_mcq_key(answerkey)
    print(f"Loaded {len(mcq_key)} MCQ answer keys.")

    questions = {q: build_mcq_question(q, ans) for q, ans in mcq_key.items()}

    total_students = 0
    engine_totals = []
    teacher_totals = []
    per_question_agree = 0
    per_question_total = 0
    exact_total_match = 0

    with open(marks_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("Student_ID"):
                continue
            total_students += 1
            teacher_mcq_mark = float(row["MCQ mark"])
            engine_sum = 0
            for qnum in range(1, 21):
                selected = (row.get(str(qnum)) or "").strip()
                if not selected:
                    continue
                q = questions[qnum]
                result = evaluate_answer(q, q.answer_scheme, f"({selected})")
                engine_sum += result.awarded_marks
                # Per-question ground truth: did the engine's correctness
                # verdict match what the answer key implies? (independent
                # check, not derived from the teacher's aggregate number)
                implied_correct = selected.upper() == mcq_key[qnum].upper()
                engine_correct = result.awarded_marks == 1
                per_question_total += 1
                if implied_correct == engine_correct:
                    per_question_agree += 1

            engine_totals.append(engine_sum)
            teacher_totals.append(teacher_mcq_mark)
            if engine_sum == teacher_mcq_mark:
                exact_total_match += 1

    print(f"\n=== Calibration: {total_students} real students, real teacher marks ===")
    print(f"Per-question verdict agreement with the answer key: "
         f"{per_question_agree}/{per_question_total} "
         f"({100 * per_question_agree / per_question_total:.2f}%)")
    print(f"Engine's summed MCQ score == teacher's recorded MCQ mark: "
         f"{exact_total_match}/{total_students} students "
         f"({100 * exact_total_match / total_students:.2f}%)")

    diffs = [e - t for e, t in zip(engine_totals, teacher_totals)]
    mean_abs_diff = sum(abs(d) for d in diffs) / len(diffs)
    print(f"Mean absolute difference (engine total vs teacher total), out of 20: "
         f"{mean_abs_diff:.3f}")
    mismatches = [(i + 1, e, t) for i, (e, t) in enumerate(zip(engine_totals, teacher_totals)) if e != t]
    if mismatches:
        print(f"\n{len(mismatches)} students where engine and teacher totals differ:")
        for student_num, e, t in mismatches[:10]:
            print(f"  Student_{student_num}: engine={e}, teacher={t}, diff={e - t}")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# What it would take to extend this to the short-answer questions (Q21-35),
# NOT attempted here:
#   1. OCR each Corrected_Pdf/Student_N.pdf (or Student_Pdf/ for the raw,
#      un-annotated version) to extract the actual handwritten response text
#      per question -- this dataset does not include transcribed text, only
#      the scanned PDFs and the teacher's final numeric marks.
#   2. Run evaluate_answer() with a *descriptive* AnswerSchemeSchema built
#      from answerkey.txt's Short_Answer entries (keyword-extract marking
#      points from the reference answer text, same as marking.py does for
#      real CBSE marking schemes).
#   3. Compare the engine's per-question mark to the CSV's real per-question
#      column (columns "21".."35" in Teacher_manual_marks_Anonymized.csv).
# This is the harder, more valuable half -- descriptive-answer grading is
# exactly where automated scoring is least trustworthy -- and needs either
# Sarvam Vision (network, cost) or a local OCR pass (tesseract, already a
# parse_priority fallback in this codebase) to get real transcribed text.
