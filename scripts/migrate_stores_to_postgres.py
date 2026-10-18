"""Copy the two SQLite stores into Postgres (R-A1): CurriculumStore and OperationsStore.

    python scripts/migrate_stores_to_postgres.py --from-gcs                 # the live snapshots
    python scripts/migrate_stores_to_postgres.py --curriculum c.sqlite --operations o.sqlite

The target is the database the app's Postgres store backend uses (`ACOS_STORE_PG_*`, else the Cloud SQL
settings `ACOS_POSTGRES_*`), in the schemas `ACOS_PG_SCHEMA_CURRICULUM` and `ACOS_PG_SCHEMA_OPERATIONS`,
which a production run must name (the app is then deployed with the same two values).

For each store, in one transaction:
  1. the schema is created by the store itself, so its tables are exactly the ones the app makes;
  2. every table is emptied, so a second run repairs a first that was interrupted;
  3. every row is copied with its SQLite rowid, which keeps "ORDER BY ..., rowid" in the same order;
  4. the identity counters are moved past the copied ids;
  5. each table's row count is compared with the SQLite file's; any difference aborts the run and the
     transaction is rolled back, leaving Postgres as it was.
A table in the file that the release no longer has, or a column the target lacks, aborts the run too.

The snapshot files are opened read-only. The run ends with a summary (row counts per table and the
SHA-256 of each file), written to --summary as JSON for the cutover record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

STORES = {
    # kind: (blob purpose, blob key)
    "curriculum": ("curriculum-snapshots", "curriculum.sqlite"),
    "operations": ("operations-snapshots", "operations.sqlite"),
}


def _download(kind: str, into: Path) -> Path:
    from academicos.storage.blobs import durable_blob_store
    purpose, key = STORES[kind]
    remote = durable_blob_store(purpose)
    if not remote.enabled:
        raise SystemExit(f"no blob store is configured for {purpose}: set ACOS_GCS_BUCKET")
    path = into / key
    path.write_bytes(remote.download(key))
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_tables(src: sqlite3.Connection) -> list[str]:
    return [r[0] for r in src.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def migrate_store(kind: str, sqlite_path: Path) -> dict:
    """Copy one store; returns {table: rows}. Raises on any mismatch, before committing."""
    from academicos.storage import pg_sqlite

    if not pg_sqlite._dsn():
        raise SystemExit("no Postgres configured: set ACOS_STORE_PG_* or ACOS_POSTGRES_*")
    os.environ["ACOS_STORE_BACKEND"] = "postgres"
    schema = pg_sqlite.schema_for(kind, sqlite_path)

    # 1. The store makes its own schema (tables, indexes, migrations), as the app will.
    if kind == "curriculum":
        from academicos.curriculum.store import CurriculumStore
        store = CurriculumStore(sqlite_path)
    else:
        from academicos.operations.store import OperationsStore
        store = OperationsStore(sqlite_path)
    store.conn.commit()
    store.conn.close()

    import psycopg
    src = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
    counts: dict[str, int] = {}
    with psycopg.connect(**pg_sqlite._dsn()) as dst:
        dst.execute(f"SET search_path TO {schema}")
        target = {r[0] for r in dst.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,))}
        tables = _source_tables(src)
        missing = [t for t in tables if t not in target]
        if missing:
            raise SystemExit(f"{kind}: tables in the file that this release does not have: {missing}")
        # 2. Empty every table first: re-running repairs an interrupted run.
        dst.execute("TRUNCATE " + ", ".join(f'"{t}"' for t in sorted(target)) + " RESTART IDENTITY CASCADE")
        for t in tables:
            cols = [r[1] for r in src.execute(f'PRAGMA table_info("{t}")')]
            have = {r[0] for r in dst.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s",
                (schema, t))}
            lacking = [c for c in cols if c not in have]
            if lacking:
                raise SystemExit(f"{kind}.{t}: columns the target lacks: {lacking}")
            # 3. Rows with their rowid, in rowid order.
            rows = src.execute(f'SELECT rowid, {", ".join(chr(34) + c + chr(34) for c in cols)} '
                               f'FROM "{t}" ORDER BY rowid').fetchall()
            if rows:
                names = ", ".join(['rowid', *[f'"{c}"' for c in cols]])
                marks = ", ".join(["%s"] * (len(cols) + 1))
                identity = "OVERRIDING SYSTEM VALUE " if _has_always_identity(dst, schema, t) else ""
                with dst.cursor() as cur:
                    cur.executemany(f'INSERT INTO "{t}" ({names}) {identity}VALUES ({marks})',
                                    [tuple(_value(v) for v in r) for r in rows])
            # 4. Identity counters past the copied ids (the hidden rowid, and an autoincrement id).
            for col in _identity_columns(dst, schema, t):
                dst.execute(f"SELECT setval(pg_get_serial_sequence(%s, %s), "
                            f'GREATEST((SELECT max("{col}") FROM "{t}"), 1), (SELECT count(*) > 0 FROM "{t}"))',
                            (f"{schema}.{t}", col))
            # 5. Counts must agree.
            got = dst.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
            if got != len(rows):
                raise SystemExit(f"{kind}.{t}: copied {got} rows of {len(rows)}; rolled back")
            counts[t] = got
        dst.commit()
    src.close()
    return counts


def _value(v):
    return bytes(v) if isinstance(v, memoryview) else v


def _identity_columns(dst, schema: str, table: str) -> list[str]:
    return [r[0] for r in dst.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s "
        "AND is_identity = 'YES'", (schema, table))]


def _has_always_identity(dst, schema: str, table: str) -> bool:
    return bool(dst.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_schema = %s AND table_name = %s "
        "AND identity_generation = 'ALWAYS'", (schema, table)).fetchone())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--from-gcs", action="store_true", help="download the live snapshots first")
    ap.add_argument("--curriculum", type=Path, help="a local copy of curriculum.sqlite")
    ap.add_argument("--operations", type=Path, help="a local copy of operations.sqlite")
    ap.add_argument("--summary", type=Path, help="write the counts and file hashes here as JSON")
    a = ap.parse_args(argv)
    files: dict[str, Path] = {}
    tmp = Path(tempfile.mkdtemp(prefix="acos_migrate_"))
    if a.from_gcs:
        files = {kind: _download(kind, tmp) for kind in STORES}
    for kind in STORES:
        given = getattr(a, kind)
        if given:
            files[kind] = given
    if not files:
        ap.error("give --from-gcs, or --curriculum and/or --operations")
    summary = {}
    for kind, path in files.items():
        counts = migrate_store(kind, path)
        summary[kind] = {"file": str(path), "sha256": _sha256(path), "rows": counts,
                         "total": sum(counts.values())}
        print(f"{kind}: {len(counts)} tables, {sum(counts.values())} rows, sha256 {summary[kind]['sha256'][:16]}")
        for t, n in counts.items():
            print(f"    {t:40s} {n:>8}")
    if a.summary:
        a.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
