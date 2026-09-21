# Question-Bank Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve CBE and SQP questions alongside board papers so teachers of classes 6–9 can generate correct papers, without breaking the offline Android app or any paper that works today.

**Architecture:** A pure composition module (`corpus/bank_merge.py`) normalises CBE/SQP records to the phone's strict `Question.fromJson` contract, excludes anything that cannot be answered or rendered, and passes board records through untouched. A script writes the served bank and its byte-identical APK copy. Around it, one grade module replaces three inconsistent grade conversions, the web pool stops discarding the record it loaded, the web PDF stops crashing on long or many-option items, and the phone loader stops failing the whole corpus on one bad row.

**Tech Stack:** Python 3.12 (FastAPI, Pydantic v2, ReportLab 5.0, pytest), Flutter 3.44 / Dart 3.12.

**Spec:** `docs/superpowers/specs/2026-09-21-question-bank-merge-design.md`

---

## Ground rules for every task

- Run Python as `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe` from the repo root.
- Work in `src/academicos/`, never `backend/`.
- **Only run your own task's tests.** Other tasks may be mid-edit in the same tree; the full suite is run between waves by the coordinator.
- Scripts that overwrite tracked data (`build_cbe_bank.py`, `build_sqp_bank.py`, `apply_chapter_tags.py`, `map_topics.py`, `enrich_question_bank.py`, `merge_question_banks.py`) are run for real **only in Task 11**. Everywhere else, `--check` or temp paths.
- Do not commit. The coordinator commits after each wave.
- Match the surrounding code's style: explanatory module/function docstrings that say *why*, measured numbers in comments where they justify a rule.

## File map

| File | Status | Responsibility | Task |
|---|---|---|---|
| `src/academicos/assessment/grades.py` | create | The one grade parser: int/roman/"7th" → 1–12 | 1 |
| `src/academicos/assessment/routes.py` | modify | grade key, export error handling | 2, 7 |
| `src/academicos/assessment/pillar_routes.py` | modify | grade key, catalog scope, practice grade validated | 2 |
| `src/academicos/assessment/mobile_routes.py` | modify | grade key; unknown assessment refused, not class 10 | 2 |
| `src/academicos/assessment/pool.py` | modify | grade match + labels + pool key; fallback keeps the record | 2, 6 |
| `src/academicos/assessment/mapping.py` | modify | grade parse; build schema from the record | 2, 6 |
| `src/academicos/corpus/cbse_cbe.py` | modify | bank record carries the passage | 3 |
| `src/academicos/corpus/bank_merge.py` | create | contract, normalise, gate, compose | 4 |
| `scripts/merge_question_banks.py` | create | reads sources, writes served + APK + exclusions | 5 |
| `src/academicos/assessment/pdf.py` | modify | labels, row split, type-gated options, unicode | 7 |
| `src/academicos/assessment/schemas.py` | modify | paper-request grades required; `GeneratedQuestionSchema.type` | 2, 7 |
| `src/academicos/assessment/question_bank.py` | modify | relink report counts carried schemes | 8 |
| `scripts/export_mobile_corpus.py` | modify | retired as a writer | 8 |
| `frontend/lib/core/local_engine/corpus_repository.dart` | modify | skip and count bad rows | 9 |
| `frontend/lib/core/local_engine/answer_evaluation.dart` | modify | unscorable → needs review | 10 |
| `frontend/lib/core/local_engine/local_api_client.dart` | modify | Quick Paper: same grade only, fill every section | 13 |
| `frontend/lib/presentation/syllabus/pages/syllabus_page.dart` | modify | stop claiming every question is a board paper | 13 |

## Waves

```
Wave A (parallel, disjoint files):  1  3  4  9  10  13
Wave B:                             2        (needs 1)
Wave C (parallel):                  6  7  5  (6 needs 2; 7 needs 2; 5 needs 4)
Wave D (parallel):                  8  14    (both need 5)
Wave E:                             11 then 12
```

---

### Task 1: One grade parser

**Files:**
- Create: `src/academicos/assessment/grades.py`
- Test: `tests/test_grades.py`

The web path converts grades three incompatible ways (spec §4). This module is the single replacement, and it **raises** on a grade it cannot read instead of defaulting to 10.

- [ ] **Step 1: Write the failing test**

```python
"""The one grade parser. See src/academicos/assessment/grades.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.assessment import grades  # noqa: E402


@pytest.mark.parametrize("raw,expected", [
    (6, 6), (7, 7), (10, 10), (12, 12),
    ("6", 6), ("9", 9), ("12", 12),
    ("VI", 6), ("vii", 7), ("VIII", 8), ("IX", 9), ("X", 10), ("XII", 12),
    ("7th", 7), ("1st", 1), ("2nd", 2), ("3rd", 3), ("10th", 10),
    ("Class 7", 7), ("Grade IX", 9), (" 8 ", 8),
])
def test_to_int_reads_every_shape_the_code_uses(raw, expected):
    assert grades.to_int(raw) == expected


@pytest.mark.parametrize("raw", [0, 13, -1, "", "XIII", "abc", None, True, 7.5])
def test_to_int_refuses_what_is_not_a_school_grade(raw):
    assert grades.to_int(raw) is None


@pytest.mark.parametrize("raw,expected", [
    (6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX"), (10, "X"), (11, "XI"), (12, "XII"),
    ("9", "IX"), ("IX", "IX"),
])
def test_to_roman(raw, expected):
    assert grades.to_roman(raw) == expected


def test_to_roman_raises_rather_than_defaulting_to_ten():
    """The bug this replaces: `romans.get(grade, "X")` turned 6 and 7 into 10."""
    with pytest.raises(ValueError):
        grades.to_roman(13)


@pytest.mark.parametrize("a,b,expected", [
    ("IX", "9", True), ("9", "IX", True), ("VIII", 8, True), ("X", "10th", True),
    ("X", "9", False), ("VI", "VII", False), ("X", "junk", False), ("junk", "junk", False),
])
def test_matches_compares_as_integers(a, b, expected):
    assert grades.matches(a, b) is expected
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_grades.py -q`
Expected: collection error, `cannot import name 'grades'`.

- [ ] **Step 3: Implement**

```python
"""The one place a school grade is parsed.

Before this module the web paper path converted grades three incompatible ways,
and each hid the others' bugs:

  * `routes._int_grade_to_roman` knew only 8-12 and defaulted to "X", so a class
    6 or 7 request silently became class 10 -- a class 7 teacher got a class 10
    board paper printed "Class: 7".
  * the baked-bank loader labelled items 6-9 as "6".."9", while `_grade_matches`
    knew only "10", so class 8 and 9 requests ("VIII", "IX") matched nothing.
  * `mapping.grade_to_int` defaulted to 10 on anything it did not know, so a
    class 9 question reported itself as class 10.

Every caller now goes through here. A grade that cannot be read is refused
(`None` / `ValueError`), never defaulted: a wrong grade is worse than an error,
because nothing downstream can tell it was wrong.
"""
from __future__ import annotations

import re

_ROMAN = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")
_BY_ROMAN = {r: i for i, r in enumerate(_ROMAN) if r}
_PREFIX = re.compile(r"^(?:CLASS|GRADE|STD)\s*")
_ORDINAL = re.compile(r"(?<=\d)(?:ST|ND|RD|TH)$")


def to_int(grade: object) -> int | None:
    """1-12 from an int, a digit string, a roman numeral, "7th" or "Class 7"."""
    if isinstance(grade, bool):
        return None
    if isinstance(grade, int):
        return grade if 1 <= grade <= 12 else None
    if not isinstance(grade, str):
        return None
    s = _ORDINAL.sub("", _PREFIX.sub("", grade.strip().upper())).strip()
    if s.isascii() and s.isdigit():
        n = int(s)
        return n if 1 <= n <= 12 else None
    return _BY_ROMAN.get(s)


def to_roman(grade: object) -> str:
    """The roman numeral a pool is keyed by. Raises on an unreadable grade."""
    n = to_int(grade)
    if n is None:
        raise ValueError(f"not a school grade (1-12): {grade!r}")
    return _ROMAN[n]


def matches(a: object, b: object) -> bool:
    """True when both sides name the same grade, whatever form each is in."""
    na = to_int(a)
    return na is not None and na == to_int(b)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_grades.py -q`
Expected: all pass.

---

### Task 2: Route every grade through the one parser

**Files:**
- Modify: `src/academicos/assessment/routes.py` (`_int_grade_to_roman`, ~line 221; the unreachable `else 10` in `generate_paper` ~268, Step 7)
- Modify: `src/academicos/assessment/pillar_routes.py` (`_GRADE_ROMAN`, `_CATALOG_SCOPE`, `catalog`, `catalog_chapters`, ~lines 218-265; `_pool_questions` ~116 and `PracticeRequestBody.grade` ~735, Step 7)
- Modify: `src/academicos/assessment/mobile_routes.py` (lines 169 and 256 call `_int_grade_to_roman`, which the routes.py change fixes; `create_scan_session` ~84 refuses an unknown assessment instead of defaulting to Science class 10, Step 7)
- Modify: `src/academicos/assessment/pool.py` (`_grade_matches` ~336; baked loader grade label ~587-588; `get_pool`/`build_pool` normalise the grade and drop the `"X"` default; the registry query compares grades through grades.py, Step 7)
- Modify: `src/academicos/assessment/mapping.py` (`grade_to_int` ~24)
- Modify: `src/academicos/assessment/schemas.py` (`QuickPaperRequest.grade` ~370 and `GenerateFromIdsRequest.grade` ~385 become required, Step 7)
- Test: `tests/test_grade_routing.py`

**Depends on:** Task 1.

- [ ] **Step 1: Write the failing test**

```python
"""Grades 6-9 must reach the web paper path, and an unreadable grade must fail loudly.

Production has no registry.sqlite, so every web request takes build_pool's
baked-bank fallback. These tests drive that fallback with a temporary bank.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.assessment import mapping, pool as pool_module, routes  # noqa: E402
from academicos.assessment.pool import _grade_matches  # noqa: E402
# A complete record, so this test keeps passing after Task 6 makes the web path
# validate the whole record as a QuestionSchema. test_bank_merge exists after wave A.
from test_bank_merge import board  # noqa: E402


@pytest.mark.parametrize("grade,roman", [(6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX"),
                                         (10, "X"), (12, "XII")])
def test_route_grade_key_covers_six_to_twelve(grade, roman):
    assert routes._int_grade_to_roman(grade) == roman


@pytest.mark.parametrize("bad", [0, 13, 99])
def test_route_grade_key_refuses_instead_of_defaulting_to_ten(bad):
    with pytest.raises(HTTPException) as exc:
        routes._int_grade_to_roman(bad)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("pool_grade,requested,expected", [
    ("IX", "IX", True), ("VIII", "8", True), ("VI", "6th", True),
    ("X", "IX", False), ("X", "10", True), ("XII", "XII", True),
])
def test_pool_grade_match(pool_grade, requested, expected):
    assert _grade_matches(pool_grade, requested) is expected


@pytest.mark.parametrize("label,expected", [("IX", 9), ("9", 9), ("VI", 6), ("X", 10), ("XII", 12)])
def test_mapping_grade_to_int(label, expected):
    assert mapping.grade_to_int(label) == expected


def test_mapping_grade_to_int_refuses_junk():
    with pytest.raises(ValueError):
        mapping.grade_to_int("junk")


def _bank(tmp_path: Path, grade: int) -> Path:
    rec = board(id=f"cbe:q:T{grade}", subject="Mathematics", grade=grade,
                source="cbse_question_bank",
                stem="Find the value of 2 + 3 and explain each step you take.")
    p = tmp_path / "syllabus" / "questions.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"questions": [rec]}), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("grade,roman", [(6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX")])
def test_baked_fallback_serves_class_six_to_nine(tmp_path, monkeypatch, grade, roman):
    from academicos.config import Config

    data_root = _bank(tmp_path, grade)
    cfg = Config(data_root=data_root)
    cfg._load_baked_questions = True
    # Point every candidate path the fallback tries at the temp bank only.
    monkeypatch.setattr(pool_module, "_baked_bank_paths",
                        lambda cfg: [data_root / "syllabus" / "questions.json"])
    built = pool_module.build_pool(cfg, subject="Mathematics", grade=roman)
    assert [q.grade for q in built.questions] == [roman]
    schema = mapping.to_question_schema(built.questions[0])
    assert schema.grade == grade
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_grade_routing.py -q`
Expected: failures — `_int_grade_to_roman(6)` returns `"X"`; `_grade_matches("IX","IX")`… etc.; `_baked_bank_paths` does not exist.

- [ ] **Step 3: Implement**

In `routes.py`, replace `_int_grade_to_roman`:

```python
def _int_grade_to_roman(grade: int) -> str:
    """Pool key for a request's grade. An unreadable grade is a 422, never class 10.

    This used to be `{8: "VIII", ..., 12: "XII"}.get(grade, "X")`, which turned a
    class 6 or 7 request into class 10 without saying so. See grades.py.
    """
    try:
        return grades.to_roman(grade)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
```

and add `from . import grades` with the other relative imports. `mobile_routes.py` already calls this function, so it is fixed by this change.

In `pool.py`, replace `_grade_matches`:

```python
def _grade_matches(pool_grade: str, requested_grade: str) -> bool:
    """Same grade, whatever form each side is in -- 'IX', '9', '9th'. See grades.py."""
    return grades.matches(pool_grade, requested_grade)
```

and in the baked-bank loader replace the grade-label line

```python
item_grade_roman = "X" if item_grade_int == 10 else ("XII" if item_grade_int == 12 else str(item_grade_int))
```

with

```python
try:
    item_grade_roman = grades.to_roman(item.get("grade"))
except ValueError:
    continue            # a record with no readable grade cannot be served to any class
```

Also extract the fallback's `candidates_paths` list into a module-level function so tests (and Task 6) can point it at one file:

