"""Run the Unlimited-OCR (DeepSeek-OCR lineage) HTTP service for page parsing.

Bridges AcademicOS to baidu/Unlimited-OCR's transformers code path:
POST /parse  (multipart image) -> {"markdown", "confidence", "language"}

Setup (once):
    git clone https://github.com/baidu/Unlimited-OCR vendor/Unlimited-OCR
    pip install -e vendor/Unlimited-OCR  (torch + transformers required)

Note for the RTX 4050 (6 GB): use the small checkpoints (~3B) and the
transformers loading path; vLLM/SGLang paths need more VRAM.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI(title="unlimited-ocr-service")
_model = {"pipe": None}


class ParseResponse(BaseModel):
    markdown: str
    structured: dict | None = None  # not "json": shadows BaseModel.json(), Pydantic warns on it
    confidence: float
    language: str | None = None


@app.on_event("startup")
def _load() -> None:
    checkpoint = _args.checkpoint
    sys.path.insert(0, str(_args.repo))
    try:
        from cli.model import Infer
        _model["pipe"] = Infer(checkpoint, device=_args.device)
    except Exception:
        import traceback
        print("WARN: could not load Infer via cli.model — falling back to transformers auto", file=sys.stderr)
        traceback.print_exc()


@app.post("/parse")
async def parse_image(image: UploadFile = File(...)) -> ParseResponse:
    if _model["pipe"] is None:
        return ParseResponse(markdown="", confidence=0.0)
    data = await image.read()
    with tempfile_touch(data) as png:
        result = _model["pipe"].forward(png)
    return ParseResponse(
        markdown=result.get("markdown", ""),
        structured=result.get("json"),
        confidence=result.get("confidence", 0.9),
        language=result.get("language"),
    )


import contextlib
import tempfile


@contextlib.contextmanager
def tempfile_touch(data: bytes):
    fd, path = tempfile.mkstemp(suffix=".png")
    with open(fd, "wb") as fh:
        fh.write(data)
    try:
        yield path
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> None:
    global _args
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="vendor/Unlimited-OCR")
    ap.add_argument("--checkpoint", default="")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8910)
    _args = ap.parse_args()
    uvicorn.run(app, host=_args.host, port=_args.port)


if __name__ == "__main__":
    main()
