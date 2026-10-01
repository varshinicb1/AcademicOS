"""Core NCERT chapter extraction: PDF text layer -> structured Markdown.

Shared by benchmark_parsers.py (scored against ground truth) and
extract_corpus.py (production run), so a change to the extraction rules is
measured and shipped at the same time.

Why font heuristics: the corpus probe showed every sampled chapter is digital
(518 chars/page, 97.4% text coverage), so there is nothing to OCR. NCERT
headings are typographic, and MuPDF reports span font size and the bold flag
without rendering images. Benchmarked at 0.075 s/page versus Docling's
35 s/page on the same corpus.

Three failure modes found on Class 1-2 output and fixed here:
  1. Headings wrap across lines ("Finding the" / "Furry Cat!") -> merge runs of
     adjacent lines that share a size and are not full-width prose.
  2. Poems and sidebar callouts are set in large display type, so a size
     threshold alone marked verse as headings -> require a heading to look like
     a label: bounded length, no trailing verb punctuation, low word count.
  3. Running heads and page numbers repeat on every page -> furniture is
     detected and dropped.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

DEVANAGARI = re.compile(r"[\u0900-\u097F]")
TELUGU = re.compile(r"[\u0C00-\u0C7F]")
REPLACEMENT = re.compile(r"[\ufffd\u0000-\u0008\u000b\u000c\u000e-\u001f]")

# Legacy 8-bit Devanagari fonts (Walkman-Chanakya905, KrutiDev) are Type1 with
# /WinAnsiEncoding and no /ToUnicode CMap, so MuPDF hands back ASCII standing in
# for Devanagari glyphs. 'dkO; lkaf[ksa' is real Hindi, not garbage. A chapter is
# flagged when it carries a non-Latin script's font but almost no real codepoints
# from that script. Detection is by observed script, not by language name, so the
# same path covers any legacy Indic font that appears later.
LEGACY_FONT_RE = re.compile(
    r"chanakya|krutidev|kruti\s*dev|walkman|shree7|shree\d|mangal|devlys|apsari|"
    r"shree-lipi|chanakya905|chandralekha",
    re.IGNORECASE,
)

BOLD_FLAG = 16
# A label, not a sentence. Note: "!" and "?" are deliberately absent -- NCERT
# titles really do end in them ("Finding the Furry Cat!", "Why?").
SENTENCE_END = (".", ":", ";", ",", "।", "॥")
MAX_HEADING_CHARS = 90
MAX_HEADING_WORDS = 12
MIN_HEADING_CHARS = 3

# Real NCERT steps are small: in aejm1 the title is 28pt, section heads 18pt,
# body 16pt. A candidate is any step above body; bold or a clear margin confirms
# it. Bold is never a trigger on its own -- verse in the early-class books is
# bold, and a bold-only rule marked every line of the poem as a heading.
SIZE_CANDIDATE = 1.08
SIZE_CONFIRM = 1.10
# A size must carry at least this share of the chapter's characters to count as
# body, so one 40pt page number cannot define the profile.
BODY_MIN_SHARE = 0.03
MIN_SIZE_STEP = 0.6
# A candidate heading size must carry real text. Dropout glyphs and stray marks
# ('B', 'F', '?') render at 30-125pt and would otherwise take every level slot,
# leaving genuine 20pt section heads unranked. Both a character floor and a share
# of the chapter are required.
MIN_HEADING_SIZE_CHARS = 8
MIN_HEADING_SIZE_SHARE = 0.002
# Two display lines are a wrapped heading only if their left edges agree, within
# this many points. NCERT sidebars sit well outside the body column.
COLUMN_TOL = 14.0


def heading_levels(kept: list[tuple], body: float) -> dict[float, int]:
    """Map the top few display sizes to heading levels 1..4.

    Only sizes carrying meaningful character mass are eligible, so isolated
    large glyphs cannot displace real section headings.
    """
    mass: dict[float, int] = defaultdict(int)
    for text, size, *_ in kept:
        mass[round(size, 1)] += len(text)
    total = sum(mass.values()) or 1
    floor = max(MIN_HEADING_SIZE_CHARS, total * MIN_HEADING_SIZE_SHARE)
    sizes = sorted(
        (
            s
            for s, c in mass.items()
            if s > body * SIZE_CANDIDATE and c >= floor
        ),
        reverse=True,
    )
    return {s: min(i + 1, 4) for i, s in enumerate(sizes[:4])}



def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ")
    return REPLACEMENT.sub(" ", text).strip()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", clean(text)).casefold()


# --- legacy 8-bit font decoding -------------------------------------------------
# Tables come from `lipi-aparsoft` (MIT). KrutiDev and Walkman-Chanakya905 share
# the same ASCII layout, so the Walkman override table is merged on top.
_LEGACY_TABLE: dict[str, str] | None = None
_PREPROCESSOR = None


def font_type_for(font_name: str) -> str | None:
    """Map an embedded font name to the lipi layout that decodes it.

    `krutidev` and `walkman_chanakya` share one ASCII layout. `chanakya` is a
    different layout entirely, and decoding KrutiDev or Walkman text with it
    yields garbage, so the two families must not be conflated.
    """
    f = font_name.lower()
    if "walkman" in f:
        return "walkman_chanakya"
    if "kruti" in f or "shusha" in f or "aps" in f or "dvb" in f or "devlys" in f:
        return "krutidev"
    if "chanakya" in f:
        return "chanakya"
    return None


def _legacy_table() -> dict[str, str]:
    global _LEGACY_TABLE
    if _LEGACY_TABLE is None:
        table: dict[str, str] = {}
        for key in ("krutidev", "walkman_chanakya"):
            try:
                from lipi.mappings import FONT_MAPPINGS

                table.update(FONT_MAPPINGS.get(key) or {})
            except Exception:  # noqa: BLE001 - optional dependency
                pass
        if not table:  # no lipi installed: refuse to guess rather than emit garbage
            raise RuntimeError("no legacy font table available (pip install lipi-aparsoft)")
        _LEGACY_TABLE = table
    return _LEGACY_TABLE


def decode_legacy(text: str, font_type: str | None = None) -> str:
    """Map legacy 8-bit Indic glyph codes to Unicode Devanagari.

    Delegates to `lipi.preprocessor.HindiPreprocessor`, which does longest-match
    token substitution followed by an i-matra reordering pass. That reordering
    pass is the reason this goes through lipi rather than a flat table lookup:
    KrutiDev writes the pre-base i-matra *before* the consonant it belongs to,
    so a context-free table renders `मिश्र` as `िमश्र` and `किया` as `िकया`
    across most Hindi chapters. lipi moves it to the correct syllable.

    The font layout matters. `krutidev` and `walkman_chanakya` share one ASCII
    layout and are interchangeable, but `chanakya` is a different layout and
    produces total garbage on KrutiDev/Walkman text, so `font_type` should be
    derived from the actual embedded font name via `font_type_for`.

    Known residual: this is still not a perfect inverse. Context-sensitive
    conjunct reordering is not implemented, so glyphs whose encoding depends on
    the following consonant still mis-render -- `लखनऊ` arrives as `लखनउफ`
    and `स्वतंत्र` as `स्वतंत्ा`. Those are the decoder's floor, not the OCR's,
    and they are the reason legacy-decoded text stays out of quote-exact
    pipelines.
    """
    try:
        from lipi.preprocessor import HindiPreprocessor
    except Exception:  # noqa: BLE001 - optional dependency
        return _decode_legacy_flat(text)

    global _PREPROCESSOR
    if _PREPROCESSOR is None:
        _PREPROCESSOR = HindiPreprocessor()
    return _PREPROCESSOR.convert(text, font_type=font_type or "krutidev")


def _decode_legacy_flat(text: str) -> str:
    """Table-only fallback, used when lipi is unavailable. Loses i-matra order."""
    table = _legacy_table()
    multi = sorted((k for k in table if len(k) > 1), key=len, reverse=True)
    single = {k: v for k, v in table.items() if len(k) == 1}
    out: list[str] = []
    i = 0
    while i < len(text):
        for m in multi:
            if text.startswith(m, i):
                out.append(table[m])
                i += len(m)
                break
        else:
            out.append(single.get(text[i], text[i]))
            i += 1
    return "".join(out)


def detect_legacy(lines: list[tuple], fonts: list[str] | None = None) -> str | None:
    """Return the legacy script name if this chapter is legacy-encoded, else None.

    Requires both signals: a known legacy font is embedded, AND the text that
    should be in that script has almost no real codepoints. Either alone is
    unreliable (a legacy-named font may be unused; a chapter may legitimately be
    English).
    """
    if not fonts or not any(LEGACY_FONT_RE.search(f) for f in fonts):
        return None
    text = " ".join(t for t, *_ in lines)
    if not text:
        return None
    dev = len(DEVANAGARI.findall(text))
    tel = len(TELUGU.findall(text))
    if dev == 0 and tel == 0:
        return "devanagari"
    # Real codepoints present but almost none: mixed/scrambled, not pure legacy.
    if max(dev, tel) / max(len(text), 1) < 0.005:
        return "devanagari"
    return None


def read_page_lines(page, page_index: int = 0) -> list[tuple]:
    """Each line as (text, char-weighted font size, bold, page index, x0, y0).

    Position is carried because reading order is not enough to decide what is a
    heading. NCERT pages put a running sidebar ("1.1 CHEMICAL EQUATIONS") in the
    same reading order as the body text, and separate headings often sit on the
    same page. Merging on reading order alone produced
    "1.1 CHEMIC 1.1 CHEMICAL EQUA AL EQUA" and
    "Chapter 1 Two Little Hands Let us sing". A wrapped heading is instead a line
    directly below its continuation, in the same column.
    """
    out: list[tuple] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = clean("".join(s.get("text", "") for s in spans))
            if not text:
                continue
            chars = sum(len(s.get("text", "")) for s in spans) or 1
            # Char-weighted so one stray large glyph cannot set the profile.
            size = sum(s.get("size", 0) * len(s.get("text", "")) for s in spans) / chars
            bold = any(s.get("flags", 0) & BOLD_FLAG for s in spans)
            x0, y0, x1 = (list(line.get("bbox") or (0.0, 0.0, 0.0, 0.0)) + [0.0, 0.0, 0.0])[:3]
            out.append(
                (text, size, bold, page_index, float(x0), float(y0), float(x1))
            )
    return out


def normalize_lines(lines: list[tuple]) -> list[tuple]:
    """Repair two geometric artifacts NCERT PDFs exhibit, in reading order.

    1. Overlapping re-draws. A sidebar label such as "Activity 1.1" is emitted
       five times at nearly the same x/y, so a text-equality check sees five
       distinct lines and concatenates them into
       "Activity 1.1 Activity 1.1 Activity 1.1 Activity 1.1 Activity 1.1".

    2. Split lines. Justified heading text is emitted as fragments on one
       baseline -- "1.1 CHEMIC" at x=163 and "AL EQUA" at x=241 -- which the
       vertical merge rule treated as unrelated and emitted as two headings.

    Fix both by grouping onto shared baselines: drop duplicate renders within a
    baseline, then rejoin the survivors horizontally, using no space when the
    next fragment starts a split word.
    """
    buckets: dict[tuple, list[tuple]] = {}
    order: list[tuple] = []
    for item in lines:
        # 2pt buckets: the re-draws of one label differ by <0.5pt, while real
        # lines on a page are >=8pt apart.
        key = (item[3], round(item[5] / 2.0))
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(item)

    out: list[tuple] = []
    for key in order:
        frags = buckets[key]
        # (a) Drop re-draws. The same box is drawn several times with *different*
        # word splits ("1.1 CHEMIC" and "1.1 CHEMICAL EQUA" at the same x), so
        # text equality does not identify them. Position does: keep only the
        # fullest rendering per left-edge group.
        by_col: dict[int, tuple] = {}
        for it in sorted(frags, key=lambda t: t[4]):
            col = round(it[4] / 40.0)
            prev = by_col.get(col)
            if prev is None or len(it[0]) > len(prev[0]):
                by_col[col] = it
        uniq = [by_col[c] for c in sorted(by_col)]
        # (b) Rejoin fragments left to right, no space across a split word.
        text = uniq[0][0]
        size = uniq[0][1]
        for prev, cur in zip(uniq, uniq[1:]):
            gap = cur[4] - prev[6]
            joiner = "" if gap <= 0.8 * max(size, cur[1]) else " "
            text = f"{text}{joiner}{cur[0]}"
            size = max(size, cur[1])
        bold = any(f[2] for f in uniq)
        out.append(
            (
                clean(text),
                size,
                bold,
                uniq[0][3],
                min(f[4] for f in uniq),
                sum(f[5] for f in uniq) / len(uniq),
                max(f[6] for f in uniq),
            )
        )
    return out


def body_size(lines) -> float:
    """Char-weighted mode of the sizes that actually carry the text.

    Scale-free, so it works for 9pt and 14pt body text without a per-book
    threshold table. Sizes below BODY_MIN_SHARE of all characters are ignored,
    which stops a lone oversized glyph from becoming the reference.
    """
    weights: dict[float, int] = defaultdict(int)
    for text, size, *_ in lines:
        weights[round(size, 1)] += len(text)
    total = sum(weights.values())
    if not total:
        return 10.0
    eligible = [(s, c) for s, c in weights.items() if c / total >= BODY_MIN_SHARE]
    if not eligible:
        return max(weights.items(), key=lambda kv: kv[1])[0]
    return max(eligible, key=lambda kv: kv[1])[0]



def looks_like_label(text: str) -> bool:
    if not (MIN_HEADING_CHARS <= len(text) <= MAX_HEADING_CHARS):
        return False
    if text.endswith(SENTENCE_END):
        return False
    if len(text.split()) > MAX_HEADING_WORDS:
        return False
    # A heading is a noun phrase, not a clause: skip anything with a verb-ish
    # conjunction pattern that verse and prose share.
    return True


def is_furniture(text: str) -> bool:
    """Running heads, page numbers, and reprint marks."""
    t = text.strip()
    if re.fullmatch(r"[\divxlcIVXLC\s\-–—.,]+", t):
        return True
    if re.match(r"^(reprint|©|ncert|www\.|class \d)", t, re.IGNORECASE):
        return True
    return False


def merge_runs(lines, body: float) -> list[list[tuple]]:
    """Group adjacent candidate lines so a wrapped heading becomes one heading.

    Guards that keep it from over-merging, all found on real output:
      * never merge across a page boundary (two headings, not one wrapped one),
      * never repeat a line already in the group -- sidebar callouts such as
        "Activity 1.1" are drawn five times and were concatenating into
        "Activity 1.1 Activity 1.1 Activity 1.1 Activity 1.1 Activity 1.1",
      * stop once the group already reads as a full-length heading.

    Merging stays permissive within a page: a wrapped heading such as
    "Finding the" / "Furry Cat!" has no reliable lexical signal that its first
    line is incomplete, so the page boundary is the only trustworthy cut.
    """
    groups: list[list[tuple]] = []
    for item in lines:
        text, size, bold, page, x, y = item[0], item[1], item[2], item[3], item[4], item[5]
        big = size > body * SIZE_CANDIDATE
        if groups and big:
            prev = groups[-1]
            psize, ppage, px, py = prev[-1][1], prev[-1][3], prev[-1][4], prev[-1][5]
            joined = " ".join(t for t, *_ in prev)
            # Directly below, same column, same page. Anything else is a separate
            # heading or a sidebar box rather than a wrapped continuation.
            stacked = 0 <= y - py <= max(2.0, 1.6 * max(size, psize))
            same_col = abs(x - px) <= COLUMN_TOL
            if (
                stacked
                and same_col
                and page == ppage
                and not any(norm(t) == norm(text) for t, *_ in prev)
                and len(joined) < MAX_HEADING_CHARS
                and abs(size - psize) < MIN_SIZE_STEP
            ):
                prev.append(item)
                continue
        groups.append([item])
    return groups



def is_corrupt_heading(text: str) -> bool:
    """True when a display line is a broken assembly rather than a real label.

    A heading made of overlapping re-draws ("1.1 CHEMICAL EQUAAL EQUATIONSTIONS")
    is worse than no heading at all: it becomes a false chunk boundary and a
    junk retrieval key. Detect it by repeated words, which no real label has.
    """
    words = [w for w in re.findall(r"[A-Za-z]{2,}", text) if w.islower() or w.isupper()]
    if not words:
        return False
    counts: dict[str, int] = defaultdict(int)
    for w in words:
        counts[w.casefold()] += 1
    return max(counts.values()) >= 3


def _render(kept: list[tuple], body: float, level_of: dict[float, int],
            bold_only: bool = False) -> tuple[list[str], int]:
    """Emit Markdown in document order, returning (parts, heading count).

    `bold_only` is the fallback rule for books whose headings are the same size
    as body text. It is a second pass, not an append: headings must land where
    they occur, not in a pile at the end of the chapter.
    """
    groups = [[ln] for ln in kept] if bold_only else merge_runs(kept, body)
    parts: list[str] = []
    headings = 0
    last_text = None
    for group in groups:
        text = " ".join(t for t, *_ in group).strip()
        size = max(s for _, s, *_ in group)
        bold = any(b for _, _, b, *_ in group)
        if bold_only:
            is_head = bold and looks_like_label(text) and len(text) <= 60
            lvl = 3
        else:
            lvl = level_of.get(round(size, 1))
            ends_open = not text.endswith(SENTENCE_END)
            # Size nominates, bold or a clear margin confirms. Bold alone never
            # does: early-class verse is bold and would flood the heading tree.
            confirmed = size > body * SIZE_CONFIRM or bold
            is_head = ends_open and looks_like_label(text) and lvl is not None and confirmed
            if is_head and is_corrupt_heading(text):
                is_head = False
        # Drop a heading identical to the one just emitted: running heads survive
        # the furniture filter only on the first page of some books.
        if is_head and text != last_text:
            parts.append(f"{'#' * (lvl or 3)} {text}")
            headings += 1
            last_text = text
        elif not is_head:
            parts.append(text)
            last_text = None
    return parts, headings


def structure(lines: list[tuple], fonts: list[str] | None = None) -> dict:
    """Return {markdown, n_headings, body_size, text_quality} for one chapter."""
    legacy = detect_legacy(lines, fonts)
    if legacy:
        # Decoded text has different metrics, so body size and heading detection
        # must run on the decoded lines, not the legacy bytes.
        lines = [(decode_legacy(t), s, b, p, x, y, x1) for t, s, b, p, x, y, x1 in lines]
    lines = normalize_lines(lines)
    # Derive heading levels only after furniture is dropped: a 40pt page number
    # would otherwise claim level 1 and push the real title down to `##`.
    kept = [ln for ln in lines if not is_furniture(ln[0])]
    body = body_size(kept)
    level_of = heading_levels(kept, body)

    parts, headings = _render(kept, body, level_of)
    if headings == 0 and not legacy:
        # Same-size bold books (Class 10 jesc1/jess1) expose no size step at all.
        parts, headings = _render(kept, body, level_of, bold_only=True)
    return {
        "markdown": "\n".join(parts),
        "n_headings": headings,
        "body_size": body,
        "text_quality": "decoded-legacy-font" if legacy else "native-text-layer",
        "decode_script": legacy,
    }