```python
def _baked_bank_paths(cfg: Config) -> list[Path]:
    """Where the baked-in bank may live, in the order it is tried."""
    root = Path(__file__).parents[3]
    return [
        root / "academicos-data" / "syllabus" / "questions.json",
        root / "academicos-data" / "questions.json",
        root / "frontend" / "assets" / "corpus" / "questions.json",
        cfg.data_root / "questions.json",
        cfg.data_root / "syllabus" / "questions.json",
    ]
```

and use `for p in _baked_bank_paths(cfg):` in the loader. Add `from . import grades` to pool.py's imports.

In `mapping.py`, replace `grade_to_int`:

```python
def grade_to_int(grade: str) -> int:
    """The int grade for a pool label. Raises on junk rather than returning 10.

    `_ROMAN_GRADE.get(g, 10)` made "9" -- the label the baked loader used for
    class 9 -- report itself as class 10. See grades.py.
    """
    n = grades.to_int(grade)
    if n is None:
        raise ValueError(f"not a school grade: {grade!r}")
    return n
```

and add `from . import grades`. Delete `_ROMAN_GRADE` if nothing else uses it (`grep -n _ROMAN_GRADE src/`).

In `pillar_routes.py`: delete `_GRADE_ROMAN`; replace each `_GRADE_ROMAN.get(grade, "X")` with `routes_grade_key(grade)` where

```python
def routes_grade_key(grade: int) -> str:
    from .routes import _int_grade_to_roman
    return _int_grade_to_roman(grade)
```

(or import `_int_grade_to_roman` directly at module top if that creates no cycle — check with a plain `import academicos.assessment.pillar_routes`). Replace the hard-coded `_CATALOG_SCOPE` with a scope derived from the served bank:

```python
def _catalog_scope(cfg) -> list[tuple[str, int]]:
    """Every (subject, grade) the served bank holds.

    This was a hand-written list of grade 10 and 12 pairs, so class 6-9 never
    appeared in the catalog however many questions existed for them.
    """
    from .pool import _baked_bank_paths

    for path in _baked_bank_paths(cfg):
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            pairs = {(q.get("subject", ""), grades.to_int(q.get("grade")))
                     for q in data.get("questions", [])}
            return sorted((s, g) for s, g in pairs if s and g)
    return []
```

and iterate `for subject, grade in _catalog_scope(cfg):` in `catalog`. Add a test to `tests/test_grade_routing.py`:

```python
def test_catalog_scope_includes_every_grade_in_the_bank(tmp_path, monkeypatch):
    from academicos.assessment import pillar_routes
    from academicos.config import Config

    data_root = _bank(tmp_path, 7)
    monkeypatch.setattr(pool_module, "_baked_bank_paths",
                        lambda cfg: [data_root / "syllabus" / "questions.json"])
    assert pillar_routes._catalog_scope(Config(data_root=data_root)) == [("Mathematics", 7)]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_grade_routing.py tests/test_grades.py tests/test_assessment_pool.py -q`
Expected: all pass. If `Question` is not importable from `academicos.domain`, find it with `grep -rn "^class Question\b" src/academicos` and fix the import.

#### Review amendments (added 2026-09-21 after the Task 1 review)

Steps 1-4 fix the three grade *conversions*. The review found grade handling that still skips `grades.py` or still defaults to 10 once they land. Steps 5-8 close those paths. Each fix below was prototyped against a scratch copy of `e1c5655`: the new tests fail there for the stated reasons and pass with the code shown, and the existing test files listed in Step 8 show no new failures.

What is wrong today:

- **A client-supplied grade string reaches the pool unvalidated.** `PracticeRequestBody.grade: str = "X"` (pillar_routes.py ~735) → `_pool_questions` → `get_pool`, which caches under the raw string, → the baked loader's `_grade_matches`. A junk grade matches nothing, so the pool is empty and `/practice/generate` returns "No auto-scorable practice available" warnings (remediation.py ~109) where it should return a 422. And `'X'`, `'10'` and `'10th'` are three `_CACHE` keys, each of which builds a full pool.
- **The registry query compares grades as raw strings.** pool.py ~436: `... AND grade=?`. In `registry.sqlite`, `sources.grade` is `'6'`..`'9'` for classes 6-9 but `'X'`/`'XII'` for 10 and 12. *Measured, 2026-09-21:* the 14 class 6-9 rows there are NCERT textbooks (`doc_type='reference_material'`), not question papers. So the `doc_type='question_paper'` query returns no class 6-9 rows before or after this task, and nothing regresses today. But a class 8 paper registered as `'8'` would never match the pool key `'VIII'`, so the comparison still goes through `grades.py`.
- **Defaults to class 10 that remain after Steps 1-4:** `QuickPaperRequest.grade: int = 10` and `GenerateFromIdsRequest.grade: int = 10` (schemas.py ~370, ~385). A request that leaves out the grade gets a class 10 paper. Another is `create_scan_session`'s `grade = assessment.grade if assessment else 10` (mobile_routes.py ~88), and there are `grade: str = "X"` defaults on `build_pool`, `get_pool` and `_pool_questions`. The baked loader's `item_grade_int = item.get("grade", 10)` (pool.py ~587) is covered by the Step 3 replacement: delete that line together with the label line.

- [ ] **Step 5: Write the failing tests.** Append the tests below to `tests/test_grade_routing.py`, and add `import sqlite3` and `from pydantic import ValidationError` to its imports:

```python
def test_get_pool_normalises_the_grade_before_caching(tmp_path, monkeypatch):
    """'X', '10' and '10th' are one pool, built once -- not three cache entries."""
    from academicos.config import Config

    data_root = _bank(tmp_path, 10)
    cfg = Config(data_root=data_root)
    cfg._load_baked_questions = True
    monkeypatch.setattr(pool_module, "_baked_bank_paths",
                        lambda cfg: [data_root / "syllabus" / "questions.json"])
    monkeypatch.setattr(pool_module, "_CACHE", {})
    built: list[str] = []
    real_build = pool_module.build_pool

    def counting_build(cfg, **kw):
        built.append(kw["grade"])
        return real_build(cfg, **kw)

    monkeypatch.setattr(pool_module, "build_pool", counting_build)
    pools = [pool_module.get_pool(cfg, subject="Mathematics", grade=g) for g in ("X", "10", "10th")]
    assert pools[0] is pools[1] is pools[2]
    assert built == ["X"]
    assert [q.grade for q in pools[0].questions] == ["X"]


@pytest.mark.parametrize("bad", ["", "junk", "XIII", "13"])
def test_get_pool_refuses_an_unreadable_grade_and_caches_nothing(tmp_path, monkeypatch, bad):
    from academicos.config import Config

    monkeypatch.setattr(pool_module, "_CACHE", {})
    with pytest.raises(ValueError):
        pool_module.get_pool(Config(data_root=tmp_path), subject="Mathematics", grade=bad)
    assert pool_module._CACHE == {}


@pytest.mark.parametrize("raw", ["X", "10", "10th", "Class 10", 10])
def test_practice_request_normalises_the_grade(raw):
    from academicos.assessment.pillar_routes import PracticeRequestBody

    assert PracticeRequestBody(student_id="s", grade=raw).grade == "X"


@pytest.mark.parametrize("bad", ["junk", "XIII", "0", ""])
def test_practice_request_refuses_an_unreadable_grade(bad):
    """A bad grade is a 422 at the request boundary, not an empty pool that
    comes back as 'no auto-scorable practice' warnings."""
    from academicos.assessment.pillar_routes import PracticeRequestBody

    with pytest.raises(ValidationError):
        PracticeRequestBody(student_id="s", grade=bad)


def test_practice_request_default_is_deliberately_still_class_ten():
    """Intentional, see 'Defaults kept on purpose' below: the shipped app posts only
    studentId and perConcept (pillar_api.dart generatePractice), and a student
    record holds no grade."""
    from academicos.assessment.pillar_routes import PracticeRequestBody

    assert PracticeRequestBody(student_id="s").grade == "X"


@pytest.mark.parametrize("model", ["QuickPaperRequest", "GenerateFromIdsRequest"])
def test_paper_requests_require_a_grade(model):
    """A request with no grade used to become a class 10 paper (`grade: int = 10`)."""
    from academicos.assessment import schemas

    with pytest.raises(ValidationError) as exc:
        getattr(schemas, model).model_validate({"subject": "Mathematics", "questionIds": ["q1"]})
    assert [e["loc"] for e in exc.value.errors()] == [("grade",)]


def test_scan_session_for_an_unknown_assessment_is_refused_not_made_class_ten(monkeypatch):
    """It used to become a Science class 10 session. Every later route on that
    session 404s anyway (require_school_owns_scan_session), so it could never be
    processed -- the default only hid the mistake."""
    from academicos.assessment import mobile_routes
    from academicos.assessment.users import User

    class _NoAssessments:
        def get(self, _id):
            return None

    monkeypatch.setattr(routes, "_store", _NoAssessments())
    user = User(id="t1", school_id="school_1", name="T", email="t@example.com",
                role="teacher", created_at="")
    req = mobile_routes.CreateScanSessionRequest(
        assessment_id="nope", student_id="s1", student_name="S")
    with pytest.raises(HTTPException) as exc:
        mobile_routes.create_scan_session(req, current=user)
    assert exc.value.status_code == 404


def test_registry_query_reads_every_grade_spelling(tmp_path):
    """registry.sqlite's sources.grade holds '6'..'9' for classes 6-9 but 'X' and
    'XII' for 10 and 12 (measured 2026-09-21). A raw `grade=?` against the pool's
    roman key would miss a class 8 paper stored as '8'."""
    from academicos.config import Config

    cfg = Config(data_root=tmp_path)
    cfg.registry_db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(cfg.registry_db)
    con.execute("CREATE TABLE sources (source_id TEXT, doc_type TEXT, subject TEXT, "
                "grade TEXT, academic_year TEXT)")
    con.executemany("INSERT INTO sources VALUES (?,?,?,?,?)", [
        ("qp8", "question_paper", "Mathematics", "8", "2025"),
        ("qp10", "question_paper", "Mathematics", "X", "2025"),
        ("book8", "reference_material", "Mathematics", "8", None),
        ("nograde", "question_paper", "Mathematics", None, "2025"),
    ])
    con.commit()
    con.close()
    rows = pool_module._registry_paper_rows
    assert [r["source_id"] for r in rows(cfg, "Mathematics", "VIII")] == ["qp8"]
    assert [r["source_id"] for r in rows(cfg, "Mathematics", "X")] == ["qp10"]
    assert rows(cfg, "Science", "X") == []
```

(`Config(...)` creates the `registry/` directory itself, which is why the test passes `exist_ok=True`.)

- [ ] **Step 6: Run them to verify they fail**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_grade_routing.py -q`
Expected failures:
  - `get_pool` does not raise on `""`, `"junk"`, `"XIII"` or `"13"`, and caches each spelling separately.
  - `PracticeRequestBody` keeps `"10"` and `"10th"` as they are, accepts junk, and rejects the int `10` as not a string.
  - Both paper requests validate without a grade.
  - `create_scan_session` returns a session instead of raising 404.
  - `_registry_paper_rows` does not exist.

- [ ] **Step 7: Implement**

In `pool.py`:
1. Normalise the grade at the pool boundary and remove the `"X"` default. Every caller passes a grade already (checked with `grep -rn "get_pool(\|build_pool(" src scripts tests`).

```python
def get_pool(cfg: Config, *, subject: str = "Science", grade: str) -> QuestionPool:
    grade = grades.to_roman(grade)   # 'X', '10', '10th' are one pool, built once; raises on junk
    key = (subject, grade)
    ...
```

   At the top of `build_pool`'s body, add `grade = grades.to_roman(grade)` (it is idempotent, and direct callers such as tests and scripts get the same check). Change its signature to `grade: str` with no default. Normalising also retires the baked loader's `if grade and ...` wildcard, where an empty grade meant "all grades". No caller passes an empty grade. `""` now raises.

2. Move the registry query into a helper that compares grades through `grades.py`:

```python
def _registry_paper_rows(cfg: Config, subject: str, grade: str) -> list:
    """The registry's question papers for (subject, grade), whatever spelling
    the registry used for the grade.

    sources.grade holds '6'..'9' for classes 6-9 but 'X' and 'XII' for 10 and
    12 (registry.sqlite, 2026-09-21), so a raw `grade=?` against the pool's
    roman key would miss a class 8 paper stored as '8'. Fetch the subject's
    papers and compare grades through grades.py instead -- at most ~70 rows.
    """
    import sqlite3

    if not cfg.registry_db.exists():
        return []
    try:
        reg = sqlite3.connect(cfg.registry_db)
        reg.row_factory = sqlite3.Row
        # AGENTS.md section 3: every connection sets both pragmas.
        reg.execute("PRAGMA journal_mode=WAL")
        reg.execute("PRAGMA busy_timeout=60000")
        rows = reg.execute(
            "SELECT source_id, doc_type, subject, grade, academic_year FROM sources "
            "WHERE doc_type='question_paper' AND subject=?",
            (subject,),
        ).fetchall()
        reg.close()
    except sqlite3.OperationalError:
        ...  # the existing block from build_pool, moved unchanged: its comment, log.error, raise
    return [r for r in rows if grades.matches(r["grade"], grade)]
```

   In `build_pool`, replace the `rows = []` / `if cfg.registry_db.exists(): try: ... except ...: raise` block with `rows = _registry_paper_rows(cfg, subject, grade)`.

In `pillar_routes.py`:
- Remove the defaults from `_pool_questions`: `def _pool_questions(subject: str, grade: str)`. Its only caller passes both.
- Validate `PracticeRequestBody.grade` when the request arrives, so FastAPI returns a 422 for junk and one spelling reaches the pool:

```python
class PracticeRequestBody(Camel):
    student_id: str
    per_concept: int = 2
    subject: str = "Science"
    # Deliberately still class 10 Science when omitted -- see "Defaults kept on purpose".
    grade: str = "X"
    correct_options: dict[str, str] = Field(default_factory=dict)

    @field_validator("grade", mode="before")
    @classmethod
    def _grade_pool_key(cls, v: object) -> str:
        return grades.to_roman(v)   # ValueError -> 422; 'X', '10', 10, '10th' -> 'X'
