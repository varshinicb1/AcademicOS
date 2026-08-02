# AcademicOS — CBSE/NCERT Academic Brain

Evidence-grounded knowledge graph + retrieval + reasoning substrate over the
official CBSE corpus (question papers, marking schemes, model answers,
curricula, circulars, bye-laws, question banks).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .            # core (pymupdf, pydantic)
pip install -e ".[api]"     # + FastAPI server
pip install -e ".[gcs]"     # + GCS mirror
```

Configure `config/config.toml` (corpus_root, gcs_bucket), then:

```powershell
python -m academicos.cli ingest
python -m academicos.cli parse
python -m academicos.cli extract
python -m academicos.cli build-graph
python -m academicos.cli search "photosynthesis light reaction"
python -m academicos.cli serve --port 8000
python -m academicos.cli sync-gcs
python -m academicos.cli stats
```

## Architecture
See `docs/architecture.md` (layers, canonical ids, stores, ensemble parse,
graph, retrieval, governance) and `docs/roadmap.md` for the 7 phases.

## Design principles
1. Evidence-first — no fact without Provenance (doc/page/bbox/method/confidence).
2. Deterministic core, generative surface — v0.1 runs fully offline.
3. UI-swappable — FastAPI + agent toolchain is the only contract.
4. GCS mirror of every artifact (`academicos sync-gcs`).

## Tests
```powershell
pytest tests/
```
The smoke test builds a tiny corpus in a temp dir and runs the whole pipeline.
