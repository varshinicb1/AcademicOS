-- Narrow the FTS update trigger to the columns it actually indexes.
--
-- `chunks_fts_au` was `AFTER UPDATE ON chunks` with no column list, so it also
-- fired for `UPDATE chunks SET vectorized = 1` -- which is every row, once, during
-- indexing. Each firing deleted and re-inserted the full heading_path and text
-- into the FTS index, re-tokenising 12,570 chunks for no reason. Restricting it to
-- the two indexed columns keeps the trigger correct for real content edits while
-- leaving the vectorized bookkeeping alone.

DROP TRIGGER IF EXISTS chunks_fts_au;

CREATE TRIGGER chunks_fts_au AFTER UPDATE OF heading_path, text ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, heading_path, text)
    VALUES ('delete', old.rowid, old.heading_path, old.text);
    INSERT INTO chunks_fts(rowid, heading_path, text)
    VALUES (new.rowid, new.heading_path, new.text);
END;
