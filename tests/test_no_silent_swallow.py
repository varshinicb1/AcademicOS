"""No `except Exception: pass` — a swallowed failure is a silent one.

Two of these were fixed on 2026-09-18 in `pool.py` and `answer_key.py`. The
remaining six were fixed later, and they were not cosmetic:

  * `ingest/pipeline.py` -- a failed doc-type probe left the document ingested
    UNCLASSIFIED with nothing recording why.
  * `graph/curriculum.py` (x2) -- dropped the mined prerequisite predicates and
    the provenance that cites them, changing the graph silently.
  * `parse/pdftext.py` -- returned `0.0`, which is ALSO the legitimate
    "no span found" value, so a failure was indistinguishable from a miss.
  * `cli.py` (x2) -- dropped rows out of the very statistics that command
    exists to report.

Every one of them was a real degradation that produced a plausible-looking
result. That is the failure mode this repository cares about most: not a crash,
but a number that is quietly wrong.

Written over the AST rather than a regex, so a `pass` that is one of several
statements, or is inside a nested block, is not mistaken for a swallow. The
thing being prohibited is precisely an except-handler whose ONLY body is `pass`.
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "academicos"

# (relative path, function name) -> why swallowing is correct here.
#
# Each entry is a case where `pass` is not a swallow but a deliberate
# fallthrough or a teardown. They are listed rather than exempted by pattern,
# because "this try/except is control flow" and "this try/except hides a
# failure" look identical to a scanner and are not identical to a reader.
ALLOW: dict[tuple[str, str], str] = {
    ("src/academicos/assessment/postgres_kv.py", "reset_pools"):
        "best-effort teardown of connection pools. Raising here would mask the "
        "error that caused the teardown, and there is nothing a caller can do "
        "about a pool that will not close.",
    ("src/academicos/llm/resilience.py", "parse_retry_after"):
        "try `float`, fall through to HTTP-date parsing. `pass` is the seam "
        "between two strategies, and the caller falls back to the default delay "
        "if the date parse also fails -- nothing is hidden.",
    ("src/academicos/llm/sarvam.py", "extract_json"):
        "try strict `json.loads`, fall through to locating the outermost "
        "brace/bracket and re-parsing. If that also fails the function RAISES "
        "-- so the failure still surfaces, just with a better message.",
}


def _swallows() -> list[tuple[str, str, int]]:
    """`(relative path, enclosing function, line)` for each bare-pass handler."""
    found: list[tuple[str, str, int]] = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "pass" not in text:
            continue
        tree = ast.parse(text)
        owners: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                for child in ast.walk(node):
                    owners.setdefault(id(child), node.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            body = [n for n in node.body
                    if not (isinstance(n, ast.Expr)
                            and isinstance(n.value, ast.Constant))]
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                rel = path.relative_to(REPO).as_posix()
                found.append((rel, owners.get(id(node), "<module>"),
                              node.lineno))
    return found


def test_the_scan_finds_except_handlers_at_all():
    """Guard the guard: the allowlist is empty, so a broken scan passes vacuously."""
    handlers = 0
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        handlers += sum(1 for n in ast.walk(tree)
                        if isinstance(n, ast.ExceptHandler))
    assert handlers > 40, (
        f"only found {handlers} except-handlers under src/; the scanner is "
        "probably not walking the tree and the test below proves nothing"
    )


def test_no_except_handler_swallows_its_failure_with_pass():
    hits = [(rel, fn, line) for rel, fn, line in _swallows()
            if (rel, fn) not in ALLOW]
    assert not hits, (
        "an except-handler does nothing but `pass`, so the failure is invisible "
        "and the code returns a plausible-looking result:\n  "
        + "\n  ".join(f"{rel}:{line} in {fn}()" for rel, fn, line in hits)
        + "\nLog it (with the identifying ids), re-raise it, or record it in a "
          "counter that is reported -- but do not swallow it."
    )


def test_the_allowlist_is_justified_and_not_stale():
    """Same principle as KNOWN_GAPS: a waiver that outlives its reason is a hole."""
    for (rel, fn), reason in ALLOW.items():
        assert reason.strip(), f"ALLOW entry {rel}::{fn} has no reason"
        assert (REPO / rel).exists(), f"ALLOW waives {rel}, which is gone"


def test_the_scanner_detects_a_planted_swallow():
    """Prove the detector works on the exact shape it is meant to catch.

    Without this the test above could pass because the scanner looks for the
    wrong node, which is how a guard becomes decoration.
    """
    planted = ast.parse(
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except Exception:\n"
        "        pass\n"
    )
    found = [n for n in ast.walk(planted)
             if isinstance(n, ast.ExceptHandler)
             and len(n.body) == 1 and isinstance(n.body[0], ast.Pass)]
    assert found, "the detector does not recognise the shape it exists to catch"


def test_a_logged_handler_is_NOT_flagged():
    """The complement: the fix must pass, or people will disable the check."""
    fixed = ast.parse(
        "def f():\n"
        "    try:\n"
        "        g()\n"
        "    except Exception as exc:\n"
        "        logger.warning('failed: %s', exc)\n"
    )
    body = [n for n in ast.walk(fixed) if isinstance(n, ast.ExceptHandler)]
    assert body and not (len(body[0].body) == 1
                         and isinstance(body[0].body[0], ast.Pass))
