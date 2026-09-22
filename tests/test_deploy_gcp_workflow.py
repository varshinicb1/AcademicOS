"""deploy-gcp.yml must not ship storage whose GCS semantics were never verified.

Why this exists: storage/blobs.py's single-writer guarantee for the curriculum
snapshot (generation preconditions, a real 412, md5 format, the pinned
download) had only ever run against an in-memory fake. The workflow ran the
real-bucket test only when GCS_TEST_BUCKET was set, and otherwise emitted a
::warning:: and deployed anyway -- "never verified" shipped green. For a
school deployment that must block. An operator can still deploy without the
check, but only by saying so: ALLOW_UNVERIFIED_GCS=true.

The `if:` expressions are evaluated here for every combination of the two
variables, so the test checks the decision the workflow actually makes, not
just that some string is present in the file.
"""
from __future__ import annotations

import ast
import itertools
import re
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "deploy-gcp.yml"


def _backend_steps() -> list[dict]:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return doc["jobs"]["backend"]["steps"]


def _evaluate(expr: str, variables: dict[str, str]) -> bool:
    """The small subset of GitHub expression syntax these steps use:
    `vars.NAME`, string literals, ==, !=, &&, ||, parentheses. Anything else
    fails loudly rather than being guessed at."""
    expr = expr.strip()
    if expr.startswith("${{") and expr.endswith("}}"):
        expr = expr[3:-2].strip()
    leftover = re.sub(r"vars\.[A-Z_]+|'[^']*'|==|!=|&&|\|\||[()\s]", "", expr)
    assert not leftover, f"unsupported expression syntax in {expr!r}: {leftover!r}"
    py = re.sub(r"vars\.([A-Z_]+)", lambda m: repr(variables.get(m.group(1), "")), expr)
    py = py.replace("&&", " and ").replace("||", " or ")
    return bool(_walk(ast.parse(py, mode="eval").body))


def _walk(node: ast.AST):
    """Evaluate the parsed expression by hand -- string constants, ==/!=,
    and/or -- instead of eval()."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BoolOp):
        values = [_walk(v) for v in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left, right = _walk(node.left), _walk(node.comparators[0])
        if isinstance(node.ops[0], ast.Eq):
            return left == right
        if isinstance(node.ops[0], ast.NotEq):
            return left != right
    raise AssertionError(f"unsupported expression node: {ast.dump(node)}")


def _steps_before_build(variables: dict[str, str]) -> list[dict]:
    """The steps that run, in order, before the image is built -- i.e. the
    ones that can stop a deploy before anything ships."""
    ran = []
    for step in _backend_steps():
        if step.get("name", "").startswith("Build + push image"):
            return ran
        cond = step.get("if")
        if cond is None or _evaluate(str(cond), variables):
            ran.append(step)
    raise AssertionError("no 'Build + push image' step found in the backend job")


def _fails(step: dict) -> bool:
    return bool(re.search(r"(?m)^\s*exit 1\s*$", step.get("run", "")))


@pytest.mark.parametrize("bucket,allow", list(itertools.product(
    ["", "vidyuthlabs-academicos-ci-test"], ["", "true", "false", "yes"])))
def test_unverified_gcs_blocks_the_deploy_unless_explicitly_allowed(bucket: str, allow: str) -> None:
    variables = {"GCP_PROJECT_ID": "vidyuthlabs", "GCS_TEST_BUCKET": bucket,
                 "ALLOW_UNVERIFIED_GCS": allow}
    ran = _steps_before_build(variables)
    integration = [s for s in ran if "test_gcs_blob_integration.py" in s.get("run", "")]
    blockers = [s for s in ran if _fails(s) and "ALLOW_UNVERIFIED_GCS" in s.get("run", "")
                and "test_gcs_blob_integration.py" not in s.get("run", "")]

    if bucket:
        # A configured bucket always runs the real test, override or not.
        assert len(integration) == 1
        assert not blockers
    elif allow == "true":
        # The explicit override, and only the exact value `true`.
        assert not integration
        assert not blockers
        assert any("::warning::" in s.get("run", "") and "ALLOW_UNVERIFIED_GCS" in s.get("run", "")
                   for s in ran), "an allowed unverified deploy must still say so"
    else:
        assert not integration
        assert len(blockers) == 1, "no bucket and no override must fail the job"
        run = blockers[0]["run"]
        assert "::error::" in run
        assert "ALLOW_UNVERIFIED_GCS" in run, "the message must name the override"


def test_the_integration_run_treats_a_skip_as_failure() -> None:
    ran = _steps_before_build({"GCP_PROJECT_ID": "p", "GCS_TEST_BUCKET": "b"})
    (step,) = [s for s in ran if "test_gcs_blob_integration.py" in s.get("run", "")]
    assert step["env"]["ACOS_GCS_TEST_BUCKET"] == "${{ vars.GCS_TEST_BUCKET }}"
    run = step["run"]
    assert "set -o pipefail" in run, "without it `| tee` hides a pytest failure"
    assert re.search(r"pytest\s+tests/test_gcs_blob_integration\.py[^\n]*-rs", run)
    assert "SKIPPED" in run and _fails(step)
    # Zero tests passing (e.g. every test deselected) is not a verification either.
    assert "passed" in run


def test_the_gate_runs_before_anything_is_built_or_deployed() -> None:
    names = [s.get("name", "") for s in _backend_steps()]
    build = next(i for i, n in enumerate(names) if n.startswith("Build + push image"))
    deploy = next(i for i, n in enumerate(names) if n == "Deploy to Cloud Run")
    gate = [i for i, s in enumerate(_backend_steps())
            if "test_gcs_blob_integration.py" in s.get("run", "")
            or ("ALLOW_UNVERIFIED_GCS" in s.get("run", "") and _fails(s))]
    assert len(gate) == 2
    assert max(gate) < build < deploy