```

  (`from pydantic import Field, field_validator`. Use `mode="before"` so an int `10` is accepted, not refused as "not a string".)

In `schemas.py`: `QuickPaperRequest.grade: int` and `GenerateFromIdsRequest.grade: int`, with no default. The Flutter client always sends `grade`. Both Dart request classes serialise it (`requests.g.dart`), and the one `QuickPaperRequest(...)` call site passes `grade: selectedGrade` (assessment_list_page.dart ~271). `GenerateFromIdsRequest` is never constructed in the app. The two Python tests that post to these routes already send `"grade": 10`.

In `mobile_routes.py`, `create_scan_session`: refuse an unknown assessment instead of making it a Science class 10 session:

```python
    if assessment_routes._store is None:
        raise HTTPException(503, "assessment module not initialized")
    # An unknown assessment used to become a Science class 10 session. Every later
    # route on it 404s through require_school_owns_scan_session, so it could never
    # be processed; refusing here reports the mistake where it is made.
    assessment = require_school_owns_assessment(assessment_routes._store, req.assessment_id, current)
    session = mobile_scan.create_session(req.assessment_id, req.student_id, req.student_name,
                                         subject=assessment.subject, grade=assessment.grade,
                                         school_id=current.school_id)
```

  (`from .authz import require_school_owns_assessment, require_school_owns_scan_session`. The same 403 for another school's assessment still applies. Every existing test creates sessions against real assessments. The governance test's docstring already notes that a made-up id 404s.)

In `routes.py` `generate_paper` (~268): the `else 10` in `grade = assessment.grade if assessment else (request.selected_questions[0].grade if request.selected_questions else 10)` cannot be reached, because the function raises 400 on an empty `selected_questions` about 15 lines earlier. Write it as `grade = assessment.grade if assessment else request.selected_questions[0].grade` so the 10 cannot come back.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_grade_routing.py tests/test_grades.py tests/test_assessment_pool.py tests/test_mobile_routes_auth.py tests/test_pillar_routes_auth.py tests/test_assessment_mobile_scan.py tests/test_assessment_governance.py tests/test_assessment_parakh_cbse.py tests/test_route_inventory.py tests/test_api_main.py -q`
Expected: all pass.

**Defaults kept on purpose** (a written decision, so nobody "fixes" them by accident):

| Site | Default | Why it stays |
|---|---|---|
| `PracticeRequestBody.grade` / `.subject` (pillar_routes.py ~735) | `"X"` / `"Science"` | The shipped app posts only `studentId` + `perConcept` (`pillar_api.dart` `generatePractice`), and a student `User` record has no grade. Making `grade` required would turn every practice request from the app into a 422. A supplied grade is now validated and normalised (Step 7). **Follow-up, not in this plan:** the client should send the student's subject and grade. Until it does, web practice for a class 6-9 student draws from class 10 Science. |
| `SendPaperRequest.grade: int = 10` (pillar_routes.py ~394) | `10` | Only a label in the outgoing email, and the app always sends it (`pillar_api.dart` `sendPaper`, `required int grade`). Making it required would also mean changing `tests/test_route_inventory.py::_valid_body_for`, which is outside this task. |
| `insights.school_insights(..., grade=10)` (insights.py ~178) | `10` | The principal rollup's headline label. `school_report` never passes a grade, so the headline reads "Science Grade 10". It does not select questions. Out of scope here, but the same kind of defect. |
| `mobile_scan.ScanSession.grade` / `create_session(grade=10)` | `10` | Dataclass and function defaults with one caller, which after Step 7 always passes the assessment's real grade. |

---

### Task 3: The CBE bank record carries its reading passage

**Files:**
- Modify: `src/academicos/corpus/cbse_cbe.py` (`to_bank_record`)
- Test: `tests/test_cbse_cbe_parser.py`

The parser already extracts passages (60 of 151 English class 6–9 items) into `CbeItem.passage`; `to_bank_record` drops them, so every English comprehension question reached the bank unanswerable.

- [ ] **Step 1: Write the failing test** (append to `tests/test_cbse_cbe_parser.py`)

```python
def test_bank_record_carries_the_reading_passage(items):
    """`CbeItem.passage` was extracted and then dropped by to_bank_record."""
    with_passage = [i for i in items if i.subject == "English" and (i.passage or "").strip()]
    if not with_passage:
        pytest.skip("no English item with a passage parsed")
    rec = to_bank_record(with_passage[0])
    assert rec["metadata"]["passage"] == with_passage[0].passage.strip()


def test_bank_record_omits_an_empty_passage(items):
    bare = next((i for i in items if not (i.passage or "").strip()), None)
    if bare is None:
        pytest.skip("every item has a passage")
    assert "passage" not in to_bank_record(bare)["metadata"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_cbse_cbe_parser.py -q -k passage`
Expected: `KeyError: 'passage'`.

- [ ] **Step 3: Implement**

In `to_bank_record`, where the record's `metadata` dict is built, add:

```python
    # The shared reading passage for a linked-passage item. Without it an
    # English comprehension question ("Give two symptoms of the writer's fear
    # as she went diving") cannot be answered by anyone.
    passage = (item.passage or "").strip()
    if passage:
        metadata["passage"] = passage
```

(adapt the variable name to the dict that becomes `"metadata"` in that function).

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_cbse_cbe_parser.py -q`
Expected: all pass.

---

### Task 4: The composition module

**Files:**
- Create: `src/academicos/corpus/bank_merge.py`
- Test: `tests/test_bank_merge.py`

This is the heart of the change. It is pure — no file I/O — so every rule is testable.

- [ ] **Step 1: Write the failing test**

```python
"""bank_merge: contract, normalisation, gates, composition."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.corpus import bank_merge as bm  # noqa: E402

TS = "2026-09-19T00:00:00+00:00"


def board(i=1, **kw):
    rec = {
        "id": f"cbse:q:src:{'a' * 24}:{i}", "questionBankId": "cbse-pilot",
        "subject": "Science", "grade": 10, "chapterIds": [], "competencyIds": [],
        "bloomLevel": "understand", "difficulty": "easy", "type": "short_answer",
        "stem": f"Explain why the sky appears blue during the day, question {i}.",
        "stemLatex": "", "parts": [],
        "answerScheme": {"totalMarks": 2, "markingPoints": [
            {"id": "mp1", "description": "Scattering of light", "marks": 2,
             "keyword": "scattering", "isRequired": True, "synonyms": []}],
            "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
            "modelAnswer": "Scattering of light", "modelAnswerLatex": "",
            "provenance": "cbse_marking_scheme"},
        "estimatedTimeMinutes": 4, "marks": 2, "language": "en",
        "source": "cbse_board_paper", "qualityScore": 0.8, "tags": [],
        "createdAt": TS, "updatedAt": TS, "metadata": {},
    }
    rec.update(kw)
    return rec


def cbe_mcq(i=1, answer="B. control", **kw):
    rec = board(i, id=f"cbe:q:English9X{i}", subject="Mathematics", grade=7,
                source="cbse_question_bank", type="mcq", marks=1,
                stem="Which of these is the largest number? Select one option.")
    rec["parts"] = [{"id": f"p{i}", "partNumber": 1, "text": t, "marks": 0,
                     "answerType": "singleChoice", "alternativeAnswers": []}
                    for t in ("A. avoid", "B. control", "C. forget", "D. understand")]
    rec["answerScheme"] = {"totalMarks": 1, "markingPoints": [
        {"id": "mp1", "description": answer, "marks": 1, "keyword": "",
         "isRequired": True, "synonyms": []}],
        "rubricLevels": [], "commonErrors": [], "alternativeAnswers": [],
        "modelAnswer": answer, "modelAnswerLatex": "", "provenance": "cbse_marking_scheme"}
    rec.update(kw)
    return rec


# ---- contract ---------------------------------------------------------------

def test_a_board_record_satisfies_the_contract():
    assert bm.contract_errors(board()) == []


@pytest.mark.parametrize("key", ["competencyIds", "bloomLevel", "stemLatex", "createdAt"])
def test_a_missing_required_field_is_reported(key):
    rec = board()
    del rec[key]
    assert any(key in e for e in bm.contract_errors(rec))


def test_a_part_without_text_latex_is_reported():
    """259 CBE rows failed on the phone for exactly this."""
    rec = cbe_mcq()
    assert any("textLatex" in e for e in bm.contract_errors(rec))


@pytest.mark.parametrize("key,value", [
    ("bloomLevel", "memorise"), ("difficulty", "tricky"),
    ("type", "essay"), ("source", "cbse_textbook"),
])
def test_a_value_the_phone_would_silently_default_is_reported(key, value):
    """The phone maps an unknown source to ncert_textbook -- a provenance mislabel."""
    assert any(key in e for e in bm.contract_errors(board(**{key: value})))


def test_a_boolean_is_not_a_number():
    assert any("marks" in e for e in bm.contract_errors(board(marks=True)))


# ---- MCQ answer recovery ----------------------------------------------------

OPTS = {"A": "avoid", "B": "control", "C": "forget", "D": "understand"}


@pytest.mark.parametrize("answer,expected", [
    ("B. control Award 1 mark for the correct answer", "B"),
    ("A – avoid", "A"),
    ("(C) forget", "C"),
    ("D", "D"),
    ("understand Award 1 mark", "D"),          # bare option text, no letter
])
def test_correct_letter_is_recovered(answer, expected):
    assert bm.correct_letter([answer], OPTS) == expected


@pytest.mark.parametrize("answer", [
    "a.A – III; B – IV; C- II; D – I",        # a matching-question key
    "modernity A. 1 & 3 B. 2 &4 C. 2 & 5 D. 1 &",          # bled-in question text
    "Read the following data and select the appropriate option",
    "Fill in the blank: SECTOR CRITERIA USED",
    "Find the odd one out from the following options",
    "something that is no option",
    "",
])
def test_a_wrong_letter_is_never_invented(answer):
    """Returning 'A' for a matching key would ship a confidently wrong answer."""
    assert bm.correct_letter([answer], OPTS) is None


# ---- normalisation ----------------------------------------------------------

def test_cbe_mcq_becomes_inline_objective_mcq():
    out, reason = bm.normalise(cbe_mcq())
    assert reason is None
    assert out["parts"] == []
    assert "(A) avoid" in out["stem"] and "(D) understand" in out["stem"]
    meta = out["answerScheme"]["metadata"]
    assert meta["objective"] is True and meta["correctOption"] == "B"
    assert bm.contract_errors(out) == []


def test_an_mcq_with_no_recoverable_key_is_refused():
    _, reason = bm.normalise(cbe_mcq(answer="Read the following passage and choose"))
    assert reason == "mcq-answer-unresolved"


def test_missing_bloom_is_inferred_and_marked_as_inferred():
    rec = cbe_mcq()
    rec["type"] = "short_answer"
    rec["parts"] = []
    del rec["bloomLevel"]
    out, _ = bm.normalise(rec)
    assert out["bloomLevel"] in bm.BLOOM_LEVELS
    assert out["metadata"]["bloomInferred"] is True


def test_a_passage_is_prepended_to_the_stem():
    rec = cbe_mcq()
    rec["type"] = "short_answer"
    rec["parts"] = []
    rec["metadata"] = {"passage": "Almonds grow in California orchards."}
    out, _ = bm.normalise(rec)
    assert out["stem"].index("Almonds grow") < out["stem"].index("largest number")


def test_normalise_does_not_mutate_its_input():
    rec = cbe_mcq()
    before = copy.deepcopy(rec)
    bm.normalise(rec)
    assert rec == before


# ---- gates ------------------------------------------------------------------

@pytest.mark.parametrize("patch,reason", [
    ({"metadata": {"needsFigure": True, "figureState": "attached"}}, "figure-unavailable"),
    ({"stem": "PART- B has two sections: Section - B1 Supplementary"}, "header-as-stem"),
    ({"stem": "Q5."}, "stem-too-short"),
])
def test_gate(patch, reason):
    rec = board(source="cbse_question_bank", **patch)
    assert bm.exclusion_reason(rec) == reason


def test_cbe_english_without_a_passage_is_excluded():
    rec = board(source="cbse_question_bank", subject="English")
    assert bm.exclusion_reason(rec) == "passage-unavailable"


def test_cbe_english_with_a_passage_is_kept():
    rec = board(source="cbse_question_bank", subject="English",
                metadata={"passage": "A long reading passage."})
    assert bm.exclusion_reason(rec) is None


def test_an_answer_that_is_question_text_is_excluded():
    rec = board(source="cbse_sample_paper")
    rec["answerScheme"]["modelAnswer"] = "Read the following data and select the appropriate option"
    assert bm.exclusion_reason(rec) == "answer-is-question-text"


def test_an_answer_far_longer_than_its_marks_is_excluded():
    rec = board(source="cbse_sample_paper", marks=1)
    rec["answerScheme"]["modelAnswer"] = "x " * 5000
    assert bm.exclusion_reason(rec) == "answer-bleed"


def test_legacy_font_garble_is_excluded():
    """Consecutive Indic vowel signs cannot occur in correctly spelled text."""
    rec = board(source="cbse_sample_paper",
                stem="মনিিোচরোপয "
                     "নিিো নিিো নিিো")
    assert bm.exclusion_reason(rec) == "garbled-script"


@pytest.mark.parametrize("stem", [
    # visarga straight after a vowel sign is correct Hindi: "dukh" (sorrow)
    "दुःख दुःख दुःख दुःख के कारण",
    # decomposed Bengali o-kar (U+09C7 U+09BE) is two vowel signs before NFC
    "কোন কোন কোন কোন প্রশ্ন",
])
def test_correct_indic_text_is_not_flagged_as_garbled(stem):
    assert bm.exclusion_reason(board(source="cbse_sample_paper", stem=stem)) is None


# ---- composition ------------------------------------------------------------

def test_board_records_pass_through_unchanged():
    b = board()
    result = bm.compose([copy.deepcopy(b)], [], [])
    assert result.questions == [b]


def test_non_board_rows_already_in_the_served_bank_are_rebuilt_from_source():
    """Idempotency: a second run must not keep the first run's CBE rows."""
    stale = cbe_mcq(9)
    result = bm.compose([board(), stale], [], [])
    assert [q["id"] for q in result.questions] == [board()["id"]]


