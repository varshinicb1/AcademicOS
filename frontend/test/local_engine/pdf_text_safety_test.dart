// Proves the real, on-device-confirmed bug this fixed: real corpus text
// with genuine Unicode subscript digits ("CuSO₄", confirmed present
// in assets/corpus/questions.json by grep) rendered as tofu boxes in the
// pdf package's base Helvetica font -- caught by eye on a real emulator
// screenshot of the new corrected-sheet PDF, not by static analysis.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/pdf_text_safety.dart';

void main() {
  test('real subscript digits from the actual corpus are mapped to plain digits', () {
    expect(pdfSafe('CuSO₄'), 'CuSO4');
    expect(pdfSafe('Na₂CO₃'), 'Na2CO3');
  });

  test('superscript digits (real exponents) are mapped to plain digits', () {
    expect(pdfSafe('x² + 4x'), 'x2 + 4x');
  });

  test('existing typographic-punctuation normalization still holds', () {
    expect(pdfSafe('a — b ‘c’ “d” • e'), "a - b 'c' \"d\" - e");
  });

  test('plain ASCII text is left untouched', () {
    const plain = 'The ratio of total surface area is 2:1';
    expect(pdfSafe(plain), plain);
  });
}
