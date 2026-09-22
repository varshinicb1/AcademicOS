"""An official answer is labelled official only when it answers this question.

The audit of 2026-09-21 found 895 of the served bank's 2,930 "official" schemes
detectably wrong, and about 75% of the subjective ones answering a different
question. The root cause: answer_keys.db holds 15,605 rows under 11,787
(paper code, question number) keys -- 3,117 keys carry answers from more than
one source document -- and the index kept whichever row loaded last.

Every stem and answer below is copied from the served bank or answer_keys.db,
cited by record id or source file, except where a docstring says otherwise.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.assessment.question_bank import (  # noqa: E402
    AnswerKeyIndex,
    OfficialAnswer,
    relink_answer_schemes,
    verify_answer,
)
from academicos.corpus.scheme_verify import REASONS, verify  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "scheme_verify_sample.json"

ANSWER_KEYS_SCHEMA = """
CREATE TABLE answer_keys (
  subject TEXT, grade TEXT, paper_code TEXT, q_no INTEGER,
  correct_option TEXT, answer_text TEXT, value_points TEXT, marks REAL,
  source TEXT
);
"""


def make_answer_keys(path: Path, rows: list[tuple]) -> Path:
    con = sqlite3.connect(path)
    con.executescript(ANSWER_KEYS_SCHEMA)
    con.executemany("INSERT INTO answer_keys VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return path


def make_parse_tree(parse_dir: Path, doc_hash: str, header: str) -> None:
    parse_dir.mkdir(parents=True, exist_ok=True)
    (parse_dir / f"src_{doc_hash}.json").write_text(json.dumps({
        "document_id": f"src:{doc_hash}", "doc_type": "question_paper",
        "pages": [{"page_no": 1, "kind": "text", "text": header + " body" * 40}],
    }), encoding="utf-8")


def rec(stem: str, *, subject: str = "Science", marks: int = 3, **extra) -> dict:
    return {"stem": stem, "subject": subject, "marks": marks, **extra}


# --------------------------------------------------------------------------- #
# each rejection reason, on a real pair
# --------------------------------------------------------------------------- #

# cbse:q:src:856803fb4333bfbe91cef527:29 (32/5/2 Q29) and the two candidates
# answer_keys.db files under its key.
SECTORS_STEM = "How are primary, secondary and tertiary sectors dependent on each other ? Explain."
SECTORS_ENGLISH = ("How primary, secondary and tertiary sectors are dependent on each other? "
                   "Primary Secondary and Tertiary sectors are interdependent as mentioned below "
                   "(i) Primary sector activities produces goods by exploiting natural resources "
                   "and provide raw material to manufacturing sector")        # "32_5_2 E.pdf"
SECTORS_HINDI = ("(a) भारतीय िोकतंत्र में र्दिीय व्यवस्था की भूनमका का नवश्लेिण संसार भर में तीन "
                 "प्रकार की पार्ी प्रणािी हैं- एक दिीय, नद्व-दिीय और बहु-दिीय प्रणािी। भारत में "
                 "बहु-दिीय इसके अिावा, भारत में राजनीनतक दिों को दो मुख्य")  # "32-5-2 H.pdf"

# cbse:q:src:c2655c8196cc86e419c8e9de:24, Geography 64/4/1 Q24. The served
# scheme is a Hindi-medium Physics answer: the old `_SUBJECT_CODE_MAP` sent
# code 64 (Geography) to 55 (Physics).
GEOGRAPHY_STEM = "Describe income and welfare approaches to human development."
PHYSICS_IN_HINDI = ("प्रेररत धारा की ष्टदशा ज्ञात औ पुष्टि करना, (a) कुोंडली ‘2’, "
                    "कुोंडली ‘1’ की ओ गष्टतमान िै ½+½")


def test_script_mismatch_rejects_a_devanagari_answer_to_an_english_question():
    """cbse:q:src:784bd959b5f48fd5620f57e6:2 (57/1/1 Q2) with its candidate
    from "XII_044_MS_57-1-1 HINDI.pdf" (HI_ROW below): the Hindi-medium
    scheme filed under the same key, naming red blood cells."""
    v = verify(rec(HCG_STEM, subject="Biology", marks=1), HI_ROW[5])
    assert not v.accepted
    assert v.reason == "script-mismatch"


def test_the_other_mediums_answer_to_another_question_is_rejected():
    """32/5/2 Q29 (cbse:q:src:856803fb4333bfbe91cef527:29): its Hindi-medium
    candidate ("32-5-2 H.pdf") answers a party-system question and is
    legacy-font garbled as well; the first reason found is the one named."""
    assert verify(rec(SECTORS_STEM, subject="Social Science"),
                  SECTORS_HINDI).reason == "legacy-font"


def test_legacy_font_rejects_garbled_devanagari():
    """The Physics answer the old code map put on Geography 64/4/1 Q24
    (cbse:q:src:c2655c8196cc86e419c8e9de:24) is Devanagari broken by a legacy
    font: vowel signs stacked on one another ("कुोंडली")."""
    v = verify(rec(GEOGRAPHY_STEM, subject="Geography", marks=5), PHYSICS_IN_HINDI)
    assert v.reason == "legacy-font"


def test_legacy_font_rejects_krutidev():
    """cbse:q:src:b34adc36798c7b462d3db1cd:25 with its candidate from
    "32-1-1 H.pdf": Hindi typed in the Krutidev font, which extracts as Latin
    letters. Script-wise it reads as English, so only a legacy-font check sees it."""
    krutidev = ("A. fdUgha rhu dkj.kksa dk o.kZu dhft, tks vlg;ksx vkanksyu ds "
                "(ii) Hkkjr ljdkj vfèkfu;e 1919 (iii) tfy;kaokyk ckx gR;kdkaM "
                "(vi) 1920 ds dkaxzsl ds vf/kos”ku")
    v = verify(rec("Explain the statement in the context of Non-Cooperation Movement.",
                   subject="Social Science"), krutidev)
    assert v.reason == "legacy-font"


def test_document_id_rejects_an_answer_that_is_only_the_scheme_id():
    """cbse:q:src:4f6182240b214906a58eaeab:22 (30/1/1 Q22): the whole answer
    is the marking scheme's page footer."""
    v = verify(rec("Find the zeroes of the polynomial p(x) = x2 + -x -.",
                   subject="Mathematics", marks=2),
               "MS_X_Mathematics_041_30/1/1_2024-25 MS_X_Mathematics_041_30/1/1_2024-25")
    assert v.reason == "document-id"


