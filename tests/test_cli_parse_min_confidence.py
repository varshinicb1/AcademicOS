"""P1.1 — `cli.cmd_parse`'s min_confidence gate.

Before this fix, `min_confidence` (config.toml / ACOS_MIN_CONFIDENCE) was
loaded but never read anywhere: every parse was registered status="parsed"
regardless of quality_score, and cmd_extract/cmd_build_graph consume any
"parsed"/"extracted" source, so a bad OCR result could reach the knowledge
graph silently. Now a parse below min_confidence is registered
status="low_confidence" instead -- excluded from that consumption set --
unless --force is passed.

EnsembleParser.parse is monkeypatched to return a canned quality_score
directly rather than exercising real PDF/OCR parsing, which is already
covered by test_parse_ensemble.py and test_smoke.py; this file tests only
cmd_parse's own gating logic.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos import cli
from academicos.config import Config
from academicos.models.document import ParsedDocument
from academicos.models.enums import DocType
from academicos.storage.registry import SourceRegistry


def _config(tmp_path: Path, min_confidence: float = 0.6) -> Config:
    return Config(data_root=tmp_path, toml={"min_confidence": min_confidence})


def _seed_source(cfg: Config, source_id: str) -> None:
    reg = SourceRegistry(cfg.registry_db)
    reg.register(source_id, file_key=f"{source_id}.pdf", doc_type="question_paper")
    reg.close()
    (cfg.documents_dir / f"{source_id}.pdf").write_bytes(b"%PDF-1.4 fake")


def _fake_parser(scores: dict[str, float]):
    """A drop-in EnsembleParser.parse replacement: returns a ParsedDocument
    whose quality_score is whatever the test wants for that source_id."""
    def parse(self, path, document_id, doc_type, max_pages=500):
        return ParsedDocument(document_id=document_id, doc_type=doc_type,
                              full_text="some text", quality_score=scores[document_id])
    return parse


def _args(**overrides) -> argparse.Namespace:
    base = dict(doc_id=None, reparse=False, vlm_mode="service",
               vlm_url="http://127.0.0.1:8910", force=False)
    base.update(overrides)
    return argparse.Namespace(**base)


def test_high_confidence_parse_is_registered_parsed(tmp_path, monkeypatch):
    cfg = _config(tmp_path, min_confidence=0.6)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    _seed_source(cfg, "doc_good")
    monkeypatch.setattr(
        "academicos.parse.ensemble.EnsembleParser.parse", _fake_parser({"doc_good": 0.9}))

    assert cli.cmd_parse(_args()) == 0

    reg = SourceRegistry(cfg.registry_db)
    row = reg.get("doc_good")
    reg.close()
    assert row["status"] == "parsed"
    assert row["quality_score"] == 0.9


def test_low_confidence_parse_is_held_not_extracted(tmp_path, monkeypatch):
    cfg = _config(tmp_path, min_confidence=0.6)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    _seed_source(cfg, "doc_bad")
    monkeypatch.setattr(
        "academicos.parse.ensemble.EnsembleParser.parse", _fake_parser({"doc_bad": 0.3}))

    assert cli.cmd_parse(_args()) == 0

    reg = SourceRegistry(cfg.registry_db)
    row = reg.get("doc_bad")
    reg.close()
    assert row["status"] == "low_confidence"
    assert row["quality_score"] == 0.3
    assert "0.3" in row["notes"] and "0.6" in row["notes"]

    # The whole point: cmd_extract only ever looks at "parsed"/"extracted".
    assert row["status"] not in ("parsed", "extracted")

    # The parse output itself is still written to disk -- nothing is lost,
    # it's just not promoted into the pipeline automatically.
    from academicos.ingest.pipeline import safe_name
    assert (cfg.parse_dir / f"{safe_name('doc_bad')}.json").exists()


def test_force_accepts_low_confidence_parse_anyway(tmp_path, monkeypatch):
    cfg = _config(tmp_path, min_confidence=0.6)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    _seed_source(cfg, "doc_bad")
    monkeypatch.setattr(
        "academicos.parse.ensemble.EnsembleParser.parse", _fake_parser({"doc_bad": 0.3}))

    assert cli.cmd_parse(_args(force=True)) == 0

    reg = SourceRegistry(cfg.registry_db)
    row = reg.get("doc_bad")
    reg.close()
    assert row["status"] == "parsed"
    assert row["quality_score"] == 0.3


def test_low_confidence_docs_are_excluded_from_extract(tmp_path, monkeypatch):
    """End-to-end proof of the actual security-relevant property: a
    low_confidence source never reaches extract's consumption set."""
    cfg = _config(tmp_path, min_confidence=0.6)
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    _seed_source(cfg, "doc_good")
    _seed_source(cfg, "doc_bad")
    monkeypatch.setattr(
        "academicos.parse.ensemble.EnsembleParser.parse",
        _fake_parser({"doc_good": 0.9, "doc_bad": 0.3}))
    cli.cmd_parse(_args())

    reg = SourceRegistry(cfg.registry_db)
    extractable = [s["source_id"] for s in reg.all() if s["status"] in ("parsed", "extracted")]
    reg.close()
    assert extractable == ["doc_good"]


def test_default_min_confidence_matches_config_default(tmp_path, monkeypatch):
    """Config.min_confidence defaults to 0.6 -- verifies the gate is wired
    to the real config value, not a hardcoded constant in cmd_parse."""
    cfg = Config(data_root=tmp_path)  # no explicit min_confidence override
    assert cfg.min_confidence == 0.6
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: cfg))
    _seed_source(cfg, "doc_borderline")
    monkeypatch.setattr(
        "academicos.parse.ensemble.EnsembleParser.parse",
        _fake_parser({"doc_borderline": 0.59}))

    cli.cmd_parse(_args())

    reg = SourceRegistry(cfg.registry_db)
    row = reg.get("doc_borderline")
    reg.close()
    assert row["status"] == "low_confidence"
