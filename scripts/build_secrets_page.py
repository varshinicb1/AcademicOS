"""Build deploy/gcp/secrets-page.html from deploy/gcp/optional-config.json.

    python scripts/build_secrets_page.py            # writes the page
    python scripts/build_secrets_page.py --check    # fails if the committed page is stale

The page is for the operator, on their own computer. It makes no network request at all
(its Content-Security-Policy forbids one), stores nothing (no localStorage, no cookies, no
URL), and turns what is typed into a script for the operator's own gcloud login, which
puts each value into Google Secret Manager and gives the running service access. The
values never pass through a chat, a repository or a server of ours.

tests/test_optional_config.py holds the page to the config and the config to the code.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "deploy" / "gcp" / "optional-config.json"
PAGE = ROOT / "deploy" / "gcp" / "secrets-page.html"

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<title>Production Secrets</title>
<style>
  :root { color-scheme: light dark; --bg:#f6f6f8; --card:#fff; --text:#1d1d1f; --muted:#5f5f6a; --line:#e2e2e8;
          --accent:#c2410c; --accent-text:#fff; --ok:#0b7a5a; --warn-bg:#fffbeb; --warn:#92400e; --input:#fff; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0b0d14; --card:#121626; --text:#f2f2f5; --muted:#a1a3b3; --line:#232844;
          --accent:#e0581c; --accent-text:#fff; --ok:#30d5a0; --warn-bg:#2a2108; --warn:#fcd9a0; --input:#0b0d14; } }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }
  main { max-width: 760px; margin: 0 auto; padding: 24px 16px 96px; }
  h1 { font-size: 24px; margin: 0 0 4px; }
  h2 { font-size: 17px; margin: 0 0 4px; }
  p { margin: 0 0 8px; }
  .muted { color: var(--muted); }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; margin:16px 0; }
  .notice { background:var(--warn-bg); color:var(--warn); border:1px solid var(--line); border-radius:12px; padding:12px 16px; margin:16px 0; }
  .field { margin: 14px 0 0; }
  .field label { font-weight: 600; display:block; }
  .tag { font-size: 12px; font-weight: 600; color: var(--muted); border:1px solid var(--line); border-radius: 999px; padding: 0 8px; margin-left: 6px; }
  .help { font-size: 13px; color: var(--muted); margin: 2px 0 6px; }
  .row { display:flex; gap: 8px; }
  input[type=text], input[type=password] { flex:1; min-width:0; padding: 10px 12px; font: inherit; background:var(--input); color:var(--text);
          border:1px solid var(--line); border-radius: 8px; }
  input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
  button { font: inherit; font-weight: 600; padding: 10px 14px; border-radius: 8px; border:1px solid var(--line); background:var(--card); color:var(--text); cursor:pointer; }
  button.primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
  button:disabled { opacity: .5; cursor: default; }
  .bad { color: #b91c1c; font-size: 13px; margin-top: 4px; }
  .grid { display:grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  @media (max-width: 560px) { .grid { grid-template-columns: 1fr; } }
  pre { background: var(--bg); border:1px solid var(--line); border-radius: 8px; padding: 12px; overflow:auto; max-height: 280px; font-size: 12px; }
  .sticky { position: fixed; left:0; right:0; bottom:0; background:var(--card); border-top:1px solid var(--line); padding: 12px 16px; }
  .sticky .in { max-width: 760px; margin: 0 auto; display:flex; gap: 8px; align-items:center; justify-content: space-between; flex-wrap: wrap; }
  ol { padding-left: 20px; margin: 8px 0; }
  code { font-family: ui-monospace,Consolas,monospace; font-size: 13px; }
</style>
</head>
<body>
<main>
  <h1>Production secrets</h1>
  <p class="muted">Keys and settings for the live AcademicOS service. Fill in only what you have; leave the rest blank and add it later.</p>

  <div class="notice">
    <strong>This page never sends anything.</strong> It runs only in your browser and cannot make a network request. Nothing you type
    is saved, logged or uploaded. It builds a script for <em>your own</em> Google Cloud login; the script stores each value in
    Google Secret Manager and gives the running service access. Run it once and it deletes itself.
  </div>

  <div class="card">
    <h2>Where it goes</h2>
    <div class="grid" style="margin-top:8px">
      <div><label for="project">Project</label><div class="row"><input id="project" type="text" autocomplete="off" spellcheck="false"></div></div>
      <div><label for="region">Region</label><div class="row"><input id="region" type="text" autocomplete="off" spellcheck="false"></div></div>
      <div><label for="service">Service</label><div class="row"><input id="service" type="text" autocomplete="off" spellcheck="false"></div></div>
    </div>
  </div>

  <div id="groups"></div>

  <div class="card" id="output" hidden>
    <h2>Your script</h2>
    <p class="muted">It contains your values (encoded, not hidden). Save it, run it once, and it removes itself. Do not send or commit it.</p>
    <ol>
      <li>Open a terminal and sign in once: <code>gcloud auth login</code></li>
      <li>Windows: <code>powershell -ExecutionPolicy Bypass -File .\apply-secrets.ps1</code><br>Mac or Linux: <code>bash apply-secrets.sh</code></li>
      <li>It ends by updating the live service, which starts a new revision and checks it is healthy.</li>
    </ol>
    <div class="row" style="flex-wrap:wrap">
      <button class="primary" id="dl-ps1" type="button">Download for Windows (.ps1)</button>
      <button id="dl-sh" type="button">Download for Mac or Linux (.sh)</button>
      <button id="toggle-script" type="button">Show the script</button>
    </div>
    <pre id="script-view" hidden></pre>
  </div>
</main>

<div class="sticky"><div class="in">
  <span id="count" class="muted">Nothing filled in yet.</span>
  <span class="row">
    <button id="clear" type="button">Clear everything</button>
    <button id="build" class="primary" type="button" disabled>Build my script</button>
  </span>
</div></div>

<script>
"use strict";
const CONFIG = __CONFIG__;

const els = {
  groups: document.getElementById("groups"), count: document.getElementById("count"),
  build: document.getElementById("build"), clear: document.getElementById("clear"),
  output: document.getElementById("output"), view: document.getElementById("script-view"),
  toggle: document.getElementById("toggle-script"), project: document.getElementById("project"),
  region: document.getElementById("region"), service: document.getElementById("service"),
};
els.project.value = CONFIG.project; els.region.value = CONFIG.region; els.service.value = CONFIG.service;

const inputs = new Map();   // env -> input element
const notes = new Map();    // env -> message element

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) { if (k === "text") e.textContent = v; else e.setAttribute(k, v); }
  for (const k of kids) if (k) e.appendChild(k);
  return e;
}

function randomHex(bytes) {
  const a = new Uint8Array(bytes); crypto.getRandomValues(a);
  return Array.from(a, b => b.toString(16).padStart(2, "0")).join("");
}

function problem(item, value) {
  if (!value) return "";
  if (item.kind === "setting" && /[\r\n]/.test(value)) return "One line only.";
  if (item.pattern && !new RegExp(item.pattern).test(value)) return "That does not look right for this field.";
  if (/^(replace_me|changeme|xxx+|your[-_ ]?key)/i.test(value)) return "That is a placeholder, not a real value.";
  return "";
}

function render() {
  for (const g of CONFIG.groups) {
    const card = el("section", { class: "card", id: "g-" + g.id }, el("h2", { text: g.title }), el("p", { class: "muted", text: g.blurb }));
    for (const item of g.items) {
      const input = el("input", { type: item.kind === "secret" ? "password" : "text", id: "f-" + item.env,
        autocomplete: "off", spellcheck: "false", autocapitalize: "off", placeholder: item.placeholder || "" });
      if (item.kind === "secret") input.dataset.secret = "1";
      input.addEventListener("input", refresh);
      inputs.set(item.env, input);
      const row = el("div", { class: "row" }, input);
      if (item.kind === "secret") {
        const show = el("button", { type: "button", text: "Show" });
        show.addEventListener("click", () => { const hidden = input.type === "password"; input.type = hidden ? "text" : "password"; show.textContent = hidden ? "Hide" : "Show"; });
        row.appendChild(show);
      }
      if (item.generate) {
        const gen = el("button", { type: "button", text: "Generate" });
        gen.addEventListener("click", () => { input.value = randomHex(32); input.type = "text"; refresh(); input.select(); });
        row.appendChild(gen);
      }
      const note = el("div", { class: "bad", hidden: "" });
      notes.set(item.env, note);
      const label = el("label", { for: "f-" + item.env, text: item.label }, el("span", { class: "tag", text: item.kind === "secret" ? "secret" : "setting" }),
        item.optional ? el("span", { class: "tag", text: "optional" }) : null);
      card.appendChild(el("div", { class: "field" }, label, el("div", { class: "help", text: item.help }), row, note));
    }
    els.groups.appendChild(card);
  }
}

function filled() {
  const out = [];
  for (const g of CONFIG.groups) for (const item of g.items) {
    const v = inputs.get(item.env).value.trim();
    if (v) out.push({ item, value: v });
  }
  return out;
}

function refresh() {
  let bad = 0;
  for (const g of CONFIG.groups) for (const item of g.items) {
    const msg = problem(item, inputs.get(item.env).value.trim());
    const note = notes.get(item.env);
    note.textContent = msg; note.hidden = !msg; if (msg) bad++;
  }
  const n = filled().length;
  els.count.textContent = n === 0 ? "Nothing filled in yet." : n + " value" + (n === 1 ? "" : "s") + " filled in" + (bad ? "; fix " + bad + " first" : ".");
  els.build.disabled = n === 0 || bad > 0;
}

function b64(text) { return btoa(String.fromCharCode(...new TextEncoder().encode(text))); }
function psq(s) { return "'" + s.replace(/'/g, "''") + "'"; }
function shq(s) { return "'" + s.replace(/'/g, "'\\''") + "'"; }

function pairs(list) {
  const out = [];
  for (const { item } of list) { out.push([item.env, item.secret]); for (const e of item.alsoEnv || []) out.push([e, item.secret]); }
  return out;
}

function buildPowerShell(list) {
  const project = els.project.value.trim(), region = els.region.value.trim(), service = els.service.value.trim();
  const rows = list.map(({ item, value }) => "  @{ Env = " + psq(item.env) + "; Secret = " + psq(item.secret) + "; B64 = " + psq(b64(value)) + " }").join(",\r\n");
  const map = pairs(list).map(([e, s]) => e + "=" + s + ":latest").join(",");
  return [
    "# apply-secrets.ps1, made by secrets-page.html on " + new Date().toISOString().slice(0, 10) + ".",
    "# It holds secret values. Run it once; it deletes itself when it finishes.",
    "$ErrorActionPreference = 'Stop'",
    "$Project = " + psq(project) + "; $Region = " + psq(region) + "; $Service = " + psq(service),
    "if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) { throw 'gcloud is not installed: https://cloud.google.com/sdk/docs/install' }",
    "$who = (& gcloud auth list --filter=status:ACTIVE '--format=value(account)') | Select-Object -First 1",
    "if (-not $who) { throw 'Not signed in. Run: gcloud auth login' }",
    "Write-Host \"Signed in as $who. Project $Project, service $Service ($Region).\"",
    "$sa = (& gcloud run services describe $Service --region $Region --project $Project '--format=value(spec.template.spec.serviceAccountName)')",
    "if (-not $sa) { throw \"Service $Service was not found in $Region of $Project.\" }",
    "$items = @(",
    rows,
    ")",
    "$tmp = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())",
    "try {",
    "  foreach ($i in $items) {",
    "    & { $ErrorActionPreference = 'Continue'; & gcloud secrets describe $i.Secret --project $Project 2>$null | Out-Null }",
    "    if ($LASTEXITCODE -ne 0) {",
    "      & gcloud secrets create $i.Secret --project $Project --replication-policy=automatic --quiet",
    "      if ($LASTEXITCODE -ne 0) { throw \"Could not create $($i.Secret)\" }",
    "    }",
    "    [IO.File]::WriteAllBytes($tmp, [Convert]::FromBase64String($i.B64))",
    "    & gcloud secrets versions add $i.Secret --project $Project \"--data-file=$tmp\" --quiet | Out-Null",
    "    if ($LASTEXITCODE -ne 0) { throw \"Could not store $($i.Secret)\" }",
    "    & gcloud secrets add-iam-policy-binding $i.Secret --project $Project \"--member=serviceAccount:$sa\" --role=roles/secretmanager.secretAccessor --quiet | Out-Null",
    "    if ($LASTEXITCODE -ne 0) { throw \"Could not let the service read $($i.Secret)\" }",
    "    Write-Host \"stored  $($i.Env)\"",
    "  }",
    "  Write-Host 'Updating the live service...'",
    "  & gcloud run services update $Service --region $Region --project $Project \"--update-secrets=" + map + "\" --quiet",
    "  if ($LASTEXITCODE -ne 0) { throw 'The service update failed: nothing is lost, the values are stored; re-run after fixing the error above.' }",
    "  $url = (& gcloud run services describe $Service --region $Region --project $Project '--format=value(status.url)')",
    "  Write-Host (Invoke-RestMethod \"$url/health\" | ConvertTo-Json -Compress)",
    "  Write-Host 'Done. Later deploys keep these (the workflow reads deploy/gcp/optional-config.json).'",
    "} finally {",
    "  Remove-Item $tmp -Force -ErrorAction SilentlyContinue",
    "  if ($PSCommandPath) { Remove-Item $PSCommandPath -Force -ErrorAction SilentlyContinue }",
    "}",
    "",
  ].join("\r\n");
}

function buildBash(list) {
  const project = els.project.value.trim(), region = els.region.value.trim(), service = els.service.value.trim();
  const rows = list.map(({ item, value }) => "  " + shq(item.env + "|" + item.secret + "|" + b64(value))).join("\n");
  const map = pairs(list).map(([e, s]) => e + "=" + s + ":latest").join(",");
  return [
    "#!/usr/bin/env bash",
    "# apply-secrets.sh, made by secrets-page.html on " + new Date().toISOString().slice(0, 10) + ".",
    "# It holds secret values. Run it once; it deletes itself when it finishes.",
    "set -euo pipefail",
    "PROJECT=" + shq(project) + "; REGION=" + shq(region) + "; SERVICE=" + shq(service),
    "command -v gcloud >/dev/null || { echo 'gcloud is not installed: https://cloud.google.com/sdk/docs/install'; exit 1; }",
    "who=\"$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n1)\"",
    "[ -n \"$who\" ] || { echo 'Not signed in. Run: gcloud auth login'; exit 1; }",
    "echo \"Signed in as $who. Project $PROJECT, service $SERVICE ($REGION).\"",
    "sa=\"$(gcloud run services describe \"$SERVICE\" --region \"$REGION\" --project \"$PROJECT\" --format='value(spec.template.spec.serviceAccountName)')\"",
    "[ -n \"$sa\" ] || { echo \"Service $SERVICE was not found in $REGION of $PROJECT.\"; exit 1; }",
    "tmp=\"$(mktemp)\"; self=\"$0\"",
    "cleanup() { rm -f \"$tmp\" \"$self\"; }; trap cleanup EXIT",
    "ITEMS=(",
    rows,
    ")",
    "for row in \"${ITEMS[@]}\"; do",
    "  IFS='|' read -r env secret b64 <<<\"$row\"",
    "  gcloud secrets describe \"$secret\" --project \"$PROJECT\" >/dev/null 2>&1 || gcloud secrets create \"$secret\" --project \"$PROJECT\" --replication-policy=automatic --quiet",
    "  printf '%s' \"$b64\" | base64 -d > \"$tmp\"",
    "  gcloud secrets versions add \"$secret\" --project \"$PROJECT\" --data-file=\"$tmp\" --quiet >/dev/null",
    "  gcloud secrets add-iam-policy-binding \"$secret\" --project \"$PROJECT\" --member=\"serviceAccount:$sa\" --role=roles/secretmanager.secretAccessor --quiet >/dev/null",
    "  echo \"stored  $env\"",
    "done",
    "echo 'Updating the live service...'",
    "gcloud run services update \"$SERVICE\" --region \"$REGION\" --project \"$PROJECT\" --update-secrets=" + shq(map) + " --quiet",
    "url=\"$(gcloud run services describe \"$SERVICE\" --region \"$REGION\" --project \"$PROJECT\" --format='value(status.url)')\"",
    "curl -fsS \"$url/health\"; echo",
    "echo 'Done. Later deploys keep these (the workflow reads deploy/gcp/optional-config.json).'",
    "",
  ].join("\n");
}

let urls = [];
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  urls.push(url);
  const a = document.createElement("a"); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
}

els.build.addEventListener("click", () => {
  const list = filled();
  const ps = buildPowerShell(list), sh = buildBash(list);
  els.output.hidden = false;
  els.view.textContent = ps;
  document.getElementById("dl-ps1").onclick = () => download("apply-secrets.ps1", ps, "text/plain");
  document.getElementById("dl-sh").onclick = () => download("apply-secrets.sh", sh, "text/plain");
  els.output.scrollIntoView({ behavior: "smooth" });
});
els.toggle.addEventListener("click", () => { els.view.hidden = !els.view.hidden; els.toggle.textContent = els.view.hidden ? "Show the script" : "Hide the script"; });
els.clear.addEventListener("click", () => {
  for (const i of inputs.values()) { i.value = ""; if (i.dataset.secret) i.type = "password"; }
  els.view.textContent = ""; els.output.hidden = true;
  document.getElementById("dl-ps1").onclick = null; document.getElementById("dl-sh").onclick = null;
  urls.forEach(u => URL.revokeObjectURL(u)); urls = [];
  refresh();
});
render(); refresh();
</script>
</body>
</html>
"""


def build() -> str:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    config.pop("_about", None)
    # `</` cannot appear inside the script element.
    payload = json.dumps(config, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return TEMPLATE.replace("__CONFIG__", payload)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    html = build()
    if args.check:
        if not PAGE.exists() or PAGE.read_text(encoding="utf-8") != html:
            print(f"{PAGE} is stale: run python scripts/build_secrets_page.py")
            return 1
        return 0
    PAGE.write_text(html, encoding="utf-8", newline="\n")
    print(f"wrote {PAGE} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
