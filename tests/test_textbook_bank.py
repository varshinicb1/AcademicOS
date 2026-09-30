"""NCERT textbook exercises (corpus/textbook.py): the questions must be the
book's, a grounded answer must quote the chapter, a worked answer must agree
with an independent second solve, and open-ended or picture questions are
never keyed. What passes is served with its tier labelled, through every merge
gate."""
from __future__ import annotations

from academicos.assessment.qbank_engine import QuestionBank, key_tier
from academicos.corpus import bank_merge as bm
from academicos.corpus import textbook as tb

CHAPTER = """
Chapter 1 Locating Places on the Earth
A map is a drawing of a place on a flat surface. Maps help us find where places are.
The four main directions are north, south, east and west. They are called cardinal directions.
The Equator divides the Earth into the Northern and Southern Hemispheres.
Questions and activities
1. What are the four cardinal directions?
2. Which line divides the Earth into two hemispheres?
3. Discuss with your friends how people found their way before maps.
4. Look at the map on page 5 and name the ocean shown.
5. If a map's scale is 1 cm to 5 km, how far apart are two towns 3 cm apart on the map?
6. The line that divides the Earth into the Northern and Southern Hemispheres is the
(a) Prime Meridian (b) Equator (c) Tropic of Cancer (d) Arctic Circle
"""


def _tb(questions):
    return {"book": {"code": "fees1", "class": 6, "subject": "Social Science", "title": "Exploring Society",
                     "language": "en"},
            "chapter": {"number": 1, "title": "Locating Places on the Earth"}, "questions": questions}


def _q(ref, stem, answer, **kw):
    return {"ref": ref, "page": 3, "type": kw.pop("type", "short_answer"), "stem": stem, "options": kw.pop("options", None),
            "parts": [], "needsFigure": kw.pop("needsFigure", False), "answer": answer, **kw}


QS = [
    _q("Q1", "What are the four cardinal directions?",
       {"source": "grounded", "points": [
           {"text": "North, south, east and west.", "evidence": "The four main directions are north, south, east and west."}]}),
    _q("Q2", "Which line divides the Earth into two hemispheres?",
       {"source": "grounded", "points": [
           {"text": "The Equator.", "evidence": "The Equator divides the Earth into the Southern and Northern halves."}]}),
    _q("Q3", "Discuss with your friends how people found their way before maps.", {"source": "open"}),
    _q("Q4", "Look at the map on page 5 and name the ocean shown.", {"source": "grounded", "points": []},
       needsFigure=True),
    _q("Q5", "If a map's scale is 1 cm to 5 km, how far apart are two towns 3 cm apart on the map?",
       {"source": "solved", "working": "3 x 5 = 15", "finalAnswer": "15 km"}),
    _q("Q6", "The line that divides the Earth into the Northern and Southern Hemispheres is the",
       {"source": "grounded", "correctOption": "B", "points": [
           {"text": "Equator", "evidence": "The Equator divides the Earth into the Northern and Southern Hemispheres."}]},
       type="mcq", options={"A": "Prime Meridian", "B": "Equator", "C": "Tropic of Cancer", "D": "Arctic Circle"}),
    _q("Q7", "Name three rivers of Europe.", {"source": "grounded", "points": [{"text": "Rhine", "evidence": "Rhine"}]}),
]


def test_only_what_can_be_checked_is_built():
    b = tb.build(_tb(QS), CHAPTER, second={"Q5": "15"})
    assert {r["id"].rsplit(":", 1)[1]: r["reason"] for r in b.refused} == {
        "Q2": "evidence-not-found",       # the quote is not the book's sentence
        "Q3": "open-ended", "Q4": "figure-unavailable",
        "Q7": "stem-not-in-book"}         # the book asks no such question
    built = {r["id"].rsplit(":", 1)[1]: r for r in b.records}
    assert set(built) == {"Q1", "Q5", "Q6"}
    assert built["Q1"]["answerScheme"]["provenance"] == "textbook_grounded"
    assert built["Q5"]["answerScheme"]["provenance"] == "two_model_solved"
    assert built["Q6"]["stem"].endswith("(A) Prime Meridian (B) Equator (C) Tropic of Cancer (D) Arctic Circle")
    assert built["Q1"]["metadata"]["marksInferred"] and built["Q1"]["marks"] == 2
    assert built["Q1"]["answerScheme"]["metadata"]["evidence"][0]["quote"].startswith("The four main directions")


