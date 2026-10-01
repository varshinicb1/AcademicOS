"""Time saved per paper — the renewal criterion, and what the number means.

Decision 11: *"Renewal is measured as time saved per paper."* The tests that
matter most here are not the arithmetic ones; they are the ones asserting that a
DECLARED baseline is never presented as a measured result. This figure will be
quoted at a principal deciding whether to renew, and the failure mode is a
number that reads as evidence when it is an assumption.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment import paper_timing as pt  # noqa: E402


@pytest.fixture()
def data_root(tmp_path):
    return tmp_path / "data"


# --- the baseline is declared, and says so --------------------------------

def test_the_default_baseline_is_declared_not_measured(monkeypatch):
    monkeypatch.delenv(pt._ENV_KEY, raising=False)
    value, provenance = pt.baseline_minutes()
    assert value == pt._DEFAULT_BASELINE_MINUTES
    assert "declared" in provenance.lower()
    assert "not measured" in provenance.lower(), (
        "the provenance must say the baseline is not measured, or the saving "
        "reads as evidence"
    )


def test_a_school_can_supply_its_own_baseline(monkeypatch):
    """A school's own figure is worth more in a renewal conversation."""
    monkeypatch.setenv(pt._ENV_KEY, "25")
    value, provenance = pt.baseline_minutes()
    assert value == 25.0
    assert pt._ENV_KEY in provenance


@pytest.mark.parametrize("bad", ["not-a-number", "", "0", "-10"])
def test_an_unusable_baseline_falls_back_and_says_why(monkeypatch, bad):
    """Never silently substitute a number without recording the substitution."""
    monkeypatch.setenv(pt._ENV_KEY, bad)
    value, provenance = pt.baseline_minutes()
    assert value == pt._DEFAULT_BASELINE_MINUTES
    if bad != "":
        assert "fell back" in provenance or "not positive" in provenance or \
               "not a number" in provenance


# --- recording ------------------------------------------------------------

def test_a_negative_duration_is_refused(data_root):
    """A duration cannot be negative; this is a caller bug, not a slow paper."""
    with pytest.raises(ValueError, match="negative"):
        pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                             paper_id="p1", elapsed_seconds=-1.0)


def test_recording_then_reporting_round_trips(data_root):
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=8.0, question_count=20)
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p2", elapsed_seconds=12.0, question_count=22)
    rep = pt.report(data_root, school_id="s1")
    assert rep.papers == 2
    assert rep.median_generation_seconds == 10.0
    assert rep.total_generation_seconds == 20.0


def test_the_report_is_scoped_to_one_school(data_root):
    """Cross-school leakage in a management figure is a tenancy bug."""
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=8.0)
    pt.record_generation(data_root=data_root, school_id="s2", user_id="u2",
                         paper_id="p2", elapsed_seconds=8.0)
    assert pt.report(data_root, school_id="s1").papers == 1
    assert pt.report(data_root, school_id="s2").papers == 1
    assert pt.report(data_root).papers == 2          # unscoped is explicit


def test_an_empty_report_is_zero_rather_than_an_error(data_root):
    rep = pt.report(data_root, school_id="s1")
    assert rep.papers == 0
    assert rep.estimated_minutes_saved_total == 0.0
    assert rep.baseline_minutes_per_paper > 0        # the baseline is still told


def test_the_saving_is_clamped_at_zero(monkeypatch, data_root):
    """A paper that took longer with the product than by hand is not a saving.

    Reporting a negative one invites the reader to distrust the figure that IS
    real, so it is clamped -- and the clamp is asserted rather than assumed.
    """
    monkeypatch.setenv(pt._ENV_KEY, "1")             # 1 minute baseline
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=0.5,
                         teacher_seconds=600.0)                  # 10 minutes
    rep = pt.report(data_root, school_id="s1")
    assert rep.estimated_minutes_saved_per_paper == 0.0
    assert rep.estimated_minutes_saved_total == 0.0
    # But the MEASURED number is still reported honestly, unclamped.
    assert rep.median_teacher_minutes == 10.0


