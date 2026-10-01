"""Races found by a signed-in stress test on production's commit (aa301d2),
one core like the release, 5-60 concurrent users, 2026-10-01:

  * two exports of one paper rewrote the one file the download route was
    streaming: 26 of 716 downloads were torn (shorter or longer than their
    Content-Length), and a download could carry another export's
    traceable-copy id;
  * a student's learner model was loaded, added to and saved with no lock, so
    two writers for one student lost one's evidence, and a reader of a local
    file caught it half-written (School insights answered 500).
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

import fitz

from test_assessment_pdf import _boot_with_paper


def _pdf_text(data: bytes) -> str:
    with fitz.open(stream=data, filetype="pdf") as doc:
        return "".join(p.get_text() for p in doc)


def test_each_export_url_fetches_exactly_that_export(tmp_path, monkeypatch):
    client, auth, paper_id = _boot_with_paper(tmp_path, monkeypatch)
    raw = {**auth, "Accept-Encoding": "identity"}       # lengths as sent, not gzipped
    try:
        first = client.post(f"/api/v1/papers/{paper_id}/export/pdf", headers=auth).json()
        second = client.post(f"/api/v1/papers/{paper_id}/export/pdf", headers=auth).json()
        assert first["watermarkId"] != second["watermarkId"]
        for exp in (first, second):
            assert exp["url"].endswith(f"export={exp['watermarkId']}")
            got = client.get(exp["url"], headers=raw)
            assert got.status_code == 200 and got.content[:4] == b"%PDF"
            assert int(got.headers["content-length"]) == len(got.content)
            assert exp["watermarkId"] in _pdf_text(got.content), "the copy carries its own export's id"
        latest = client.get(f"/api/v1/papers/{paper_id}/file", headers=auth)
        assert second["watermarkId"] in _pdf_text(latest.content), "the plain path serves the latest export"
        key = client.post(f"/api/v1/papers/{paper_id}/export/answer-key", headers=auth).json()
        assert key["url"].endswith(f"format=answer-key&export={key['watermarkId']}")
        assert key["watermarkId"] in _pdf_text(client.get(key["url"], headers=auth).content)
        # an export id is checked, and an unknown one is a clear 404
        bad = client.get(f"/api/v1/papers/{paper_id}/file", params={"export": "../../secrets"}, headers=auth)
        assert bad.status_code == 422
        gone = client.get(f"/api/v1/papers/{paper_id}/file", params={"export": "exp_0000000000"}, headers=auth)
        assert gone.status_code == 404 and "expired" in gone.json()["detail"]
    finally:
        client.__exit__(None, None, None)


def test_exports_and_downloads_at_once_are_never_torn(tmp_path, monkeypatch):
    client, auth, paper_id = _boot_with_paper(tmp_path, monkeypatch)
    raw = {**auth, "Accept-Encoding": "identity"}       # lengths as sent, not gzipped
    try:
        problems: list[str] = []

        def one(i: int) -> None:
            fmt = ("pdf", "answer-key", "docx")[i % 3]
            exp = client.post(f"/api/v1/papers/{paper_id}/export/{fmt}", headers=auth)
            if exp.status_code != 200:
                problems.append(f"export {exp.status_code}")
                return
            for url in (exp.json()["url"], f"/api/v1/papers/{paper_id}/file"):
                got = client.get(url, headers=raw)
                body = got.content
                whole = body[:4] == b"%PDF" and body.rstrip().endswith(b"%%EOF") if not url.endswith(
                    "docx&export=" + exp.json()["watermarkId"]) else body[:2] == b"PK"
                if got.status_code != 200 or int(got.headers["content-length"]) != len(body) or not whole:
                    problems.append(f"{url}: {got.status_code}, {len(body)} bytes")

        threads = [threading.Thread(target=one, args=(i,)) for i in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert problems == []
    finally:
        client.__exit__(None, None, None)


def test_old_exports_are_swept(tmp_path):
    from academicos.assessment import export_files
    old = export_files.run_dir(tmp_path, "exp_0123456789")
    (old / "p.pdf").write_bytes(b"%PDF")
    fresh = export_files.run_dir(tmp_path, "exp_abcdefabcd")
    export_files.sweep(tmp_path, now=time.time() + export_files.KEEP_SECONDS + 5)
    assert not old.exists() and not fresh.exists()
    kept = export_files.run_dir(tmp_path, "exp_1111111111")
    export_files.sweep(tmp_path)
    assert kept.exists(), "a fresh export stays fetchable"


def _evaluation(qid: str, chapter: str):
    from academicos.assessment.evaluate import Evaluation
    from academicos.assessment.schemas import AnswerSchemeSchema, QuestionSchema
    q = QuestionSchema(id=qid, question_bank_id="b", subject="Science", grade=10, chapter_ids=[chapter],
                       bloom_level="remember", difficulty="easy", type="short_answer", stem="?",
                       estimated_time_minutes=1, marks=1, source="teacher_created",
                       created_at="2026-10-01T00:00:00Z", updated_at="2026-10-01T00:00:00Z",
                       answer_scheme=AnswerSchemeSchema(total_marks=1, model_answer="a"))
    return q, Evaluation(question_id=qid, awarded_marks=1, max_marks=1, verdict="teacher", confidence=1.0,
                         reasoning="", needs_review=False)


def test_two_writers_for_one_student_lose_nothing(tmp_path, monkeypatch):
    from academicos.assessment import knowledge as kmod
    store = kmod.KnowledgeStore(tmp_path / "km")
    monkeypatch.setattr(kmod, "_tell", lambda *a, **k: None)
    real_read = store._read_raw

    def slow_read(student_id):              # widen the window a race needs
        time.sleep(0.002)
        return real_read(student_id)

    monkeypatch.setattr(store, "_read_raw", slow_read)
    errors: list[BaseException] = []

    def writer(w: int) -> None:
        try:
            for i in range(10):
                if i % 2:
                    store.record_evaluations("s1", [_evaluation(f"w{w}q{i}", f"chapter-{w}")])
                else:
                    store.record_sheet("s1", [_evaluation(f"w{w}q{i}", f"chapter-{w}")], source=f"marks:p{w}:{i}")
                store.mastery("s1")
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(w,)) for w in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    model = store.load("s1")
    assert sum(len(s.history) for s in model.concepts.values()) == 60, "every writer's evidence is kept"
    assert set(model.concepts) == {f"chapter-{w}" for w in range(6)}


def test_a_local_model_is_never_read_half_written(tmp_path, monkeypatch):
    from academicos.assessment import knowledge as kmod
    store = kmod.KnowledgeStore(tmp_path / "km")
    monkeypatch.setattr(kmod, "_tell", lambda *a, **k: None)
    store.record_evaluations("s1", [_evaluation("q0", "c")])
    stop = time.time() + 1.5
    failures: list[BaseException] = []

    def write():
        i = 0
        while time.time() < stop:
            store.record_evaluations("s1", [_evaluation(f"q{i}", "c")])
            i += 1

    def read():
        while time.time() < stop:
            try:
                store.mastery("s1")
            except BaseException as e:  # noqa: BLE001
                failures.append(e)
                return

    threads = [threading.Thread(target=write)] + [threading.Thread(target=read) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert failures == []
    assert Path(store._path("s1")).exists()
