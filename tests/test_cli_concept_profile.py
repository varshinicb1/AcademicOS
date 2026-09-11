"""P1.4 — `concept-profile` CLI: skip-already-profiled-by-default + --force.

Before this change, every run re-selected the same top-occurrence concepts
regardless of whether they already carried a `difficulty` attribute, so
repeated runs never made forward progress across the graph (verified live:
running `concept-profile --top 500` twice left concept-spine coverage
unchanged at 1,911/6,708). This isolates just the new selection logic
(empty registry/index so the heavy curriculum-mining path is a fast no-op
downstream of the print we assert on) rather than re-testing
CurriculumEstimator's mining itself, which test_graph_curriculum.py already
covers.
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
from academicos.graph.schema import new_node
from academicos.graph.store import GraphStore
from academicos.models.enums import NodeType
from academicos.retrieval.index import ChunkIndex


def _seed(tmp_path: Path) -> None:
    # CurriculumEstimator opens cfg.index_db directly and queries its FTS5
    # `chunks` table -- must exist even with zero rows, or every
    # est.occurs_in()/contexts() call errors before it gets a chance to
    # return "not found".
    ChunkIndex(tmp_path / "index" / "index.sqlite").close()
    store = GraphStore(tmp_path / "graph" / "graph.sqlite")
    # Two already-profiled concepts (a real profile run would never assign
    # difficulty=99 -- a sentinel proving "left untouched" vs "recomputed").
    for label in ("Photosynthesis", "Mitosis"):
        n = new_node(NodeType.CONCEPT, label,
                     attributes={"occurrences": 10, "source_docs": 2, "difficulty": 99})
        store.upsert_node(n)
    # Three never-profiled concepts.
    for label in ("Osmosis", "Diffusion", "Respiration"):
        n = new_node(NodeType.CONCEPT, label,
                     attributes={"occurrences": 5, "source_docs": 1})
        store.upsert_node(n)
    store.close()


def _args(**overrides) -> argparse.Namespace:
    base = dict(top=100, min_occ=0, model=None, method="rule", force=False)
    base.update(overrides)
    return argparse.Namespace(**base)


def test_default_run_skips_already_profiled_concepts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: Config(data_root=tmp_path)))
    _seed(tmp_path)

    assert cli.cmd_concept_profile(_args(force=False)) == 0
    out = capsys.readouterr().out
    assert "profiling 3 concepts" in out
    assert "skipping already-profiled" in out

    store = GraphStore(tmp_path / "graph" / "graph.sqlite")
    already = {n.label: n.attributes for n in store.query_nodes(ntype=NodeType.CONCEPT, status=None, limit=100)
              if n.label in ("Photosynthesis", "Mitosis")}
    store.close()
    # Sentinel untouched -- proves they were excluded from selection, not
    # merely recomputed to the same value.
    assert already["Photosynthesis"]["difficulty"] == 99
    assert already["Mitosis"]["difficulty"] == 99


def test_force_includes_already_profiled_concepts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: Config(data_root=tmp_path)))
    _seed(tmp_path)

    assert cli.cmd_concept_profile(_args(force=True)) == 0
    out = capsys.readouterr().out
    assert "profiling 5 concepts" in out
    assert "skipping already-profiled" not in out


def test_min_occ_and_force_combine(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli.Config, "load", staticmethod(lambda: Config(data_root=tmp_path)))
    _seed(tmp_path)

    # min_occ=8 keeps only the two already-profiled (occurrences=10)
    # concepts; force=True still includes them despite already having a
    # difficulty attribute.
    assert cli.cmd_concept_profile(_args(min_occ=8, force=True)) == 0
    out = capsys.readouterr().out
    assert "profiling 2 concepts" in out
