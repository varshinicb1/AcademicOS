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
import re
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


def test_an_mcq_keyed_by_letter_and_its_options_words_is_accepted():
    assert verify(rec(TOMATO, marks=1), "(d) Oxalic acid", option="D").accepted
    assert verify(rec(TOMATO, marks=1), "Oxalic acid 1 mark", option="D").accepted
    assert verify(rec(TOMATO, marks=1), "(d) Oxalic acid").option == "D"


# cbse:q:src:0b3c7b807dcc7e88fd1809df:17 (430/5/2 Q17): "430_5_2.pdf" keys it
# B, a bare letter. The sum is 100 x 101 = 10100, option A.
EVENS = ("The sum of the first 100 even natural numbers is : (a) 10100 (b) 2550 "
         "(c) 5050 (d) 10010")
# cbse:q:src:6df8d2b3a2f6c8cce1428573:1 (55/1/1 Q1): the Hindi-medium scheme
# keys it A, a bare letter. The field at the centre of a charged ring is zero.
RING = ("A thin plastic rod is bent into a circular ring of radius R. It is uniformly "
        "charged with charge density . The magnitude of the electric field at its centre "
        "is : (A) R 2 0 (B) Zero (C) 0R (D) R 4")


@pytest.mark.parametrize("stem, subject, letter", [(EVENS, "Mathematics", "B"),
                                                   (RING, "Physics", "A")])
def test_a_bare_letter_key_is_not_trusted(stem, subject, letter):
    """A letter is always "among the options", so on its own it says nothing
    about which question its row answers. Of the 24 bare-letter keys the
    verifier accepted at 960455e, 12 were judged wrong and 8 correct (fixture
    stratum objective-accepted) -- 430/5/2 Q17 and 55/1/1 Q1 among the wrong."""
    record = rec(stem, subject=subject, marks=1)
    assert verify(record, "", option=letter).reason == "unverifiable-letter"
    assert verify(record, f"({letter.lower()})", option=letter).reason == "unverifiable-letter"
    assert verify(record, f"({letter})").reason == "unverifiable-letter"


def test_a_numeric_option_can_be_named_in_words():
    """The page-footer cut used to strip "2550" to nothing, so no key could
    name a numeric option -- and a served scheme "2550" for option B could
    not even be traced back to its (bare-letter) row."""
    record = rec(EVENS, subject="Mathematics", marks=1)
    assert verify(record, "10100", option="A").option == "A"
    assert verify(record, "10100").option == "A"
    assert verify(record, "2550", option="A").reason == "option-mismatch"


def test_options_that_extracted_as_dashes_name_nothing():
    """cbse:q:src:88532141f34ac8143c0d1b45:6 (30/3/2 Q6): the options are
    extraction debris, and the key "– 3x2 – x – 6" from
    "MS_X_041_Mathematics_30-3-2_2025-26 (1).pdf" is another question's
    polynomial that merely opens with a dash."""
    stem = "p(y) = 7y2 -y (A) -, -(B) -, (C) -, -(D) -,"
    v = verify(rec(stem, subject="Mathematics", marks=1), "– 3x2 – x – 6", option="D")
    assert v.reason == "option-mismatch"


def test_a_bare_letter_from_the_items_own_builder_is_kept():
    """A CBE/SQP scheme was attached from its own item (judge_content=False):
    there is no row to misalign, so its letter stands."""
    record = rec(EVENS, subject="Mathematics", marks=1)
    assert verify(record, "", option="A", judge_content=False).accepted


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
                            "unreadable-options", "unverifiable-letter", "option-mismatch",
                            "content-mismatch"}


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


# 56/4/2 Q3 (cbse:q:src:a5d35ea98c8f5dd80214b6f2:3): "56_4_2.pdf" names no
# medium and keys it A; "043_56_4_2_Hindi.pdf" keys it B. Both real rows are
# bare letters (BARE_A, BARE_B), which the verifier no longer accepts, so the
# keys below add the option's words to each: two accepted keys that disagree.
# (Constructed from the real rows.) The index used to take A because an
# unknown medium outranks the other one. Nothing here says which is right.
KOH_STEM = ("Reaction of 1-phenyl-2-chloropropane with alcoholic KOH gives mainly : "
            "(a) 1-phenylpropene (b) 3-phenylpropene (c) 1-phenylpropan-3-ol "
            "(d) 1-phenylypropan-2-ol")
EN_KEY = ("English", "XII", "56/4/2", 3, "A", "1-phenylpropene", "[]", 1.0, "56_4_2.pdf")
HI_KEY = ("Chemistry", "XII", "56/4/2", 3, "B", "3-phenylpropene", "[]", 1.0,
          "043_56_4_2_Hindi.pdf")
HI_KEY_A = HI_KEY[:4] + ("A", "1-phenylpropene") + HI_KEY[6:]
# Two keys of the SAME rank (neither names a medium) that disagree: rank and
# score tie, so a stable sort would have handed the key to load order.
# (The second filename is invented.)
SET_A = ("Chemistry", "XII", "56/4/2", 3, "A", "1-phenylpropene", "[]", 1.0, "56_4_2.pdf")
SET_C = ("Chemistry", "XII", "56/4/2", 3, "C", "1-phenylpropan-3-ol", "[]", 1.0,
         "XII_043_56_4_2.pdf")
# The real bare-letter rows.
BARE_A = ("English", "XII", "56/4/2", 3, "A", "", "[]", 1.0, "56_4_2.pdf")
BARE_B = ("Chemistry", "XII", "56/4/2", 3, "B", "", "[]", 1.0, "043_56_4_2_Hindi.pdf")


@pytest.mark.parametrize("rows", [[SET_A, SET_C], [SET_C, SET_A]])
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


