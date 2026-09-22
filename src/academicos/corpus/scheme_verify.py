"""Does this official answer answer this question?

Pure functions: a question record and one candidate answer in, a verdict out.
The index (`assessment.question_bank.AnswerKeyIndex`) asks this of every
candidate it holds for a (paper code, question number) and labels only an
accepted one `cbse_marking_scheme`.

Why it exists
-------------
answer_keys.db holds 15,605 rows under 11,787 (paper code, q_no) keys: 3,117
keys carry answers from more than one source document -- the English- and
Hindi-medium schemes of one paper, two editions of the same scheme, a question
paper parsed as if it were a scheme -- and within one source the question
numbers are often misaligned. The index used to keep whichever row loaded last
and the relink labelled it official unseen. The audit of 2026-09-21 measured
895 of 2,930 served "official" schemes detectably wrong and about 75% of the
subjective ones answering a different question.

A verdict names one reason, checked in this order:

  document-id         the answer is a document identifier, not an answer
  legacy-font         Krutidev/legacy-font text, unreadable as served
  script-mismatch     the answer is in another script than the question
  unreadable-options  an option letter, for a stem whose options cannot be read
  option-mismatch     an MCQ key that resolves to none of the stem's options
  content-mismatch    a subjective answer that shares too little with the stem

The content rule was calibrated on 120 hand-judged pairs, saved with their seed
in tests/fixtures/scheme_verify_sample.json. The judgements are an AI
reviewer's, not a teacher's. The rule accepts none of the 76 pairs judged wrong
and 17 of the 32 judged correct; the constants below say where each number
comes from.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from ..assessment.marking import parse_options
from .mcq_shape import (
    correct_letter,
    has_option_labels,
    options_from_parts,
    options_from_stem,
    tokens,
)

REASONS = ("document-id", "legacy-font", "script-mismatch", "unreadable-options",
           "option-mismatch", "content-mismatch")

# --- calibration (tests/fixtures/scheme_verify_sample.json) ---------------- #
# An answer is judged only on the words it shares with the stem; with fewer
# than three shared, judged-correct and judged-wrong pairs are not separable
# (two shared words is what any two questions of one chapter have in common).
MIN_SHARED_WORDS = 3
# Share of the ANSWER's content words the stem also has. Judged-wrong pairs
# reached 0.50 (another set's case study: same verbs, different company);
# judged-correct pairs accepted on this share sit at 0.56 and above. The
# margin is thin, and the fixture test pins it.
ANSWER_SHARE = 0.55
# Share of the STEM's content words the answer also has: a long answer that
# addresses every term of a short question. Judged-wrong pairs reached 0.57
# (the parallel question of another set); the 5 judged-correct pairs accepted
# on this share alone start at 0.62.
STEM_SHARE = 0.6
# Mathematics shares few words and many numbers. Three of the stem's own
# numbers (two digits or more) in the answer: no judged-wrong pair had more
# than two -- a word limit ("120-150 words") and an LCM question repeated back
# ("576 and 512"). Of the 25 maths pairs, 2 of the 3 judged correct are
# accepted (one on three numbers and one word) and all 20 judged wrong are
# rejected. At least one content word must be shared too: on the served bank
# a mean-and-median question (class intervals 0-10, 10-20, 20-30) took a
# speed-of-a-boat answer that happened to say 10, 20 and 30.
MIN_SHARED_NUMBERS = 3
# An answer whose tokens are 80% runs copied from the stem repeats the
# question; 4 judged-wrong pairs were exactly that, no judged-correct one.
ECHO_SHARE = 0.8
ECHO_RUN = 3

# Words any question or scheme uses, whatever it is about. Sharing them says
# nothing: an assertion-reason verdict shares "assertion", "reason", "true"
# with every assertion-reason stem, and "sin", "cos", "tan" are in every
# trigonometry question -- 1 judged-wrong maths pair matched on those alone.
_STOPWORDS = frozenset("""
the and for are was were this that with from have has had not but can will shall would
should could may might been being into onto than then them they their there these those
which what when where who whom whose why how its his her our your you any all each some
such only also very more most other about above below after before between both during
over under again further once here same own too just because while until upon per via
given following find show write state explain give name mention describe discuss define
two three four five one marks mark answer answers question questions correct option
options value point points award awarded either reason reasons assertion true false
explanation statement attempt words word note ans sol candidates candidate section part
parts extract passage read based information using use used case study hence thus
therefore let also
sin cos tan sec cosec cot log
का के की में है हैं और से को पर एक यह वह इस उस लिए द्वारा तथा या भी नहीं होता होती होते
किया करते कीजिए लिखिए क्या किस कौन
""".split())

# --- document ids ---------------------------------------------------------- #
# "MS_X_Mathematics_041_30/2/1_2022-23", "XII_042_Physics_MS_55_1_1,2,3.pdf":
# an underscore-joined run with the scheme's code and year, or a filename.
_DOC_ID = re.compile(r"\b(?:MS_)?(?:X|XII)_[\w/,.\-]*\d[\w/,.\-]*|\S+(?i:\.pdf)\b")

# --- legacy font ----------------------------------------------------------- #
# Krutidev maps Devanagari glyphs onto Latin code points, so Hindi typed in it
# extracts as "fdUgha rhu dkj.kksa dk o.kZu dhft,". Its commonest words are
# fixed strings. Across the served bank's 3,286 stems and their 4,176
# candidates, >= 3 of them at >= 4% of tokens flags 127 Krutidev answers and
# no English text; one English stem has 2 hits in 238 tokens (0.8%).
_KRUTIDEV = frozenset("""
gS gSa esa dk ds dh dks vkSj rFkk ls fd ;g og Hkh ugha fy, tks bl mUgsa gks x;k fn;k dj
djsa djrs djus gksrk gksrh gksus ,d vFkok iz'u mÙkj
""".split())
_KRUTIDEV_HITS = 3
_KRUTIDEV_SHARE = 0.04

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_CAPITAL_LABEL = re.compile(r"\(([A-D])\)")
_COMPANY = re.compile(r"\b([A-Z][A-Za-z]+)\s+(?:Ltd|Limited)\b")
_PARTNERS = re.compile(
    r"((?:[A-Z][a-z]+\s*,\s*)*[A-Z][a-z]+\s+and\s+[A-Z][a-z]+)\s+(?:were|are)\s+partners")
_ASSERTION_REASON = re.compile(r"\bAssertion\s*\(A\).*\bReason\s*\(R\)", re.I | re.S)
# "(B) / ", "Ans. (c)", "C." -- the letter a key opens with -- and the mark
# note a scheme closes one with ("1 mark", "1 Mark", "½").
_KEY_LABEL = re.compile(r"^\s*(?:ans\.?\s*)?\(?\s*[A-Da-d]\s*\)?\s*(?:[/.):\-]\s*)*(?=\s|$)", re.I)
_MARK_NOTE = re.compile(r"(?:\s*(?:\d+|½)\s*marks?\b)+\s*$", re.I)


@dataclass(frozen=True)
class Verdict:
    """`reason` is None when the answer is accepted. `score` ranks accepted
    candidates against each other; it means nothing on a rejection. `option`
    is the letter an accepted MCQ key resolved to, whether it was keyed by
    letter or by the option's words."""

    reason: str | None = None
    score: float = 0.0
    option: str | None = None

    @property
    def accepted(self) -> bool:
        return self.reason is None


