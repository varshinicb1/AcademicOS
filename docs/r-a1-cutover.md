# R-A1: moving CurriculumStore and OperationsStore to Cloud SQL

**What it changes.** The two stores hold about 80 tables: the school's year, classes, timetable,
plans, cover, homework, marks, exams and notifications. Today they live in SQLite files on the
container, snapshotted to GCS every 20 to 30 seconds. That pins the service to one instance, because
two would overwrite each other's snapshots. A crash can also lose up to 30 seconds of a school's
writes. On Cloud SQL every write is durable when it commits, and two or more instances can serve
the same school.

**State of the code (October 2026).** Everything below is in `master`, and none of it is active
until `ACOS_STORE_BACKEND=postgres` is set on the service. Until the cutover, live runs exactly as
before.

| Piece | Where |
|---|---|
| SQLite-shaped connection over Postgres: every call site keeps its SQL | `src/academicos/storage/pg_sqlite.py` |
| The stores pick it when `ACOS_STORE_BACKEND=postgres` | `curriculum/store.py`, `operations/store.py` |
| One automation run and one delivery pass across instances | `pg_sqlite.exclusive`, `operations/automations.py`, `operations/notifications.py` |
| Copy of the live snapshots into Postgres, verified value by value | `src/academicos/storage/migrate_stores.py` (`python -m academicos.storage.migrate_stores`) |
| Marker that stops a forgotten SQLite boot after the move | `pg_sqlite.refuse_if_moved`, `--mark-moved` |
| Which backend live is on | `/health/storage` → `school_stores` |

## How the plan's open findings were resolved

The 7 October plan (`docs/handover/2026-10-07-r-a1-plan.md`) was approved on 13 October (issue 143)
on condition that six findings were fixed first. Each one, and its evidence:

1. **Check-then-act across instances.**
   - What it was: every instance runs the automations on its own (every five minutes of traffic, and on the scheduler's call), so two runs at once both found a job "not done" and both ran it. Notification delivery was locked only inside one process.
   - The fix: both now take `pg_sqlite.exclusive`, a process lock plus a Postgres advisory lock. A run that finds another one going skips that round.
   - Evidence: `tests/test_two_instances.py` starts two processes on one schema at the same moment. Each scheduled job runs once and each of 6 messages is sent once. With the advisory lock removed, both jobs run twice (`[2, 2]`) and every message is sent twice (`[6, 6]`).
   - Other read-modify-write paths (cover, plan rebuilds, leave decisions) are started by a person, one request at a time. They keep their transactions, as on SQLite.
2. **SQLite constructs the plan missed.**
   - The translator handles all of them: `INSERT OR IGNORE` (3 sites), `INSERT OR REPLACE` (4), `rowid` ordering (5), `AUTOINCREMENT` (1), `instr()` (1), `IS ?`, `WHERE 0`, two-argument `max`/`min`, and every `PRAGMA`. It does this without touching their call sites.
   - `rowid` is a hidden identity column on every table, so `ORDER BY date, rowid` keeps insertion order. The copy preserves each row's SQLite rowid.
   - Out of scope: the other SQLite files (`storage/event_store.py`, `storage/registry.py`) and the JSONB stores, which are already on Cloud SQL.
3. **`%` in statements.** Every literal `%` is doubled before psycopg reads the text (`test_placeholders_and_percent_signs_but_not_inside_strings`).
4. **The concurrency test compared row counts only.** It now counts side effects (finding 1's test). It also proves its own value: it fails with the lock removed.
5. **No performance criterion.**
   - Statements sent per operation, counted under the test suite:
     - setting up a whole school: about 5,600;
     - planning every section: about 4,300;
     - the term report: about 400.
   - At an assumed 1 ms per statement on Cloud SQL, that is about 14 s, 11 s and under 1 s, against 13 s, 7.5 s and under 1 s on SQLite today. That is within the 2× bar and far from Cloud Run's 300 s limit.
   - The rehearsal measures the real round trip (`--latency`) and turns these estimates into figures. A route that comes out over 2× is batched before the cutover.
6. **Ordering.**
   - SQLite sorts NULLs first and text byte by byte. Every `ORDER BY` term gains `NULLS FIRST` (ascending) or `NULLS LAST` (descending), and every TEXT column is `COLLATE "C"`.
   - The case-insensitive columns (`COLLATE NOCASE`) use an ICU collation that ignores case.
   - Tests: `test_nulls_sort_first_and_text_sorts_by_bytes_as_in_sqlite`.

**The whole backend suite on Postgres:**
- `ACOS_STORE_BACKEND=postgres` against PostgreSQL 18: 5,025 passed, then the last 12 fixed or marked.
- The 11 tests that inspect the SQLite file itself (its snapshot, its bytes after an erasure, migrating an old `.sqlite`) are marked `sqlite_only` and skip there.

## Decisions for the owner

1. **The rehearsal database.** Proposed: `academicos_rehearsal` on the existing `academicos-pg` instance. The rehearsal only reads the live snapshots and writes into that database, so live is untouched.
2. **The cutover window.** About 30 minutes outside school hours. Users see errors for the 10 to 15 minutes the service is closed (step 2 below). Proposed: a weekday between 21:00 and 22:00 IST, with no exam running.

## Rehearsal

The copy runs as a one-off Cloud Run job, from the image that is about to be deployed, with the service's own account and database connection. The live data never leaves Google Cloud.

```bash
SHA=<the commit about to be deployed>        # its image must be built (deploy-by-hand.md step 2)
IMAGE=asia-south1-docker.pkg.dev/vidyuthlabs/academicos/backend:$SHA
gcloud sql databases create academicos_rehearsal --instance academicos-pg --project vidyuthlabs

gcloud run jobs deploy acos-move-stores --project vidyuthlabs --region asia-south1 --image "$IMAGE" \
  --service-account academicos-runtime@vidyuthlabs.iam.gserviceaccount.com \
  --set-cloudsql-instances vidyuthlabs:asia-south1:academicos-pg \
  --set-secrets ACOS_POSTGRES_PASSWORD=postgres-password:latest \
  --set-env-vars "^@^ACOS_POSTGRES_HOST=/cloudsql/vidyuthlabs:asia-south1:academicos-pg@ACOS_POSTGRES_DB=academicos_rehearsal@ACOS_POSTGRES_USER=academicos@ACOS_GCS_BUCKET=vidyuthlabs-academicos-media@ACOS_PG_SCHEMA_CURRICULUM=curriculum@ACOS_PG_SCHEMA_OPERATIONS=operations" \
  --command python --args="-m,academicos.storage.migrate_stores,--from-gcs,--latency" \
  --max-retries 0 --task-timeout 1800
gcloud run jobs execute acos-move-stores --project vidyuthlabs --region asia-south1 --wait
```

Read the job's log in the console, or with `gcloud logging read`. It prints:
- every table's row count;
- the SHA-256 of each snapshot;
- one statement's round trip.

A value that would not read back as it was stops the job. It names the table, row and column, and rolls back. Record the counts and the round trip in the cutover PR. Run the job twice: the second run must print the same counts, which proves a re-run repairs rather than doubles.

The rehearsal database can be dropped afterwards: `gcloud sql databases delete academicos_rehearsal --instance academicos-pg`.

## Cutover

All in one sitting, at the agreed window.

1. **Build** the release image and run the gates (`docs/deploy-by-hand.md`, steps 1 and 2).
2. **Close the service** to the public and let the last snapshot upload:
   ```bash
   gcloud run services update academicos-backend --project vidyuthlabs --region asia-south1 --ingress internal
   ```
   Wait 2 minutes: the snapshot debounce is at most 30 s. Check that both objects in the bucket stop changing (`gcloud storage ls -l gs://vidyuthlabs-academicos-media/academicos/curriculum-snapshots/` and the operations equivalent).
3. **Copy** with the job above, pointed at the live database. Set `ACOS_POSTGRES_DB=academicos` and add `--mark-moved` to its args. The job aborts and rolls back on any mismatch; if it does, go to Rollback. `--mark-moved` leaves `MOVED_TO_POSTGRES` beside each snapshot. From then on a SQLite boot refuses to start unless `ACOS_STORE_BACKEND=sqlite` is set on purpose.
4. **Deploy** the same image with three more settings: `ACOS_STORE_BACKEND=postgres`, `ACOS_PG_SCHEMA_CURRICULUM=curriculum` and `ACOS_PG_SCHEMA_OPERATIONS=operations`. Add them to `ENV_VARS` in `docs/deploy-by-hand.md` step 3, and in the same change add them to `.github/workflows/deploy-gcp.yml`. Every later deploy must carry them; the marker is there to catch the one that does not.
5. **Verify** before reopening:
   - `/health` names the commit;
   - `/health/storage` shows `"school_stores": {"backend": "postgres", "schemas": {"curriculum": "curriculum", "operations": "operations"}}`;
   - `scripts/prod_check.py` passes;
   - sign in as the operator and open a school's My week, a homework and the term report.
6. **Reopen**: `gcloud run services update academicos-backend --ingress all`.
7. **Watch** the logs and error reports for an hour. Then, in a separate change a day later, raise `--max-instances` to 2 in both deploy paths. `test_two_instances.py` is what makes that safe.

## Rollback

Before step 6, or within the first hours: deploy the previous configuration with `ACOS_STORE_BACKEND=sqlite`, set explicitly (it gets past the marker). Then delete the two `MOVED_TO_POSTGRES` objects. The service restores the snapshots frozen at step 2.

Writes made on Postgres after step 6 are not in those snapshots and would be lost. That is why the decision to roll back has to be made before reopening, or quickly after. Later, roll forward instead: fix on Postgres, where the data now is.