# cbse:q:src:41439dcef4b5c6d47ef118db:4 (31/4/2 Q4).
TOMATO = "Acid present in tomato is : (a) Methanoic acid (b) Acetic acid (c) Lactic acid (d) Oxalic acid"


def test_option_mismatch_rejects_a_key_naming_no_option():
    """Its candidate from "X_086_31_4-1 to 3_Science_MS.pdf" answers a
    question about villi."""
    villi = ("The inner lining of the small intestine has numerous finger-like "
             "projections called villi, which increases the surface area for absorption")
    v = verify(rec(TOMATO, marks=1), villi)
    assert v.reason == "option-mismatch"


def test_an_mcq_keyed_by_letter_is_accepted():
    assert verify(rec(TOMATO, marks=1), "", option="D").accepted
    assert verify(rec(TOMATO, marks=1), "(d) Oxalic acid").accepted


def test_a_letter_outside_the_options_is_an_option_mismatch():
    stem = "The reducing agent in this reaction is : (a) Na (b) H₂O (c) NaOH"
    assert verify(rec(stem, marks=1), "", option="D").reason == "option-mismatch"


def test_a_letter_key_with_no_readable_options_is_not_trusted():
    """cbse:q:src:a5d35ea98c8f5dd80214b6f2:15 (Chemistry): the key is "D", but
    for this assertion-reason item both statements are true and R explains A.
    With no options in the stem nothing ties a letter to this question, and 2
    of the 3 such keys checked by hand were wrong."""
    stem = ("Assertion (A) : When glucose is added to water, an elevation in boiling "
            "point is observed. Reason (R) : The lowering of vapour pressure causes "
            "elevation in the boiling point.")
    v = verify(rec(stem, subject="Chemistry", marks=1), "", option="D")
    assert v.reason == "unreadable-options"


def test_content_mismatch_rejects_another_questions_answer():
    """cbse:q:src:c6d75fd02ddaf5c1411d9743:17 (57/3/1 Q17) with its candidate
    from "57-3-1.pdf", which answers questions on contraceptives and vaccines."""
    v = verify(rec("(a) Explain the process of the development of a male gametophyte "
                   "in an angiosperm.", subject="Biology"),
               "Progesterone, Progestogen – Estrogen combination ‘Saheli’ is a "
               "non-steroidal preparation, ‘once a week’ pill with very few side effects, "
               "Vaccine is a preparation of antigenic proteins of pathogen")
    assert v.reason == "content-mismatch"


