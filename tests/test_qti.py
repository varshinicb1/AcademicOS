"""QTI 2.1 export (C4).

Assertions are on parsed XML rather than on substrings, so a formatting change
cannot make a broken document look fine.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.qti import (
    QTI_NS,
    split_options,
    to_qti_item,
    to_qti_package,
    to_qti_test,
)

NS = {"qti": QTI_NS}


def mcq(qid="cbse:q:src:deadbeefdeadbeefdeadbeef:1", **over):
    q = {
        "id": qid,
        "marks": 1,
        "stem": "Which gas turns lime water milky? (a) oxygen (b) carbon dioxide "
                "(c) hydrogen (d) nitrogen",
        "answerScheme": {
            "totalMarks": 1,
            "provenance": "cbse_marking_scheme",
            "sourcePaperCode": "31/1/1",
            "markingPoints": [{"id": "mp1", "description": "carbon dioxide", "marks": 1}],
        },
        "provenance": {"sourceDocumentId": "src:deadbeef", "pageNumber": 4},
    }
    q.update(over)
    return q


def subjective(**over):
    q = {
        "id": "cbse:q:src:deadbeefdeadbeefdeadbeef:22",
        "marks": 3,
        "stem": "Explain why the reaction of lead nitrate with potassium iodide "
                "is a double displacement reaction.",
        "answerScheme": {
            "totalMarks": 3,
            "provenance": "cbse_marking_scheme",
            "sourcePaperCode": "31/1/1",
            "markingPoints": [
                {"id": "mp1", "description": "identifies double displacement", "marks": 1},
                {"id": "mp2", "description": "states the precipitate formed", "marks": 2},
            ],
        },
    }
    q.update(over)
    return q


# --------------------------------------------------------------------------- #
# option splitting
# --------------------------------------------------------------------------- #

def test_split_options_pulls_the_prompt_out():
    prompt, opts = split_options(mcq()["stem"])
    assert prompt == "Which gas turns lime water milky?"
    assert opts == ["oxygen", "carbon dioxide", "hydrogen", "nitrogen"]


@pytest.mark.parametrize("stem", [
    "Explain the reaction.",           # no markers at all
    "Which is correct? (a) only one",  # a single option is not a choice
    "",
])
def test_split_options_declines_when_there_is_no_real_choice(stem):
    prompt, opts = split_options(stem)
    assert opts == []


def test_uppercase_markers_also_split():
    _, opts = split_options("Pick one (A) yes (B) no")
    assert opts == ["yes", "no"]


# --------------------------------------------------------------------------- #
# item XML
# --------------------------------------------------------------------------- #

def test_mcq_exports_as_a_choice_interaction():
    item = ET.fromstring(to_qti_item(mcq()))
    body = item.find("qti:itemBody/qti:choiceInteraction", NS)
    assert body is not None
    assert body.get("maxChoices") == "1"
    choices = body.findall("qti:simpleChoice", NS)
    assert len(choices) == 4
    assert [c.get("identifier") for c in choices] == ["A", "B", "C", "D"]
    assert choices[1].text == "carbon dioxide"


def test_subjective_exports_as_extended_text():
    item = ET.fromstring(to_qti_item(subjective()))
    body = item.find("qti:itemBody/qti:extendedTextInteraction", NS)
    assert body is not None
    assert item.find("qti:itemBody/qti:choiceInteraction", NS) is None


def test_item_identifier_is_a_legal_xml_name():
    """A canonical id contains colons, which QTI identifiers forbid. Passing it
    through unchanged makes the importing LMS reject the package."""
    item = ET.fromstring(to_qti_item(mcq()))
    ident = item.get("identifier")
    assert ident is not None
    assert ":" not in ident
    assert ident[0].isalpha()


def test_the_marking_scheme_survives_the_export():
    """The value points are the scarce half of the bank. A format that carries
    the question and drops the scheme exports the cheap part."""
    item = ET.fromstring(to_qti_item(subjective()))
    rubric = item.find("qti:rubricBlock", NS)
    assert rubric is not None
    text = "".join(rubric.itertext())
    assert "identifies double displacement" in text
    assert "states the precipitate formed" in text
    assert "Official CBSE marking scheme" in text
    assert "31/1/1" in text


def test_an_item_with_no_scheme_still_exports():
    q = subjective()
    q["answerScheme"] = {"totalMarks": 3, "markingPoints": []}
    item = ET.fromstring(to_qti_item(q))
    assert item.find("qti:itemBody", NS) is not None
    assert item.find("qti:rubricBlock", NS) is None


def test_provenance_travels_in_item_metadata():
    item = ET.fromstring(to_qti_item(mcq()))
    text = "".join(item.itertext())
    assert "src:deadbeef" in text
    assert "sourceDocument" in text


def test_declared_outcomes_are_present():
    """The spec requires an SCORE outcome; some LMSs refuse a package without it."""
    item = ET.fromstring(to_qti_item(mcq()))
    score = item.find("qti:outcomeDeclaration", NS)
    assert score is not None and score.get("identifier") == "SCORE"


def test_special_characters_are_escaped():
    q = subjective(stem="State the value of x < 5 and y > 3 & explain.")
    xml = to_qti_item(q)
    ET.fromstring(xml)                       # must parse, not just be produced
    assert "&lt;" in xml and "&amp;" in xml


# --------------------------------------------------------------------------- #
# test XML
# --------------------------------------------------------------------------- #

def test_test_references_every_item():
    doc = ET.fromstring(to_qti_test([mcq(), subjective()]))
    refs = doc.findall(".//qti:itemRef", NS)
    assert len(refs) == 2
    assert all(r.get("identifierref") for r in refs)


def test_test_title_reports_total_marks():
    doc = ET.fromstring(to_qti_test([mcq(), subjective()], title="Science"))
    assert "4 marks" in doc.get("title", "")


def test_test_declares_a_score_outcome():
    doc = ET.fromstring(to_qti_test([mcq()]))
    assert doc.find("qti:outcomeDeclaration", NS) is not None


# --------------------------------------------------------------------------- #
# the package
# --------------------------------------------------------------------------- #

def test_package_is_a_zip_with_a_manifest_items_and_a_test():
    blob = to_qti_package([mcq(), subjective()], title="Science Term 1")
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        assert "imsmanifest.xml" in names
        assert "test.xml" in names
        assert sum(1 for n in names if n.startswith("items/")) == 2


def test_every_file_in_the_package_parses_as_xml():
    """A package is only useful if an importer can read it."""
    blob = to_qti_package([mcq(), subjective()])
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for name in zf.namelist():
            ET.fromstring(zf.read(name))


def test_manifest_lists_every_file_it_ships():
    blob = to_qti_package([mcq(), subjective()])
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        manifest = zf.read("imsmanifest.xml").decode("utf-8")
        names = zf.namelist()
        for name in names:
            if name == "imsmanifest.xml":
                continue
            assert name in manifest, f"{name} shipped but not declared"


def test_package_handles_an_empty_bank():
    """Degenerate input must not raise; it should produce a valid empty test."""
    blob = to_qti_package([])
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        ET.fromstring(zf.read("test.xml"))


def test_item_identifiers_are_unique_and_stable():
    """Two runs over the same bank must produce the same identifiers, or a
    re-import duplicates every question."""
    a = to_qti_package([mcq(), subjective()])
    b = to_qti_package([mcq(), subjective()])
    with zipfile.ZipFile(io.BytesIO(a)) as za, zipfile.ZipFile(io.BytesIO(b)) as zb:
        assert sorted(za.namelist()) == sorted(zb.namelist())
