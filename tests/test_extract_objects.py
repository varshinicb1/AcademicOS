"""Hermetic tests for the extract layer.

Covers the deterministic heuristics: question/marking-point/blueprint
extraction, heading-anchored chunking, layout reclassification, table
detection/markdown, Sarvam-LLM OpenIE with a fake llm, and the pure helpers
in local_ie. No spacy models, no network, no LLM.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from academicos.extract.academic import (
    _canonical_qid,
    _guess_bloom,
    _guess_type,
    extract_blueprint,
    extract_marking_points,
    extract_questions,
)
from academicos.extract.chunking import Chunk, chunk_document
from academicos.extract.layout import analyze_page_layout
from academicos.extract.openie import OpenIE, OpenIEResult, clean, json_dumps
from academicos.extract.tables import Cell, Table, detect_tables, extract_table_marks
from academicos.extract.local_ie import _clean_concept, _is_meaningful_concept
from academicos.models.common import BoundingBox
from academicos.models.document import Block, Page, ParsedDocument
from academicos.models.enums import BlockKind, BloomLevel, DocType


def _block(text, order=0, kind=BlockKind.PARAGRAPH, fontsize=None):
    return Block(
        kind=kind,
        text=text,
        bbox=BoundingBox(x0=0, y0=order, x1=500, y1=order + 10),
        order=order,
        metadata={"fontsize_estimate": fontsize} if fontsize else {},
    )


def _page(blocks, page_no=1, text=""):
    return Page(page_no=page_no, blocks=blocks, text=text or "\n".join(b.text for b in blocks))


def _doc(blocks, page_no=1, doc_id="doc1", page_text=""):
    return ParsedDocument(
        document_id=doc_id,
        doc_type=DocType.QUESTION_PAPER,
        title="paper",
        pages=[_page(blocks, page_no, page_text)],
    )


# --------------------------------------------------------------------------- #
# extract_questions
# --------------------------------------------------------------------------- #

def test_extract_questions_basic():
    doc = _doc([
        _block("Section A", kind=BlockKind.HEADING),
        _block("1. What is photosynthesis? (2 marks)", order=1),
        _block("(a) Define it in one sentence.", order=2),
        _block("2. Compare aerobic and anaerobic respiration. (3 marks)", order=3),
    ])
    qs = extract_questions(doc, DocType.QUESTION_PAPER)
    assert len(qs) == 2
    q1 = qs[0]
    assert q1.q_no == "1"
    assert q1.marks == 2.0
    assert q1.canonical_id == _canonical_qid("doc1", "1")
    assert q1.question_paper_id == "doc1"
    assert len(q1.parts) == 1
    assert q1.parts[0].part == "a"
    assert q1.parts[0].canonical_id == _canonical_qid("doc1", "1a")
    q2 = qs[1]
    assert q2.q_no == "2"
    assert q2.marks == 3.0
    assert q2.parts == []


def test_extract_questions_guesses_type_and_bloom():
    doc = _doc([
        _block("3. MCQ: Choose the correct option. (1 mark)", order=0),
        _block("4. Long answer type question on respiration. (5 marks)", order=1),
        _block("5. Calculate the resistance. (2 marks)", order=2),
    ])
    qs = extract_questions(doc, DocType.QUESTION_PAPER)
    assert qs[0].question_type == "mcq"
    assert qs[1].question_type == "long_answer"
    assert qs[2].cognitive == BloomLevel.APPLY
    assert qs[0].cognitive is None


def test_extract_questions_appends_continuation_text():
    doc = _doc([
        _block("1. State the law of conservation of energy. (2 marks)", order=0),
        _block("It implies energy can neither be created nor destroyed.", order=1),
        _block("(a) Give one example.", order=2),
        _block("A pendulum is a classic example.", order=3),
    ])
    qs = extract_questions(doc, DocType.QUESTION_PAPER)
    assert len(qs) == 1
    assert "conservation of energy" in qs[0].source_text
    assert "neither be created nor destroyed" in qs[0].source_text
    assert "A pendulum is a classic example" in qs[0].source_text


def test_guess_type_and_bloom_unit_level():
    assert _guess_type("1. Multiple choice question") == "mcq"
    assert _guess_type("2. Case study based") == "case_study"
    assert _guess_type("3. Short answer type") == "short_answer"
    assert _guess_type("4. Essay") == "long_answer"
    assert _guess_type("5. Whatever") == "unknown"
    assert _guess_bloom("Explain the process") == BloomLevel.UNDERSTAND
    assert _guess_bloom("Recall the definition") == BloomLevel.REMEMBER
    assert _guess_bloom("Design an experiment") == BloomLevel.CREATE
    assert _guess_bloom("Nothing special") is None


# --------------------------------------------------------------------------- #
# extract_marking_points / extract_blueprint
# --------------------------------------------------------------------------- #

def test_extract_marking_points():
    doc = _doc([
        _block("1. (2 marks) Correct statement of the law.", order=0),
        _block("(1 mark) Identification of example.", order=1),
        _block("No marks here, just commentary.", order=2),
        _block("(2.5 marks) partial credit awarded.", order=3),
    ])
    mps = extract_marking_points(doc)
    assert len(mps) == 3
    assert mps[0].point_no == 1
    assert mps[0].marks == 2.0
    assert mps[1].marks == 1.0
    assert mps[2].marks == 2.5
    assert all(mp.answer_scheme_id == "doc1" for mp in mps)


def test_extract_blueprint():
    doc = _doc([_block("Design of Question Paper", order=0)], page_text="Design of Question Paper with marks table")
    bps = extract_blueprint(doc)
    assert len(bps) == 1
    assert bps[0].canonical_id.startswith("cbse:bp:doc1:")
    doc2 = _doc([_block("Nothing here", order=0)])
    assert extract_blueprint(doc2) == []


# --------------------------------------------------------------------------- #
# chunk_document
# --------------------------------------------------------------------------- #

def test_chunk_heading_anchored():
    doc = _doc([
        _block("Unit 1: Electricity", kind=BlockKind.HEADING),
        _block("Current is the flow of electric charge.", order=1),
        _block("Resistance opposes current.", order=2),
    ])
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.heading == "Unit 1: Electricity"
    assert c.heading_path == ["Unit 1: Electricity"]
    assert "Current is the flow" in c.text
    assert c.page == 1
    assert c.id == "doc1:p1:0"


def test_chunk_splits_on_heading_via_regex():
    # a PARAGRAPH-kind block that looks like a heading still splits
    doc = _doc([
        _block("Chapter 2: Motion", order=0),
        _block("Motion is a change in position.", order=1),
        _block("Speed is the distance covered.", order=2),
    ])
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].heading_path == ["Chapter 2: Motion"]


def test_chunk_multiple_heads_and_pages():
    blocks_p1 = [_block("Unit 1: Light", kind=BlockKind.HEADING),
                 _block("Light travels in straight lines.", order=1)]
    blocks_p2 = [_block("Unit 2: Sound", kind=BlockKind.HEADING),
                 _block("Sound needs a medium.", order=1)]
    doc = ParsedDocument(
        document_id="doc1",
        doc_type=DocType.QUESTION_PAPER,
        title="t",
        pages=[_page(blocks_p1, 1), _page(blocks_p2, 2)],
    )
    chunks = chunk_document(doc)
    # heading_path persists across pages, so the second chunk nests under the first
    assert [c.heading for c in chunks] == ["Unit 1: Light", "Unit 1: Light > Unit 2: Sound"]
    assert [c.page for c in chunks] == [1, 2]


def test_chunk_max_chars_triggers_flush():
    p1 = "A" * 100
    p2 = "B" * 100
    p3 = "C" * 100
    doc = _doc([_block(p1, order=0), _block(p2, order=1), _block(p3, order=2)])
    chunks = chunk_document(doc, max_chars=150)
    assert len(chunks) == 2
    assert chunks[0].text.startswith("A" * 100)
    assert chunks[0].text.endswith("B" * 100)
    assert chunks[1].text == p3
    # char span tracking across chunks
    assert chunks[1].char_start == chunks[0].char_end


def test_chunk_heading_path_capped_and_truncated():
    heads = ["Unit 1: Deeply nested topic heading", "Chapter 2", "Section 3", "Extra"]
    doc = _doc([_block(h, order=i, kind=BlockKind.HEADING) for i, h in enumerate(heads)] +
               [_block("Body text for the chunk.", order=10)])
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert len(chunks[0].heading_path) == 3  # capped
    assert all(len(h) <= 80 for h in chunks[0].heading_path)


# --------------------------------------------------------------------------- #
# analyze_page_layout
# --------------------------------------------------------------------------- #

def test_layout_reclassifies_blocks():
    page = _page([
        _block("4. Notes without marks here", order=0),
        _block("3. Two charges attract. (2 marks)", order=1),
        _block("a. sub part listing", order=2),
    ])
    analyze_page_layout(page)
    kinds = [b.kind for b in page.blocks]
    assert kinds[0] == BlockKind.LIST
    assert kinds[1] == BlockKind.QUESTION
    assert kinds[2] == BlockKind.LIST


def test_layout_keeps_paragraph_after_heading_without_marks():
    page = _page([
        _block("CHAPTER 1: Intro", order=0, fontsize=20),
        _block("5. This is a numbered prose paragraph after a heading.", order=1),
    ])
    analyze_page_layout(page)
    assert page.blocks[1].kind == BlockKind.PARAGRAPH


def test_layout_font_delta_promotes_short_text():
    page = _page([
        _block("Photosynthesis and its significance in green plants for food.", order=0, fontsize=16),
        _block("Chlorophyll is the pigment responsible for green colour.", order=1, fontsize=10),
    ])
    analyze_page_layout(page)
    assert page.blocks[0].kind == BlockKind.HEADING
    assert page.blocks[1].kind == BlockKind.PARAGRAPH


# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #

def test_table_to_markdown():
    tbl = Table(page_no=1, n_rows=2, n_cols=2,
                cells=[Cell(0, 0, "Topic"), Cell(0, 1, "Marks"),
                       Cell(1, 0, "Electricity"), Cell(1, 1, "20")])
    md = tbl.to_markdown()
    assert md.splitlines()[0] == "| Topic | Marks |"
    assert md.splitlines()[1].startswith("|---|")
    assert md.splitlines()[2] == "| Electricity | 20 |"


def test_table_to_markdown_escapes_pipe():
    tbl = Table(page_no=1, n_rows=1, n_cols=1, cells=[Cell(0, 0, "a|b")])
    assert "a\\|b" in tbl.to_markdown()


def test_detect_tables_from_rawdict():
    page_raw = {
        "blocks": [
            {"type": 0, "lines": [
                {"bbox": [0, 0, 200, 10],
                 "spans": [{"bbox": [0, 0, 50, 10], "text": "Topic"},
                           {"bbox": [60, 0, 120, 10], "text": "Marks"},
                           {"bbox": [130, 0, 200, 10], "text": "Weight"}]},
                {"bbox": [0, 20, 140, 30],
                 "spans": [{"bbox": [0, 20, 60, 30], "text": "Electricity"},
                           {"bbox": [70, 20, 100, 30], "text": "20"},
                           {"bbox": [110, 20, 140, 30], "text": "25%"}]},
            ]}
        ]
    }
    tables = detect_tables(page_raw, 3)
    assert len(tables) == 2
    assert tables[0].page_no == 3
    assert tables[0].n_cols == 3
    assert tables[0].cells[0].text == "Topic"
    assert tables[1].cells[0].text == "Electricity"


def test_detect_tables_requires_multiple_span_entries():
    # a single span produces a single entry -> below the >=2 line gate
    page_raw = {"blocks": [{"type": 0, "lines": [
        {"bbox": [0, 0, 100, 10],
         "spans": [{"bbox": [0, 0, 120, 10], "text": "a lone cell"}]},
    ]}]}
    assert detect_tables(page_raw, 1) == []


def test_extract_table_marks():
    tbl = Table(page_no=1, n_rows=2, n_cols=2,
                cells=[Cell(0, 0, "Topic"), Cell(0, 1, "Marks"),
                       Cell(1, 0, "Electricity"), Cell(1, 1, "20 marks")])
    out = extract_table_marks(tbl)
    assert out["r1c1"] == 20.0
    assert "r0c0" not in out


# --------------------------------------------------------------------------- #
# OpenIE
# --------------------------------------------------------------------------- #

class _FakeLLM:
    def __init__(self, available=True, ner=None, triples=None):
        self.available = available
        self._ner = ner or {"named_entities": ["Photosynthesis", "sunlight"]}
        self._triples = triples or [["Photosynthesis", "requires", "sunlight"]]
        self.seen_passages = []

    def chat_json(self, messages, temperature=0.0, max_tokens=4096):
        system = messages[0]["content"]
        self.seen_passages.append(messages[-1]["content"])
        if '"triples"' in system:
            return {"triples": self._triples}
        return self._ner


def test_openie_skips_when_llm_unavailable():
    oie = OpenIE(_FakeLLM(available=False))
    res = oie.extract("Photosynthesis is the process green plants use.")
    assert res == OpenIEResult()


def test_openie_skips_empty_text():
    oie = OpenIE(_FakeLLM())
    assert oie.extract("   ") == OpenIEResult()


def test_openie_extracts_entities_and_triples():
    oie = OpenIE(_FakeLLM())
    res = oie.extract("Photosynthesis is the process green plants use with sunlight.")
    assert res.entities == ["Photosynthesis", "sunlight"]
    assert res.triples == [("Photosynthesis", "requires", "sunlight")]


def test_openie_no_relations_without_entities():
    oie = OpenIE(_FakeLLM(ner={"named_entities": []}))
    res = oie.extract("Some passage text without any entity.")
    assert res.entities == []
    assert res.triples == []


def test_openie_truncates_long_passage():
    llm = _FakeLLM()
    oie = OpenIE(llm, max_chars=200)
    oie.extract("X" * 1000)
    # _ner receives at most 600 chars; extract truncates to max_chars first
    assert all(len(p) <= 600 for p in llm.seen_passages)


def test_openie_clean_and_json_dumps():
    assert clean("  a   b\tc  ") == "a b c"
    assert json_dumps(["x", "y"]) == '["x", "y"]'


# --------------------------------------------------------------------------- #
# local_ie pure helpers
# --------------------------------------------------------------------------- #

def test_is_meaningful_concept():
    assert _is_meaningful_concept("Photosynthesis") is True
    assert _is_meaningful_concept("resistance") is True
    assert _is_meaningful_concept("process") is False       # generic noun
    assert _is_meaningful_concept("chapter 3") is False     # structural prefix
    assert _is_meaningful_concept("answer") is False
    assert _is_meaningful_concept("q.") is False
    assert _is_meaningful_concept("a") is False             # too short
    assert _is_meaningful_concept("1 2 3") is False         # no letters
    assert _is_meaningful_concept("x" * 61) is False        # too long


def test_clean_concept_strips_stopwords():
    class Tok:
        def __init__(self, text):
            self.text = text

    span = [Tok("the"), Tok("green"), Tok("plants"), Tok("a"), Tok("India")]
    assert _clean_concept(span) == "green plants India"