"""School paper-template store (assessment/school_templates.py).

Verify TemplateStore.list_for_school(): a school with zero templates gets a
real, *persisted* default template — calling list_for_school() twice for a
fresh school_id must return the exact same template id both times, not a
newly-generated one each call. SQLite via tmp_path, no Supabase.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.school_templates import TemplateStore
from academicos.assessment.schemas import SchoolTemplate, SectionBlueprint


def _store(tmp_path: Path) -> TemplateStore:
    return TemplateStore(tmp_path / "templates.sqlite")


def _section() -> SectionBlueprint:
    return SectionBlueprint(
        id="section-a", label="A", name="MCQ", marks_per_question=1,
        question_count=5, total_marks=5,
    )


def test_list_for_school_seeds_persistent_default(tmp_path):
    store = _store(tmp_path)
    first = store.list_for_school("school-fresh")
    assert len(first) == 1
    t1 = first[0]
    assert t1.school_id == "school-fresh"
    assert t1.name == "Default CBSE Template"
    assert t1.is_default is True
    assert not t1.id.startswith("new")  # real, generated id — not a placeholder

    # The default must be persisted, not ephemeral: the second call returns
    # the same template, not a freshly generated one each time.
    second = store.list_for_school("school-fresh")
    assert len(second) == 1
    assert second[0].id == t1.id
    assert second[0].name == t1.name


def test_default_template_has_cbse_sections(tmp_path):
    store = _store(tmp_path)
    template = store.list_for_school("sections-school")[0]
    # A template stores its own fixed section layout (seeded at the 100-mark
    # scale) — sections_for returns that stored layout, not a re-scale for
    # the requested total.
    sections = store.sections_for("sections-school", template.id, 80)
    labels = [s.label for s in sections]
    assert labels == ["A", "B", "C", "D", "E"]
    assert sections[0].marks_per_question == 1
    assert sections[0].question_count == 25  # 25% of the stored 100-mark scale


def test_sections_for_falls_back_to_builtin_for_unknown_school(tmp_path):
    # A school with no saved template (never seeded) gets the built-in CBSE
    # pattern scaled to the requested total.
    store = _store(tmp_path)
    sections = store.sections_for("no-such-school", None, 80)
    assert sections[0].label == "A"
    assert sections[0].question_count == 20  # 25% of 80


def test_sections_for_default_when_no_template_id(tmp_path):
    store = _store(tmp_path)
    store.list_for_school("school-x")
    sections = store.sections_for("school-x", None, 80)
    assert sections and sections[0].label == "A"


def test_distinct_schools_get_distinct_defaults(tmp_path):
    store = _store(tmp_path)
    a = store.list_for_school("school-a")[0]
    b = store.list_for_school("school-b")[0]
    assert a.id != b.id
    assert store.list_for_school("school-a")[0].id == a.id
    assert store.list_for_school("school-b")[0].id == b.id


def test_save_and_get_roundtrip(tmp_path):
    store = _store(tmp_path)
    template = SchoolTemplate(id="tpl_springfield", school_id="s1",
                              name="Springfield High", brand_color="#1a2b3c",
                              tagline="Learn with rigour")
    saved = store.save(template, [_section()])
    assert saved.id == "tpl_springfield"
    got, sections = store.get("tpl_springfield")
    assert got.name == "Springfield High"
    assert got.brand_color == "#1a2b3c"
    assert got.tagline == "Learn with rigour"
    assert sections[0].question_count == 5


def test_save_generates_id_for_new_template(tmp_path):
    store = _store(tmp_path)
    template = SchoolTemplate(id="new", school_id="s2", name="Willow Valley")
    saved = store.save(template, [_section()])
    assert saved.id != "new"
    assert store.get(saved.id) is not None


def test_saved_template_survives_store_reopen(tmp_path):
    store = _store(tmp_path)
    template = SchoolTemplate(id="tpl_persist", school_id="s3", name="Persistent School")
    store.save(template, [_section()])

    reopened = TemplateStore(tmp_path / "templates.sqlite")
    got, _ = reopened.get("tpl_persist")
    assert got.name == "Persistent School"


def test_default_for_returns_seeded_default(tmp_path):
    store = _store(tmp_path)
    seeded = store.list_for_school("school-d")[0]
    assert store.default_for("school-d").id == seeded.id


def test_delete_removes_template(tmp_path):
    store = _store(tmp_path)
    template = SchoolTemplate(id="tpl_gone", school_id="s4", name="Gone School")
    store.save(template, [_section()])
    store.delete("tpl_gone")
    assert store.get("tpl_gone") is None


def test_list_for_school_returns_saved_template_over_default(tmp_path):
    store = _store(tmp_path)
    custom = SchoolTemplate(id="tpl_custom", school_id="s5", name="Custom High")
    store.save(custom, [_section()])
    listed = store.list_for_school("s5")
    assert len(listed) == 1
    assert listed[0].id == "tpl_custom"