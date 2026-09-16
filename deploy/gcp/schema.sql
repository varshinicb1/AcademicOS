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
-- Idempotent: every statement is IF NOT EXISTS, so re-running is safe.
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
CREATE TABLE IF NOT EXISTS papers (
    id      TEXT PRIMARY KEY,
    payload JSONB
);

-- -- practice_sets -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS practice_sets (
    id      TEXT PRIMARY KEY,
    payload JSONB
);

-- -- scan_sessions -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scan_sessions (
    id            TEXT PRIMARY KEY,
    assessment_id TEXT,
    payload       JSONB
);
CREATE INDEX IF NOT EXISTS idx_scan_sessions_assessment ON scan_sessions (assessment_id);

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
-- Emails are stored already lowercased by UserStore.register, so a plain
-- index is enough to serve the login lookup.
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
CREATE INDEX IF NOT EXISTS idx_users_email       ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_school_role ON users (school_id, role);

-- -- sessions ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    TEXT,
    created_at TEXT,
    expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);

-- -- audit_log -----------------------------------------------------------------
-- CERT-In requires this to be retained >= 180 days and effectively
-- append-only. The store never issues an UPDATE/DELETE against it, but that
-- is application-level: no DB constraint enforces it (see docs/compliance.md).
CREATE TABLE IF NOT EXISTS audit_log (
    id            TEXT PRIMARY KEY,
    timestamp     TEXT,
    action        TEXT,
    assessment_id TEXT,
    student_id    TEXT,
    actor         TEXT,
    details       JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_assessment ON audit_log (assessment_id);
CREATE INDEX IF NOT EXISTS idx_audit_action     ON audit_log (action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp  ON audit_log (timestamp DESC);

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