# --------------------------------------------------------------------------- #
# script
# --------------------------------------------------------------------------- #

def _garble():
    """bank_merge's garble detector and its script table, imported late.

    One detector, not two: the composer drops CBE/SQP rows with it and the
    verifier rejects answers with it. The import is deferred because
    bank_merge imports assessment.question_bank, which imports this module.
    """
    from .bank_merge import _ARTS, _GARBLE_RUNS, _SUBJECT_SCRIPTS, _vowel_sign_runs
    return _ARTS, _GARBLE_RUNS, _SUBJECT_SCRIPTS, _vowel_sign_runs


def _script_of(ch: str) -> str:
    return unicodedata.name(ch, "").split(" ", 1)[0]


def dominant_script(text: str, *, minimum: int = 4) -> str | None:
    """LATIN, DEVANAGARI, ... for the script most letters are in.

    Only scripts a paper is written in count: Greek and the mathematical
    alphanumerics (θ, 𝑥) appear in every script's maths. Fewer than `minimum`
    letters is no evidence either way.
    """
    _, _, scripts, _ = _garble()
    writing = {"LATIN"}.union(*scripts.values())
    counts: dict[str, int] = {}
    for ch in text or "":
        if ch.isalpha():
            s = _script_of(ch)
            if s in writing:
                counts[s] = counts.get(s, 0) + 1
    if sum(counts.values()) < minimum:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def medium_of_text(text: str) -> str:
    """'hi' for Devanagari text, 'en' for Latin, '' when it cannot tell."""
    script = dominant_script(text)
    return {"DEVANAGARI": "hi", "LATIN": "en"}.get(script or "", "")


def question_medium(record: dict) -> str:
    return medium_of_text(str(record.get("stem") or "")) or "en"


