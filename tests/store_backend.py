"""Which store backend this run uses (R-A1). `sqlite_only` marks a test of the SQLite file itself
(its GCS snapshot, or migrating an old .sqlite file): with ACOS_STORE_BACKEND=postgres there is no
such file, and the test is skipped."""
import pytest

from academicos.storage import pg_sqlite

sqlite_only = pytest.mark.skipif(pg_sqlite.enabled(), reason="tests the SQLite file; the stores are on Postgres")