def test_a_worked_answer_needs_a_second_solve_that_agrees():
    q5 = [QS[4]]
    assert tb.build(_tb(q5), CHAPTER, second=None).refused[0]["reason"] == "solve-unchecked"
    assert tb.build(_tb(q5), CHAPTER, second={"Q5": "18 km"}).refused[0]["reason"] == "solve-disagrees"
    assert tb.build(_tb(q5), CHAPTER, second={"Q5": "15km"}).records
    assert tb.final_answer_key("x = 15 cm") == tb.final_answer_key("15")


def test_checked_keys_are_served_with_their_tier():
    b = tb.build(_tb(QS), CHAPTER, second={"Q5": "15"})
    for raw in b.records:
        rec, reason = bm.normalise(raw)
        assert reason is None and bm.unservable_reason(rec) is None and bm.contract_errors(rec) == [], raw["id"]
        assert QuestionBank.has_answer_key(rec) and key_tier(rec) == "checked"
    out = bm.compose([], [], [], textbook=b.records)
    assert out.counts["textbook"] == 3


def test_a_hindi_chapter_is_checked_in_its_own_script():
    hindi = "पाठ 1 सूरज\nसूरज पूरब में उगता है और पश्चिम में डूबता है।\n1. सूरज किस दिशा में उगता है?"
    book = {**_tb([])["book"], "code": "fhml1", "subject": "Hindi", "language": "hi"}
    q = _q("Q1", "सूरज किस दिशा में उगता है?",
           {"source": "grounded", "points": [{"text": "पूरब में", "evidence": "सूरज पूरब में उगता है"}]})
    b = tb.build({"book": book, "chapter": {"number": 1, "title": "सूरज"}, "questions": [q]}, hindi)
    assert b.refused == [] and b.records[0]["language"] == "hi"


def test_a_question_about_a_picture_the_student_cannot_see_is_refused():
    q = _q("G1", "What is the purpose of the four arrows shown in the top right corner of the city map?",
           {"source": "grounded", "points": [{"text": "Directions", "evidence": "The four main directions are north, "
                                              "south, east and west."}]}, origin="generated")
    assert tb.build(_tb([q]), CHAPTER).refused[0]["reason"] == "figure-referenced"
    # a word problem about a map's scale needs no picture
    assert tb.build(_tb([QS[4]]), CHAPTER, second={"Q5": "15"}).records


# ---------------------------------------------------------------------------
# Review of #54: answers that reached a tier without being checked.
# ---------------------------------------------------------------------------

def test_a_book_answer_must_be_found_where_the_book_prints_it():
    """`source: book` became the official tier on the transcriber's word."""
    stem = "What are the four cardinal directions?"
    unquoted = _q("Q1", stem, {"source": "book", "points": [{"text": "North, south, east and west."}]})
    quoted = _q("Q1", stem, {"source": "book", "points": [
        {"text": "North, south, east and west.",
         "evidence": "The four main directions are north, south, east and west."}]})
    wrong = _q("Q1", stem, {"source": "book", "points": [
        {"text": "Up and down.", "evidence": "The four main directions are up and down and around."}]})
    assert [r["reason"] for r in tb.build(_tb([unquoted]), CHAPTER).refused] == ["evidence-not-found"]
    assert [r["reason"] for r in tb.build(_tb([wrong]), CHAPTER).refused] == ["evidence-not-found"]
    [rec] = tb.build(_tb([quoted]), CHAPTER).records
    assert rec["answerScheme"]["provenance"] == "ncert_textbook_answer"


def test_a_generated_question_never_claims_a_printed_answer():
    q = _q("G1", "Name the four cardinal directions.", {"source": "book", "points": [
        {"text": "North, south, east and west.",
         "evidence": "The four main directions are north, south, east and west."}]}, origin="generated")
    assert [r["reason"] for r in tb.build(_tb([q]), CHAPTER).refused] == ["generated-unkeyed"]


