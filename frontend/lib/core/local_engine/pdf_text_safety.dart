/// Shared sanitizer for every on-device PDF exporter (local_pdf_export.dart,
/// local_report_card_pdf_export.dart, local_scan_pdf_export.dart) -- was
/// duplicated three times as a private `_safe()` in each file. The `pdf`
/// package's base Helvetica font has no Unicode support, so typographic
/// punctuation and, per a real on-device screenshot of the new corrected-
/// sheet PDF, real subscript digits in the actual corpus text ("CuSO₄",
/// U+2084) silently render as tofu boxes -- confirmed by grepping the real
/// corpus for the exact codepoint, not guessed.
String pdfSafe(String text) {
  var out = text
      .replaceAll('—', '-')
      .replaceAll('–', '-')
      .replaceAll('•', '-')
      .replaceAll('‘', "'")
      .replaceAll('’', "'")
      .replaceAll('“', '"')
      .replaceAll('”', '"');
  // Subscript/superscript digits (U+2080-2089 subscript, U+00B2/00B3/00B9 +
  // U+2074-2079 superscript) -- map to plain digits rather than dropping
  // them, since the digit itself is real content (a real chemical formula's
  // subscript, a real exponent), just not renderable at this glyph.
  const subscripts = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
  };
  const superscripts = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
  };
  subscripts.forEach((k, v) => out = out.replaceAll(k, v));
  superscripts.forEach((k, v) => out = out.replaceAll(k, v));

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
    '∆': 'triangle ', // INCREMENT (U+2206), used for triangle notation in geometry proofs
    'Δ': 'triangle ', // GREEK CAPITAL LETTER DELTA (U+0394) -- visually identical,
    // a different codepoint, also real and present in the corpus.
    '∫': 'integral',
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
  return buffer.toString();
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
