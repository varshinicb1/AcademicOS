"""Generate CBSE-format questions for one chapter, and say what it refused.

    python scripts/gen_cbse_chapter.py --book aejm1 --chapter 1 [--check]
    python scripts/gen_cbse_chapter.py --all --limit 3

The LLM is Cloudflare Workers AI, reached with the account's API token, because
that is the one that is free at a scale worth generating at and speaks JSON
schema -- which is what makes "follow the board's format" a constraint the model
cannot talk its way around.

Nothing here writes to the served bank. Output goes to
`academicos-data/corpus/ai-cbse/questions.json`, which the merge reads like any
other corpus, so a generated chapter is reviewable before it is ever served.

Every question that comes back is validated in `cbse_generate.validate` before it
is kept, and a refusal is recorded with its reason. A section that produces
nothing but refusals is reported as such: that is the signal that the chapter does
not support that section, not a reason to loosen the check.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.corpus import cbse_blueprint as bp            # noqa: E402
from academicos.corpus import cbse_generate as cg             # noqa: E402
from academicos.corpus import hindi_ocr as ho                   # noqa: E402
from academicos.corpus import textbook as tb                  # noqa: E402

BOOKS = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters")
TRANSCRIPTIONS = Path(
    r"C:\Users\varsh\OneDrive\Documents\Sarvam\bank-pipeline\transcriptions\textbook")
OUT = ROOT / "academicos-data" / "corpus" / "ai-cbse" / "questions.json"

API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"

# Measured on this account, three runs each, on a CBSE MCQ with the blueprint's
# schema:
#
#   llama-3.1-8b-instruct   3 of 3 runs FAILED -- it never emitted a stop token,
#                          ran to max_tokens every time, and produced output with
#                          no parseable JSON in it. It also routes to
#                          `llama-3.1-8b-fast-v2`, the non-JSON variant, so the
#                          schema is not reaching it.
#   llama-3.3-70b-...-fast clean on the objective and written sections, but
#                          4 of 4 REFUSED on Section E -- asked for a case-based
#                          passage it returns another short question.
#
# So the free tier is not a usable single model, and the routing below is by
# section *value* rather than by provider.
#
# On cost: 74% of a Gemini call is output tokens, measured on the Section E call
# (1,570 in / 536 out = $0.00181, of which $0.00134 is output). So the savings
# come from writing less and calling less often, not from picking a small model.
# `flash-lite` is $0.10/$0.40 against flash's $0.30/$2.50 -- five times cheaper on
# output -- which is worth having on the sections whose whole output is four
# options, and not worth having on a case-based passage.
WORKERS_CHEAP = "@cf/meta/llama-3.1-8b-instruct"      # unusable; kept to record why
WORKERS_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

GEMINI_MODEL = "gemini-2.5-flash"            # everything that has to be right
GEMINI_LITE = "gemini-2.5-flash-lite"        # objective sections, five times cheaper

# Sections whose marking points a human will read, and where a weak question is
# expensive: a case-based passage and a long answer are written, judged, and
# printed. An MCQ is four options and a letter.
CHEAP_SECTIONS = frozenset({cg.bp.MCQ, cg.bp.ASSERTION_REASON, cg.bp.VSA})

DEFAULT_BY_PROVIDER = {
    "gemini": GEMINI_MODEL,
    "workers": WORKERS_MODEL,
}
CHEAP_MODEL = WORKERS_MODEL
STRONG_MODEL = WORKERS_MODEL
STRONG_SECTIONS: set[str] = set()


def model_for(section, tiered: bool, provider: str = "gemini") -> str:
    """The model a section is generated with.

    The one thing this will not do is let the cheap model near Section E. A
    case-based question is the part of a CBSE paper that carries the board's
    competency weight, and it is the one the weakest model on the free tier could
    not produce at all.
    """
    if provider == "workers":
        return WORKERS_MODEL
    if not tiered:
        return GEMINI_MODEL
    return GEMINI_LITE if section.qtype in CHEAP_SECTIONS else GEMINI_MODEL


# Gemini 2.5 Flash, per million tokens, as published. Used only to report what a
# run cost; the number is not a budget the pipeline enforces.
GEMINI_IN_PER_M = 0.30
GEMINI_CACHED_PER_M = 0.03     # cached input is a tenth of fresh
GEMINI_OUT_PER_M = 2.50
GEMINI_LITE_IN_PER_M = 0.10
GEMINI_LITE_OUT_PER_M = 0.40


def _cost_of(usage: dict, model: str = GEMINI_MODEL) -> float:
    """What one call cost, in dollars. Zero for Workers AI, which is neurons.

    Reads `cached_tokens` where the provider reports it, so the saving from prompt
    caching appears in the number rather than being assumed.
    """
    lite = model == GEMINI_LITE
    rate_in = GEMINI_LITE_IN_PER_M if lite else GEMINI_IN_PER_M
    rate_out = GEMINI_LITE_OUT_PER_M if lite else GEMINI_OUT_PER_M
    prompt = usage.get("prompt_tokens") or 0
    cached = usage.get("cached_tokens") or 0
    fresh = max(0, prompt - cached)
    return (fresh / 1e6 * rate_in
            + cached / 1e6 * GEMINI_CACHED_PER_M
            + (usage.get("completion_tokens") or 0) / 1e6 * rate_out)


def group_plan(plan: list[tuple], per_call: int = 3) -> list[list[tuple]]:
    """The plan collapsed into calls.

    Nine one-question calls pay for the chapter nine times; three three-question
    calls pay for it three times, and the chapter text is most of the prompt. So
    this is the largest cost lever in the pipeline, and it is a quality lever too:
    a model writing the third question in a section can see the first two, which is
    what stops it restating the same sentence -- the failure that produced four
    questions testing one line of text on the first real run.

    Only same-section items are grouped, because the schema pins the section's type
    and marks. Topic rotates inside the group, so a group still spans the chapter
    rather than hammering one heading.
    """
    if per_call < 1:
        per_call = 1
    grouped: list[list[tuple]] = []
    current: list[tuple] = []
    current_key = None
    for section, topic in plan:
        key = (section.key, section.qtype, section.marks)
        if key != current_key or len(current) >= per_call:
            if current:
                grouped.append(current)
            current = []
            current_key = key
        current.append((section, topic))
    if current:
        grouped.append(current)
    return grouped
    """What one call cost, in dollars. Zero for Workers AI, which is neurons."""
    return ((usage.get("prompt_tokens") or 0) / 1e6 * GEMINI_IN_PER_M
            + (usage.get("completion_tokens") or 0) / 1e6 * GEMINI_OUT_PER_M)


def _env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return ""


_RETRY_IN = re.compile(r"retry in\s+([0-9.]+)\s*s", re.I)


def _retry_after(detail: str) -> float | None:
    """The wait Gemini asked for, in seconds.

    Its 429 body ends "Please retry in 53.138167936s." -- the number is the
    provider's own view of when the request-per-minute window frees up, and
    guessing a shorter wait just spends the window again.
    """
    match = _RETRY_IN.search(detail or "")
    return float(match.group(1)) if match else None


def call_gemini(system: str, schema: dict, user: str, *, model: str,
                temperature: float = 0.4, max_tokens: int = 3000,
                retries: int = 3) -> tuple[dict, dict]:
    """One generation call against Gemini. Returns (parsed, usage).

    Gemini holds a schema as firmly as Workers AI does, but its `responseSchema`
    is a smaller subset -- no `const`, no `enum` on a number, no `minItems` -- which
    is why `_schema` sticks to string enums. See that function for the whole
    intersection.
    """
    key = _env("GEMINI_API_KEY", "GOOGLE_API_KEY")
    if not key:
        raise SystemExit("set GEMINI_API_KEY")

    payload = json.dumps({
        # The chapter text opens the user turn and is identical for every section
        # of the chapter, so it is the stable prefix. Cached input is $0.03/M
        # against $0.30/M fresh, and every section after the first for a chapter
        # reads the same ~1,500 tokens. The system prompt is deliberately *not*
        # cached: it differs per section, and a changing prefix would invalidate
        # the cache for everything after it.
        "contents": [
            {"parts": [{"text": user}]},
            {"parts": [{"text": system + "\n\nReturn only the questions, as JSON "
                                     "matching the schema."}]},
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }).encode("utf-8")

    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    last = ""
    for attempt in range(retries):
        request = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            last = f"HTTP {exc.code}: {detail}"
            if exc.code == 429:
                # Gemini says exactly how long to wait, and it is worth listening
                # to: the free tier is 20 requests a minute for gemini-2.5-flash,
                # and a corpus run is thousands of calls. Backing off two seconds
                # and retrying just spends the rest of the window. So the wait
                # comes from the message when there is one, and grows without it.
                wait = _retry_after(detail) or min(120, 15 * (2 ** attempt))
                print(f"   429 from Gemini, waiting {wait:.0f}s", flush=True)
                time.sleep(wait)
                continue
            if exc.code in (500, 502, 503):
                time.sleep(2 ** attempt * 3)
                continue
            raise SystemExit(f"gemini generation failed: {last}")
        except (urllib.error.URLError, TimeoutError) as exc:
            last = f"network: {exc}"
            time.sleep(2 ** attempt * 3)
            continue

        try:
            parsed = json.loads(
                body["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError, ValueError) as exc:
            finish = (body.get("candidates") or [{}])[0].get("finishReason")
            last = f"unreadable response (finish={finish}): {exc}"
            time.sleep(1.5)
            continue
        if not isinstance(parsed, dict) or "questions" not in parsed:
            last = f"no 'questions' in response: {str(parsed)[:160]}"
            time.sleep(1.5)
            continue
        meta = body.get("usageMetadata") or {}
        return parsed, {"prompt_tokens": meta.get("promptTokenCount", 0),
                        "cached_tokens": meta.get("cachedContentTokenCount", 0),
                        "completion_tokens": meta.get("candidatesTokenCount", 0),
                        "neurons": None}

    raise SystemExit(f"gemini generation failed after {retries} attempts: {last}")


def call_workers_ai(system: str, schema: dict, user: str, *,
                    model: str = cg.DEFAULT_MODEL, temperature: float = 0.4,
                    max_tokens: int = 3000, retries: int = 3) -> tuple[dict, dict]:
    """One generation call. Returns (parsed, usage).

    Workers AI will not always honour the schema; when it does not it says so with
    an `error` JSON body rather than an HTTP failure, so that case is caught here
    instead of being parsed into a question with fields missing.
    """
    account = _env("CLOUDFLARE_ACCOUNT_ID", "CF_ACCOUNT_ID")
    token = _env("CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", "CLOUDFLARE_API_KEY")
    if not account or not token:
        raise SystemExit(
            "set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN "
            "(a free Workers AI token is enough)")

    payload = json.dumps({
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "response_format": {"type": "json_schema", "json_schema": schema},
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    url = API.format(account=account, model=model)
    last = ""
    for attempt in range(retries):
        request = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            last = f"HTTP {exc.code}: {detail}"
            if exc.code in (429, 500, 502, 503):
                time.sleep(2 ** attempt * 2)
                continue
            raise SystemExit(f"generation failed: {last}")
        except (urllib.error.URLError, TimeoutError) as exc:
            last = f"network: {exc}"
            time.sleep(2 ** attempt * 2)
            continue

        # The REST envelope is {success, errors, messages, result}; the completion
        # and the usage are inside `result`, not at the top level.
        result = body.get("result") or {}
        parsed = result.get("response")
        if parsed is None:
            # A 200 with no body is a real failure mode, not a valid empty answer.
            # Returning it as `{}` here would silently drop every question in the
            # section and report the chapter as generated with nothing in it.
            last = (f"no response body (success={body.get('success')}, "
                    f"errors={body.get('errors')}, result keys={sorted(result)[:8]})")
            time.sleep(1.5)
            continue
        if isinstance(parsed, dict) and "error" in parsed:
            last = f"schema not met: {parsed['error']}"
            time.sleep(1.5)
            continue
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except ValueError:
                last = "response was not JSON"
                time.sleep(1.5)
                continue
        if not isinstance(parsed, dict) or "questions" not in parsed:
            # Present, parseable, and not the shape the schema asked for. The
            # model returned prose or an empty object.
            last = f"response had no 'questions': {str(parsed)[:160]}"
            time.sleep(1.5)
            continue
        return parsed, (result.get("usage") or {})

    raise SystemExit(f"generation failed after {retries} attempts: {last}")


def book_registry() -> dict[str, dict]:
    """Book code -> the metadata the books do not print on the cover.

    Taken from the transcriptions, which already carry it, rather than decoded
    from the code: `jemh1` and `femm1` are not distinguishable by inspection and a
    wrong subject silently files a whole book under the wrong paper.
    """
    out: dict[str, dict] = {}
    for path in sorted(TRANSCRIPTIONS.glob("*.json")):
        if path.name.endswith(".solve2.json"):
            continue
        try:
            book = (json.loads(path.read_text(encoding="utf-8")) or {}).get("book") or {}
        except (OSError, ValueError):
            continue
        if book.get("code"):
            out[book["code"]] = book
    return out


def chapter_topics(book_code: str) -> dict[int, list[str]]:
    """Chapter number -> the topics the transcriptions named for it."""
    out: dict[int, list[str]] = {}
    for path in sorted(TRANSCRIPTIONS.glob(f"{book_code}-*.json")):
        if path.name.endswith(".solve2.json"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        chapter = doc.get("chapter") or {}
        number = int(chapter.get("number") or 0)
        names = [t.get("title") for t in (doc.get("topics") or [])
                 if t.get("title")]
        if number and names:
            out.setdefault(number, list(dict.fromkeys(names)))
    return out


TAXONOMY = ROOT / "academicos-data" / "syllabus" / "taxonomy"

_tree_chapters: dict[str, dict[int, dict]] | None = None


def taxonomy_chapters() -> dict[str, dict[int, dict]]:
    """book code -> chapter number -> {name, id, topics}.

    The trees are the one place that knows a chapter's *name* as well as its
    topics, for every grade: the classes 6-10 trees were read off the books' own
    typography and point straight at the chapter PDFs, and the classes 1-5 trees
    were read off the transcriptions.

    The name matters, not just the topics. A chapter's id is a slug of its name, so
    a chapter named after its first topic rather than its own name gets an id that
    is in no tree -- and every question generated for it would be filed under a
    chapter nothing can resolve.
    """
    global _tree_chapters
    if _tree_chapters is not None:
        return _tree_chapters
    out: dict[str, dict[int, dict]] = {}
    for path in sorted(TAXONOMY.glob("*.json")):
        if path.name.startswith("_") or path.name == "review_queue.json":
            continue
        try:
            tree = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for chapter in tree.get("chapters") or []:
            source = str(chapter.get("source_file") or "")
            if not source:
                continue
            code = Path(source).parent.name
            digits = Path(source).stem[len(code):]
            if not code or not digits.isdigit():
                continue
            out.setdefault(code, {})[int(digits)] = {
                "name": chapter.get("name") or "",
                "id": chapter.get("id") or "",
                "topics": [t.get("name") for t in (chapter.get("topics") or [])
                           if t.get("name")],
            }
    _tree_chapters = out
    return out


def topics_for(book_code: str, number: int) -> list[str]:
    """A chapter's topics: the taxonomy tree's, else the chapter's own headings."""
    from_trees = taxonomy_chapters().get(book_code, {}).get(number, {}).get("topics")
    if from_trees:
        return from_trees
    from_transcription = chapter_topics(book_code).get(number) or []
    if from_transcription:
        return from_transcription
    pdf = chapter_pdf(book_code, number)
    if pdf.is_file():
        return cg.headings_in_chapter(pdf, number)
    return []


