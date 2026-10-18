"""SQLite-shaped connections over PostgreSQL, for CurriculumStore and OperationsStore (R-A1, NFR-4).

The two stores keep about 80 tables in SQLite files snapshotted to GCS, which pins the service to one
instance: two would overwrite each other's snapshots. Their SQL is portable but for a handful of
SQLite-isms, and it is issued from about 110 places, not just the stores' helpers. So the seam is the
connection: with `ACOS_STORE_BACKEND=postgres` a store gets a `Connection` from here instead of
`sqlite3.connect`, and every call site keeps its SQL. What this module translates, and why:

- `?` placeholders become `%s`; a literal `%` is doubled (psycopg reads `%` anywhere in the text).
- `IS ?` / `IS NOT ?` become `IS [NOT] DISTINCT FROM %s`: Postgres has no `IS <parameter>`.
- `LIKE` becomes `ILIKE`: SQLite's LIKE ignores (ASCII) case.
- `INSERT OR IGNORE` and `INSERT OR REPLACE` become `ON CONFLICT` clauses (the replace on the
  table's primary key, read from the catalog).
- Two-argument `max(a, b)` / `min(a, b)` become `GREATEST` / `LEAST`.
- `ORDER BY` terms gain `NULLS FIRST` (ascending) or `NULLS LAST` (descending), SQLite's order.
- DDL: INTEGER is 64-bit (BIGINT), REAL is double precision, an autoincrement key is an identity
  column, `COLLATE NOCASE` is a case-insensitive ICU collation, and every other TEXT column sorts
  byte by byte (`COLLATE "C"`), as SQLite's BINARY does. Every table gains a hidden `rowid` identity
  column, so `ORDER BY ..., rowid` keeps insertion order; rows leave it out unless the statement
  names it, as SQLite's `SELECT *` does.
- `PRAGMA table_info(t)` reads information_schema; the other PRAGMAs do nothing.

Behaviour kept from sqlite3: a failed statement leaves the transaction usable (each statement runs
inside a savepoint, in the same round trip), errors are sqlite3's types, rows are `sqlite3.Row`-like,
values are loosely typed (an integer parameter compares with a TEXT column, a bool is 0/1, a date is
its ISO text, booleans and numerics come back as int or float).

Each store gets its own Postgres schema: `ACOS_PG_SCHEMA_CURRICULUM` / `ACOS_PG_SCHEMA_OPERATIONS`
in production, otherwise one derived from the store's file path, so every test's store is separate.
The connection settings are `ACOS_STORE_PG_*` when set (tests point the stores at a scratch database
without moving the JSONB stores), else the Cloud SQL settings `postgres_kv` uses.
"""
from __future__ import annotations

import datetime as _dt
import decimal
import hashlib
import logging
import os
import re
import sqlite3
import threading
import weakref
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------------------------------
# configuration


def enabled() -> bool:
    """`ACOS_STORE_BACKEND=postgres` and a database to connect to."""
    return os.environ.get("ACOS_STORE_BACKEND", "sqlite").strip().lower() == "postgres" and _dsn() is not None


def _dsn() -> Optional[dict[str, str]]:
    host = os.environ.get("ACOS_STORE_PG_HOST", "").strip()
    if host:
        return {"host": host, "port": os.environ.get("ACOS_STORE_PG_PORT", "5432").strip(),
                "dbname": os.environ.get("ACOS_STORE_PG_DB", "postgres").strip(),
                "user": os.environ.get("ACOS_STORE_PG_USER", "postgres").strip(),
                "password": os.environ.get("ACOS_STORE_PG_PASSWORD", ""), "connect_timeout": "10"}
    from ..assessment.postgres_kv import _dsn_parts
    return _dsn_parts()


MOVED_MARKER = "MOVED_TO_POSTGRES"


