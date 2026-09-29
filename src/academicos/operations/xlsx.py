"""A small Excel (.xlsx) writer: named sheets of rows, the first row bold.

The reports need a file a principal can open in Excel, and nothing more
than cells: text and numbers, no formulas, no formatting beyond a header.
openpyxl is not a dependency of the deployed image, and an .xlsx is a zip of
a few XML parts, so this writes them directly. Text goes in as inline
strings, escaped; a cell that would start a formula (=, +, -, @) is kept as
text, so a name like "=HYPERLINK(...)" typed into the school's data cannot
run when the file is opened.
"""
from __future__ import annotations

import io
import zipfile
from typing import Any, Iterable, Sequence
from xml.sax.saxutils import escape

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
{sheets}
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>
</styleSheet>"""


def _col(i: int) -> str:
    name = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        name = chr(65 + r) + name
    return name


def _cell(ref: str, value: Any, bold: bool) -> str:
    style = ' s="1"' if bold else ""
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        value = "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"{style}><v>{value}</v></c>'
    text = str(value)
    if text.startswith(_FORMULA_START):
        text = "'" + text
    return f'<c r="{ref}"{style} t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'


def _sheet(rows: Iterable[Sequence[Any]]) -> str:
    out = []
    for r, row in enumerate(rows, start=1):
        cells = "".join(_cell(f"{_col(c)}{r}", v, r == 1) for c, v in enumerate(row))
        out.append(f'<row r="{r}">{cells}</row>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(out)}</sheetData></worksheet>')


def _sheet_name(name: str, taken: set[str]) -> str:
    clean = "".join(ch for ch in name if ch not in '[]:*?/\\')[:31] or "Sheet"
    base, n = clean, 2
    while clean.casefold() in taken:
        suffix = f" ({n})"
        clean, n = base[:31 - len(suffix)] + suffix, n + 1
    taken.add(clean.casefold())
    return clean


def workbook(sheets: Sequence[tuple[str, Sequence[Sequence[Any]]]]) -> bytes:
    """An .xlsx with one sheet per (name, rows); each first row is bold."""
    if not sheets:
        sheets = [("Sheet", [])]
    taken: set[str] = set()
    names = [_sheet_name(n, taken) for n, _ in sheets]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES.format(sheets="".join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, len(sheets) + 1))))
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(n, {chr(34): "&quot;"})}" sheetId="{i}" r:id="rId{i}"/>'
                             for i, n in enumerate(names, start=1))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i}" '
                             'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                             f'Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1))
                   + f'<Relationship Id="rId{len(sheets) + 1}" '
                     'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                     'Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", _STYLES)
        for i, (_, rows) in enumerate(sheets, start=1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet(rows))
    return buf.getvalue()
