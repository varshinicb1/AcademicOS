"""Run the full corpus through ingest -> parse -> extract -> graph -> index.

Usage:
    python scripts/run_ingest.py [--limit N] [--skip-parse] [--skip-extract] [--skip-graph]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.config import Config
from academicos.graph.builder import GraphBuilder
from academicos.graph.store import GraphStore
from academicos.ingest.pipeline import IngestionPipeline, safe_name
from academicos.parse.ensemble import EnsembleParser
from academicos.retrieval.index import ChunkIndex
from academicos.storage.base import LocalStore
from academicos.storage.registry import SourceRegistry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--skip-parse", action="store_true")
    ap.add_argument("--skip-extract", action="store_true")
    ap.add_argument("--skip-graph", action="store_true")
    ap.add_argument("--vlm-mode", default="service")
    args = ap.parse_args()

    cfg = Config.load()
    registry = SourceRegistry(cfg.registry_db)
    store = LocalStore(cfg.documents_dir)

    print("== ingest ==")
    pipe = IngestionPipeline(cfg.corpus_root, registry, store)
    res = pipe.run(max_files=args.limit)
    print(f"accepted={len(res.accepted)} rejected={len(res.rejected)} dups={len(res.duplicates)}")
    for sf, problems in res.rejected[:15]:
        print(f"  REJECT {sf.path.name}: {problems}")

    if not args.skip_parse:
        print("== parse ==")
        parser = EnsembleParser(vlm_mode=args.vlm_mode)
        sources = [s for s in registry.all() if s["status"] == "registered"]
        for i, src in enumerate(sources, 1):
            local = cfg.documents_dir / src["file_key"]
            if not local.exists():
                continue
            out = parser.parse(local, src["source_id"], None, max_pages=cfg.max_pages_per_doc)
            (cfg.parse_dir / f"{safe_name(src["source_id"])}.json").write_text(
                out.model_dump_json(indent=2), encoding="utf-8")
            registry.update(src["source_id"], status="parsed", quality_score=round(out.quality_score, 3))
            if i % 50 == 0:
                print(f"  parsed {i}/{len(sources)}")

    if not args.skip_extract:
        print("== extract ==")
        _extract_all(cfg, registry)

    if not args.skip_graph:
        print("== graph ==")
        graph = GraphStore(cfg.graph_db)
        builder = GraphBuilder(graph)
        from academicos.models.academic import AnswerScheme, MarkingPoint, Question, QuestionPaper
        from academicos.models.enums import EdgeType
        import json

        sources = [s for s in registry.all() if s["status"] == "extracted"]
        for src in sources:
            ef = cfg.extracted_dir / f"{safe_name(src["source_id"])}.json"
            if not ef.exists():
                continue
            payload = json.loads(ef.read_text(encoding="utf-8"))
            doc_node = builder.upsert_object(QuestionPaper(
                canonical_id=f"cbse:doc:{src['source_id']}", title=src["title"] or src["source_id"],
                academic_year=src["academic_year"], subject=src["subject"]))
            for q in payload.get("questions", []):
                qobj = Question.model_validate(q)
                qobj.question_paper_id = doc_node
                qid = builder.build_question(qobj)
                builder.link(doc_node, qid, EdgeType.CONTAINS)
            for mp in payload.get("marking_points", []):
                scheme = AnswerScheme(canonical_id=f"cbse:scheme:{src['source_id']}",
                                      document_id=src["source_id"], title=f"Scheme {src['source_id']}",
                                      marking_points=[MarkingPoint.model_validate(mp)])
                builder.link(doc_node, builder.build_answer_scheme(scheme), EdgeType.HAS_MARKING_POINT)
        n, e = graph.count()
        graph.snapshot(notes="full corpus build")
        print(f"  graph: {n} nodes, {e} edges")
        graph.close()

    registry.close()
    return 0


def _extract_all(cfg: Config, registry: SourceRegistry) -> None:
    import json

    from academicos.extract.academic import extract_marking_points, extract_questions
    from academicos.extract.chunking import chunk_document
    from academicos.models.document import ParsedDocument
    from academicos.models.enums import DocType

    idx = ChunkIndex(cfg.index_db)
    sources = [s for s in registry.all() if s["status"] == "parsed"]
    for src in sources:
        pf = cfg.parse_dir / f"{safe_name(src["source_id"])}.json"
        if not pf.exists():
            continue
        doc = ParsedDocument.model_validate_json(pf.read_text(encoding="utf-8"))
        doc.doc_type = DocType(src["doc_type"]) if src["doc_type"] else DocType.UNKNOWN
        chunks = chunk_document(doc)
        idx.add(chunks, replace_doc=True)
        payload: dict = {"chunks": [c.__dict__ for c in chunks]}
        if src["doc_type"] == "question_paper":
            payload["questions"] = [q.model_dump(mode="json") for q in extract_questions(doc, doc.doc_type)]
        if src["doc_type"] == "marking_scheme":
            payload["marking_points"] = [m.model_dump(mode="json") for m in extract_marking_points(doc)]
        (cfg.extracted_dir / f"{safe_name(src["source_id"])}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        registry.update(src["source_id"], status="extracted")
    print(f"  extracted {len(sources)} docs, {idx.count()} chunks in index")
    idx.close()


if __name__ == "__main__":
    raise SystemExit(main())