@pytest.mark.parametrize("rows", [[BARE_A, BARE_B], [BARE_B, BARE_A], [BARE_A]])
def test_bare_letter_rows_answer_nothing(tmp_path, rows):
    """The real 56/4/2 Q3 rows: two bare letters. Neither is labelled."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    choice = idx.choose("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1))
    assert choice.best is None
    assert {v.reason for _, v in choice.rejected} == {"unverifiable-letter"}


def test_a_bare_letter_row_does_not_outvote_a_key_in_words(tmp_path):
    """A bare letter that disagrees with a key naming its option in words is
    not a conflict: the letter is not evidence, the words are."""
    words = ("English", "XII", "56/4/2", 3, None, "(a) 1-phenylpropene", "[]", 1.0,
             "56-4-2 English.pdf")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [BARE_B, words]))
    choice = idx.choose("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1))
    assert choice.best is not None and choice.best.correct_option == "A"
    assert [v.reason for _, v in choice.rejected] == ["unverifiable-letter"]


def test_a_labelled_scheme_built_from_a_bare_letter_is_quarantined(tmp_path):
    """cbse:q:src:0b3c7b807dcc7e88fd1809df:17 (430/5/2 Q17) served "Correct
    option B: 2550" as official, from the bare letter in "430_5_2.pdf". Standing
    alone the scheme names its option -- `build_official_scheme` wrote the
    option's text as the model answer -- but its row is a bare letter."""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "b" * 24, "Series 430/5/2 Mathematics")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [
        ("Mathematics", "X", "430/5/2", 17, "B", "", "[]", 1.0, "430_5_2.pdf")]))
    served = {"totalMarks": 1, "modelAnswer": "2550",
              "markingPoints": [{"id": "m1", "description": "Correct option B: 2550", "marks": 1}],
              "metadata": {"objective": True, "correctOption": "B"},
              "provenance": "cbse_marking_scheme"}
    recs = [_board("b" * 24, 17, EVENS, served, subject="Mathematics", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    scheme = recs[0]["answerScheme"]
    assert scheme.get("provenance") != "cbse_marking_scheme"
    assert "correctOption" not in (scheme.get("metadata") or {})
    assert report.quarantined == {"unverifiable-letter": 1}
    assert report.verified == 0


def test_a_labelled_scheme_built_from_a_conflicting_key_is_quarantined(tmp_path):
    parse = tmp_path / "parse"
    make_parse_tree(parse, "a" * 24, "Series 56/4/2 Chemistry")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [SET_A, SET_C]))
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
    assert entry["text"] == PHYSICS_IN_HINDI


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
    # Replaced, not verified: the scheme the record had is the one removed.
    assert report.replaced_after_quarantine == 1
    assert report.verified_existing_scheme == 0
    assert report.verified == 1
    assert report.rejected == {"script-mismatch": 1}      # the Hindi candidate
    assert any("replaced" in line and line.rstrip().endswith(": 1")
               for line in report.lines())


