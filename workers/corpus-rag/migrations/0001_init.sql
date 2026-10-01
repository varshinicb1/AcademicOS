-- Chapter-isolated chunk store for the NCERT corpus.
--
-- Tokenizer note (verified against this corpus, not assumed): FTS5's default
-- unicode61 treats Devanagari vowel signs as separators, so "मैं अपने दादाजी के
-- साथ रहती हूँ" indexes as म / अपन / क / ज / थ / द / रहत / स / ह. BM25 over those
-- fragments is noise. Adding the combining-mark categories keeps matras attached
-- to their base letter, giving whole words (मैं, दादाजी, रहती) while leaving Latin
-- tokenization unchanged. remove_diacritics 0 is deliberate: stripping diacritics
-- would mangle nukta and anusvara in Hindi text.

CREATE TABLE IF NOT EXISTS chunks (
  id            TEXT PRIMARY KEY,          -- matches the Vectorize vector id
  chapter_id    TEXT NOT NULL,             -- also the Vectorize namespace
  heading_path  TEXT NOT NULL DEFAULT '',
  text          TEXT NOT NULL,
  embed_text    TEXT NOT NULL,             -- breadcrumb + text, what was embedded
  book_code     TEXT NOT NULL DEFAULT '',
  class_no      INTEGER,
  subject       TEXT NOT NULL DEFAULT '',
  language      TEXT NOT NULL DEFAULT '',
  chapter_no    INTEGER,
  -- Provenance gate. A legacy-font chapter decoded to readable Devanagari is fine
  -- for retrieval and topic detection, but its characters are not shaped or
  -- segmented, so it must never be quoted verbatim as evidence.
  text_quality  TEXT NOT NULL DEFAULT 'native-text-layer',
  quote_exact   INTEGER NOT NULL DEFAULT 1,
  n_chars       INTEGER,
  est_tokens    INTEGER,
  text_sha      TEXT,
  -- Set once the vector is confirmed in the index, so a re-run only does the
  -- rows that are actually missing instead of re-embedding 12k chunks.
  vectorized    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_chunks_chapter  ON chunks(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chunks_class    ON chunks(class_no);
CREATE INDEX IF NOT EXISTS idx_chunks_subject  ON chunks(subject, class_no);
CREATE INDEX IF NOT EXISTS idx_chunks_pending  ON chunks(vectorized);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  heading_path,
  text,
  content = 'chunks',
  content_rowid = 'rowid',
  tokenize = "unicode61 remove_diacritics 0 categories 'L* N* Mn Mc'"
);

CREATE TRIGGER IF NOT EXISTS chunks_fts_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, heading_path, text)
  VALUES (new.rowid, new.heading_path, new.text);
END;

CREATE TRIGGER IF NOT EXISTS chunks_fts_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, heading_path, text)
  VALUES ('delete', old.rowid, old.heading_path, old.text);
END;

CREATE TRIGGER IF NOT EXISTS chunks_fts_au AFTER UPDATE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, heading_path, text)
  VALUES ('delete', old.rowid, old.heading_path, old.text);
  INSERT INTO chunks_fts(rowid, heading_path, text)
  VALUES (new.rowid, new.heading_path, new.text);
END;

-- One row per indexing run. The indexer is a long job that has been killed
-- before, so progress has to survive the Worker as well as the client.
CREATE TABLE IF NOT EXISTS index_runs (
  run_id           TEXT PRIMARY KEY,
  status           TEXT NOT NULL,          -- running | done | failed
  started_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL,
  total_chunks     INTEGER NOT NULL DEFAULT 0,
  indexed_chunks   INTEGER NOT NULL DEFAULT 0,
  failed_chunks    INTEGER NOT NULL DEFAULT 0,
  embed_batch_size INTEGER,
  model            TEXT,
  last_error       TEXT
);
