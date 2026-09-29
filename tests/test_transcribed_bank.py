"""Papers transcribed with their official schemes (corpus/transcribed.py):
nothing served on the transcription's word -- every value point found in the
scheme's own text, and where its question's answer is; half marks joined into
whole marks; figures, unkeyed MCQs and unverified answers refused with the
reason; and in the merge, a placed long "any N" answer is not mistaken for a
run-on while an unplaced one still is."""
from __future__ import annotations

from academicos.corpus import bank_merge as bm
from academicos.corpus import transcribed as tr

SCHEME = """
Marking Scheme 32/1/1
1 (B) Italy 1
21 Any two points: The silk routes linked Asia with Europe and northern Africa.
Chinese pottery travelled the same route. Textiles and spices from India went to Europe.
Precious metals flowed from Europe to Asia. 2
22 Industries help modernise agriculture. They reduce dependence on agricultural income. 1/2+1/2
23 Democracy promotes equality among citizens. 1
"""


def _paper(questions):
    return {"paper": {"kind": "board", "year": 2024, "class": 10, "subject": "Social Science", "code": "32/1/1"},
            "questions": questions}


def _q(number, **kw):
    q = {"number": number, "section": "B", "marks": 2, "type": "short_answer", "stem": f"Question {number} text?",
         "options": None, "parts": [], "alternative": None, "needsFigure": False,
         "scheme": {"correctOption": None, "points": [], "anyN": None}}
    q.update(kw)
    return q


def _build(questions):
    return tr.build(_paper(questions), source="cbse_board_paper", scheme=tr.SchemeText.of(SCHEME),
                    scheme_file="32-1-1 E.pdf", id_prefix="cbse:board")


def test_an_mcq_and_a_verified_answer_build_and_pass_the_merge_gates():
    b = _build([
        _q("1", marks=1, type="mcq", stem="Giuseppe Garibaldi belonged to which country?",
           options={"A": "Austria", "B": "Italy", "C": "Greece", "D": "Spain"},
           scheme={"correctOption": "B", "points": []}),
        _q("22", scheme={"points": [{"text": "Industries help modernise agriculture.", "marks": 0.5},
                                    {"text": "They reduce dependence on agricultural income.", "marks": 0.5},
                                    {"text": "Democracy promotes equality among citizens.", "marks": 1}]}),
    ])
    assert b.refused == []
    mcq, sa = b.records
    assert mcq["stem"].endswith("(A) Austria (B) Italy (C) Greece (D) Spain")
    assert mcq["answerScheme"]["metadata"]["correctOption"] == "B"
    # two half-mark points are one whole-mark point; the phone's scheme holds whole marks
    assert [(p["description"], p["marks"]) for p in sa["answerScheme"]["markingPoints"]] == [
        ("Industries help modernise agriculture.; They reduce dependence on agricultural income.", 1),
        ("Democracy promotes equality among citizens.", 1)]
    for raw in b.records:
        rec, reason = bm.normalise(raw)
        assert reason is None and bm.unservable_reason(rec) is None and bm.contract_errors(rec) == [], raw["id"]


def test_what_is_refused_and_why():
    b = _build([
        _q("2", marks=1, type="mcq", options={"A": "a", "B": "b", "C": "c", "D": "d"},
           scheme={"correctOption": None, "notes": "marks to be given if attempted"}),
        _q("3", marks=1, type="mcq", options={"A": "a", "B": "b"}, scheme={"correctOption": "A"}),
        _q("37", marks=5, type="map", needsFigure=True, scheme={"points": [{"text": "Dandi", "marks": 1}]}),
        _q("23", scheme={"points": [{"text": "Parliament passes the budget every year.", "marks": 2}]}),
        _q("24", scheme={"points": []}),
    ])
    assert {r["id"].rsplit(":", 1)[1]: r["reason"] for r in b.refused} == {
        "q2": "mcq-answer-unresolved", "q3": "options-missing", "q37": "figure-unavailable",
        "q23": "scheme-unverified", "q24": "no-answer"}
    assert b.records == []


def test_an_internal_choice_is_its_own_record():
    choice = _q("", scheme={"points": [{"text": "Democracy promotes equality among citizens.", "marks": 2}]})
    b = _build([_q("22", alternative=choice,
                   scheme={"points": [{"text": "Industries help modernise agriculture.", "marks": 2}]})])
    assert [r["id"] for r in b.records] == ["cbse:board:2024:32-1-1:q22", "cbse:board:2024:32-1-1:q22-or"]
    assert b.records[1]["metadata"]["alternativeOf"] == "cbse:board:2024:32-1-1:q22"


# A real scheme puts hundreds of characters between answers (value points, notes, marks).
_FILL = " Note to examiners: award marks for any correct explanation in the student's own words." * 4
SCHEME_ORDERED = f"""
Marking Scheme 31/1/1
24 Photosynthesis needs sunlight, water and carbon dioxide. 2 {_FILL}
25 Respiration releases energy from glucose. 2 {_FILL}
26 Transpiration pulls water up the xylem. 2 {_FILL}
27 Digestion breaks food into simpler substances. 2 {_FILL}
"""