def test_content_mismatch_rejects_an_answer_that_only_repeats_the_question():
    """cbse:q:src:94cb306f384779a2121f9f55:21 (430/5/1 Q21), candidate from
    "430_5_1.pdf": every word of the answer is the question's own."""
    stem = "Find LCM of 576 and 512 by prime factorization."
    v = verify(rec(stem, subject="Mathematics"), "Find LCM of 576 and 512 by prime factorization")
    assert v.reason == "content-mismatch"


def test_a_correct_subjective_answer_is_accepted():
    """The English-medium candidate for 32/5/2 Q29 covers every term of the
    question although most of its own words are new."""
    v = verify(rec(SECTORS_STEM, subject="Social Science"), SECTORS_ENGLISH)
    assert v.accepted, v


def test_a_correct_answer_sharing_too_little_is_still_rejected():
    """The price of the calibration, stated as a test: 57/5/1 Q25's answer
    (cbse:q:src:09a7d8a43ab84dbfb45c1229:25, "57-5-1.pdf") is right, but it
    shares 5 of the stem's 11 content words and 5 of its own 14 -- the same
    shares as another set's case study."""
    stem = ("If the cells in the leaves of a maize plant contain 10 chromosomes each, "
            "write the number of chromosomes in its endosperm and zygote. Name and "
            "explain the process by which an endosperm and a zygote are formed in maize.")
    answer = ("Endosperm – 15 chromosomes Endosperm is formed by the process of triple "
              "fusion, the fusion of two polar nuclei with one male gamete, - Zygote is "
              "formed by the process of syngamy, the fusion of egg cell")
    assert verify(rec(stem, subject="Biology"), answer).reason == "content-mismatch"


def test_maths_is_judged_on_the_stems_numbers_too():
    """cbse:q:src:0b3c7b807dcc7e88fd1809df:28 (430/5/2 Q28), "430_5_2.pdf".
    One content word in common; four of the stem's numbers."""
    stem = ("(a) Sabina went to a bank ATM to withdraw < 2,000. She received < 50 and "
            "< 100 notes only. If Sabina got 25 notes in all, how many notes of < 50 "
            "and < 100 did she receive ?")
    answer = ("Let the number of ₹50 notes be x and the number of ₹100 notes be y ATQ "
              "x + y = 25 _______ (i) and 50x + 100y = 2000 ________ (ii) Solving (i) "
              "and (ii), x= 10, y = 15")
    assert verify(rec(stem, subject="Mathematics"), answer).accepted


def test_another_sets_case_study_is_rejected_by_its_names():
    """cbse:q:src:0633f3094b94306e4131353d:26 (67/4/2 Q26) asks about Bhumi
    and Chavi; its candidate from "XII_055_MS_67_4_2_unsigned.pdf" answers
    for Saket and Suveni, sharing the ledger words."""
    stem = ("(a) Bhumi and Chavi were partners in a firm sharing profits and losses in the "
            "ratio of 5 : 3. They admitted Aditi in the firm on 1st April, 2022. On that date "
            "their Balance Sheet was as follows : Balance Sheet of Bhumi and Chavi as at 1st "
            "April, 2022 Liabilities Amount < Assets Amount < Capitals : Machinery 3,80,000 "
            "Bhumi 3,20,000 Furniture 50,000 Chavi 3,40,000 6,60,000 Debtors 2,30,000 General "
            "Reserve 80,000 Stock 1,50,000 Bank loan 60,000 Cash 50,000 Creditors 60,000 "
            "Prepare Revaluation Account and Partners Capital Accounts.")
    answer = ("Saket and Suveni were partners in a firm By Sundry Liabilities: 1/2 5,76,000 "
              "By Bank/ Cash A/c 1/2 8,00,000 By Suveni’s Capital A/c 1")
    v = verify(rec(stem, subject="Accountancy", marks=2), answer)
    assert v.reason == "content-mismatch"


