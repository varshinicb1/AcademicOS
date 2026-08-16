"""Exports the real, already-extracted question corpus (all subjects/grades)
into a single compact JSON file for bundling as a Flutter asset -- the
on-device data source for the standalone Android build. Only the final
extracted questions + marking schemes are exported, not raw source PDFs or
parse artifacts, so this is a small fraction of academicos-data's 1.24GB.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from academicos.config import Config
from academicos.assessment.pool import get_pool
from academicos.assessment.mapping import to_question_schema


def question_to_dict(q) -> dict:
    # Exact same serialization the live FastAPI responses already use (Camel
    # alias_generator, camelCase keys) -- guarantees this is parseable by the
    # same Question.fromJson() the app already uses for HTTP responses today,
    # no hand-rolled field mapping to get subtly wrong.
    return q.model_dump(mode="json", by_alias=True)


def main() -> None:
    cfg = Config.load()

    # Discover subject/grade pairs from the registry (same source the
    # /catalog endpoint reads from).
    import sqlite3
    reg = sqlite3.connect(cfg.registry_db)
    reg.row_factory = sqlite3.Row
    pairs = reg.execute(
        "SELECT DISTINCT subject, grade FROM sources "
        "WHERE doc_type='question_paper' AND subject IS NOT NULL AND grade IS NOT NULL"
    ).fetchall()
    reg.close()

    all_questions = []
    seen_ids = set()
    for row in pairs:
        subject, grade = row["subject"], row["grade"]
        pool = get_pool(cfg, subject=subject, grade=grade)
        for pq in pool.questions:
            schema = to_question_schema(pq)
            if schema.id in seen_ids:
                continue
            seen_ids.add(schema.id)
            all_questions.append(question_to_dict(schema))
        print(f"{subject} grade {grade}: {len(pool.questions)} questions")

    out = {"questions": all_questions, "exportedCount": len(all_questions)}
    out_path = Path(__file__).resolve().parent.parent / "frontend" / "assets" / "corpus" / "questions.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(all_questions)} questions to {out_path}")
    print(f"File size: {out_path.stat().st_size / 1_000_000:.1f} MB")


if __name__ == "__main__":
    main()