def refuse_if_moved(purpose: str) -> None:
    """Stop a SQLite-mode boot of a store whose data has moved to Postgres (docs/r-a1-cutover.md).

    After the cutover the GCS snapshot is frozen at the moment of the move. A deploy that forgot
    ACOS_STORE_BACKEND=postgres would restore it and run on, losing every write since, so the
    cutover leaves a marker beside the snapshot and this refuses to start. Rolling back on purpose
    sets ACOS_STORE_BACKEND=sqlite, which says so explicitly."""
    if os.environ.get("ACOS_STORE_BACKEND", "").strip().lower() == "sqlite":
        return
    from .blobs import BlobNotFound, durable_blob_store
    remote = durable_blob_store(purpose)
    if not remote.enabled:
        return
    try:
        note = remote.download(MOVED_MARKER).decode("utf-8", "replace").strip()
    except BlobNotFound:
        return
    except Exception as exc:  # noqa: BLE001 - checking for the marker must never stop a boot by itself
        if getattr(getattr(exc, "response", None), "status_code", None) == 404:
            return              # Supabase storage answers a missing object with a 404 error
        logger.warning("could not check %s for the Postgres move marker; starting on the snapshot "
                       "(its own boot checks still apply)", purpose, exc_info=True)
        return
    raise RuntimeError(f"{purpose}: this store moved to Postgres ({note}). Deploy with "
                       "ACOS_STORE_BACKEND=postgres, or with ACOS_STORE_BACKEND=sqlite to roll back on purpose.")


def describe() -> dict[str, Any]:
    """Where CurriculumStore and OperationsStore keep their tables, for /health/storage: the cutover
    is verified by reading this on the live service."""
    if not enabled():
        return {"backend": "sqlite_snapshots"}
    return {"backend": "postgres",
            "schemas": {k: os.environ.get(f"ACOS_PG_SCHEMA_{k.upper()}", "").strip() or "per-path"
                        for k in ("curriculum", "operations")}}


def schema_for(kind: str, db_path: Path) -> str:
    """The store's schema: named in production, derived from the file path otherwise."""
    named = os.environ.get(f"ACOS_PG_SCHEMA_{kind.upper()}", "").strip()
    if named:
        return _ident(named)
    digest = hashlib.sha1(str(Path(db_path).resolve()).encode("utf-8")).hexdigest()[:12]
    return f"{kind}_{digest}"