# --- the saving is the baseline less the teacher's measured time (D49) -------
#
# Audits 2026-09-27 to 2026-10-01: "time saved" was the declared baseline
# times the paper count. What was subtracted was server compute (0.02-0.15 s
# per paper, `perPaper = baseline - median/60`); the teacher's time in the
# builder was timed nowhere.

def test_time_saved_is_the_baseline_less_the_teachers_measured_time(monkeypatch, data_root):
    monkeypatch.delenv(pt._ENV_KEY, raising=False)                 # 45 minutes
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=0.03, teacher_seconds=600.0)
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p2", elapsed_seconds=0.05)       # not measured
    rep = pt.report(data_root, school_id="s1")
    assert rep.estimated_minutes_saved_total == pytest.approx((45 - 10) + 45)
    assert rep.estimated_minutes_saved_per_paper == pytest.approx(40.0)
    assert rep.papers_with_teacher_time == 1
    assert rep.median_teacher_minutes == 10.0
    payload = rep.as_dict()
    assert payload["papersWithTeacherTime"] == 1 and payload["medianTeacherMinutes"] == 10.0
    assert payload["estimated"] is True
    assert "1 of 2 paper(s) count the baseline less the time their teacher spent" in payload["caveat"]


def test_server_compute_is_not_the_teachers_time(monkeypatch, data_root):
    """A paper with no measured time counts the whole baseline -- labelled
    estimated -- not the baseline less how long the server took."""
    monkeypatch.delenv(pt._ENV_KEY, raising=False)
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=30.0)
    rep = pt.report(data_root, school_id="s1")
    assert rep.estimated_minutes_saved_total == 45.0
    assert rep.papers_with_teacher_time == 0 and rep.median_teacher_minutes is None
    assert "DECLARED, not measured" in rep.as_dict()["caveat"]


def test_a_negative_teacher_time_is_refused(data_root):
    with pytest.raises(ValueError, match="negative"):
        pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                             paper_id="p1", elapsed_seconds=1.0, teacher_seconds=-3.0)


# --- the payload separates measured from declared -------------------------

def test_the_payload_names_which_fields_are_measured(monkeypatch, data_root):
    """The word "estimated" has to travel with the number.

    This is the whole design: a saving built on a declared baseline is a
    perfectly good management figure and an unacceptable engineering claim, and
    the difference is only visible if it is written down next to the value.
    """
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=5.0)
    payload = pt.report(data_root, school_id="s1").as_dict()

    assert payload["measured"] == ["generationSeconds", "teacherSeconds"]
    assert payload["declared"] == ["baselineMinutesPerPaper"]
    assert "DECLARED, not measured" in payload["caveat"]
    assert "baselineProvenance" in payload
    assert payload["baselineProvenance"]


def test_the_timer_measures_something_real():
    """A monotonic clock, so an adjustment mid-generation cannot alter it."""
    import time as _time

    with pt.generation_timer() as timer:
        _time.sleep(0.02)
    assert timer.elapsed_seconds >= 0.02
    assert timer.elapsed_seconds < 5.0        # sanity: not minutes


def test_the_action_constant_matches_what_the_route_writes(data_root):
    """The writer and the reader must not drift apart.

    `routes.py` records this action through `record_generation`, which puts
    `generationSeconds` in the details; if either changes alone, the report
    silently reports zero papers.
    """
    source = (REPO / "src" / "academicos" / "assessment"
              / "routes.py").read_text(encoding="utf-8")
    assert '"quick_paper_generated"' in source
    assert "paper_timing.record_generation(" in source
    assert pt.ACTION == "quick_paper_generated"
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=1.0)
    from academicos.assessment.audit_log import get_audit_log
    row = get_audit_log(data_root).for_action(pt.ACTION)[0]
    assert row["details"]["generationSeconds"] == 1.0


def test_an_action_the_report_does_not_read_is_refused(data_root):
    with pytest.raises(ValueError, match="not a generation action"):
        pt.record_generation("paper_made", data_root=data_root, school_id="s1",
                             user_id="u1", paper_id="p1", elapsed_seconds=1.0)


