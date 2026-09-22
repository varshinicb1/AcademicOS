"""academicos.syllabus.tagger: chapter -> topic -> subtopic tags on questions,
with a confidence, and a review queue for everything below the threshold.

The unit tests use real questions, copied field-for-field from the banks and
cited by id, so a change to the tagger is judged on what the banks hold. The
gold test runs the committed tagger over ``taxonomy/_tag_gold.json`` (labels
by an AI reviewer, not a teacher -- the fixture says so) and holds it to the
rule the tagger exists for: an accepted tag is right at least 90% of the time.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.syllabus.tagger import (  # noqa: E402
    TAG_FIELDS, TopicTagger, apply_tags,
)

TAXONOMY = ROOT / "academicos-data" / "syllabus" / "taxonomy"
EXEMPLAR = ROOT / "academicos-data" / "corpus" / "ncert-exemplar" / "questions.json"
CBE = ROOT / "academicos-data" / "corpus" / "cbse-cbe" / "questions.json"
BOARD = ROOT / "academicos-data" / "syllabus" / "questions.json"


def _q(qid, subject, grade, stem, options=(), answer="", exemplar_chapter=None, **extra):
    """A question record shaped like the banks' (only the fields the tagger reads
    plus a few it must leave alone)."""
    rec = {
        "id": qid, "subject": subject, "grade": grade, "chapterIds": [], "type": "mcq",
        "stem": stem, "marks": 1, "tags": [],
        "parts": [{"id": f"{qid}:p1", "text": "", "options": list(options),
                   "expectedAnswer": answer}] if options else [],
        "answerScheme": {"modelAnswer": answer},
        "metadata": {},
    }
    if exemplar_chapter:
        rec["metadata"]["exemplarChapter"] = {"number": 0, "title": exemplar_chapter,
                                              "exercise": None}
    rec.update(extra)
    return rec


# exemplar:q:10:mathematics:5:5.1:16
AP_SUM = _q("exemplar:q:10:mathematics:5:5.1:16", "Mathematics", 10,
            "The sum of first 16 terms of the AP: 10, 6, 2,... is",
            ["–320", "320", "–352", "–400"], "(A) –320", "Arithmetic Progressions")
# exemplar:q:7:science:2:-:18
NUTRITION = _q("exemplar:q:7:science:2:-:18", "Science", 7,
               "Following statements describe the five steps in animal nutrition. Read each "
               "statement and give one word for each statement. Write the terms that describes "
               "each process. (a) Transportation of absorbed food to different parts of body and "
               "their utilisation. (b) Breaking of complex food substances into simpler and "
               "soluble substances. (c) Removal of undigested and unabsorbed solid residues of "
               "food from the body. (d) Taking food into the body. (e) Transport of digested and "
               "soluble food from the intestine to blood vessels.",
               answer="(a) Assimilation (b) Digestion (c) Egestion (d) Ingestion (e) Absorption",
               exemplar_chapter="Nutrition in Animals")
# cbse:q:src:9ea9344987df8c25364b39a1:30 (board paper, academicos-data/syllabus/questions.json)
CONSERVATISM = _q("cbse:q:src:9ea9344987df8c25364b39a1:30", "Social Science", 10,
                  "(a) European Governments were driven by a spirit of conservatism in 1815. "
                  "Support this statement.")
# exemplar:q:6:mathematics:8:-:25 -- ratio is taught in no chapter of Ganita Prakash 6
RATIO_CLASS6 = _q("exemplar:q:6:mathematics:8:-:25", "Mathematics", 6,
                  "State whether the given statements are true (T) or false (F): The ratio of "
                  "10kg to 100kg is 1:10", answer="True", exemplar_chapter="Ratio and Proportion")


@pytest.fixture(scope="module")
def tagger():
    return TopicTagger()


@pytest.fixture(scope="module")
def exemplar_bank():
    return json.loads(EXEMPLAR.read_text(encoding="utf-8"))["questions"]


def test_maths_question_tags_chapter_and_topic(tagger, exemplar_bank):
    # Tagged with the rest of its Exemplar chapter, as a bank is: the pooled
    # chapter is the prior, and alone the question is only its own pool.
    chapter = [q for q in exemplar_bank if q["grade"] == 10 and q["subject"] == "Mathematics"
               and q["metadata"]["exemplarChapter"]["title"] == "Arithmetic Progressions"]
    tags = dict(zip([q["id"] for q in chapter], tagger.tag_records(chapter)))
    tag = tags[AP_SUM["id"]]
    assert tag.chapter_id == "mathematics-10/arithmetic-progressions"
    assert tag.topic_id == "mathematics-10/arithmetic-progressions/sum-of-first-n-terms-of-an-ap"
    assert tag.accepted["chapter"] and tag.accepted["topic"]
    assert 0.0 <= tag.confidence["topic"] <= tag.confidence["chapter"] <= 1.0
    [alone] = tagger.tag_records([AP_SUM])
    assert alone.topic_id == tag.topic_id
    assert alone.confidence["chapter"] < tag.confidence["chapter"]


def test_science_question_tags_chapter_topic_and_subtopic(tagger):
    [tag] = tagger.tag_records([NUTRITION])
    assert tag.chapter_id == "science-7/life-processes-in-animals"
    assert tag.topic_id == "science-7/life-processes-in-animals/nutrition-in-animals"
    assert tag.subtopic_ids[:1] == [
        "science-7/life-processes-in-animals/nutrition-in-animals/digestion-in-human-beings"]


def test_social_science_question_tags_chapter_and_topic(tagger):
    [tag] = tagger.tag_records([CONSERVATISM])
    assert tag.chapter_id == "social-science-10/the-rise-of-nationalism-in-europe"
    assert tag.topic_id == ("social-science-10/the-rise-of-nationalism-in-europe/"
                            "the-making-of-nationalism-in-europe")


# Board-paper records (academicos-data/syllabus/questions.json) whose stem
# alone leans to the wrong chapter, and whose existing chapterIds is right.
# cbse:q:src:9ea9344987df8c25364b39a1:31 -- "national economy" pulls it to
# Lifelines of National Economy without the prior.
INDUSTRIES = _q("cbse:q:src:9ea9344987df8c25364b39a1:31", "Social Science", 10,
                "(a) How are industries contributing to the national economy ? Explain.",
                chapterIds=["manufacturing-industries"], source="cbse_board_paper")
# cbse:q:src:e6935f18e16e69433650b0a3:27 -- "political participation" pulls it
# to Political Parties without the prior.
WOMEN = _q("cbse:q:src:e6935f18e16e69433650b0a3:27", "Social Science", 10,
           "Suggest any three ways to enhance political participation of women in India. 3 1=3",
           chapterIds=["gender-religion-caste"], source="cbse_board_paper")


@pytest.mark.parametrize("rec,chapter", [
    (INDUSTRIES, "social-science-10/manufacturing-industries"),
    (WOMEN, "social-science-10/gender-religion-and-caste"),
])
def test_existing_chapter_ids_are_a_prior(tagger, rec, chapter):
    [with_prior] = tagger.tag_records([rec])
    assert with_prior.features["chapter"]["hasPrior"]
    assert with_prior.features["chapter"]["idPrior"]
    assert with_prior.chapter_id == chapter
    [without] = tagger.tag_records([dict(rec, chapterIds=[])])
    assert not without.features["chapter"]["hasPrior"]
    assert without.chapter_id != chapter          # the prior is what moved it


def test_chapter_ids_pool_the_bank_like_exemplar_chapters(tagger):
    """A chapter id that names no chapter by its words (a CBE learning-outcome
    code) is still a prior: the records sharing it are pooled and matched."""
    a = _q("t:1", "Science", 10, "Balance the chemical equation Fe + H2O -> Fe3O4 + H2.",
           chapterIds=["10.1.22"])
    b = _q("t:2", "Science", 10, "What is a displacement reaction? Give an example.",
           chapterIds=["10.1.22"])
    tags = tagger.tag_records([a, b])
    assert all(t.features["chapter"]["hasPrior"] for t in tags)
    # a code seen on one record only, with no name, is no prior: the pool would
    # be the question itself
    [lone] = tagger.tag_records([dict(a, chapterIds=["10.9.4"])])
    assert not lone.features["chapter"]["hasPrior"]


def test_exemplar_chapter_wins_over_chapter_ids(tagger):
    rec = dict(NUTRITION, chapterIds=["electricity"])
    [tag] = tagger.tag_records([rec])
    assert tag.features["chapter"]["hasPrior"] and not tag.features["chapter"]["idPrior"]
    assert tag.chapter_id == "science-7/life-processes-in-animals"


def test_every_tag_names_its_evidence(tagger):
    [tag] = tagger.tag_records([AP_SUM])
    assert tag.evidence["chapter"]            # the shared terms that decided it
    assert tag.evidence["topic"]


def test_question_outside_the_trees_is_not_tagged(tagger):
    english = _q("cbe:q:English9JV41a", "English", 9, "Which of these statements is true "
                 "about the pollination of almond trees?")
    class11 = _q("x", "Mathematics", 11, "Find the derivative of x squared.")
    assert tagger.tag_records([english, class11]) == [None, None]


def test_a_question_whose_class_has_no_such_chapter_goes_to_review(tagger):
    """Ratio is not taught in Ganita Prakash 6: the tagger's best chapter for it
    is a guess, and a guess must not reach the question."""
    records, review = apply_tags([RATIO_CLASS6], tagger, bank="exemplar")
    assert records[0]["topicIds"] == [] and records[0]["subtopicIds"] == []
    assert records[0]["taxonomyChapterId"] is None
    assert [r["id"] for r in review] == [RATIO_CLASS6["id"]]
    assert review[0]["level"] == "chapter"


def test_threshold_decides_between_tag_and_review_queue():
    strict = TopicTagger(thresholds={"chapter": 1.01, "topic": 1.01, "subtopic": 1.01})
    lax = TopicTagger(thresholds={"chapter": 0.0, "topic": 0.0, "subtopic": 0.0})
    tagged, review = apply_tags([AP_SUM], strict, bank="exemplar")
    assert tagged[0]["topicIds"] == [] and len(review) == 1
    assert review[0]["proposed"]["topicId"].endswith("sum-of-first-n-terms-of-an-ap")
    tagged, review = apply_tags([AP_SUM], lax, bank="exemplar")
    assert tagged[0]["topicIds"] == [
        "mathematics-10/arithmetic-progressions/sum-of-first-n-terms-of-an-ap"]
    assert tagged[0]["taxonomyChapterId"] == "mathematics-10/arithmetic-progressions"
    assert review == []          # this topic has no subtopics: nothing left to review


def test_apply_is_additive(tagger):
    before = copy.deepcopy([AP_SUM, NUTRITION, RATIO_CLASS6])
    after, _ = apply_tags(before, tagger, bank="exemplar")
    assert before == [AP_SUM, NUTRITION, RATIO_CLASS6]          # input untouched
    for old, new in zip(before, after):
        assert set(new) - set(old) == set(TAG_FIELDS)
        assert {k: v for k, v in new.items() if k not in TAG_FIELDS} == old
        assert new["tagMethod"] and set(new["tagConfidence"]) == {"chapter", "topic", "subtopic"}


def test_apply_leaves_out_of_scope_records_alone(tagger):
    english = _q("cbe:q:English9JV41a", "English", 9, "Which statement is true?")
    after, review = apply_tags([english], tagger, bank="cbe")
    assert after == [english] and review == []


def test_script_writes_only_tag_fields_and_the_review_queue(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "tag_question_bank", ROOT / "scripts" / "tag_question_bank.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bank = tmp_path / "bank.json"
    payload = {"questions": [AP_SUM, RATIO_CLASS6], "notice": "kept"}
    bank.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    queue = tmp_path / "review_queue.json"
    assert mod.main(["--topics", str(bank), "--check", "--review-queue", str(queue)]) == 0
    assert json.loads(bank.read_text(encoding="utf-8")) == payload      # --check wrote nothing
    assert not queue.exists()
    assert mod.main(["--topics", str(bank), "--review-queue", str(queue)]) == 0
    out = json.loads(bank.read_text(encoding="utf-8"))
    assert out["notice"] == "kept"
    for old, new in zip(payload["questions"], out["questions"]):
        assert {k: v for k, v in new.items() if k not in TAG_FIELDS} == old
    q = json.loads(queue.read_text(encoding="utf-8"))
    queued = {e["id"]: e for e in q["items"]}
    assert RATIO_CLASS6["id"] in queued
    field = {"chapter": "taxonomyChapterId", "topic": "topicIds", "subtopic": "subtopicIds"}
    for rec in out["questions"]:
        if rec["id"] in queued:           # what was queued is not on the question
            assert not rec[field[queued[rec["id"]]["level"]]]
    # a second run replaces this bank's entries instead of stacking them
    assert mod.main(["--topics", str(bank), "--review-queue", str(queue)]) == 0
    assert len(json.loads(queue.read_text(encoding="utf-8"))["items"]) == len(queued)


def _gold_records():
    gold = json.loads((TAXONOMY / "_tag_gold.json").read_text(encoding="utf-8"))
    banks = {"exemplar": EXEMPLAR, "cbe": CBE, "board": BOARD}
    wanted = {it["id"] for it in gold["items"]}
    by_bank = {}
    for name, path in banks.items():
        by_bank[name] = json.loads(path.read_text(encoding="utf-8"))["questions"]
    return gold, by_bank, wanted


def test_gold_set_is_large_enough_and_spans_the_classes_and_subjects():
    gold = json.loads((TAXONOMY / "_tag_gold.json").read_text(encoding="utf-8"))
    items = gold["items"]
    assert len(items) >= 150
    assert "not by a teacher" in gold["notice"].lower()
    assert {it["grade"] for it in items} == {6, 7, 8, 9, 10}
    assert {it["subject"] for it in items} == {"Mathematics", "Science", "Social Science"}


def test_accepted_tags_on_the_gold_set_are_at_least_90_percent_right(tagger):
    from academicos.syllabus.tagger import score_against_gold
    gold, by_bank, _ = _gold_records()
    report = score_against_gold(tagger, gold["items"], by_bank)
    model = json.loads((TAXONOMY / "_tagger_model.json").read_text(encoding="utf-8"))
    for level in ("chapter", "topic"):
        acc = report["accepted"][level]
        assert acc["tags"] >= 10, (level, acc)             # not vacuous
        assert acc["precision"] >= 0.90, (level, acc)
    # Subtopics: no threshold reaches 90% on 10+ gold tags (measured: a picked
    # subtopic is right 55 times in 82 when its topic is right), so the model
    # accepts none and every subtopic goes to review. If a later model does
    # accept subtopics, they are held to the same bar.
    acc = report["accepted"]["subtopic"]
    if acc["tags"]:
        assert acc["tags"] >= 10 and acc["precision"] >= 0.90, acc
    else:
        assert model["thresholds"]["subtopic"] > 1.0
    # the committed model reports the same numbers the test measures
    assert model["gold"]["inSample"]["accepted"] == report["accepted"]


def test_question_schema_carries_the_tags_as_optional_fields():
    from academicos.assessment.schemas import QuestionSchema
    ex = json.loads(EXEMPLAR.read_text(encoding="utf-8"))["questions"][0]
    untagged = {k: v for k, v in ex.items() if k not in TAG_FIELDS}
    q = QuestionSchema.model_validate(untagged)
    assert q.topic_ids == [] and q.subtopic_ids == [] and q.taxonomy_chapter_id is None
    tagged = dict(untagged, taxonomyChapterId="mathematics-6/number-play",
                  topicIds=["mathematics-6/number-play/simple-estimation"], subtopicIds=[],
                  tagConfidence={"chapter": 0.93, "topic": 0.8, "subtopic": None},
                  tagMethod="tfidf_textbook_v1")
    q = QuestionSchema.model_validate(tagged)
    assert q.topic_ids == ["mathematics-6/number-play/simple-estimation"]
    assert q.tag_confidence["chapter"] == 0.93 and q.tag_method == "tfidf_textbook_v1"
    dumped = q.model_dump(by_alias=True)
    assert dumped["topicIds"] == tagged["topicIds"] and dumped["subtopicIds"] == []