def test_a_duplicate_of_a_board_question_is_dropped_in_favour_of_the_board():
    b = board(stem="Explain why the sky appears blue during the day, question 1.")
    dup = board(2, id="cbse:sqp:X:Science:1", source="cbse_sample_paper",
                stem=b["stem"])
    result = bm.compose([b], [], [dup])
    assert [q["id"] for q in result.questions] == [b["id"]]
    assert result.excluded[0]["reason"] == "duplicate-stem"


def test_every_exclusion_is_recorded_with_its_reason():
    fig = board(3, id="cbe:q:F1", source="cbse_question_bank",
                metadata={"needsFigure": True})
    result = bm.compose([], [fig], [])
    assert result.questions == []
    assert result.excluded == [{"id": "cbe:q:F1", "source": "cbse_question_bank",
                                "reason": "figure-unavailable", "subject": "Science",
                                "grade": 10, "stem": fig["stem"][:200]}]


def test_a_contract_violation_after_normalising_fails_the_whole_merge(monkeypatch):
    monkeypatch.setattr(bm, "normalise", lambda rec: ({"id": rec["id"]}, None))
    with pytest.raises(bm.ContractError):
        bm.compose([], [board(4, id="cbe:q:Z", source="cbse_question_bank")], [])
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_bank_merge.py -q`
Expected: `ModuleNotFoundError: academicos.corpus.bank_merge`.

- [ ] **Step 3: Implement**

```python
"""Compose the served question bank from its three sources.

The served bank -- academicos-data/syllabus/questions.json and its byte-identical
APK copy, frontend/assets/corpus/questions.json -- is what every surface reads.
It is composed from:

  board  records already in it with source == "cbse_board_paper"
  cbe    academicos-data/corpus/cbse-cbe/questions.json   (classes 6-10)
  sqp    academicos-data/corpus/cbse-sqp/questions.json   (classes 10, 12)

Board records pass through untouched: they already decode on the phone and
render on the web, and this module must not be the thing that breaks them.
CBE and SQP records are normalised to the phone's contract and then gated.

Why the contract is the phone's and not the API's
--------------------------------------------------
`QuestionSchema` accepts all 720 CBE records; the phone's `Question.fromJson`
rejects 259 of them (parts with no `textLatex`) and all 1,834 SQP records (no
`competencyIds`, no `bloomLevel`). One rejected row fails the whole corpus load,
before runApp(), so the app never leaves its splash screen. The two contracts
have drifted, so this enforces the stricter one. `contract_errors` mirrors
frontend/lib/domain/entities/question.g.dart; a Dart test that decodes the real
asset is the final word.

Why a value is checked, not just its presence
---------------------------------------------
The phone's enum converters do not fail on an unknown value -- they default.
An unknown `source` becomes `ncert_textbook`, which would print a CBSE sample
paper question as an NCERT textbook one. So values are checked against the sets
the converters accept.

What is excluded, and why
-------------------------
Nothing is dropped silently; every exclusion is returned with its reason.

  figure-unavailable     no surface can resolve a `cbe-figure:` asset
  passage-unavailable    a comprehension question with no passage to read
  header-as-stem         the "question" is a page header
  stem-too-short         no question text to speak of
  no-answer              rule Q1: no answer key, no question
  answer-is-question-text  the scheme joined the wrong text -- often another
                         question's stem
  answer-bleed           an answer far longer than its marks allow: the
                         scheme ran on into the following questions
  garbled-script         legacy-font extraction produced text nobody can read
  mcq-answer-unresolved  the correct option cannot be recovered with certainty
  duplicate-stem         already served, under a board-paper id where possible
"""
from __future__ import annotations

import copy
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..assessment.mapping import _resolve_bloom, _resolve_difficulty, _resolve_type
from ..assessment.question_bank import OfficialAnswer, build_official_scheme

BOARD_SOURCE = "cbse_board_paper"

# The values each phone converter accepts (frontend/lib/domain/entities/enums.dart).
BLOOM_LEVELS = frozenset({"remember", "understand", "apply", "analyze", "evaluate", "create"})
DIFFICULTIES = frozenset({"easy", "medium", "hard"})
QUESTION_TYPES = frozenset({
    "mcq", "very_short_answer", "short_answer", "long_answer", "very_long_answer",
    "case_study", "assertion_reason", "map_based", "diagram_based", "graph_based",
    "table_based", "competency_based"})
SOURCES = frozenset({
    "cbse_board_paper", "cbse_sample_paper", "cbse_question_bank", "ncert_exemplar",
    "ncert_textbook", "school_database", "teacher_created", "ai_generated",
    "competency_framework"})
ANSWER_TYPES = frozenset({
    "singleChoice", "multipleChoice", "textShort", "textLong", "numeric", "diagram",
    "map", "graph", "table"})


class ContractError(Exception):
    """A normalised record still breaks the phone's contract -- a normaliser bug."""

    def __init__(self, record_id: str, errors: list[str]) -> None:
        super().__init__(f"{record_id}: {'; '.join(errors)}")
        self.record_id = record_id
        self.errors = errors


# --------------------------------------------------------------------------- #
# the contract
# --------------------------------------------------------------------------- #

