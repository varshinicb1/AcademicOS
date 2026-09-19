"""Smoke test: end-to-end mini corpus -> ingest -> parse -> extract -> graph -> search."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def sandbox(tmp_path_factory):
    box = tmp_path_factory.mktemp("acos")
    corpus = box / "corpus"
    corpus.mkdir()
    # tiny born-digital PDF (PyMuPDF)
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Sample Question Paper 2025", fontsize=14)
    page.insert_text((72, 100), "Time Allowed: 3 Hours  Maximum Marks: 80", fontsize=10)
    page.insert_text((72, 120), "General Instructions:", fontsize=10)
    page.insert_text((72, 140), "Section A 1. What is photosynthesis? (2 marks)", fontsize=10)
    page.insert_text((72, 160), "2. State Newton's second law of motion. (2 marks)", fontsize=10)
    page.insert_text((72, 180), "Section B 3. Explain the working of a solar cell. (3 marks)", fontsize=10)
    page.insert_text((72, 200), "This question paper comprises five sections A, B, C, D and E.", fontsize=10)
    qp = corpus / "XII_Physics_QP_2025.pdf"
    doc.save(qp)
    doc.close()
    ms = corpus / "XII_Physics_MS_2025.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Marking Scheme 2025", fontsize=14)
    page.insert_text((72, 100), "1. Photosynthesis  (2 marks)", fontsize=10)
    page.insert_text((72, 120), "Conversion of light energy to chemical energy. (1 mark)", fontsize=10)
    page.insert_text((72, 140), "Chlorophyll absorbs light and splits water. (1 mark)", fontsize=10)
    page.insert_text((72, 160), "2. Newton's second law  (2 marks)", fontsize=10)
    page.insert_text((72, 180), "F = ma with correct explanation. (2 marks)", fontsize=10)
    doc.save(ms)
    doc.close()
    return box, corpus


def test_end_to_end(sandbox):
    box, corpus = sandbox
    from academicos.config import Config
    from academicos.ingest.pipeline import IngestionPipeline
    from academicos.parse.ensemble import EnsembleParser
    from academicos.extract.chunking import chunk_document
    from academicos.extract.academic import extract_questions
    from academicos.graph.builder import GraphBuilder
    from academicos.graph.store import GraphStore
    from academicos.retrieval.hybrid import HybridRetriever
    from academicos.retrieval.index import ChunkIndex
    from academicos.storage.base import LocalStore
    from academicos.storage.registry import SourceRegistry
    from academicos.models.document import ParsedDocument
    from academicos.models.enums import DocType

    cfg = Config(data_root=box / "data")
    cfg.corpus_root = corpus

    # Diagnose the fixture before the pipeline, not after. `Config` prefers the
    # environment's `ACOS_DATA_ROOT` over the `data_root=` argument, so an
    # ambient value used to redirect the registry out from under this test and
    # the failure surfaced as an empty `accepted` with an empty `rejected` --
    # which reads like a pipeline bug and is actually a test-isolation bug.
    # `_no_ambient_data_root` in conftest now prevents it; these two assertions
    # make a recurrence say so directly.
    assert cfg.data_root == box / "data", (
        f"Config ignored data_root={box / 'data'} and used {cfg.data_root}. "
        "Something in the environment (ACOS_DATA_ROOT) overrode it."
    )
    assert sorted(p.name for p in corpus.glob("*.pdf")) == [
        "XII_Physics_MS_2025.pdf", "XII_Physics_QP_2025.pdf"], (
        "the sandbox corpus is not what this test wrote; the fixture is being "
        "redirected or cleaned by something else"
    )

    reg = SourceRegistry(cfg.registry_db)
    store = LocalStore(cfg.documents_dir)
    pipe = IngestionPipeline(corpus, reg, store)
    res = pipe.run(min_pdf_bytes=256)
    assert len(res.accepted) == 2, [p for _, p in res.rejected]

    parser = EnsembleParser()
    parsed: list[ParsedDocument] = []
    for sf in res.accepted:
        out = parser.parse(sf.path, sf.source_id, DocType.UNKNOWN)
        assert out.full_text
        parsed.append(out)

    idx = ChunkIndex(cfg.index_db)
    for doc in parsed:
        chunks = chunk_document(doc)
        assert chunks
        idx.add(chunks, replace_doc=True)

    graph = GraphStore(cfg.graph_db)
    builder = GraphBuilder(graph)
    from academicos.models.academic import Question
    q = Question(canonical_id="cbse:q:test:1", question_paper_id="p1", q_no="1", marks=2,
                 title="What is photosynthesis?", source_text="What is photosynthesis? (2 marks)")
    builder.build_question(q)
    n, e = graph.count()
    assert n >= 1 and e >= 0

    retriever = HybridRetriever(idx, graph)
    hits = retriever.search("photosynthesis", limit=5)
    assert hits, "expected at least one hit for photosynthesis"
    assert any("photosynthesis" in h.chunk.text.lower() for h in hits)

    from academicos.eval.metrics import precision_at_k
    relevant = {h.chunk.id for h in hits}
    assert precision_at_k(relevant, [h.chunk.id for h in hits], k=len(hits)) == 1.0

    reg.close(); idx.close(); graph.close()
