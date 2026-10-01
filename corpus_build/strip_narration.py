"""Strip Sarvam Vision narration and page furniture from the 38 OCR outputs.

Reads from `sarvam_ocr/`, writes to `sarvam_ocr_clean/`, and never modifies an
original. Every removal is written to an audit file with a reason, because the
failure mode here is silent: a corpus that looks plausible while quoting a
vision model's description of a cartoon instead of the textbook.

Three things this has to get right, each of which was measured first:

* Narration is written in the page's own language. The English books get
  "*This image contains a drawing of a plant...*" and the Hindi books get
  "*यह चित्र एक गुलाबी रंग की तस्वीर है...*". A detector that only knows the
  English form leaves every Hindi book untouched.
* Narration is not always one line. Vision wraps long descriptions across
  several lines, so the opening `*` is on the first line and the closing one
  several lines later. Matching line by line leaves the tail of the description
  behind as if it were body text.
* Some openers are real prose. "the picture related to the narration" is a
  textbook instruction fragment, not a description of a picture, and
  `NEVER_REMOVE` exists so the rule cannot eat it.
"""
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr")
DST = Path(r"D:\wt\tagfix\corpus_build\sarvam_ocr_clean")
AUDIT = Path(r"D:\wt\tagfix\corpus_build\ocr_strip_audit.md")

# --- what Vision says -------------------------------------------------------
# Word boundary that works for Devanagari. Python does not treat combining vowel
# signs (category Mn) as word characters, so `छवि\b` and `में\b` can never match:
# the boundary is tested after `ि`/`ं`, which Python sees as non-word, and there
# is no boundary between a non-word char and the space that follows. English
# alternatives are unaffected but use the same guard for symmetry.
NOT_DEVA = r"(?![ऀ-ॿ])"
NARRATION_OPENER = re.compile(
    r"^\s*\*?\s*(?:"
    r"this\s+(?:image|photo|picture|diagram|figure|illustration|page|chart|graph|map)\b"
    r"|the\s+(?:image|photo|picture|diagram|figure|illustration)\b"
    r"|an?\s+(?:image|photo|picture|diagram|figure)\s+(?:of|showing|depicting)\b"
    r"|image\s+(?:of|shows|showing|depicts|contains)\b"
    r"|(?:the\s+)?(?:picture|photograph)\s+(?:of|shows|showing)\b"
    rf"|यह\s+(?:चित्र|छवि|तस्वीर|चित्रण|पृष्ठ|रेखाचित्र|मानचित्र){NOT_DEVA}"
    rf"|इस\s+(?:चित्र|छवि|तस्वीर|चित्रण|पृष्ठ){NOT_DEVA}"
    rf"|उपरोक्त\s+(?:चित्र|छवि|तस्वीर|चित्रण){NOT_DEVA}"
    rf"|(?:चित्र|छवि|तस्वीर|चित्रण)\s+में{NOT_DEVA}"
    rf"|(?:ऊपर|नीचे|बाईं|दाईं|दाएँ)\s+(?:दिया|दिए|दिखाया)\s+गया\s+(?:चित्र|चित्रण){NOT_DEVA}"
    r")",
    re.I,
)
NO_TEXT_TAIL = re.compile(
    r"(इसमें\s+कोई\s+पाठ\s+नहीं|इस\s+चित्र\s+में\s+कोई\s+पाठ\s+नहीं"
    r"|इसमें\s+कोई\s+लिखित\s+पाठ\s+नहीं|no\s+text\s+in\s+the\s+image"
    r"|not\s+(?:a\s+)?text|no\s+text\s+to\s+transcribe"
    r"|no\s+readable\s+text|not\s+any\s+human-readable\s+text)",
    re.I,
)
# Textbook prose that begins like a narration opener. Checked before everything
# else so no rule below can remove it.
NEVER_REMOVE = re.compile(
    r"picture\s+related\s+to\s+the\s+narration|related\s+to\s+the\s+narration",
    re.I,
)