def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_str_list(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _is_iso(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _check(obj: dict, where: str, spec: dict[str, str], errs: list[str]) -> None:
    for key, kind in spec.items():
        present = key in obj and obj[key] is not None
        value = obj.get(key)
        optional = kind.endswith("?")
        kind = kind.rstrip("?")
        if not present:
            if not optional:
                errs.append(f"{where}.{key} missing")
            continue
        ok = {
            "str": isinstance(value, str),
            "num": _is_num(value),
            "bool": isinstance(value, bool),
            "strlist": _is_str_list(value),
            "list": isinstance(value, list),
            "dict": isinstance(value, dict),
            "iso": _is_iso(value),
        }[kind]
        if not ok:
            errs.append(f"{where}.{key} is not {kind}")


_QUESTION = {
    "id": "str", "questionBankId": "str", "subject": "str", "grade": "num",
    "chapterIds": "strlist", "competencyIds": "strlist", "bloomLevel": "str",
    "difficulty": "str", "type": "str", "stem": "str", "stemLatex": "str",
    "parts": "list", "answerScheme": "dict", "estimatedTimeMinutes": "num",
    "marks": "num", "language": "str", "source": "str", "qualityScore": "num",
    "tags": "strlist", "createdAt": "iso", "updatedAt": "iso", "metadata": "dict?",
    "diagramAssetId": "str?", "mapAssetId": "str?", "graphAssetId": "str?",
    "tableAssetId": "str?",
}
_PART = {
    "id": "str", "partNumber": "num", "text": "str", "textLatex": "str", "marks": "num",
    "answerType": "str", "options": "strlist?", "correctOption": "str?",
    "expectedAnswer": "str?", "expectedAnswerLatex": "str?", "keywords": "strlist?",
    "alternativeAnswers": "strlist?",
}
_SCHEME = {
    "totalMarks": "num", "markingPoints": "list", "rubricLevels": "list",
    "commonErrors": "strlist", "alternativeAnswers": "strlist", "modelAnswer": "str",
    "modelAnswerLatex": "str", "hasPartialCredit": "bool?", "metadata": "dict?",
}
_POINT = {"id": "str", "description": "str", "marks": "num", "keyword": "str",
          "isRequired": "bool", "synonyms": "strlist?"}
_RUBRIC = {"level": "num", "label": "str", "minMarks": "num", "maxMarks": "num",
           "description": "str"}
_ENUMS = {"bloomLevel": BLOOM_LEVELS, "difficulty": DIFFICULTIES,
          "type": QUESTION_TYPES, "source": SOURCES}


def contract_errors(rec: dict) -> list[str]:
    """Every way this record would fail, or mis-decode on, the phone."""
    errs: list[str] = []
    _check(rec, "question", _QUESTION, errs)
    for key, allowed in _ENUMS.items():
        if isinstance(rec.get(key), str) and rec[key] not in allowed:
            errs.append(f"question.{key}={rec[key]!r} is not one of the phone's values")
    for i, part in enumerate(rec.get("parts") or []):
        if not isinstance(part, dict):
            errs.append(f"parts[{i}] is not an object")
            continue
        _check(part, f"parts[{i}]", _PART, errs)
        if isinstance(part.get("answerType"), str) and part["answerType"] not in ANSWER_TYPES:
            errs.append(f"parts[{i}].answerType={part['answerType']!r} is not one of the phone's values")
    scheme = rec.get("answerScheme")
    if isinstance(scheme, dict):
        _check(scheme, "answerScheme", _SCHEME, errs)
        for i, mp in enumerate(scheme.get("markingPoints") or []):
            _check(mp if isinstance(mp, dict) else {}, f"markingPoints[{i}]", _POINT, errs)
        for i, rl in enumerate(scheme.get("rubricLevels") or []):
            _check(rl if isinstance(rl, dict) else {}, f"rubricLevels[{i}]", _RUBRIC, errs)
    return errs


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #

_HEADER = re.compile(
    r"^(?:PART\s*[-–]|Page\b|Class\s*[-–]|Subject\s*[-–]|Time allowed|"
    r"Maximum marks|General Instructions)", re.I)
# A scheme that joined the wrong text often carries the next question's stem.
_INSTRUCTION = re.compile(
    r"^(?:read the (?:following|given|passage|extract|data|information)|fill in the blank|"
    r"find the odd one|select the (?:correct|appropriate)|choose the (?:correct|appropriate))",
    re.I)
_PASSAGE_REF = re.compile(r"\bread the (?:following )?(?:passage|extract|poem|text)\b", re.I)
_AWARD = re.compile(r"\s*\bAward\b.*$", re.I | re.S)
_MIN_STEM = 15
_GARBLE_RUNS = 3


def _answer_text(rec: dict) -> str:
    scheme = rec.get("answerScheme") or {}
    points = " ".join(str(p.get("description") or "") for p in scheme.get("markingPoints") or [])
    return f"{scheme.get('modelAnswer') or ''} {points}".strip()


def _first_answer(rec: dict) -> str:
    scheme = rec.get("answerScheme") or {}
    if (scheme.get("modelAnswer") or "").strip():
        return scheme["modelAnswer"].strip()
    points = scheme.get("markingPoints") or []
    return str(points[0].get("description") or "").strip() if points else ""


def _vowel_sign_runs(text: str) -> int:
    """Places where two dependent vowel signs sit side by side.

    In any Indic script a vowel sign (matra) attaches to a consonant, so two in a
    row never occur in correctly spelled text. Legacy-font extraction produces
    them constantly: "নিিো".

    Two cases that would otherwise be false positives, both handled:
      * only characters NAMED as vowel signs count. Visarga and anusvara are
        spacing/nonspacing marks too, and "दुःख" (Hindi,
        "sorrow") correctly puts visarga straight after a vowel sign.
      * the text is NFC-composed first. Bengali "ো" decomposes to two
        vowel signs (U+09C7 U+09BE); decomposed-but-correct text must not count.
    """
    runs = 0
    prev = False
    for ch in unicodedata.normalize("NFC", text):
        is_sign = "VOWEL SIGN" in unicodedata.name(ch, "")
        if is_sign and prev:
            runs += 1
        prev = is_sign
    return runs


def exclusion_reason(rec: dict) -> str | None:
    """Why this CBE/SQP record cannot be served, or None if it can."""
    meta = rec.get("metadata") or {}
    stem = str(rec.get("stem") or "").strip()
    passage = str(meta.get("passage") or "").strip()
    if meta.get("needsFigure"):
        return "figure-unavailable"
    if rec.get("source") == "cbse_question_bank" and rec.get("subject") == "English" and not passage:
        # Every CBE English item is read against a text; without it none can be answered.
        return "passage-unavailable"
    if not passage and _PASSAGE_REF.search(stem) and len(stem) < 400:
        return "passage-unavailable"
    if _HEADER.match(stem):
        return "header-as-stem"
    if len(stem) < _MIN_STEM:
        return "stem-too-short"
    if _vowel_sign_runs(stem) >= _GARBLE_RUNS:
        return "garbled-script"
    answer = _answer_text(rec)
    if not answer:
        return "no-answer"
    if _INSTRUCTION.match(_first_answer(rec)):
        return "answer-is-question-text"
    marks = rec.get("marks") if _is_num(rec.get("marks")) else 1
    if len(answer) > max(600, 450 * max(int(marks), 1)):
        return "answer-bleed"
    return None


# --------------------------------------------------------------------------- #
# MCQs
# --------------------------------------------------------------------------- #

_PART_OPTION = re.compile(r"^\s*\(?([A-Da-d])\)?\s*[.)–—:\-]\s*(.*)$", re.S)
_LEADING_LETTER = re.compile(r"^\s*\(?([A-Da-d])\)?\s*(?:[.)–—:\-]|$)")
_LABEL = re.compile(r"(?<![A-Za-z])([A-D])\s*[.)–—:\-]")
_INLINE_OPTION = re.compile(r"\(([A-Da-d])\)\s*")


def _norm(text: str) -> str:
    return " ".join(re.findall(r"\w+", (text or "").lower()))


def _options_from_parts(parts: list[dict]) -> dict[str, str] | None:
    """{'A': 'avoid', ...} from CBE/SQP option parts, or None if they are not A-D in order."""
    opts: dict[str, str] = {}
    for part in parts:
        m = _PART_OPTION.match(str(part.get("text") or ""))
        if not m:
            return None
        letter = m.group(1).upper()
        if letter in opts:
            return None
        opts[letter] = m.group(2).strip()
    if len(opts) < 2 or list(opts) != list("ABCD"[: len(opts)]):
        return None
    return opts


def _options_from_stem(stem: str) -> dict[str, str] | None:
    """Options already written inline as (A)..(D) -- the board and most SQP shape."""
    matches = list(_INLINE_OPTION.finditer(stem))
    labels = [m.group(1).upper() for m in matches]
    if len(labels) < 2 or labels != list("ABCD"[: len(labels)]):
        return None
    return {labels[i]: stem[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(stem)]
            .strip(" .;") for i, m in enumerate(matches)}


def correct_letter(answers: list[str], options: dict[str, str]) -> str | None:
    """The correct option, only when the scheme states it unambiguously.

    Refuses rather than guesses. Two failure shapes are common in the SQP
    schemes and both would yield a confident wrong key if read loosely:
    a matching-question key ("A - III; B - IV; ..."), and question text that
    the scheme parser joined in place of the answer ("modernity A. 1 & 3 B. ...",
    "Read the following data and select ..."). A wrong key is worse than none:
    a teacher trusts it and marks students wrong.
    """
    for raw in answers:
        text = _AWARD.sub("", raw or "").strip()
        if not text:
            continue
        if len(set(_LABEL.findall(text))) >= 2 or _INSTRUCTION.match(text):
            return None
        m = _LEADING_LETTER.match(text)
        if m:
            letter = m.group(1).upper()
            return letter if letter in options else None
        hits = [k for k, v in options.items() if _norm(v) and _norm(v) == _norm(text)]
        return hits[0] if len(hits) == 1 else None
    return None


def _objective_scheme(rec: dict, options: dict[str, str], letter: str) -> dict:
    """The same objective scheme a board MCQ carries, via the same builder."""
    old = rec.get("answerScheme") or {}
    marks = int(rec["marks"])
    scheme = build_official_scheme(
        OfficialAnswer(q_no=0, correct_option=letter, answer_text=options[letter], marks=marks),
        marks=marks, question_id=rec["id"],
        code=str(old.get("sourcePaperCode") or ""),
        document_id=str(old.get("sourceDocumentId") or ""),
        options=options,
    )
    return scheme.model_dump(mode="json", by_alias=True)


# --------------------------------------------------------------------------- #
# normalisation
# --------------------------------------------------------------------------- #

def _normalise_scheme(scheme: dict, marks: int, record_id: str) -> dict:
    s = dict(scheme)
    s["totalMarks"] = int(s.get("totalMarks") or marks)
    points = []
    for i, mp in enumerate(s.get("markingPoints") or []):
        points.append({
            **mp,
            "id": str(mp.get("id") or f"{record_id}:mp{i + 1}"),
            "description": str(mp.get("description") or ""),
            "marks": int(mp.get("marks") or 0),
            "keyword": str(mp.get("keyword") or ""),
            "isRequired": bool(mp.get("isRequired", False)),
            "synonyms": [str(x) for x in (mp.get("synonyms") or [])],
        })
    s["markingPoints"] = points
    s["rubricLevels"] = [r for r in (s.get("rubricLevels") or []) if isinstance(r, dict)]
    s["commonErrors"] = [str(x) for x in (s.get("commonErrors") or [])]
    s["alternativeAnswers"] = [str(x) for x in (s.get("alternativeAnswers") or [])]
    s["modelAnswer"] = str(s.get("modelAnswer") or "")
    s["modelAnswerLatex"] = str(s.get("modelAnswerLatex") or "")
    s["hasPartialCredit"] = bool(s.get("hasPartialCredit", len(points) > 1))
    s["metadata"] = dict(s.get("metadata") or {})
    return s


def _normalise_part(part: dict, index: int, record_id: str) -> dict:
    p = dict(part)
    p["id"] = str(p.get("id") or f"{record_id}:p{index + 1}")
    p["partNumber"] = int(p.get("partNumber") or index + 1)
    p["text"] = str(p.get("text") or "")
    p["textLatex"] = str(p.get("textLatex") or "")
    p["marks"] = int(p.get("marks") or 0)
    if p.get("answerType") not in ANSWER_TYPES:
        p["answerType"] = "textShort"
    p["alternativeAnswers"] = [str(x) for x in (p.get("alternativeAnswers") or [])]
    return p


def normalise(rec: dict) -> tuple[dict, str | None]:
    """A new record that satisfies the phone's contract, or a reason it cannot.

    Values that had to be supplied are marked `metadata.<field>Inferred`, so an
    inferred Bloom level is never readable as one CBSE authored.
    """
    r = copy.deepcopy(rec)
    meta = dict(r.get("metadata") or {})
    scheme = r.get("answerScheme") or {}
    marks = r.get("marks") if _is_num(r.get("marks")) else scheme.get("totalMarks")
    marks = int(marks) if _is_num(marks) and marks > 0 else 1
    r["marks"] = marks

    if r.get("bloomLevel") not in BLOOM_LEVELS:
        r["bloomLevel"] = _resolve_bloom(None)
        meta["bloomInferred"] = True
    if r.get("type") not in QUESTION_TYPES:
        r["type"] = _resolve_type(r.get("type"), marks)
        meta["typeInferred"] = True
    if r.get("difficulty") not in DIFFICULTIES:
        r["difficulty"] = _resolve_difficulty(marks, r["bloomLevel"])
        meta["difficultyInferred"] = True

    for key in ("chapterIds", "competencyIds", "tags"):
        r[key] = [str(x) for x in (r.get(key) or [])]
    r["stem"] = str(r.get("stem") or "").strip()
    r["stemLatex"] = str(r.get("stemLatex") or "")
    r["language"] = str(r.get("language") or "en")
    r["questionBankId"] = str(r.get("questionBankId") or r.get("source") or "unknown")
    if not _is_num(r.get("estimatedTimeMinutes")):
        r["estimatedTimeMinutes"] = max(1, marks * 2)
    if not _is_num(r.get("qualityScore")):
        r["qualityScore"] = 0.7
    for key in ("createdAt", "updatedAt"):
        if not _is_iso(r.get(key)):
            r[key] = "2026-01-01T00:00:00+00:00"
    r["parts"] = [_normalise_part(p, i, r["id"]) for i, p in enumerate(r.get("parts") or [])]
    r["answerScheme"] = _normalise_scheme(scheme, marks, r["id"])

    passage = str(meta.get("passage") or "").strip()
    if passage:
        r["stem"] = f"Read the passage below and answer the question that follows.\n\n{passage}\n\n{r['stem']}"
        meta["passageInline"] = True

    if r["type"] == "mcq":
        options = _options_from_stem(r["stem"]) or _options_from_parts(r["parts"])
        if options is None:
            return r, "mcq-options-unresolved"
        letter = correct_letter(
            [r["answerScheme"]["modelAnswer"]]
            + [mp["description"] for mp in r["answerScheme"]["markingPoints"]],
            options)
        if letter is None:
            return r, "mcq-answer-unresolved"
        if _options_from_stem(r["stem"]) is None:
            r["stem"] = r["stem"] + " " + " ".join(f"({k}) {v}" for k, v in options.items())
        r["parts"] = []            # options live inline, as on every board MCQ
        r["answerScheme"] = _normalise_scheme(_objective_scheme(r, options, letter), marks, r["id"])

    r["metadata"] = meta
    return r, None


# --------------------------------------------------------------------------- #
# composition
# --------------------------------------------------------------------------- #

@dataclass
class ComposeResult:
    questions: list[dict]
    excluded: list[dict] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def _excluded(rec: dict, reason: str) -> dict:
    return {"id": rec.get("id"), "source": rec.get("source"), "reason": reason,
            "subject": rec.get("subject"), "grade": rec.get("grade"),
            "stem": str(rec.get("stem") or "")[:200]}


def compose(served: list[dict], cbe: list[dict], sqp: list[dict]) -> ComposeResult:
    """Board records from `served`, then CBE, then SQP.

    Non-board rows already in `served` are ignored and rebuilt from their source
    files, so running the merge twice gives the same bank. A normalised record
    that still breaks the contract raises ContractError and nothing is written.
    """
    out: list[dict] = []
    excluded: list[dict] = []
    seen_ids: set[str] = set()
    seen_stems: set[tuple] = set()
    counts = {"board": 0, "cbe": 0, "sqp": 0}

    for rec in served:
        if rec.get("source") != BOARD_SOURCE:
            continue
        errors = contract_errors(rec)
        if errors:
            raise ContractError(str(rec.get("id")), errors)
        out.append(rec)
        seen_ids.add(rec["id"])
        seen_stems.add((rec.get("subject"), rec.get("grade"), _norm(rec.get("stem", ""))))
        counts["board"] += 1

    for label, rows in (("cbe", cbe), ("sqp", sqp)):
        for raw in rows:
            if raw.get("id") in seen_ids:
                excluded.append(_excluded(raw, "duplicate-id"))
                continue
            reason = exclusion_reason(raw)
            if reason:
                excluded.append(_excluded(raw, reason))
                continue
            rec, reason = normalise(raw)
            if reason:
                excluded.append(_excluded(raw, reason))
                continue
            key = (rec.get("subject"), rec.get("grade"), _norm(raw.get("stem", "")))
            if key in seen_stems:
                excluded.append(_excluded(raw, "duplicate-stem"))
                continue
            errors = contract_errors(rec)
            if errors:
                raise ContractError(str(rec.get("id")), errors)
            out.append(rec)
            seen_ids.add(rec["id"])
            seen_stems.add(key)
            counts[label] += 1

    return ComposeResult(questions=out, excluded=excluded, counts=counts)
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_bank_merge.py -q`
Expected: all pass. If `OfficialAnswer` needs different constructor arguments, read `question_bank.OfficialAnswer` and adapt `_objective_scheme` — do not change the test's expectation that the scheme's `metadata.correctOption` is the recovered letter.

- [ ] **Step 5: Measure against the real banks** (read-only)

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "
import sys, json, collections; sys.path.insert(0,'src')
from pathlib import Path
from academicos.corpus import bank_merge as bm
L=lambda p: json.loads(Path(p).read_text(encoding='utf-8'))['questions']
r=bm.compose(L('academicos-data/syllabus/questions.json'),
             L('academicos-data/corpus/cbse-cbe/questions.json'),
             L('academicos-data/corpus/cbse-sqp/questions.json'))
print('counts', r.counts, 'excluded', len(r.excluded))
print(collections.Counter((e['source'], e['reason']) for e in r.excluded).most_common())
"
```

Report the output in your task summary. `ContractError` here is a bug in `normalise` — fix it, do not catch it.

---

### Task 5: The merge script

**Files:**
- Create: `scripts/merge_question_banks.py`
- Test: `tests/test_merge_question_banks.py`

**Depends on:** Task 4.

- [ ] **Step 1: Write the failing test**

```python
"""scripts/merge_question_banks.py, run against temporary files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import merge_question_banks as mqb  # noqa: E402
from test_bank_merge import board, cbe_mcq  # noqa: E402


def _write(path: Path, questions, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"questions": questions, **extra}), encoding="utf-8")


@pytest.fixture
def layout(tmp_path):
    paths = mqb.Paths(
        served=tmp_path / "served.json", apk=tmp_path / "apk.json",
        cbe=tmp_path / "cbe.json", sqp=tmp_path / "sqp.json",
        excluded=tmp_path / "excluded.json")
    _write(paths.served, [board()], chapterTaggedAt="t", chapterTagMethod="m")
    _write(paths.cbe, [cbe_mcq()], chapterTaggedAt="t", builtAt="2026-09-19T00:00:00+00:00")
    _write(paths.sqp, [], chapterTaggedAt="t", builtAt="2026-09-19T00:00:00+00:00")
    return paths


def test_writes_served_and_apk_byte_identical(layout):
    assert mqb.run(layout, check=False) == 0
    assert layout.served.read_bytes() == layout.apk.read_bytes()
    ids = [q["id"] for q in json.loads(layout.served.read_text(encoding="utf-8"))["questions"]]
    assert ids == [board()["id"], cbe_mcq()["id"]]


def test_is_idempotent(layout):
    mqb.run(layout, check=False)
    first = layout.served.read_bytes()
    mqb.run(layout, check=False)
    assert layout.served.read_bytes() == first


def test_check_writes_nothing(layout):
    before = layout.served.read_bytes()
    assert mqb.run(layout, check=True) == 0
    assert layout.served.read_bytes() == before
    assert not layout.apk.exists()


def test_refuses_an_untagged_source(layout):
    """Rebuilding a builder discards chapter tags; merging then ships class 6-9 untagged."""
    _write(layout.cbe, [cbe_mcq()])
    assert mqb.run(layout, check=False) != 0
    assert not layout.apk.exists()


def test_records_every_exclusion(layout):
    _write(layout.cbe, [board(7, id="cbe:q:F", source="cbse_question_bank",
                              metadata={"needsFigure": True})], chapterTaggedAt="t")
    mqb.run(layout, check=False)
    excluded = json.loads(layout.excluded.read_text(encoding="utf-8"))
    assert [e["reason"] for e in excluded["excluded"]] == ["figure-unavailable"]


def test_scheme_coverage_counts_carried_official_schemes(layout):
    mqb.run(layout, check=False)
    payload = json.loads(layout.served.read_text(encoding="utf-8"))
    assert payload["schemeCoverage"] == 1.0
    assert payload["composedFrom"] == {"board": 1, "cbe": 1, "sqp": 0}
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_merge_question_banks.py -q`
Expected: `ModuleNotFoundError: merge_question_banks`.

- [ ] **Step 3: Implement**

```python
"""Compose the served question bank from board papers, CBE and SQP.

Run AFTER the builders and the chapter tagger:

    build_cbe_bank.py   build_sqp_bank.py
    tag_question_bank.py
    apply_chapter_tags.py
    merge_question_banks.py        <- this
    enrich_question_bank.py

It writes academicos-data/syllabus/questions.json and its APK copy,
frontend/assets/corpus/questions.json, byte-identical, plus every record it left
out and why in academicos-data/syllabus/_merge_excluded.json. The rules live in
src/academicos/corpus/bank_merge.py; this file only does the I/O.

It refuses a source with no chapter tags. Re-running a builder discards the tags
apply_chapter_tags.py wrote, and merging such a source ships class 6-9 with no
chapter a paper blueprint can select on.

Run:  python scripts/merge_question_banks.py [--check]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.corpus import bank_merge  # noqa: E402


@dataclass
class Paths:
    served: Path
    apk: Path
    cbe: Path
    sqp: Path
    excluded: Path


DEFAULT = Paths(
    served=REPO / "academicos-data" / "syllabus" / "questions.json",
    apk=REPO / "frontend" / "assets" / "corpus" / "questions.json",
    cbe=REPO / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json",
    sqp=REPO / "academicos-data" / "corpus" / "cbse-sqp" / "questions.json",
    excluded=REPO / "academicos-data" / "syllabus" / "_merge_excluded.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_official_scheme(rec: dict) -> bool:
    scheme = rec.get("answerScheme") or {}
    return scheme.get("provenance") == "cbse_marking_scheme" and bool(
        scheme.get("markingPoints") or (scheme.get("modelAnswer") or "").strip())


def run(paths: Paths, *, check: bool) -> int:
    served, cbe, sqp = _load(paths.served), _load(paths.cbe), _load(paths.sqp)
    for name, payload in (("CBE", cbe), ("SQP", sqp)):
        if payload.get("questions") and not payload.get("chapterTaggedAt"):
            print(f"refusing: the {name} bank carries no chapter tags -- "
                  f"run scripts/apply_chapter_tags.py first")
            return 2

    result = bank_merge.compose(served["questions"], cbe["questions"], sqp["questions"])
    questions = result.questions
    covered = sum(1 for q in questions if _has_official_scheme(q))

    # Deterministic, so re-running on unchanged sources gives identical bytes:
    # the timestamp comes from the sources, not the clock, and every key this
    # script writes is rebuilt in a fixed order. (Carrying a previous run's
    # composedFrom/composedAt forward would move them ahead of "questions" on
    # the second run and change the bytes although nothing else had.)
    composed_at = max(str(p.get("builtAt") or "") for p in (cbe, sqp)) or None
    written_here = ("questions", "exportedCount", "schemeCoverage", "composedFrom", "composedAt")
    payload = {k: v for k, v in served.items() if k not in written_here}
    payload.update({
        "questions": questions,
        "exportedCount": len(questions),
        "schemeCoverage": round(covered / len(questions), 4) if questions else 0.0,
        "composedFrom": result.counts,
        "composedAt": composed_at,
    })

    reasons = collections.Counter((e["source"], e["reason"]) for e in result.excluded)
    grades = collections.Counter((q.get("grade"), q.get("source")) for q in questions)
    print(f"composed {len(questions):,} questions  {result.counts}")
    print(f"excluded {len(result.excluded):,}")
    for (source, reason), n in reasons.most_common():
        print(f"  {n:5,}  {source:20s} {reason}")
    print("by grade:", dict(sorted(collections.Counter(q.get("grade") for q in questions).items())))
    print(f"official scheme coverage: {covered:,}/{len(questions):,}")
    if check:
        print("\n--check: nothing written")
        return 0

    body = json.dumps(payload, ensure_ascii=False)
    for target in (paths.served, paths.apk):
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, target)
    paths.excluded.write_text(json.dumps(
        {"excluded": result.excluded, "counts": dict(collections.Counter(
            e["reason"] for e in result.excluded))}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nwrote {paths.served}\nwrote {paths.apk}\nwrote {paths.excluded}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    return run(DEFAULT, check=ap.parse_args().check)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_merge_question_banks.py -q`
Expected: all pass. Then `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/merge_question_banks.py --check` and report its output.

---

### Task 6: The web pool keeps the record it loaded

**Files:**
- Modify: `src/academicos/assessment/pool.py` (`PoolQuestion`, baked loader)
- Modify: `src/academicos/assessment/mapping.py` (`to_question_schema`)
- Test: `tests/test_pool_record_fidelity.py`

**Depends on:** Task 2.

The baked loader built a bare `Question` from the stem and threw the record away, so `to_question_schema` re-invented it: source always `cbse_board_paper`, parts empty, the official scheme replaced by one rebuilt from `modelAnswer` alone — which is empty for every SQP MCQ, so all 404 lost their key. The served bank's records already **are** the API wire shape (3,286 board and 720 CBE validate as `QuestionSchema`), so the fix is to keep the record and validate it.

- [ ] **Step 1: Write the failing test**

```python
"""The baked-bank path must serve the record it loaded, not a reconstruction."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from academicos.assessment import mapping, pool as pool_module  # noqa: E402
from academicos.config import Config  # noqa: E402
from academicos.corpus import bank_merge as bm  # noqa: E402
from test_bank_merge import board, cbe_mcq  # noqa: E402


def _pool(tmp_path, monkeypatch, records, subject, grade):
    path = tmp_path / "q.json"
    path.write_text(json.dumps({"questions": records}), encoding="utf-8")
    monkeypatch.setattr(pool_module, "_baked_bank_paths", lambda cfg: [path])
    cfg = Config(data_root=tmp_path)
    cfg._load_baked_questions = True
    return pool_module.build_pool(cfg, subject=subject, grade=grade)


def test_source_is_the_records_own(tmp_path, monkeypatch):
    rec, _ = bm.normalise(cbe_mcq())
    built = _pool(tmp_path, monkeypatch, [rec], "Mathematics", "VII")
    assert mapping.to_question_schema(built.questions[0]).source == "cbse_question_bank"


def test_the_official_objective_scheme_survives(tmp_path, monkeypatch):
    """Every SQP MCQ lost its key: the key is in markingPoints, modelAnswer is empty."""
    rec, _ = bm.normalise(cbe_mcq())
    schema = mapping.to_question_schema(
        _pool(tmp_path, monkeypatch, [rec], "Mathematics", "VII").questions[0])
    assert schema.answer_scheme.metadata["correctOption"] == "B"
    assert schema.answer_scheme.marking_points


def test_inline_options_reach_the_stem(tmp_path, monkeypatch):
    rec, _ = bm.normalise(cbe_mcq())
    schema = mapping.to_question_schema(
        _pool(tmp_path, monkeypatch, [rec], "Mathematics", "VII").questions[0])
    assert "(A) avoid" in schema.stem


def test_board_questions_come_first(tmp_path, monkeypatch):
    """Existing class 10/12 papers must not be silently re-composed from SQP items."""
    sqp = board(2, id="cbse:sqp:X:Science:2", source="cbse_sample_paper",
                stem="Describe how a rainbow is formed after rain, question 2.")
    built = _pool(tmp_path, monkeypatch, [sqp, board()], "Science", "X")
    assert [q.id for q in built.questions][0] == board()["id"]


def test_the_fallback_applies_the_same_quality_gates(tmp_path, monkeypatch):
    fig = board(3, stem="Study the figure given below and answer the question that follows.")
    built = _pool(tmp_path, monkeypatch, [fig], "Science", "X")
    assert built.questions == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_pool_record_fidelity.py -q`
Expected: failures on source, scheme, ordering and gates.

- [ ] **Step 3: Implement**

Add to `PoolQuestion`:

```python
    # The served-bank record this came from, when it came from the baked bank.
    # Kept whole because that record already IS the API wire shape; rebuilding
    # it from the stem lost the source, the parts and every SQP MCQ's key.
    record: dict | None = None
```

In the baked loader, before building the `Question`, apply the primary path's quality gates (read `pool.py:476-508` for their exact names — `needs_missing_figure`, `looks_truncated`, `has_broken_options`, and the near-duplicate index) and `continue` on any hit, counting it in the same `skipped_*` counters the log line reports. Set `record=item` on the `PoolQuestion`. After the loop, order board records first, stably:

```python
pool.questions.sort(key=lambda pq: 0 if (pq.record or {}).get("source") == "cbse_board_paper" else 1)
```

In `mapping.to_question_schema`, at the top:

```python
    if pq.record is not None:
        # The baked bank's records are already the wire shape; serve them as-is.
        return QuestionSchema.model_validate(pq.record)
```

Run `grep -rn "PoolQuestion(" src/academicos` to confirm no other constructor breaks (the field has a default).

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_pool_record_fidelity.py tests/test_grade_routing.py tests/test_assessment_pool.py -q`
Expected: all pass. If the stable board-first sort changes a selection test elsewhere, report it — do not loosen it.

---

### Task 7: The web PDF stops crashing and stops garbling

**Files:**
- Modify: `src/academicos/assessment/pdf.py`
- Modify: `src/academicos/assessment/schemas.py` (`GeneratedQuestionSchema`)
- Modify: the code that builds `GeneratedQuestionSchema` (`grep -rn "GeneratedQuestionSchema(" src/academicos`)
- Modify: `src/academicos/assessment/routes.py` (export endpoint ~line 569)
- Test: `tests/test_assessment_pdf.py` (append)

**Depends on:** Task 2 (routes.py).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_assessment_pdf.py`)

```python
from academicos.assessment.pdf import export_answer_key_pdf, pdf_safe  # noqa: E402


def _paper_with(gq, answer="x"):
    now = datetime.now(timezone.utc)
    section = GeneratedSectionSchema(section_id="s", label="A", name="Q",
                                     questions=[gq], total_marks=gq.marks)
    meta = PaperMetadataSchema(assessment_title="T", subject="Science", grade=9,
                               total_marks=gq.marks, duration_minutes=60, generated_at=now)
    return GeneratedPaper(id="p", assessment_id="a", sections=[section],
                          metadata=meta, answer_key={"1": answer})


def _gq(stem, qtype="mcq", marks=1):
    return GeneratedQuestionSchema(question_id="q", display_number=1, stem=stem,
                                   marks=marks, bloom_level="remember",
                                   difficulty="easy", type=qtype)


def test_more_than_four_option_labels_do_not_crash(tmp_path):
    """labels="ABCD" indexed by position raised IndexError on a fifth."""
    stem = "Pick one. (A) a (B) b (C) c (D) d (D) e"
    assert export_pdf(_paper_with(_gq(stem)), tmp_path).exists()


def test_a_question_taller_than_a_page_exports(tmp_path):
    """Each question was one Table row, which cannot split: LayoutError, HTTP 500."""
    stem = "Explain in detail. " + ("This sentence is deliberately long. " * 900)
    assert export_pdf(_paper_with(_gq(stem, "long_answer", 5)), tmp_path).exists()


def test_an_answer_taller_than_a_page_exports(tmp_path):
    paper = _paper_with(_gq("Explain photosynthesis fully.", "long_answer", 5),
                        answer="Value point. " * 3000)
    assert export_answer_key_pdf(paper, tmp_path).exists()


def test_subparts_of_a_descriptive_question_are_not_gridded_as_options(tmp_path):
    stem = "Two brothers share money. (a) Find each share. (b) Explain. (c) Check. (d) State."
    text = _extract_text(export_pdf(_paper_with(_gq(stem, "long_answer", 4)), tmp_path))
    assert "(A)" not in text and "(a) Find each share" in text


def test_math_italic_letters_survive():
    """'12𝑥2 + 11𝑥−15' printed as '122 + 11−15' -- the variable vanished."""
    assert pdf_safe("12\U0001d4652 + 11\U0001d465−15") == "12x2 + 11x-15"
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_assessment_pdf.py -q`
Expected: failures (`type` not a field, `pdf_safe` missing, IndexError, LayoutError).

- [ ] **Step 3: Implement**

`schemas.py` — add to `GeneratedQuestionSchema`:

```python
    # The question's type, so the renderer grids (A)-(D) only for an MCQ. Without
    # it, a descriptive question's sub-parts (a)-(d) were printed as options.
    # Empty for papers generated before this field existed.
    type: str = ""
```

and set `type=q.type` wherever a `GeneratedQuestionSchema` is built from a `QuestionSchema`.

`pdf.py`:

1. Port `frontend/lib/core/local_engine/pdf_text_safety.dart` exactly, so the web and phone papers print the same text. Add near the top of `pdf.py`:

```python
# A line-for-line port of frontend/lib/core/local_engine/pdf_text_safety.dart,
# so a question prints the same on the web as on the phone. The web had no
# equivalent: CBE Maths writes variables as Mathematical Alphanumeric letters
# (U+1D434-) and symbol-font private-use characters, and those vanished --
# "12x^2 + 11x - 15" printed as "122 + 11-15". In production it is worse: the
# container falls back to Helvetica (WinAnsi only) when DejaVu is missing.
_PDF_PUNCTUATION = (("—", "-"), ("–", "-"), ("•", "-"),
                    ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'))
_SUB_SUPER_DIGITS = str.maketrans(
    "₀₁₂₃₄₅₆₇₈₉"
    "⁰¹²³⁴⁵⁶⁷⁸⁹",
    "01234567890123456789")
_PDF_MATH = (
    ("−", "-"), ("√", "sqrt"), ("∴", "therefore"), ("∵", "because"),
    ("∠", "angle "), ("⇒", "=>"), ("⟹", "=>"), ("≠", "!="),
    ("≥", ">="), ("≤", "<="), ("∈", "in"), ("∞", "infinity"),
    ("∆", "triangle "), ("Δ", "triangle "), ("∫", "integral"),
    ("′", "'"), ("θ", "theta"), ("π", "pi"), ("⃗", ""),
    ("̂", ""), ("₹", "Rs."), ("…", "..."),
    ("ଶ", "2"),              # an OCR artifact standing in for a superscript 2
    ("\U0001d6fc", "alpha"), ("\U0001d703", "theta"), ("\U0001d70b", "pi"),
)
_PRIVATE_USE = re.compile("[-]")
_MATH_LETTER_BLOCKS = (0x1D400, 0x1D434, 0x1D468, 0x1D49C, 0x1D4D0, 0x1D504, 0x1D538,
                       0x1D56C, 0x1D5A0, 0x1D5D4, 0x1D608, 0x1D63C, 0x1D670)


def _demathify(cp: int) -> int | None:
    """A styled Mathematical Alphanumeric letter or digit, back to plain ASCII."""
    for start in _MATH_LETTER_BLOCKS:
        offset = cp - start
        if 0 <= offset < 52:
            return 0x41 + offset if offset < 26 else 0x61 + offset - 26
    if 0x1D7CE <= cp <= 0x1D7FF:
        return 0x30 + (cp - 0x1D7CE) % 10
    return None


def pdf_safe(text: str) -> str:
    """Text a base PDF font can print, keeping every symbol's meaning."""
    for a, b in _PDF_PUNCTUATION:
        text = text.replace(a, b)
    text = text.translate(_SUB_SUPER_DIGITS)
    for a, b in _PDF_MATH:
        text = text.replace(a, b)
    text = _PRIVATE_USE.sub("", text)
    return "".join(chr(_demathify(ord(c)) or ord(c)) for c in text)
```

Then apply it inside `escape()` so every Paragraph gets it:

```python
def escape(text: str) -> str:
    text = pdf_safe(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
```

2. In `_question_flowables`, split options only for an objective question:

```python
    objective = gq.type in ("", "mcq", "assertion_reason")
    head, options = split_stem_and_options(gq.stem) if objective else (gq.stem.strip(), [])
```

and replace `labels = "ABCD"` / `labels[idx]` with `chr(ord("A") + idx)`.

3. Make the question row and the answer-key table split across pages: construct both `Table`s with `splitInRow=1`, and drop the `KeepTogether` around an oversized question (keep it for questions that fit — `KeepTogether` is harmless when its content is smaller than a frame).

`routes.py` — around the two `pdf_export.export_*` calls, turn a render failure into a clear 422 instead of a bare 500:

```python
    try:
        path = pdf_export.export_pdf(paper, out_dir, template=template, watermark_id=watermark_id)
    except Exception as exc:   # ReportLab raises LayoutError/IndexError/ValueError
        log.exception("paper %s failed to render", paper_id)
        raise HTTPException(422, f"this paper could not be rendered: {exc}") from exc
```

(and the same around `export_answer_key_pdf`).

- [ ] **Step 4: Run to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_assessment_pdf.py -q`
Expected: all pass, including the pre-existing watermark tests.

---

### Task 8: The relink report and the retired APK writer

**Files:**
- Modify: `src/academicos/assessment/question_bank.py` (`RelinkReport`, `relink_answer_schemes`)
- Modify: `scripts/export_mobile_corpus.py`
- Test: `tests/test_question_bank.py`, `tests/test_export_mobile_corpus.py`

**Depends on:** Task 5.

After the merge, `enrich_question_bank.py --check` reported **50.4%** coverage when the real figure is **93.9%**: CBE/SQP ids are not `cbse:q:src:<hash>:<n>`, so they fall into "did not reach an answer key" although they carry their own official scheme. It does not change them (verified: 0 fields), it only miscounts them. Separately, `export_mobile_corpus.py` writes a registry-derived board-only corpus straight over the APK asset.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_question_bank.py (append)
def test_relink_counts_a_carried_official_scheme_as_covered(tmp_path):
    """A CBE/SQP record keeps its builder's scheme and must count toward coverage."""
    rec = {"id": "cbe:q:Maths7X1", "answerScheme": {
        "provenance": "cbse_marking_scheme", "modelAnswer": "5",
        "markingPoints": [{"description": "5"}]}}
    before = json.dumps(rec, sort_keys=True)
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    report = relink_answer_schemes([rec], idx, parse_dir=tmp_path)
    assert json.dumps(rec, sort_keys=True) == before
    assert report.carried_official == 1
    assert report.with_scheme == 1
```

```python
# tests/test_export_mobile_corpus.py
"""export_mobile_corpus.py must never overwrite the APK corpus with a board-only export."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "frontend" / "assets" / "corpus" / "questions.json"


def test_it_refuses_to_write_the_apk_asset():
    before = ASSET.read_bytes() if ASSET.exists() else None
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "export_mobile_corpus.py")],
                          capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode != 0
    assert "merge_question_banks.py" in (proc.stdout + proc.stderr)
    assert (ASSET.read_bytes() if ASSET.exists() else None) == before
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_question_bank.py tests/test_export_mobile_corpus.py -q -k "carried or refuses"`
Expected: `AttributeError: carried_official`; the export script exits 0 and writes.

- [ ] **Step 3: Implement**

In `RelinkReport` add `carried_official: int = 0` and a report line `"  carried an official scheme from its builder : {:,}"`. In `relink_answer_schemes`, on the path where `parse_question_id` returns None (currently `no_source_hash += 1; continue`), first check the record's own scheme; if `provenance == "cbse_marking_scheme"` and it has marking points or a model answer, increment `carried_official` and count it in the with-scheme total, then `continue` without touching it. Read the function to find where `with_scheme` is computed and include `carried_official` there.

Replace `scripts/export_mobile_corpus.py`'s `main()` body with a refusal, keeping the module docstring and adding why:

```python
def main() -> int:
    print(
        "export_mobile_corpus.py no longer writes the APK corpus.\n"
        "It rebuilt it from registry question papers only -- grades X and XII -- and\n"
        "wrote that straight over frontend/assets/corpus/questions.json, which would\n"
        "silently delete every merged CBE and SQP question from the offline app.\n"
        "The APK copy is now written by scripts/merge_question_banks.py (and kept in\n"
        "step by scripts/enrich_question_bank.py). Run those instead.",
        file=sys.stderr)
    return 2
```

with `raise SystemExit(main())` under `__main__`. Remove imports that become unused. `grep -rn export_mobile_corpus` across the repo (docs, .github, scripts) and update any instruction that tells someone to run it.

- [ ] **Step 4: Run to verify they pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_question_bank.py tests/test_export_mobile_corpus.py -q`
Expected: all pass.

---

### Task 9: The phone loader skips a bad row instead of failing the corpus

**Files:**
- Modify: `frontend/lib/core/local_engine/corpus_repository.dart`
- Test: `frontend/test/local_engine/corpus_repository_skip_test.dart`

Today one row that `Question.fromJson` rejects throws out of `_parseQuestions`; for the bundled asset that happens before `runApp()`, so the app never leaves its splash screen.

- [ ] **Step 1: Write the failing test**

```dart
import 'dart:convert';

import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _good(String id) => {
      'id': id, 'questionBankId': 'b', 'subject': 'Science', 'grade': 7,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'Why is the sky blue?', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': {
        'totalMarks': 1, 'markingPoints': <dynamic>[], 'rubricLevels': <dynamic>[],
        'commonErrors': <String>[], 'alternativeAnswers': <String>[],
        'modelAnswer': 'Scattering', 'modelAnswerLatex': '',
      },
      'estimatedTimeMinutes': 2, 'marks': 1, 'language': 'en',
      'source': 'cbse_question_bank', 'qualityScore': 0.8, 'tags': <String>[],
      'createdAt': '2026-09-19T00:00:00.000Z', 'updatedAt': '2026-09-19T00:00:00.000Z',
    };