def test_numbers_alone_do_not_make_an_answer():
    """cbse:q:src:fa1dc4cb28f4b304ea8e618c:34 (30/2/1 Q34), a mean-and-median
    table; its candidate from "X_MS_041_Mathematics Standard_30-2-1_2024-25.pdf"
    is a speed problem that happens to say 10, 20 and 30."""
    stem = ("A student noted the number of cars passing through a spot on a road for 100 "
            "periods each of 3 minutes and summarised it in the table given below. Find the "
            "mean and median of the following data. Number of cars 0 -10 10⁻²⁰ 20 -30 30 -40 "
            "40 -50 50 -60 60 -70 70 -80 Frequency (periods) 8")
    answer = ("Let the speed in upward direction be ‘x’ km/h and the speed in downward "
              "direction = (x + 10) km/h Therefore, speeds in upward and downward direction "
              "are 20 km/h and 30 km/h respectively")
    assert verify(rec(stem, subject="Mathematics", marks=5), answer).reason == "content-mismatch"


def test_an_assertion_reason_key_in_words_is_not_trusted_either():
    """cbse:q:src:7c78ffa137e914e0b76bd4e2:17 (31/3/1 Q17): the served key,
    "(B)/ The reaction of a reactive metal with dilute acid", shares enough
    words with the item to pass the overlap rule. An assertion-reason
    verdict proves nothing about which item it belongs to."""
    stem = ("Assertion (A) : Hydrogen gas is not evolved when a metal reacts with nitric "
            "acid. Reason (R) : Nitric acid is a strong reducing agent and reduces the "
            "hydrogen produced in the reaction to water.")
    v = verify(rec(stem, marks=1), "(B)/ The reaction of a reactive metal with dilute acid")
    assert v.reason == "unreadable-options"


def test_a_hindi_question_accepts_a_devanagari_answer():
    """The served bank holds no readable Hindi stem -- its 13 Hindi records are
    extraction debris -- so this pair is composed: the answer follows the
    Hindi-medium scheme for 57/1/2 Q26 ("57-1-2 hindi.pdf"), spelled
    correctly, and the stem is the question it answers."""
    stem = ("दात्र कोशिका अरक्तता (सिकल सेल एनीमिया) का कारण लिखिए। हीमोग्लोबिन अणु की "
            "बीटा ग्लोबिन शृंखला में क्या परिवर्तन होता है?")
    answer = ("दात्र कोशिका अरक्तता का कारण - हीमोग्लोबिन अणु की बीटा ग्लोबिन शृंखला के "
              "छठे स्थान पर वेलीन द्वारा ग्लूटामिक अम्ल का प्रतिस्थापन।")
    v = verify(rec(stem, subject="Hindi"), answer)
    assert v.accepted, v
    # The same answer on an English question is a medium mismatch.
    assert verify(rec("Explain the cause of sickle-cell anaemia.", subject="Biology"),
                  answer).reason == "script-mismatch"


def test_every_reason_is_named():
    assert set(REASONS) == {"document-id", "legacy-font", "script-mismatch",
                            "unreadable-options", "option-mismatch", "content-mismatch"}


# --------------------------------------------------------------------------- #
# the index keeps every candidate and chooses by medium, not load order
# --------------------------------------------------------------------------- #

# 57/1/1 Q2 in answer_keys.db: the English-medium key ("57-1-1.pdf", which
# the writer filed under subject "English") and the Hindi-medium one, whose
# text answers a different question.
HCG_STEM = ("Which one of the following hormones is secreted by the human placenta that "
            "helps in the maintenance of pregnancy ? (A) Relaxin (B) Human Chorionic "
            "Gonadotropin (C) Oxytocin (D) Human Placental Lactogen -11")
EN_ROW = ("English", "XII", "57/1/1", 2, None, "(B) / Human Chorionic Gonadotropin",
          '[["(B) / Human Chorionic Gonadotropin", 0.0]]', 0.0, "57-1-1.pdf")
HI_ROW = ("Biology", "XII", "57/1/1", 2, None, "(C) / लाल रĉ (रुिधर) कोिशकाएँ",
          '[["(C) / लाल रĉ (रुिधर) कोिशकाएँ", 0.0]]', 0.0, "XII_044_MS_57-1-1 HINDI.pdf")


@pytest.mark.parametrize("rows", [[EN_ROW, HI_ROW], [HI_ROW, EN_ROW]])
def test_every_candidate_is_kept_with_its_medium(tmp_path, rows):
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    cands = idx.candidates("57/1/1", 2)
    assert sorted(c.medium for c in cands) == ["en", "hi"]
    assert {c.source for c in cands} == {EN_ROW[-1], HI_ROW[-1]}


