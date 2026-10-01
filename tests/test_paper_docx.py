"""A question paper as an editable Word file (EX-5, DOCX export): the same
header, instructions, sections, numbered questions with marks, options and
OR choices as the PDF; a traceable-copy id in every page's footer; valid
XML even when a scanned stem carries a control character; and through the
routes, exported, audited and downloaded by staff only."""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile

from test_assessment_pdf import _make_paper
from test_paper_templates import _boot_client, _register
from test_paper_swap_pick import _generate, seeded  # noqa: F401 - `seeded` is a fixture


def _text(docx: bytes, part: str = "word/document.xml") -> str:
    xml = zipfile.ZipFile(io.BytesIO(docx)).read(part).decode()
    ET.fromstring(xml)                                  # well-formed, or this raises
    return re.sub(r"<[^>]+>", "", xml.replace("<w:tab/>", "\t").replace("</w:p>", "\n"))


def test_the_word_file_carries_the_paper(tmp_path):
    from academicos.assessment.docx_export import export_docx
    paper = _make_paper()
    paper.sections[0].questions[0].internal_choice_text = "Name a noble gas."
    paper.sections[0].questions[0].stem += "\x0c"        # a form feed from a scanned page
    path = export_docx(paper, tmp_path, watermark_id="Z9-TRACE-42")
    data = path.read_bytes()
    body = _text(data)
    for expected in ("Mid Term Examination", "Subject: Science  |  Class: 10", "Maximum Marks: 1",
                     "Time Allowed: 1 hour", "General Instructions:", "SECTION A",
                     "1.\tWhich of the following is a gas?\t[1]", "(A)  Oxygen", "(D)  Copper", "OR",
                     "Name a noble gas."):
        assert expected in body, expected
    footer = _text(data, "word/footer1.xml")
    assert "Confidential — traceable copy Z9-TRACE-42" in footer and "Q.P. Code AB12CD" in footer
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert {"[Content_Types].xml", "word/document.xml", "word/_rels/document.xml.rels"} <= set(names)


def test_a_teacher_exports_and_downloads_the_word_file(tmp_path, monkeypatch, seeded):
    from academicos.assessment.audit_log import get_audit_log
    with _boot_client(tmp_path, monkeypatch) as client:
        t1 = _register(client, "school_1", "ana@example.com")
        pid = _generate(client, t1)["id"]
        r = client.post(f"/api/v1/papers/{pid}/export/docx", headers=t1)
        assert r.status_code == 200, r.text
        # The URL names this export, so it fetches exactly this export's file
        # (tests/test_concurrency_fixes.py); the plain path still serves the latest.
        assert r.json()["url"] == f"/api/v1/papers/{pid}/file?format=docx&export={r.json()['watermarkId']}"
        f = client.get(f"/api/v1/papers/{pid}/file", params={"format": "docx"}, headers=t1)
        assert f.status_code == 200
        assert f.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml")
        assert "traceable copy " + r.json()["watermarkId"] in _text(f.content, "word/footer1.xml")
        exported = get_audit_log(tmp_path).for_action("paper_exported")
        assert any(e["details"]["format"] == "docx" for e in exported)
        other = _register(client, "school_2", "bo@example.com")
        assert client.get(f"/api/v1/papers/{pid}/file", params={"format": "docx"}, headers=other).status_code in (403, 404)
        assert client.post(f"/api/v1/papers/{pid}/export/odt", headers=t1).status_code == 400
