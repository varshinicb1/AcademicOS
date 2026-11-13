"""The teacher, student and offline Android apps install side by side (R-B1).

`frontend/android/app/build.gradle.kts` declares one product flavor per app,
each with its own application id and launcher label, and refuses a build whose
`--dart-define` would put a different app in that package. This test holds the
Gradle file, the manifest, the documented build commands and the gitignore to
the same table, so a renamed flavor or a doc command that no longer builds is
caught here rather than on a phone. It is static: building an APK needs the
Android SDK, which CI does not have.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANDROID = REPO / "frontend" / "android"
GRADLE = (ANDROID / "app" / "build.gradle.kts").read_text(encoding="utf-8")

# flavor -> (applicationIdSuffix or None, label, the dart-define it needs)
EXPECTED = {
    "teacher": (".teacher", "AcademicOS Teacher", ("ACADEMICOS_APP", "teacher")),
    "student": (".student", "AcademicOS Student", ("ACADEMICOS_APP", "student")),
    # No suffix: the offline app keeps the id it shipped under, so it upgrades in place.
    "offline": (None, "AcademicOS Offline", ("ACADEMICOS_OFFLINE", "true")),
}

_FLAVOR_ROW = re.compile(
    r'AppFlavor\("(?P<name>\w+)",\s*(?:"(?P<suffix>[^"]*)"|null),\s*"(?P<label>[^"]+)",\s*'
    r'"(?P<key>\w+)"\s+to\s+"(?P<value>\w+)"\)'
)


def _flavor_table() -> dict[str, tuple[str | None, str, tuple[str, str]]]:
    return {
        m["name"]: (m["suffix"], m["label"], (m["key"], m["value"]))
        for m in _FLAVOR_ROW.finditer(GRADLE)
    }


def test_each_app_is_a_flavor_with_its_own_id_and_label():
    assert _flavor_table() == EXPECTED
    assert 'flavorDimensions += "app"' in GRADLE
    assert "applicationIdSuffix = it" in GRADLE
    assert 'resValue("string", "app_name", f.label)' in GRADLE
    assert "resValues = true" in GRADLE
    suffixes = [s for s, _, _ in EXPECTED.values()]
    assert len(set(suffixes)) == len(suffixes), "two flavors would share an application id"


def test_the_launcher_label_comes_from_the_flavor():
    manifest = (ANDROID / "app" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert 'android:label="@string/app_name"' in manifest


def test_gradle_refuses_a_flavor_built_with_another_apps_define():
    # The guard reads Flutter's dart-defines and fails a flavorless build or a mismatch.
    assert 'findProperty("dart-defines")' in GRADLE
    assert "name one with --flavor" in GRADLE
    assert "must be built with --dart-define" in GRADLE


def test_release_signing_reads_an_uncommitted_key_and_falls_back_loudly():
    assert 'file("../key.properties")' in GRADLE
    assert "local DEBUG key" in GRADLE
    ignore = (ANDROID / ".gitignore").read_text(encoding="utf-8").splitlines()
    for pattern in ("key.properties", "**/*.jks", "**/*.keystore"):
        assert pattern in ignore, f"{pattern} must stay gitignored"
    # Tracked files only: the owner's own key.properties sits in their checkout, ignored.
    tracked = subprocess.run(
        ["git", "ls-files", "frontend/android"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    committed = [p for p in tracked if p.endswith((".jks", ".keystore", "key.properties"))]
    assert committed == [], f"a signing key is committed: {committed}"


def _documented_builds() -> list[str]:
    commands = []
    for doc in ("docs/apps.md", "docs/PRODUCTS_AND_RELEASES.md"):
        text = (REPO / doc).read_text(encoding="utf-8")
        commands += [
            line.strip()
            for line in text.splitlines()
            if re.search(r"flutter (build|run) (apk|appbundle)\b", line) or "flutter run --flavor" in line
        ]
    return commands


def test_every_documented_android_build_names_a_flavor_and_its_define():
    commands = _documented_builds()
    assert commands, "docs/apps.md lost its build commands"
    seen = set()
    for cmd in commands:
        m = re.search(r"--flavor (\w+)", cmd)
        assert m, f"documented Android build without --flavor would fail: {cmd}"
        flavor = m[1]
        assert flavor in EXPECTED, cmd
        key, value = EXPECTED[flavor][2]
        assert f"--dart-define={key}={value}" in cmd, f"--flavor {flavor} needs {key}={value}: {cmd}"
        seen.add(flavor)
    assert seen == set(EXPECTED), f"no documented build for {set(EXPECTED) - seen}"