void main() {
  test('a row Question.fromJson rejects is skipped and counted', () {
    final bad = _good('bad')..remove('competencyIds');
    final raw = jsonEncode({'questions': [_good('a'), bad, _good('b')]});
    final result = CorpusRepository.parseQuestionsForTest(raw);
    expect(result.questions.map((q) => q.id), ['a', 'b']);
    expect(result.skipped, 1);
  });

  test('a corpus with no readable row yields zero questions, not an exception', () {
    final bad = _good('bad')..remove('stemLatex');
    final result = CorpusRepository.parseQuestionsForTest(jsonEncode({'questions': [bad]}));
    expect(result.questions, isEmpty);
    expect(result.skipped, 1);
  });
}
```

- [ ] **Step 2: Run to verify it fails**

Run (from `frontend/`): `flutter test test/local_engine/corpus_repository_skip_test.dart`
Expected: compile error — `parseQuestionsForTest` does not exist.

- [ ] **Step 3: Implement**

```dart
/// What a corpus parse produced: the rows that decoded, and how many did not.
class ParsedCorpus {
  const ParsedCorpus(this.questions, this.skipped);
  final List<Question> questions;
  final int skipped;
}
```

Replace `_parseQuestions` with a version that decodes row by row:

```dart
  /// Decode every row that can be decoded, and count the rest.
  ///
  /// One row Question.fromJson rejects used to throw out of the whole parse.
  /// For the bundled asset that ran before runApp(), so a single malformed
  /// question kept the app on its splash screen for good. A bad row now costs
  /// that one question and is counted in [skippedRows].
  static ParsedCorpus _parse(String raw) {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final rows = (data['questions'] as List?) ?? const [];
    final out = <Question>[];
    var skipped = 0;
    for (final e in rows) {
      try {
        out.add(Question.fromJson(Map<String, dynamic>.from(e as Map)));
      } catch (err) {
        skipped++;
        debugPrint('corpus: skipped a row Question.fromJson rejected: $err');
      }
    }
    return ParsedCorpus(out, skipped);
  }

  @visibleForTesting
  static ParsedCorpus parseQuestionsForTest(String raw) => _parse(raw);

  int _skippedRows = 0;

  /// Rows the loaded corpus could not decode. Zero for a healthy corpus.
  int get skippedRows => _skippedRows;