def chapter_pdf(book_code: str, number: int) -> Path:
    folder = BOOKS / book_code
    for name in (f"{book_code}{number:02d}.pdf", f"{book_code}{number}.pdf"):
        candidate = folder / name
        if candidate.is_file():
            return candidate
    return folder / f"{book_code}{number:02d}.pdf"


def _squash(text: str) -> str:
    """Case, spacing and punctuation folded away, so a quote survives a line wrap.

    Letters, combining marks (a Devanagari vowel sign is one) and digits of every script are
    kept; everything else, quotes and the danda included, is a space. Only ASCII used to be
    kept, which turned every Hindi line into nothing and refused every Hindi question."""
    text = unicodedata.normalize("NFKC", text or "")
    kept = "".join(c if unicodedata.category(c)[0] in "LMN" else " " for c in text.lower())
    return re.sub(r"\s+", " ", kept).strip()


def _quoted_in(quote: str, haystack: str) -> bool:
    """Whether a quote is the chapter's own words.

    The extracted text keeps the page's lines but not always their order: a two-column
    page, a figure's labels or a table are interleaved with the prose, so a quote that
    reads correctly on the page is not one unbroken string in the extraction. So the
    whole quote is tried first, and failing that every line of it that is long enough
    to mean something must be found on its own. An invented sentence still fails: none
    of its lines exist in the text."""
    whole = _squash(quote)
    if len(whole) < 12:
        return False
    if whole in haystack:
        return True
    lines = [_squash(l) for l in quote.splitlines()]
    substantial = [l for l in lines if len(l) >= 12]
    return bool(substantial) and all(l in haystack for l in substantial)


