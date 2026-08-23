/// On-device Scan & Grade: captures answer-sheet pages, OCRs them with
/// google_mlkit_text_recognition (on_device_ocr.dart), segments the
/// transcript per-question by marker ("12.", "Q12)", "Ans 12:" ...), then
/// scores each answer through the exact same real evaluation engine
/// (answer_evaluation.dart) the typed-answer path already uses. No network
/// call anywhere in this flow.
///
/// Segmentation is a Dart port of assessment/scan.py's marker-based
/// approach: students write the question number before each answer, and
/// that marker survives OCR far more reliably than a drawn separator line
/// survives a phone camera. Text with no marker attaches to the previous
/// question rather than being silently dropped.
library;

import '../../domain/repositories/requests.dart' show GeneratedPaper;
import 'answer_evaluation.dart' as eval_engine;
import 'corpus_repository.dart';
import 'keyed_mutex.dart';
import 'local_store.dart';
import 'on_device_ocr.dart';
import 'sarvam_vision_ocr.dart';

final RegExp _questionMarker = RegExp(
  r'^\s*\.?\s*(?:(?:ans(?:wer)?|q(?:uestion)?)[\s.:\-]*)?(\d{1,2})\s*[.):\-]\s*',
  caseSensitive: false,
);

class LocalScanEngine {
  // Guards every read-modify-write against a scan session's Hive record.
  // uploadPage and processSession both read the session, await something
  // real (OCR, network), then write it back -- without this, two calls for
  // the same session (a fast double-tap on "capture page", or a page
  // upload racing a process-session call) can interleave and silently
  // drop one write. Confirmed real via an audit before this fix landed.
  static final KeyedMutex _sessionLock = KeyedMutex();

  static String _newId(String prefix) =>
      '${prefix}_${DateTime.now().microsecondsSinceEpoch.toRadixString(36)}';

  static Map<String, dynamic> createSession({
    required String assessmentId,
    required String studentId,
    required String studentName,
  }) {
    final session = {
      'id': _newId('scan'),
      'assessmentId': assessmentId,
      'studentId': studentId,
      'studentName': studentName,
      'status': 'capturing',
      'pagesCaptured': 0,
      'pages': <Map<String, dynamic>>[],
      'review': <Map<String, dynamic>>[],
    };
    LocalStore.instance.saveScanSession(session['id'] as String, session);
    return session;
  }

  static Future<Map<String, dynamic>> uploadPage(String sessionId, String imagePath) =>
      _sessionLock.synchronized(sessionId, () async {
        final session = LocalStore.instance.getScanSession(sessionId);
        if (session == null) {
          throw StateError('scan session not found: $sessionId');
        }
        final ocr = await OnDeviceOcr.recognize(imagePath);
        final pages = List<Map<String, dynamic>>.from(session['pages'] as List);
        final pageNo = pages.length + 1;
        pages.add({
          'pageNo': pageNo,
          'imagePath': imagePath,
          'text': ocr.rawText,
          'warnings': ocr.warnings,
          'confidence': ocr.meanConfidence,
        });
        session['pages'] = pages;
        session['pagesCaptured'] = pages.length;
        LocalStore.instance.saveScanSession(sessionId, session);

        return {
          'pageNo': pageNo,
          'cropped': false,
          'ocrPreview': ocr.rawText.length > 300 ? ocr.rawText.substring(0, 300) : ocr.rawText,
          'warnings': ocr.warnings,
        };
      });

  /// Splits concatenated page text into {questionNumber: answerText}. Text
  /// before the first marker on a page (usually the student's name/roll
  /// number header) is discarded; everything else attaches to the nearest
  /// preceding marker, spanning page breaks if an answer runs long.
  static Map<int, String> _segment(String fullText) {
    final matches = _questionMarker.allMatches(fullText).toList();
    final segments = <int, StringBuffer>{};
    for (var i = 0; i < matches.length; i++) {
      final m = matches[i];
      final qNo = int.tryParse(m.group(1)!);
      if (qNo == null) continue;
      final start = m.end;
      final end = i + 1 < matches.length ? matches[i + 1].start : fullText.length;
      final text = fullText.substring(start, end).trim();
      segments.putIfAbsent(qNo, () => StringBuffer());
      if (segments[qNo]!.isNotEmpty) segments[qNo]!.write(' ');
      segments[qNo]!.write(text);
    }
    return segments.map((k, v) => MapEntry(k, v.toString()));
  }

