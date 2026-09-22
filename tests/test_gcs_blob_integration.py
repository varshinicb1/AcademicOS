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
