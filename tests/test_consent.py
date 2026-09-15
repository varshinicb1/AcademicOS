from pathlib import Path
import tempfile
import pytest

from academicos.assessment.consent import ConsentStore, ParentalConsentRecord
from test_assessment_routes_auth import _boot_client, _register


def test_consent_store_local_crud(tmp_path: Path):
    store = ConsentStore(tmp_path / "consents.db")

    # 1. Record consent
    rec = store.record_consent(
        school_id="school_1",
        student_id="student_101",
        guardian_name="Anita Sharma",
        guardian_relationship="mother",
        method="Signed admission form on file",
        recorded_by="user_teacher_1",
        notes="Physical slip in filing cabinet A",
    )
    assert rec.id.startswith("consent_")
    assert rec.school_id == "school_1"
    assert rec.student_id == "student_101"
    assert rec.status == "granted"

    # 2. Query consent
    assert store.has_consent("school_1", "student_101") is True
    assert store.has_consent("school_1", "student_999") is False

    fetched = store.get_consent("school_1", "student_101")
    assert fetched is not None
    assert fetched.guardian_name == "Anita Sharma"

    # 3. Cross-school isolation at store level
    assert store.get_consent("school_2", "student_101") is None
    assert store.has_consent("school_2", "student_101") is False

    # 4. Revoke consent
    revoked = store.revoke_consent("school_1", "student_101", revoked_by="user_principal_1")
    assert revoked is not None
    assert revoked.status == "revoked"
    assert revoked.revoked_by == "user_principal_1"
    assert store.has_consent("school_1", "student_101") is False

    # 5. List for school
    store.record_consent(
        school_id="school_1",
        student_id="student_102",
        guardian_name="Rajesh Kumar",
        method="Physical consent slip",
        recorded_by="user_teacher_1",
    )
    all_s1 = store.list_for_school("school_1")
    assert len(all_s1) == 2
    assert {r.student_id for r in all_s1} == {"student_101", "student_102"}


def test_consent_api_routes_auth_and_isolation(tmp_path: Path, monkeypatch):
    from academicos.assessment import consent as consent_mod

    monkeypatch.setattr(consent_mod, "_INSTANCE", None)

    with _boot_client(tmp_path, monkeypatch) as client:
        # 1. Unauthenticated calls must 401
        assert client.get("/api/v1/consent").status_code == 401
        assert client.get("/api/v1/consent/students/stu_1").status_code == 401
        assert client.post("/api/v1/consent", json={
            "studentId": "stu_1", "guardianName": "Parent", "method": "Form",
        }).status_code == 401

        # Register teacher for School A
        teacher_a = _register(client, "school_a", "teacher_a@example.com", name="Teacher A")
        auth_a = {"Authorization": f"Bearer {teacher_a['token']}"}

        # Register teacher for School B
        teacher_b = _register(client, "school_b", "teacher_b@example.com", name="Teacher B")
        auth_b = {"Authorization": f"Bearer {teacher_b['token']}"}

        # 2. Teacher A records consent for student in School A
        post_res = client.post("/api/v1/consent", headers=auth_a, json={
            "studentId": "stu_101",
            "guardianName": "Ramesh Gupta",
            "guardianRelationship": "father",
            "method": "Signed admission form",
            "notes": "Verified against school register",
        })
        assert post_res.status_code == 200, post_res.text
        data = post_res.json()
        assert data["studentId"] == "stu_101"
        assert data["schoolId"] == "school_a"
        assert data["status"] == "granted"

        # 3. Query consent as Teacher A -> has_consent: true
        get_res = client.get("/api/v1/consent/students/stu_101", headers=auth_a)
        assert get_res.status_code == 200
        assert get_res.json()["hasConsent"] is True
        assert get_res.json()["record"]["guardianName"] == "Ramesh Gupta"

        # 4. Cross-school isolation: Teacher B querying student stu_101 gets hasConsent: false (School B has no consent for stu_101)
        get_b_res = client.get("/api/v1/consent/students/stu_101", headers=auth_b)
        assert get_b_res.status_code == 200
        assert get_b_res.json()["hasConsent"] is False
        assert get_b_res.json()["record"] is None

        # 5. List consents for School A vs School B
        list_a = client.get("/api/v1/consent", headers=auth_a).json()
        assert len(list_a) == 1
        assert list_a[0]["studentId"] == "stu_101"

        list_b = client.get("/api/v1/consent", headers=auth_b).json()
        assert len(list_b) == 0

        # 6. Revoke consent
        del_res = client.delete("/api/v1/consent/students/stu_101", headers=auth_a)
        assert del_res.status_code == 200
        assert del_res.json()["hasConsent"] is False
        assert del_res.json()["record"]["status"] == "revoked"

        # Status is now revoked
        status_after = client.get("/api/v1/consent/students/stu_101", headers=auth_a).json()
        assert status_after["hasConsent"] is False
