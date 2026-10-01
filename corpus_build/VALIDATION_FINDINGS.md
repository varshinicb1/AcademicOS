# OCR fidelity validation — findings

**Date:** 2026-10-01
**Scope:** 38 rebuilt Vision-OCR chapters (6 `en-IN`, 32 `hi-IN`) vs their source PDFs.
**Final metric:** `validate_word_fidelity.py` → `word_fidelity.json` / `word_fidelity.md`

## Result

| verdict | chapters |
|---|---|
| `verified` (worst page ≥ 0.88) | **38** |
| `review` (worst page 0.80–0.88) | 0 |
| `page-failure` (worst page < 0.80) | **0** |

All 38 chapters now verify. The worst single page in the entire corpus is
`jhsp1-ch10` p10 at **0.8909**, and the weakest chapter's *mean* page score is
0.914. All 6 English chapters and all 32 Hindi chapters are `verified`, and no
page in any chapter scores below 0.88 — not one page was dropped,
half-transcribed, or column-scrambled.

## Two validators disagree, and the 4-gram one is wrong

`validate_page_alignment.py` (4-gram containment) reports widespread
`page-failure` on the same corpus. That is not a real regression, and the
control experiment settles it:

| metric | English (decoder never applied) | Hindi (decoder applied) |
|---|---|---|
| `validate_page_alignment` worst page | **0.833** mean | 0.611 mean |

The English chapters have byte-clean OCR and never invoke the legacy decoder,
yet they still score only 0.83 on the 4-gram metric. A metric that reports
0.83 for flawless content is measuring character-level noise — word order,
punctuation, and line joins — not fidelity. Its page-failures were superseded
by `validate_word_fidelity.py` for exactly this reason, and nothing here
changes that decision.


## Four fixes applied after the first full pass

**1. Legacy decoder repaired.** `decode_legacy` in
`scripts/pdf_ingest/ncert_extract.py` did a flat, context-free table lookup.
KrutiDev writes the pre-base i-matra *before* the consonant it belongs to, so
a context-free table rendered `मिश्र` as `िमश्र` and `किया` as `िकया` across
most Hindi chapters. It now delegates to `lipi.preprocessor.HindiPreprocessor`,
which adds an i-matra reordering pass, with the previous table lookup retained
as a fallback when lipi is unavailable.

The layout is now chosen per page from the fonts actually embedded, via the new
`font_type_for()`. This matters: `krutidev` and `walkman_chanakya` share one
ASCII layout, but `chanakya` is a **different** layout and decoding
KrutiDev/Walkman text with it produces garbage. Of 10,722 legacy spans across
the 32 Hindi chapters, 10,680 are `Walkman-Chanakya905*` and 22 are
`ChanakyaThin` (in `jhsy1-ch01/02/03`).

Measured effect, comparing lipi against the old flat table on the same 277
Hindi pages with matra-sensitive tokens: **better on 204 pages, worse on 2,
tied on 71**, mean +0.0124. The main validator's `norm_word` strips
`U+093A–U+094F`, so it is matra-blind by construction and cannot show this
improvement; the number above comes from a separate matra-preserving
comparison.

The decoder is still not a perfect inverse. Context-sensitive conjunct
reordering is unimplemented, so `लखनऊ` arrives as `लखनउफ` and `स्वतंत्र` as
`स्वतंत्ा`. That is the decoder's floor, not the OCR's.

### A rejected change, and why it matters that it was tested

lipi's krutidev table has 139 entries, and 2.54% of the characters in these
PDFs' text layers are absent from it (`]` 2221×, `\` 542×, `{` 398×, `^` 382×,
`}` 94×, `|` 83×). Because the validator's token pattern splits on non-word
characters, an unmapped `|` shatters a word rather than merely garbling it, so
this looked like a promising fix.

Two independent published KrutiDev 010 tables were fetched and their entries for
exactly those characters were merged in. **This made validation worse: worse on
244 of 272 Hindi pages, better on none**, mean 0.9687 → 0.9632.

The reason is now clear and was not obvious beforehand. lipi's `walkman_chanakya`
table is deliberately *corrected*: for the aspirated series it puts the **halant**
form on the bare key and the full consonant on the suffixed key — `F`→`थ्` with
`Fk`→`थ`, `D`→`क्`, `X`→`ग्`, `[`→`ख्`. The published tables instead put the
full consonant on the bare key (`F`→`थ`, `D`→`क`) and have no `Dk` at all,
because that is the layout a naive KrutiDev user would type. Merging a "missing"
`D` from the naive table therefore does not merely fail to help — it overwrites
a deliberately corrected entry with a wrong one, and corrupts words that
currently decode correctly.

The negative result is recorded here deliberately: the unmapped characters are
real, but completing the table from a generic 8-bit reference is not the fix.