def test_the_relink_counts_of_records_that_had_a_scheme_add_up(tmp_path):
    """Every board record that had a scheme ends in exactly one bucket:
    verified as it was, replaced after quarantine, or removed with nothing in
    its place. (Kept-unlabelled is gone: an unverified scheme is not served.)"""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "d" * 24, "Series 57/1/1 Biology")
    make_parse_tree(parse, "c" * 24, "Series 64/4/1 Geography")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [EN_ROW, HI_ROW]))
    hindi = {"totalMarks": 1, "modelAnswer": HI_ROW[5], "provenance": "cbse_marking_scheme",
             "markingPoints": [{"id": "m1", "description": HI_ROW[5], "marks": 1}]}
    english = {"totalMarks": 1, "modelAnswer": "Human Chorionic Gonadotropin",
               "markingPoints": [{"id": "m1", "description": "Human Chorionic Gonadotropin",
                                  "marks": 1}]}
    wrong = {"totalMarks": 5, "modelAnswer": PHYSICS_IN_HINDI,
             "markingPoints": [{"id": "m1", "description": PHYSICS_IN_HINDI, "marks": 5}],
             "provenance": "cbse_marking_scheme"}
    recs = [_board("d" * 24, 2, HCG_STEM, hindi, subject="Biology", marks=1),
            _board("d" * 24, 2, HCG_STEM, english, subject="Biology", marks=1),
            _board("c" * 24, 24, GEOGRAPHY_STEM, wrong)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    assert report.already_had_scheme == 3
    assert report.replaced_after_quarantine == 1
    assert report.verified_existing_scheme == 1
    assert report.existing_scheme_removed == 1
    assert report.already_had_scheme == (
        report.verified_existing_scheme + report.replaced_after_quarantine
        + report.existing_scheme_removed)
    assert sum(report.quarantined.values()) == 2


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
    assert report.verified == 0 and report.with_scheme == 0


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
    ans = OfficialAnswer(q_no=4, correct_option="D", answer_text="Oxalic acid")
    assert verify_answer(rec(TOMATO, marks=1), ans).accepted
    ans = OfficialAnswer(q_no=4, correct_option="D", answer_text="")
    assert verify_answer(rec(TOMATO, marks=1), ans).reason == "unverifiable-letter"
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
    """The verifier alone on the question-number strata. The join strata
    (join-*) calibrate `join_verdict`; see test_the_combined_fixture_is_precise."""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    out = []
    for p in fx["pairs"]:
        if p["stratum"].startswith("join-"):
            continue
        ans = OfficialAnswer(q_no=p["qNo"], correct_option=p.get("correctOption"),
                             answer_text=p["answerText"],
                             value_points=[tuple(v) for v in p["valuePoints"]])
        record = {"stem": p["stem"], "subject": p["subject"], "marks": p["marks"]}
        if "type" in p:
            record["type"] = p["type"]
        out.append((p, verify_answer(record, ans)))
    return fx, out


def _objective(verdicts):
    return [(p, v) for p, v in verdicts if p["stratum"].startswith("objective")]


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
    correct = [(p, v) for p, v in verdicts
               if p["judgement"] == "correct" and not p["stratum"].startswith("objective")]
    assert len(correct) == 32
    assert sum(v.accepted for _, v in correct) == 17


def test_the_objective_strata_are_judged_and_seeded():
    fx, verdicts = _fixture_verdicts()
    objective = _objective(verdicts)
    assert {p["stratum"] for p, _ in objective} == {"objective-accepted", "objective-random"}
    assert len(objective) == 75
    assert "20260922" in fx["strata"]["objective-random"]
    assert all(p["options"] for p, _ in objective)


def test_no_objective_pair_judged_wrong_is_accepted():
    """The census of every objective key the verifier accepted at 960455e:
    12 of its 24 bare letters were judged wrong (430/5/2 Q17, 30/2/3 Q8,
    430/5/3 Q2 and Q12, 30/5/1 Q18, 430/2/1 Q16, 56/1/3 Q2, 56/4/3 Q3,
    55/1/1 Q1, ...). None may be accepted."""
    _, verdicts = _fixture_verdicts()
    wrong = [(p, v) for p, v in _objective(verdicts) if p["judgement"] == "wrong"]
    assert len(wrong) == 29
    assert [p["id"] for p, v in wrong if v.accepted] == []


def test_an_objective_key_is_accepted_only_on_its_options_words():
    """Pinned so a change to `_option_verdict` or `_named_options` shows up:
    every objective pair accepted resolves to an option and carries words
    beyond its letter, and of the 32 judged correct 24 are accepted -- the 8
    lost are bare letters."""
    _, verdicts = _fixture_verdicts()
    objective = _objective(verdicts)
    for p, v in objective:
        if v.accepted:
            assert v.option, p["id"]
            assert re.search(r"\w", _unlabelled(p)), p["id"]
    correct = [(p, v) for p, v in objective if p["judgement"] == "correct"]
    assert len(correct) == 32
    assert sum(v.accepted for _, v in correct) == 24
    assert [v.reason for _, v in correct if not v.accepted] == ["unverifiable-letter"] * 8


def _unlabelled(p) -> str:
    """The key's text with its option label and mark note cut."""
    text = " ".join([p["answerText"]] + [v[0] for v in p["valuePoints"]]).strip()
    text = re.sub(r"^(?:ans\.?\s*)?\(?\s*[A-Da-d]\s*\)?\s*[/.):\-]*", "", text, flags=re.I)
    return re.sub(r"(?:\s*(?:\d+|½)\s*marks?\b)+\s*$", "", text, flags=re.I)


# --------------------------------------------------------------------------- #
# the content join (Task 151): the answer is found by content across every
# set of the paper series, not by question number
# --------------------------------------------------------------------------- #

from academicos.corpus import bank_merge  # noqa: E402
from academicos.corpus.scheme_verify import (  # noqa: E402
    JOIN_MARGIN,
    join_verdict,
    outright_option,
    question_options,
    row_text,
)

# cbse:q:src:80a49b071cb04186873bccda:17 is 30/5/2 Q17. Its own row in
# "X_MS_041_Mathematics Standard_30-5-2_2024-25.pdf" keys A, "17 cm" --
# another question's answer. Set 1 prints the question as Q11, and
# "X_MS_041_Mathematics Standard_30-5-1_2024-25.pdf" keys it D, "30°".
POLE_STEM = ("The ratio of the length of a pole and its shadow on the ground is 1 : 3 . "
             "The angle of elevation of the Sun is : (A) 90° (B) 60° (C) 45° (D) 30°")
POLE_OWN = ("Mathematics", "X", "30/5/2", 17, "A", "17 cm", "[]", 1.0,
            "X_MS_041_Mathematics Standard_30-5-2_2024-25.pdf")
POLE_SET1 = ("Mathematics", "X", "30/5/1", 11, "D", "30°", "[]", 1.0,
             "X_MS_041_Mathematics Standard_30-5-1_2024-25.pdf")
# Two more real rows of the series that mention angles and name no option.
COS_60 = ("Mathematics", "X", "30/5/1", 12, "B", "cos 60°", "[]", 1.0,
          "X_MS_041_Mathematics Standard_30-5-1_2024-25.pdf")
TAN_60 = ("Mathematics", "X", "30/5/2", 12, "B", "– tan 60°", "[]", 1.0,
          "X_MS_041_Mathematics Standard_30-5-2_2024-25.pdf")


def test_a_set_two_question_is_answered_from_set_one_numbering(tmp_path):
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db",
                                          [POLE_OWN, POLE_SET1, COS_60, TAN_60]))
    record = rec(POLE_STEM, subject="Mathematics", marks=1)
    choice = idx.choose("30/5/2", 17, record)

    assert choice.best is not None
    assert (choice.best.code, choice.best.q_no) == ("30/5/1", 11)
    assert choice.best.source == POLE_SET1[-1]
    assert choice.best.correct_option == "D"
    # The own-number row answers another question; it is never attached.
    assert [(a.answer_text, v.reason) for a, v in choice.rejected] == [
        ("17 cm", "option-mismatch")]


