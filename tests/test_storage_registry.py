"""Deep coverage of SourceRegistry (src/academicos/storage/registry.py).

Complements tests/test_ingest_registry.py (roundtrip, idempotent re-register,
status reset, checksum-addressed ids, basic update/listing). These tests focus
on the ledger's remaining contract: conflict semantics, update, by_status,
ordering, meta round-trip, field whitelisting and durability across reopen.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from academicos.storage.registry import SourceRegistry


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "registry.sqlite"


@pytest.fixture
def reg(db_path: Path) -> SourceRegistry:
    r = SourceRegistry(db_path)
    yield r
    r.close()


def test_register_then_reegister_updates_file_key_and_resets_status(reg: SourceRegistry) -> None:
    reg.register("src:r", file_key="old.pdf", status="parsed", quality_score=0.5)
    reg.register("src:r", file_key="new.pdf")
    row = reg.get("src:r")
    assert row["file_key"] == "new.pdf"
    assert row["status"] == "registered"
    assert row["quality_score"] == 0.5  # conflict-update leaves other cols alone
    assert reg.count() == 1


def test_reegister_status_argument_does_not_override_reset(reg: SourceRegistry) -> None:
    reg.register("src:r", file_key="k1", status="parsed")
    reg.register("src:r", file_key="k2", status="extracted")
    row = reg.get("src:r")
    assert row["status"] == "registered"  # ON CONFLICT hardcodes 'registered'
    assert row["file_key"] == "k2"


def test_update_sets_fields(reg: SourceRegistry) -> None:
    reg.register("src:u", file_key="k")
    reg.update("src:u", status="parsed", quality_score=0.92, page_count=14)
    row = reg.get("src:u")
    assert row["status"] == "parsed"
    assert row["quality_score"] == 0.92
    assert row["page_count"] == 14


def test_update_dict_field_json_serialized(reg: SourceRegistry) -> None:
    reg.register("src:u", file_key="k")
    reg.update("src:u", meta={"a": [1, 2]})
    row = reg.get("src:u")
    assert json.loads(row["meta"]) == {"a": [1, 2]}


def test_get_returns_all_stored_fields_and_meta_roundtrips(reg: SourceRegistry) -> None:
    meta = {"tracking": {"pass": 1, "fail": [0, 1]}, "tags": ["a", "b"]}
    reg.register("src:m", file_key="qp/2025.pdf", sha256="s256", sha512="s512",
                 size_bytes=100, source_url="https://x", kind="file",
                 doc_type="question_paper", title="QP 2025", subject="physics",
                 grade="12", academic_year="2025", series="S1", page_count=8,
                 status="registered", notes="n", meta=meta)
    row = reg.get("src:m")
    assert row["source_id"] == "src:m"
    assert row["file_key"] == "qp/2025.pdf"
    assert row["sha256"] == "s256"
    assert row["sha512"] == "s512"
    assert row["size_bytes"] == 100
    assert row["source_url"] == "https://x"
    assert row["kind"] == "file"
    assert row["doc_type"] == "question_paper"
    assert row["title"] == "QP 2025"
    assert row["subject"] == "physics"
    assert row["grade"] == "12"
    assert row["academic_year"] == "2025"
    assert row["series"] == "S1"
    assert row["page_count"] == 8
    assert row["status"] == "registered"
    assert row["notes"] == "n"
    # meta is stored as JSON text and round-trips through json.loads
    assert json.loads(row["meta"]) == meta


def test_get_missing_returns_none(reg: SourceRegistry) -> None:
    assert reg.get("src:nope") is None


def test_by_status_filters(reg: SourceRegistry) -> None:
    reg.register("src:1", file_key="a", status="registered")
    reg.register("src:2", file_key="b", status="parsed")
    reg.register("src:3", file_key="c", status="parsed")
    reg.register("src:4", file_key="d", status="failed")
    assert {r["source_id"] for r in reg.by_status("parsed")} == {"src:2", "src:3"}
    assert {r["source_id"] for r in reg.by_status("registered")} == {"src:1"}
    assert reg.by_status("retracted") == []


def test_all_ordered_by_registered_at(reg: SourceRegistry) -> None:
    reg.register("src:a", file_key="a")
    reg.register("src:b", file_key="b")
    assert [r["source_id"] for r in reg.all()] == ["src:a", "src:b"]
    # force b to be older; ORDER BY registered_at must flip the listing
    reg.conn.execute(
        "UPDATE sources SET registered_at='2000-01-01T00:00:00+00:00' WHERE source_id='src:b'"
    )
    reg.conn.commit()
    assert [r["source_id"] for r in reg.all()] == ["src:b", "src:a"]


def test_count(reg: SourceRegistry) -> None:
    assert reg.count() == 0
    for i in range(3):
        reg.register(f"src:{i}", file_key=f"k{i}")
    assert reg.count() == 3


def test_source_id_and_file_key_bound_to_explicit_params(reg: SourceRegistry) -> None:
    # source_id/file_key are consumed by register()'s positional parameters,
    # so passing them through a kwargs dict stores the canonical values (they
    # can never be overwritten from **fields).
    fields = {"source_id": "src:real", "file_key": "real_key.pdf",
              "doc_type": "question_paper"}
    reg.register(**fields)
    row = reg.get("src:real")
    assert row["source_id"] == "src:real"
    assert row["file_key"] == "real_key.pdf"
    assert row["doc_type"] == "question_paper"
    assert reg.count() == 1


def test_source_id_or_file_key_in_fields_is_a_type_error(reg: SourceRegistry) -> None:
    # The signature register(source_id, file_key, **fields) means these keys
    # can never reach **fields (Python raises before the body runs). This is
    # the contract the old per-key whitelist guard in register() was dead code:
    # remove it without changing behavior.
    with pytest.raises(TypeError):
        reg.register("src:1", file_key="k", source_id="hijack")


def test_get_returns_meta_as_json_text(reg: SourceRegistry) -> None:
    # meta is persisted as JSON *text*; consumers parse it with json.loads.
    # It must not come back pre-parsed (that would break every caller that
    # treats it as a string column).
    reg.register("src:m", file_key="k", meta={"a": [1, 2], "b": {"c": 3}})
    row = reg.get("src:m")
    assert isinstance(row["meta"], str)
    assert json.loads(row["meta"]) == {"a": [1, 2], "b": {"c": 3}}


def test_unknown_field_raises_not_silently_stored(reg: SourceRegistry) -> None:
    with pytest.raises(sqlite3.OperationalError):
        reg.register("src:x", file_key="k", not_a_column=42)
    assert reg.count() == 0


def test_close_and_reopen_persists(db_path: Path) -> None:
    r = SourceRegistry(db_path)
    r.register("src:1", file_key="a", status="parsed", quality_score=0.7,
               meta={"x": 1})
    r.close()
    r2 = SourceRegistry(db_path)
    assert r2.count() == 1
    row = r2.get("src:1")
    assert row["status"] == "parsed"
    assert row["quality_score"] == 0.7
    assert json.loads(row["meta"]) == {"x": 1}
    r2.close()


def test_nested_dict_field_json_serialized(reg: SourceRegistry) -> None:
    reg.register("src:d", file_key="k", notes={"a": 1, "b": [2]})
    row = reg.get("src:d")
    assert json.loads(row["notes"]) == {"a": 1, "b": [2]}