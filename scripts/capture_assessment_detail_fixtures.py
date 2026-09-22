"""Capture the three API responses the teacher's assessment detail screen reads.

Why this exists: `AssessmentReviewPage` reopens an assessment with
`GET /assessments/{id}` + `GET /papers/{paperId}` and parses both with the
shared models, while the paper builder parses the *same* paper through
`paper_builder_api.parsePaper`, which patches the JSON first. The two paths
drifted -- a template-generated paper has `metadata.schoolName: null`, which
only the patched path survived -- so the fix is pinned by a test that replays
the real bodies. A body written by hand would agree with the model by
construction and prove nothing, so these files are what the real backend
answered, in-process, on a temp data root with the real served bank
(academicos-data/syllabus/questions.json, read-only).

The captured flow is the one the bug was found on: sign in as a teacher who
joined by invite, take the "Class 10 Mathematics - Unit Test" CBSE preset,
generate a paper from it, then read the assessment and the paper back.

Run from the repo root (outside pytest -- under pytest the served bank is
deliberately not loaded, see pool.build_pool):

    PYTHONPATH=src PYTHONIOENCODING=utf-8 python scripts/capture_assessment_detail_fixtures.py

Writes frontend/test/assessment_detail/fixtures/*.json and a manifest.json
recording each request and its status.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "test" / "assessment_detail" / "fixtures"

SCHOOL = "school_demo_detail"
BOOTSTRAP_KEY = "capture-assessment-detail-local-key"
PASSWORD = "demo-pass-801"


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="acos_assessment_detail_"))
    os.environ["ACOS_DATA_ROOT"] = str(tmp)
    os.environ["ACOS_DISABLE_RATE_LIMIT"] = "1"
    os.environ["ACOS_PRINCIPAL_BOOTSTRAP_KEY"] = BOOTSTRAP_KEY
    from fastapi.testclient import TestClient

    from academicos.api.main import app

    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    def save(name: str, method: str, path: str, r, body=None) -> dict:
        assert r.status_code == 200, (path, r.status_code, r.text)
        data = r.json()
        (OUT / f"{name}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        manifest.append({"file": f"{name}.json", "method": method, "path": path,
                         "status": r.status_code, "body": body})
        print(f"{r.status_code} {method} {path} -> {name}.json")
        return data

    with TestClient(app) as client:
        # A teacher can only join through an invite, so a principal has to
        # exist first -- the same two steps seed_phone_demo_school.py takes.
        r = client.post("/api/v1/auth/register", json={
            "principalKey": BOOTSTRAP_KEY, "schoolId": SCHOOL,
            "name": "Priya Principal", "email": "principal@demo.detail",
            "password": PASSWORD})
        assert r.status_code == 200, r.text
        principal = {"Authorization": f"Bearer {r.json()['token']}"}
        r = client.post("/api/v1/auth/invites",
                        json={"role": "teacher", "email": "teacher@demo.detail"},
                        headers=principal)
        assert r.status_code == 200, r.text
        r = client.post("/api/v1/auth/register", json={
            "inviteCode": r.json()["code"], "name": "Tara Teacher",
            "email": "teacher@demo.detail", "password": PASSWORD})
        assert r.status_code == 200, r.text
        auth = {"Authorization": f"Bearer {r.json()['token']}"}

        templates = client.get(f"/api/v1/schools/{SCHOOL}/teacher-templates",
                               params={"grade": 10, "subject": "Mathematics"},
                               headers=auth).json()
        unit = next(p for p in templates["presets"] if p["examType"] == "unit_test")
        r = client.post("/api/v1/papers/generate-from-template", headers=auth, json={
            "templateId": unit["id"], "scope": {"chapterIds": []}, "allowGaps": True})
        gen = save("generate_from_template_10_maths_unit_test", "POST",
                   "/api/v1/papers/generate-from-template", r,
                   {"templateId": unit["id"], "scope": {"chapterIds": []},
                    "allowGaps": True})
        assessment_id = gen["assessmentId"]
        paper_id = gen["paper"]["id"]

        # The three calls the detail screen makes, in its order.
        save("assessment_10_maths_unit_test", "GET",
             f"/api/v1/assessments/{assessment_id}",
             client.get(f"/api/v1/assessments/{assessment_id}", headers=auth))
        save("assessments_by_school", "GET", f"/api/v1/assessments?school_id={SCHOOL}",
             client.get("/api/v1/assessments", params={"school_id": SCHOOL},
                        headers=auth))
        save("paper_10_maths_unit_test", "GET", f"/api/v1/papers/{paper_id}",
             client.get(f"/api/v1/papers/{paper_id}", headers=auth))

    (OUT / "manifest.json").write_text(json.dumps({
        "command": "PYTHONPATH=src PYTHONIOENCODING=utf-8 python "
                   "scripts/capture_assessment_detail_fixtures.py",
        "bank": "academicos-data/syllabus/questions.json",
        "responses": manifest}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