def test_the_relink_attaches_the_recovered_key_and_counts_it(tmp_path):
    parse = tmp_path / "parse"
    make_parse_tree(parse, "8" * 24, "Series 30/5/2 Mathematics")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db",
                                          [POLE_OWN, POLE_SET1, COS_60, TAN_60]))
    recs = [_board("8" * 24, 17, POLE_STEM, {}, subject="Mathematics", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    scheme = recs[0]["answerScheme"]
    assert scheme["provenance"] == "cbse_marking_scheme"
    assert scheme["metadata"]["correctOption"] == "D"
    assert scheme["metadata"]["schemeCode"] == "30/5/1"
    assert scheme["metadata"]["schemeQNo"] == 11
    assert report.newly_attached == 1 and report.recovered_elsewhere == 1


@pytest.mark.parametrize("rows", [[EN_KEY, HI_KEY], [HI_KEY, EN_KEY]])
def test_an_english_question_never_takes_a_hindi_medium_answer(tmp_path, rows):
    """56/4/2 Q3: the Hindi-medium key ("043_56_4_2_Hindi.pdf") is not in an
    English stem's pool at all, so it neither answers nor conflicts."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    best = idx.lookup("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1))
    assert best is not None and best.source == EN_KEY[-1]
    assert best.correct_option == "A"


def test_a_hindi_medium_key_alone_answers_nothing_in_english(tmp_path):
    """Even one whose words are an option: HI_KEY_A names 1-phenylpropene."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [HI_KEY_A]))
    assert idx.lookup("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1)) is None


# Constructed: two answers to 32/5/2 Q29 (SECTORS_STEM) that restate it alike
# and then say different things, each with five words of its own -- the
# runner-up scores exactly what the best does.
TIE_A = ("Primary, secondary and tertiary sectors are dependent: agriculture supplies "
         "cotton, jute, sugarcane, timber, minerals")
TIE_B = ("Primary, secondary and tertiary sectors are dependent: railways carry "
         "fertiliser, tractors, pumps, seeds, credit")


def test_a_near_tie_between_two_candidates_is_refused(tmp_path):
    rows = [("Social Science", "X", "32/5/2", 29, None, TIE_A, "[]", 3.0, "32_5_2 E.pdf"),
            ("Social Science", "X", "32/5/2", 29, None, TIE_B, "[]", 3.0, "32-5-2 E v2.pdf")]
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", rows))
    record = rec(SECTORS_STEM, subject="Social Science")
    assert all(verify(record, r[5]).accepted for r in rows)
    choice = idx.choose("32/5/2", 29, record)
    assert choice.best is None
    assert choice.ratio == pytest.approx(1.0)
    assert choice.rejected[0][1].reason == "near-tie"


def test_the_margin_is_what_decides_a_close_pair():
    record = rec(SECTORS_STEM, subject="Social Science")
    assert join_verdict(record, SECTORS_ENGLISH, ratio=0.0, anchored=True).accepted
    edge = 1.0 - JOIN_MARGIN
    assert join_verdict(record, SECTORS_ENGLISH, ratio=edge - 0.01, anchored=True).accepted
    assert join_verdict(record, SECTORS_ENGLISH, ratio=edge + 0.01,
                        anchored=True).reason == "near-tie"


TERTIARY = ("(a) Describe the importance of tertiary sector in the economy The activities of "
            "tertiary sector help in the development of the primary and secondary sectors "
            "Tertiary activities do not produce goods but they are")     # "32-5-1-E.pdf" Q38


def test_an_unanchored_subjective_pick_must_restate_the_question():
    """A topical answer from another number of the series is not evidence
    unless it restates the question: 32/5/1 Q38's tertiary-sector answer
    shares enough words with 32/5/2 Q29 to pass the verifier."""
    record = rec(SECTORS_STEM, subject="Social Science")
    assert verify(record, TERTIARY).accepted
    assert join_verdict(record, TERTIARY, ratio=0.0, anchored=False).reason == "unanchored"
    assert join_verdict(record, TERTIARY, ratio=0.0, anchored=True).accepted


def test_a_restated_question_from_another_set_is_recovered(tmp_path):
    """32/5/1 Q27 ("Analyse any three challenges ...") is answered by
    "32_5_2 E.pdf" under set 2's Q33, which restates it and then answers.
    The Hindi-medium row under that number is not in the pool."""
    stem = "Analyse any three challenges faced by political parties in India."
    parties = ("(a) Explain any five challenges faced by political parties in India (i) Lack "
               "of internal democracy within parties (ii) Parties do not keep membership "
               "registers , do not hold organizational meeting and do not conduct internal "
               "election regularly")
    credit = ("(a) How does credit play a positive and negative role? Explain with examples "
              "It plays two roles-positive and negative (i) A large number of transactions "
              "in day to day activities involve credit")
    hindi = ("1 सत्ता की साझेर्दारी राििीनतक खस्थरता को कैसे िावा (i) सत्ता की साझेदारी के "
             "माध्यम से िोग सीधे राजनीनतक प्रणािी में भाग िेते हैं।")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [
        ("Science", "X", "32/5/2", 33, None, parties, "[]", 0.0, "32_5_2 E.pdf"),
        ("Science", "X", "32/5/2", 30, None, credit, "[]", 0.0, "32_5_2 E.pdf"),
        ("Social Science", "X", "32/5/2", 33, None, hindi, "[]", 0.0, "32-5-2 H.pdf"),
    ]))
    record = rec(stem, subject="Social Science")
    choice = idx.choose("32/5/1", 27, record)
    assert choice.best is not None and (choice.best.code, choice.best.q_no) == ("32/5/2", 33)
    assert choice.best.source == "32_5_2 E.pdf"
    assert choice.anchored is False


def test_a_pick_at_a_sibling_questions_number_is_anchored(tmp_path):
    """The same question served from another set: a pick at ITS number is
    the answer the question-number join gives it, found again by content."""
    record = rec(SECTORS_STEM, subject="Social Science")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [
        ("Social Science", "X", "32/5/1", 38, None, TERTIARY, "[]", 5.0, "32-5-1-E.pdf")]))
    assert idx.choose("32/5/2", 29, record).rejected[0][1].reason == "unanchored"
    choice = idx.choose("32/5/2", 29, record, siblings=[("32/5/1", 38)])
    assert choice.best is not None and choice.anchored


# cbse:q:src:13313fa90a8d349b3d8f7299:2 (61/3/2 Q2, the Visually Impaired
# alternative). Krishnadeva Raya was of the Tuluva dynasty (b).
KRISHNADEVA = ("Identify the given image of a temple from the following options : Note : "
               "The following question is for the Visually Impaired Candidates, only in "
               "lieu of Q. No. 2 : Krishnadeva Raya belonged to which of the following "
               "dynasties of Vijayanagara Empire ? (a) Sangama (b) Tuluva (c) Saluva "
               "(d) Aravidu")
# "set 61_3_2 new 2026.pdf" Q54: a sentence from another answer that opens
# with option (a)'s word.
SANGAMA = ("English", "XII", "61/3/2", 54, None,
           "Sangama dynasty, the first dynasty, exercised control till 1485",
           '[["Sangama dynasty, the first dynasty, exercised control till 1485", 0.0]]',
           0.0, "set 61_3_2 new 2026.pdf")


