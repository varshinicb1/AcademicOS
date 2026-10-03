"""Make every class 9 and 10 CBSE paper from the served bank, and verify each one.

    python scripts/verify_papers.py                       # 5 subjects x classes 9, 10 x 4 exams
    python scripts/verify_papers.py --exams annual --grades 10 --pdf
    python scripts/verify_papers.py --json report.json    # the full report, for a gap-driven bank

Run it from the checkout whose bank you mean (the pool reads academicos-data/syllabus/questions.json
from the source tree). It boots the application in process against a throwaway data root, registers
a principal, and for each CBSE preset asks the real route (POST /papers/generate-from-template)
for a paper WITHOUT allowing gaps: a section the bank cannot fill is a 409 that names the gap, and
that is the report. A paper that comes back is held to its template by
assessment/paper_verify.py, and with --pdf its printed and answer-key PDFs are exported and read.

Exit 0 only when every cell is a verified paper.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SUBJECTS = ("english", "hindi", "mathematics", "science", "social-science")
EXAMS = ("unit_test", "periodic", "half_yearly", "annual")
KEY = "verify-papers-bootstrap-key-0123456789abcdef"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grades", default="9,10")
    ap.add_argument("--subjects", default=",".join(SUBJECTS))
    ap.add_argument("--exams", default=",".join(EXAMS))
    ap.add_argument("--pdf", action="store_true", help="also export and read each paper's PDF and answer key")
    ap.add_argument("--json", type=Path, help="write the full report here")
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="verify_papers_")
    os.environ["ACOS_DATA_ROOT"] = tmp
    os.environ["ACOS_PRINCIPAL_BOOTSTRAP_KEY"] = KEY
    os.environ.setdefault("ACOS_DISABLE_RATE_LIMIT", "1")
    from fastapi.testclient import TestClient

    from academicos.api.main import app
    from academicos.assessment import paper_verify, template_presets

    grades = [int(g) for g in args.grades.split(",")]
    subjects = args.subjects.split(",")
    exams = args.exams.split(",")
    tags = _paper_section_tags()
    available = {p.id: p for g in grades for p in template_presets.presets(grade=g)}
    wanted = [available[i] for g in grades for s in subjects for e in exams
              if (i := f"preset:cbse:{g}:{s}:{e}") in available]
    report = []
    with TestClient(app) as client:
        reg = client.post("/api/v1/auth/register", json={
            "name": "Verifier", "email": "verify@school.test", "password": "correct horse battery",
            "schoolId": "verify-school", "principalKey": KEY})
        reg.raise_for_status()
        auth = {"Authorization": f"Bearer {reg.json()['token']}"}
        for preset in wanted:
            slug = preset.id.split(":")[3]
            cell = {"template": preset.id, "grade": int(preset.id.split(":")[2]), "subject": slug,
                    "exam": preset.id.split(":")[4], "status": "", "problems": [], "gaps": []}
            r = client.post("/api/v1/papers/generate-from-template", headers=auth, json={"templateId": preset.id})
            if r.status_code == 409:
                detail = r.json().get("detail")
                cell["status"] = "short"
                cell["gaps"] = detail.get("gaps", []) if isinstance(detail, dict) else [str(detail)]
                cell["problems"] = [detail.get("message", "") if isinstance(detail, dict) else str(detail)]
            elif r.status_code != 200:
                cell["status"] = "error"
                cell["problems"] = [f"HTTP {r.status_code}: {r.text[:200]}"]
            else:
                paper = r.json()["paper"]
                cell["problems"] = paper_verify.verify(paper, preset, language="hi" if slug == "hindi" else "en",
                                                 tags=tags)
                if args.pdf and not cell["problems"]:
                    cell["problems"] += _check_pdfs(client, auth, paper, slug)
                cell["status"] = "verified" if not cell["problems"] else "defects"
            report.append(cell)
            print(f"{cell['status']:9s} class {cell['grade']:<2d} {slug:15s} {cell['exam']:12s} "
                  f"{len(cell['problems'])} problem(s)", flush=True)

    ok = sum(1 for c in report if c["status"] == "verified")
    print(f"\n{ok} of {len(report)} verified")
    for c in report:
        if c["status"] != "verified":
            print(f"\n{c['template']}: {c['status']}")
            for p in c["problems"][:6]:
                print(f"   - {p}")
            for g in c["gaps"][:8]:
                print(f"   gap: {g}")
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if ok == len(report) else 1


def _paper_section_tags() -> dict[str, str]:
    """question id -> `paperSection`, from the served bank this checkout would serve."""
    bank = ROOT / "academicos-data" / "syllabus" / "questions.json"
    data = json.loads(bank.read_text(encoding="utf-8"))
    records = data if isinstance(data, list) else data.get("questions", [])
    return {r["id"]: r["metadata"]["paperSection"] for r in records
            if (r.get("metadata") or {}).get("paperSection")}


def _check_pdfs(client, auth, paper: dict, slug: str) -> list[str]:
    """Export the printed paper and its answer key, and read them back."""
    import pymupdf

    problems: list[str] = []
    for fmt in ("pdf", "answer-key"):
        r = client.post(f"/api/v1/papers/{paper['id']}/export/{fmt}", headers=auth)
        if r.status_code != 200:
            problems.append(f"the {fmt} export answered HTTP {r.status_code}")
            continue
        url = r.json()["url"]
        f = client.get(url.replace("/api/v1", "/api/v1", 1), headers=auth)
        if f.status_code != 200 or not f.content.startswith(b"%PDF"):
            problems.append(f"the {fmt} file is not a PDF (HTTP {f.status_code})")
            continue
        with pymupdf.open(stream=f.content, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)
        if doc.page_count < 1 or len(text.strip()) < 200:
            problems.append(f"the {fmt} PDF has no readable text")
        if "�" in text:
            problems.append(f"the {fmt} PDF holds replacement characters")
        if slug == "hindi" and fmt == "pdf":
            dev = sum(1 for c in text if "ऀ" <= c <= "ॿ")
            if dev < 200:
                problems.append("the Hindi paper's PDF has no Devanagari text (a font that cannot print it)")
    return problems


if __name__ == "__main__":
    sys.exit(main())
