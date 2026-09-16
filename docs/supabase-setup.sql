-- AcademicOS — required Supabase setup (run once, in the target project's
-- SQL editor).
--
-- Mirrors what each store actually writes via
-- src/academicos/assessment/supabase_kv.py::SupabaseTable, so the column
-- shapes here are load-bearing, not stylistic:
--
--   * PostgREST filters/orders on real columns (e.g. select(email=eq.…),
--     order="seq.desc"), so an "id + payload JSONB" table alone is NOT
--     enough for most of these stores.
--   * graded_evaluations' primary key MUST be (assessment_id, student_id):
--     GradedStore upserts with on_conflict="assessment_id,student_id" and
--     PostgREST rejects that without a matching unique constraint.
--   * learner_events.seq MUST be an integer type: EventStore paginates with
--     `seq > since_seq`, and a text column would compare lexically
--     ('10' < '5' is true for text, false for numbers).
--
-- Why this file exists: on 2026-09-15 the live Render deployment 500'd on
-- /api/v1/auth/login, /auth/register and /auth/me because public.users and
-- public.sessions did not exist, while GET /health/storage still reported
-- "supabase_reachable": true (it probed only the assessments table). Both
-- halves are fixed now — /health/storage probes every table below and
-- reports each one by name — but the tables still have to exist.
-- `create table if not exists` makes this whole file safe to run on a
-- project that already has some of them.
--
-- The service talks to these tables with the project's anon key, from the
-- server only (that key is never shipped to the Flutter client). The GRANT
-- below mirrors Supabase's own default privileges for the public schema.
-- If you enable row level security on any of these tables, add policies
-- for the `anon` role too, or every call will start failing (selects
-- silently return [], writes 401/403): the server-side key carries no JWT
-- claims for RLS to match.

create table if not exists public.users (
  id            text primary key,
  school_id     text not null,
  name          text not null,
  email         text not null,
  password_hash text not null,
  password_salt text not null,
  role          text not null,
  created_at    text not null
);
create unique index if not exists idx_users_email on public.users (email);
create index if not exists idx_users_school on public.users (school_id);

create table if not exists public.sessions (
  token      text primary key,
  user_id    text not null,
  created_at text not null,
  expires_at text not null
);
create index if not exists idx_sessions_user on public.sessions (user_id);

create table if not exists public.assessments (
  id         text primary key,
  school_id  text not null,
  teacher_id text not null,
  created_at text not null,
  payload    jsonb not null
);
create index if not exists idx_assessments_teacher on public.assessments (teacher_id, created_at desc);
create index if not exists idx_assessments_school on public.assessments (school_id, created_at desc);

-- school_id (2026-09-17): real column, not just inside payload -- lets
-- list_by_school() filter server-side for the school-data export route
-- instead of pulling every school's rows to filter client-side. Nullable:
-- rows written before this column existed have no value, and the route
-- being generated for is what supplies it (see paper_store.py's docstring
-- on why this is store-level metadata, not a field on GeneratedPaper itself).
create table if not exists public.papers (
  id        text primary key,
  school_id text,
  payload   jsonb not null
);
-- `create table if not exists` only helps a project that doesn't have this
-- table yet -- the live Render project already did (papers/practice_sets/
-- scan_sessions all reported "ok" on /health/storage before school_id
-- existed at all), so re-running this file there would silently skip adding
-- the column. `add column if not exists` is the real idempotent fix for an
-- already-existing table; safe to run whether or not the table is new.
alter table public.papers add column if not exists school_id text;
create index if not exists idx_papers_school on public.papers (school_id);

create table if not exists public.practice_sets (
  id        text primary key,
  school_id text,
  payload   jsonb not null
);
alter table public.practice_sets add column if not exists school_id text;
create index if not exists idx_practice_sets_school on public.practice_sets (school_id);

create table if not exists public.graded_evaluations (
  assessment_id text not null,
  student_id    text not null,
  payload       jsonb not null,
  primary key (assessment_id, student_id)
);

create table if not exists public.scan_sessions (
  id            text primary key,
  school_id     text,
  assessment_id text not null,
  payload       jsonb not null
);
alter table public.scan_sessions add column if not exists school_id text;
create index if not exists idx_scan_sessions_school on public.scan_sessions (school_id);

create table if not exists public.school_templates (
  id         text primary key,
  school_id  text not null,
  is_default boolean not null default false,
  payload    jsonb not null
);
create index if not exists idx_school_templates_school on public.school_templates (school_id, is_default desc);

create table if not exists public.audit_log (
  id            text primary key,
  timestamp     text not null,
  action        text not null,
  assessment_id text,
  student_id    text,
  actor         text,
  details       jsonb not null default '{}'::jsonb
);
create index if not exists idx_audit_log_assessment on public.audit_log (assessment_id, timestamp desc);
create index if not exists idx_audit_log_action on public.audit_log (action, timestamp desc);

create table if not exists public.learner_events (
  learner_id   text not null,
  seq          bigint not null,
  event_id     text primary key,
  kind         text not null,
  concept_id   text not null,
  outcome      double precision,
  bloom        text,
  difficulty   double precision,
  affect       text,
  duration_sec double precision,
  ts           text not null,
  payload      jsonb,
  unique (learner_id, seq)
);
create index if not exists idx_learner_events_learner on public.learner_events (learner_id, seq);

create table if not exists public.parental_consents (
  id                    text primary key,
  school_id             text not null,
  student_id            text not null,
  guardian_name         text not null,
  guardian_relationship text not null default 'parent',
  method                text not null,
  status                text not null default 'granted',
  purpose               text not null default 'assessment_and_grading',
  notes                 text,
  recorded_by           text not null,
  recorded_at           text not null,
  revoked_at            text,
  revoked_by            text,
  unique (school_id, student_id)
);
create index if not exists idx_parental_consents_school on public.parental_consents (school_id);

grant all on public.users, public.sessions, public.assessments, public.papers,
              public.practice_sets, public.graded_evaluations,
              public.scan_sessions, public.school_templates,
              public.audit_log, public.learner_events,
              public.parental_consents
  to anon, authenticated, service_role;

-- Verify: should return eleven rows, one per table:
--
--   select table_name, count(*) as columns
--   from information_schema.columns
--   where table_schema = 'public'
--     and table_name in ('users','sessions','assessments','papers',
--       'practice_sets','graded_evaluations','scan_sessions',
--       'school_templates','audit_log','learner_events','parental_consents')
--   group by table_name
--   order by table_name;