def test_one_word_is_not_evidence():
    q = _q("Q2", "Which line divides the Earth into two hemispheres?",
           {"source": "grounded", "points": [{"text": "The Equator.", "evidence": "Equator"}]})
    assert [r["reason"] for r in tb.build(_tb([q]), CHAPTER).refused] == ["evidence-not-found"]


def test_a_worked_answer_serves_only_the_checked_final_answer():
    """Only `finalAnswer` is compared with the second solve, so only it is the
    key; a working that does not reach it is not printed ("Area = 50" beside a
    checked 48)."""
    q = _q("Q5", "If a map's scale is 1 cm to 5 km, how far apart are two towns 3 cm apart on the map?",
           {"source": "solved", "points": [{"text": "Distance = 50 km"}], "working": "3 x 5 = 50",
            "finalAnswer": "15 km"})
    [rec] = tb.build(_tb([q]), CHAPTER, second={"Q5": "15 km"}).records
    scheme = rec["answerScheme"]
    assert [p["description"] for p in scheme["markingPoints"]] == ["15 km"]
    assert "50" not in scheme["modelAnswer"]
    ok = _q("Q5", q["stem"], {"source": "solved", "working": "3 x 5 = 15", "finalAnswer": "15 km"})
    [rec] = tb.build(_tb([ok]), CHAPTER, second={"Q5": "15 km"}).records
    assert "Working: 3 x 5 = 15" in rec["answerScheme"]["modelAnswer"]


def test_the_answer_served_is_the_one_its_quote_states():
    """A verified quote beside an unrelated answer served that answer at the
    published tier (re-review of #54)."""
    quote = "The four main directions are north, south, east and west."
    made_up = _q("Q1", "What are the four cardinal directions?",
                 {"source": "book", "finalAnswer": "a made-up answer 99", "evidence": quote})
    assert [r["reason"] for r in tb.build(_tb([made_up]), CHAPTER).refused] == ["answer-not-in-quote"]
    wrong_point = _q("Q1", "What are the four cardinal directions?",
                     {"source": "grounded", "points": [{"text": "Up, down and around.", "evidence": quote}]})
    assert [r["reason"] for r in tb.build(_tb([wrong_point]), CHAPTER).refused] == ["answer-not-in-quote"]
    stem = "The line that divides the Earth into the Northern and Southern Hemispheres is the"
    opts = {"A": "Prime Meridian", "B": "Equator", "C": "Tropic of Cancer", "D": "Arctic Circle"}
    evidence = [{"text": "Equator", "evidence": "The Equator divides the Earth into the Northern and Southern Hemispheres."}]
    wrong_letter = _q("Q6", stem, {"source": "grounded", "correctOption": "C", "points": evidence},
                      type="mcq", options=opts)
    assert [r["reason"] for r in tb.build(_tb([wrong_letter]), CHAPTER).refused] == ["answer-not-in-quote"]
    right = _q("Q6", stem, {"source": "grounded", "correctOption": "B", "points": evidence}, type="mcq", options=opts)
    assert len(tb.build(_tb([right]), CHAPTER).records) == 1


def test_support_needs_whole_words_agreeing_negation_and_one_option():
    """The re-review's three false accepts: a quote naming two options keyed
    either; a dropped or added "not" passed on word overlap; "Sun" matched
    inside "sunlight"."""
    assert tb._supported("Plants need sunlight to make food", "Plants need sunlight to make food.")
    assert not tb._supported("Plants do not need sunlight", "Plants need sunlight to make food.")
    assert not tb._supported("Plants need sunlight", "Plants do not need sunlight in the dark room.")
    assert not tb._supported("Sun", "Plants use sunlight.")
    q = {"options": {"A": "Earth", "B": "Venus", "C": "Mars", "D": "Jupiter"}}
    quote = "Earth is the only planet with life, and Venus is the hottest planet."
    assert not tb._one_option_stated(q, "B", quote)
    assert tb._one_option_stated(q, "A", "Earth is the only planet known to support life.")
