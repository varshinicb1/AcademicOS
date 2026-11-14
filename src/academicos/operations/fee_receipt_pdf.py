"""A printable fee receipt (FEE-1): one A5 page with the school's own name,
logo and brand colour, the receipt number, the student, the fee, the amount
and how it was paid. A reversed payment prints with the cancellation and its
reason, so a parent holding the old copy can tell it no longer stands.

Built in memory and returned as bytes: a receipt names a student, so it is
never written to disk where erasure would have to find it.
"""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Image, SimpleDocTemplate, Spacer, Table, TableStyle

from ..assessment import pdf as pdf_export

METHOD_LABELS = {"cash": "Cash", "cheque": "Cheque", "bank": "Bank transfer", "upi": "UPI", "other": "Other"}


def _day(iso: str) -> str:
    try:
        return date.fromisoformat(iso[:10]).strftime("%d %b %Y")
    except ValueError:
        return iso


def receipt_pdf(*, receipt: dict, student_name: str, class_name: str, fee_name: str, recorded_by: str,
                amount: str, template=None) -> bytes:
    """`receipt` is a payment row with its reversal fields
    (`OperationsStore.get_fee_payment`); `amount` is already formatted."""
    pdf_export._register_unicode_font()
    body_font, bold_font = pdf_export._BODY_FONT, pdf_export._BODY_FONT_BOLD
    brand = colors.HexColor(template.brand_color) if template is not None and getattr(template, "brand_color", None) \
        else colors.black
    ss = getSampleStyleSheet()
    st = {
        "school": ParagraphStyle("FSchool", parent=ss["Title"], fontName=bold_font, fontSize=14, leading=17,
                                 textColor=brand, alignment=TA_CENTER, spaceAfter=0),
        "title": ParagraphStyle("FTitle", parent=ss["Normal"], fontName=bold_font, fontSize=12,
                                alignment=TA_CENTER, spaceBefore=4),
        "label": ParagraphStyle("FLabel", parent=ss["Normal"], fontName=body_font, fontSize=9,
                                textColor=colors.HexColor("#555555")),
        "value": ParagraphStyle("FValue", parent=ss["Normal"], fontName=body_font, fontSize=10.5, leading=13),
        "amount": ParagraphStyle("FAmount", parent=ss["Normal"], fontName=bold_font, fontSize=14, leading=17),
        "cancelled": ParagraphStyle("FCancel", parent=ss["Normal"], fontName=bold_font, fontSize=11, leading=14,
                                    textColor=colors.HexColor("#B00020"), alignment=TA_CENTER),
        "small": ParagraphStyle("FSmall", parent=ss["Normal"], fontName=body_font, fontSize=8,
                                textColor=colors.HexColor("#666666"), alignment=TA_CENTER),
    }
    P, esc = pdf_export.Paragraph, pdf_export.escape

    buf = io.BytesIO()
    margin = 12 * mm
    doc = SimpleDocTemplate(buf, pagesize=A5, leftMargin=margin, rightMargin=margin, topMargin=margin,
                            bottomMargin=margin, title=f"Receipt {receipt['receipt_no']}")
    width = A5[0] - 2 * margin
    story: list = []

    school = pdf_export.printable_school_name(None, template)
    heading = [*([P(esc(school), st["school"])] if school else []), P("Fee receipt", st["title"])]
    from ..curriculum.school_profile import printable_logo
    logo_url = getattr(template, "logo_url", None) if template is not None else None
    logo = printable_logo(Path(logo_url) if logo_url else None)
    if logo:
        band = Table([[Image(str(logo), width=14 * mm, height=14 * mm), heading]], colWidths=[18 * mm, width - 18 * mm])
        band.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(band)
    else:
        story.extend(heading)
    story += [Spacer(1, 4), HRFlowable(width="100%", thickness=1.2, color=brand, spaceAfter=8)]

    if receipt.get("reversed_at"):
        story += [P(esc(f"CANCELLED on {_day(receipt['reversed_at'])}: {receipt.get('reversal_reason') or ''}"),
                    st["cancelled"]), Spacer(1, 8)]

    rows = [
        ("Receipt no.", str(receipt["receipt_no"])),
        ("Date paid", _day(receipt["paid_on"])),
        ("Student", student_name + (f", class {class_name}" if class_name else "")),
        ("For", fee_name),
        ("Paid by", METHOD_LABELS.get(receipt["method"], receipt["method"])
         + (f" ({receipt['reference']})" if receipt.get("reference") else "")),
    ]
    table = Table([[P(esc(k), st["label"]), P(esc(v), st["value"])] for k, v in rows]
                  + [[P("Amount received", st["label"]), P(esc(amount), st["amount"])]],
                  colWidths=[32 * mm, width - 32 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEABOVE", (0, len(rows)), (-1, len(rows)), 0.6, colors.HexColor("#BBBBBB")),
        ("TOPPADDING", (0, len(rows)), (-1, len(rows)), 8),
    ]))
    story += [table, Spacer(1, 14),
              P(esc(f"Recorded by {recorded_by} on {_day(receipt['recorded_at'])}."), st["small"])]
    doc.build(story)
    return buf.getvalue()
