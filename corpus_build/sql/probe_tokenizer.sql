-- Tokenizer probe: does FTS5 keep Devanagari matras attached to base letters?
DROP TABLE IF EXISTS t_u61;
DROP TABLE IF EXISTS t_tok;
DROP TABLE IF EXISTS t_tri;
DROP TABLE IF EXISTS v_u61;
DROP TABLE IF EXISTS v_tok;
DROP TABLE IF EXISTS v_tri;

CREATE VIRTUAL TABLE t_u61 USING fts5(x, tokenize = "unicode61");
CREATE VIRTUAL TABLE t_tok USING fts5(
  x, tokenize = "unicode61 remove_diacritics 0 categories 'L* N* Mn Mc'"
);
CREATE VIRTUAL TABLE t_tri USING fts5(x, tokenize = "trigram");

INSERT INTO t_u61(rowid, x) VALUES
  (1, 'मैं अपने दादाजी के साथ रहती हूँ'),
  (2, 'photosynthesis chlorophyll chloroplast'),
  (3, 'मैं अपने दादाजी के साथ रहती हूँ');
INSERT INTO t_tok(rowid, x) SELECT rowid, x FROM t_u61;
INSERT INTO t_tri(rowid, x) SELECT rowid, x FROM t_u61;

CREATE VIRTUAL TABLE v_u61 USING fts5vocab(t_u61, row);
CREATE VIRTUAL TABLE v_tok USING fts5vocab(t_tok, row);
CREATE VIRTUAL TABLE v_tri USING fts5vocab(t_tri, row);

SELECT 'u61' AS tok, term FROM v_u61 WHERE term <> '' ORDER BY term;
SELECT 'marks' AS tok, term FROM v_tok WHERE term <> '' ORDER BY term;
SELECT 'tri' AS tok, term FROM v_tri WHERE term <> '' ORDER BY term;