```

In `_tryLoadDownloaded`, treat a download with no readable row as a failed download so the bundled asset is used:

```dart
      final parsed = _parse(await downloaded.readAsString());
      if (parsed.questions.isEmpty) return null;
      _skippedRows = parsed.skipped;
      return parsed.questions;
```

and in `reload()` replace the bundled branch with:

```dart
    try {
      final parsed = _parse(await rootBundle.loadString('assets/corpus/questions.json'));
      _questions = parsed.questions;
      _skippedRows = parsed.skipped;
    } catch (err) {
      // Unreadable JSON or a missing asset. Start with an empty corpus rather
      // than hang on the splash screen; the UI shows "no questions".
      debugPrint('corpus: bundled asset could not be read: $err');
      _questions = const [];
      _skippedRows = 0;
    }
```

Add `import 'package:flutter/foundation.dart';` if `debugPrint`/`visibleForTesting` are not already imported.

- [ ] **Step 4: Run to verify it passes**

Run (from `frontend/`): `flutter test test/local_engine/corpus_repository_skip_test.dart test/local_engine/`
Expected: all pass.

---

### Task 10: Scan & Grade flags what it cannot score

**Files:**
- Modify: `frontend/lib/core/local_engine/answer_evaluation.dart`
- Test: `frontend/test/local_engine/answer_evaluation_unscorable_test.dart`

A marking point with an empty keyword and no synonyms has nothing to match, so it is never awarded — and the confidence formula `0.9 - 0.5 * (1 - |2 * ratio - 1|)` gives a total miss the **same 0.9** as a full match. Every CBE and SQP descriptive answer therefore scored 0 at high confidence with no review flag. Merged MCQs are fixed by the objective scheme (Task 4); this task makes the descriptive case honest instead of inventing keywords.

- [ ] **Step 1: Write the failing test**

Built entirely from JSON maps: `AnswerScheme.toJson()` leaves nested
`MarkingPoint` objects rather than maps (no `explicitToJson`), so feeding it back
into `Question.fromJson` would fail its `as Map` cast.

```dart
import 'package:academicos/core/local_engine/answer_evaluation.dart';
import 'package:academicos/domain/entities/question.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _schemeJson() => {
      'totalMarks': 2,
      'markingPoints': [
        {'id': 'mp1', 'description': 'Scattering of sunlight by air',
         'marks': 2, 'keyword': '', 'isRequired': true},
      ],
      'rubricLevels': <dynamic>[], 'commonErrors': <String>[],
      'alternativeAnswers': <String>[],
      'modelAnswer': 'Scattering of sunlight by air', 'modelAnswerLatex': '',
    };

Question _question() => Question.fromJson({
      'id': 'q1', 'questionBankId': 'b', 'subject': 'Science', 'grade': 7,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'Why is the sky blue?', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': _schemeJson(), 'estimatedTimeMinutes': 2, 'marks': 2,
      'language': 'en', 'source': 'cbse_question_bank', 'qualityScore': 0.8,
      'tags': <String>[], 'createdAt': '2026-09-19T00:00:00.000Z',
      'updatedAt': '2026-09-19T00:00:00.000Z',
    });

void main() {
  test('a scheme with nothing to match is sent for review, not scored 0 confidently', () {
    final scheme = AnswerScheme.fromJson(_schemeJson());
    final result = evaluateAnswer(_question(), scheme,
        'Because blue light is scattered more by the atmosphere.');
    expect(result.needsReview, isTrue);
    expect(result.confidence, lessThan(0.5));
  });
}
```

- [ ] **Step 2: Run to verify it fails**

Run (from `frontend/`): `flutter test test/local_engine/answer_evaluation_unscorable_test.dart`
Expected: `needsReview` is false and confidence is 0.9.

- [ ] **Step 3: Implement**

In `evaluateAnswer`, after the marking-point outcomes are computed and before the confidence formula, detect points with no usable candidate:

```dart
  // A marking point whose keyword and synonyms are all empty cannot be matched
  // against anything, so "not awarded" says nothing about the answer. CBE and
  // SQP schemes carry the official value point as a description only. Treat
  // such a scheme as unscorable and hand it to the teacher, rather than report
  // 0 marks at 0.9 confidence.
  final unscorable = scheme.markingPoints.isNotEmpty &&
      scheme.markingPoints.every((p) =>
          p.keyword.trim().isEmpty && p.synonyms.every((s) => s.trim().isEmpty));
