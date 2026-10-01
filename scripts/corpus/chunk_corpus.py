"""Chunk the extracted NCERT chapters for per-chapter RAG.

Design is driven by the two hard limits and by provenance:

- `@cf/baai/bge-m3` accepts 512 input tokens, so chunks are capped well under
  that. Indic text tokenizes far less efficiently than English (XLM-R
  sentencepiece), so the budget is measured in *estimated* tokens, not chars.
- The heading tree is the only structure that survives extraction, so chunks
  are cut on heading boundaries and carry their heading breadcrumb. That
  breadcrumb is what lets question generation say *which section* an answer
  came from.
- `text_quality` / `quote_exact` propagate to every chunk. A question that
  quotes a legacy-decoded Hindi chunk verbatim is a defect, so downstream
  generation must be able to filter on it without re-reading the Markdown.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
from pathlib import Path

DEVANAGARI = re.compile(r"[\u0900-\u097F]")
TELUGU = re.compile(r"[\u0C00-\u0C7F]")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
SENT_SPLIT = re.compile(r"(?<=[।?!.])\s+")

# bge-m3 is a 512-token model; stay under it with room for the heading prefix.
TARGET_TOKENS = 340
HARD_TOKENS = 430
OVERLAP_SENTENCES = 1
MIN_CHUNK_CHARS = 220


def est_tokens(text: str) -> int:
    """Conservative token estimate for a mixed English/Devanagari string.

    Latin script runs ~1 token per 4 chars. Devanagari is denser in tokens
    (roughly 1 per 2), and under-estimating here would push chunks past the
    model limit and get them silently truncated by Workers AI.
    """
    dev = sum(len(m) for m in DEVANAGARI.findall(text))
    tel = sum(len(m) for m in TELUGU.findall(text))
    rest = max(len(text) - dev - tel, 0)
    return int(rest / 4.0 + (dev + tel) / 2.0)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Return (front matter dict, body). Tolerates a missing/short header."""
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    head = raw[3:end]
    body = raw[end + 4 :].lstrip("\n")
    meta: dict = {}
    for line in head.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, body


def sections(body: str) -> list[tuple[list[str], str]]:
    """Split body into (heading_breadcrumb, text) sections."""
    out: list[tuple[list[str], str]] = []
    stack: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        text = "\n".join(buf).strip()
        if text:
            out.append((list(stack), text))
        buf.clear()

    for line in body.splitlines():
        m = HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            del stack[level - 1 :]
            stack.append(title)
            continue
        buf.append(line)
    flush()
    return out


def split_long(text: str, budget: int) -> list[str]:
    """Split over-long text on sentence boundaries, never mid-word."""
    sentences = [s for s in SENT_SPLIT.split(text) if s.strip()]
    pieces: list[str] = []
    cur = ""
    for s in sentences:
        if cur and est_tokens(cur + " " + s) > budget:
            pieces.append(cur.strip())
            cur = s
        else:
            cur = f"{cur} {s}".strip()
        # A single oversized sentence (tables, poems) still has to break.
        while est_tokens(cur) > HARD_TOKENS:
            words, acc = cur.split(), ""
            for w in words:
                if acc and est_tokens(acc + " " + w) > budget:
                    break
                acc = f"{acc} {w}".strip()
            if not acc:
                acc = cur[:budget * 3]
            pieces.append(acc)
            cur = " ".join(words[len(acc.split()):])
    if cur.strip():
        pieces.append(cur.strip())
    return pieces


def chunk_section(breadcrumb: list[str], text: str) -> list[str]:
    if est_tokens(text) <= TARGET_TOKENS:
        return [text]
    pieces = split_long(text, TARGET_TOKENS)
    # Overlap must EXTEND the new chunk, never replace the previous one.
    # (Rewriting out[-1] here silently deletes the prior piece's body text.)
    out: list[str] = []
    prev_tail = ""
    for piece in pieces:
        chunk = f"{prev_tail} {piece}".strip() if prev_tail else piece
        if prev_tail and est_tokens(chunk) > HARD_TOKENS:
            chunk = piece  # too tight to prepend; keep the clean piece
        out.append(chunk)
        prev_tail = " ".join(
            SENT_SPLIT.split(piece)[-OVERLAP_SENTENCES:]
        ).strip()
    return out