def ungrounded(item: dict, source: str) -> str | None:
    """Why a question is not tied to the text it was set from, or None.

    A free model asked to use only the chapter will still add a plausible figure
    from memory (a state's infant-mortality rate that the page does not print), and
    `cg.validate` cannot see that: the question is well-formed and wrong. Two
    checks catch it without a second model. Every question carries `evidence`,
    quotes copied from the text, and each quote must be found in it. And every
    figure of two or more digits in the question or its answer must occur in the
    text, because an invented number is the commonest invented fact.
    """
    haystack = _squash(source)
    quotes = item.get("evidence")
    if isinstance(quotes, str):
        quotes = [quotes]
    quotes = [q for q in (quotes or []) if isinstance(q, str) and q.strip()]
    if not quotes:
        return "no-evidence"
    for quote in quotes:
        if not _quoted_in(quote, haystack):
            return "evidence-not-in-text"
    parts = [item.get("stem") or "", item.get("passage") or "",
             item.get("modelAnswer") or ""]
    parts += list((item.get("options") or {}).values())
    parts += [str(x) for x in item.get("markingPoints") or []]
    printed = {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,]*\.?\d*", source)}
    # A single digit is a count in most questions ("three states"), but not when it
    # is a rate or a share: "6 per 1,000", "9%".
    # "In about 45 words" and "(5 marks)" instruct the student; they are not facts.
    asked = re.sub(r"\b\d+\s*(?:words?|marks?|minutes?|lines?|steps?|sentences?|points?)\b",
                   " ", " ".join(parts), flags=re.I)
    figures = re.findall(r"\d[\d,]*\.?\d*\d|\d{2,}|\b\d(?=\s*(?:%|per\b|percent))", asked)
    for figure in figures:
        if figure.replace(",", "").rstrip(".") not in printed:
            return f"figure-not-in-text:{figure}"
    return None


