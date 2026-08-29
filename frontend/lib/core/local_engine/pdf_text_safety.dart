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
  return out;
}