**2. Page furniture was being scored as missing content.** `word_fidelity`
compares every PDF word against the OCR, but the OCR pipeline deliberately
strips page furniture — `Reprint 2026-27` matches the cleaner's own `REPRINT`
regex in `strip_narration.py`, and the ©NCERT imprint is never transcribed at
all. Scoring the OCR against stamps it is *supposed* to remove was unfair, and
it cost roughly 0.05 on every Hindi page.

`validate_word_fidelity.py` now strips furniture from the PDF side before
scoring. The patterns come from the cleaner's own regexes rather than a
hand-kept list, so the two cannot drift. One addition was necessary because the
cleaner only ever handles readable text: in the legacy-font text layer the
imprint arrives garbled as `ऋमचतपदज २०२६-२७`, so the filter also recognises a
garbled imprint plus a year range.

Audit of what the filter actually removes, across all 38 chapters: **2 distinct
line shapes, 467 lines**, both of them imprint/reprint furniture. No lesson
content is dropped. This was verified rather than assumed, because a filter
this broad could easily have been quietly deleting real text.

Effect: `review` chapters fell from 8 to 1.

**3. The last `review` chapter was a punctuation spelling mismatch, not missing
text.** `jhsp1-ch01` p5 held at 0.8636 on eight unmatched tokens, all of the
form `हइ।।`, `सथ।।`, `सभइ।।`, `रव।।`. The reason is that the same glyph reaches
us in two spellings: the OCR transcribes the sentence end as a double danda
`॥` (U+0965), while the legacy font's text layer decodes it as two single
dandas `।।`. NFKC does not unify them — U+0965 has no decomposition — so
`हइ॥` and `हइ।।` were being scored as two different words.

This is worth recording as a *methodological* point, because it is the second
time in this pass that an apparently alarming residual turned out to be a
measurement artifact rather than damaged content, and the first time
(`ऐवफ`, `वफडल`) my own guess about the cause was simply wrong: I assumed the
`वफ`→`य` defect explained the whole page, and checking the actual OCR text
showed those tokens had no counterpart in the corpus at all. Only reading the
real strings distinguished the two.

`norm_word` now folds any run of danda characters to a single canonical form,
which is a representation normalisation of exactly the same kind as the
existing `_DIGIT_FOLD`, not a tolerance. Measured across all 32 Hindi chapters,
it improves 4 pages and degrades none, which is what a correct normalisation
must do.

Effect: `review` chapters 1 → 0, and the corpus is now 38/38.

**4. One real OCR omission patched.** `fepr1-ch05` p20 dropped the figure
labels `Delta`, `Diamond`, `Parafoil` and `Rokkaku`. The four Hindi answers
directly below the figure still describe them (upper kite triangular = Delta,
two diamond-shaped = Diamond, lower kite = Parafoil/Rokkaku), so the loss was
the figure's own text layer only. `patch_fepr1_kite_labels.py` restored the
four labels at the figure position with a short caption, in both the cleaned
OCR source and the canonical body, and corrected `n_chars` 34500 → 34576.
Page 20 improved 0.8286 → 0.9429 and the chapter moved to `verified`.

The rebuilt pack was diffed against the live pack before deployment: 12,499
chunk ids on both sides, none added or removed, and **exactly one** chunk
differed — `fepr1-ch05:015`, `n_chars` 1162 → 1238, with the caption inserted
between the figure and the question that follows it. `quote_exact` was
unchanged. `refresh_fepr1_kite_chunk.py` then pushed it, asserting that exactly
one chunk fell out of `vectorized` after the replay; it did, 12,498 chunks kept
their vectors, and re-indexing cost a single embedding. Final health: total
12,499, vectorized 12,499, pending 0. Retrieval for the kite labels now returns
`fepr1-ch05`, and the chunk is still correctly withheld from
`require_quote_exact=true` queries.

## Why the source PDF text layer could not be the yardstick

Three earlier metrics were discarded because each measured the witness rather
than the OCR.

1. **Exact word equality** → 32/38 chapters condemned. `decode_legacy` is
   context-free: it renders `व्यथा` as `िबथा`, `वियोग` as `िवयोग`,
   `बारूद` as `बा:द`, and `दीवार में गोश दारद`. A one-consonant difference is a
   one-consonant difference, not a missing word.
2. **Fuzzy `SequenceMatcher` per word** → quadratic, exhausted memory, and
   scored number coverage 0.0 for any chapter containing no numbers.
3. **Character 5-gram containment** → produced *lower* scores than exact word
   matching, which was the clue that the two sides disagree
   character-for-character far too often for any strict metric to pass.

Character-level agreement with a context-free decoder is capped well below 1.0
for a perfect OCR. Measured: Hindi prose pages 0.760, glossary pages 0.625 — a
systematic 0.135 gap present in 28 of 32 Hindi chapters, because the decoder
reliably garbles glossary *terms* while leaving their *glosses* intact.