def test_an_objective_key_is_accepted_only_when_its_words_are_the_option(tmp_path):
    record = rec(KRISHNADEVA, subject="History", marks=1)
    # The verifier alone takes it: its words open with option (a).
    assert verify(record, SANGAMA[5]).accepted
    assert outright_option(SANGAMA[5], question_options(record)) is None
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [SANGAMA]))
    choice = idx.choose("61/3/2", 2, record)
    assert choice.best is None
    assert choice.rejected[0][1].reason == "not-an-option"
    # The option's own words, label and mark note aside, are the key.
    assert outright_option("(b) / Tuluva 1 mark", question_options(record)) == "B"


def test_a_bare_letter_is_no_key_to_the_join_either(tmp_path):
    """The real 56/4/2 Q3 rows are bare letters; the join ranks nothing."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [BARE_A, BARE_B]))
    choice = idx.choose("56/4/2", 3, rec(KOH_STEM, subject="Chemistry", marks=1))
    assert choice.best is None and choice.ratio is None


# "66_1_3..pdf" Q6 keys the Mehta Sons question and runs on into the next one
# (the row, shortened).
MEHTA_ROW = ("English", "XII", "66/1/3", 6, "C",
             "Sales promotion 1 mark 7 Q. Beenu had a bookstore in Sabad called 'Book-mark' "
             "For years, the bookstore was doing reasonably well but with the rise of digital "
             "books and online retailers, her sales had declined. Beenu's daughter decided "
             "to launch a marketing campaign to revive the bookstore. The tool of "
             "communication used by Beenu's daughter to revive the bookstore was "
             "(A) Advertising 6 (B) Personal selling (C) Sales promotion (D) Public relations",
             "[]", 1.0, "66_1_3..pdf")
BEENU_STEM = ("Beenu had a bookstore in Sabad called ‘Book-mark’. For years, the bookstore "
              "was doing reasonably well but with the rise of digital books and online "
              "retailers, her sales had declined. Beenu’s daughter, who had just completed "
              "her MBA with a specialisation in marketing decided to launch a marketing "
              "campaign to revive the bookstore. The tool of communication used by Beenu’s "
              "daughter to revive the bookstore was : (A) Advertising (B) Personal selling "
              "(C) Sales promotion (D) Public relations 11-")


def test_a_row_is_not_ranked_by_the_next_question_it_ran_on_into(tmp_path):
    """cbse:q:src:3901e48d946b1f956b5a21c7:19 (66/1/1 Q19, Beenu) is keyed
    "Public relations" in every set (66_1_1..pdf Q19, 66_1_3..pdf Q7). Set 3's
    Q6 row keys Mehta Sons "Sales promotion" and then prints Beenu's question
    in full, so ranked on its whole text it beat the right keys by far and
    Beenu took "Sales promotion". Read up to its mark note, it scores as a
    key naming another option does, and the two are too close to call."""
    assert row_text(MEHTA_ROW[5]) == "Sales promotion"
    own = ("Business Studies", "XII", "66/1/1", 19, "D",
           "Public relations 1 mark 20 Q. 'Best Electronics' is led by its visionary "
           "Chief Executive Officer, Nikhil.", "[]", 1.0, "66_1_1..pdf")
    set3 = ("Business Studies", "XII", "66/1/3", 7, "D",
            "Public relations 1 mark 8 Q. The marketing management philosophy which uses "
            "availability and affordability as a means to achieve the objectives is",
            "[]", 1.0, "66_1_3..pdf")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [MEHTA_ROW, own, set3]))
    choice = idx.choose("66/1/1", 19, rec(BEENU_STEM, subject="Business Studies", marks=1))
    assert choice.best is None or choice.best.correct_option == "D"
    assert "C" not in {a.correct_option for a, v in choice.rejected if v.accepted}


# cbse:q:src:4f6182240b214906a58eaeab:3 is 30/1/1 Q3. Its scheme file
# "MS_X_041_Mathematics_30-1-1_2025-26 (1).pdf" numbers as the paper does:
# Q3 keys B "6" (words that are no option of this stem, so the row is not
# eligible) and Q8 keys A "x-axis" -- Q8's answer, whose words happen to be
# option (A) here. The mid-point (0, 5.5) lies on the y-axis.
MIDPOINT_STEM = ("The mid-point of the line segment joining the points P( -4, 5) and Q(4, 6) "
                 "lies on : (A) x-axis (B) y-axis (C) origin (D) neither x-axis nor y-axis")
MIDPOINT_SCHEME = "MS_X_041_Mathematics_30-1-1_2025-26 (1).pdf"
MIDPOINT_Q3 = ("Mathematics", "X", "30/1/1", 3, "B", "6", "[]", 1.0, MIDPOINT_SCHEME)
MIDPOINT_Q8 = ("Mathematics", "X", "30/1/1", 8, "A", "𝑥-axis", "[]", 1.0, MIDPOINT_SCHEME)


def test_a_key_at_another_number_of_the_questions_own_paper_is_refused(tmp_path):
    """One set's scheme numbers as that set's paper does, so a row under the
    question's own code at another number answers another question on the
    same paper. The census accepted 30/1/1 Q8's "x-axis" for Q3 (judged
    wrong); the pick is now refused as other-number."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [MIDPOINT_Q3, MIDPOINT_Q8]))
    record = rec(MIDPOINT_STEM, subject="Mathematics", marks=1)
    choice = idx.choose("30/1/1", 3, record)

    assert choice.best is None
    assert choice.pick is not None and (choice.pick.code, choice.pick.q_no) == ("30/1/1", 8)
    assert choice.anchored is False
    assert choice.rejected[0][1].reason == "other-number"
    # The same key served from another set's numbering is still a recovery.
    assert join_verdict(record, "𝑥-axis", ratio=0.0, anchored=False).accepted
    assert join_verdict(record, "𝑥-axis", ratio=0.0, anchored=False,
                        other_number=True).reason == "other-number"