@pytest.mark.parametrize("rows", [[EN_ROW, HI_ROW], [HI_ROW, EN_ROW]])
def test_an_english_stem_gets_the_english_answer_in_either_load_order(tmp_path, rows):
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    best = idx.lookup("57/1/1", 2, rec(HCG_STEM, subject="Biology", marks=1))
    assert best is not None
    assert best.source == EN_ROW[-1]


# 56/4/2 Q3 (cbse:q:src:a5d35ea98c8f5dd80214b6f2:3): two letter keys, both
# among the options, so both pass the verifier -- and they disagree.
# "56_4_2.pdf" names no medium and says A; "043_56_4_2_Hindi.pdf" says B. The
# index used to take A because an unknown medium outranks the other one; the
# same pair answer Q12 A and C. Nothing here says which is right.
KOH_STEM = ("Reaction of 1-phenyl-2-chloropropane with alcoholic KOH gives mainly : "
            "(a) 1-phenylpropene (b) 3-phenylpropene (c) 1-phenylpropan-3-ol "
            "(d) 1-phenylypropan-2-ol")
EN_KEY = ("English", "XII", "56/4/2", 3, "A", "", "[]", 1.0, "56_4_2.pdf")
HI_KEY = ("Chemistry", "XII", "56/4/2", 3, "B", "", "[]", 1.0, "043_56_4_2_Hindi.pdf")
HI_KEY_A = HI_KEY[:4] + ("A",) + HI_KEY[5:]
# Two keys of the SAME rank (neither names a medium) that disagree: rank and
# score tie, so a stable sort would have handed the key to load order.
# (Constructed from the two real rows above; the second filename is invented.)
SET_A = ("Chemistry", "XII", "56/4/2", 3, "A", "", "[]", 1.0, "56_4_2.pdf")
SET_C = ("Chemistry", "XII", "56/4/2", 3, "C", "", "[]", 1.0, "XII_043_56_4_2.pdf")


@pytest.mark.parametrize("rows", [[EN_KEY, HI_KEY], [HI_KEY, EN_KEY],
                                  [SET_A, SET_C], [SET_C, SET_A]])
def test_accepted_keys_that_disagree_are_ambiguous_in_either_load_order(tmp_path, rows):
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    record = rec(KOH_STEM, subject="Chemistry", marks=1)
    assert all(verify_answer(record, c).accepted for c in idx.candidates("56/4/2", 3))
    choice = idx.choose("56/4/2", 3, record)
    assert choice.best is None
    assert [v.reason for _, v in choice.rejected] == ["conflicting-keys"] * 2
    assert idx.lookup("56/4/2", 3, record) is None


@pytest.mark.parametrize("rows", [[EN_KEY, HI_KEY_A], [HI_KEY_A, EN_KEY]])
def test_the_matching_medium_wins_between_two_keys_that_agree(tmp_path, rows):
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    best = idx.lookup("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1))
    assert best.correct_option == "A"
    assert best.source == EN_KEY[-1]       # names no medium: outranks Hindi


def test_a_key_in_words_and_a_key_by_letter_that_agree_are_not_a_conflict(tmp_path):
    words = ("English", "XII", "56/4/2", 3, None, "(a) 1-phenylpropene", "[]", 1.0,
             "56-4-2 English.pdf")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [SET_A, words]))
    best = idx.lookup("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1))
    assert best is not None and best.correct_option == "A"


def test_a_labelled_scheme_built_from_a_conflicting_key_is_quarantined(tmp_path):
    parse = tmp_path / "parse"
    make_parse_tree(parse, "a" * 24, "Series 56/4/2 Chemistry")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [EN_KEY, HI_KEY]))
    served = {"totalMarks": 1, "modelAnswer": "1-phenylpropene",
              "markingPoints": [{"id": "m1", "description": "Correct option A: 1-phenylpropene",
                                 "marks": 1}],
              "metadata": {"objective": True, "correctOption": "A"},
              "provenance": "cbse_marking_scheme"}
    recs = [_board("a" * 24, 3, KOH_STEM, served, subject="Chemistry", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    scheme = recs[0]["answerScheme"]
    assert scheme.get("provenance") != "cbse_marking_scheme"
    assert "correctOption" not in (scheme.get("metadata") or {})
    assert report.quarantined == {"conflicting-keys": 1}
    assert report.rejected == {"conflicting-keys": 2}
    assert report.verified == 0


def test_medium_falls_back_to_the_script_of_the_text(tmp_path):
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [
        ("Physics", "XII", "55/3/1", 5, None, "िनकाय की धाįरता इसकी Ǜािमती पर िनभŊर करती है",
         "[]", 1.0, "XII-2-042-3-1.pdf"),
    ]))
    assert idx.candidates("55/3/1", 5)[0].medium == "hi"


