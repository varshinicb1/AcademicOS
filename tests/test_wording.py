"""Counted nouns in the builder's and the papers' sentences (QA P-33)."""
from __future__ import annotations

import pytest

from academicos.assessment.wording import counted


@pytest.mark.parametrize("text, said", [
    ("Only 2 3-mark question(s) are available; 3 short.", "Only 2 3-mark questions are available; 3 short."),
    ("Ask for 1 question(s) instead of 6", "Ask for 1 question instead of 6"),
    ("Section B: 1 OR alternative(s) taken", "Section B: 1 OR alternative taken"),
    ("Section B: 2 OR alternative(s) taken", "Section B: 2 OR alternatives taken"),
    ("(Any 2 of the above value points, 1 mark(s) each.)", "(Any 2 of the above value points, 1 mark each.)"),
    ("None of the 4 Social Science question(s)", "None of the 4 Social Science questions"),
    ("at most 0 competency-based question(s) of the 4", "at most 0 competency-based questions of the 4"),
    ("the bank has 5 2-mark short answer question(s) of", "the bank has 5 2-mark short answer questions of"),
    ("no count, question(s) left as written", "no count, question(s) left as written"),
])
def test_each_count_settles_its_own_noun(text, said):
    assert counted(text) == said