def _expected_script(record: dict) -> str | None:
    """The script an answer to this question is written in.

    A language paper's own script (Hindi and Sanskrit are Devanagari on both
    sides whatever the stem's instructions are in); otherwise the stem's.
    """
    arts, _, scripts, _ = _garble()
    subject = str(record.get("subject") or "").strip()
    if not arts.search(subject):
        first = re.split(r"[\s(]", subject.lower(), maxsplit=1)[0]
        own = scripts.get(first)
        if own is not None:
            return sorted(own)[0] if len(own) == 1 else None
    return dominant_script(str(record.get("stem") or ""))


def is_legacy_font(text: str) -> bool:
    _, runs_needed, _, vowel_sign_runs = _garble()
    if vowel_sign_runs(text) >= runs_needed:
        return True
    toks = [t.strip(".,()[]") for t in (text or "").split()]
    hits = sum(t in _KRUTIDEV for t in toks)
    return hits >= _KRUTIDEV_HITS and hits / max(len(toks), 1) >= _KRUTIDEV_SHARE


def strip_document_ids(text: str) -> str:
    return " ".join(_DOC_ID.sub(" ", text or "").split())


# --------------------------------------------------------------------------- #
# overlap
# --------------------------------------------------------------------------- #

def _words(text: str) -> list[str]:
    """Runs of letters and combining marks, casefolded.

    Letters AND marks, because a Devanagari word without its vowel signs is
    not the word (\\w drops them). Digits split a word: "6V" is "v".
    """
    out, cur = [], []
    for ch in unicodedata.normalize("NFC", text or "").casefold():
        if unicodedata.category(ch)[0] in "LM":
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def content_words(text: str) -> set[str]:
    """Words of 3+ characters that are not generic, cut to 6 characters so
    "reflect" and "reflection" meet."""
    return {w[:6] for w in _words(text) if len(w) >= 3 and w not in _STOPWORDS}


def numbers(text: str) -> set[str]:
    """Numbers of two significant characters or more, commas dropped:
    "30,00,000" and "3000000" meet; single digits are in every question."""
    out = set()
    for m in _NUMBER.findall(unicodedata.normalize("NFKC", text or "")):
        v = m.replace(",", "").rstrip(".")
        if len(v.replace(".", "")) >= 2:
            out.add(v)
    return out


def _echo_share(stem: str, answer: str) -> float:
    """Share of the answer's tokens that sit in runs copied from the stem."""
    a = [t for t in re.findall(r"\w+", answer.casefold())]
    s = [t for t in re.findall(r"\w+", stem.casefold())]
    if not a:
        return 0.0
    blocks = SequenceMatcher(None, a, s, autojunk=False).get_matching_blocks()
    return sum(b.size for b in blocks if b.size >= ECHO_RUN) / len(a)


def case_names(text: str) -> set[str]:
    """The firms and partners a case study names: "Saket and Suveni were
    partners", "Shivalik Ltd.". Lower-cased."""
    names = {m.group(1).casefold() for m in _COMPANY.finditer(text or "")}
    for m in _PARTNERS.finditer(text or ""):
        names |= {n.casefold() for n in re.findall(r"[A-Z][a-z]+", m.group(1))}
    return names


def _content_verdict(stem: str, answer: str) -> Verdict:
    if _echo_share(stem, answer) >= ECHO_SHARE:
        return Verdict("content-mismatch")
    named = case_names(answer)
    if named and not any(n in stem.casefold() for n in named):
        # Another set's case study: the same verbs and ledger words, other
        # people. 67/4/2 Q26 asks about Bhumi and Chavi; its candidate
        # answers for "Saket and Suveni were partners" and shares enough
        # accounting words to pass the overlap rule.
        return Verdict("content-mismatch")
    a, s = content_words(answer), content_words(stem)
    shared = len(a & s)
    answer_share = shared / len(a) if a else 0.0
    stem_share = shared / len(s) if s else 0.0
    if shared >= MIN_SHARED_WORDS and (answer_share >= ANSWER_SHARE or stem_share >= STEM_SHARE):
        return Verdict(score=max(answer_share, stem_share))
    shared_numbers = len(numbers(answer) & numbers(stem))
    if shared_numbers >= MIN_SHARED_NUMBERS and shared:
        return Verdict(score=min(1.0, shared_numbers / max(len(numbers(stem)), 1)))
    return Verdict("content-mismatch")


# --------------------------------------------------------------------------- #
# options
# --------------------------------------------------------------------------- #