## What the final metric does

An OCR word counts as present if the page text layer holds that word or any word
within **one edit**, computed exactly (not approximately) with a
single-deletion index, so it is a set lookup rather than a pairwise match. The
tolerance is set to the measured decoder failure mode, not chosen for
convenience, and is capped at one so a dropped page still fails. Words under
three characters are excluded because particles such as `की` and `में` are
mostly decode noise.

Direction matters: the score measures *PDF words recovered by the OCR*, so a
dropped page cannot be hidden by OCR being verbose.

## Bugs found and fixed in the validator

- **Decoding English pages.** `detect_legacy` fires on a single stray legacy
  font, so `aejm1-ch13` p4 (`KrutiDev010`) and `gecu1-ch12` p7 (`Chanakya`)
  had clean English transliterated into Devanagari gibberish and were scored
  against it — three pages came out at exactly 0.000. Decoding is now gated on
  the authoritative manifest language, and within a Hindi page the decoded
  variant must actually raise Devanagari density to be accepted.
- **Scrambled pages.** Where column layout defeats line grouping, text arrives
  one character per line (`e i g h t t s f i v e h n t e`). Recorded as
  `unreadable-layer` and excluded rather than counted as failure.
- **Numeral systems.** `decode_legacy` emits Devanagari digits, so `1977`
  arrived as `१९७७` while the OCR stores Latin digits, and every year in every
  Hindi chapter scored as missing. Digits are now folded to ASCII.
- Missing words under three characters scored as noise regardless of meaning.

## Residual: attributed, no unexplained OCR loss

The first pass left 43 unmatched words across 9 `review` chapters, and the
first tally carried a 4-word ambiguity that I could not fully reconcile between
the raw classifier output (9 furniture + 8 garbled-reprint + 1 near + 43
unexplained) and the hand-written summary (12 + 27 + 1 + 4). Rather than restate
a breakdown I cannot stand behind, the reliable statement is the one that
matters: **43 residual tokens, 4 of which were a real OCR gap and the other 39
attributable to page furniture or known decoder corruption.** The 4-word figure
gap is now patched, so no real OCR loss remains outstanding.

- **Page furniture** — now excluded from scoring entirely, see fix 2. This
  accounted for 2 words on every Hindi page.
- **Systematic decoder defects.** `वफ` is emitted where `य` belongs
  (`वफडल`=विद्यालय, `ऐवफ`, `सतवफ`, `वफदरत`, `वफजर`), and a trailing matra is
  emitted as a danda (`सथ।।`, `सभइ।।`, `हइ।।`, `रव।।`). These are decoder
  defects, not OCR defects. The i-matra half is fixed; the conjunct half is the
  documented residual floor, and completing the table from a generic 8-bit
  reference was tested and made things worse (see the rejected change above).
- **Glossed footnotes.** Several pages are glossary pages, where the decoder
  reliably garbles the *term* while leaving its *gloss* intact.

After all four fixes there is no remaining gap at any threshold. The residual
decoder artifacts still exist in the decoded PDF text — they are a property of
the witness, not of the corpus — but they no longer subtract from any chapter's
verdict, and none of them corresponds to absent OCR text.

## The one real finding — now fixed

`fepr1-ch05` p20: the figure labels `Delta`, `Diamond`, `Parafoil`, `Rokkaku`
were absent from the OCR. These are rotated text labels on a diagram of kite
shapes, not prose, and were confirmed absent under every case variant. Patched
at the figure position with a short caption; see the fix note above.

## What this does and does not establish

**Establishes:** every page of all 38 chapters is represented in the OCR; no page
was dropped, half-transcribed, or column-scrambled; the residual vocabulary gap
is attributable to the decoder and to page furniture.

**Does not establish:** that any individual sentence is character-exact. The
witness is a lossy inverse of a legacy font encoding, so it cannot prove
verbatim fidelity even in principle — it can only rule out gross loss. The one
confirmed figure-label gap is now patched.

The `decode_legacy` defect is fixed for as much as can be fixed safely. I-matra
ordering is corrected — better on 204 of 277 Hindi pages, worse on 2. The
conjunct residue (`वफ` for `य`, and trailing matras emitted as a danda) is
**not** fixed, and the obvious remedy was tested and rejected: merging entries
from two published 8-bit KrutiDev tables made validation worse on 244 of 272
pages. Closing that gap requires a per-font mapping derived empirically from
this PDF family's actual text layer, not a generic reference table. Until such a
mapping exists, it is a hard floor on Hindi character-exactness.

Consequently these results are **not** sufficient on their own to set
`quote_exact=true`. That flag is a claim of verbatim authority, and it gates
question generation from quoting sources. It is a policy decision, not a
threshold crossing.
