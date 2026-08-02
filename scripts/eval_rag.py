"""End-to-end RAG evaluation harness for AcademicOS.

Adapted from praj2408/RAG-Enhanced-NCERT-Tutor (MIT License):
evaluation_script.py's structure (question CSV -> retrieve -> generate ->
score). Metric functions are dependency-free reimplementations in
academicos.eval.metrics (rouge_l, bleu1, token_f1, exact_match); retrieval
quality uses the existing precision@k / recall@k / mrr / ndcg_at_k with
a token-overlap relevance rule.

Relevance (retrieval gold): a chunk is relevant when it contains >= 40% of
the reference answer's tokens. This mirrors the tutor's SequenceMatcher
heuristic but is token-based. recall@k is computed against the retrieved
window (full-corpus relevance is unbounded here) -- treat it as window
recall, not corpus recall.

Usage: python eval_rag.py [--questions FILE.csv] [--limit N] [--k N] [--no-llm]
CSV needs columns 'Question' and 'Answer'.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\varsh\OneDrive\Documents\Sarvam\AcademicOS\src")

from academicos.config import Config
from academicos.eval.metrics import (answer_groundedness, bleu1, exact_match,
                                     mrr, ndcg_at_k, precision_at_k, recall_at_k,
                                     rouge_l, token_f1)
from academicos.graph.store import GraphStore
from academicos.retrieval.hybrid import HybridRetriever
from academicos.retrieval.index import ChunkIndex

TOK = re.compile(r"[a-z0-9]+", re.I)
RELEVANCE_OVERLAP = 0.4


def load_dataset(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        q, a = r.get("Question", "").strip(), r.get("Answer", "").strip()
        if q and a:
            out.append({"question": q, "answer": a})
    return out[:limit] if limit else out


def is_relevant(chunk_text: str, answer: str) -> bool:
    a = set(TOK.findall(answer.lower()))
    if not a:
        return False
    c = set(TOK.findall(chunk_text.lower()))
    return len(c & a) / len(a) >= RELEVANCE_OVERLAP


def run(questions_csv: Path, limit: int | None, k: int, use_llm: bool) -> int:
    cfg = Config.load()
    index = ChunkIndex(cfg.index_db)
    graph = GraphStore(cfg.graph_db)
    retriever = HybridRetriever(index, graph)
    llm = None
    if use_llm and cfg.llm_api_key:
        from academicos.llm.sarvam import SarvamLLM
        llm = SarvamLLM(api_key=cfg.llm_api_key, base_url=cfg.llm_base_url,
                        model=cfg.llm_model, timeout=cfg.llm_timeout)
        if not llm.available:
            llm = None

    dataset = load_dataset(questions_csv, limit)
    print(f"evaluating {len(dataset)} questions (k={k}, llm={'on' if llm else 'off'})")

    metrics = {"precision_at_k": [], "recall_at_k": [], "mrr": [], "ndcg_at_k": [],
               "rouge_l": [], "bleu1": [], "token_f1": [], "exact_match": [],
               "groundedness": [], "retrieval_ms": [], "generation_ms": []}
    rows_out = []

    for i, sample in enumerate(dataset, 1):
        q, ref = sample["question"], sample["answer"]
        t0 = time.perf_counter()
        hits = retriever.search(q, limit=k * 2)
        retrieval_ms = (time.perf_counter() - t0) * 1000

        retrieved = [h.chunk for h in hits][:k]
        relevant_ids = {h.chunk.id for h in hits if is_relevant(h.chunk.text, ref)}
        order = [h.chunk.id for h in hits]
        relevant_dict = {cid: 1.0 for cid in relevant_ids}

        metrics["precision_at_k"].append(precision_at_k(relevant_ids, order, k))
        metrics["recall_at_k"].append(recall_at_k(relevant_ids, order, k))
        metrics["mrr"].append(mrr(relevant_ids, order))
        metrics["ndcg_at_k"].append(ndcg_at_k(relevant_dict, order, k))
        metrics["retrieval_ms"].append(retrieval_ms)

        candidate = ""
        if llm:
            context = "\n\n".join(c.text for c in retrieved[:5])
            prompt = (f"Answer the question based ONLY on the following context:\n"
                      f"{context}\n\nQuestion: {q}")
            t1 = time.perf_counter()
            candidate = llm.chat([{"role": "user", "content": prompt}])
            metrics["generation_ms"].append((time.perf_counter() - t1) * 1000)
        else:
            metrics["generation_ms"].append(0.0)

        metrics["rouge_l"].append(rouge_l(ref, candidate))
        metrics["bleu1"].append(bleu1(ref, candidate))
        metrics["token_f1"].append(token_f1(ref, candidate))
        metrics["exact_match"].append(exact_match(ref, candidate))
        metrics["groundedness"].append(
            answer_groundedness(candidate, [c.text for c in retrieved]) if candidate else 0.0)

        rows_out.append({
            "question": q, "retrieved_relevant": len(relevant_ids),
            "top_hit_relevant": int(bool(relevant_ids)),
            "p@k": metrics["precision_at_k"][-1], "r@k": metrics["recall_at_k"][-1],
            "mrr": metrics["mrr"][-1], "ndcg@k": metrics["ndcg_at_k"][-1],
            "rouge_l": metrics["rouge_l"][-1], "bleu1": metrics["bleu1"][-1],
            "token_f1": metrics["token_f1"][-1],
            "exact_match": metrics["exact_match"][-1],
            "groundedness": metrics["groundedness"][-1],
            "candidate": candidate[:200].replace("\n", " "),
        })
        print(f"[{i}/{len(dataset)}] p@{k}={metrics['precision_at_k'][-1]:.2f} "
              f"r@{k}={metrics['recall_at_k'][-1]:.2f} "
              f"mrr={metrics['mrr'][-1]:.2f} "
              f"f1={metrics['token_f1'][-1]:.2f} "
              f"rougeL={metrics['rouge_l'][-1]:.2f} "
              f"grounded={metrics['groundedness'][-1]:.2f} "
              f"({metrics['retrieval_ms'][-1]:.0f}ms retr)")

    out_csv = Path("eval_rag_results.csv")
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out
                                else ["question"])
        writer.writeheader()
        writer.writerows(rows_out)

    print("\n-- averages --")
    for name in ("precision_at_k", "recall_at_k", "mrr", "ndcg_at_k",
                 "rouge_l", "bleu1", "token_f1", "exact_match", "groundedness"):
        vals = metrics[name]
        if vals:
            print(f"  {name:<14} {sum(vals) / len(vals):.3f}")
    if metrics["retrieval_ms"]:
        print(f"  {'retrieval_ms':<14} {sum(metrics['retrieval_ms']) / len(metrics['retrieval_ms']):.0f}")
    print(f"results -> {out_csv}")
    index.close(); graph.close()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="End-to-end RAG evaluation")
    ap.add_argument("--questions", required=True, help="CSV with Question,Answer columns")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--no-llm", action="store_true", help="skip generation; retrieval only")
    args = ap.parse_args()
    return run(Path(args.questions), args.limit, args.k, not args.no_llm)


if __name__ == "__main__":
    sys.exit(main())