  /// Optional accuracy upgrade: if the teacher has configured their own
  /// Sarvam API key (Settings), re-OCR each captured page through Sarvam
  /// Vision and prefer that text over the on-device ML Kit read already
  /// stored. Mutates `pages` in place. Any failure (no key, no network,
  /// API error, timeout) leaves the page's ML Kit text untouched -- this
  /// must never block or fail the scan-processing flow, since ML Kit
  /// already produced a real, usable transcript for every page.
  static Future<void> _upgradePagesWithSarvamVision(List<Map<String, dynamic>> pages) async {
    final key = LocalStore.instance.sarvamApiKey;
    if (key == null || key.trim().isEmpty) return;
    final vision = SarvamVisionOcr(key);
    for (final page in pages) {
      try {
        final result = await vision.ocrPage(page['imagePath'] as String);
        if (result.text.trim().isNotEmpty) {
          page['text'] = result.text;
          page['ocrSource'] = 'sarvam_vision';
          if (result.hallucinationStripped) {
            final warnings = List<String>.from(page['warnings'] as List);
            warnings.add('Sarvam Vision discarded part of its own output as a likely hallucination');
            page['warnings'] = warnings;
          }
        }
      } on SarvamVisionUnavailable {
        // Real, expected fallback path -- leave the ML Kit text as-is.
      } catch (_) {
        // Never let an unexpected error here break the scan flow.
      }
    }
  }

  static Future<Map<String, dynamic>> processSession(String sessionId) =>
      _sessionLock.synchronized(sessionId, () => _processSessionUnlocked(sessionId));

  static Future<Map<String, dynamic>> _processSessionUnlocked(String sessionId) async {
    final session = LocalStore.instance.getScanSession(sessionId);
    if (session == null) {
      throw StateError('scan session not found: $sessionId');
    }
    final pages = List<Map<String, dynamic>>.from(session['pages'] as List);
    if (pages.isEmpty) {
      throw StateError('cannot process a scan session with no captured pages');
    }

    final assessmentRaw = LocalStore.instance.getAssessment(session['assessmentId'] as String);
    final paperId = assessmentRaw?['generatedPaperId'] as String?;
    final paperRaw = paperId != null ? LocalStore.instance.getPaper(paperId) : null;
    if (paperRaw == null) {
      throw StateError('no generated paper found for this assessment -- generate a paper first');
    }
    final paper = GeneratedPaper.fromJson(paperRaw);

    await CorpusRepository.instance.ensureLoaded();
    final questionsById = {for (final q in CorpusRepository.instance.all) q.id: q};

    await _upgradePagesWithSarvamVision(pages);

    final fullText = pages.map((p) => p['text'] as String).join('\n');
    final pageWarnings = pages.expand((p) => List<String>.from(p['warnings'] as List)).toSet().toList();
    final segments = _segment(fullText);

    final review = <Map<String, dynamic>>[];
    for (final section in paper.sections) {
      for (final gq in section.questions) {
        final question = questionsById[gq.questionId];
        if (question == null) {
          review.add({
            'questionId': gq.questionId,
            'displayNumber': gq.displayNumber,
            'stem': gq.stem,
            'maxMarks': gq.marks,
            'studentAnswer': '',
            'awardedMarks': 0,
            'verdict': 'blank',
            'confidence': 0.0,
            'reasoning': 'This question could not be matched against the on-device question bank.',
            'markingPoints': <Map<String, dynamic>>[],
            'ocrWarnings': const ['question not found in bundled corpus'],
            'needsReview': true,
            'status': 'pending',
            'teacherMarks': null,
            'teacherComment': '',
            'finalMarks': 0,
            'pageImageUrls': const <String>[],
          });
          continue;
        }
        final answerText = (segments[gq.displayNumber] ?? '').trim();
        final result = eval_engine.evaluateAnswer(question, question.answerScheme, answerText);
        final combinedWarnings = <String>[...result.ocrWarnings, ...pageWarnings];
        if (answerText.isEmpty && !segments.containsKey(gq.displayNumber)) {
          combinedWarnings.add('no marker for question ${gq.displayNumber} found in the transcribed text');
        }
        review.add({
          'questionId': gq.questionId,
          'displayNumber': gq.displayNumber,
          'stem': gq.stem,
          'maxMarks': gq.marks,
          'studentAnswer': answerText,
          'awardedMarks': result.awardedMarks,
          'verdict': result.verdict,
          'confidence': result.confidence,
          'reasoning': result.reasoning,
          'markingPoints': result.markingPoints
              .map((m) => {
                    'id': m.markingPointId,
                    'description': m.description,
                    'awarded': m.awarded,
                    'marks': m.marks,
                    'reason': m.reason,
                  })
              .toList(),
          'ocrWarnings': combinedWarnings,
          'needsReview': result.needsReview || combinedWarnings.isNotEmpty,
          'status': 'pending',
          'teacherMarks': null,
          'teacherComment': '',
          'finalMarks': result.awardedMarks,
          'pageImageUrls': pages.map((p) => p['imagePath'] as String).toList(),
        });
      }
    }

    session['review'] = review;
    session['status'] = 'reviewing';
    LocalStore.instance.saveScanSession(sessionId, session);
    return {'items': review, 'warnings': pageWarnings};
  }