def bridge_call(folder: Path, index: int, system: str, schema: dict, user: str,
                section, topic: str) -> dict | None:
    """The answer to call `index`, or None after writing its prompt for a model
    that runs elsewhere. A malformed answer file is a refusal's worth of signal, so
    it is returned as an empty section rather than skipped quietly."""
    folder.mkdir(parents=True, exist_ok=True)
    answer = folder / f"r{index:03d}.json"
    if answer.is_file():
        try:
            parsed = json.loads(answer.read_text(encoding="utf-8"))
        except ValueError:
            return {"questions": []}
        return parsed if isinstance(parsed, dict) else {"questions": []}
    (folder / f"p{index:03d}.json").write_text(json.dumps(
        {"index": index, "section": section.key, "topic": topic, "system": system,
         "schema": schema, "user": user}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return None


def prefer_ocr(chapter: cg.Chapter) -> cg.Chapter:
    """A Hindi chapter whose PDF text layer is not Hindi (a legacy font), read from its OCR cache
    instead. Anything else, and a chapter not yet OCR'd, is returned as it was: the batch then
    skips it for its text, naming the reason, rather than set questions from the wrong characters."""
    if chapter.language != "hi" or ho.devanagari_share(chapter.text) >= ho.DEVANAGARI_SHARE_MIN:
        return chapter
    cached = ho.load(chapter.book_code, chapter.number)
    return dataclasses.replace(chapter, pages=tuple(cached)) if cached else chapter


def generate_chapter(book_code: str, number: int, *, mark_budget: int,
                     model: str, provider: str = 'gemini', tiered: bool = True,
                     delay: float = 0.0, per_call: int = 3,
                     bridge: Path | None = None
                     ) -> tuple[list[dict], list[dict], dict]:
    """Questions, refusals, and the cost, for one chapter.

    `bridge` is a folder, for a model that cannot be called from here (an
    opencode session). Each call's prompt is written to `<bridge>/p###.json`; when
    `<bridge>/r###.json` exists it is read as that call's answer and goes through
    the same validator as any other provider. A call with no answer yet is counted
    as pending, not refused.
    """
    registry = book_registry()
    book = registry.get(book_code)
    if not book:
        raise SystemExit(f"no book metadata for {book_code}")
    subject = tb.bank_subject(book.get("subject"))
    grade = int(book.get("class") or 0)
    known = taxonomy_chapters().get(book_code, {}).get(number) or {}
    topics = topics_for(book_code, number)
    # The chapter's own name, from the tree that named it. Never the first topic:
    # a chapter named after its first topic gets an id that is in no tree, and
    # every question generated for it lands under a chapter nothing resolves.
    chapter_name = known.get("name") or f"Chapter {number}"
    title = chapter_name

    pdf = chapter_pdf(book_code, number)
    if not pdf.is_file():
        raise SystemExit(f"no chapter PDF at {pdf}")
    chapter = cg.read_chapter(
        pdf, book_code=book_code, subject=subject, grade=grade,
        language=book.get("language") or "en", number=number, title=title)
    chapter = prefer_ocr(chapter)
    if not chapter.pages:
        raise SystemExit(f"{pdf} extracted no text")

    blueprint = bp.for_paper(subject, grade)
    untopiced = not topics
    if untopiced:
        # No taxonomy tree for this chapter: set from the chapter as a whole,
        # with one item per section in proportion to the marks it carries. The
        # section shape still holds; only the topic tagging is lost, and that is
        # reported rather than hidden.
        plan = []
        for section in blueprint.sections:
            for _ in range(max(1, round(section.marks / mark_budget))):
                plan.append((section, ""))
    else:
        plan = cg.plan_for_chapter(subject, grade, topics, mark_budget)
    chapter_id = known.get("id") or tb.chapter_id(subject, grade, chapter_name)
    if not known:
        # No tree names this chapter, so the id is one nothing can resolve.
        # Recorded on the record so the gap is visible in the bank rather than
        # inferred later.
        pass

    kept: list[dict] = []
    refused: list[dict] = []
    usage = {"neurons": 0.0, "usd": 0.0, "calls": 0, "cached": 0,
             "prompt_tokens": 0, "completion_tokens": 0}
    by_section: dict[str, int] = {}

    pending = 0
    for index, group in enumerate(group_plan(plan, per_call=per_call), start=1):
        section = group[0][0]
        # One topic per group, the first in it; the schema pins section and marks,
        # and the model is told to make the questions differ.
        topic = group[0][1]
        chosen = model or model_for(section, tiered, provider)
        system, schema, user = cg.build_prompt(
            chapter, section, topic, count=len(group), bank_subject=subject,
            topics=topics)
        if bridge is not None:
            parsed = bridge_call(bridge, index, system, schema, user, section, topic)
            if parsed is None:
                pending += 1
                continue
            spent, chosen = {}, model or "opencode"
        elif delay:
            # Gemini's free tier is a few requests a minute. A corpus run is
            # thousands of calls, so the pacing is not a nicety.
            time.sleep(delay)
        if bridge is None:
            try:
                if provider == "gemini":
                    parsed, spent = call_gemini(system, schema, user, model=chosen)
                else:
                    parsed, spent = call_workers_ai(system, schema, user, model=chosen)
            except SystemExit as exc:
                refused.append({"section": section.key, "qtype": section.qtype,
                                "topic": topic, "reason": str(exc)})
                continue
        usage["calls"] += 1
        usage["neurons"] += float(spent.get("neurons") or 0.0)
        usage["usd"] += _cost_of(spent, chosen)
        usage["cached"] += int(spent.get("cached_tokens") or 0)
        usage.setdefault("usd", 0.0)
        usage["prompt_tokens"] += int(spent.get("prompt_tokens") or 0.0)
        usage["completion_tokens"] += int(spent.get("completion_tokens") or 0.0)

        for raw in parsed.get("questions") or []:
            item = cg.parse_item(raw)
            reason = cg.validate(item, section)
            if not reason and bridge is not None:
                reason = ungrounded(item, user)
            if reason:
                refused.append({"section": section.key, "qtype": section.qtype,
                                "topic": topic, "reason": reason,
                                "stem": (item.get("stem") or "")[:120]})
                continue
            # The id is built from this number. The model numbers a call's questions 1, 2, 3, so
            # two calls for one section both produced "...:D:1", and the second was dropped as a
            # duplicate id. Number them across the chapter's section instead.
            item["option"] = by_section.get(section.key, 0) + 1
            record = cg.to_record(
                item, section, chapter, topic, chapter_id=chapter_id,
                topic_id="", model=chosen)
            if bridge is not None:
                # It passed `ungrounded`: every quote is the chapter's own text. That is the
                # definition of the checked tier `textbook_grounded` (qbank_engine), and the
                # merge serves a model-written record only with this label and these quotes.
                quotes = item.get("evidence")
                quotes = [quotes] if isinstance(quotes, str) else list(quotes or [])
                scheme = record.setdefault("answerScheme", {})
                scheme["provenance"] = "textbook_grounded"
                scheme.setdefault("metadata", {})["evidence"] = [q for q in quotes if isinstance(q, str)]
            kept.append(record)
            by_section[section.key] = by_section.get(section.key, 0) + 1

    return kept, refused, {"usage": usage, "bySection": by_section, "pending": pending,
                           "topics": len(topics), "untopiced": untopiced,
                           "pages": len(chapter.page_numbers)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="NCERT book code, e.g. aejm1")
    ap.add_argument("--chapter", type=int, help="chapter number")
    ap.add_argument("--all", action="store_true", help="every chapter of --book")
    ap.add_argument("--limit", type=int, default=3, help="chapters with --all")
    ap.add_argument("--marks", type=int, default=12,
                    help="marks of paper to cover from this chapter")
    ap.add_argument("--provider", choices=["gemini", "workers"], default="gemini",
                    help="gemini: paid, ~1 cent per chapter. workers: the free tier")
    ap.add_argument("--model", default=None,
                    help="model id; the default depends on --provider")
    ap.add_argument("--no-tier", action="store_true",
                    help="use one model for every section")
    ap.add_argument("--delay", type=float, default=4.0,
                    help="seconds between calls; Gemini's free tier needs this")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true", help="generate, print, write nothing")
    ap.add_argument("--per-call", type=int, default=3,
                    help="questions asked for in one call")
    ap.add_argument("--bridge", type=Path, default=None,
                    help="folder of prompts (p###.json) and answers (r###.json) for a "
                         "model run elsewhere, e.g. an opencode session")
    args = ap.parse_args()

    if not args.book:
        ap.error("--book is required")

    if args.all:
        folder = BOOKS / args.book
        numbers = sorted(
            int(p.stem[len(args.book):]) for p in folder.glob(f"{args.book}*.pdf")
            if p.stem[len(args.book):].isdigit())
        chapters = numbers[:args.limit]
    elif args.chapter:
        chapters = [args.chapter]
    else:
        ap.error("--chapter or --all is required")

    records: list[dict] = []
    all_refusals: list[dict] = []
    totals = {"neurons": 0.0, "usd": 0.0, "calls": 0, "cached": 0}
    for number in chapters:
        kept, refused, meta = generate_chapter(
            args.book, number, mark_budget=args.marks, model=args.model,
            provider=args.provider, tiered=not args.no_tier, delay=args.delay,
            per_call=args.per_call, bridge=args.bridge and args.bridge / f"{args.book}-{number:02d}")
        records += kept
        all_refusals += refused
        totals["neurons"] += meta["usage"]["neurons"]
        totals["usd"] += meta["usage"].get("usd", 0.0)
        totals["cached"] += meta["usage"].get("cached", 0)
        totals["calls"] += meta["usage"]["calls"]
        print(f"ch{number:02d}  kept {len(kept):>3}  refused {len(refused):>3}  "
              f"pages {meta['pages']:>3}  topics {meta['topics']:>2}  "
              f"sections {meta['bySection']}"
              + (f"  PENDING {meta['pending']} calls" if meta.get("pending") else ""))

    # Workers AI reports neurons, Gemini reports dollars. Show whichever the run
    # actually spent, and both are 0 when the run failed before any call.
    if totals["usd"]:
        cached = totals.get("cached", 0)
        spend = ", $%.3f" % totals["usd"]
        if cached:
            spend += " (%d cached tokens)" % cached
    elif totals["neurons"]:
        spend = ", %.0f neurons" % totals["neurons"]
    else:
        spend = ""
    print(f"\n{len(records)} questions, {len(all_refusals)} refused, "
          f"{totals['calls']} calls{spend}")

    keys = cg.audit_key_distribution(records)
    if keys["total"]:
        spread = "  ".join("%s %d" % (k, keys["counts"][k])
                           for k in sorted(keys["counts"]))
        print(f"key position: {spread}"
              + ("   <- BIASED, retry or drop these"
                 if keys["biased"] else ""))

    if all_refusals:
        reasons: dict[str, int] = {}
        for refusal in all_refusals:
            reasons[refusal["reason"]] = reasons.get(refusal["reason"], 0) + 1
        print("refusals by reason:")
        for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
            print(f"   {count:>3}  {reason}")

    if records:
        print("\nfirst question:")
        print(json.dumps(records[0], ensure_ascii=False, indent=2)[:900])

    if args.check:
        print("\n--check: nothing written")
        return 1 if all_refusals else 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        {"questions": records, "refusals": all_refusals,
         "meta": {"model": args.model, "tiered": not args.no_tier,
                  "book": args.book,
                  "chapters": chapters, "markBudget": args.marks,
                  "neurons": totals["neurons"]}},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {len(records)} questions to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
