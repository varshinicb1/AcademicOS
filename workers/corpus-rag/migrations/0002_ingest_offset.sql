-- Ingest needs its own resumable cursor.
--
-- The embed cursor is `chunks.vectorized`, but ingest streams a gzipped R2 object
-- and has to resume mid-object. It cannot ask "which rows are missing" the way the
-- embedder can, so it records how many records of the pack it has consumed.
-- Kept on index_runs rather than in KV so it commits with the counts it describes.

ALTER TABLE index_runs ADD COLUMN ingest_offset INTEGER NOT NULL DEFAULT 0;
