"""Tests for the topic mapper and, more importantly, for its refusals.

`test_science10_like_reference_is_refused` is the one that matters. The mapper
was calibrated on the real CBE reference and returned precision of 3% for
Science class 10 -- chance. A mapper that answered anyway would have filed
~400 questions under wrong topics and every topic-wise report from then on
would have been quietly wrong. The gate exists to stop that, so it is tested
against the shape that actually caused the failure: many fine-grained topics
with only a couple of examples each.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from academicos.assessment.topic_mapper import TopicMapper, tokenize  # noqa: E402


# --- tokenising -----------------------------------------------------------

def test_stopwords_and_short_words_are_dropped():
    got = tokenize("What is the value of the following in a triangle?")
    assert "the" not in got
    assert "what" not in got
    assert "following" not in got        # a stopword
    assert "value" in got
    assert "triangle" in got
    # `question`, `marks` and `answer` are boilerplate in this corpus and are
    # deliberately stopped, since every item has them.
    assert "question" not in tokenize("Answer this question for marks")


def test_tokenizer_keeps_letters_only():
    """Digits are dropped, so a test vocabulary must be alphabetic.

    This is asserted rather than assumed because synthetic fixtures built from
    `w0`, `t1x5` silently vanish through this filter, and a fixture that
    tokenises to nothing makes a refusal test pass for the wrong reason.
    """
    assert tokenize("triangle") == ["triangle"]
    assert tokenize("w0") == []
    assert tokenize("t1x5") == []


def test_tokenize_handles_empty_and_none():
    assert tokenize("") == []
    assert tokenize(None) == []


# --- fitting and predicting ----------------------------------------------

def test_a_clearly_separable_corpus_is_classified():
    """Two topics with distinct vocabulary must be separable."""
    examples = [
        ("photosynthesis chlorophyll stomata glucose plants leaves", "BIO"),
        ("photosynthesis leaves stomata chlorophyll oxygen plants", "BIO"),
        ("photosynthesis green leaves chlorophyll glucose stomata", "BIO"),
        ("refraction mirror lens focal image light concave", "OPT"),
        ("mirror lens refraction focal concave image light", "OPT"),
        ("lens concave refraction light focal mirror image", "OPT"),
    ]
    m = TopicMapper().fit(examples)
    topic, score = m.predict("chlorophyll stomata photosynthesis leaves")
    assert topic == "BIO"
    assert score > 0


def test_an_unrelated_query_falls_below_a_raised_gate():
    m = TopicMapper(min_score=0.99).fit([
        ("photosynthesis chlorophyll stomata glucose", "BIO"),
        ("refraction mirror lens focal light", "OPT"),
    ])
    topic, _score = m.predict("accounting ledger depreciation balance sheet")
    assert topic is None


def test_predict_without_fitting_returns_none():
    assert TopicMapper().predict("anything at all") == (None, 0.0)


def test_predict_on_unseen_vocabulary_returns_none():
    m = TopicMapper().fit([("photosynthesis chlorophyll", "BIO")])
    topic, score = m.predict("zzzz qqqq")
    assert topic is None
    assert score == 0.0


def test_scores_are_deterministic_and_sorted():
    examples = [
        ("algebra equation variable solve", "ALG"),
        ("geometry triangle angle side", "GEO"),
        ("algebra equation solve variable", "ALG"),
        ("geometry angle triangle side", "GEO"),
    ]
    m = TopicMapper().fit(examples)
    first = m.scores("algebra equation solve")
    second = TopicMapper().fit(examples).scores("algebra equation solve")
    assert [t for t, _ in first] == [t for t, _ in second]
    assert [s for _, s in first] == sorted((s for _, s in first), reverse=True)


def test_majority_topic_wins_a_tie_in_centroid_mass():
    """A topic with more examples has a more populated centroid."""
    m = TopicMapper().fit([
        ("cell membrane nucleus cytoplasm", "BIO"),
        ("cell membrane nucleus cytoplasm mitochondria", "BIO"),
        ("cell membrane nucleus", "BIO"),
    ])
    topic, _ = m.predict("cell membrane nucleus cytoplasm mitochondria")
    assert topic == "BIO"


# --- the gate -------------------------------------------------------------

def test_gate_from_cv_picks_the_LOWEST_threshold_that_clears_the_bar():
    """Lowest, not highest: the gate should cost as little coverage as possible."""
    cv = {"total": 100, "folds": 5, "rows": [
        {"threshold": 0.0, "covered": 100, "coverage": 1.0, "precision": 0.40, "recall": 0.40},
        {"threshold": 0.2, "covered": 80, "coverage": 0.80, "precision": 0.82, "recall": 0.66},
        {"threshold": 0.4, "covered": 40, "coverage": 0.40, "precision": 0.95, "recall": 0.38},
    ]}
    assert TopicMapper.gate_from_cv(cv, min_precision=0.80) == 0.2


def test_gate_from_cv_returns_None_when_the_bar_is_unreachable():
    """None is a STOP signal, not a shrug. The caller must not apply the mapper."""
    cv = {"total": 100, "folds": 5, "rows": [
        {"threshold": 0.0, "covered": 100, "coverage": 1.0, "precision": 0.05, "recall": 0.05},
        {"threshold": 0.5, "covered": 10, "coverage": 0.10, "precision": 0.30, "recall": 0.03},
    ]}
    assert TopicMapper.gate_from_cv(cv, min_precision=0.80) is None


def test_gate_from_cv_rejects_high_precision_at_negligible_coverage():
    """99% precision on 1% of the corpus is not a usable mapping."""
    cv = {"total": 1000, "folds": 5, "rows": [
        {"threshold": 0.0, "covered": 1000, "coverage": 1.0, "precision": 0.10, "recall": 0.10},
        {"threshold": 0.9, "covered": 5, "coverage": 0.005, "precision": 1.0, "recall": 0.005},
    ]}
    assert TopicMapper.gate_from_cv(cv, min_precision=0.80, min_coverage=0.10) is None


def test_science10_like_reference_is_refused():
    """The shape that actually failed: many topics, ~2 examples each.

    ``Science class 10`` scored 3% precision on the real CBE reference. This
    reproduces that shape and asserts the gate refuses, so the refusal cannot be
    quietly loosened later.

    The vocabulary is alphabetic on purpose: the tokenizer is `[a-z]{3,}`, so a
    fixture built from `w0`/`t1x5` tokenises to nothing and would make this pass
    for the wrong reason.
    """
    import random
    import string
    rng = random.Random(3)
    vocab = ["".join(rng.choice(string.ascii_lowercase) for _ in range(7))
             for _ in range(400)]
    examples = []
    for topic in range(30):                       # 30 fine-grained topics
        for _ in range(2):                        # 2 examples each
            words = rng.sample(vocab, 8)          # overlapping vocabulary
            examples.append((" ".join(words), f"topic{topic}"))
    m = TopicMapper()
    cv = m.cross_validate(examples, folds=5)
    gate = TopicMapper.gate_from_cv(cv, min_precision=0.80, min_coverage=0.15)
    assert gate is None, (
        "a reference with ~2 examples per topic must not clear an 80% precision "
        "bar; if this fails, the calibration has been loosened"
    )


def test_a_dense_separable_reference_IS_accepted():
    """The complement: the gate must not refuse everything out of caution."""
    import random
    import string
    rng = random.Random(5)
    examples = []
    for topic in range(3):
        tag = string.ascii_lowercase[topic] * 3           # "aaa", "bbb", "ccc"
        own = [tag + string.ascii_lowercase[i] + string.ascii_lowercase[j]
               for i in range(6) for j in range(6)]        # 36 distinct words
        noise = ["".join(rng.choice(string.ascii_lowercase) for _ in range(6))
                 for _ in range(60)]
        for _ in range(40):                       # many, tight examples
            words = rng.sample(own, 6) + rng.sample(noise, 2)
            examples.append((" ".join(words), f"topic{topic}"))
    cv = TopicMapper().cross_validate(examples, folds=5)
    gate = TopicMapper.gate_from_cv(cv, min_precision=0.80, min_coverage=0.15)
    assert gate is not None


def test_cross_validate_reports_coverage_and_precision_monotonically():
    """Tightening the gate cannot increase coverage or decrease precision."""
    examples = [
        ("alpha beta gamma delta", "A"), ("alpha beta gamma epsilon", "A"),
        ("alpha beta delta zeta", "A"), ("alpha gamma delta eta", "A"),
        ("mu nu xi omicron", "B"), ("mu nu xi pi", "B"),
        ("mu xi omicron rho", "B"), ("nu xi pi sigma", "B"),
    ]
    cv = TopicMapper().cross_validate(examples, folds=4)
    prev_cov, prev_prec = 1.1, -1.1
    for row in cv["rows"]:
        assert row["coverage"] <= prev_cov + 1e-9
        assert row["precision"] >= prev_prec - 1e-9
        prev_cov, prev_prec = row["coverage"], row["precision"]


def test_cross_validate_is_deterministic():
    examples = [(f"alpha beta gamma {i}", "A" if i % 2 else "B") for i in range(20)]
    a = TopicMapper().cross_validate(examples, folds=4)
    b = TopicMapper().cross_validate(examples, folds=4)
    assert a == b