def test_an_other_number_key_the_questions_own_row_repeats_is_kept(tmp_path):
    """cbse:q:src:3901e48d946b1f956b5a21c7:10 (66/1/1 Q10). "66_1_1..pdf"
    keys Q3 and Q10 alike, "Both the Statements are true", and the join
    picks Q3's (load order): the question's own row names the same letter,
    so the pick is anchored and kept."""
    stem = ("Statement I : A financial market facilitates the transfer of savings from "
            "savers to investors. Statement II : It gives savers the choice of different "
            "investments and helps to channelise surplus funds into the most productive use. "
            "Choose the correct option from the following : (A) Statement I is true and "
            "Statement II is false. (B) Statement II is true and Statement I is false. "
            "(C) Both the Statements are true. (D) Both the Statements are false.")
    q3 = ("English", "XII", "66/1/1", 3, "C",
          "Both the Statements are true 1 mark 4 Q. _------------ refers to doing the task "
          "correctly and with minimum cost (A) Effectiveness (B) Coordination (C) Process "
          "(D) Efficiency", "[]", 1.0, "66_1_1..pdf")
    q10 = ("English", "XII", "66/1/1", 10, "C",
           "Both the Statements are true 1 mark 11 Q. Choose the incorrect statement from "
           "the following about functions of a Stock Exchange (A) Provides liquidity and "
           "marketability to new securities (B) Ensures safety of transactions (C) Contributes "
           "to economic growth (D) Provides scope for speculation", "[]", 1.0, "66_1_1..pdf")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [q3, q10]))
    choice = idx.choose("66/1/1", 10, rec(stem, subject="Business Studies", marks=1))
    assert choice.best is not None and choice.anchored
    assert (choice.best.code, choice.best.q_no) == ("66/1/1", 3)
    assert choice.best.correct_option == "C"


def test_an_edition_of_the_own_row_does_not_anchor_another_number(tmp_path):
    """cbse:q:src:c2655c8196cc86e419c8e9de:29 (64/4/1 Q29, world-map
    features). "XII_029_MS_64-4-1  ENG UNSIGNED.pdf" prints one Visually
    Impaired alternative under Q22 and Q29 (0.94 of their terms in common);
    the join picked Q22's and called it anchored because it is an edition of
    the own row. Its (29.3) answers a question this set does not ask (judged
    wrong). At another number of the question's own paper, only the row
    itself at an anchor would anchor it."""
    stem = ("On the given political outline map of the World (on page 21), seven "
            "geographical features have been marked as A, B, C, D, E, F and G. Identify "
            "any five with the help of the following information and write their correct "
            "names on the lines drawn near them : 5 1=5 A. An international airport in "
            "South America B. A canal linking Atlantic Ocean with Pacific Ocean C. A major "
            "seaport in Australia D. A terminal station of Trans-Siberian Railway E. A major "
            "area of commercial livestock rearing F. An area of extensive commercial grain "
            "farming G. A major seaport in Asia Note : The following questions are for "
            "Visually Impaired Candidates only in lieu of Q. No. 29. Answer any five "
            "questions out of the following : 5 1=5 (29.1) Name any one international "
            "airport of Argentina. (29.2) Which canal links Atlantic Ocean with Pacific "
            "Ocean ? (29.3) Name any one major seaport of Australia. (29.4) Which is the "
            "terminal station on the eastern end of Trans-Siberian Railway ? (29.5) Mention "
            "the major area of commercial livestock rearing in Argentina. (29.6) Name any "
            "one area of extensive commercial grain farming. (29.7) Name any one major "
            "seaport located in Pakistan.")
    note = "Note: For Visually Impaired Candidates only in lieu of Q.No. 29"
    arabia = "(29.3) Arabian Peninsula/ Mongolia / Central China / Tundra region of"
    usa = "(29.4) United States of America (U.S.A)"
    tail = "Note : For Visually Impaired Candidates only in lieu of Q. No 30"
    scheme = "XII_029_MS_64-4-1  ENG UNSIGNED.pdf"
    q22 = ("Geography", "XII", "64/4/1", 22, None, f"{note} {arabia} {usa}",
           json.dumps([[note, 0.0], [arabia, 0.0], [usa, 0.0]]), 0.0, scheme)
    q29 = ("Geography", "XII", "64/4/1", 29, None, f"{note} {arabia} {usa} {tail}",
           json.dumps([[note, 0.0], [arabia, 0.0], [usa, 0.0], [tail, 0.0]]), 0.0, scheme)
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [q22, q29]))
    choice = idx.choose("64/4/1", 29, rec(stem, subject="Geography", marks=3))
    assert choice.best is None
    assert choice.pick is not None and (choice.pick.code, choice.pick.q_no) == ("64/4/1", 22)
    assert choice.anchored is False
    assert choice.rejected[0][1].reason == "other-number"


def test_english_core_rows_are_filed_under_their_real_paper(tmp_path):
    """The writer filed "XII_301_1_1_3_MS_unsigned (1).pdf" under 301/1/1
    (subject code 301 read as the series) and "XII_301_English Core_MS_Set
    6-3.pdf" under 301/1/6. They are papers 1/1/3 and 1/6/3."""
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", [
        ("English", "XII", "301/1/1", 4, None, "Notice: audition for the play", "[]", 5.0,
         "XII_301_1_1_3_MS_unsigned (1).pdf"),
        ("English", "XII", "301/1/6", 7, None, "The poet recalls her mother", "[]", 3.0,
         "XII_301_English Core_MS_Set 6-3.pdf"),
        ("English", "XII", "301/1/2", 9, None, "No set in this name", "[]", 3.0,
         "XII_301_English Core_MS.pdf"),
    ]))
    assert [a.source for a in idx.candidates("1/1/3", 4)] == [
        "XII_301_1_1_3_MS_unsigned (1).pdf"]
    assert [a.source for a in idx.candidates("1/6/3", 7)] == [
        "XII_301_English Core_MS_Set 6-3.pdf"]
    assert idx.candidates("301/1/1", 4) == [] and idx.candidates("301/1/6", 7) == []
    assert "301/1/2" not in idx.codes          # no set to read: not guessed
    assert {"1/1", "1/6"} <= idx.families


