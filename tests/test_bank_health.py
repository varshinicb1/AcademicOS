"""academicos.syllabus.bank_health: the question bank's health per class,
subject, chapter and topic -- including what is missing (PRD rules Q3/Q4).

Everything here runs on a tiny synthetic bank and tree, so each count can be
checked by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.templates import EXAM_PRESETS  # noqa: E402
from academicos.syllabus.bank_health import (  # noqa: E402
    build_report, mark_bucket, render_markdown, subject_family, tagging_accuracy,
)

TREE = {
    "subject": "Mathematics", "grade": 7, "book": "Ganita Prakash",
    "chapters": [
        {"id": "mathematics-7/integers", "name": "Integers", "number": 1, "topics": [
            {"id": "mathematics-7/integers/adding", "name": "Adding", "subtopics": []},
            {"id": "mathematics-7/integers/history", "name": "History", "subtopics": []},
        ]},
        {"id": "mathematics-7/fractions", "name": "Fractions", "number": 2, "topics": [
            {"id": "mathematics-7/fractions/halves", "name": "Halves", "subtopics": []},
        ]},
        {"id": "mathematics-7/symmetry", "name": "Symmetry", "number": 3, "topics": []},
    ],
}


def _q(qid, marks, *, chapter=None, topic=None, subtopic=None, key="answer", subject="Mathematics",
       grade=7, prov="ncert_exemplar_answer", source="ncert_exemplar", difficulty=None,
       qtype="short_answer", **extra):
    rec = {
        "id": qid, "subject": subject, "grade": grade, "marks": marks, "type": qtype,
        "source": source, "chapterIds": [],
        "difficulty": difficulty or {1: "easy", 2: "easy", 3: "medium"}.get(marks, "hard"),
        "answerScheme": {"modelAnswer": key, "markingPoints": [], "provenance": prov},
        "metadata": {},
    }
    if chapter is not None:
        rec.update(taxonomyChapterId=chapter, topicIds=[topic] if topic else [],
                   subtopicIds=[subtopic] if subtopic else [], tagMethod="tfidf_textbook_v2")
    rec.update(extra)
    return rec


ADD = "mathematics-7/integers/adding"
BANK = [
    _q("a1", 1, chapter="mathematics-7/integers", topic=ADD, subtopic=ADD + "/rule"),
    _q("a2", 3, chapter="mathematics-7/integers", topic=ADD),
    _q("a3", 5, chapter="mathematics-7/integers"),
    _q("a4", 1, chapter="mathematics-7/fractions", topic="mathematics-7/fractions/halves"),
    _q("a5", 2),                                           # untagged, keyed
    _q("a6", 3, chapter="mathematics-7/fractions", key=""),  # no answer key (Q1)
    _q("a7", 7, prov="cbse_marking_scheme", source="cbse_question_bank", qtype="long_answer"),
    _q("x1", 1, grade=12),                                  # outside classes 6-10
    _q("x2", 1, subject="German", grade=7),                 # outside the five subjects
]

# `_merge_excluded.json`'s shape (bank_merge._excluded): the id, where it came
# from, why it was refused, and 200 characters of the stem.
def _out(qid, reason, *, subject="Mathematics", grade=7, source="ncert_exemplar"):
    return {"id": qid, "source": source, "reason": reason, "subject": subject,
            "grade": grade, "stem": f"a stem refused for {reason}"}


EXCLUDED = [
    _out("b1", "options-missing"),
    _out("b2", "options-missing"),
    _out("b3", "figure-shown-below"),
    _out("b4", "no-verified-key", source="cbse_board_paper"),
    _out("b5", "duplicate-stem", subject="Science", grade=9),
    _out("b6", "options-missing", subject="Mathematics (Standard)", grade=10),
    _out("b7", "answer-bleed", grade=12),                    # outside classes 6-10
    _out("b8", "answer-bleed", subject="German"),            # outside the five subjects
]

TINY = {
    "tiny": {"name": "Tiny", "sections": [
        ("A", "MCQ", 1, 2, ["easy", "medium"], False, 0),
        ("C", "Short Answer", 3, 1, ["medium", "hard"], True, 1),
    ]},
    "ones": {"name": "Ones", "sections": [("A", "MCQ", 1, 2, ["easy", "medium"], False, 0)]},
}


def _report(bank=BANK, presets=TINY, **kw):
    return build_report({"exemplar": bank}, {("Mathematics", 7): TREE}, presets=presets, **kw)


def _cell(report, subject="Mathematics", grade=7):
    return next(c for c in report["cells"] if c["subject"] == subject and c["grade"] == grade)


def test_every_class_and_subject_gets_a_cell_even_an_empty_one():
    report = _report()
    got = {(c["subject"], c["grade"]) for c in report["cells"]}
    assert got == {(s, g) for s in ("Mathematics", "Science", "Social Science", "English", "Hindi")
                   for g in range(6, 11)}
    empty = _cell(report, "Hindi", 6)
    assert empty["questions"] == 0 and empty["tree"] is False


def test_cell_counts():
    c = _cell(_report())
    assert c["questions"] == 7                    # grade 12 and German are out of scope
    assert c["byBank"] == {"exemplar": 7}
    assert c["bySource"] == {"ncert_exemplar": 6, "cbse_question_bank": 1}
    assert c["keyed"] == 6 and c["noKey"] == 1
    assert c["keyProvenance"] == {"ncert_exemplar_answer": 5, "cbse_marking_scheme": 1}
    assert c["tagged"]["chapter"]["n"] == 5
    assert c["tagged"]["topic"]["n"] == 3
    assert c["tagged"]["subtopic"]["n"] == 1
    assert c["tagged"]["chapter"]["pct"] == round(100 * 5 / 7, 1)
    # a5 and a7 never went through the tagger (no tagMethod): their blank is not
    # the tagger declining, and the report keeps the two apart
    assert c["neverTagged"] == 2
    # the marks and types of the questions that can be served (keyed)
    assert c["marks"] == {"1": 2, "2": 1, "3": 1, "4": 0, "5": 1, "6+": 1}
    assert c["types"] == {"short_answer": 5, "long_answer": 1}


def test_mark_buckets_and_subject_families():
    assert [mark_bucket(m) for m in (1, 2, 3, 4, 5, 6, 10)] == ["1", "2", "3", "4", "5", "6+", "6+"]
    assert subject_family({"subject": "Mathematics (Standard)"}) == "Mathematics"
    assert subject_family({"subject": "Hindi Course A"}) == "Hindi"
    assert subject_family({"subject": "English Language and Literature"}) == "English"
    assert subject_family({"subject": "X", "metadata": {"subjectFamily": "Science"}}) == "Science"
    assert subject_family({"subject": "German"}) is None


def test_verifier_state_is_said_not_implied():
    """The relink's own rule decides (question_bank.builder_key_reason for a
    CBE/SQP/Exemplar key, bank_merge.has_verified_key for a board one); a
    verdict recorded on the scheme wins."""
    v = _cell(_report())["verified"]
    assert v["state"] == "verified" and v["passed"] == v["of"] == 6 and v["unchecked"] == 0
    bank = [dict(q, answerScheme=dict(q["answerScheme"], verification={"passed": q["id"] != "a2"}))
            for q in BANK]
    v = _cell(_report(bank))["verified"]
    assert v["state"] == "verified" and v["passed"] == 5 and v["of"] == 6
    assert _cell(_report([BANK[5]]))["verified"] == {"state": "not verified"}


def test_a_key_the_relink_would_remove_and_an_unstamped_board_key_fail():
    from academicos.syllabus.bank_health import key_verified

    # An assertion-reason letter for a stem that prints no options.
    ar = _q("s1", 1, key="B)", source="cbse_sample_paper", prov="cbse_marking_scheme",
            stem="Assertion (A): HCF of any two consecutive even natural numbers is always 2. "
                 "Reason (R): Even natural numbers are divisible by 2.")
    assert key_verified(ar) is False
    board = _q("b1", 2, source="cbse_board_paper", prov="cbse_marking_scheme")
    assert key_verified(board) is False          # no relink stamp: fails closed
    board["answerScheme"]["metadata"] = {"schemeCode": "31/1/1", "schemeQNo": 4}
    assert key_verified(board) is True
    assert key_verified(_q("n1", 2, key="")) is None


def test_chapters_and_topics_count_keyed_questions_and_marks():
    chapters = {ch["id"]: ch for ch in _cell(_report())["chapters"]}
    integers = chapters["mathematics-7/integers"]
    assert integers["questions"] == 3 and integers["marks"] == 9
    assert integers["byMarks"] == {"1": 1, "2": 0, "3": 1, "4": 0, "5": 1, "6+": 0}
    adding = next(t for t in integers["topics"] if t["id"] == ADD)
    assert adding["questions"] == 2 and adding["marks"] == 4
    fractions = chapters["mathematics-7/fractions"]
    assert fractions["questions"] == 1              # a6 has no key and is not counted


def test_empty_chapters_and_topics_are_listed():
    c = _cell(_report())
    assert c["emptyChapters"] == ["mathematics-7/symmetry"]
    assert c["chaptersWithout3Mark"] == ["mathematics-7/fractions", "mathematics-7/symmetry"]
    assert c["chaptersWithout5Mark"] == ["mathematics-7/fractions", "mathematics-7/symmetry"]
    assert c["emptyTopics"] == ["mathematics-7/integers/history"]
    assert c["untaggedKeyed"] == 2                 # a5 and a7 sit in no chapter


def test_a_chapter_whose_only_long_question_is_not_5_marks_has_no_5_mark_question():
    # the board paper's Section D needs exactly 5 marks; an 8-mark CBE item does not fill it
    bank = [_q("f1", 8, chapter="mathematics-7/fractions", topic="mathematics-7/fractions/halves"),
            _q("f2", 5, chapter="mathematics-7/integers", topic=ADD)]
    c = _cell(_report(bank))
    fractions = next(ch for ch in c["chapters"] if ch["id"] == "mathematics-7/fractions")
    assert fractions["byMarks"]["5"] == 0 and fractions["byMarks"]["6+"] == 1
    assert "mathematics-7/fractions" in c["chaptersWithout5Mark"]
    assert "mathematics-7/fractions/halves" in c["topicsWithout5Mark"]
    assert "mathematics-7/integers" not in c["chaptersWithout5Mark"]
    assert ADD not in c["topicsWithout5Mark"]
    md = render_markdown(_report(bank))
    assert "| 5m | 6m+ |" in md
    assert "**Chapters with no 5-mark question (2):** Fractions" in md


def test_paper_verdict_and_its_reason():
    papers = _cell(_report())["papers"]["all"]
    assert papers["ones"] == {"possible": True, "reasons": []}
    tiny = papers["tiny"]
    assert tiny["possible"] is False
    # section C needs 1 question + 1 OR alternative at exactly 3 marks; a2 is
    # the only keyed one (a6 has no key, so Q1 keeps it out)
    assert tiny["reasons"] == [
        "Section C (Short Answer): needs 2 keyed 3-mark questions (1 + 1 OR), has 1"]


def test_paper_verdict_is_given_for_the_served_bank_alone_too():
    report = build_report({"served": BANK[:1], "exemplar": BANK[1:]},
                          {("Mathematics", 7): TREE}, presets=TINY, served="served")
    cell = _cell(report)
    papers = cell["papers"]
    assert cell["servedKeyed"] == 1
    assert papers["served"]["ones"]["possible"] is False
    assert papers["all"]["ones"]["possible"] is True


def test_the_default_presets_are_the_paper_builders():
    assert set(_cell(_report(presets=None))["papers"]["all"]) == set(EXAM_PRESETS)


MODEL = {"thresholds": {"chapter": 0.73, "topic": 0.76, "subtopic": 0.68},
         "gold": {"items": 389, "nested": {"accepted": {
             "chapter": {"right": 120, "tags": 129, "precision": 0.9302, "wilsonLower95": 0.8727},
             "topic": {"right": 51, "tags": 55, "precision": 0.9273, "wilsonLower95": 0.8274},
             "subtopic": {"right": 40, "tags": 43, "precision": 0.9302, "wilsonLower95": 0.8139}}}}}
AUDIT_SUB = {"measured": {"right": 28, "tags": 30}}
AUDIT_CT = {"measured": {"chapter": {"right": 30, "tags": 30}, "topic": {"right": 2, "tags": 7}},
            "items": [
                {"id": "t1", "levels": ["topic"], "right": True, "topics": ["a/ch/x"],
                 "chapters": ["a/ch"], "taggedAs": {"chapter": "a/ch", "topic": "a/ch/x"}},
                {"id": "t2", "levels": ["topic"], "right": False, "topics": ["a/ch/y"],
                 "chapters": ["a/ch"], "taggedAs": {"chapter": "a/ch", "topic": "a/ch/x"},
                 "note": "other"},
                {"id": "t3", "levels": ["topic"], "right": False, "topics": [], "chapters": [],
                 "taggedAs": {"chapter": "a/ch", "topic": "a/ch/x"}, "note": "not taught"},
                # taught in the tagged chapter, but no section of it fits: NOT "not in the book"
                {"id": "t5", "levels": ["topic"], "right": False, "topics": [],
                 "chapters": ["a/ch"], "taggedAs": {"chapter": "a/ch", "topic": "a/ch/x"},
                 "note": "chapter opening"},
                # the fitting section is in a different chapter of the same book
                {"id": "t6", "levels": ["topic"], "right": False, "topics": ["a/other/z"],
                 "chapters": ["a/other"], "taggedAs": {"chapter": "a/ch", "topic": "a/ch/x"},
                 "note": "elsewhere"},
                # a fitting section in the tagged chapter and one outside it: the tagged chapter wins
                {"id": "t7", "levels": ["topic"], "right": False,
                 "topics": ["a/other/z", "a/ch/y"], "chapters": ["a/other", "a/ch"],
                 "taggedAs": {"chapter": "a/ch", "topic": "a/ch/x"}, "note": "both"},
                {"id": "t4", "levels": ["topic"], "right": True, "topics": ["a/ch/z"],
                 "chapters": ["a/ch"], "taggedAs": {"chapter": "a/ch", "topic": "a/ch/z"}},
                {"id": "c1", "levels": ["chapter"], "right": True},
            ]}


def test_tagging_accuracy_quotes_nested_and_held_out_numbers():
    acc = tagging_accuracy(MODEL, AUDIT_SUB, AUDIT_CT)
    assert acc["nested"]["topic"] == {"right": 51, "tags": 55, "precision": 0.9273,
                                      "wilsonLower95": 0.8274}
    assert acc["heldOut"]["chapter"] == {"right": 30, "tags": 30, "precision": 1.0}
    assert acc["heldOut"]["topic"] == {"right": 2, "tags": 7, "precision": 0.2857}
    assert acc["heldOut"]["subtopic"] == {"right": 28, "tags": 30, "precision": 0.9333}
    # a wrong topic tag is bucketed by comparing the audit's topics and chapters with the
    # chapter it was tagged to; an empty topics list alone does not mean "not in the book"
    assert acc["wrongTopics"] == {"otherSection": 2, "otherChapter": 1, "noSectionFits": 1,
                                  "notInBook": 1,
                                  "items": [{"id": "t2", "note": "other", "bucket": "otherSection"},
                                            {"id": "t3", "note": "not taught",
                                             "bucket": "notInBook"},
                                            {"id": "t5", "note": "chapter opening",
                                             "bucket": "noSectionFits"},
                                            {"id": "t6", "note": "elsewhere",
                                             "bucket": "otherChapter"},
                                            {"id": "t7", "note": "both",
                                             "bucket": "otherSection"}]}


def test_markdown_does_not_call_a_chapter_taught_question_absent_from_the_book():
    report = _report()
    report["tagging"] = tagging_accuracy(MODEL, AUDIT_SUB, AUDIT_CT)
    md = render_markdown(report)
    assert "All 5 wrong topic tags" in md
    assert "in 2 another section of the same chapter does" in md
    assert "in 1 a section of another chapter of the same book does" in md
    assert "1 is taught in a chapter of the book but fit no one section of it" in md
    assert "1 is taught nowhere in the class's book" in md


def test_what_the_merge_left_out_is_counted_per_reason_and_per_cell():
    """Task 126, requirement 4: every record the gate removes is in the
    exclusions file with its reason AND the health report counts it. The
    report used to count only what survived, so a class whose sources were
    mostly refused read as healthy."""
    report = _report(exclusions=EXCLUDED)
    assert report["excluded"]["records"] == 8
    # b7 is class 12 and b8 is German: refused, counted in the total, in no cell
    assert report["excluded"]["inScope"] == 6
    assert report["excluded"]["outOfScope"] == 2
    # commonest first, so the biggest hole is the first thing read
    assert list(report["excluded"]["byReason"])[0] == "options-missing"
    assert report["excluded"]["byReason"]["options-missing"] == 3
    assert report["excluded"]["bySource"] == {"ncert_exemplar": 7, "cbse_board_paper": 1}

    cell = _cell(report)
    assert cell["excluded"]["n"] == 4       # b1-b4; b6 is class 10
    assert cell["excluded"]["byReason"] == {"options-missing": 2,
                                            "figure-shown-below": 1,
                                            "no-verified-key": 1}
    # "Mathematics (Standard)" is counted under Mathematics, as a question is
    assert _cell(report, "Mathematics", 10)["excluded"]["n"] == 1
    assert _cell(report, "Science", 9)["excluded"]["n"] == 1
    assert _cell(report, "Hindi", 6)["excluded"] == {"n": 0, "byReason": {}}


def test_a_report_shown_no_exclusions_file_claims_nothing_about_it():
    """Absent is not zero. A report built without the file must not print
    "0 left out" for a class whose sources were thrown away wholesale."""
    report = _report()
    assert "excluded" not in report
    assert all("excluded" not in c for c in report["cells"])
    assert "What the merge left out" not in render_markdown(report)


def test_markdown_says_what_was_left_out_and_why():
    report = _report(exclusions=EXCLUDED)
    report["excludedPath"] = "academicos-data/syllabus/_merge_excluded.json"
    md = render_markdown(report)
    assert "## What the merge left out" in md
    assert "_merge_excluded.json" in md
    assert "**8 records refused**, 6 of them in scope" in md
    assert "| options-missing | 3 |" in md
    assert "| cbse_board_paper | 1 |" in md
    # the per-pair row: the bank's own count beside what was refused for it
    assert "| Mathematics | 7 | 7 | 4 | options-missing 2, figure-shown-below 1," in md


def test_markdown_names_its_inputs_date_gaps_and_verdicts():
    report = _report()
    report["inputs"] = [{"label": "exemplar", "path": "bank.json", "sha256": "ab" * 32,
                         "records": 9}]
    report["builtAt"] = "2026-09-22"
    report["tagging"] = tagging_accuracy(MODEL, AUDIT_SUB, AUDIT_CT)
    md = render_markdown(report)
    assert "ab" * 32 in md and "2026-09-22" in md
    assert "| 6/6 passed (100.0% of keyed; 0 unchecked) |" in md  # the verifier's verdict
    assert "not verified" in render_markdown(_report([BANK[5]]))  # a6: no key to check
    assert "Symmetry" in md                               # the empty chapter, by name
    assert "needs 2 keyed 3-mark questions" in md          # the verdict's reason
    assert "51/55" in md and "2/7" in md                   # nested and held-out topic figures


def test_script_writes_both_reports_with_the_inputs_sha256(tmp_path):
    import hashlib
    import importlib.util
    import json

    spec = importlib.util.spec_from_file_location("bank_health_script",
                                                  ROOT / "scripts" / "bank_health.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    served, extra = tmp_path / "served" / "questions.json", tmp_path / "exemplar" / "questions.json"
    for path, recs in ((served, BANK[:3]), (extra, BANK[3:])):
        path.parent.mkdir()
        path.write_text(json.dumps({"questions": recs}), encoding="utf-8")
    tax = tmp_path / "taxonomy"
    tax.mkdir()
    for name, data in (("Mathematics_7.json", TREE), ("_tagger_model.json", MODEL),
                       ("_tag_audit.json", AUDIT_SUB), ("_tag_audit_chapter_topic.json", AUDIT_CT)):
        (tax / name).write_text(json.dumps(data), encoding="utf-8")
    excluded = tmp_path / "served" / "_merge_excluded.json"
    excluded.write_text(json.dumps({"excluded": EXCLUDED}), encoding="utf-8")
    md, js = tmp_path / "out" / "bank-health.md", tmp_path / "out" / "bank_health.json"
    args = ["--served", str(served), "--bank", str(extra), "--taxonomy", str(tax),
            "--excluded", str(excluded), "--md", str(md), "--json", str(js)]
    assert mod.main(args + ["--check"]) == 0 and not md.exists() and not js.exists()
    assert mod.main(args) == 0
    report = json.loads(js.read_text(encoding="utf-8"))
    sha = hashlib.sha256(served.read_bytes()).hexdigest()
    shas = {i["label"]: i["sha256"] for i in report["inputs"]}
    assert shas["served"] == sha
    assert sha in md.read_text(encoding="utf-8")
    assert _cell(report)["byBank"] == {"served": 3, "exemplar": 4}
    # the exclusions file is an input like any other, named and hashed, so the
    # report can be matched to the merge run that wrote it
    assert shas["excluded"] == hashlib.sha256(excluded.read_bytes()).hexdigest()
    assert report["excluded"]["records"] == len(EXCLUDED)
    assert "## What the merge left out" in md.read_text(encoding="utf-8")


def test_a_missing_exclusions_file_is_reported_not_guessed_at(tmp_path, capsys):
    """The report says it was not shown the file rather than printing zeroes."""
    import importlib.util
    import json

    spec = importlib.util.spec_from_file_location("bank_health_script",
                                                  ROOT / "scripts" / "bank_health.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    served = tmp_path / "served" / "questions.json"
    served.parent.mkdir()
    served.write_text(json.dumps({"questions": BANK}), encoding="utf-8")
    tax = tmp_path / "taxonomy"
    tax.mkdir()
    for name, data in (("Mathematics_7.json", TREE), ("_tagger_model.json", MODEL),
                       ("_tag_audit.json", AUDIT_SUB), ("_tag_audit_chapter_topic.json", AUDIT_CT)):
        (tax / name).write_text(json.dumps(data), encoding="utf-8")
    assert mod.main(["--served", str(served), "--bank", "--taxonomy", str(tax),
                     "--excluded", str(tmp_path / "nowhere.json"), "--check"]) == 0
    out = capsys.readouterr().out
    assert "will not say what the merge left out" in out


def test_repo_banks_are_named_by_their_repo_path_even_through_a_junction():
    """This checkout's academicos-data is a junction to another drive; the
    report named every input by its D: path until it read the path unresolved."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("bank_health_script_rel",
                                                  ROOT / "scripts" / "bank_health.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._rel(mod.SERVED) == "academicos-data/syllabus/questions.json"
    assert mod._label(mod.EXTRA[0], served=False) == "ncert-exemplar"


def test_untagged_keyed_questions_make_the_gap_lists_a_lower_bound():
    # a5 and a7 are keyed but untagged: a chapter with none of the tagged
    # questions may still hold them, so "no question" would be false.
    report = _report()
    c = _cell(report)
    assert c["chapterCountsComplete"] is False
    md = render_markdown(report)
    assert "Chapters with no tagged question" in md
    assert "Chapters with no question" not in md
    assert "2 keyed questions are untagged" in md


def test_a_fully_tagged_cell_lists_its_gaps_as_absolute():
    tagged = [q for q in BANK if q.get("taxonomyChapterId") or q["id"] in ("x1", "x2")]
    report = _report(bank=tagged)
    assert _cell(report)["chapterCountsComplete"] is True
    assert "Chapters with no question" in render_markdown(report)
