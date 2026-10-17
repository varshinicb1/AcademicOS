-- =============================================================================
-- AcademicOS -- Cloud SQL (PostgreSQL) schema
-- =============================================================================
--
-- The Cloud SQL equivalent of docs/supabase-setup.sql. One table per store
-- that used a Supabase table, with the same shape: a handful of real columns
-- used for filtering/ordering, plus one JSONB column holding the full
-- payload. See src/academicos/assessment/postgres_kv.py for why.
--
-- Apply (the instance is private by default; run this from Cloud Shell, which
-- is already inside the project):
--
--   gcloud sql connect academicos-pg --user=academicos --database=academicos \
--     < deploy/gcp/schema.sql
--
-- or from anywhere with the instance reachable:
--
--   psql "host=/cloudsql/PROJECT:REGION:academicos-pg dbname=academicos \
--         user=academicos" -f deploy/gcp/schema.sql
--
-- Idempotent: every statement is IF NOT EXISTS (or CREATE OR REPLACE / DROP
-- IF EXISTS for the audit_log trigger), so re-running is safe.
-- =============================================================================

-- -- assessments ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessments (
    id          TEXT PRIMARY KEY,
    school_id   TEXT,
    teacher_id  TEXT,
    created_at  TEXT,
    payload     JSONB
);
CREATE INDEX IF NOT EXISTS idx_assessments_school  ON assessments (school_id);
CREATE INDEX IF NOT EXISTS idx_assessments_teacher ON assessments (teacher_id);
CREATE INDEX IF NOT EXISTS idx_assessments_created ON assessments (created_at DESC);

-- -- papers --------------------------------------------------------------------
-- school_id (2026-09-17): store-level metadata for list_by_school() / the
-- school-data export route -- see src/academicos/assessment/paper_store.py's
-- module docstring for why it's a column here rather than a field on
-- GeneratedPaper itself. ADD COLUMN IF NOT EXISTS alongside CREATE TABLE IF
-- NOT EXISTS so this stays correct however far this file has already been
-- applied (matching docs/supabase-setup.sql's equivalent fix, made after the
-- Render project's already-existing tables didn't get a column that only
-- CREATE TABLE IF NOT EXISTS would have added).
CREATE TABLE IF NOT EXISTS papers (
    id        TEXT PRIMARY KEY,
    school_id TEXT,
    payload   JSONB
);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS school_id TEXT;
CREATE INDEX IF NOT EXISTS idx_papers_school ON papers (school_id);

-- -- practice_sets -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS practice_sets (
    id        TEXT PRIMARY KEY,
    school_id TEXT,
    payload   JSONB
);
ALTER TABLE practice_sets ADD COLUMN IF NOT EXISTS school_id TEXT;
CREATE INDEX IF NOT EXISTS idx_practice_sets_school ON practice_sets (school_id);

-- -- scan_sessions -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scan_sessions (
    id            TEXT PRIMARY KEY,
    school_id     TEXT,
    assessment_id TEXT,
    payload       JSONB
);
ALTER TABLE scan_sessions ADD COLUMN IF NOT EXISTS school_id TEXT;
CREATE INDEX IF NOT EXISTS idx_scan_sessions_assessment ON scan_sessions (assessment_id);
CREATE INDEX IF NOT EXISTS idx_scan_sessions_school ON scan_sessions (school_id);

-- -- graded_evaluations --------------------------------------------------------
-- Composite key, matching the store's on_conflict="assessment_id,student_id".
CREATE TABLE IF NOT EXISTS graded_evaluations (
    assessment_id TEXT NOT NULL,
    student_id    TEXT NOT NULL,
    payload       JSONB,
    PRIMARY KEY (assessment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_graded_student ON graded_evaluations (student_id);

-- -- users ---------------------------------------------------------------------
-- Emails are stored already lowercased by UserStore.register. The email
-- index is UNIQUE, as in docs/supabase-setup.sql: two invites for one email
-- redeemed at the same moment both pass UserStore's get_by_email check, and
-- only this index stops the second (UserStore maps SQLSTATE 23505 to
-- "email already registered"). It was a plain index until 2026-09-22, which
-- let Cloud SQL store that email twice.
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    school_id     TEXT,
    name          TEXT,
    email         TEXT,
    password_hash TEXT,
    password_salt TEXT,
    role          TEXT,
    created_at    TEXT
);
DROP INDEX IF EXISTS idx_users_email;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_school_role ON users (school_id, role);

-- -- sessions ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    TEXT,
    created_at TEXT,
    expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);