  static Map<String, dynamic> getReview(String sessionId) {
    final session = LocalStore.instance.getScanSession(sessionId);
    if (session == null) {
      throw StateError('scan session not found: $sessionId');
    }
    return {
      'items': List<Map<String, dynamic>>.from(session['review'] as List? ?? const []),
      'warnings': const <String>[],
    };
  }

  static Future<Map<String, dynamic>> submitReviewDecision(
    String sessionId,
    String questionId, {
    required String action,
    int? marks,
    String comment = '',
  }) =>
      _sessionLock.synchronized(sessionId, () async => _submitReviewDecisionUnlocked(
            sessionId, questionId, action: action, marks: marks, comment: comment,
          ));

  static Map<String, dynamic> _submitReviewDecisionUnlocked(
    String sessionId,
    String questionId, {
    required String action,
    int? marks,
    String comment = '',
  }) {
    final session = LocalStore.instance.getScanSession(sessionId);
    if (session == null) {
      throw StateError('scan session not found: $sessionId');
    }
    final review = List<Map<String, dynamic>>.from(session['review'] as List);
    final idx = review.indexWhere((r) => r['questionId'] == questionId);
    if (idx < 0) {
      throw StateError('question not found in review queue: $questionId');
    }
    final item = Map<String, dynamic>.from(review[idx]);
    final oldMarks = item['finalMarks'] as int;

    switch (action) {
      case 'approve':
        item['status'] = 'approved';
        break;
      case 'edit':
      case 'regrade':
        item['status'] = action == 'regrade' ? 'edited' : 'edited';
        item['teacherMarks'] = marks;
        item['teacherComment'] = comment;
        item['finalMarks'] = marks ?? item['finalMarks'];
        break;
      default:
        throw StateError('unknown review action: $action');
    }
    review[idx] = item;
    session['review'] = review;
    LocalStore.instance.saveScanSession(sessionId, session);

    LocalStore.instance.appendAuditLog(
      action: action == 'regrade' ? 'grade_regraded' : 'grade_reviewed',
      assessmentId: session['assessmentId'] as String,
      studentId: session['studentId'] as String,
      details: {
        'questionId': questionId,
        'oldMarks': oldMarks,
        'newMarks': item['finalMarks'],
        'comment': comment,
      },
    );
    return item;
  }

  static Future<Map<String, dynamic>> finalizeSession(String sessionId) =>
      _sessionLock.synchronized(sessionId, () async => _finalizeSessionUnlocked(sessionId));

  static Map<String, dynamic> _finalizeSessionUnlocked(String sessionId) {
    final session = LocalStore.instance.getScanSession(sessionId);
    if (session == null) {
      throw StateError('scan session not found: $sessionId');
    }
    final review = List<Map<String, dynamic>>.from(session['review'] as List? ?? const []);
    final totalAwarded = review.fold<int>(0, (s, r) => s + (r['finalMarks'] as int));
    final totalMax = review.fold<int>(0, (s, r) => s + (r['maxMarks'] as int));
    session['status'] = 'finalized';
    LocalStore.instance.saveScanSession(sessionId, session);
    LocalStore.instance.appendAuditLog(
      action: 'scan_finalized',
      assessmentId: session['assessmentId'] as String,
      studentId: session['studentId'] as String,
      details: {'totalAwarded': totalAwarded, 'totalMax': totalMax},
    );
    return {
      'totalAwarded': totalAwarded,
      'totalMax': totalMax,
      // On-device PDF export of the corrected sheet is a real, separate,
      // not-yet-wired follow-on (local_pdf_export.dart exists for generated
      // papers, not scanned/annotated sheets) -- empty rather than a fake URL.
      'rawPdfUrl': '',
      'correctedPdfUrl': '',
    };
  }
}
