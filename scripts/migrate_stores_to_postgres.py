"""Copy the two SQLite stores into Postgres (R-A1). The code is
`academicos.storage.migrate_stores`, so the deployed image can run it too; see its docstring."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from academicos.storage.migrate_stores import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