-- -- invites -------------------------------------------------------------------
-- Registration needs one since 2026-09-21 (see assessment/users.py). The empty
-- string, not NULL, means "not yet" for email/used_by/used_at/revoked_at:
-- UserStore claims an invite with one UPDATE filtered on used_at = '' AND
-- revoked_at = '', and equality never matches NULL. Keep the NOT NULL
-- DEFAULT '' or single use stops being enforceable.
CREATE TABLE IF NOT EXISTS invites (
    code       TEXT PRIMARY KEY,
    school_id  TEXT NOT NULL,
    role       TEXT NOT NULL,
    email      TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_by    TEXT NOT NULL DEFAULT '',
    used_at    TEXT NOT NULL DEFAULT '',
    revoked_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_invites_school ON invites (school_id);

-- -- audit_log -----------------------------------------------------------------
-- CERT-In requires this to be retained >= 180 days and append-only. Until
-- 2026-09-22 that was only an application convention, and the audit
-- reproduced a raw UPDATE and DELETE rewriting rows (item 8.5). Now the
-- database enforces it:
--   * a trigger aborts every UPDATE and DELETE, from any role, including the
--     table owner the service connects as;
--   * AuditLog appends with a plain INSERT (PostgresTable.insert), so a
--     replayed id is a unique violation, not an overwrite;
--   * seq / prev_hash / entry_hash form a hash chain that
--     AuditLog.verify_chain() checks (see audit_log.py). seq is UNIQUE, so
--     two instances racing for the same seq cannot fork the chain.
-- TRUNCATE is not a row trigger event and is still possible for the owner.
-- The test fixtures rely on that, and removing it is a DBA decision about
-- the owner role, not something this file can enforce.
CREATE TABLE IF NOT EXISTS audit_log (
    id            TEXT PRIMARY KEY,
    timestamp     TEXT,
    action        TEXT,
    assessment_id TEXT,
    student_id    TEXT,
    actor         TEXT,
    details       JSONB
);
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS seq        BIGINT;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS prev_hash  TEXT;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS entry_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_audit_assessment ON audit_log (assessment_id);
CREATE INDEX IF NOT EXISTS idx_audit_action     ON audit_log (action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp  ON audit_log (timestamp DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_seq ON audit_log (seq);

CREATE OR REPLACE FUNCTION audit_log_refuse_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only: % refused', TG_OP;
END;
$$;
DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log;
CREATE TRIGGER audit_log_append_only
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_refuse_change();

-- -- school_templates ----------------------------------------------------------
-- is_default is TEXT ('true'/'false'), not BOOLEAN: the store filters on the
-- literal string "true" and orders by is_default DESC, both of which work
-- correctly on text ('true' > 'false'). See postgres_kv.py's docstring.
CREATE TABLE IF NOT EXISTS school_templates (
    id         TEXT PRIMARY KEY,
    school_id  TEXT,
    is_default TEXT DEFAULT 'false',
    payload    JSONB
);
CREATE INDEX IF NOT EXISTS idx_templates_school ON school_templates (school_id, is_default DESC);

-- -- learner_events ------------------------------------------------------------
-- seq must be a real integer: EventStore pages with seq > since_seq and
-- ORDER BY seq, which would sort wrongly if it were text.
CREATE TABLE IF NOT EXISTS learner_events (
    event_id     TEXT PRIMARY KEY,
    learner_id   TEXT NOT NULL,
    seq          BIGINT NOT NULL,
    kind         TEXT,
    concept_id   TEXT,
    outcome      TEXT,
    bloom        TEXT,
    difficulty   TEXT,
    affect       TEXT,
    duration_sec DOUBLE PRECISION,
    ts           TEXT,
    payload      JSONB
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_learner_seq ON learner_events (learner_id, seq);

-- -- parental_consents ---------------------------------------------------------
-- DPDP Act 2023: verifiable consent record for minor accounts. One row per
-- (school, student) -- re-consent and revocation overwrite in place.
CREATE TABLE IF NOT EXISTS parental_consents (
    id                    TEXT,
    school_id             TEXT NOT NULL,
    student_id            TEXT NOT NULL,
    guardian_name         TEXT,
    guardian_relationship TEXT,
    method                TEXT,
    status                TEXT,
    purpose               TEXT,
    notes                 TEXT,
    recorded_by           TEXT,
    recorded_at           TEXT,
    revoked_at            TEXT,
    revoked_by            TEXT,
    PRIMARY KEY (school_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_consents_school ON parental_consents (school_id);

-- -- learner_models ------------------------------------------------------------
-- KnowledgeStore (assessment/knowledge.py): one row per student holding the
-- whole mastery history as JSONB. Added 2026-09-22 when the store moved onto
-- durable_table -- before that it spoke Supabase REST directly and, with the
-- Supabase secrets dropped from the GCP deploy, would have written local JSON
-- that every redeploy wipes. Copy existing rows with
-- scripts/migrate_supabase_to_cloudsql.py --only learner_models.
CREATE TABLE IF NOT EXISTS learner_models (
    student_id TEXT PRIMARY KEY,
    payload    JSONB
);

-- -- rate_limit_hits (not created here) ----------------------------------------
-- The shared rate limiter (src/academicos/api/rate_limit.py, R-A3) creates its
-- own table on first use, because its rows are disposable hits and no store
-- reads them; /health/storage does not list it. If the app's database user
-- may not create tables, run this once instead:
--
--   create table if not exists rate_limit_hits (limiter text not null,
--     key text not null, at timestamptz not null default now());
--   create index if not exists idx_rate_limit_hits
--     on rate_limit_hits (limiter, key, at);