def chunk_file(path: Path) -> tuple[dict, list[dict]]:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    chapter_id = meta.get("id") or path.stem
    base = {
        "chapter_id": chapter_id,
        "namespace": chapter_id,  # Vectorize namespace == one chapter
        "book_code": meta.get("book_code", ""),
        "class": int(meta["class"]) if meta.get("class", "").isdigit() else None,
        "subject": meta.get("subject", ""),
        "language": meta.get("language", ""),
        "chapter_no": int(meta["chapter"]) if meta.get("chapter", "").isdigit() else None,
        "text_quality": meta.get("text_quality", "native-text-layer"),
        "quote_exact": meta.get("quote_exact", "true") == "true",
        "source_pdf": meta.get("source_pdf", ""),
    }
    chunks: list[dict] = []
    source_chars = 0
    emitted_chars = 0
    dropped_chars = 0
    for crumb, text in sections(body):
        source_chars += len(text)
        for piece in chunk_section(crumb, text):
            if len(piece) < MIN_CHUNK_CHARS:
                dropped_chars += len(piece)
                continue
            emitted_chars += len(piece)
            crumb_text = " > ".join(crumb)
            idx = len(chunks)
            cid = f"{chapter_id}:{idx:03d}"
            rec = dict(base)
            rec.update(
                {
                    "id": cid,
                    "chunk_index": idx,
                    "heading_path": crumb_text,
                    # Embed the breadcrumb: a bare sentence from a chapter is
                    # far weaker evidence than "Ch 1 > Chemical Reactions > ..."
                    "embed_text": f"{crumb_text}\n{piece}" if crumb_text else piece,
                    "text": piece,
                    "n_chars": len(piece),
                    "est_tokens": est_tokens(piece),
                    "text_sha": hashlib.sha256(piece.encode("utf-8")).hexdigest()[:16],
                }
            )
            chunks.append(rec)

    # Invariant: every character handed to the splitter must leave it. Overlap
    # may duplicate text, so the total may exceed the input -- never fall short.
    if source_chars and emitted_chars + dropped_chars < source_chars * 0.99:
        raise SystemExit(
            f"text loss in {chapter_id}: in={source_chars} "
            f"emitted={emitted_chars} dropped={dropped_chars}"
        )
    base["_source_chars"] = source_chars
    base["_dropped_chars"] = dropped_chars
    return base, chunks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="chapter root with .md files")
    ap.add_argument("--out", required=True, help="output .jsonl[.gz]")
    args = ap.parse_args()

    src = Path(args.src)
    files = sorted(src.rglob("*.md"))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_chunks = 0
    n_chapters = 0
    per_lang: dict[str, int] = {}
    tok_hist: list[int] = []
    quality: dict[str, int] = {}
    ids: set[str] = set()

    raw = io.StringIO()
    for i, f in enumerate(files, 1):
        base, chunks = chunk_file(f)
        if not chunks:
            print(f"  !! no chunks: {f}")
            continue
        n_chapters += 1
        n_chunks += len(chunks)
        per_lang[base["language"]] = per_lang.get(base["language"], 0) + len(chunks)
        quality[base["text_quality"]] = quality.get(base["text_quality"], 0) + len(chunks)
        for c in chunks:
            if c["id"] in ids:
                raise SystemExit(f"duplicate vector id {c['id']}")
            ids.add(c["id"])
            tok_hist.append(c["est_tokens"])
            raw.write(json.dumps(c, ensure_ascii=False) + "\n")
        if i % 50 == 0:
            print(f"  [{i}/{len(files)}] {n_chapters} chapters -> {n_chunks} chunks")

    data = raw.getvalue().encode("utf-8")
    if out_path.suffix == ".gz":
        out_path.write_bytes(gzip.compress(data, 6))
    else:
        out_path.write_bytes(data)

    tok_hist.sort()
    over = sum(1 for t in tok_hist if t > HARD_TOKENS)
    print(f"\nwrote {out_path}  ({out_path.stat().st_size/1e6:.1f} MB)")
    print(f"  chapters={n_chapters}  chunks={n_chunks}  mean={n_chunks/max(n_chapters,1):.1f}/chapter")
    print(f"  est tokens: p50={tok_hist[len(tok_hist)//2]} p95={tok_hist[int(len(tok_hist)*0.95)]} max={tok_hist[-1]}")
    print(f"  chunks over {HARD_TOKENS} tokens: {over}")
    print(f"  by language: {per_lang}")
    print(f"  by text_quality: {quality}")
    print(f"  longest vector id: {max(len(i) for i in ids)} bytes (limit 64)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