def test_a_quarantine_entry_keeps_the_whole_scheme(tmp_path):
    """A person must be able to review a removed scheme and restore it: every
    marking point, the model answer, the option letter and the scheme file.
    The entry used to keep 200 characters."""
    parse = tmp_path / "parse"
    make_parse_tree(parse, "9" * 24, "Series 99/9/9 Science")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db", []))
    long_point = "Crystalline lens " + "focuses light on the retina " * 12
    scheme = {"totalMarks": 1, "modelAnswer": "Crystalline lens",
              "markingPoints": [{"id": "m1", "description": "Correct option B: Crystalline lens",
                                 "marks": 1},
                                {"id": "m2", "description": long_point, "marks": 0}],
              "metadata": {"objective": True, "correctOption": "B",
                           "schemeSource": "X_086_31_4_MS.pdf"},
              "provenance": "cbse_marking_scheme"}
    stem = ("In the human eye, most of the refraction for the light rays entering the eye "
            "occurs at the surface of : (A) Cornea (B) Crystalline lens (C) Pupil "
            "(D) Aqueous humor")
    recs = [_board("9" * 24, 13, stem, json.loads(json.dumps(scheme)),
                   subject="Science", marks=1)]
    report = relink_answer_schemes(recs, idx, parse_dir=parse)

    [entry] = report.quarantine
    assert entry["reason"] == "unbacked-key"
    assert entry["code"] == "99/9/9" and entry["q_no"] == 13
    assert entry["correctOption"] == "B"
    assert entry["schemeSource"] == "X_086_31_4_MS.pdf"
    assert entry["scheme"] == scheme
    assert len(entry["scheme"]["markingPoints"][1]["description"]) > 200


def test_the_merge_serves_no_board_record_without_a_verified_key():
    """Rule Q1 for board records (user decision 2026-09-22): a board record
    whose scheme the relink did not verify is excluded as no-verified-key,
    recorded like every other exclusion."""
    sys.path.insert(0, str(ROOT / "tests"))
    from test_bank_merge import board
    verified = board(1)
    unlabelled = board(2)
    unlabelled["answerScheme"] = dict(unlabelled["answerScheme"], provenance="none")
    emptied = board(3)
    emptied["answerScheme"] = dict(emptied["answerScheme"], markingPoints=[], modelAnswer="")
    result = bank_merge.compose([verified, unlabelled, emptied], [], [])

    assert [q["id"] for q in result.questions] == [verified["id"]]
    assert [(e["id"], e["reason"]) for e in result.excluded] == [
        (unlabelled["id"], "no-verified-key"), (emptied["id"], "no-verified-key")]
    assert result.counts["board"] == 1


def test_a_label_the_relink_did_not_stamp_is_no_verified_key():
    """The served bank still carries 2,930 cbse_marking_scheme labels from
    before Task 15, and hand audits found about 30% of them detectably wrong.
    Only the relink's `build_official_scheme` stamps the row it verified
    (metadata.schemeCode, metadata.schemeQNo), so a label without the stamp
    fails closed, whether or not the merge ran after a relink."""
    sys.path.insert(0, str(ROOT / "tests"))
    from test_bank_merge import board
    stamped = board(1)
    stale = board(2)
    stale["answerScheme"] = dict(stale["answerScheme"], metadata={})
    half = board(3)
    half["answerScheme"] = dict(half["answerScheme"], metadata={"schemeCode": "31/1/1"})
    assert bank_merge.has_verified_key(stamped)
    result = bank_merge.compose([stamped, stale, half], [], [])
    assert [q["id"] for q in result.questions] == [stamped["id"]]
    assert [(e["id"], e["reason"]) for e in result.excluded] == [
        (stale["id"], "no-verified-key"), (half["id"], "no-verified-key")]


def test_the_relinks_scheme_carries_the_stamp_the_merge_reads(tmp_path):
    parse = tmp_path / "parse"
    make_parse_tree(parse, "8" * 24, "Series 30/5/2 Mathematics")
    idx = AnswerKeyIndex(make_answer_keys(tmp_path / "ak.db",
                                          [POLE_OWN, POLE_SET1, COS_60, TAN_60]))
    sys.path.insert(0, str(ROOT / "tests"))
    from test_bank_merge import board
    rec_ = board(17, id="cbse:q:src:" + "8" * 24 + ":17", subject="Mathematics",
                 stem=POLE_STEM, marks=1, answerScheme={})
    relink_answer_schemes([rec_], idx, parse_dir=parse)
    assert bank_merge.has_verified_key(rec_)


def test_an_enrich_run_relinks_the_withheld_board_records_too(tmp_path):
    """A board record the merge withheld lives only in board_withheld.json.
    The relink reads it there, so a later, better join can re-attach its key,
    and writes it back there whole; it never enters the served files."""
    script = _load_enrich_script()
    data = tmp_path / "data"
    parse = data / "parse"
    make_parse_tree(parse, "8" * 24, "Series 30/5/2 Mathematics")
    make_answer_keys(data / "answer_keys.db", [POLE_OWN, POLE_SET1, COS_60, TAN_60])
    bank = data / "syllabus" / "questions.json"
    mirror = tmp_path / "frontend" / "questions.json"
    bank.parent.mkdir(parents=True)
    bank.write_text(json.dumps({"questions": []}), encoding="utf-8")
    held = bank.with_name("board_withheld.json")
    pole = _board("8" * 24, 17, POLE_STEM, {}, subject="Mathematics", marks=1)
    pole["source"] = "cbse_board_paper"
    held.write_text(json.dumps({"questions": [pole]}), encoding="utf-8")

    assert script.run(targets=[bank, mirror], quarantine=bank.with_name("q.json"),
                      data_root=data, check=False) == 0

    assert json.loads(bank.read_text(encoding="utf-8"))["questions"] == []
    [back] = json.loads(held.read_text(encoding="utf-8"))["questions"]
    assert back["id"] == pole["id"]
    assert bank_merge.has_verified_key(back)
    assert back["answerScheme"]["metadata"]["correctOption"] == "D"