def _ident(name: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", name):
        raise ValueError(f"not a schema name: {name!r}")
    return name


# ---------------------------------------------------------------------------------------------------
# translation


def _mask(sql: str) -> str:
    """`sql` with the insides of string literals, quoted identifiers and comments blanked, so the
    rewrites below never look inside them; positions are unchanged."""
    out = list(sql)
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c in ("'", '"'):
            j = i + 1
            while j < n:
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            for k in range(i + 1, min(j, n)):
                out[k] = "_"
            i = j + 1
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                out[k] = " "
            i = j
        else:
            i += 1
    return "".join(out)


class _Edits:
    """Position-keyed replacements over one statement, applied right to left."""

    def __init__(self, sql: str):
        self.sql = sql
        self.edits: list[tuple[int, int, str]] = []

    def replace(self, start: int, end: int, text: str) -> None:
        self.edits.append((start, end, text))

    def apply(self) -> str:
        out = self.sql
        for start, end, text in sorted(self.edits, key=lambda e: (e[0], e[1]), reverse=True):
            out = out[:start] + text + out[end:]
        return out


def _matching_paren(masked: str, open_at: int) -> int:
    depth = 0
    for i in range(open_at, len(masked)):
        if masked[i] == "(":
            depth += 1
        elif masked[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return len(masked)


def _top_level_commas(masked: str, start: int, end: int) -> list[int]:
    depth, out = 0, []
    for i in range(start, end):
        ch = masked[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append(i)
    return out


_ORDER_STOP = re.compile(r"\b(LIMIT|OFFSET|UNION|EXCEPT|INTERSECT|FOR)\b", re.I)


def _order_by_nulls(masked: str, ed: _Edits) -> None:
    for m in re.finditer(r"\bORDER\s+BY\b", masked, re.I):
        start, depth, end = m.end(), 0, len(masked)
        for i in range(start, len(masked)):
            ch = masked[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                if depth == 0:
                    end = i
                    break
                depth -= 1
            elif ch == ";" and depth == 0:
                end = i
                break
            elif depth == 0 and ch.isalpha() and (i == 0 or not (masked[i - 1].isalnum() or masked[i - 1] == "_")):
                if _ORDER_STOP.match(masked, i):
                    end = i
                    break
        bounds = [start, *[c + 1 for c in _top_level_commas(masked, start, end)]]
        stops = [*[c for c in _top_level_commas(masked, start, end)], end]
        for b, e in zip(bounds, stops):
            term = masked[b:e]
            stripped = term.rstrip()
            if not stripped.strip() or re.search(r"\bNULLS\s+(FIRST|LAST)\b", term, re.I):
                continue
            at = b + len(stripped)
            ed.replace(at, at, " NULLS LAST" if re.search(r"\bDESC$", stripped, re.I) else " NULLS FIRST")


def _greatest_least(masked: str, ed: _Edits) -> None:
    for m in re.finditer(r"\b(max|min)\s*\(", masked, re.I):
        close = _matching_paren(masked, m.end() - 1)
        if _top_level_commas(masked, m.end(), close):
            ed.replace(m.start(), m.start() + len(m.group(1)), "GREATEST" if m.group(1).lower() == "max" else "LEAST")


_TYPE_REWRITES = [
    (re.compile(r"\bINTEGER\s+PRIMARY\s+KEY(\s+AUTOINCREMENT)?\b", re.I), "BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY"),
    (re.compile(r"\bINTEGER\b", re.I), "BIGINT"),
    (re.compile(r"\bREAL\b", re.I), "DOUBLE PRECISION"),
    (re.compile(r"\bBLOB\b", re.I), "BYTEA"),
]


def _column_ddl(defn: str) -> str:
    """One column definition (or table constraint) in Postgres terms."""
    head = defn.strip().split(None, 1)[0].upper() if defn.strip() else ""
    if head in ("PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT"):
        return defn
    out = defn
    for rx, to in _TYPE_REWRITES:
        if rx.search(out):
            out = rx.sub(to, out, count=1)
            break
    if re.search(r"\bCOLLATE\s+NOCASE\b", out, re.I):
        out = re.sub(r"\bCOLLATE\s+NOCASE\b", "COLLATE nocase", out, flags=re.I)
    elif re.search(r"\bTEXT\b", out, re.I) and not re.search(r"\bCOLLATE\b", out, re.I):
        out = re.sub(r"\bTEXT\b", 'TEXT COLLATE "C"', out, count=1, flags=re.I)
    return out


def _ddl(sql: str, masked: str) -> Optional[str]:
    """CREATE TABLE / ALTER TABLE ADD COLUMN in Postgres terms, or None for another statement."""
    m = re.match(r"\s*CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(", masked, re.I)
    if m:
        open_at = m.end() - 1
        close = _matching_paren(masked, open_at)
        cuts = [open_at, *_top_level_commas(masked, open_at + 1, close), close]
        parts = [_column_ddl(sql[a + 1:b]) for a, b in zip(cuts, cuts[1:])]
        body = ",".join(["\n  rowid BIGINT GENERATED BY DEFAULT AS IDENTITY", *parts])
        return sql[:open_at + 1] + body + sql[close:]
    m = re.match(r"(\s*ALTER\s+TABLE\s+\w+\s+ADD\s+(COLUMN\s+)?)(.*)$", sql, re.I | re.S)
    if m:
        return m.group(1) + _column_ddl(m.group(3))
    return None


class Translated:
    __slots__ = ("sql", "noop", "replace_into", "names_rowid", "table_info")

    def __init__(self, sql: str, *, noop: bool = False, replace_into: Optional[tuple[str, list[str]]] = None,
                 names_rowid: bool = False, table_info: Optional[str] = None):
        self.sql, self.noop, self.replace_into = sql, noop, replace_into
        self.names_rowid, self.table_info = names_rowid, table_info


@lru_cache(maxsize=4096)
def translate(sql: str) -> Translated:
    """One SQLite statement in Postgres terms (see the module docstring)."""
    masked = _mask(sql)
    pragma = re.match(r"\s*PRAGMA\s+(\w+)\s*(\(\s*(\w+)\s*\))?", masked, re.I)
    if pragma:
        if pragma.group(1).lower() == "table_info" and pragma.group(3):
            return Translated("", table_info=pragma.group(3))
        return Translated("", noop=True)
    ddl = _ddl(sql, masked)
    if ddl is not None:
        sql, masked = ddl, _mask(ddl)
    ed = _Edits(sql)
    for m in re.finditer(r"\bIS\s+(NOT\s+)?\?", masked, re.I):
        ed.replace(m.start(), m.end(), "IS DISTINCT FROM ?" if m.group(1) else "IS NOT DISTINCT FROM ?")
    for m in re.finditer(r"\b(WHERE|AND|OR|ON|WHEN)\s+([01])\b(?!\s*[-+*/%=<>!|.])", masked, re.I):
        ed.replace(m.start(2), m.end(2), "TRUE" if m.group(2) == "1" else "FALSE")
    for m in re.finditer(r"\bLIKE\b", masked, re.I):
        ed.replace(m.start(), m.end(), "ILIKE")
    for m in re.finditer(r"\bCOLLATE\s+NOCASE\b", masked, re.I):
        if ddl is None:
            ed.replace(m.start(), m.end(), "COLLATE nocase")
    _qualify_upsert(masked, ed)
    replace_into = None
    ins = re.match(r"\s*INSERT\s+OR\s+(IGNORE|REPLACE)\s+INTO\s+(\w+)\s*(\(([^)]*)\))?", masked, re.I)
    if ins:
        or_at = re.search(r"\bOR\s+(IGNORE|REPLACE)\s+", masked, re.I)
        ed.replace(or_at.start(), or_at.end(), "")
        if ins.group(1).upper() == "IGNORE":
            ed.replace(len(sql.rstrip().rstrip(";")), len(sql), " ON CONFLICT DO NOTHING")
        else:
            cols = [c.strip() for c in (ins.group(4) or "").split(",") if c.strip()]
            replace_into = (ins.group(2), cols)
    if ddl is None:
        _greatest_least(masked, ed)
        _order_by_nulls(masked, ed)
    out = ed.apply()
    out = out.replace("%", "%%")
    out = _placeholders(out)
    return Translated(out, replace_into=replace_into, names_rowid=_selects_rowid(masked))


def _selects_rowid(masked: str) -> bool:
    """Whether the outermost select list names `rowid`. `SELECT * ... ORDER BY seq, rowid` does not:
    SQLite's `*` never includes it, so the hidden column is dropped from such rows."""
    m = re.match(r"\s*SELECT\b", masked, re.I)
    if not m:
        return False
    depth = 0
    for i in range(m.end(), len(masked)):
        ch = masked[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and re.match(r"FROM\b", masked[i:i + 5], re.I) and not masked[i - 1].isalnum():
            return bool(re.search(r"\browid\b", masked[m.end():i], re.I))
    return bool(re.search(r"\browid\b", masked[m.end():], re.I))


_UPSERT_WORDS = {"case", "when", "then", "else", "end", "and", "or", "not", "null", "is", "in", "like", "ilike",
                 "true", "false", "distinct", "from", "between", "excluded", "cast", "as", "collate", "nocase"}


def _qualify_upsert(masked: str, ed: _Edits) -> None:
    """`ON CONFLICT ... DO UPDATE SET n = n + 1`: in Postgres a bare column there could mean the
    existing row or `excluded`, and is refused as ambiguous; SQLite means the existing row. Qualify
    it with the table name, which both read the same way."""
    ins = re.match(r"\s*INSERT\s+(OR\s+\w+\s+)?INTO\s+(\w+)", masked, re.I)
    upd = re.search(r"\bDO\s+UPDATE\s+SET\b", masked, re.I)
    if not ins or not upd:
        return
    table, start = ins.group(2), upd.end()
    stop = re.search(r"\b(WHERE|RETURNING)\b", masked[start:], re.I)
    end = start + stop.start() if stop else len(masked)
    bounds = [start - 1, *_top_level_commas(masked, start, end), end]
    for a, b in zip(bounds, bounds[1:]):
        eq = masked.find("=", a + 1, b)
        if eq < 0:
            continue
        for m in re.finditer(r"[A-Za-z_]\w*", masked[eq + 1:b]):
            word, at = m.group(0), eq + 1 + m.start()
            after = masked[at + len(word):b].lstrip()
            if (word.lower() in _UPSERT_WORDS or not re.search(r"[A-Za-z]", word)
                    or (at > 0 and masked[at - 1] in ".'\"") or after.startswith((".", "("))):
                continue
            ed.replace(at, at, f"{table}.")


def _placeholders(sql: str) -> str:
    masked = _mask(sql)
    return "".join("%s" if masked[i] == "?" else sql[i] for i in range(len(sql)))


def split_script(script: str) -> list[str]:
    masked = _mask(script)
    out, start = [], 0
    for i, ch in enumerate(masked):
        if ch == ";":
            out.append(script[start:i])
            start = i + 1
    out.append(script[start:])
    return [s for s in out if _mask(s).strip()]


# ---------------------------------------------------------------------------------------------------
# rows and cursors


class Row:
    """Like sqlite3.Row: by index, by name, `dict(row)`, iteration over the values."""

    __slots__ = ("_values", "_names")

    def __init__(self, values: Sequence[Any], names: Sequence[str]):
        self._values, self._names = tuple(values), tuple(names)

    def keys(self) -> list[str]:
        return list(self._names)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, (int, slice)):
            return self._values[key]
        try:
            return self._values[self._names.index(key)]
        except ValueError:
            lowered = [n.lower() for n in self._names]
            if isinstance(key, str) and key.lower() in lowered:
                return self._values[lowered.index(key.lower())]
            raise IndexError(f"No item with that key: {key!r}")

    def __iter__(self):
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Row) and other._values == self._values and other._names == self._names

    def __hash__(self) -> int:
        return hash((self._values, self._names))

    def __repr__(self) -> str:
        return f"Row({dict(zip(self._names, self._values))!r})"


class Cursor:
    def __init__(self, rows: list[Row], description: Optional[list[tuple]], rowcount: int):
        self._rows, self.description, self.rowcount = rows, description, rowcount
        self.lastrowid = None
        self._at = 0

    def fetchone(self) -> Optional[Row]:
        if self._at >= len(self._rows):
            return None
        self._at += 1
        return self._rows[self._at - 1]

    def fetchall(self) -> list[Row]:
        out, self._at = self._rows[self._at:], len(self._rows)
        return out

    def fetchmany(self, size: int = 1) -> list[Row]:
        out = self._rows[self._at:self._at + size]
        self._at += len(out)
        return out

    def __iter__(self):
        while (r := self.fetchone()) is not None:
            yield r

    def close(self) -> None:
        pass


_EMPTY = Cursor([], None, -1)


# ---------------------------------------------------------------------------------------------------
# value adaptation


def _adapt(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, _dt.datetime):
        return value.isoformat(" ")
    if isinstance(value, _dt.date):
        return value.isoformat()
    if isinstance(value, memoryview):
        return bytes(value)
    return value


def _params(params: Any) -> Sequence[Any]:
    if params is None:
        return ()
    if isinstance(params, dict):
        raise sqlite3.ProgrammingError("named parameters are not used by these stores")
    return [_adapt(p) for p in params]


def _configure_types(conn: Any) -> None:
    """Loose typing like SQLite's: an int parameter is an untyped literal ('5'), so it compares with
    a TEXT column and fills an INTEGER one; numerics and booleans come back as int or float."""
    from psycopg.adapt import Loader
    from psycopg.types.numeric import IntDumper

    class LooseInt(IntDumper):
        oid = 0

        # IntDumper hands each value to a size-specific dumper (int2/int4/int8/numeric), which
        # would print a typed literal again; this one keeps every int.
        def get_key(self, obj: int, format: Any) -> type:
            return self.cls

        def upgrade(self, obj: int, format: Any) -> "LooseInt":
            return self

        def quote(self, obj: int) -> bytes:  # noqa: D401 - psycopg API
            return b"'" + str(int(obj)).encode() + b"'"

    class NumericLoader(Loader):
        def load(self, data: Any) -> Any:
            d = decimal.Decimal(bytes(data).decode())
            return int(d) if d == d.to_integral_value() else float(d)

    class BoolAsInt(Loader):
        def load(self, data: Any) -> Any:
            return 1 if bytes(data) in (b"t", b"true", b"1") else 0

    conn.adapters.register_dumper(int, LooseInt)
    conn.adapters.register_loader("numeric", NumericLoader)
    conn.adapters.register_loader("bool", BoolAsInt)


def _map_error(exc: Exception) -> sqlite3.Error:
    """sqlite3's error type, and for a constraint SQLite's words ("UNIQUE constraint failed: ..."),
    which callers test for."""
    import psycopg
    diag = getattr(exc, "diag", None)
    message = (getattr(diag, "message_primary", None) or str(exc)).strip()
    where = ".".join(x for x in (getattr(diag, "table_name", None), getattr(diag, "column_name", None)
                                 or getattr(diag, "constraint_name", None)) if x)
    for kind, words in (("UniqueViolation", "UNIQUE"), ("NotNullViolation", "NOT NULL"),
                        ("ForeignKeyViolation", "FOREIGN KEY"), ("CheckViolation", "CHECK")):
        if type(exc).__name__ == kind:
            message = f"{words} constraint failed: {where} ({message})"
    if isinstance(exc, psycopg.errors.IntegrityError):
        out: sqlite3.Error = sqlite3.IntegrityError(message)
    elif isinstance(exc, (psycopg.OperationalError, psycopg.ProgrammingError, psycopg.errors.SyntaxError)):
        out = sqlite3.OperationalError(message)
    else:
        out = sqlite3.DatabaseError(message)
    out.__cause__ = exc
    return out


# ---------------------------------------------------------------------------------------------------
# the connection

_BOOT_LOCK = 7_360_224_502
_OPEN: "weakref.WeakSet[Connection]" = weakref.WeakSet()


def close_idle() -> int:
    """Close every connection with no uncommitted writes; the next use reopens it (`_ensure`).
    Production holds two stores per process, so two connections; the test suite makes thousands of
    stores, and without this each kept a Postgres connection until garbage collection."""
    closed = 0
    for c in list(_OPEN):
        if not c._dirty and c._conn is not None and not c._conn.closed:
            c.close()
            closed += 1
    return closed


class Connection:
    """The sqlite3.Connection calls the stores make, over one psycopg connection. Not thread-safe on
    its own: the stores already serialise every use under their `_conn_lock`."""

    def __init__(self, schema: str, dsn: Optional[dict[str, str]] = None):
        self.schema = _ident(schema)
        self._dsn = dsn or _dsn()
        if self._dsn is None:
            raise sqlite3.OperationalError("ACOS_STORE_BACKEND=postgres but no database is configured")
        self.row_factory = None          # accepted for compatibility; rows are always Row
        self._pk: dict[str, list[str]] = {}
        self._lock = threading.RLock()
        self._dirty = False
        self._conn = None
        self._connect()
        _OPEN.add(self)

    # -- connection ---------------------------------------------------------------------------------
    def _connect(self) -> None:
        import psycopg
        conn = psycopg.connect(**self._dsn, autocommit=True, cursor_factory=psycopg.ClientCursor)
        _configure_types(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (_BOOT_LOCK,))
            try:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
                cur.execute(f"SET search_path TO {self.schema}")
                cur.execute("SELECT 1 FROM pg_collation WHERE collname = 'nocase' "
                            "AND collnamespace = %s::regnamespace", (self.schema,))
                if cur.fetchone() is None:
                    cur.execute("CREATE COLLATION nocase (provider = icu, locale = 'und-u-ks-level2', "
                                "deterministic = false)")
                cur.execute("CREATE OR REPLACE FUNCTION instr(text, text) RETURNS integer "
                            "LANGUAGE sql IMMUTABLE AS 'SELECT strpos($1, $2)'")
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (_BOOT_LOCK,))
        conn.autocommit = False
        self._conn = conn
        self._dirty = False

    def _ensure(self) -> None:
        if self._conn is None or self._conn.closed or self._conn.broken:
            if self._dirty:
                self._dirty = False
                raise sqlite3.OperationalError("the database connection was lost with uncommitted writes")
            self._connect()

    # -- statements ---------------------------------------------------------------------------------
    def _primary_key(self, table: str) -> list[str]:
        if table not in self._pk:
            rows = self._run("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid "
                             "AND a.attnum = ANY(i.indkey) WHERE i.indrelid = to_regclass(%s) AND i.indisprimary "
                             "ORDER BY array_position(i.indkey, a.attnum)", [table], write=False)._rows
            self._pk[table] = [r[0] for r in rows]
        return self._pk[table]

    def _resolve(self, sql: str) -> Translated:
        t = translate(sql)
        if t.replace_into is None:
            return t
        table, cols = t.replace_into
        pk = self._primary_key(table)
        rest = [c for c in cols if c not in pk]
        tail = (f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET " + ", ".join(f"{c} = EXCLUDED.{c}" for c in rest)
                if pk and rest else " ON CONFLICT DO NOTHING")
        return Translated(t.sql.rstrip().rstrip(";") + tail, names_rowid=t.names_rowid)

    def _run(self, sql: str, params: Sequence[Any], *, write: bool, names_rowid: bool = True) -> Cursor:
        import psycopg
        with self._lock:
            self._ensure()
            cur = self._conn.cursor()
            try:
                cur.execute(f"SAVEPOINT acos_s; {sql}; RELEASE SAVEPOINT acos_s", params)
            except psycopg.Error as exc:
                self._recover()
                raise _map_error(exc) from exc
            cur.nextset()
            description = cur.description
            rows: list[Row] = []
            out_desc = None
            if description is not None:
                names = [d.name for d in description]
                keep = [i for i, n in enumerate(names) if names_rowid or n != "rowid"]
                kept = [names[i] for i in keep]
                rows = [Row([r[i] for i in keep], kept) for r in cur.fetchall()]
                out_desc = [(n, None, None, None, None, None, None) for n in kept]
            rowcount = cur.rowcount
            cur.nextset()
            if write:
                self._dirty = True
            return Cursor(rows, out_desc, rowcount)

    def _recover(self) -> None:
        """Back to the state before the failed statement, as SQLite leaves it."""
        try:
            if self._conn is not None and not self._conn.closed and not self._conn.broken:
                self._conn.execute("ROLLBACK TO SAVEPOINT acos_s")
                self._conn.execute("RELEASE SAVEPOINT acos_s")
        except Exception:  # noqa: BLE001 - the savepoint itself never started: roll the transaction back
            logger.warning("store %s: rolling back the transaction after a failed statement", self.schema,
                           exc_info=True)
            try:
                self._conn.rollback()
            except Exception:  # noqa: BLE001 - a broken connection is reopened by the next _ensure
                logger.warning("store %s: rollback failed; the connection reopens on next use", self.schema,
                               exc_info=True)
            self._dirty = False

    def execute(self, sql: str, params: Any = ()) -> Cursor:
        t = self._resolve(sql)
        if t.noop:
            return _EMPTY
        if t.table_info is not None:
            return self._run("SELECT ordinal_position - 2 AS cid, column_name AS name, data_type AS type, "
                             "CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END AS notnull, "
                             "column_default AS dflt_value, 0 AS pk FROM information_schema.columns "
                             "WHERE table_schema = current_schema() AND table_name = %s AND column_name <> 'rowid' "
                             "ORDER BY ordinal_position", [t.table_info], write=False)
        is_write = not re.match(r"\s*(SELECT|WITH)\b", _mask(sql), re.I)
        return self._run(t.sql, _params(params), write=is_write, names_rowid=t.names_rowid)

    def executemany(self, sql: str, seq: Iterable[Any]) -> Cursor:
        import psycopg
        t = self._resolve(sql)
        rows = [_params(p) for p in seq]
        if t.noop or not rows:
            return _EMPTY
        with self._lock:
            self._ensure()
            cur = self._conn.cursor()
            try:
                cur.execute("SAVEPOINT acos_s")
                cur.executemany(t.sql, rows)
                cur.execute("RELEASE SAVEPOINT acos_s")
            except psycopg.Error as exc:
                self._recover()
                raise _map_error(exc) from exc
            self._dirty = True
            return Cursor([], None, len(rows))

    def executescript(self, script: str) -> Cursor:
        """The stores' schema scripts: one transaction, serialised across instances."""
        self.commit()
        with self._lock:
            self._ensure()
            self._run("SELECT pg_advisory_xact_lock(hashtext(%s))", [self.schema], write=False)
            for stmt in split_script(script):
                self.execute(stmt)
            self.commit()
        return _EMPTY

    def commit(self) -> None:
        with self._lock:
            if self._conn is not None and not self._conn.closed:
                self._conn.commit()
            self._dirty = False

    def rollback(self) -> None:
        with self._lock:
            if self._conn is not None and not self._conn.closed:
                self._conn.rollback()
            self._dirty = False

    def close(self) -> None:
        with self._lock:
            if self._conn is not None and not self._conn.closed:
                self._conn.close()

    @property
    def in_transaction(self) -> bool:
        return self._dirty

    def scrub(self) -> None:
        """After an erasure is committed: VACUUM this store's tables, so the erased rows' space is
        freed for reuse instead of kept as dead tuples. (Postgres has no `secure_delete`: the bytes
        are overwritten as the space is reused, and Cloud SQL encrypts the disk; see
        storage/secure_delete.py.) VACUUM cannot run in a transaction, so it uses its own
        connection."""
        import psycopg
        tables = [r[0] for r in self._run("SELECT table_name FROM information_schema.tables "
                                          "WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'",
                                          [], write=False)._rows]
        self.commit()
        with psycopg.connect(**self._dsn, autocommit=True) as conn:
            for t in tables:
                conn.execute(f'VACUUM {self.schema}."{t}"')


_PROCESS_LOCKS: dict[str, threading.Lock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


@contextmanager
def exclusive(conn: Any, name: str) -> Iterator[bool]:
    """At most one holder of `name` across threads and, for a store on Postgres, across instances:
    yields True to the holder and False to anyone who arrives meanwhile, who should skip this round.

    For the work every instance starts on its own (the automations every five minutes of traffic,
    notification delivery), where a check-then-act sequence run twice at once sends things twice.
    Postgres side: a session advisory lock, keyed by the store's schema and `name`; it is reentrant
    within a session, which is why the process lock comes first."""
    with _PROCESS_LOCKS_GUARD:
        local = _PROCESS_LOCKS.setdefault(f"{getattr(conn, 'schema', id(conn))}:{name}", threading.Lock())
    if not local.acquire(blocking=False):
        yield False
        return
    try:
        if not isinstance(conn, Connection):
            yield True
            return
        key = f"{conn.schema}:{name}"
        got = conn._run("SELECT pg_try_advisory_lock(hashtext(%s))", [key], write=False)._rows[0][0]
        if not got:
            yield False
            return
        try:
            yield True
        finally:
            try:
                conn._run("SELECT pg_advisory_unlock(hashtext(%s))", [key], write=False)
            except sqlite3.Error:
                logger.warning("store %s: could not release lock %s; it ends with the connection",
                               conn.schema, name, exc_info=True)
    finally:
        local.release()


def connect(kind: str, db_path: Path) -> Connection:
    return Connection(schema_for(kind, db_path))


class NoSnapshots:
    """The SnapshotSync calls the stores make, for a store whose data is already in Postgres:
    committing is the whole of saving."""

    def commit(self, conn: Connection) -> None:
        conn.commit()

    commit_derived = commit
    save_empty_boot = commit

    def flush(self, *, raise_on_conflict: bool = False) -> bool:
        return True

    def close(self) -> None:
        pass