def test_every_route_records_its_generation_through_the_one_writer():
    """D51: the routes appended their rows directly, so `record_generation`
    -- the only writer that stored the baseline in force -- was dead code and
    no row carried one. Each generation action is now written only there."""
    import re
    for path in (REPO / "src" / "academicos").rglob("*.py"):
        if path.name == "paper_timing.py":
            continue
        text = path.read_text(encoding="utf-8")
        for action in re.findall(r'"([a-z_]+_paper_generated)"', text):
            assert re.search(r'record_generation\(\s*"' + action + '"', text), (path.name, action)


# --- a paper keeps the baseline it was made under (D51) ----------------------
#
# Audit 2026-09-27: 0 generation rows carried `baselineMinutesAtRecordTime`,
# and raising Term 1's baseline from 60 to 120 moved the same 13 papers from
# 780 to 1,560 minutes saved -- a closed term's figure rewritten after the fact.

def test_a_paper_keeps_the_baseline_it_was_made_under(monkeypatch, data_root):
    monkeypatch.delenv(pt._ENV_KEY, raising=False)
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p1", elapsed_seconds=0.0)           # under 45
    monkeypatch.setenv(pt._ENV_KEY, "90")
    pt.record_generation(data_root=data_root, school_id="s1", user_id="u1",
                         paper_id="p2", elapsed_seconds=0.0)           # under 90
    rep = pt.report(data_root, school_id="s1", baseline=(120.0, "set by the principal for Term 1"))
    assert rep.estimated_minutes_saved_total == 45.0 + 90.0
    assert rep.papers_at_recorded_baseline == 2
    # What a paper made now would be measured against.
    assert rep.baseline_minutes_per_paper == 120.0
    assert rep.as_dict()["papersAtRecordedBaseline"] == 2


def test_a_row_from_before_rows_carried_a_baseline_takes_todays(data_root):
    _append(data_root, "template_paper_generated", seconds=0.0)
    rep = pt.report(data_root, school_id="s1", baseline=(60.0, "set by the principal for Term 1"))
    assert rep.estimated_minutes_saved_total == 60.0
    assert rep.papers_at_recorded_baseline == 0


# --- every way the product makes a paper is counted -------------------------
#
# Audit 2026-09-26 (item 5.2/6.1): the report read `quick_paper_generated` only,
# and the web app never calls quick-generate -- the guided builder appends
# `template_paper_generated` and the hand-picked path `id_curated_paper_generated`.
# After 20 quick, 11 builder and 2 hand-picked papers it reported 20; on the live
# web app a principal's card said no paper had been generated.

def _append(data_root, action, *, school_id="s1", seconds=6.0, paper_id="p"):
    from academicos.assessment.audit_log import get_audit_log
    get_audit_log(data_root).append(
        action, details={"paperId": paper_id, "schoolId": school_id,
                         "generationSeconds": seconds})


def test_every_generation_path_is_counted(data_root):
    _append(data_root, "quick_paper_generated", paper_id="q1")
    _append(data_root, "template_paper_generated", paper_id="t1")
    _append(data_root, "template_paper_generated", paper_id="t2")
    _append(data_root, "id_curated_paper_generated", paper_id="h1")
    rep = pt.report(data_root, school_id="s1")
    assert rep.papers == 4
    assert rep.as_dict()["papersByPath"] == {"quick": 1, "builder": 2, "hand-picked": 1}


def test_a_builder_only_school_is_not_reported_as_zero(data_root):
    _append(data_root, "template_paper_generated", seconds=4.0)
    rep = pt.report(data_root, school_id="s1")
    assert rep.papers == 1
    assert rep.median_generation_seconds == 4.0
    assert rep.estimated_minutes_saved_total > 0


def test_every_path_is_scoped_to_one_school(data_root):
    _append(data_root, "template_paper_generated", school_id="s1")
    _append(data_root, "id_curated_paper_generated", school_id="s2")
    assert pt.report(data_root, school_id="s1").papers == 1
    assert pt.report(data_root, school_id="s2").papers == 1
    assert pt.report(data_root).papers == 2


