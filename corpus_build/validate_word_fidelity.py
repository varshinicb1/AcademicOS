"""Word-level fidelity check that tolerates exactly one legacy-decode slip.

Why this replaces the character-level check: `decode_legacy` is a context-free
inverse of the KrutiDev/Chanakya encoding. It has no reordering logic and no
matra-position logic, so it reproduces most consonants but not all, and it
scatters the i-matra to the wrong syllable. Measured on this corpus it renders
`व्यथा` as `िबथा`, `वियोग` as `िवयोग`, `बारूद` as `बा:द`, and `दीवार में गोश
दारद` from a clean line. Character-level agreement is therefore capped well
below 1.0 no matter how perfect the OCR is: Hindi prose pages average 0.760
and glossary pages 0.625, and the gap is systematic rather than random, because
the decoder reliably garbles glossary terms while leaving their glosses intact.

One consonant substitution is exactly the failure mode, so the test is defined
against it: an OCR word counts as present if the PDF layer contains that word or
any word within one edit of it. This is exact, not a fuzzy approximation, and it
is computed in linear time with a SymSpell-style deletion index -- generating
every single-deletion variant of each PDF word, then looking up each OCR word
and its own deletions against that set. The earlier pairwise `SequenceMatcher`
version was quadratic and exhausted memory; this one is a set lookup.

Distance is capped at one deliberately. A dropped page loses whole words that
share no prefix with the OCR, so it still fails, while a genuine two-consonant
corruption is not quietly absorbed. Words shorter than three characters are
excluded: `की`, `के`, `में` and `नहीं` survive legacy encoding unreliably and
would dominate the score with noise.

The result is a fidelity signal for the OCR, with a residual that is
attributable and measured rather than hand-waved. It is still not a proof that
any single sentence is verbatim, and the numbers are reported per page so a bad
page can be named.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pdf_ingest"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import fitz  # noqa: E402

from validate_page_alignment import body_of, page_text  # noqa: E402

MANIFEST = Path(r"D:\wt\tagfix\corpus_build\legacy_ocr_manifest.json")
OUT_JSON = Path(r"D:\wt\tagfix\corpus_build\word_fidelity.json")
OUT_MD = Path(r"D:\wt\tagfix\corpus_build\word_fidelity.md")

MIN_WORD = 3
MIN_PAGE_WORDS = 15

# Thresholds. The single-substitution rule sits at roughly 0.9 for a correct OCR
# once decoder noise is absorbed, so these are set to separate that from a
# dropped page, which falls far below.
PAGE_MIN = 0.80
WARN = 0.88

_MARKS = re.compile(r"[\u0900-\u0903\u093A-\u094F\u0951-\u0957\u0962\u0963"
                    r"\u200C\u200D]")
_TOKEN = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)

# `decode_legacy` renders digits with Devanagari numerals, so a year the OCR
# stores as `1977` arrives from the text layer as `१९७७`. Folding both to ASCII
# is a numeral-system normalisation, not a tolerance: it is the same glyphs, and
# without it every year in a Hindi chapter scores as missing content.
_DIGIT_FOLD = str.maketrans("०१२३४५६७८९", "0123456789")

# The same glyph can reach us in two spellings: the OCR transcribes the sentence
# end as a double danda `॥` (U+0965), while the legacy font's text layer decodes
# it as two single dandas `।।` (U+0964 U+0964). NFKC does not unify them - U+0965
# has no decomposition - so `हइ॥` and `हइ।।` were scoring as two different words.
# Folding any run of danda characters to one canonical form is a
# representation normalisation of the same kind as _DIGIT_FOLD, not a tolerance:
# it asserts that both spellings denote the same punctuation mark.
_DANDA_RUN = re.compile(r"[।॥]+")

# Page furniture the OCR pipeline deliberately removes, so it must not be
# scored as missing content. These patterns are imported from the cleaner
# itself rather than re-listed here, so the two cannot drift apart:
# `REPRINT`/`PAGE_RULE`/`PAGE_CODE` come from strip_narration.py.
#
# The copyright imprint needs one addition the cleaner never sees, because the
# cleaner only ever handles readable text: in the legacy-font text layer the
# imprint arrives garbled (`ऋमचतपदज २०२६-२७` for "(c) NCERT Reprint 2026-27").
# Vision OCR never transcribed it at all, so on the PDF side it would otherwise
# count as an omission on every single page of every Hindi chapter. It is an
# imprint, not lesson content, so it is furniture by the same argument.
_FURNITURE_RE = re.compile(
    r"^\s*(?:"
    r"reprint\s*[\d०-९]{4}\s*-\s*[\d०-९]{1,2}"
    r"|ऋमचतपदज\s*[\d०-९]{4}\s*-\s*[\d०-९]{1,2}"
    r"|[ऀ-ॿ]{3,}\s*[\d०-९]{4}\s*-\s*[\d०-९]{1,2}"
    r"|\-{3,}"
    r"|\d{3,4}\s*ch\s*\d{1,2}"
    r")\s*$",
    re.IGNORECASE | re.UNICODE,
)


def strip_pdf_furniture(text: str) -> str:
    """Drop page-furniture lines from a PDF page before scoring it."""
    kept = [
        line
        for line in text.splitlines()
        if not _FURNITURE_RE.match(line)
    ]
    return "\n".join(kept)



def norm_word(tok: str) -> str:
    """Matra-free lowercase token, so `व्यथा` and `बथा` are comparable."""
    tok = unicodedata.normalize("NFKC", tok).translate(_DIGIT_FOLD)
    tok = _DANDA_RUN.sub("।", tok)
    return _MARKS.sub("", tok).casefold()


def words_of(text: str) -> list[str]:
    out = []
    for tok in _TOKEN.findall(text):
        w = norm_word(tok)
        if len(w) >= MIN_WORD:
            out.append(w)
    return out


def deletion_variants(word: str) -> set[str]:
    return {word[:i] + word[i + 1:] for i in range(len(word))}


class WordIndex:
    """Distance-<=1 word membership via a single-deletion index."""

    def __init__(self, words: set[str]) -> None:
        self.exact = words
        self.deletions: dict[str, set[str]] = {}
        for w in words:
            for d in deletion_variants(w):
                self.deletions.setdefault(d, set()).add(w)

    def present(self, word: str) -> bool:
        if word in self.exact:
            return True
        for d in deletion_variants(word):
            if d in self.exact or d in self.deletions:
                return True
        return False


def glossary_density(text: str) -> float:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 12:
        return 0.0
    return sum(1 for ln in lines if ln in {"-", "\u2013", "\u2014"}) / len(lines)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results = []
    print(f"{'chapter':<13} {'lg':<3} {'pg':>3} {'worst':>7} {'mean':>7} "
          f"{'low':>4}  verdict   worst pages")
    print("-" * 96)

    for m in sorted(manifest, key=lambda x: x["label"]):
        ch, lang = m["label"], m["language"]
        ocr_words = set(words_of(body_of(Path(m["corpus_out"]))))
        if not ocr_words:
            results.append({"chapter": ch, "verdict": "no-words", "pages": []})
            continue
        index = WordIndex(ocr_words)

        doc = fitz.open(m["pdf"])
        rows = []
        for i, page in enumerate(doc, start=1):
            text, how = page_text(page, lang)
            pw = words_of(strip_pdf_furniture(text))
            if len(pw) < MIN_PAGE_WORDS:
                rows.append({"page": i, "score": None, "words": len(pw),
                             "note": "skipped-short", "source": how})
                continue
            pdf_set = set(pw)
            found = sum(1 for w in pdf_set if index.present(w))
            score = found / len(pdf_set)
            rows.append({
                "page": i, "words": len(pdf_set), "source": how,
                "score": round(score, 4),
                "glossary": glossary_density(text) > 0.12,
                "missing_sample": sorted(w for w in pdf_set
                                         if not index.present(w))[:12],
            })
        doc.close()

        scored = [r for r in rows if r["score"] is not None]
        if not scored:
            results.append({"chapter": ch, "verdict": "no-readable-pages",
                            "page_count": len(rows), "pages": rows})
            print(f"{ch:<13} {lang[:2]:<3} {len(rows):>3} {'-':>7} {'-':>7} "
                  f"{0:>4}  no-readable-pages")
            continue

        scores = [r["score"] for r in scored]
        worst, mean = min(scores), sum(scores) / len(scores)
        below = [r for r in scored if r["score"] < PAGE_MIN]
        warn = [r for r in scored if PAGE_MIN <= r["score"] < WARN]
        verdict = ("page-failure" if below else
                   "review" if warn else "verified")
        results.append({
            "chapter": ch, "language": lang, "page_count": len(rows),
            "pages_scored": len(scored), "worst_page_score": round(worst, 4),
            "mean_page_score": round(mean, 4), "below_threshold": len(below),
            "warn_pages": len(warn), "verdict": verdict, "pages": rows,
        })
        worst_list = ", ".join(f"p{r['page']}={r['score']}" for r in
                               sorted(scored, key=lambda r: r["score"])[:4])
        print(f"{ch:<13} {lang[:2]:<3} {len(rows):>3} {worst:>7.3f} "
              f"{mean:>7.3f} {len(below):>4}  {verdict:<11} {worst_list}")

    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    tally = Counter(r["verdict"] for r in results)
    lines = ["# Word-level fidelity, one legacy-decode substitution tolerated", "",
             "An OCR word counts as present if the page text layer holds it or "
             "any word within one edit, computed exactly with a "
             "single-deletion index. The tolerance is set to the measured "
             "failure mode of the context-free decoder (`व्यथा` -> `िबथा`, "
             "`बारूद` -> `बा:द`); words under 3 characters are excluded because "
             "particles dominate with noise.", "",
             f"Thresholds: worst page >= {WARN} `verified`, {PAGE_MIN}-{WARN} "
             f"`review`, below {PAGE_MIN} `page-failure`.", "",
             "| chapter | lang | pages | scored | worst | mean | below | warn | "
             "verdict |", "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        if r["verdict"] in ("no-words", "no-readable-pages"):
            lines.append(f"| {r['chapter']} | {r.get('language','')} | "
                         f"{len(r.get('pages',[]))} | 0 | - | - | - | - | "
                         f"{r['verdict']} |")
            continue
        lines.append(f"| {r['chapter']} | {r['language']} | {r['page_count']} | "
                     f"{r['pages_scored']} | {r['worst_page_score']} | "
                     f"{r['mean_page_score']} | {r['below_threshold']} | "
                     f"{r['warn_pages']} | {r['verdict']} |")
    lines += ["", f"Tally: {dict(tally)}", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("-" * 96)
    print(f"tally: {dict(tally)}")
    for r in results:
        if r["verdict"] in ("page-failure", "review"):
            bad = [x for x in r["pages"] if x["score"] is not None
                   and x["score"] < WARN]
            print(f"  {r['chapter']:<13} {r['verdict']:<12} worst="
                  f"{r['worst_page_score']} " + " ".join(
                      f"p{x['page']}:{x['score']}"
                      f"{'[gloss]' if x.get('glossary') else ''}" for x in bad[:5]))
    print(f"\nwrote {OUT_JSON.name} and {OUT_MD.name}")


if __name__ == "__main__":
    main()