# --------------------------------------------------------------------------- #
# the census through the real index
# --------------------------------------------------------------------------- #

DATA = ROOT / "academicos-data"
SERVED = DATA / "syllabus" / "questions.json"


@pytest.mark.skipif(not (DATA / "answer_keys.db").exists() or not SERVED.exists()
                    or not (DATA / "parse").exists(),
                    reason="needs academicos-data: answer_keys.db, the served bank, parse trees")
def test_the_census_picks_are_what_choose_picks_today():
    """The pinned precision below runs `join_verdict` on pool features frozen
    in the fixture; this re-runs the join itself -- ranking, eligibility,
    edition and sibling anchoring, the objective tie rule, the ratio -- over
    the real bank, through `relink_answer_schemes` (and so `_siblings`), and
    holds every census pair to its frozen pick, anchored flag and ratio. A
    regression in `AnswerKeyIndex.choose` moves one of them."""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    census = {p["id"]: p for p in fx["pairs"] if p["stratum"] == "join-accepted"}
    assert len(census) == 89

    records = [r for r in json.loads(SERVED.read_text(encoding="utf-8"))["questions"]
               if r.get("source") == "cbse_board_paper"]
    held = SERVED.with_name("board_withheld.json")
    if held.exists():
        ids = {r.get("id") for r in records}
        records += [r for r in json.loads(held.read_text(encoding="utf-8"))["questions"]
                    if r.get("id") not in ids]
    assert census.keys() <= {r.get("id") for r in records}

    index = AnswerKeyIndex(DATA / "answer_keys.db")
    seen: dict[str, object] = {}
    real_choose = index.choose

    def recording(code, q_no, record, *, siblings=()):
        choice = real_choose(code, q_no, record, siblings=siblings)
        if record.get("id") in census:
            seen[record["id"]] = choice
        return choice

    index.choose = recording
    relink_answer_schemes(records, index, parse_dir=DATA / "parse")

    assert seen.keys() == census.keys()
    drift = []
    for rid, p in census.items():
        c = seen[rid]
        got = ((c.pick.code, c.pick.q_no) if c.pick else None, c.anchored,
               round(c.ratio or 0.0, 4), c.best is not None)
        want = ((p["paperCode"], p["qNo"]), p["joinAnchored"],
                round(p["joinRatio"] or 0.0, 4), _join_accepted(p))
        if got != want:
            drift.append((rid, got, want))
    assert drift == []


# --------------------------------------------------------------------------- #
# calibration of the join: the combined fixture
# --------------------------------------------------------------------------- #

def _join_accepted(p) -> bool:
    """What the join does with a fixture pair: accepted only when the pair's
    row is the join's pick for its question and `join_verdict` takes it with
    the stored pool features."""
    if not p["joinPicked"]:
        return False
    ans = OfficialAnswer(q_no=p["qNo"], correct_option=p.get("correctOption"),
                         answer_text=p["answerText"],
                         value_points=[tuple(v) for v in p["valuePoints"]])
    record = {"stem": p["stem"], "subject": p["subject"], "marks": p["marks"]}
    if "type" in p:
        record["type"] = p["type"]
    # A census pair names the question's own (code, q_no) apart from the
    # picked row's; the older strata are pairs at the question's own number.
    other_number = ("questionCode" in p and p["paperCode"] == p["questionCode"]
                    and p["qNo"] != p["questionQNo"])
    return join_verdict(record, row_text(ans.text()), ratio=p["joinRatio"],
                        anchored=p["joinAnchored"], other_number=other_number).accepted


def test_the_join_strata_are_seeded_and_judged():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    join = [p for p in fx["pairs"] if p["stratum"].startswith("join-")]
    assert {p["stratum"] for p in join} == {"join-accepted", "join-random"}
    assert len(join) >= 80
    assert "20260922" in fx["strata"]["join-random"]
    assert all("joinPicked" in p for p in fx["pairs"])
    assert "AI reviewer" in fx["about"] and "NOT a teacher" in fx["about"]


def test_the_combined_fixture_is_precise():
    """Every judged pair, old strata and join strata alike, through the join.

    Precision is judged-correct over judged-correct plus judged-wrong among
    the accepted; cannot-tell pairs are counted apart, not as correct. Pinned
    so a change to the join shows its cost: 116 correct, 1 wrong, 9
    cannot-tell -- precision 0.991, or 0.921 if every cannot-tell were wrong.
    The 1 wrong: 67/4/1 Q26 (Yash Ltd.'s shares) took the debenture answer
    both sets print under Q26, its OR part -- at the question's own number,
    which no rule here can tell from a right key. The other-number rule
    refused 30/1/1 Q3 (Q8's "x-axis"), 64/4/1 Q29 (Q22's Visually Impaired
    alternative), both judged wrong, and 430/3/3 Q7 (Q9's "6.4 cm" for a
    stem that fuses Q7 to Q9, cannot-tell); it was 116, 3 and 10 before.
    Recall: 116 of the fixture's 153 pairs judged correct (0.758); the strata
    over-sample what the rules accept, so that is not the bank's recall."""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    accepted = [p for p in fx["pairs"] if _join_accepted(p)]
    judged = {j: sum(p["judgement"] == j for p in accepted)
              for j in ("correct", "wrong", "cannot-tell")}
    precision = judged["correct"] / (judged["correct"] + judged["wrong"])
    assert precision >= 0.95
    assert judged == {"correct": 116, "wrong": 1, "cannot-tell": 9}
    assert sum(p["judgement"] == "correct" for p in fx["pairs"]) == 153
