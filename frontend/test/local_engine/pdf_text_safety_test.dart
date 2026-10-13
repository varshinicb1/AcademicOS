// Proves the real, on-device-confirmed bug this fixed: real corpus text
// with genuine Unicode subscript digits ("CuSO₄", confirmed present
// in assets/corpus/questions.json by grep) rendered as tofu boxes in the
// pdf package's base Helvetica font -- caught by eye on a real emulator
// screenshot of the new corrected-sheet PDF, not by static analysis.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/pdf_text_safety.dart';

void main() {
  test('real subscript digits from the actual corpus are mapped to plain digits', () {
    expect(pdfSafe('CuSO₄'), 'CuSO4');
    expect(pdfSafe('Na₂CO₃'), 'Na2CO3');
  });

  test('an exponent prints as an exponent, not a plain digit', () {
    // "4y³" printed "4y3" -- a different quantity (re-audit 2026-09-23,
    // cbe:q:Maths8BS2). A subscript stays a plain digit: H2O is how chemistry
    // is written in ASCII, and no subscript changes a value.
    expect(pdfSafe('x² + 4x'), 'x^2 + 4x');
    expect(pdfSafe('(A) 4y³ (B) 9y³'), '(A) 4y^3 (B) 9y^3');
    expect(pdfSafe('10⁻³'), '10^-3');
    expect(pdfSafe('H₂O and CO₂'), 'H2O and CO2');
  });

  test('existing typographic-punctuation normalization still holds', () {
    expect(pdfSafe('a — b ‘c’ “d” • e'), "a - b 'c' \"d\" - e");
  });

  test('plain ASCII text is left untouched', () {
    const plain = 'The ratio of total surface area is 2:1';
    expect(pdfSafe(plain), plain);
  });

  // Real gap found via an on-device screenshot of the demo corrected-sheet
  // PDF (a real seeded Mathematics marking scheme): several real math
  // symbols still rendered as tofu boxes even after the subscript fix.
  // Every codepoint below was confirmed present in the real bundled corpus
  // (assets/corpus/questions.json) by direct inspection -- U+2212 alone
  // appears 363 times in real Mathematics marking-point text -- not guessed.
  test('real math symbols from the actual corpus are mapped to a plain-ASCII reading', () {
    expect(pdfSafe('q − 0'), 'q - 0', reason: 'U+2212 MINUS SIGN, distinct from ASCII hyphen');
    expect(pdfSafe('√(x2 + y2)'), 'sqrt(x2 + y2)', reason: 'U+221A SQUARE ROOT');
    expect(pdfSafe('∴ Height = 25√3 m'), 'therefore Height = 25sqrt3 m');
    expect(pdfSafe('∠OAB = 60°'), 'angle OAB = 60°',
        reason: 'U+2220 ANGLE maps; the Latin-1 degree sign is left alone since Helvetica renders it fine');
    expect(pdfSafe('5q2 = p2 ⇒ p2 is divisible by 5'), '5q2 = p2 => p2 is divisible by 5');
    expect(pdfSafe('a ≠ 0 and p & q are coprime'), 'a != 0 and p & q are coprime');
    expect(pdfSafe('sin θ = opposite/hypotenuse'), 'sin theta = opposite/hypotenuse');
    expect(pdfSafe('Area = πr2'), 'Area = pir2');
    expect(pdfSafe('\u{2206}OAB is an equilateral triangle'), 'triangle OAB is an equilateral triangle',
        reason: 'U+2206 INCREMENT, the actual codepoint confirmed in the corpus -- visually '
            'identical to but a different codepoint from Greek capital Delta (U+0394), which is '
            'also real and present, and mapped the same way');
    expect(pdfSafe('\u{0394}x is small'), 'delta x is small',
        reason: 'U+0394 GREEK CAPITAL LETTER DELTA before a variable is "change in", not a triangle');
    expect(pdfSafe('Increase in Income (\u{0394}Y)'), 'Increase in Income (delta Y)',
        reason: 'an Economics stem in the served bank printed "triangle Y"');
    expect(pdfSafe('Energy released = \u{2206}m'), 'Energy released = delta m');
    expect(pdfSafe('\u{2206}\u{1D443}\u{1D446}\u{1D444} ~ \u{0394} ABC'), 'triangle PSQ ~ triangle ABC',
        reason: 'italic vertex letters are demathified before the triangle check');
    expect(pdfSafe('\u{2206}\u{1D438}\u{1D43C}\u{1D43C} > \u{2206}EIV'), 'delta EII > delta EIV',
        reason: 'Roman-numeral energy levels are not triangle vertices');
  });

  // Real gap found the same way: italic/bold math-alphabet variables
  // (Mathematical Alphanumeric Symbols block) are a DIFFERENT codepoint
  // from the plain letter -- 𝑥 (U+1D465) is not the same character as
  // ASCII 'x', so it silently tofu-boxed even though a plain "x" appears
  // right next to it in the same sentence. Confirmed real and common in
  // the corpus (155 occurrences of 𝑥 alone in Mathematics marking text).
  test('styled math-alphabet letters/digits are mapped back to plain ASCII', () {
    expect(pdfSafe('let \u{1D465} be a rational number'), 'let x be a rational number',
        reason: 'U+1D465 MATHEMATICAL ITALIC SMALL X');
    expect(pdfSafe('\u{1D468}\u{1D469}\u{1D46A} is a triangle'), 'ABC is a triangle',
        reason: 'U+1D468-1D46A MATHEMATICAL BOLD ITALIC CAPITAL A/B/C');
    expect(pdfSafe('area = \u{1D7D0} \u{1D7D1} sq. units'), 'area = 2 3 sq. units',
        reason: 'U+1D7D0/1D7D1 MATHEMATICAL BOLD DIGIT TWO/THREE');
  });

  // Real gap found via a direct character-frequency scan of the full bundled
  // corpus (assets/corpus/questions.json), not just the one demo sheet --
  // every codepoint below was counted as actually present, not guessed.
  test('rupee sign, ellipsis, and combining accents from the real corpus are handled', () {
    expect(pdfSafe('\u{20B9}500 at 10% p.a.'), 'Rs.500 at 10% p.a.',
        reason: 'U+20B9 INDIAN RUPEE SIGN -- 52 real occurrences, common in CBSE word problems');
    expect(pdfSafe('and so on\u{2026}'), 'and so on...', reason: 'U+2026 HORIZONTAL ELLIPSIS');
    expect(pdfSafe('unit vector v\u{0302}'), 'unit vector v',
        reason: 'U+0302 COMBINING CIRCUMFLEX ACCENT -- 98 real occurrences (e.g. "v\u{0302}" for a '
            'unit vector); dropped like the combining arrow above, keeping the base letter');
  });

  // Real gap found the same way: a confirmed OCR-extraction artifact, not
  // real Oriya text -- the source PDFs' superscript "2" (as in "cm²")
  // decodes as the Oriya letter SHA in the real corpus, 42 times, always
  // in the same area/volume-unit context. Mapped from the actual observed
  // substitution, not from the Unicode block's real (unrelated) meaning.
  test('the real Oriya-SHA OCR artifact for superscript 2 is corrected', () {
    expect(pdfSafe('60\u{221A}3 cm\u{0B36}'), '60sqrt3 cm2');
  });

  // Real gap found the same way: styled Greek letters (Mathematical Italic
  // Greek, a separate Unicode range from the Latin block _demathify()
  // already covers) still tofu-boxed. All three confirmed real in the
  // corpus.
  test('styled Greek math letters are mapped to their plain-ASCII names', () {
    expect(pdfSafe('sin \u{1D703} and cos \u{1D6FC} and \u{1D70B}r2'),
        'sin theta and cos alpha and pir2');
  });

  // Real gap found the same way: Private Use Area codepoints (U+F05C,
  // U+F044, U+F05E, U+F0DE all confirmed present) are leftover Wingdings/
  // Symbol-font glyph references from OCR, not real content -- genuinely
  // unmappable, so dropped rather than guessed at.
  test('zero-width characters are dropped, not printed as boxes', () {
    // The model-written Hindi questions (2026-10-14) carry U+200D to form half letters; Helvetica
    // has no Devanagari and prints the joiner itself as a box.
    expect(pdfSafe('a‍b‌c​d⁠e﻿f'), 'abcdef');
  });

  test('unmappable Private Use Area glyphs from OCR font substitution are dropped', () {
    expect(pdfSafe('stray glyph \u{F05C} here'), 'stray glyph  here');
  });

  // Task 121 review: the map was a sample, not a guard. The merge put two new
  // characters into the bundled corpus and only one of them was added here --
  // U+22C5 DOT OPERATOR (2 occurrences) was, U+03C1 GREEK SMALL LETTER RHO
  // (12) was not. That rho is cbe:q:Science9PS1's, the record the whole
  // symbol repair was built around: its options are "W rho g", "W rho / g",
  // "W g / rho", "W / rho g", and on the phone every rho printed as a box.
  test('the rho the symbol repair restores prints as a word, not a box', () {
    expect(pdfSafe('a body of weight W and density \u{03C1}'),
        'a body of weight W and density rho');
    expect(pdfSafe('(A) W \u{03C1} g (B) W \u{03C1} / g'), '(A) W rho g (B) W rho / g');
  });

  test('the Greek and arrow characters the corpus carries are readable', () {
    expect(pdfSafe('R1 = 20 \u{03A9}'), 'R1 = 20 Omega');
    expect(pdfSafe('2\u{03B1} + 50\u{00B0}'), '2alpha + 50°');
    expect(pdfSafe('\u{03BB} = 600 nm, \u{03C9}t'), 'lambda = 600 nm, omegat');
    expect(pdfSafe('Zn + CuSO4 \u{2192} ZnSO4 + Cu'), 'Zn + CuSO4 -> ZnSO4 + Cu');
    expect(pdfSafe('\u{2211}fi xi'), 'sumfi xi');
    expect(pdfSafe('\u{2220}A = 100\u{00B0}'), 'angle A = 100°');
    expect(pdfSafe('\u{0391}BC'), 'ABC',
        reason: 'GREEK CAPITAL ALPHA in the corpus is a mis-encoded vertex name');
  });

  // The guard the sample above could not be: every symbol character the real
  // bundled corpus holds, through pdfSafe, must come out Latin-1 -- that is
  // exactly what base Helvetica can draw, and anything else is a box. A
  // language paper written in its own script (the Assamese, Bhutia, Tibetan
  // and Persian SQPs) is a different problem, not a character table's: no
  // base font draws Bengali, Tibetan or Arabic and no ASCII reading replaces
  // them, so those blocks are out of scope here and named as such.
  const symbolBlocks = [
    [0x0370, 0x03FF], // Greek
    [0x02B0, 0x02FF], // spacing modifier letters (the ring-above degree)
    [0x2000, 0x206F], // general punctuation
    [0x2070, 0x209F], // super/subscripts
    [0x20A0, 0x20CF], // currency
    [0x20D0, 0x20FF], // combining marks for symbols
    [0x2100, 0x214F], // letterlike
    [0x2190, 0x21FF], // arrows
    [0x2200, 0x22FF], // mathematical operators
    [0x2300, 0x23FF], // miscellaneous technical
    [0x2500, 0x257F], // box drawing
    [0x25A0, 0x25FF], // geometric shapes
    [0x2600, 0x26FF], // miscellaneous symbols
    [0x27C0, 0x27EF], // miscellaneous mathematical A
    [0x2980, 0x29FF], // miscellaneous mathematical B
    [0x2A00, 0x2AFF], // supplemental mathematical operators
    [0x1D400, 0x1D7FF], // mathematical alphanumeric
    [0xE000, 0xF8FF], // private use (dropped, so it must come out empty)
    [0xFF01, 0xFF5E], // fullwidth forms
  ];

  bool isSymbol(int rune) =>
      symbolBlocks.any((b) => rune >= b[0] && rune <= b[1]);

  test('every symbol character in the real bundled corpus survives pdfSafe as Latin-1', () {
    final file = File('assets/corpus/questions.json');
    if (!file.existsSync()) {
      markTestSkipped('assets/corpus/questions.json not bundled');
      return;
    }
    final runes = <int>{};
    void walk(dynamic value) {
      if (value is String) {
        for (final r in value.runes) {
          if (isSymbol(r)) runes.add(r);
        }
      } else if (value is Map) {
        value.values.forEach(walk);
      } else if (value is List) {
        value.forEach(walk);
      }
    }

    walk(jsonDecode(file.readAsStringSync()));
    expect(runes, isNotEmpty, reason: 'the corpus should carry math symbols');
    final unprintable = <String>[];
    for (final rune in runes) {
      final ch = String.fromCharCode(rune);
      if (pdfSafe(ch).runes.any((r) => r > 0xFF)) {
        unprintable.add('U+${rune.toRadixString(16).toUpperCase()} $ch');
      }
    }
    expect(unprintable, isEmpty,
        reason: 'these print as tofu boxes in the pdf package base Helvetica');
  });

}
