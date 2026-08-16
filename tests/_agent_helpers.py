"""Shared hermetic helpers for the agents test suite.

FakeLLM is a duck-typed stand-in for SarvamLLM: the critic and orchestrator
only ever touch ``.available`` and ``.chat_json``, so no network or API key is
ever involved. Chunk/Graph fixtures are built on real SQLite in pytest
``tmp_path``.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from academicos.agents.critic import RETRIEVE_SYSTEM
from academicos.extract.chunking import Chunk
from academicos.retrieval.index import ChunkIndex


class FakeLLM:
    """Duck-typed SarvamLLM stand-in with two response modes:

    * ``responses``: a FIFO queue of canned return values (or an ``Exception``
      instance, which is raised instead of returned).
    * ``handler``: a ``callable(messages, **kw) -> Any`` evaluated per call.

    Every ``chat_json`` invocation is recorded in ``.calls`` as
    ``(messages, kwargs)`` so tests can assert on the prompts.
    """

    def __init__(self, responses: list | None = None, *, available: bool = True,
                 handler: Callable[..., Any] | None = None):
        self.available = available
        self._responses = list(responses) if responses is not None else None
        self._handler = handler
        self.calls: list[tuple[list[dict[str, str]], dict[str, Any]]] = []

    def chat_json(self, messages: list[dict[str, str]], **kw: Any) -> Any:
        self.calls.append((messages, kw))
        if self._handler is not None:
            return self._handler(messages, **kw)
        if self._responses:
            item = self._responses.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        raise AssertionError("FakeLLM.chat_json called but no response was configured")

    @property
    def call_count(self) -> int:
        return len(self.calls)


def make_chunk(cid: str, doc_id: str, page: int, heading: str, text: str) -> Chunk:
    return Chunk(id=cid, document_id=doc_id, page=page,
                 heading_path=[heading] if heading else [], text=text)


def build_index(tmp_path, chunks: list[Chunk]) -> ChunkIndex:
    idx = ChunkIndex(Path(tmp_path) / "idx.sqlite")
    if chunks:
        idx.add(chunks)
    return idx


def scoring_handler(scores_by_doc: dict[str, dict], *, retrieve: bool = True) -> Callable:
    """FakeLLM handler that answers the retrieve-decision call, then returns a
    per-document canned score for each evidence-path call.

    The retrieve decision is recognized by the RETRIEVE_SYSTEM system message;
    the document being scored is parsed out of the ``[<doc> p.<page>]`` marker
    inside the candidate-answer text.
    """

    def handler(messages: list[dict[str, str]], **kw: Any) -> dict:
        if messages and messages[0]["content"] == RETRIEVE_SYSTEM:
            return {"retrieve": retrieve}
        user = messages[1]["content"] if len(messages) > 1 else ""
        m = re.search(r"\[([^\]]+?)\s+p\.", user)
        doc = m.group(1) if m else None
        return scores_by_doc.get(doc, {"relevant": False, "support": "none", "utility": 1})

    return handler