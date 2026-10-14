/// Shared sanitizer for every on-device PDF exporter (local_pdf_export.dart,
/// local_report_card_pdf_export.dart, local_scan_pdf_export.dart) -- was
/// duplicated three times as a private `_safe()` in each file. The `pdf`
/// package's base Helvetica font has no Unicode support, so typographic
/// punctuation and, per a real on-device screenshot of the new corrected-
/// sheet PDF, real subscript digits in the actual corpus text ("CuSO₄",
/// U+2084) silently render as tofu boxes -- confirmed by grepping the real
/// corpus for the exact codepoint, not guessed.
String pdfSafe(String text) {
  // Zero-width characters (space, non-joiner, joiner, word joiner, BOM) are
  // invisible, and Helvetica prints each as a box. Hindi text carries the
  // joiner to form half letters (the model-written Hindi 9-10 questions of
  // 2026-10-14); with no Devanagari font here there is nothing for it to join.
  // The web renderer (assessment/pdf.py) draws with a Unicode font and keeps it.
  var out = text
      .replaceAll(RegExp('[​-‍⁠﻿]'), '')
      // A thin space and the IPA length mark, both from the NCERT textbook
      // questions (2026-10-14): "1 0 kg", a phonics answer's "/uː/".
      .replaceAll(' ', ' ')
      .replaceAll('ː', ':')
      .replaceAll('—', '-')
      .replaceAll('–', '-')
      .replaceAll('•', '-')
      .replaceAll('‘', "'")
      .replaceAll('’', "'")
      .replaceAll('“', '"')
      .replaceAll('”', '"');
  // Subscripts (U+2080-2089) become plain digits: a subscript names a thing --
  // H2O, a1 -- and never changes a value, so the ASCII spelling in everyday
  // use reads correctly.
  const subscripts = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
  };
  subscripts.forEach((k, v) => out = out.replaceAll(k, v));
  // A superscript is an exponent, and a plain digit is a DIFFERENT quantity:
  // cbe:q:Maths8BS2's options are "(A) 4y³ (B) 9y³ (C) 13y³ (D) 36y³" and
  // printed "4y3, 9y3 ..." -- the question itself, gone (re-audit 2026-09-23).
  // The caret goes in front of the whole run, so "10⁻³" is "10^-3", not
  // "10^-^3". Mirrors assessment/pdf.py's `_exponent`; the two must agree,
  // because the same paper prints through either.
  const superscripts = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
    '⁺': '+', '⁻': '-', '⁼': '=', '⁽': '(', '⁾': ')', 'ⁿ': 'n',
  };
  out = out.replaceAllMapped(
    RegExp('[${superscripts.keys.join()}]+'),
    (m) => '^${m.group(0)!.split('').map((c) => superscripts[c]!).join()}',
  );

  // Real math symbols found by direct inspection of the bundled corpus's
  // own marking-point/model-answer text (assets/corpus/questions.json,
  // Mathematics subject) -- counted real occurrences, not guessed: U+2212
  // MINUS SIGN alone appears 363 times, U+221A SQUARE ROOT 201 times,
  // U+2234 THEREFORE 127 times, U+03B8 THETA 112 times, and so on. Every
  // one of these renders as a tofu box in Helvetica; mapped to a plain-
  // ASCII reading rather than dropped, since the symbol is real content in
  // a real CBSE marking scheme (e.g. "q ≠ 0" must still say "q != 0", not
  // silently lose the condition).
  const mathSymbols = {
    '−': '-', // MINUS SIGN (U+2212) -- distinct codepoint from ASCII hyphen
    '√': 'sqrt', // SQUARE ROOT
    '∴': 'therefore',
    '∵': 'because',
    '∠': 'angle ',
    '⇒': '=>',
    '⟹': '=>',
    '≠': '!=',
    '≥': '>=',
    '≤': '<=',
    '∈': 'in',
    '∞': 'infinity',
    // ∆ (U+2206) and Δ (U+0394) are NOT here: whether one means "triangle"
    // or "change in" depends on what follows, so they are mapped below,
    // after _demathify has turned italic vertex letters back into ASCII.
    '∫': 'integral',
    '⋅': '·', // DOT OPERATOR (U+22C5) -- restored from a symbol font by the
    // merge (corpus/symbol_font.py) and drawn by no bundled font, while
    // MIDDLE DOT (U+00B7) draws the same mark and is Latin-1. The mark is
    // kept rather than read: the papers use it for a decimal point
    // ("2⋅4 g/litre") as well as for a product.
    '′': "'", // PRIME (e.g. A' in geometry)
    'θ': 'theta',
    'π': 'pi',
    '⃗': '', // COMBINING RIGHT ARROW ABOVE (vector notation) -- drop the
    // combining decoration, keep the base letter it was attached to.
    '̂': '', // COMBINING CIRCUMFLEX ACCENT (U+0302, e.g. a unit vector "v̂"
    // or angle notation "Â") -- 98 real occurrences in the corpus, same
    // drop-the-decoration treatment as the combining arrow above.
    '₹': 'Rs.', // INDIAN RUPEE SIGN (U+20B9) -- real, common in CBSE
    // Mathematics word problems ("₹500 at 10% p.a."); 52 occurrences.
    '…': '...', // HORIZONTAL ELLIPSIS (U+2026)
    'ଶ': '2', // ORIYA LETTER SHA (U+0B36) -- not real Oriya text; a
    // confirmed OCR-extraction artifact that stands in for a superscript
    // "2" in the source PDFs (directly observed in the real corpus as
    // "𝑐𝑚ଶ" where a human reader would see "cm²"). 42 occurrences, all in
    // the Mathematics subject alongside other area/volume-unit questions.
    '𝛼': 'alpha', // MATHEMATICAL ITALIC SMALL ALPHA (U+1D6FC) -- the
    '𝜃': 'theta', // MATHEMATICAL ITALIC SMALL THETA (U+1D703) -- and
    '𝜋': 'pi', // MATHEMATICAL ITALIC SMALL PI (U+1D70B) -- three real,
    // styled-Greek variants found in the corpus, outside the Latin-only
    // Mathematical Alphanumeric range _demathify() covers below.
    // Every remaining character the bundled corpus holds that base Helvetica
    // cannot draw, plus every value of the Adobe Symbol table the merge's
    // repair can restore (src/academicos/corpus/symbol_font.py). Counted on
    // assets/corpus/questions.json, not guessed: U+2192 RIGHTWARDS ARROW 388
    // times, U+03A9 OMEGA 48 (Science 10's resistors), U+03C1 RHO 12 -- the
    // rho of cbe:q:Science9PS1, whose options "W rho g / W rho / g / W g /
    // rho / W / rho g" are the whole reason the symbol repair exists and
    // which printed four boxes here until this line. The repair can emit any
    // of the table's 95 non-Latin-1 values the day a source uses that code,
    // so the table is covered whole rather than sampled.
    //
    // This is where the port diverges from pdf_safe() in
    // src/academicos/assessment/pdf.py, and why: that renderer registers a
    // real Unicode font (Segoe UI, Arial or DejaVu) and keeps the glyphs it
    // draws -- a web paper prints a real rho. The pdf package here has only
    // its base Helvetica, which is Latin-1 and nothing else, so every one of
    // these has to be spelled out. Greek capitals that are letter-for-letter
    // a Latin capital (Alpha, Beta, Epsilon, ... ) read as that letter: in
    // the corpus they are a mis-encoded vertex name, "angle A = 100 degrees"
    // (exemplar:q:7:mathematics:6:-:40), not the Greek letter.
    '∀': 'for all ', // FOR ALL
    '∃': 'there exists ', // THERE EXISTS
    '∋': 'contains', // CONTAINS AS MEMBER
    '∗': '*', // ASTERISK OPERATOR
    '≅': 'congruent', // APPROXIMATELY EQUAL TO
    'Α': 'A', // GREEK CAPITAL LETTER ALPHA
    'Β': 'B', // GREEK CAPITAL LETTER BETA
    'Ε': 'E', // GREEK CAPITAL LETTER EPSILON
    'Φ': 'Phi', // GREEK CAPITAL LETTER PHI
    'Γ': 'Gamma', // GREEK CAPITAL LETTER GAMMA
    'Η': 'H', // GREEK CAPITAL LETTER ETA
    'Ι': 'I', // GREEK CAPITAL LETTER IOTA
    'ϑ': 'theta', // GREEK THETA SYMBOL
    'Κ': 'K', // GREEK CAPITAL LETTER KAPPA
    'Λ': 'Lambda', // GREEK CAPITAL LETTER LAMDA
    'Μ': 'M', // GREEK CAPITAL LETTER MU
    'Ν': 'N', // GREEK CAPITAL LETTER NU
    'Ο': 'O', // GREEK CAPITAL LETTER OMICRON
    'Π': 'Pi', // GREEK CAPITAL LETTER PI
    'Θ': 'Theta', // GREEK CAPITAL LETTER THETA
    'Ρ': 'P', // GREEK CAPITAL LETTER RHO
    'Σ': 'Sigma', // GREEK CAPITAL LETTER SIGMA
    'Τ': 'T', // GREEK CAPITAL LETTER TAU
    'Υ': 'Y', // GREEK CAPITAL LETTER UPSILON
    'ς': 'sigma', // GREEK SMALL LETTER FINAL SIGMA
    'Ω': 'Omega', // GREEK CAPITAL LETTER OMEGA
    'Ξ': 'Xi', // GREEK CAPITAL LETTER XI
    'Ψ': 'Psi', // GREEK CAPITAL LETTER PSI
    'Ζ': 'Z', // GREEK CAPITAL LETTER ZETA
    '⊥': 'perpendicular', // UP TACK
    'α': 'alpha', // GREEK SMALL LETTER ALPHA
    'β': 'beta', // GREEK SMALL LETTER BETA
    'χ': 'chi', // GREEK SMALL LETTER CHI
    'δ': 'delta', // GREEK SMALL LETTER DELTA
    'ε': 'epsilon', // GREEK SMALL LETTER EPSILON
    'φ': 'phi', // GREEK SMALL LETTER PHI
    'γ': 'gamma', // GREEK SMALL LETTER GAMMA
    'η': 'eta', // GREEK SMALL LETTER ETA
    'ι': 'iota', // GREEK SMALL LETTER IOTA
    'ϕ': 'phi', // GREEK PHI SYMBOL
    'κ': 'kappa', // GREEK SMALL LETTER KAPPA
    'λ': 'lambda', // GREEK SMALL LETTER LAMDA
    'μ': 'mu', // GREEK SMALL LETTER MU
    'ν': 'nu', // GREEK SMALL LETTER NU
    'ο': 'o', // GREEK SMALL LETTER OMICRON
    'ρ': 'rho', // GREEK SMALL LETTER RHO
    'σ': 'sigma', // GREEK SMALL LETTER SIGMA
    'τ': 'tau', // GREEK SMALL LETTER TAU
    'υ': 'upsilon', // GREEK SMALL LETTER UPSILON
    'ω': 'omega', // GREEK SMALL LETTER OMEGA
    'ξ': 'xi', // GREEK SMALL LETTER XI
    'ψ': 'psi', // GREEK SMALL LETTER PSI
    'ζ': 'zeta', // GREEK SMALL LETTER ZETA
    '∼': '~', // TILDE OPERATOR
    '€': 'EUR', // EURO SIGN
    'ϒ': 'Y', // GREEK UPSILON WITH HOOK SYMBOL
    '⁄': '/', // FRACTION SLASH
    'ƒ': 'f', // LATIN SMALL LETTER F WITH HOOK
    '↔': '<->', // LEFT RIGHT ARROW
    '←': '<-', // LEFTWARDS ARROW
    '↑': 'up', // UPWARDS ARROW
    '→': '->', // RIGHTWARDS ARROW
    '↓': 'down', // DOWNWARDS ARROW
    '″': '"', // DOUBLE PRIME
    '∝': 'proportional to', // PROPORTIONAL TO
    '∂': 'd', // PARTIAL DIFFERENTIAL
    '≡': '==', // IDENTICAL TO
    '≈': '~=', // ALMOST EQUAL TO
    '↵': '', // DOWNWARDS ARROW WITH CORNER LEFTWARDS
    'ℵ': 'aleph', // ALEF SYMBOL
    'ℑ': 'Im', // BLACK-LETTER CAPITAL I
    'ℜ': 'Re', // BLACK-LETTER CAPITAL R
    '℘': 'P', // SCRIPT CAPITAL P
    '⊗': '(x)', // CIRCLED TIMES
    '⊕': '(+)', // CIRCLED PLUS
    '∅': 'empty set', // EMPTY SET
    '∩': 'intersection', // INTERSECTION
    '∪': 'union', // UNION
    '⊃': 'superset of', // SUPERSET OF
    '⊇': 'superset of or equal to', // SUPERSET OF OR EQUAL TO
    '⊄': 'not a subset of', // NOT A SUBSET OF
    '⊂': 'subset of', // SUBSET OF
    '⊆': 'subset of or equal to', // SUBSET OF OR EQUAL TO
    '∉': 'not in', // NOT AN ELEMENT OF
    '∇': 'nabla', // NABLA
    '∏': 'product', // N-ARY PRODUCT
    '∧': 'and', // LOGICAL AND
    '∨': 'or', // LOGICAL OR
    '⇔': '<=>', // LEFT RIGHT DOUBLE ARROW
    '⇐': '<==', // LEFTWARDS DOUBLE ARROW
    '⇑': 'up', // UPWARDS DOUBLE ARROW
    '⇓': 'down', // DOWNWARDS DOUBLE ARROW
    '\u{2329}': '<', // LEFT-POINTING ANGLE BRACKET
    '∑': 'sum', // N-ARY SUMMATION
    '\u{232A}': '>', // RIGHT-POINTING ANGLE BRACKET
    '⁻': '-', // SUPERSCRIPT MINUS
    '\u{1D6E5}': '\u{0394}', // MATHEMATICAL ITALIC CAPITAL DELTA
    'ℎ': 'h', // PLANCK CONSTANT
    '∘': '°', // RING OPERATOR
    '⁺': '+', // SUPERSCRIPT PLUS SIGN
    '\u{1D6FD}': 'beta', // MATHEMATICAL ITALIC SMALL BETA
    '●': '-', // BLACK CIRCLE
    '\u{1D700}': 'epsilon', // MATHEMATICAL ITALIC SMALL EPSILON
    '△': 'triangle ', // WHITE UP-POINTING TRIANGLE
    '\u{1D707}': 'mu', // MATHEMATICAL ITALIC SMALL MU
    'ⁿ': 'n', // SUPERSCRIPT LATIN SMALL LETTER N
    '∥': '||', // PARALLEL TO
    '⩭': 'congruent', // CONGRUENT WITH DOT ABOVE
    '‟': '"', // DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    'ₙ': 'n', // LATIN SUBSCRIPT SMALL LETTER N
    '\u{1D6F4}': 'Sigma', // MATHEMATICAL ITALIC CAPITAL SIGMA
    '\u{1D70E}': 'sigma', // MATHEMATICAL ITALIC SMALL SIGMA
    '„': '"', // DOUBLE LOW-9 QUOTATION MARK
    '\u{1D714}': 'omega', // MATHEMATICAL ITALIC SMALL OMEGA
    '∜': '4th root ', // FOURTH ROOT
    '∛': 'cbrt', // CUBE ROOT
    '∶': ':', // RATIO
    '║': '||', // BOX DRAWINGS DOUBLE VERTICAL
    '⟘': 'perpendicular', // LARGE UP TACK
    '\u{1D745}': 'pi', // MATHEMATICAL BOLD ITALIC SMALL PI
    'ₖ': 'k', // LATIN SUBSCRIPT SMALL LETTER K
    '˚': '°', // RING ABOVE
    '（': '(', // FULLWIDTH LEFT PARENTHESIS
    '）': ')', // FULLWIDTH RIGHT PARENTHESIS
    '～': '~', // FULLWIDTH TILDE
    '土': '±', // CJK UNIFIED IDEOGRAPH-571F
  };
  mathSymbols.forEach((k, v) => out = out.replaceAll(k, v));

  // Private Use Area codepoints (U+E000-U+F8FF) -- real, found in the
  // corpus (e.g. U+F05C, U+F044, U+F05E, U+F0DE), but genuinely unmappable:
  // PUA has no defined meaning by design, and these are leftover symbol-font
  // glyph references (Wingdings/Symbol-style) from the source PDFs' font
  // substitution during OCR, not real content. Dropped rather than guessed,
  // since a wrong ASCII guess would misrepresent real marking-scheme text.
  out = out.replaceAll(RegExp('[-]'), '');

  // Mathematical Alphanumeric Symbols block (U+1D400-U+1D7FF) -- real,
  // common in the corpus (e.g. italic 𝑥, 𝑦, 𝑖, bold-italic 𝑨, 𝑫, bold
  // digit 𝟐): these are purely STYLISTIC Unicode variants of plain Latin
  // letters/digits (italic/bold/script/etc. "x" is a different codepoint
  // from plain "x"), each style block a contiguous run of 26 capitals then
  // 26 lowercase (Unicode 9.0 "Mathematical Alphanumeric Symbols"). Mapped
  // back to the plain letter algorithmically -- more robust than hardcoding
  // the dozen-odd variants actually observed, since any other styled
  // variant in this well-defined block maps the same way.
  final runes = out.runes.toList();
  final buffer = StringBuffer();
  for (final rune in runes) {
    buffer.write(String.fromCharCode(_demathify(rune) ?? rune));
  }

  // ∆ INCREMENT (U+2206) and Δ GREEK CAPITAL DELTA (U+0394), visually
  // identical and both real in the corpus. Geometry writes a triangle as
  // "∆ABC", but Economics, Physics and Chemistry use the same glyph for
  // "change in": "Increase in Income (ΔY)", "Energy released = ∆m x 931.5
  // MeV", "∆E_I > ∆E_II". Mapping every delta to "triangle" printed
  // "triangle Y". So "triangle" only before a three-capital vertex name that
  // is not an energy-level subscript (EII, EIV); everything else is "delta".
  // Kept identical to pdf_safe() in src/academicos/assessment/pdf.py.
  return buffer
      .toString()
      .replaceAll(RegExp(r'[∆Δ] ?(?=(?!E[IVX]{2}\b)[A-Z]{3}(?![A-Za-z]))'), 'triangle ')
      .replaceAll(RegExp(r'[∆Δ] ?'), 'delta ');
}

int? _demathify(int rune) {
  const letterBlockStarts = [
    0x1D400, // Bold
    0x1D434, // Italic
    0x1D468, // Bold Italic
    0x1D49C, // Script
    0x1D4D0, // Bold Script
    0x1D504, // Fraktur
    0x1D538, // Double-struck
    0x1D56C, // Bold Fraktur
    0x1D5A0, // Sans-serif
    0x1D5D4, // Sans-serif bold
    0x1D608, // Sans-serif italic
    0x1D63C, // Sans-serif bold italic
    0x1D670, // Monospace
  ];
  for (final start in letterBlockStarts) {
    final offset = rune - start;
    if (offset >= 0 && offset < 52) {
      return offset < 26 ? 0x41 + offset : 0x61 + (offset - 26);
    }
  }
  // Bold/Double-struck/Sans-serif/Sans-serif-bold/Monospace digits: five
  // contiguous 10-digit runs starting at U+1D7CE.
  if (rune >= 0x1D7CE && rune <= 0x1D7FF) {
    return 0x30 + ((rune - 0x1D7CE) % 10);
  }
  return null;
}