# --- page furniture ---------------------------------------------------------
REPRINT = re.compile(r"^\s*reprint\s+\d{4}\s*-\s*\d{2}\s*$", re.I)
PAGE_RULE = re.compile(r"^\s*-{3,}\s*$")
PAGE_CODE = re.compile(r"^\s*\d{3,4}\s*ch\s*\d{1,2}\s*$", re.I)
BARE_NUMBER_PAGE = re.compile(r"^\s*\d{1,4}\s*$")
# A description is at most a few lines. Past this, the asterisk is unbalanced and
# what follows is real text, not the tail of a description. Deliberately unused:
# `BARE_NUMBER_PAGE` is never applied, because a bare number in a maths textbook
# can be an exercise or step label, not a page number.
MAX_CONTINUATION = 6


@dataclass
class Removal:
    line_no: int
    reason: str
    text: str


@dataclass
class Stats:
    file: str
    lines_in: int = 0
    lines_out: int = 0
    chars_in: int = 0
    chars_out: int = 0
    dev_in: int = 0
    dev_out: int = 0
    words_in: int = 0
    words_out: int = 0
    removals: list[Removal] = field(default_factory=list)
    tables_converted: int = 0
    table_rows: int = 0


def strip_html_tables(lines: list[str], st: Stats) -> list[str]:
    """Flatten <table> markup to pipe-separated rows.

    The census found 73 tables and 2,572 HTML tags. They hold real data
    (temperature columns, element symbols) so they are converted, not deleted --
    dropping them would quietly lose the tabular content of six books.
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not re.match(r"^\s*<table\b", line, re.I):
            out.append(line)
            i += 1
            continue

        st.tables_converted += 1
        block = [line]
        i += 1
        while i < len(lines) and not re.match(r"^\s*</table>", lines[i], re.I):
            block.append(lines[i])
            i += 1
        if i < len(lines):
            block.append(lines[i])
            i += 1

        cells: list[str] = []
        for raw in block:
            for cell in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", raw, re.I | re.S):
                text = re.sub(r"<[^>]+>", " ", cell)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    cells.append(text)
            if not cells and re.search(r"</tr>", raw, re.I):
                cells.append("")
        if cells:
            st.table_rows += 1
            out.append("")
            out.append("| " + " | ".join(cells) + " |")
            out.append("")
        # A table with no cells at all is dropped; there is nothing to keep.
    return out


def dev_count(text: str) -> int:
    return sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x097F)


def body_words(text: str) -> int:
    """Count real words, ignoring markup, so text loss cannot pass unnoticed.

    Character counts move for boring reasons -- table flattening, blank-line
    collapsing -- so they are a poor guard. Word count is the thing that would
    actually fall if a regex ate a page of prose.
    """
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`#>|]", " ", text)
    return len(re.findall(r"[\wऀ-ॿ]+", text, re.UNICODE))


def strip_file(path: Path) -> tuple[str, Stats]:
    st = Stats(file=path.name)
    original = path.read_text(encoding="utf-8", errors="replace")
    st.chars_in = len(original)
    st.dev_in = dev_count(original)
    st.words_in = body_words(original)
    lines = original.splitlines()
    st.lines_in = len(lines)

    lines = strip_html_tables(lines, st)

    kept: list[str] = []
    continuation = 0  # lines consumed so far inside an open description
    in_narration = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        if in_narration:
            # Vision wraps long descriptions over several lines: the opening `*`
            # is on the first line and the closing one further down. Consume
            # only until the description closes, and bail out on a blank line or
            # a short cap. The books leave italic markers unbalanced (fegp1-ch10
            # has an odd asterisk count), so an unbounded `until it closes` loop
            # would delete real body text all the way to end of file.
            continuation += 1
            if stripped.endswith("*") or not stripped or continuation > MAX_CONTINUATION:
                in_narration = False
                continuation = 0
            continue

        if NEVER_REMOVE.search(line):
            kept.append(line)
            continue

        if (NARRATION_OPENER.match(line) or NO_TEXT_TAIL.search(line)):
            if (stripped.startswith("*") and not stripped.endswith("*")
                    and len(stripped) > 2 and stripped.count("*") == 1):
                in_narration = True
                continuation = 0
            st.removals.append(Removal(idx, "narration", stripped))
            continue

        if REPRINT.match(line):
            st.removals.append(Removal(idx, "reprint-stamp", stripped))
            continue
        if PAGE_RULE.match(line):
            st.removals.append(Removal(idx, "page-rule", stripped))
            continue
        if PAGE_CODE.match(line):
            st.removals.append(Removal(idx, "page-code", stripped))
            continue

        kept.append(line)

    # Collapse the blank-line runs that stripping leaves behind, and strip
    # trailing spaces.
    tidy: list[str] = []
    blanks = 0
    for line in kept:
        line = line.rstrip()
        if not line:
            blanks += 1
            if blanks > 1:
                continue
        else:
            blanks = 0
        tidy.append(line)
    while tidy and not tidy[-1]:
        tidy.pop()

    text = "\n".join(tidy) + "\n"
    st.lines_out = len(tidy)
    st.chars_out = len(text)
    st.dev_out = dev_count(text)
    st.words_out = body_words(text)
    return text, st


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC.glob("*.md"))
    stats: list[Stats] = []
    for path in files:
        text, st = strip_file(path)
        (DST / path.name).write_text(text, encoding="utf-8", newline="\n")
        stats.append(st)

    audit = ["# OCR strip audit\n",
             "Every removed line, with the rule that removed it.\n"]
    for st in stats:
        by_reason: dict[str, int] = {}
        for r in st.removals:
            by_reason[r.reason] = by_reason.get(r.reason, 0) + 1
        drop_pct = 1 - (st.chars_out / st.chars_in) if st.chars_in else 0
        audit.append(f"\n## {st.file}\n")
        audit.append(
            f"chars {st.chars_in} -> {st.chars_out} ({drop_pct:.1%} removed), "
            f"devanagari {st.dev_in} -> {st.dev_out}, "
            f"tables {st.tables_converted} ({st.table_rows} rows), "
            f"removals {by_reason}\n"
        )
        audit.append("| line | reason | text |")
        audit.append("|---:|---|---|")
        for r in st.removals:
            text = r.text.replace("|", "\\|")
            audit.append(f"| {r.line_no} | {r.reason} | {text[:160]} |")

    AUDIT.write_text("\n".join(audit) + "\n", encoding="utf-8")

    total_in = sum(s.chars_in for s in stats)
    total_out = sum(s.chars_out for s in stats)
    words_in = sum(s.words_in for s in stats)
    words_out = sum(s.words_out for s in stats)
    print(f"files            : {len(stats)}")
    print(f"chars            : {total_in} -> {total_out} "
          f"({1 - total_out / total_in:.1%} removed)")
    print(f"words            : {words_in} -> {words_out} "
          f"({1 - words_out / words_in:.1%} removed)")
    print(f"lines removed    : {sum(len(s.removals) for s in stats)}")
    print(f"tables converted : {sum(s.tables_converted for s in stats)} "
          f"({sum(s.table_rows for s in stats)} rows)")
    print()
    print(f"{'file':<14} {'chars in':>9} {'chars out':>9} {'removed':>8} "
          f"{'words in':>9} {'words out':>9} {'w%':>7} {'dev in':>8} {'dev out':>8}")
    for s in stats:
        drop = 1 - (s.chars_out / s.chars_in) if s.chars_in else 0
        wdrop = 1 - (s.words_out / s.words_in) if s.words_in else 0
        print(f"{s.file:<14} {s.chars_in:>9} {s.chars_out:>9} {drop:>7.1%} "
              f"{s.words_in:>9} {s.words_out:>9} {wdrop:>6.1%} "
              f"{s.dev_in:>8} {s.dev_out:>8}")
    print()
    print("words_kept_pct must be >= chars_removed_pct for every file: if more")
    print("words vanished than narration accounted for, a rule ate body text.")
    for s in stats:
        wdrop = 1 - (s.words_out / s.words_in) if s.words_in else 0
        cdrop = 1 - (s.chars_out / s.chars_in) if s.chars_in else 0
        if wdrop > cdrop + 0.10:
            print(f"  WARNING {s.file}: words -{wdrop:.0%} vs chars -{cdrop:.0%}")
    print()
    print(f"clean output : {DST}")
    print(f"audit        : {AUDIT}")
    json.dump(
        [{"file": s.file, "chars_in": s.chars_in, "chars_out": s.chars_out,
          "words_in": s.words_in, "words_out": s.words_out,
          "dev_in": s.dev_in, "dev_out": s.dev_out,
          "removals": len(s.removals), "tables": s.tables_converted}
         for s in stats],
        open(r"D:\wt\tagfix\corpus_build\ocr_strip_stats.json", "w", encoding="utf-8"),
        indent=1,
    )


if __name__ == "__main__":
    main()