```

and when `unscorable` is true, return early with `awardedMarks: 0`, `verdict: 'needsReview'`, `confidence: 0.2`, `needsReview: true`, and a reasoning string that says the scheme has no keywords to match and quotes the first marking-point description so the teacher can mark it. Use the same `LocalEvaluation` constructor arguments the function already uses. If `'needsReview'` is not an accepted verdict value, grep for how verdicts are consumed and use the closest existing value (`'noCredit'`), keeping `needsReview: true`.

- [ ] **Step 4: Run to verify it passes**

Run (from `frontend/`): `flutter test test/local_engine/`
Expected: all pass, including existing evaluation tests.

---

### Task 13: The phone's Quick Paper — same grade only, every section filled

**Files:**
- Modify: `frontend/lib/core/local_engine/local_api_client.dart` (quick path ~line 395-405; `generatePaper` metadata ~line 293-294)
- Modify: `frontend/lib/presentation/syllabus/pages/syllabus_page.dart:148`
- Test: `frontend/test/local_engine/select_for_sections_test.dart`

The phone is the primary surface, and its Quick Paper undoes the merge in three lines:

```dart
final selected = (candidates.isNotEmpty ? candidates
    : CorpusRepository.instance.all.where((q) => q.subject == request.subject).toList()).take(11).toList();
```

With no same-grade question it silently takes **every grade** of the subject — already happening today: a class 7 Science request returns eleven class 10 questions. It then takes the first eleven hits whatever their marks, and `generatePaper` drops each one that fits no section: a 20-mark class 9 Science paper came out as 2 questions worth 4 marks. And the paper's grade is `request.selectedQuestions.firstOrNull?.grade`, the first question's, not the teacher's.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/domain/entities/blueprint.dart';
import 'package:academicos/domain/entities/enums.dart';
import 'package:academicos/domain/entities/question.dart';
import 'package:flutter_test/flutter_test.dart';

Question _q(String id, int marks) => Question.fromJson({
      'id': id, 'questionBankId': 'b', 'subject': 'Science', 'grade': 9,
      'chapterIds': <String>[], 'competencyIds': <String>[],
      'bloomLevel': 'understand', 'difficulty': 'easy', 'type': 'short_answer',
      'stem': 'Question $id', 'stemLatex': '', 'parts': <dynamic>[],
      'answerScheme': {
        'totalMarks': marks, 'markingPoints': <dynamic>[], 'rubricLevels': <dynamic>[],
        'commonErrors': <String>[], 'alternativeAnswers': <String>[],
        'modelAnswer': 'a', 'modelAnswerLatex': '',
      },
      'estimatedTimeMinutes': 2, 'marks': marks, 'language': 'en',
      'source': 'cbse_question_bank', 'qualityScore': 0.8, 'tags': <String>[],
      'createdAt': '2026-09-19T00:00:00.000Z', 'updatedAt': '2026-09-19T00:00:00.000Z',
    });

SectionBlueprint _s(String id, int marks, int count) => SectionBlueprint(
      id: id, label: id, name: id, marksPerQuestion: marks, questionCount: count,
      totalMarks: marks * count, allowedBloomLevels: const [BloomLevel.understand],
      allowedDifficulties: const [Difficulty.easy]);

void main() {
  test('each section is filled from questions of its own marks', () {
    // Eleven one-markers first: take(11) would have filled only the MCQ section.
    final pool = [
      for (var i = 0; i < 11; i++) _q('one$i', 1),
      for (var i = 0; i < 3; i++) _q('two$i', 2),
      for (var i = 0; i < 3; i++) _q('three$i', 3),
    ];
    final picked = selectForSections(pool, [_s('A', 1, 5), _s('B', 2, 3), _s('C', 3, 3)]);
    expect(picked.where((q) => q.marks == 1), hasLength(5));
    expect(picked.where((q) => q.marks == 2), hasLength(3));
    expect(picked.where((q) => q.marks == 3), hasLength(3));
  });

  test('a question is never used twice', () {
    final pool = [_q('a', 1), _q('b', 1)];
    final picked = selectForSections(pool, [_s('A', 1, 2), _s('A2', 1, 2)]);
    expect(picked.map((q) => q.id).toSet(), hasLength(picked.length));
  });
}
```

Import paths for `SectionBlueprint`, `BloomLevel`, `Difficulty` must match the project — find them with `grep -rn "class SectionBlueprint" frontend/lib`.

- [ ] **Step 2: Run to verify it fails**

Run (from `frontend/`): `flutter test test/local_engine/select_for_sections_test.dart`
Expected: compile error — `selectForSections` does not exist.

- [ ] **Step 3: Implement**

Add a top-level function to `local_api_client.dart`:

```dart
/// Fill each section with questions of exactly its marks, in pool order,
/// never reusing one.
///
/// The quick path used to take the first eleven search hits whatever their
/// marks, and generatePaper then dropped every one that fitted no section: a
/// 20-mark class 9 Science paper came out as 2 questions worth 4 marks.
List<Question> selectForSections(List<Question> pool, List<SectionBlueprint> sections) {
  final used = <String>{};
  final out = <Question>[];
  for (final section in sections) {
    final picks = pool
        .where((q) => q.marks == section.marksPerQuestion && !used.contains(q.id))
        .take(section.questionCount)
        .toList();
    for (final q in picks) {
      used.add(q.id);
      out.add(q);
    }
  }
  return out;
}
```

and an exception the UI can show:

```dart
/// No question exists for this subject at this grade. Raised instead of
/// quietly serving another grade's questions under this grade's name.
class NoQuestionsForGradeException implements Exception {
  NoQuestionsForGradeException(this.subject, this.grade);
  final String subject;
  final int grade;
  @override
  String toString() => 'There are no $subject questions for class $grade yet.';
}
```

Replace the quick path's selection:

```dart
    final pool = CorpusRepository.instance.search(QuestionSearchParams(
      subject: request.subject,
      grade: request.grade,
      chapterIds: request.chapterIds.isEmpty ? null : request.chapterIds,
    ));
    if (pool.isEmpty) {
      throw NoQuestionsForGradeException(request.subject, request.grade);
    }
    final selected = selectForSections(pool, assessment.blueprint.sections);
```

(no `limit` — every question of the grade is a candidate; check that `search` applies `limit` only when it is non-null). In `generatePaper`, take subject and grade from the assessment it already loaded, not from the first question:

```dart
        subject: assessment.subject,
        grade: assessment.grade,
```

In `syllabus_page.dart:148`, the label claims a provenance the bank no longer has:

```dart
                                      '${_selected!.questionCount} questions',
```

- [ ] **Step 4: Run to verify it passes**

Run (from `frontend/`): `flutter test test/local_engine/`
Expected: all pass. Then add one test to `frontend/test/local_engine/local_api_client_test.dart`, following that file's existing setup, asserting that `quickGeneratePaper` for a grade with no questions throws `NoQuestionsForGradeException`, and that a generated paper's `metadata.grade` equals the requested grade.

---

### Task 14: A chapter's name leads its tags

**Files:**
- Modify: `src/academicos/corpus/bank_merge.py`
- Modify: `scripts/merge_question_banks.py`
- Test: `tests/test_bank_merge.py`, `tests/test_merge_question_banks.py`

**Depends on:** Task 5.

The phone bundles no syllabus, so its chapter picker names a chapter by `tags[0]` of its first question (`corpus_repository.dart:118`). Board records put the chapter name there; CBE records put the topic — so class 6 Mathematics showed `decimals-6`, `basic-geometrical-ideas` and `ratio-and-proportion` all as "Algebra". The chapter tagger records only the id (`metadata.chapterTag.chapterId`), so the name comes from the syllabus.

- [ ] **Step 1: Write the failing test** (append to `tests/test_bank_merge.py`)

```python
def test_chapter_name_is_moved_to_the_front_of_tags():
    rec = board(source="cbse_question_bank", subject="Mathematics", grade=6,
                chapterIds=["decimals-6"], tags=["Algebra", "6N1a"])
    out = bm.apply_chapter_names([rec], {("Mathematics", 6, "decimals-6"): "Decimals"})
    assert out[0]["tags"] == ["Decimals", "Algebra", "6N1a"]


def test_board_records_keep_their_tags():
    rec = board(chapterIds=["x"], tags=["Light"])
    assert bm.apply_chapter_names([rec], {("Science", 10, "x"): "Other"})[0]["tags"] == ["Light"]


def test_an_unknown_chapter_leaves_tags_alone():
    rec = board(source="cbse_question_bank", chapterIds=["9N1e"], tags=["Number systems"])
    assert bm.apply_chapter_names([rec], {})[0]["tags"] == ["Number systems"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_bank_merge.py -q -k chapter`
Expected: `AttributeError: apply_chapter_names`.

- [ ] **Step 3: Implement** — in `bank_merge.py`:

```python
def apply_chapter_names(records: list[dict],
                        names: dict[tuple[str, int, str], str]) -> list[dict]:
    """Put each non-board record's syllabus chapter name first in its tags.

    The phone bundles no syllabus, so its chapter picker names a chapter by the
    first tag of its first question. CBE records carried a topic there, which
    labelled several different chapters "Algebra". Board records already lead
    with the chapter name and are left alone. A chapter id the syllabus does not
    know -- a raw CBE content code like "9N1e" -- keeps its tags unchanged.
    """
    out = []
    for rec in records:
        chapter = (rec.get("chapterIds") or [None])[0]
        name = names.get((rec.get("subject"), rec.get("grade"), chapter))
        if rec.get("source") == BOARD_SOURCE or not name:
            out.append(rec)
            continue
        rec = dict(rec)
        rec["tags"] = [name] + [t for t in rec.get("tags") or [] if t != name]
        out.append(rec)
    return out
```

In `merge_question_banks.py`, after `compose`:

```python
    questions = bank_merge.apply_chapter_names(result.questions, _chapter_names(result.questions))
```

with

```python
def _chapter_names(questions: list[dict]) -> dict[tuple[str, int, str], str]:
    """(subject, grade, chapter id) -> chapter name, from the syllabus files."""
    from academicos.syllabus.cbse_syllabus import load_syllabus

    names: dict[tuple[str, int, str], str] = {}
    for subject, grade in {(q.get("subject"), q.get("grade")) for q in questions}:
        syllabus = load_syllabus(subject, grade) if subject and grade else None
        if syllabus is None:
            continue
        for _unit, chapter in syllabus.all_chapters():
            names[(subject, grade, chapter.id)] = chapter.name
    return names
```

and use `questions` (not `result.questions`) for everything written after that line.

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_bank_merge.py tests/test_merge_question_banks.py -q`
Expected: all pass.

---

### Task 11: Run the pipeline for real

**Depends on:** Tasks 1–10 all green in the full suite.

- [ ] **Step 1: Back up the data files**

```bash
mkdir -p ../merge-backup && cp academicos-data/syllabus/questions.json frontend/assets/corpus/questions.json academicos-data/corpus/cbse-cbe/questions.json academicos-data/corpus/cbse-sqp/questions.json ../merge-backup/
```

- [ ] **Step 2: Rebuild CBE so records carry passages, then restore chapter tags**

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/build_cbe_bank.py
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/apply_chapter_tags.py
```

`apply_chapter_tags.py` also rewrites the SQP bank and the served bank; verify with a timestamp-insensitive comparison against `HEAD` that SQP changed only in `chapterTaggedAt`, and restore it with `git checkout HEAD -- academicos-data/corpus/cbse-sqp/questions.json` if so. Leave the served bank — the merge rewrites it.

- [ ] **Step 3: Merge, check first**

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/merge_question_banks.py --check
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/merge_question_banks.py
```

- [ ] **Step 4: Relink and enrich**

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/enrich_question_bank.py --check
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/enrich_question_bank.py
```

Confirm afterwards that the served bank and APK copy are still byte-identical (`cmp`).

- [ ] **Step 5: Measure and record**

Report: total served; by grade × source; classes 6–9 by subject; every exclusion reason with its count; scheme coverage. Compare to the spec's projection (§3) and explain any difference.

---

### Task 12: Verify end to end

- [ ] **Step 1: Every served row decodes on the phone** — add `frontend/test/local_engine/real_asset_contract_test.dart`:

```dart
import 'dart:convert';
import 'dart:io';

import 'package:academicos/domain/entities/question.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('every row of the bundled corpus decodes with Question.fromJson', () {
    final raw = File('assets/corpus/questions.json').readAsStringSync();
    final rows = (jsonDecode(raw) as Map<String, dynamic>)['questions'] as List;
    final failures = <String>[];
    for (final e in rows) {
      try {
        Question.fromJson(Map<String, dynamic>.from(e as Map));
      } catch (err) {
        failures.add('${(e as Map)['id']}: $err');
      }
    }
    expect(failures, isEmpty, reason: failures.take(5).join('\n'));
    expect(rows.length, greaterThan(3286));
  });
}
```

Run: `flutter test` (whole `frontend/` suite). Expected: all pass.

- [ ] **Step 2: Full Python suite** — `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests -q`. Expected: all pass.

- [ ] **Step 3: Real papers through the real route.** With no registry (production's configuration — point `Config.data_root` at an empty temp directory and set `_load_baked_questions=True`), call `routes.quick_generate_paper(QuickPaperRequest(subject=..., grade=...))` for Mathematics 6, 7, 8, 9; Science 7 and 9; English 9; and History 12, Social Science 10, Geography 12 (the four that returned 500 in the research). For each: export the paper **and** the answer key, open both PDFs with PyMuPDF, and check —
  - every question's grade in the paper equals the requested grade;
  - the header says the requested class;
  - MCQs show options, and the answer key's letter is one of them;
  - no `(pending teacher entry)` rows for questions whose record carries a scheme;
  - for the class 10/12 papers, no export error, and board-paper questions still make up the paper where enough exist.

- [ ] **Step 4: Report** the paper-level results and the Task 11 numbers against the spec's projection.
