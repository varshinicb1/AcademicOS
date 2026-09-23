"""The syllabus screen names the chapters of the book a class actually studies.

`GET /api/v1/syllabus/{subject}/{grade}` built each unit's `chapterNames` from
`units[].chapters`. fb0107a moved the book's own chapters to the document's top
level for the eight files whose units carry CBSE's marks weightage and no
chapter list of their own, so those pairs answered with units and no chapter
names at all -- a screen listing "Number Systems, 15 marks" and nothing under
it. What it replaced was worse (Mathematics 6 printed the new book's names
against the old book's ids, the rest printed a pre-2024 book's chapters), so
this is not a regression in truth, but it is a regression in usefulness.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.api.main import app  # noqa: E402

# The eight files fb0107a rewrote, plus the two it deliberately kept
# (Science 6 and Science 10 read the same edition as the taxonomy).
PAIRS = [("Mathematics", g) for g in range(6, 11)] + [("Science", g) for g in range(6, 11)]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_DATA_ROOT", str(tmp_path))
    with TestClient(app) as c:
        yield c


def _named(body: dict) -> list[str]:
    """Every chapter the response names, wherever the file keeps them.

    A class whose book divides into CBSE units lists its chapters under the
    unit that owns them. A class whose units are marks weightage only -- the
    eight files fb0107a rewrote -- lists the book's chapters at the top level,
    because no unit owns them and inventing an owner would be a claim the file
    does not make."""
    return [n for u in body["units"] for n in u["chapterNames"]] +            [c["name"] for c in body.get("chapters") or []]


@pytest.mark.parametrize("subject,grade", PAIRS)
def test_every_class_6_to_10_syllabus_names_its_chapters(client, subject, grade):
    body = client.get(f"/api/v1/syllabus/{subject}/{grade}").json()
    assert _named(body), f"{subject} {grade} answers with units and no chapter anywhere"


def test_a_chapter_is_named_once(client):
    body = client.get("/api/v1/syllabus/Mathematics/6").json()
    named = _named(body)
    assert len(named) == len(set(named)), named
    assert "Number Play" in named


def test_a_top_level_chapter_carries_the_id_the_bank_is_tagged_with(client):
    """The screen is not the only reader: a client that wants the questions of
    a chapter needs the id `taxonomyChapterId` holds, or it has to match on
    names again -- which is what went wrong in the first place."""
    body = client.get("/api/v1/syllabus/Mathematics/6").json()
    ids = [c["id"] for c in body.get("chapters") or []]
    assert "mathematics-6/number-play" in ids, ids