def test_another_questions_answer_copied_in_is_out_of_place():
    assert tr.misplaced([("a", [10]), ("b", [500]), ("c", [900])], slack=50) == set()
    assert tr.misplaced([("a", [10]), ("b", [900]), ("c", [300]), ("d", [500]), ("e", [950])], slack=50) == {"b"}
    answers = ["Photosynthesis needs sunlight, water and carbon dioxide.", "Respiration releases energy from glucose.",
               "Transpiration pulls water up the xylem.", "Digestion breaks food into simpler substances."]
    # Q25's answer is Q27's: every point is in the scheme, but not where Q25's answer is
    given = [answers[0], answers[3], answers[2], answers[3]]
    b = tr.build(_paper([_q(str(24 + i), scheme={"points": [{"text": t, "marks": 2}]}) for i, t in enumerate(given)]),
                 source="cbse_board_paper", scheme=tr.SchemeText.of(SCHEME_ORDERED), scheme_file="31-1-1.pdf",
                 id_prefix="cbse:board")
    assert b.refused == [{"id": "cbse:board:2024:32-1-1:q25", "reason": "scheme-out-of-place"}]
    assert all(r["answerScheme"]["metadata"]["placeVerified"] for r in b.records)


def test_a_long_any_n_answer_is_not_a_run_on_only_when_placed():
    long_points = [{"text": f"Value point number {i} about the silk routes linked Asia with Europe.", "marks": 1}
                   for i in range(14)]
    raw = tr.record(_q("21", marks=2, scheme={"points": long_points, "anyN": 2}), _paper([])["paper"],
                    rid="cbse:board:2024:32-1-1:q21", bank_id="b", source="cbse_board_paper", scheme_file="x")
    raw["answerScheme"]["metadata"]["placeVerified"] = True
    rec, reason = bm.normalise(raw)
    assert reason is None and bm.unservable_reason(rec) is None
    rec["answerScheme"]["metadata"]["placeVerified"] = False
    assert bm.unservable_reason(rec) == "answer-bleed"


def test_compose_serves_transcribed_papers_before_the_other_sources():
    b = _build([_q("22", scheme={"points": [{"text": "Industries help modernise agriculture.", "marks": 2}]})])
    out = bm.compose([], [], [], transcribed=b.records)
    assert out.counts["transcribed"] == 1 and out.questions[0]["id"] == "cbse:board:2024:32-1-1:q22"
    # a second run reads the served copy back: it is rebuilt from its source, not taken as a relinked board record
    again = bm.compose(out.questions, [], [], transcribed=b.records)
    assert again.counts == {**out.counts} and not again.withheld


def test_sample_papers_of_one_year_have_an_id_per_subject():
    """Every sample paper of a year carries the code "SQP 2025-26": keyed on the
    code alone, two subjects' question 1 were one id (124 collisions,
    2026-09-29). The subject names the paper too, and an id has no spaces."""
    ids = []
    for subject in ("Hindi Course A", "Hindi Course B"):
        paper = {"paper": {"kind": "sqp", "year": 2025, "class": 10, "subject": subject, "code": "SQP 2025-26"},
                 "questions": [_q("22", scheme={"points": [
                     {"text": "Industries help modernise agriculture.", "marks": 2}]})]}
        b = tr.build(paper, source="cbse_sample_paper", scheme=tr.SchemeText.of(SCHEME), scheme_file="x.pdf",
                     id_prefix="cbse:sqpt")
        ids += [r["id"] for r in b.records]
    assert ids == ["cbse:sqpt:2025:hindi-course-a-sqp-2025-26:q22", "cbse:sqpt:2025:hindi-course-b-sqp-2025-26:q22"]
    # A board code names its paper alone, as before; a note beside a number is not part of the id.
    assert tr.paper_key({"code": "32/1/1", "subject": "Social Science"}) == "32-1-1"
    b = tr.build(_paper([_q("37 (Visually Impaired)", visuallyImpairedVariant=True, scheme={"points": [
        {"text": "Democracy promotes equality among citizens.", "marks": 2}]})]),
        source="cbse_board_paper", scheme=tr.SchemeText.of(SCHEME), scheme_file="x.pdf", id_prefix="cbse:board")
    assert [r["id"] for r in b.records] == ["cbse:board:2024:32-1-1:q37-vi"]


def test_the_builder_reads_a_papers_second_solves_and_never_as_a_paper(tmp_path):
    """scripts/build_transcribed_bank.py read `<paper>.solve2.json` as a paper
    ("scheme file missing") and never handed it to the checker, so an answer
    the scheme's text cannot confirm (Mathematics working set as images)
    stayed refused however well it had been solved again."""
    import json
    import sys
    from pathlib import Path

    import pymupdf

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import build_transcribed_bank as btb

    pdf = tmp_path / "32-1-1 E.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((40, 60), SCHEME * 6, fontsize=6)
    doc.save(str(pdf))
    worked = _q("25", marks=3, stem="A car covers 45 km in 3 hours. Find its speed.",
                scheme={"points": [{"text": "Speed = 45 / 3 = 15 km/h", "marks": 3}]})
    paper = _paper([worked])
    paper["paper"]["schemeFile"] = str(pdf)
    folder = tmp_path / "board"
    folder.mkdir()
    (folder / "board-2024-32-1-1.json").write_text(json.dumps(paper), encoding="utf-8")

    records, refused, report = btb.build(folder)
    assert (records, [r["reason"] for r in refused]) == ([], ["scheme-unverified"])

    (folder / "board-2024-32-1-1.solve2.json").write_text(json.dumps({"25": "15 km/h"}), encoding="utf-8")
    records, refused, report = btb.build(folder)
    assert [r["id"] for r in records] == ["cbse:board:2024:32-1-1:q25"] and refused == []
    assert [r["file"] for r in report] == ["board-2024-32-1-1.json"], "the second solves are not a paper"