def question_options(record: dict) -> dict[str, str] | None:
    """The options an MCQ prints, or None when this is not one.

    `options_from_stem` also reads the (a)-(d) sub-parts of a 5-mark question
    as options, and a subjective answer judged against them would fail for the
    wrong reason, so above 1 mark only all four CAPITAL labels (A)-(D) make an
    MCQ: 67/1/1 Q29 is filed at 3 marks with a 1-mark MCQ fused into its stem,
    and its candidate -- the question's own opening plus the next part's --
    shares enough words to pass as a subjective answer. Capital labels that
    `options_from_stem` refuses ("(a) Analysis ... (A) Labour Unions (B) ...",
    where a part label comes first) are read by `parse_options`.
    """
    parts = record.get("parts") or []
    if parts:
        # CBE/SQP items carry their options as parts, not in the stem.
        from_parts = options_from_parts(parts)
        if from_parts:
            return from_parts
    stem = str(record.get("stem") or "")
    marks = record.get("marks")
    one_mark = (record.get("type") == "mcq" or not isinstance(marks, (int, float))
                or marks <= 1)
    if one_mark:
        opts = options_from_stem(stem)
        if not opts and has_option_labels(stem):
            opts = parse_options(stem) or None
        return opts
    if set("ABCD") <= set(_CAPITAL_LABEL.findall(stem)):
        return parse_options(stem) or None
    return None


def _core(option: str) -> list[str]:
    """An option's tokens without the page footer extraction glued on:
    "Public relations 11-" is option D of 66/1/1 Q16."""
    toks = tokens(option)
    while toks and re.fullmatch(r"\d+|-", toks[-1]):
        toks.pop()
    return toks


def _named_options(text: str, options: dict[str, str]) -> list[str]:
    """The options whose words open `text`, once any "(B) /" label is cut."""
    body = tokens(_KEY_LABEL.sub("", text))
    return [k for k, v in options.items() if (core := _core(v)) and body[:len(core)] == core]


def _option_verdict(options: dict[str, str], answer: str, option: str | None) -> Verdict:
    """A key resolves to an option by its letter or by its words -- and when
    it has both, they must agree.

    A letter alone is always "among the options", so it is only as good as
    the row it came from. Of the served bank's 200 MCQ candidates with a
    letter, 26 are the bare letter, 18 carry words naming the letter's option
    and 156 words naming none: "Noise For Visually Impaired Candidates" keyed
    C for "doing the task correctly
    and with minimum cost" (66/1/1 Q4), "59" keyed A among four coordinate
    pairs. Words that name no option mean the row answers another question.
    """
    if option:
        letter = str(option).strip().upper()
        if letter not in options:
            return Verdict("option-mismatch")
        rest = _MARK_NOTE.sub("", _KEY_LABEL.sub("", answer)).strip()
        if not re.search(r"\w", rest) or letter in _named_options(answer, options):
            return Verdict(score=1.0, option=letter)
        return Verdict("option-mismatch")
    named = _named_options(answer, options)
    letter = correct_letter([answer], options) or (named[0] if len(named) == 1 else None)
    return Verdict(score=1.0, option=letter) if letter else Verdict("option-mismatch")


# --------------------------------------------------------------------------- #
# the verdict
# --------------------------------------------------------------------------- #

def verify(record: dict, answer: str, option: str | None = None, *,
           judge_content: bool = True) -> Verdict:
    """Accept `answer` (and its option letter, if the key has one) as the
    answer to `record`, or reject it with one of `REASONS`.

    `record` is the wire-shaped question: `stem`, `subject`, `marks`, `type`,
    `parts`. `judge_content=False` skips the content-mismatch rule, for a
    scheme its builder attached from the same item (CBE/SQP): the rule
    measures how board marking-scheme rows misalign with their questions, the
    calibration sample holds no CBE/SQP pair, and their one-word and numeric
    answers would all fail it. Every other check still applies.
    """
    answer = (answer or "").strip()
    options = question_options(record)
    if not options and (option or _ASSERTION_REASON.search(str(record.get("stem") or ""))):
        # A letter for a stem with no readable options: nothing ties it to
        # this question. 2 of the 3 checked by hand keyed the wrong verdict
        # of an assertion-reason item. An assertion-reason item's answer is a
        # verdict among four fixed alternatives, so its words are the same
        # for every such item and prove nothing either: "(B)/ The reaction of
        # a reactive metal with dilute acid" shares enough words with 31/3/1
        # Q17 (hydrogen and nitric acid) to pass as a subjective answer.
        return Verdict("unreadable-options")
    if options and option:
        return _option_verdict(options, answer, option)

    if answer and not strip_document_ids(answer):
        return Verdict("document-id")
    answer = strip_document_ids(answer)
    if is_legacy_font(answer):
        return Verdict("legacy-font")
    expected = _expected_script(record)
    got = dominant_script(answer)
    if expected and got and got != expected:
        return Verdict("script-mismatch")
    if options:
        return _option_verdict(options, answer, None)
    if not judge_content:
        return Verdict(score=0.0)
    return _content_verdict(str(record.get("stem") or ""), answer)
