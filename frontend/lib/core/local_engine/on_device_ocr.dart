/// Real on-device OCR for the offline build's Scan & Grade path, backed by
/// Google ML Kit's on-device text recognizer (Android only). No network
/// call per scan -- the model is bundled/cached locally by Play Services
/// the first time text recognition runs on the device, then reused offline
/// from then on. This replaces the earlier hard "Scan & Grade needs an
/// internet connection" limitation for the standalone Android build.
library;

import 'dart:io';

import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

class OcrResult {
  final String rawText;
  final double meanConfidence;
  final List<String> warnings;
  OcrResult({required this.rawText, required this.meanConfidence, required this.warnings});
}

class OnDeviceOcr {
  static TextRecognizer? _recognizer;

  static TextRecognizer get _instance =>
      _recognizer ??= TextRecognizer(script: TextRecognitionScript.latin);

  /// Runs real on-device text recognition over a captured page image.
  /// meanConfidence is a coverage heuristic (ML Kit doesn't expose a
  /// per-block confidence score the way a cloud OCR API does): the fraction
  /// of recognized lines that are not single stray characters/noise, which
  /// tracks well with genuinely legible vs. blurry/blank captures in
  /// practice. A real page with real handwriting produces many multi-word
  /// lines; a blank or badly-lit page produces mostly 1-2 character noise.
  static Future<OcrResult> recognize(String imagePath) async {
    final warnings = <String>[];
    final file = File(imagePath);
    if (!await file.exists()) {
      return OcrResult(rawText: '', meanConfidence: 0.0, warnings: ['image file not found']);
    }

    final inputImage = InputImage.fromFilePath(imagePath);
    final RecognizedText recognized;
    try {
      recognized = await _instance.processImage(inputImage);
    } catch (e) {
      return OcrResult(rawText: '', meanConfidence: 0.0, warnings: ['OCR failed: $e']);
    }

    final lines = <String>[];
    var legibleLines = 0;
    for (final block in recognized.blocks) {
      for (final line in block.lines) {
        final text = line.text.trim();
        if (text.isEmpty) continue;
        lines.add(text);
        final wordCount = text.split(RegExp(r'\s+')).length;
        if (text.length >= 3 && wordCount >= 1) legibleLines++;
      }
    }

    final rawText = lines.join('\n');
    if (lines.isEmpty) {
      warnings.add('no text detected -- page may be blank or the photo is too blurry/dark');
      return OcrResult(rawText: '', meanConfidence: 0.1, warnings: warnings);
    }

    final coverage = legibleLines / lines.length;
    if (coverage < 0.5) {
      warnings.add('low OCR confidence -- recapture with better lighting/focus if the score looks wrong');
    }
    // Calibrated conservatively below cloud-OCR-typical confidence: ML Kit's
    // Latin recognizer is trained mainly on printed text, so real cursive
    // handwriting genuinely reads with more noise than a clean scan -- this
    // number feeds straight into needsReview via the same reviewThreshold
    // every other evaluation confidence uses, so under-trusting it here is
    // the safe direction, not a cosmetic tweak.
    final confidence = (0.55 + coverage * 0.35).clamp(0.1, 0.9);

    return OcrResult(rawText: rawText, meanConfidence: confidence, warnings: warnings);
  }

  static Future<void> dispose() async {
    await _recognizer?.close();
    _recognizer = null;
  }
}
