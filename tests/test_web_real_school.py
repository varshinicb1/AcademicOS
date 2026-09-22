"""The live web app for a real school: honest paper totals and the school's own
branding on export (Task 604).

The 2026-09-22 re-audit of the live release (a153003) found two server-side
defects a real school hits on day one:

  * quick-generate handed back short papers silently. English 10 at 80 marks
    held 20, Hindi 10 held 2, Computer Applications 27, Biology 12 48 -- each
    printed "Maximum Marks: 80" with `warnings` empty. selection.optimize had
    already written each section's shortfall into `gaps`; the route threw it
    away.
  * export fell back to `store.default_for("school_1")` when a paper carried
    no template, so school_2's PDF printed school_1's branded header.

The quick-generate test runs on the real served bank (a copy is read, never
written); the branding test uses the hermetic fixture pool of
tests/test_paper_swap_pick.py.
"""
from __future__ import annotations

import pytest

from academicos.assessment import pool as pool_mod
from test_paper_swap_pick import FIXTURE, _pool
from test_paper_templates import _REAL_BANK, _boot_client, _register

QUICK = "/api/v1/papers/quick-generate"


def _pdf_text(content: bytes) -> str:
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    try:
        return " ".join(" ".join(page.get_text() for page in doc).split())
    finally:
        doc.close()


def _printed_total(paper: dict) -> int:
    return sum(s["totalMarks"] for s in paper["sections"])


@pytest.fixture(scope="module")
def real_english_10(tmp_path_factory):
    if not _REAL_BANK.exists():
        pytest.skip("the served question bank is not in this checkout")
    from academicos.config import Config

    cfg = Config(data_root=tmp_path_factory.mktemp("bank"))
    cfg._load_baked_questions = True
    return pool_mod.build_pool(cfg, subject="English", grade="X")


def test_a_short_quick_paper_says_so_and_prints_its_real_total(
        tmp_path, monkeypatch, real_english_10):
    monkeypatch.setitem(pool_mod._CACHE, ("English", "X"), real_english_10)
    with _boot_client(tmp_path, monkeypatch) as client:
        t = _register(client, "school_1", "ana@example.com")
        r = client.post(QUICK, json={"subject": "English", "grade": 10, "totalMarks": 80},
                        headers=t)
        assert r.status_code == 200, r.text
        paper = r.json()

        real = _printed_total(paper)
        assert 0 < real < 80, "the audit measured 20 of 80 on this bank"
        # The header states what the paper holds, never what was asked for.
        assert paper["metadata"]["totalMarks"] == real
        assert f"Maximum Marks: {real}" in paper["formattedContent"]
        assert "Maximum Marks: 80" not in paper["formattedContent"]

        # The shortfall is named: the paper's total, then each short section.
        warnings = paper["warnings"]
        assert any(f"{real} of the 80 marks" in w for w in warnings), warnings
        short = [s for s in paper["sections"] if not s["questions"]]
        for s in short:
            assert any(f"Section {s['label']}" in w and "prints short" in w for w in warnings), (
                s["label"], warnings)

        # The PDF a teacher prints carries the same real total.
        assert client.post(f"/api/v1/papers/{paper['id']}/export/pdf",
                           headers=t).status_code == 200
        pdf = client.get(f"/api/v1/papers/{paper['id']}/file", headers=t)
        assert pdf.status_code == 200
        text = _pdf_text(pdf.content)
        assert f"Maximum Marks: {real}" in text
        assert "Maximum Marks: 80" not in text


def test_school_2s_pdf_never_carries_school_1s_branding(tmp_path, monkeypatch):
    monkeypatch.setitem(pool_mod._CACHE, ("Science", "X"), _pool(FIXTURE))
    with _boot_client(tmp_path, monkeypatch) as client:
        s1 = _register(client, "school_1", "ana@example.com")
        s2 = _register(client, "school_2", "bea@example.com")

        branded = client.post("/api/v1/schools/school_1/school-templates", json={
            "template": {"id": "new", "schoolId": "school_1",
                         "name": "Green Valley Public School",
                         "tagline": "Affiliated to CBSE, Delhi", "isDefault": True},
        }, headers=s1)
        assert branded.status_code == 200, branded.text

        # school_2 has configured no branding: its paper carries no template.
        r = client.post(QUICK, json={"subject": "Science", "grade": 10, "totalMarks": 6},
                        headers=s2)
        assert r.status_code == 200, r.text
        pid = r.json()["id"]

        for fmt, query in (("pdf", ""), ("answer-key", "?format=answer-key")):
            assert client.post(f"/api/v1/papers/{pid}/export/{fmt}",
                               headers=s2).status_code == 200
            pdf = client.get(f"/api/v1/papers/{pid}/file{query}", headers=s2)
            assert pdf.status_code == 200, pdf.text
            text = _pdf_text(pdf.content)
            assert "Green Valley" not in text, fmt
            assert "Affiliated to CBSE, Delhi" not in text, fmt

        # school_1's own paper still gets school_1's branding.
        r1 = client.post(QUICK, json={"subject": "Science", "grade": 10, "totalMarks": 6},
                         headers=s1)
        assert r1.status_code == 200, r1.text
        pid1 = r1.json()["id"]
        assert client.post(f"/api/v1/papers/{pid1}/export/pdf", headers=s1).status_code == 200
        text1 = _pdf_text(client.get(f"/api/v1/papers/{pid1}/file", headers=s1).content)
        assert "Green Valley Public School" in text1