def test_no_route_writes_a_generation_action_the_report_does_not_read():
    """The drift guard the single-file check above could not be.

    Reads every module under src/academicos for a `"..._paper_generated"`
    action literal, so a new generation path that forgets to be counted fails
    here -- and an action the report reads that nothing writes fails too.
    """
    import re
    written = set()
    for path in (REPO / "src" / "academicos").rglob("*.py"):
        if path.name == "paper_timing.py":
            continue
        written |= set(re.findall(r'"([a-z_]+_paper_generated)"',
                                  path.read_text(encoding="utf-8")))
    assert written, "found no generation action at all; the scan is broken"
    assert written == set(pt.GENERATION_ACTIONS), (
        f"routes write {sorted(written)}, the report reads "
        f"{sorted(pt.GENERATION_ACTIONS)}")


# --- a paper counts once, and only while it exists ---------------------------
#
# D42 (audits 2026-09-27 to 2026-10-01): every press of Generate counted as a
# paper set and a full baseline saved. Generate pressed again on the same
# choices made the same questions under a second paper id and counted twice,
# a regeneration on the same assessment counted the paper it replaced, and a
# deleted paper still counted.

def _asm(aid, paper_id, questions=("q1", "q2"), teacher="u1", subject="Science", grade=10):
    from types import SimpleNamespace
    return SimpleNamespace(id=aid, teacher_id=teacher, subject=subject, grade=grade,
                           generated_paper_id=paper_id, selected_question_ids=list(questions))


def test_each_paper_that_still_exists_counts_once(data_root):
    _append(data_root, "template_paper_generated", paper_id="t1", seconds=2.0)
    _append(data_root, "template_paper_generated", paper_id="t2", seconds=2.0)    # pressed again
    _append(data_root, "template_paper_generated", paper_id="t3", seconds=9.0)    # deleted since
    _append(data_root, "id_curated_paper_generated", paper_id="h1", seconds=30.0)  # replaced by h2
    _append(data_root, "id_curated_paper_generated", paper_id="h2", seconds=6.0)
    # a1 and a2 hold the same questions (Generate pressed twice); t3's
    # assessment is gone; a4 now holds h2, not h1.
    kept = pt.kept_papers([_asm("a1", "t1"), _asm("a2", "t2"), _asm("a4", "h2", questions=("q7",)),
                           _asm("a5", None)])
    rep = pt.report(data_root, school_id="s1", kept=kept)
    assert rep.papers == 2
    assert rep.papers_by_path == {"builder": 1, "hand-picked": 1}
    # Generation time is per counted paper: 2 s and 6 s, not every press.
    assert rep.median_generation_seconds == 4.0 and rep.total_generation_seconds == 8.0
    assert rep.estimated_minutes_saved_total == pytest.approx(2 * rep.estimated_minutes_saved_per_paper)
    assert "DECLARED, not measured" in rep.as_dict()["caveat"], "still labelled an estimate"


def test_the_same_questions_are_another_paper_for_another_teacher_or_class(data_root):
    for pid in ("t1", "t2", "t3"):
        _append(data_root, "template_paper_generated", paper_id=pid)
    kept = pt.kept_papers([_asm("a1", "t1"), _asm("a2", "t2", teacher="u2"), _asm("a3", "t3", grade=9)])
    assert pt.report(data_root, school_id="s1", kept=kept).papers == 3


def test_every_report_the_routes_give_counts_kept_papers_only():
    """Without `kept` the report counts every recorded generation (no store
    to check against): each caller in src/ must pass it."""
    import re
    calls = []
    for path in (REPO / "src" / "academicos").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"paper_timing\.report\(", text):
            depth, i = 1, m.end()
            while depth:
                depth += {"(": 1, ")": -1}.get(text[i], 0)
                i += 1
            calls.append((path.name, text[m.end():i]))
    assert calls, "found no caller at all; the scan is broken"
    assert all("kept=" in args for _, args in calls), [name for name, args in calls if "kept=" not in args]
