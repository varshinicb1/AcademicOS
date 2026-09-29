"""The school's own name and logo on its papers (REQUIREMENTS EX-5, audit D41).

D41: "No default flow prints the school's own name." A school that had not
opened the Template Maker printed "Default CBSE Template" at the top of every
paper, and one that had saved a format printed the format's "Template name"
there. Nothing stored the school's name, and a logo chosen on the web never
reached a printed paper (the PDF reads the logo as a file on the server).

Now the principal sets the school's name, address, affiliation line and logo
once; every paper export prints them, and without them the header prints no
school name rather than someone else's words.
"""
from __future__ import annotations

import io
import struct
import zlib

import pytest

from academicos.assessment.pdf import export_pdf, printable_school_name
from academicos.assessment.schemas import SchoolTemplate
from academicos.curriculum.school_profile import (PLACEHOLDER_NAMES, SchoolProfile, printed_branding)
from academicos.curriculum.store import CurriculumStore

from test_assessment_pdf import _boot_with_paper, _extract_text, _make_paper


def _png(width: int = 4, height: int = 4) -> bytes:
    """A real PNG, small enough to upload."""
    raw = b"".join(b"\x00" + b"\x20\x60\xa0" * width for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------- #
# The store and the branding rule
# --------------------------------------------------------------------- #

@pytest.fixture
def store(tmp_path):
    s = CurriculumStore(tmp_path / "curriculum.sqlite")
    yield s
    s.close()


def test_the_profile_is_kept_and_checked(store):
    assert store.get_school_profile("s1") is None
    before, after = store.set_school_profile("s1", name="  Sunrise   Public School ", address="12 MG Road",
                                             affiliation="CBSE Affiliation No. 1234567", updated_by="p1")
    assert before is None
    assert (after.name, after.address, after.affiliation, after.has_logo) == \
        ("Sunrise Public School", "12 MG Road", "CBSE Affiliation No. 1234567", False)
    for bad, match in (("", "cannot be empty"), ("x" * 121, "at most 120"),
                       (next(iter(PLACEHOLDER_NAMES)), "placeholder")):
        with pytest.raises(ValueError, match=match):
            store.set_school_profile("s1", name=bad, address=None, affiliation=None, updated_by="p1")
    with pytest.raises(KeyError):
        store.set_school_logo("s2", logo_type="image/png", blob_key=None, updated_by="p1")


def test_a_placeholder_is_never_printed_and_the_profile_wins(tmp_path):
    placeholder = SchoolTemplate(id="default", school_id="s1", name="Default CBSE Template")
    blank_named = SchoolTemplate(id="t0", school_id="s1", name="School Template")
    format_named = SchoolTemplate(id="t1", school_id="s1", name="Half-yearly format", brand_color="#123456")
    assert printed_branding(placeholder, None, None, "s1").name == ""
    assert printed_branding(blank_named, None, None, "s1").name == ""
    # A name the school gave its branding still prints until it sets a profile.
    assert printed_branding(format_named, None, None, "s1").name == "Half-yearly format"
    profile = SchoolProfile(school_id="s1", name="Sunrise Public School")
    got = printed_branding(format_named, profile, None, "s1")
    assert (got.name, got.brand_color) == ("Sunrise Public School", "#123456"), "the look stays, the name is the school's"
    assert printed_branding(None, None, None, "s1") is None
    # A logo "path" typed on the web is not a file here: printed without it.
    web_logo = SchoolTemplate(id="t2", school_id="s1", name="x", logo_url="https://example.com/logo.png")
    assert printed_branding(web_logo, profile, None, "s1").logo_url == ""
    # The paper's own header (a named branch, a joint exam) still wins.
    assert printable_school_name("Sunrise Junior Wing", got) == "Sunrise Junior Wing"
    assert printable_school_name(None, placeholder) == ""


def test_the_pdf_prints_the_schools_name_and_logo_and_never_a_placeholder(tmp_path):
    paper = _make_paper()
    unnamed = _extract_text(export_pdf(paper, tmp_path / "a",
                                       template=printed_branding(
                                           SchoolTemplate(id="default", school_id="s1", name="Default CBSE Template"),
                                           None, None, "s1")))
    assert "Default CBSE Template" not in unnamed and "AcademicOS School" not in unnamed
    logo = tmp_path / "logo.png"
    logo.write_bytes(_png())
    named = export_pdf(paper, tmp_path / "b", template=printed_branding(
        None, SchoolProfile(school_id="s1", name="Sunrise Public School", logo_type="image/png"), logo, "s1"))
    assert "Sunrise Public School" in _extract_text(named)
    import fitz
    with fitz.open(str(named)) as doc:
        assert doc[0].get_images(), "the logo is drawn on the first page"


# --------------------------------------------------------------------- #
# Through the routes, and on a real export
# --------------------------------------------------------------------- #

def test_routes_set_the_profile_and_logo_and_the_export_prints_them(tmp_path, monkeypatch):
    from academicos.assessment.audit_log import get_audit_log
    from test_assessment_routes_auth import _register

    client, teacher_auth, paper_id = _boot_with_paper(tmp_path, monkeypatch)
    try:
        principal = _register(client, "school_1", "p1@example.com", "Priya", principal_key="test-bootstrap-key")
        other = _register(client, "school_2", "p2@example.com", "Ravi", principal_key="test-bootstrap-key")
        p_auth = {"Authorization": f"Bearer {principal['token']}"}
        o_auth = {"Authorization": f"Bearer {other['token']}"}
        base = "/api/v1/curriculum/school-profile"

        # Before a name is set: never a placeholder or the product's name.
        assert client.get(base, headers=teacher_auth).json()["name"] is None
        client.post(f"/api/v1/papers/{paper_id}/export/pdf", headers=teacher_auth)
        before = client.get(f"/api/v1/papers/{paper_id}/file", headers=teacher_auth)
        (tmp_path / "before.pdf").write_bytes(before.content)
        first = _extract_text(tmp_path / "before.pdf")
        assert "Default CBSE Template" not in first and "AcademicOS School" not in first
        # The fixture's paper carries a branding template named "Default".
        assert "Default" in first.splitlines()

        assert client.put(base, json={"name": "Sunrise Public School"}, headers=teacher_auth).status_code == 403
        assert client.post(f"{base}/logo", files={"file": ("l.png", _png(), "image/png")},
                           headers=p_auth).status_code == 409, "a logo belongs to a named school"
        r = client.put(base, json={"name": "Sunrise Public School", "affiliation": "CBSE No. 1234567"},
                       headers=p_auth)
        assert r.status_code == 200, r.text
        assert client.get(base, headers=teacher_auth).json()["name"] == "Sunrise Public School"
        assert client.get(base, headers=o_auth).json()["name"] is None, "another school sees its own, not this one"

        assert client.post(f"{base}/logo", files={"file": ("l.gif", b"GIF89a", "image/gif")},
                           headers=p_auth).status_code == 415
        assert client.post(f"{base}/logo", files={"file": ("l.png", b"not a png at all", "image/png")},
                           headers=p_auth).status_code == 415
        assert client.post(f"{base}/logo", files={"file": ("l.png", b"\x89PNG\r\n\x1a\n" + b"0" * (1024 * 1024),
                                                           "image/png")}, headers=p_auth).status_code == 413
        up = client.post(f"{base}/logo", files={"file": ("l.png", _png(), "image/png")}, headers=p_auth)
        assert up.status_code == 200 and up.json()["hasLogo"] is True
        got = client.get(f"{base}/logo", headers=teacher_auth)
        assert got.status_code == 200 and got.content == _png() and got.headers["content-type"] == "image/png"
        assert client.get(f"{base}/logo", headers=o_auth).status_code == 404

        exported = client.post(f"/api/v1/papers/{paper_id}/export/pdf", headers=teacher_auth)
        assert exported.status_code == 200, exported.text
        pdf = client.get(f"/api/v1/papers/{paper_id}/file", headers=teacher_auth)
        (tmp_path / "out.pdf").write_bytes(pdf.content)
        after = _extract_text(tmp_path / "out.pdf")
        assert "Sunrise Public School" in after
        assert "Default" not in after.splitlines(), "the profile's name replaces the template's"
        import fitz
        with fitz.open(str(tmp_path / "out.pdf")) as doc:
            assert doc[0].get_images(), "the uploaded logo is on the printed paper"

        removed = client.delete(f"{base}/logo", headers=p_auth)
        assert removed.json()["hasLogo"] is False
        assert client.get(f"{base}/logo", headers=teacher_auth).status_code == 404

        actions = [e["action"] for e in reversed(get_audit_log(tmp_path).for_action("school_profile_set"))]
        assert actions == ["school_profile_set"]
        assert get_audit_log(tmp_path).for_action("school_logo_set") and \
            get_audit_log(tmp_path).for_action("school_logo_removed")
        export = client.get("/api/v1/curriculum/export", headers=p_auth).json()
        assert export["school_profile"]["name"] == "Sunrise Public School"
    finally:
        client.__exit__(None, None, None)
