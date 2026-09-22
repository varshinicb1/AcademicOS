"""export_mobile_corpus.py must never overwrite the APK corpus with a board-only export."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "frontend" / "assets" / "corpus" / "questions.json"


def test_it_refuses_to_write_the_apk_asset():
    before = ASSET.read_bytes() if ASSET.exists() else None
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "export_mobile_corpus.py")],
                          capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode != 0
    assert "merge_question_banks.py" in (proc.stdout + proc.stderr)
    assert (ASSET.read_bytes() if ASSET.exists() else None) == before
