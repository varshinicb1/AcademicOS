"""Opt-in: GcsBlobStore against a REAL bucket with the REAL client.

Why this exists: tests/test_blob_factory.py runs every line of GcsStore's
put_bytes/get_bytes/stat against an in-memory fake. The fake encodes what we
believe google-cloud-storage does -- `blob.generation` is set after
upload_from_string, a precondition mismatch raises an exception whose
`.code == 412`, `bucket.get_blob` returns None for a missing object, and
`md5_hash` is base64 of the raw digest. Those are assumptions until they have
run against the real client once. This file is that run.

Skipped unless ACOS_GCS_TEST_BUCKET names a bucket the current Application
Default Credentials can write to. Use a scratch bucket, never the production
media bucket: every run writes under a unique prefix and deletes it after.

    ACOS_GCS_TEST_BUCKET=my-scratch-bucket pytest tests/test_gcs_blob_integration.py -v

deploy-gcp.yml runs this file before every deploy when the GCS_TEST_BUCKET
repository variable is set. Until it has passed once, the GCS correctness
claims in storage/blobs.py are unverified (docs/gcp-deployment.md section 8).
"""
from __future__ import annotations

import os
import uuid

import pytest

BUCKET = os.environ.get("ACOS_GCS_TEST_BUCKET", "").strip()

pytestmark = pytest.mark.skipif(
    not BUCKET, reason="set ACOS_GCS_TEST_BUCKET to a scratch bucket to run against real GCS")


@pytest.fixture
def real_store():
    storage = pytest.importorskip("google.cloud.storage")
    from academicos.storage import blobs

    client = storage.Client()
    prefix = f"acos-integration-{uuid.uuid4().hex[:12]}"
    blobs.reset_status()
    make = lambda: blobs.GcsBlobStore(  # noqa: E731 - two instances, one bucket
        "curriculum-snapshots", bucket=BUCKET, prefix=prefix, client=client,
        guard_generations=True)
    yield make
    for blob in client.list_blobs(BUCKET, prefix=prefix):
        blob.delete()
    blobs.reset_status()


def test_create_then_stale_overwrite_is_a_real_412(real_store) -> None:
    from academicos.storage import blobs

    a = real_store()
    with pytest.raises(blobs.BlobNotFound):          # get_blob -> None on 404
        a.download("curriculum.sqlite")

    a.upload("curriculum.sqlite", b"v1 from A", "application/x-sqlite3")
    gen_a = a._generations["curriculum.sqlite"]
    assert gen_a > 0, "blob.generation must be populated after upload_from_string"

    b = real_store()
    assert b.download("curriculum.sqlite") == b"v1 from A"
    assert b._generations["curriculum.sqlite"] == gen_a
    b.upload("curriculum.sqlite", b"v2 from B", "application/x-sqlite3")

    # A still holds gen_a: the real service must answer 412, and the real
    # exception must be recognised as a precondition failure.
    with pytest.raises(blobs.BlobConflict) as info:
        a.upload("curriculum.sqlite", b"stale from A", "application/x-sqlite3")
    assert getattr(info.value.__cause__, "code", None) == 412
    assert b.download("curriculum.sqlite") == b"v2 from B"
    assert blobs.blob_status()["curriculum_snapshot_conflict_count"] == 1


def test_md5_matches_what_we_compute(real_store) -> None:
    """The retry-adoption path compares GCS's md5_hash with ours; the formats
    must agree on the real service, or every lost-response retry is a false
    conflict."""
    a = real_store()
    a.upload("curriculum.sqlite", b"payload", "application/x-sqlite3")
    assert a._own_write_generation("curriculum.sqlite", b"payload") == \
        a._generations["curriculum.sqlite"]
    assert a._own_write_generation("curriculum.sqlite", b"other") is None


def test_self_412_on_a_retried_upload_is_adopted_on_the_real_service(real_store) -> None:
    """The lost-response retry, reproduced on the real service: the retry
    carries the precondition of the FIRST attempt (here "must not exist"),
    meets the generation that attempt created, and gets a real 412. The md5
    comparison must recognise it as our own write and adopt that generation,
    or every lost response would wedge the curriculum store as a conflict."""
    from academicos.storage import blobs

    a = real_store()
    a.upload("curriculum.sqlite", b"first attempt landed", "application/x-sqlite3")
    landed = a._generations["curriculum.sqlite"]
    a._generations["curriculum.sqlite"] = 0          # what the retry still expects
    a.upload("curriculum.sqlite", b"first attempt landed", "application/x-sqlite3")
    assert a._generations["curriculum.sqlite"] == landed
    assert blobs.blob_status()["curriculum_snapshot_conflict_count"] == 0


def test_download_is_pinned_to_the_generation_it_reports(real_store) -> None:
    """get_bytes reads metadata (get_blob) and then download_as_bytes with
    if_generation_match set to that generation; the pair must describe one
    version, and the generation must be the one the next guarded write needs."""
    a = real_store()
    a.upload("curriculum.sqlite", b"v1", "application/x-sqlite3")
    b = real_store()
    assert b.download("curriculum.sqlite") == b"v1"
    assert b._generations["curriculum.sqlite"] == a._generations["curriculum.sqlite"]
    b.upload("curriculum.sqlite", b"v2", "application/x-sqlite3")   # accepted
    assert real_store().download("curriculum.sqlite") == b"v2"


def test_conflict_copy_lands_in_the_real_bucket(real_store) -> None:
    """curriculum/store.py preserves a losing snapshot under conflicts/ with a
    key the guarded store has never seen, i.e. if_generation_match=0."""
    a = real_store()
    a.upload("conflicts/20260922T000000Z-test-abcd1234.sqlite", b"losing file",
             "application/x-sqlite3")
    assert real_store().download("conflicts/20260922T000000Z-test-abcd1234.sqlite") \
        == b"losing file"
