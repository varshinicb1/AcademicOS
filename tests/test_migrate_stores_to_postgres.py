"""R-A1: academicos.storage.migrate_stores copies both SQLite stores into Postgres, and the app
then reads the same data there. Needs a Postgres (ACOS_STORE_PG_HOST or ACOS_TEST_PG_HOST)."""
from __future__ import annotations

import os
import uuid

import pytest

def _pg_env() -> dict[str, str] | None:
    if os.environ.get("ACOS_STORE_PG_HOST"):
        pre = "ACOS_STORE_PG_"
    elif os.environ.get("ACOS_TEST_PG_HOST"):
        pre = "ACOS_TEST_PG_"
    else:
        return None
    return {f"ACOS_STORE_PG_{k}": os.environ.get(pre + k, d) for k, d in
            (("HOST", ""), ("PORT", "5432"), ("DB", "postgres"), ("USER", "postgres"), ("PASSWORD", ""))}


pytestmark = pytest.mark.skipif(_pg_env() is None, reason="set ACOS_STORE_PG_HOST or ACOS_TEST_PG_HOST")


def _script():
    from academicos.storage import migrate_stores
    return migrate_stores


@pytest.fixture
def env(monkeypatch):
    for k, v in _pg_env().items():
        monkeypatch.setenv(k, v)
    tag = uuid.uuid4().hex[:8]
    monkeypatch.setenv("ACOS_PG_SCHEMA_CURRICULUM", f"mig_curriculum_{tag}")
    monkeypatch.setenv("ACOS_PG_SCHEMA_OPERATIONS", f"mig_operations_{tag}")
    yield tag
    import psycopg
    from academicos.storage import pg_sqlite
    pg_sqlite.close_idle()
    with psycopg.connect(**pg_sqlite._dsn(), autocommit=True) as c:
        c.execute(f"DROP SCHEMA IF EXISTS mig_curriculum_{tag} CASCADE")
        c.execute(f"DROP SCHEMA IF EXISTS mig_operations_{tag} CASCADE")


def _sqlite_stores(tmp_path, monkeypatch):
    """Both stores in SQLite, filled through their own methods, as the live service fills them."""
    monkeypatch.setenv("ACOS_STORE_BACKEND", "sqlite")
    from academicos.curriculum.store import CurriculumStore
    from academicos.operations.store import OperationsStore
    cs = CurriculumStore(tmp_path / "curriculum.sqlite")
    year = cs.create_academic_year(school_id="school_1", label="2026-27", start_date="2026-04-01",
                                   end_date="2027-03-31")
    grade = cs.create_grade(academic_year_id=year.id, number=10)
    for name in ("B", "C", "D"):
        cs.create_section(grade_id=grade.id, name=name)
    cs.create_subject(grade_id=grade.id, name="Science")
    cs.create_term(academic_year_id=year.id, name="Term 1", start_date="2026-04-01", end_date="2026-09-30")
    ops = OperationsStore(tmp_path / "operations.sqlite")
    ops.deliver_inline = True
    ops.notify(school_id="school_1", user_ids=["u1", "u2"], kind="holiday_declared",
               params={"title": "Holiday", "body": "Diwali"}, link="/my-day", dedupe_key="h1")
    for _ in range(3):
        ops.create_practice(student_id="s1", subject="Science", grade=10, chapter_ids=["c1"],
                            questions=[{"id": "q1", "marks": 1}])
    expected = {
        "sections": [s.name for s in cs.sections_for_grade(grade.id)],
        "terms": [t.name for t in cs.terms_for_year(year.id)],
        "practice": [p["id"] for p in ops.practice_for("s1")],
        "notifications": sorted(n["user_id"] for n in ops._fetchall("SELECT user_id FROM notifications")),
    }
    cs.conn.commit()
    ops.conn.commit()
    cs.conn.close()
    ops.conn.close()
    return year.id, grade.id, expected


def test_both_stores_copy_and_read_the_same_on_postgres(tmp_path, monkeypatch, env):
    year_id, grade_id, expected = _sqlite_stores(tmp_path, monkeypatch)
    mod = _script()
    summary = tmp_path / "summary.json"
    assert mod.main(["--curriculum", str(tmp_path / "curriculum.sqlite"),
                     "--operations", str(tmp_path / "operations.sqlite"), "--summary", str(summary),
                     "--latency"]) == 0

    monkeypatch.setenv("ACOS_STORE_BACKEND", "postgres")
    from academicos.curriculum.store import CurriculumStore
    from academicos.operations.store import OperationsStore
    cs = CurriculumStore(tmp_path / "curriculum.sqlite")
    ops = OperationsStore(tmp_path / "operations.sqlite")
    assert cs.conn.schema == f"mig_curriculum_{env}"
    assert [s.name for s in cs.sections_for_grade(grade_id)] == expected["sections"]
    assert [t.name for t in cs.terms_for_year(year_id)] == expected["terms"]
    assert [p["id"] for p in ops.practice_for("s1")] == expected["practice"], "insertion order kept"
    assert sorted(n["user_id"] for n in ops._fetchall("SELECT user_id FROM notifications")) == expected["notifications"]

    # A row written after the copy gets a fresh rowid, after the copied ones.
    cs.create_section(grade_id=grade_id, name="E")
    names = [r["name"] for r in cs._fetchall("SELECT name FROM sections WHERE grade_id=? ORDER BY rowid", (grade_id,))]
    assert names[-1] == "E"

    import json
    record = json.loads(summary.read_text(encoding="utf-8"))
    assert record["curriculum"]["rows"]["sections"] == len(expected["sections"])
    assert len(record["operations"]["sha256"]) == 64


def test_a_second_run_replaces_rather_than_doubles(tmp_path, monkeypatch, env):
    _sqlite_stores(tmp_path, monkeypatch)
    mod = _script()
    args = ["--curriculum", str(tmp_path / "curriculum.sqlite"), "--operations", str(tmp_path / "operations.sqlite")]
    mod.main(args)
    first = mod.migrate_store("curriculum", tmp_path / "curriculum.sqlite")
    assert mod.main(args) == 0
    assert mod.migrate_store("curriculum", tmp_path / "curriculum.sqlite") == first


def test_a_value_sqlite_stored_with_another_type_than_its_column_stops_the_copy(tmp_path, monkeypatch, env):
    """SQLite types each value, not the column: an INTEGER column keeps 5.5 as it is. Postgres would
    round it to 6 without a word, and the app would read another number; the copy says where and stops."""
    import sqlite3
    _sqlite_stores(tmp_path, monkeypatch)
    raw = sqlite3.connect(tmp_path / "operations.sqlite")
    raw.execute("UPDATE practice_sets SET grade = 5.5")
    raw.commit()
    raw.close()
    with pytest.raises(SystemExit, match=r"practice_sets: rowid \d+ column 'grade' reads back as a int, was a float"):
        _script().migrate_store("operations", tmp_path / "operations.sqlite")