def test_a_geography_code_is_never_answered_from_physics(tmp_path):
    """The removed `_SUBJECT_CODE_MAP` sent 64/* (Geography) to 55/* (Physics)
    and 55/* (Physics) to 301/* (English Core): 7 served Geography records
    carried Physics answers. answer_keys.db files Geography under 64/* itself."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [
        ("Physics", "XII", "55/4/1", 24, None, PHYSICS_IN_HINDI, "[]", 5.0,
         "XII_042_Physics_MS_55_4_1,2,3_hindi_med.pdf"),
    ]))
    assert idx.candidates("64/4/1", 24) == []
    assert idx.lookup("64/4/1", 24, rec(GEOGRAPHY_STEM, subject="Geography")) is None


# --------------------------------------------------------------------------- #
# the relink labels only what it verified, and removes what it rejected
# --------------------------------------------------------------------------- #

def _board(doc_hash: str, q_no: int, stem: str, scheme: dict, *, subject="Geography",
           marks=5) -> dict:
    return {"id": f"cbse:q:src:{doc_hash}:{q_no}", "subject": subject, "marks": marks,
            "stem": stem, "answerScheme": scheme}


def test_an_already_labelled_wrong_scheme_is_unlabelled_and_quarantined(tmp_path):
    parse = tmp_path / "parse"
    make_parse_tree(parse, "c" * 24, "Series 64/4/1 Geography")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    wrong = {"totalMarks": 5, "modelAnswer": PHYSICS_IN_HINDI,
             "markingPoints": [{"id": "m1", "description": PHYSICS_IN_HINDI, "marks": 5}],
             "provenance": "cbse_marking_scheme", "sourcePaperCode": "64/4/1"}
    recs = [_board("c" * 24, 24, GEOGRAPHY_STEM, wrong)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    scheme = recs[0]["answerScheme"]
    assert scheme.get("provenance") != "cbse_marking_scheme"
    assert scheme["markingPoints"] == []
    assert scheme["modelAnswer"] == ""
    assert report.quarantined == {"legacy-font": 1}
    assert report.verified == 0
    [entry] = report.quarantine
    assert entry["id"] == recs[0]["id"]
    assert entry["code"] == "64/4/1" and entry["q_no"] == 24
    assert entry["reason"] == "legacy-font"
    assert entry["text"] == PHYSICS_IN_HINDI[:200]


def test_a_rejected_existing_scheme_is_replaced_by_a_verified_candidate(tmp_path):
    """The served 57/1/1 Q2 record labelled the Hindi-medium key official
    (whichever row loaded last). It is quarantined and the English one attached."""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "d" * 24, "Series 57/1/1 Biology")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [EN_ROW, HI_ROW]))
    hindi = {"totalMarks": 1, "modelAnswer": HI_ROW[5], "provenance": "cbse_marking_scheme",
             "markingPoints": [{"id": "m1", "description": HI_ROW[5], "marks": 1}]}
    recs = [_board("d" * 24, 2, HCG_STEM, hindi, subject="Biology", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    scheme = recs[0]["answerScheme"]
    assert scheme["provenance"] == "cbse_marking_scheme"
    assert scheme["modelAnswer"] == "Human Chorionic Gonadotropin"
    assert scheme["metadata"]["correctOption"] == "B"
    assert scheme["metadata"]["schemeSource"] == EN_ROW[-1]
    assert scheme["metadata"]["schemeMedium"] == "en"
    assert report.quarantined == {"script-mismatch": 1}
    assert report.verified_existing_scheme == 1
    assert report.rejected == {"script-mismatch": 1}      # the Hindi candidate


def test_a_labelled_mcq_key_no_official_row_backs_is_quarantined(tmp_path):
    """cbse:q:src:9081575f9ac53e99a3ff660c:13 is served "Correct option B:
    Crystalline lens" as official; most refraction happens at the cornea (A).
    Standing alone the scheme passes -- `build_official_scheme` wrote option
    B's own text as its model answer, so the key "verifies" against itself.
    With no index row to check it against, the letter goes with the label:
    the scorer reads `correctOption` whatever the label says."""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "e" * 24, "Series 99/9/9 Science")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    stem = ("In the human eye, most of the refraction for the light rays entering the eye "
            "occurs at the surface of : (A) Cornea (B) Crystalline lens (C) Pupil "
            "(D) Aqueous humor")
    scheme = {"totalMarks": 1, "modelAnswer": "Crystalline lens",
              "markingPoints": [{"id": "m1", "description": "Correct option B: Crystalline lens",
                                 "marks": 1}],
              "metadata": {"objective": True, "correctOption": "B"},
              "provenance": "cbse_marking_scheme"}
    recs = [_board("e" * 24, 13, stem, scheme, subject="Science", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    served = recs[0]["answerScheme"]
    assert served.get("provenance") != "cbse_marking_scheme"
    assert "correctOption" not in (served.get("metadata") or {})
    assert not (served.get("metadata") or {}).get("objective")
    assert served["modelAnswer"] == "" and served["markingPoints"] == []
    assert report.quarantined == {"unbacked-key": 1}
    [entry] = report.quarantine
    assert entry["reason"] == "unbacked-key" and entry["text"] == "Crystalline lens"
    assert report.verified == 0 and report.existing_scheme_unverifiable == 0


def test_a_labelled_subjective_scheme_no_official_row_backs_is_quarantined(tmp_path):
    """Its content was built from an answer_keys row too, and no row backs it
    now: the verifier can say the text is on this question's topic, not that
    it is the board's answer. It goes to review rather than staying unlabelled."""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "f" * 24, "Series 32/5/2 Social Science")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    scheme = {"totalMarks": 3, "modelAnswer": SECTORS_ENGLISH,
              "markingPoints": [{"id": "m1", "description": SECTORS_ENGLISH, "marks": 3}],
              "provenance": "cbse_marking_scheme"}
    recs = [_board("f" * 24, 29, SECTORS_STEM, scheme, subject="Social Science", marks=3)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert recs[0]["answerScheme"]["markingPoints"] == []
    assert report.quarantined == {"unbacked-key": 1}


def test_an_unlabelled_mcq_key_no_official_row_backs_loses_its_letter(tmp_path):
    """Unlabelled, the same self-referential key is still read by the scorer.
    Its letter can be checked against nothing, so it is removed too."""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "e" * 24, "Series 99/9/9 Science")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    scheme = {"totalMarks": 1, "modelAnswer": "Oxalic acid",
              "markingPoints": [{"id": "m1", "description": "Correct option D: Oxalic acid",
                                 "marks": 1}],
              "metadata": {"objective": True, "correctOption": "D"}, "provenance": "none"}
    recs = [_board("e" * 24, 4, TOMATO, scheme, subject="Science", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert "correctOption" not in (recs[0]["answerScheme"].get("metadata") or {})
    assert report.quarantined == {"unbacked-key": 1}


def test_a_carried_scheme_is_verified_too(tmp_path):
    """CBE/SQP records keep their builder's scheme only if it passes."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    carried = {"id": "sqp:q:x", "subject": "Mathematics", "marks": 2,
               "stem": "Find the zeroes of the polynomial p(x) = x2 - 3x.",
               "answerScheme": {"provenance": "cbse_marking_scheme",
                                "modelAnswer": "MS_X_Mathematics_041_30/1/1_2024-25",
                                "markingPoints": [{"description": "MS_X_Mathematics_041_30/1/1_2024-25"}]}}
    report = relink_answer_schemes([carried], idx, parse_dir=tmp_path)
    assert report.carried_official == 0
    assert report.quarantined == {"document-id": 1}
    assert carried["answerScheme"].get("provenance") != "cbse_marking_scheme"


def test_verify_answer_reads_the_candidates_letter_and_points():
    ans = OfficialAnswer(q_no=4, correct_option="D", answer_text="")
    assert verify_answer(rec(TOMATO, marks=1), ans).accepted
    ans = OfficialAnswer(q_no=4, correct_option=None, answer_text="",
                         value_points=[("(d) Oxalic acid", 1.0)])
    assert verify_answer(rec(TOMATO, marks=1), ans).accepted


# --------------------------------------------------------------------------- #
# the quarantine file keeps what every run removed
# --------------------------------------------------------------------------- #

def _load_enrich_script():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "enrich_question_bank", ROOT / "scripts" / "enrich_question_bank.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_second_run_does_not_lose_the_first_runs_quarantine(tmp_path):
    """After the first run the served bank holds the stripped schemes, so a
    rerun finds almost nothing to quarantine (measured on the real bank:
    2,685, then 1). Overwriting the file on the second run lost the 2,685."""
    script = _load_enrich_script()
    data = tmp_path / "data"
    parse = data / "parse"
    make_parse_tree(parse, "c" * 24, "Series 64/4/1 Geography")
    make_answer_keys(data / "answer_keys.db", [])
    wrong = {"totalMarks": 5, "modelAnswer": PHYSICS_IN_HINDI,
             "markingPoints": [{"id": "m1", "description": PHYSICS_IN_HINDI, "marks": 5}],
             "provenance": "cbse_marking_scheme"}
    bank = data / "syllabus" / "questions.json"
    mirror = tmp_path / "frontend" / "questions.json"
    bank.parent.mkdir(parents=True)
    bank.write_text(json.dumps({"questions": [
        _board("c" * 24, 24, GEOGRAPHY_STEM, wrong)]}), encoding="utf-8")
    quarantine = data / "syllabus" / "scheme_quarantine.json"

    for _ in range(2):
        assert script.run(targets=[bank, mirror], quarantine=quarantine,
                          data_root=data, check=False) == 0

    saved = json.loads(quarantine.read_text(encoding="utf-8"))
    assert [e["id"] for e in saved["entries"]] == ["cbse:q:src:" + "c" * 24 + ":24"]
    assert saved["entries"][0]["reason"] == "legacy-font"
    assert saved["counts"] == {"legacy-font": 1}
    served = json.loads(bank.read_text(encoding="utf-8"))["questions"][0]
    assert served["answerScheme"]["markingPoints"] == []


def test_the_quarantine_merge_adds_and_never_drops(tmp_path):
    script = _load_enrich_script()
    path = tmp_path / "q.json"
    first = [{"id": "a", "code": "1/1/1", "q_no": 1, "reason": "legacy-font", "text": "x"}]
    second = [{"id": "b", "code": "1/1/1", "q_no": 2, "reason": "unbacked-key", "text": "y"},
              dict(first[0])]
    script.write_quarantine(path, first)
    saved = script.write_quarantine(path, second)
    assert [e["id"] for e in saved["entries"]] == ["a", "b"]
    assert saved["counts"] == {"legacy-font": 1, "unbacked-key": 1}


# --------------------------------------------------------------------------- #
# calibration
# --------------------------------------------------------------------------- #

def _fixture_verdicts():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    out = []
    for p in fx["pairs"]:
        ans = OfficialAnswer(q_no=p["qNo"], correct_option=None, answer_text=p["answerText"],
                             value_points=[tuple(v) for v in p["valuePoints"]])
        record = {"stem": p["stem"], "subject": p["subject"], "marks": p["marks"]}
        out.append((p, verify_answer(record, ans)))
    return fx, out


def test_the_fixture_is_seeded_and_says_whose_judgements_they_are():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fx["seed"] == 20260922
    assert "AI reviewer" in fx["about"] and "NOT a teacher" in fx["about"]
    assert len(fx["pairs"]) >= 60
    assert {p["judgement"] for p in fx["pairs"]} == {"correct", "wrong", "cannot-tell"}


def test_the_calibrated_rule_accepts_no_pair_judged_wrong():
    _, verdicts = _fixture_verdicts()
    accepted_wrong = [p["id"] for p, v in verdicts if p["judgement"] == "wrong" and v.accepted]
    assert accepted_wrong == []


def test_the_calibrated_rule_keeps_what_it_can():
    """Pinned so a change to the rule shows its cost: of the 32 pairs judged
    correct, 17 are accepted. The 15 lost are short answers, assertion-reason
    verdicts (which no overlap can tell apart) and correct answers that share
    too few words with a long stem."""
    _, verdicts = _fixture_verdicts()
    correct = [(p, v) for p, v in verdicts if p["judgement"] == "correct"]
    assert len(correct) == 32
    assert sum(v.accepted for _, v in correct) == 17
