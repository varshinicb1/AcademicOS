# Per-page alignment of OCR text against source PDFs

Each readable page's character 4-gram content is matched against the whole OCR text. A chapter is judged by its WORST page, so one garbled page cannot hide in an average.

The manifest language governs decoding. A Hindi page is decoded only when decoding raises its Devanagari density; an English page is never decoded, because a single stray `KrutiDev010` or `Chanakya` font otherwise gets transliterated into gibberish and scored against the OCR. Pages shredded into one character per line by column detection are recorded as `unreadable-layer` and excluded.

Thresholds: worst page >= 0.75 is `verified`, 0.6-0.75 is `review`, below 0.6 is `page-failure`.

| chapter | pages | scored | skipped | worst page | mean | below | warn | verdict |
|---|---|---|---|---|---|---|---|---|
| aejm1-ch13 | 11 | 7 | 4 | 0.7935 | 0.8809 | 0 | 0 | verified |
| fegp1-ch10 | 56 | 27 | 29 | 0.788 | 0.9096 | 0 | 0 | verified |
| fepr1-ch05 | 34 | 33 | 1 | 0.8166 | 0.9378 | 0 | 0 | verified |
| gecu1-ch12 | 20 | 19 | 1 | 0.8959 | 0.9436 | 0 | 0 | verified |
| gegp1-ch04 | 41 | 30 | 11 | 0.83 | 0.9376 | 0 | 0 | verified |
| gepr1-ch02 | 48 | 48 | 0 | 0.8712 | 0.9558 | 0 | 0 | verified |
| jhkr1-ch01 | 9 | 8 | 1 | 0.6866 | 0.7962 | 0 | 1 | review |
| jhkr1-ch02 | 14 | 14 | 0 | 0.7106 | 0.7999 | 0 | 2 | review |
| jhkr1-ch03 | 5 | 5 | 0 | 0.6785 | 0.7497 | 0 | 3 | review |
| jhks1-ch01 | 9 | 8 | 1 | 0.4614 | 0.6985 | 2 | 3 | page-failure |
| jhks1-ch02 | 7 | 7 | 0 | 0.6912 | 0.774 | 0 | 1 | review |
| jhks1-ch03 | 5 | 5 | 0 | 0.5976 | 0.7154 | 1 | 2 | page-failure |
| jhks1-ch04 | 6 | 6 | 0 | 0.5952 | 0.685 | 1 | 4 | page-failure |
| jhks1-ch05 | 7 | 7 | 0 | 0.5965 | 0.7292 | 1 | 4 | page-failure |
| jhks1-ch06 | 8 | 7 | 1 | 0.6601 | 0.7799 | 0 | 2 | review |
| jhks1-ch07 | 9 | 9 | 0 | 0.7034 | 0.7835 | 0 | 2 | review |
| jhks1-ch08 | 9 | 9 | 0 | 0.6489 | 0.7629 | 0 | 3 | review |
| jhks1-ch09 | 6 | 6 | 0 | 0.4669 | 0.7376 | 1 | 0 | page-failure |
| jhks1-ch10 | 12 | 12 | 0 | 0.7625 | 0.8136 | 0 | 0 | verified |
| jhks1-ch11 | 12 | 11 | 1 | 0.5142 | 0.7491 | 1 | 4 | page-failure |
| jhks1-ch12 | 8 | 7 | 1 | 0.528 | 0.7311 | 1 | 2 | page-failure |
| jhsp1-ch01 | 7 | 5 | 2 | 0.5652 | 0.6606 | 2 | 3 | page-failure |
| jhsp1-ch02 | 5 | 5 | 0 | 0.6181 | 0.7379 | 0 | 3 | review |
| jhsp1-ch03 | 7 | 6 | 1 | 0.5736 | 0.7112 | 1 | 3 | page-failure |
| jhsp1-ch04 | 6 | 6 | 0 | 0.5899 | 0.714 | 1 | 3 | page-failure |
| jhsp1-ch05 | 5 | 5 | 0 | 0.6804 | 0.794 | 0 | 2 | review |
| jhsp1-ch06 | 5 | 5 | 0 | 0.5622 | 0.705 | 1 | 2 | page-failure |
| jhsp1-ch07 | 5 | 5 | 0 | 0.6018 | 0.7199 | 0 | 3 | review |
| jhsp1-ch08 | 17 | 16 | 1 | 0.4915 | 0.7539 | 2 | 4 | page-failure |
| jhsp1-ch09 | 9 | 9 | 0 | 0.5905 | 0.7402 | 1 | 3 | page-failure |
| jhsp1-ch10 | 12 | 12 | 0 | 0.5457 | 0.7636 | 1 | 3 | page-failure |
| jhsp1-ch11 | 10 | 10 | 0 | 0.4669 | 0.6636 | 2 | 5 | page-failure |
| jhsp1-ch12 | 8 | 8 | 0 | 0.6883 | 0.7806 | 0 | 2 | review |
| jhsp1-ch13 | 10 | 9 | 1 | 0.6327 | 0.7535 | 0 | 5 | review |
| jhsp1-ch14 | 10 | 10 | 0 | 0.4182 | 0.6814 | 1 | 6 | page-failure |
| jhsy1-ch01 | 19 | 18 | 1 | 0.7643 | 0.8484 | 0 | 0 | verified |
| jhsy1-ch02 | 12 | 11 | 1 | 0.7438 | 0.8136 | 0 | 2 | review |
| jhsy1-ch03 | 13 | 11 | 2 | 0.7193 | 0.798 | 0 | 2 | review |

Tally: {'verified': 8, 'review': 14, 'page-failure': 16}
