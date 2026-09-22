"""Capture the real API responses the paper builder's widget tests replay.

Task 902's tests drive the whole builder (class/subject -> template -> scope
-> generate -> swap/pick -> download) against a fake API. A fake written by
hand would agree with the widget code by construction and prove nothing, so
the fake serves these files instead: every one is what the real backend
answered, in-process, on a temp data root with the real served bank
(academicos-data/syllabus/questions.json, read-only).

Run from the repo root (outside pytest -- under pytest the served bank is
deliberately not loaded, see pool.build_pool):

    PYTHONPATH=src PYTHONIOENCODING=utf-8 python scripts/capture_paper_builder_fixtures.py

Writes frontend/test/paper_builder/fixtures/*.json and a manifest.json that
records each request and its status. PDFs are not stored (hundreds of KB,
and the widget tests only check that both downloads happen); the manifest
records their real sizes.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "test" / "paper_builder" / "fixtures"


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="acos_builder_fixtures_"))
    os.environ["ACOS_DATA_ROOT"] = str(tmp)
    os.environ["ACOS_DISABLE_RATE_LIMIT"] = "1"
    from fastapi.testclient import TestClient

    from academicos.api.main import app

    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    def save(name: str, method: str, path: str, r, body=None) -> dict:
        assert r.status_code < 500, (path, r.status_code, r.text)
        data = r.json()
        (OUT / f"{name}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        manifest.append({"file": f"{name}.json", "method": method, "path": path,
                         "status": r.status_code, "body": body})
        print(f"{r.status_code} {method} {path} -> {name}.json")
        return data

    with TestClient(app) as client:
        r = client.post("/api/v1/auth/register", json={
            "schoolId": "school_1", "name": "Asha", "email": "asha@example.com",
            "password": "correct horse battery", "role": "teacher"})
        assert r.status_code == 200, r.text
        auth = {"Authorization": f"Bearer {r.json()['token']}"}
        school = "school_1"

        def get(name, path, params=None):
            r = client.get(path, params=params, headers=auth)
            full = path + ("?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else "")
            return save(name, "GET", full, r)

        def post(name, path, body):
            r = client.post(path, json=body, headers=auth)
            return save(name, "POST", path, r, body)

        # ---- Class 10 Science, half-yearly (the complete-paper path)
        t10 = get("templates_10_science", f"/api/v1/schools/{school}/teacher-templates",
                  {"grade": 10, "subject": "Science"})
        ch10 = get("chapters_10_science", "/api/v1/catalog/Science/10/chapters")
        preset = next(p for p in t10["presets"] if p["examType"] == "half_yearly")
        # Half-yearly: the first half of the chapters, the way a school sets it.
        half = [c["chapterId"] for c in ch10[: max(1, len(ch10) // 2)]]
        post("availability_10_science_all",
             f"/api/v1/schools/{school}/teacher-templates/{preset['id']}/availability",
             {"scope": {"chapterIds": []}})
        post("availability_10_science_half",
             f"/api/v1/schools/{school}/teacher-templates/{preset['id']}/availability",
             {"scope": {"chapterIds": half}})
        gen = post("generate_10_science", "/api/v1/papers/generate-from-template",
                   {"templateId": preset["id"], "scope": {"chapterIds": []},
                    "setCount": 2, "allowGaps": True})
        paper = gen["paper"]
        first = paper["sections"][0]["questions"][0]
        swap = post("swap_10_science",
                    f"/api/v1/papers/{paper['id']}/questions/{first['displayNumber']}/swap", {})
        # The bank picker for a slot in the 3-mark section: same marks, keyed.
        three = next(s for s in swap["paper"]["sections"]
                     if s["questions"] and s["questions"][0]["marks"] == 3)
        slot_q = three["questions"][0]
        found = post("search_10_science_3m", "/api/v1/questions/search",
                     {"subject": "Science", "grade": 10, "minMarks": 3, "maxMarks": 3,
                      "limit": 25})
        on_paper = {q["questionId"] for s in swap["paper"]["sections"] for q in s["questions"]}
        keyed = [q for q in found if q["id"] not in on_paper
                 and ((q.get("answerScheme") or {}).get("modelAnswer") or "").strip()]
        if keyed:
            post("pick_10_science",
                 f"/api/v1/papers/{paper['id']}/questions/{slot_q['displayNumber']}",
                 {"questionId": keyed[0]["id"]})
        # Remove: the first long answer (Section D), OR alternative and all.
        # The section then prints short, and every later number moves up.
        long_q = next(s for s in paper["sections"] if s["label"] == "D")["questions"][0]
        r = client.delete(f"/api/v1/papers/{paper['id']}/questions/{long_q['displayNumber']}",
                          headers=auth)
        edited = save("remove_10_science", "DELETE",
                      f"/api/v1/papers/{paper['id']}/questions/{long_q['displayNumber']}", r)
        # Set B after the swap and pick: the builder fetches a set fresh once
        # set A has been edited (the server edits every set).
        get("paper_10_science_set_b", f"/api/v1/papers/{paper['id']}_set_B")
        for pid, tag in ((paper["id"], ""), (f"{paper['id']}_set_B", "_set_b")):
            for fmt in ("pdf", "answer-key"):
                r = client.post(f"/api/v1/papers/{pid}/export/{fmt}", headers=auth)
                exp = save(f"export_10_science{tag}_{fmt.replace('-', '_')}", "POST",
                           f"/api/v1/papers/{pid}/export/{fmt}", r)
                f = client.get(exp["url"], headers=auth)
                manifest.append({"file": None, "method": "GET", "path": exp["url"],
                                 "status": f.status_code, "bytes": len(f.content),
                                 "startsWith": f.content[:5].decode("latin-1")})
                print(f"{f.status_code} GET {exp['url']} -> {len(f.content)} bytes")
        # "Make another like this": the same template and chapters, with the
        # questions of the paper as the teacher left it to be printed only
        # where the bank has nothing else.
        left = sorted({i for s in edited["paper"]["sections"] for q in s["questions"]
                       for i in (q["questionId"], q.get("internalChoiceQuestionId")) if i})
        post("generate_10_science_another", "/api/v1/papers/generate-from-template",
             {"templateId": preset["id"], "scope": {"chapterIds": []}, "setCount": 2,
              "allowGaps": False, "fillFromOutsideScope": False, "avoidQuestionIds": left})
        # "Quick paper (CBSE pattern)" opens on the annual preset.
        annual = next(p for p in t10["presets"] if p["examType"] == "annual")
        post("availability_10_science_annual_all",
             f"/api/v1/schools/{school}/teacher-templates/{annual['id']}/availability",
             {"scope": {"chapterIds": []}})

        # ---- Class 7 Mathematics, unit test (the gaps path)
        t7 = get("templates_7_maths", f"/api/v1/schools/{school}/teacher-templates",
                 {"grade": 7, "subject": "Mathematics"})
        ch7 = get("chapters_7_maths", "/api/v1/catalog/Mathematics/7/chapters")
        unit = next(p for p in t7["presets"] if p["examType"] == "unit_test")
        two = [c["chapterId"] for c in ch7[:2]]
        post("availability_7_maths_all",
             f"/api/v1/schools/{school}/teacher-templates/{unit['id']}/availability",
             {"scope": {"chapterIds": []}})
        post("availability_7_maths_two",
             f"/api/v1/schools/{school}/teacher-templates/{unit['id']}/availability",
             {"scope": {"chapterIds": two}})
        post("generate_7_maths_refused", "/api/v1/papers/generate-from-template",
             {"templateId": unit["id"], "scope": {"chapterIds": two}})

        # ---- A teacher's own template: the server's view of a bad total
        post("create_template_mismatch", f"/api/v1/schools/{school}/teacher-templates", {
            "name": "Weekly check", "grade": 10, "subject": "Science", "examType": "custom",
            "totalMarks": 25, "durationMinutes": 45,
            "sections": [{"title": "Section A", "questionCount": 10, "marksEach": 1},
                         {"title": "Section B", "questionCount": 4, "marksEach": 3}]})
        created = post("create_template_ok", f"/api/v1/schools/{school}/teacher-templates", {
            "name": "Weekly check", "grade": 10, "subject": "Science", "examType": "custom",
            "totalMarks": 22, "durationMinutes": 45,
            "sections": [{"title": "Section A", "questionCount": 10, "marksEach": 1},
                         {"title": "Section B", "questionCount": 4, "marksEach": 3}]})
        # What the builder asks next: the list (now with the new template
        # under "mine") and the new template's availability.
        get("templates_10_science_after_create", f"/api/v1/schools/{school}/teacher-templates",
            {"grade": 10, "subject": "Science"})
        post("availability_created_all",
             f"/api/v1/schools/{school}/teacher-templates/{created['id']}/availability",
             {"scope": {"chapterIds": []}})

    (OUT / "manifest.json").write_text(json.dumps({
        "command": "PYTHONPATH=src PYTHONIOENCODING=utf-8 python "
                   "scripts/capture_paper_builder_fixtures.py",
        "bank": "academicos-data/syllabus/questions.json",
        "responses": manifest}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
