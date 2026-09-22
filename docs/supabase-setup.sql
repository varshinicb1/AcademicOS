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

-- Registration needs an invite since 2026-09-21 (see assessment/users.py).
-- The empty string, not NULL, means "not yet" for email/used_by/used_at/
-- revoked_at: UserStore claims an invite with one PATCH filtered on
-- used_at=eq.&revoked_at=eq., and that filter never matches NULL. Keep the
-- NOT NULL DEFAULT '' or single use stops being enforceable.
create table if not exists public.invites (
  code       text primary key,
  school_id  text not null,
  role       text not null,
  email      text not null default '',
  created_by text not null,
  created_at text not null,
  expires_at text not null,
  used_by    text not null default '',
  used_at    text not null default '',
  revoked_at text not null default ''
);
create index if not exists idx_invites_school on public.invites (school_id);

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
-- Hash chain (2026-09-22; see src/academicos/assessment/audit_log.py). The
-- server writes these three columns on every append, so they must exist
-- BEFORE a build that includes this change is deployed. Without them every
-- remote append fails and falls back to the instance's local disk, which
-- Render wipes on restart.
alter table public.audit_log add column if not exists seq        bigint;
alter table public.audit_log add column if not exists prev_hash  text;
alter table public.audit_log add column if not exists entry_hash text;
create index if not exists idx_audit_log_assessment on public.audit_log (assessment_id, timestamp desc);
create index if not exists idx_audit_log_action on public.audit_log (action, timestamp desc);
create unique index if not exists idx_audit_log_seq on public.audit_log (seq);

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

grant all on public.users, public.sessions, public.invites, public.assessments, public.papers,
              public.practice_sets, public.graded_evaluations,
              public.scan_sessions, public.school_templates,
              public.learner_events,
              public.parental_consents
  to anon, authenticated, service_role;

-- audit_log is append-only (audit item 8.5, 2026-09-21). Until this block it
-- was granted `all` to anon with no RLS, so anyone holding the key could
-- PATCH or DELETE entries through PostgREST. The server uses the anon key
-- (see the note at the top of this file), so anon is the role that must be
-- able to INSERT and SELECT, and nothing more:
--   * privileges: INSERT and SELECT only; UPDATE, DELETE and TRUNCATE are
--     revoked from every API role;
--   * RLS on, with policies for INSERT and SELECT only. With no UPDATE or
--     DELETE policy, PostgREST cannot do either even if a grant comes back;
--   * a trigger aborts UPDATE and DELETE for every role, including
--     service_role and postgres, which bypass RLS.
-- `authenticated` gets nothing: no client of this service holds a Supabase
-- user JWT.
revoke all on public.audit_log from anon, authenticated, service_role;
grant select, insert on public.audit_log to anon, service_role;
alter table public.audit_log enable row level security;
drop policy if exists audit_log_server_insert on public.audit_log;
create policy audit_log_server_insert on public.audit_log
  for insert to anon, service_role with check (true);
drop policy if exists audit_log_server_select on public.audit_log;
create policy audit_log_server_select on public.audit_log
  for select to anon, service_role using (true);

create or replace function public.audit_log_refuse_change() returns trigger
language plpgsql as $$
begin
  raise exception 'audit_log is append-only: % refused', tg_op;
end;
$$;
drop trigger if exists audit_log_append_only on public.audit_log;
create trigger audit_log_append_only
  before update or delete on public.audit_log
  for each row execute function public.audit_log_refuse_change();

-- Verify the audit_log lock (expect: rls on; anon has INSERT and SELECT
-- only; one trigger):
--
--   select relrowsecurity from pg_class where oid = 'public.audit_log'::regclass;
--   select grantee, privilege_type from information_schema.role_table_grants
--    where table_schema = 'public' and table_name = 'audit_log' order by 1, 2;
--   select tgname from pg_trigger
--    where tgrelid = 'public.audit_log'::regclass and not tgisinternal;

-- KnowledgeStore's per-student mastery history. Long-standing on the Render
-- project (created by an earlier migration); listed here so a fresh project
-- gets it too, now that /health/storage probes it.
create table if not exists public.learner_models (
  student_id text primary key,
  payload    jsonb not null
);

grant all on public.users, public.sessions, public.assessments, public.papers,
              public.practice_sets, public.graded_evaluations,
              public.scan_sessions, public.school_templates,
              public.audit_log, public.learner_events,
              public.parental_consents, public.learner_models
  to anon, authenticated, service_role;

-- Verify: should return twelve rows, one per table:
--
--   select table_name, count(*) as columns
--   from information_schema.columns
--   where table_schema = 'public'
--     and table_name in ('users','sessions','invites','assessments','papers',
--       'practice_sets','graded_evaluations','scan_sessions',
--       'school_templates','audit_log','learner_events','parental_consents',
--       'learner_models')
--   group by table_name
--   order by table_name;
