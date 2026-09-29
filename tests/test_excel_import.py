"""Excel for bulk import and export (INT-3): a workbook's first sheet imports
exactly like the same rows as CSV -- shared strings, numbers without ".0",
dates typed into Excel as dates -- and every export and template downloads
as .xlsx that imports back. Files that are not workbooks, or carry XML this
importer does not open, are refused with a reason."""
from __future__ import annotations

import base64
import io
import zipfile

from test_homework import w  # noqa: F401 - `w` is a fixture


def _excel_style_workbook() -> bytes:
    """What Excel itself writes: shared strings, a number, and a date stored
    as a serial number with a date format (numFmtId 14)."""
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/></Types>')
    book = ('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Holidays" sheetId="1" r:id="rId7"/></sheets></workbook>')
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/></Relationships>')
    styles = ('<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cellXfs count="2">'
              '<xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>')
    shared = ('<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<si><t>date</t></si><si><t>end_date</t></si><si><t>name</t></si><si><t>kind</t></si>'
              '<si><r><t>Diwali </t></r><r><t>break</t></r></si><si><t>holiday</t></si></sst>')
    # 46315 is 2026-10-20 and 46319 is 2026-10-24 in Excel's day numbering.
    sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c>'
             '<c r="D1" t="s"><v>3</v></c></row>'
             '<row r="3"><c r="A3" s="1"><v>46315</v></c><c r="B3" s="1"><v>46319</v></c><c r="C3" t="s"><v>4</v></c>'
             '<c r="D3" t="s"><v>5</v></c></row></sheetData></worksheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, body in (("[Content_Types].xml", ct), ("xl/workbook.xml", book), ("xl/_rels/workbook.xml.rels", rels),
                           ("xl/styles.xml", styles), ("xl/sharedStrings.xml", shared),
                           ("xl/worksheets/sheet1.xml", sheet)):
            z.writestr(name, body)
    return buf.getvalue()


def _imp(w, kind, data: bytes, dry=True):
    return w.c.post(f"/api/v1/admin/import/{kind}", params={"dryRun": str(dry).lower()},
                    json={"xlsx": base64.b64encode(data).decode(), "academicYearId": w.year}, headers=w.p)


def test_an_excel_sheet_imports_like_csv_with_real_dates(w):
    w.store.create_calendar(academic_year_id=w.year, weekly_off_days=["sunday"], alternate_saturday_rule="none")
    r = _imp(w, "holidays", _excel_style_workbook(), dry=False)
    assert r.status_code == 200, r.text
    [row] = r.json()["rows"]
    assert row["row"] == 3 and row["status"] == "ok", row
    cal = w.store.get_calendar_for_year(w.year)
    [h] = w.store.holidays_for_calendar(cal.id)
    assert (h.date, h.end_date, h.label, h.kind) == ("2026-10-20", "2026-10-24", "Diwali break", "holiday")


def test_exports_and_templates_download_as_excel_and_import_back(w):
    for kind in ("sections", "people", "allocations", "holidays", "timetable"):
        x = w.c.get(f"/api/v1/admin/export/{kind}", params={"format": "xlsx"}, headers=w.p)
        assert x.status_code == 200 and x.headers["content-disposition"].endswith(f'{kind}.xlsx"'), kind
        assert zipfile.ZipFile(io.BytesIO(x.content)).namelist(), kind
    t = w.c.get("/api/v1/admin/import/sections/template", params={"format": "xlsx"}, headers=w.p)
    assert t.headers["content-disposition"].endswith('sections-template.xlsx"')
    sections = w.c.get("/api/v1/admin/export/sections", params={"format": "xlsx"}, headers=w.p).content
    again = _imp(w, "sections", sections).json()
    assert again["rows"] and all(r["status"] == "skip" for r in again["rows"]), "an export imports back unchanged"
    assert w.c.get("/api/v1/admin/export/sections", params={"format": "ods"}, headers=w.p).status_code == 422


def test_what_the_excel_import_refuses(w):
    assert "not an Excel .xlsx file" in _imp(w, "sections", b"name,grade\n").json()["detail"]
    bomb = io.BytesIO()
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", b"<!DOCTYPE lol [<!ENTITY a 'aaaa'>]><workbook/>")
        z.writestr("xl/_rels/workbook.xml.rels", b"<Relationships/>")
    assert "XML this importer does not open" in _imp(w, "sections", bomb.getvalue()).json()["detail"]
    both = w.c.post("/api/v1/admin/import/sections", json={"csv": "grade,section\n", "xlsx": "AAAA"}, headers=w.p)
    assert both.status_code == 422 and "one of the two" in both.json()["detail"]
    broken = w.c.post("/api/v1/admin/import/sections", json={"xlsx": "not base64!"}, headers=w.p)
    assert broken.status_code == 422 and "did not arrive whole" in broken.json()["detail"]
