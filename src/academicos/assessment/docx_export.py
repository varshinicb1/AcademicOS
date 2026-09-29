"""A question paper as an editable Word document (EX-5, DOCX export).

The same paper the PDF prints -- the school's name, the exam, subject and
class, time and marks, the general instructions, each section with its
note, each question numbered with its marks at the right margin, options
(A)-(D), and an internal choice as "OR" -- written as a .docx a teacher can
open and change in Word or Google Docs. It uses the PDF's own helpers for
options, instructions and section notes, so the two cannot say different
things. Every page's footer carries the Q.P. code and the export's
traceable-copy id, as the PDF's does.

A .docx is a zip of a few XML parts; this writes them directly, with no new
dependency (python-docx is not in the image).
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape

from .pdf import DEFAULT_INSTRUCTIONS, _section_note, split_stem_and_options

# A4 with 18 mm margins, in twentieths of a point.
_PAGE_W, _PAGE_H, _MARGIN = 11906, 16838, 1020
_TEXT_W = _PAGE_W - 2 * _MARGIN
_NUMBER_W = 567                      # 1 cm for the question number

_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" ' \
     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


_XML_INVALID = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def _run(text: str, *, bold: bool = False, size: Optional[int] = None, italic: bool = False) -> str:
    text = _XML_INVALID.sub("", text)   # a control character from a scanned stem would corrupt the file
    props = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + (f'<w:sz w:val="{size}"/>' if size else "")
    parts = text.split("\t")
    body = '<w:tab/>'.join(f'<w:t xml:space="preserve">{escape(p)}</w:t>' for p in parts)
    return f"<w:r>{f'<w:rPr>{props}</w:rPr>' if props else ''}{body}</w:r>"


def _p(*runs: str, align: Optional[str] = None, space_after: int = 80, space_before: int = 0,
       indent: Optional[tuple[int, int]] = None, tabs: Optional[list[tuple[str, int]]] = None,
       keep_next: bool = False, border_bottom: bool = False) -> str:
    props = ""
    if keep_next:
        props += "<w:keepNext/>"
    if border_bottom:
        props += '<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="1" w:color="000000"/></w:pBdr>'
    if tabs:
        props += "<w:tabs>" + "".join(f'<w:tab w:val="{k}" w:pos="{pos}"/>' for k, pos in tabs) + "</w:tabs>"
    props += f'<w:spacing w:before="{space_before}" w:after="{space_after}"/>'
    if indent:
        props += f'<w:ind w:left="{indent[0]}" w:hanging="{indent[1]}"/>'
    if align:
        props += f'<w:jc w:val="{align}"/>'
    return f"<w:p><w:pPr>{props}</w:pPr>{''.join(runs)}</w:p>"


def _question(gq) -> list[str]:
    """One question: number, stem, marks at the right margin; options and
    an OR choice below, indented under the stem."""
    split_head, split_options = split_stem_and_options(gq.stem)
    objective = gq.type in ("", "mcq", "assertion_reason") or (gq.marks == 1 and len(split_options) == 4)
    head, options = (split_head, split_options) if objective else (gq.stem.strip(), [])
    tabs = [("left", _NUMBER_W), ("right", _TEXT_W)]
    lines = head.splitlines() or [""]
    out = [_p(_run(f"{gq.display_number}.", bold=True), _run("\t" + lines[0] + f"\t[{gq.marks}]"),
              tabs=tabs, indent=(_NUMBER_W, _NUMBER_W), space_after=60, space_before=160)]
    out += [_p(_run(line), indent=(_NUMBER_W, 0), space_after=60) for line in lines[1:]]
    for i, opt in enumerate(options):
        out.append(_p(_run(f"({chr(ord('A') + i)})  {opt}"), indent=(_NUMBER_W * 2, _NUMBER_W), space_after=40))
    if gq.internal_choice_text:
        out.append(_p(_run("OR", bold=True), align="center", space_after=60))
        out.append(_p(_run(gq.internal_choice_text), indent=(_NUMBER_W, 0), space_after=60))
    return out


def _body(paper, template) -> str:
    m = paper.metadata
    school = (m.school_name or (template.name if template and template.name else "") or "AcademicOS School")
    paras = [_p(_run(school, bold=True, size=32), align="center", space_after=40)]
    if m.exam_name and m.exam_name != m.assessment_title:
        paras.append(_p(_run(m.exam_name, bold=True, size=26), align="center", space_after=40))
    title = m.assessment_title + (f"  |  SET {paper.set_label}" if paper.set_label else "")
    paras.append(_p(_run(title, bold=True, size=26), align="center", space_after=40))
    paras.append(_p(_run(f"Subject: {m.subject}  |  Class: {m.grade}"), align="center", space_after=40))
    if template and template.tagline:
        paras.append(_p(_run(template.tagline, italic=True), align="center", space_after=40))
    if m.date_line:
        paras.append(_p(_run(m.date_line), align="center", space_after=40))
    paras.append(_p(_run("Roll No.: ____________        Name: ______________________________"), space_after=120))
    marks = f"Maximum Marks: {m.total_marks}" + (f"   [SET {paper.set_label}]" if paper.set_label else "")
    paras.append(_p(_run(f"Time Allowed: {m.duration_minutes // 60} hours {m.duration_minutes % 60:02d} minutes",
                         bold=True), _run("\t" + marks, bold=True),
                    tabs=[("right", _TEXT_W)], border_bottom=True, space_after=160))

    paras.append(_p(_run("General Instructions:", bold=True), space_after=60, keep_next=True))
    teacher = [line.strip() for line in (m.instructions or "").splitlines() if line.strip()]
    if teacher:
        lines = teacher
    else:
        total_q = sum(len(s.questions) for s in paper.sections)
        labels = ", ".join(s.label for s in paper.sections)
        lines = [t.format(n=total_q, sections=len(paper.sections), labels=labels) for t in DEFAULT_INSTRUCTIONS]
    for i, line in enumerate(lines, start=1):
        paras.append(_p(_run(f"({i})\t{_plain(line)}"), tabs=[("left", _NUMBER_W)], indent=(_NUMBER_W, _NUMBER_W),
                        space_after=40))

    for section in paper.sections:
        paras.append(_p(_run(f"SECTION {section.label}", bold=True, size=26), align="center", space_after=40,
                        keep_next=True))
        paras.append(_p(_run(f"({section.name} — {len(section.questions)} questions, {section.total_marks} marks. "
                             f"This section {_section_note(section)})", italic=True), align="center",
                        space_after=160, keep_next=True))
        for gq in section.questions:
            paras += _question(gq)
    sect = (f'<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/>'
            f'<w:pgSz w:w="{_PAGE_W}" w:h="{_PAGE_H}"/>'
            f'<w:pgMar w:top="{_MARGIN}" w:right="{_MARGIN}" w:bottom="{_MARGIN}" w:left="{_MARGIN}" '
            f'w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {_W}><w:body>'
            + "".join(paras) + sect + "</w:body></w:document>")


def _plain(markup: str) -> str:
    """DEFAULT_INSTRUCTIONS carry the PDF's inline tags; Word gets the text."""
    import re
    return re.sub(r"<[^>]+>", "", markup).replace("&nbsp;", " ").replace("&amp;", "&")


def _footer(paper, template, watermark_id: Optional[str]) -> str:
    code = paper.id.replace("paper_", "").upper()[:10]
    school = template.name if template and template.name else "AcademicOS"
    lines = [_p(_run(f"{school}  ·  Q.P. Code {code}", size=15), align="center", space_after=0)]
    if watermark_id:
        lines.append(_p(_run(f"Confidential — traceable copy {watermark_id}", size=12), align="center", space_after=0))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {_W}>' + "".join(lines) + "</w:ftr>")


def export_docx(paper, output_dir: Path, template=None, watermark_id: Optional[str] = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{paper.id}.docx"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                   '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                   '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                   '</Relationships>')
        z.writestr("docProps/core.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                   'xmlns:dc="http://purl.org/dc/elements/1.1/">'
                   f'<dc:title>{escape(paper.metadata.assessment_title)}</dc:title><dc:creator>AcademicOS</dc:creator>'
                   '</cp:coreProperties>')
        z.writestr("word/_rels/document.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
                   '</Relationships>')
        z.writestr("word/document.xml", _body(paper, template))
        z.writestr("word/footer1.xml", _footer(paper, template, watermark_id))
    out_path.write_bytes(buf.getvalue())
    return out_path
