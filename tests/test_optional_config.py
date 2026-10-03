"""The optional production settings: one JSON file feeds the operator's page and the deploy.

deploy/gcp/optional-config.json lists every setting; scripts/build_secrets_page.py builds the
operator's page from it; the deploy workflow wires every listed secret that exists in Secret
Manager into the service. These tests hold the three to each other and to the code that
reads the variables, and run the scripts the page makes through a PowerShell and a bash parser.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "deploy" / "gcp" / "optional-config.json"
PAGE = ROOT / "deploy" / "gcp" / "secrets-page.html"
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-gcp.yml"

sys.path.insert(0, str(ROOT / "scripts"))
import build_secrets_page as page_builder  # noqa: E402


def _items() -> list[dict]:
    return [i for g in json.loads(CONFIG.read_text(encoding="utf-8"))["groups"] for i in g["items"]]


def test_every_item_is_well_formed_and_unique():
    items = _items()
    assert len({i["env"] for i in items}) == len(items), "an environment variable is listed twice"
    assert len({i["secret"] for i in items}) == len(items), "a secret id is used twice"
    for i in items:
        assert re.fullmatch(r"[A-Z][A-Z0-9_]+", i["env"]), i["env"]
        assert re.fullmatch(r"[a-z][a-z0-9-]{2,60}", i["secret"]), i["secret"]
        assert i["kind"] in ("secret", "setting"), i["env"]
        assert i["label"] and i["help"] and i["unlocks"], i["env"]
        if "pattern" in i:
            re.compile(i["pattern"])


def test_every_listed_variable_is_one_the_code_reads():
    # A name typed wrong here would be stored, wired in and never read.
    source = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                       for p in (ROOT / "src" / "academicos").rglob("*.py"))
    for i in _items():
        for env in [i["env"], *i.get("alsoEnv", [])]:
            assert f'"{env}"' in source or f"'{env}'" in source, f"{env} is not read anywhere in src/"


def test_new_secrets_follow_one_naming_rule():
    for i in _items():
        if i.get("preWired"):
            continue
        assert i["secret"] == "acos-cfg-" + re.sub(r"^acos-", "", i["env"].lower().replace("_", "-")), i["env"]


def test_the_page_is_built_from_the_config():
    assert PAGE.read_text(encoding="utf-8") == page_builder.build(), \
        "deploy/gcp/secrets-page.html is stale: run python scripts/build_secrets_page.py"


def test_the_page_can_make_no_request_and_stores_nothing():
    html = PAGE.read_text(encoding="utf-8")
    assert "default-src 'none'" in html
    assert "connect-src" not in html, "the policy must forbid every connection, not allow one"
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "localStorage",
                      "sessionStorage", "indexedDB", "document.cookie", "location.search", "location.hash"):
        assert forbidden not in html, forbidden
    assert not re.search(r"<(script|link|img|iframe)[^>]+(src|href)=[\"']https?:", html)


def test_the_deploy_wires_in_what_the_config_lists():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "deploy/gcp/optional-config.json" in workflow
    assert "gcloud secrets describe" in workflow
    # The two secrets the workflow already wires by hand are not wired twice.
    pre_wired = [i["env"] for i in _items() if i.get("preWired")]
    assert pre_wired == ["ACOS_LLM_API_KEY"]
    assert "ACOS_LLM_API_KEY=acos-llm-api-key:latest" in workflow


# --------------------------------------------------------------------------- #
# the scripts the page makes
# --------------------------------------------------------------------------- #
NODE_HARNESS = textwrap.dedent(r"""
    const fs = require("fs");
    const html = fs.readFileSync(process.argv[2], "utf8");
    const code = html.split("<script>")[1].split("</script>")[0];
    const stub = () => new Proxy(function () {}, {
      get: (t, k) => k === "value" ? "" : k === "dataset" ? {} : k === Symbol.toPrimitive ? () => "" : stub(),
      apply: () => stub(), set: () => true });
    const ctx = { document: { getElementById: () => stub(), createElement: () => stub(), body: stub() },
      crypto: { getRandomValues: a => a }, TextEncoder, btoa: s => Buffer.from(s, "latin1").toString("base64"),
      URL: { createObjectURL: () => "", revokeObjectURL: () => {} }, Blob: function () {}, console };
    require("vm").createContext(ctx);
    // Replace the DOM-reading parts with fixed values, then run the builders on test values.
    const patched = code.replace(/els\.project\.value\.trim\(\)/g, "'vidyuthlabs'")
      .replace(/els\.region\.value\.trim\(\)/g, "'asia-south1'").replace(/els\.service\.value\.trim\(\)/g, "'academicos-backend'");
    require("vm").runInContext(patched + `
      const list = [
        { item: CONFIG.groups[0].items[0], value: "key with 'quote', \\"double\\", $dollar, \`tick and unicode é" },
        { item: CONFIG.groups[2].items[0], value: "smtp.example.com" } ];
      globalThis.__out = { ps: buildPowerShell(list), sh: buildBash(list), map: pairs(list) };
    `, ctx);
    fs.writeFileSync(process.argv[3], ctx.__out.ps); fs.writeFileSync(process.argv[4], ctx.__out.sh);
    fs.writeFileSync(process.argv[5], JSON.stringify(ctx.__out.map));
""")


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    d = tmp_path_factory.mktemp("page")
    harness = d / "h.js"
    harness.write_text(NODE_HARNESS, encoding="utf-8")
    ps, sh, mp = d / "apply.ps1", d / "apply.sh", d / "map.json"
    run = subprocess.run([node, str(harness), str(PAGE), str(ps), str(sh), str(mp)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    return ps, sh, json.loads(mp.read_text(encoding="utf-8"))


def test_the_scripts_hold_no_plain_secret_and_wire_both_names_of_one_key(made):
    ps, sh, mapping = made
    for script in (ps, sh):
        text = script.read_text(encoding="utf-8")
        assert "key with" not in text and "smtp.example.com" not in text, "a value is in the clear"
    assert ["ACOS_LLM_API_KEY", "acos-llm-api-key"] in mapping and ["SARVAM_API_KEY", "acos-llm-api-key"] in mapping


def test_the_bash_script_parses(made):
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash is not installed")
    _, sh, _ = made
    check = subprocess.run([bash, "-n", str(sh)], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr


def test_the_powershell_script_parses(made):
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        pytest.skip("PowerShell is not installed")
    ps, _, _ = made
    cmd = ("$e=$null;$t=$null;[void][System.Management.Automation.Language.Parser]::ParseFile("
           f"'{ps}',[ref]$t,[ref]$e); if($e.Count){{$e|%{{$_.Message}};exit 1}}")
    check = subprocess.run([pwsh, "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    assert check.returncode == 0, check.stdout + check.stderr
