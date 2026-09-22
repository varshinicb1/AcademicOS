/// Dart port of src/academicos/assessment/evaluate.py -- the
/// deterministic (no LLM, no network) marking-point/keyword evaluation
/// engine. This is the real scoring logic, not a simplified stand-in: every
/// mark still traces to a named marking point, confidence still gates
/// needsReview, MCQ vs descriptive still branch the same way. Keep the two
/// in step: a scheme with no marking points, or only keyword-less ones, must
/// go to review in both engines (tests/test_assessment_evaluate.py and
/// test/local_engine/answer_evaluation_unscorable_test.dart pin each side).
///
/// llm_evaluate.py's richer natural-language grading (the version used for
/// the real handwritten-booklet proof earlier) genuinely needs a cloud LLM
/// call and is NOT ported here -- that stays an optional, cloud-backed path
/// with the user's own key, same pattern as OCR. This is the on-device
/// default.
library;

import '../../domain/entities/entities.dart';

const reviewThreshold = 0.75;
const descriptiveMinChars = 8;

// Unicode letters, not [A-Za-z]: 213 bundled questions (measured 2026-09-22)
// carry a Devanagari keyword on a marking point, and an ASCII-only tokeniser
// drops every Devanagari word from the answer, so those points could never be
// awarded. \p{M} keeps the vowel signs and virama inside a word ('प्रबल' is
// प + ् + र + ब + ल); without it each word would split at every matra. On
// ASCII text this matches exactly what the old pattern did. evaluate.py's
// _WORD is still ASCII-only; Python keyword matching is not on the phone's path.
final _wordPattern = RegExp(r'\p{L}[\p{L}\p{M}\p{N}\-]+', unicode: true);
// Python's str.isalnum(): any Unicode letter or digit. See evaluateAnswer.
final _alnumPattern = RegExp(r'[\p{L}\p{N}]', unicode: true);
final _fusedNumberPattern = RegExp(r'\b\d{5,}\b');
final _optionAnswerPattern = RegExp(r'\b(?:OPTION\s*)?\(?([A-D])\)?\b');
const _blankPhrases = {
  'not attempted', 'no answer', 'blank', 'skipped', 'n/a', 'na', '-', 'none',
};

class MarkingPointOutcome {
  final String markingPointId;
  final String description;
  final bool awarded;
  final int marks;
  final String reason;
  final double similarity;
  MarkingPointOutcome({
    required this.markingPointId,
    required this.description,
    required this.awarded,
    required this.marks,
    required this.reason,
    required this.similarity,
  });
}

class LocalEvaluation {
  final String questionId;
  final int awardedMarks;
  final int maxMarks;
  final String verdict; // fullCredit | partialCredit | noCredit | blank
  final double confidence;
  final String reasoning;
  final List<MarkingPointOutcome> markingPoints;
  final List<String> strengths;
  final List<String> gaps;
  final List<String> ocrWarnings;
  final bool needsReview;

  LocalEvaluation({
    required this.questionId,
    required this.awardedMarks,
    required this.maxMarks,
    required this.verdict,
    required this.confidence,
    required this.reasoning,
    this.markingPoints = const [],
    this.strengths = const [],
    this.gaps = const [],
    this.ocrWarnings = const [],
    required this.needsReview,
  });

  double get percentage => maxMarks > 0 ? (100.0 * awardedMarks / maxMarks) : 0.0;
}

List<String> ocrRiskFlags(String answer) {
  final flags = <String>[];
  if (_fusedNumberPattern.hasMatch(answer)) {
    flags.add('possible struck-through working merged into one number '
        '(cancellations are not reliably transcribed)');
  }
  if ('?'.allMatches(answer).length > 2) {
    flags.add('multiple unresolved characters in transcription');
  }
  // Python: `letters = [c for c in answer if c.isalpha()]`. Dart has no
  // built-in per-rune isAlpha, so approximate with the Unicode letter
  // category via a regex (covers Latin + the Devanagari/other-script runs
  // this check exists to catch).
  final letterPattern = RegExp(r'\p{L}', unicode: true);
  final letters = answer.runes.map(String.fromCharCode).where((c) => letterPattern.hasMatch(c)).toList();
  if (letters.isNotEmpty) {
    final nonAscii = letters.where((c) => c.codeUnitAt(0) > 0x2FF).length;
    if (nonAscii / letters.length > 0.3) {
      flags.add('mixed-script transcription; may be mis-segmented');
    }
  }
  return flags;
}

Set<String> _normalise(String text) =>
    _wordPattern.allMatches(text).map((m) => m.group(0)!.toLowerCase()).toSet();

MarkingPointOutcome _matchPoint(MarkingPoint point, Set<String> answerWords, String answerLow) {
  final candidates = [point.keyword, ...point.synonyms];
  var best = 0.0;
  var hit = '';
  for (final cand in candidates) {
    final c = cand.trim().toLowerCase();
    if (c.isEmpty) continue;
    double score;
    if (c.contains(' ')) {
      score = answerLow.contains(c) ? 1.0 : 0.0;
    } else {
      score = answerWords.contains(c) ? 1.0 : 0.0;
    }
    if (score > best) {
      best = score;
      hit = c;
    }
  }
  final awarded = best >= 1.0;
  return MarkingPointOutcome(
    markingPointId: point.id,
    description: point.description,
    awarded: awarded,
    marks: awarded ? point.marks : 0,
    reason: awarded ? "found '$hit' in the answer" : "no mention of '${point.keyword}' or its variants",
    similarity: best,
  );
}

LocalEvaluation evaluateAnswer(Question question, AnswerScheme scheme, String studentAnswer,
    {String? conceptLabel}) {
  final answer = studentAnswer.trim();
  final maxMarks = scheme.totalMarks != 0 ? scheme.totalMarks : (question.marks != 0 ? question.marks : 1);
  final ocrFlags = ocrRiskFlags(answer);
  final objective = scheme.metadata['objective'] == true;

  // evaluate.py uses `any(c.isalnum() for c in answer)`. This used to be
  // [a-zA-Z0-9], so an answer written only in Devanagari took this path: 0
  // marks at 0.95 confidence, no review. 149 bundled rows have a model answer
  // with no ASCII letter or digit (measured 2026-09-22, e.g.
  // cbse:q:src:de9d7a7a1c777974c1dd9138:13); written out by a student, each
  // scored 'blank'.
  final hasAlnum = _alnumPattern.hasMatch(answer);
  final stripped = answer.replaceAll(RegExp(r'^[ .]+|[ .]+$'), '').toLowerCase();
  if (!hasAlnum || _blankPhrases.contains(stripped)) {
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'blank',
      confidence: 0.95,
      reasoning: 'No answer written for this question.',
      ocrWarnings: ocrFlags,
      needsReview: false,
    );
  }

  if (objective) {
    return _evaluateObjective(question, scheme, answer, maxMarks, ocrFlags);
  }

  if (answer.length < descriptiveMinChars) {
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'noCredit',
      confidence: 0.4,
      reasoning: 'Answer is too short to assess against the marking scheme.',
      ocrWarnings: ocrFlags,
      needsReview: true,
    );
  }

  if (scheme.markingPoints.isEmpty) {
    // Mirrors evaluate.py's C4 branch. With no points, outcomes is empty, so
    // matched=0, totalPoints=1, ratio=0 and the confidence formula gives 0.9:
    // 0 marks, noCredit, no review. The bundled corpus has 345 descriptive
    // board-paper rows (grades 10 and 12) with markingPoints=[] and an empty
    // modelAnswer (measured 2026-09-22), and paper_selection.dart does not
    // filter them out, so they reach Scan & Grade.
    // Verdict 'noCredit', not 'partialCredit': the review UI shows the verdict
    // as a label, and "Partial Credit" on 0/N reads as a marking error. The 0.0
    // confidence and needsReview carry the "unscored" signal.
    final model = scheme.modelAnswer.trim();
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'noCredit',
      confidence: 0.0,
      reasoning: 'This question has no marking scheme (no marking points) to '
          'score against — it cannot be graded automatically; a teacher '
          'must mark it manually.'
          '${model.isEmpty ? '' : " Model answer: '$model'."}',
      ocrWarnings: ocrFlags,
      needsReview: true,
    );
  }

  return _evaluateDescriptive(question, scheme, answer, maxMarks, ocrFlags);
}

LocalEvaluation _evaluateObjective(
    Question question, AnswerScheme scheme, String answer, int maxMarks, List<String> ocrFlags) {
  final key = (scheme.metadata['correctOption']?.toString() ?? '').toUpperCase();
  var chosen = '';
  var ambiguous = false;
  // First-seen order, de-duplicated -- keep the first-mentioned letter (the
  // genuine selection consistently comes first in real CBSE scan data;
  // "prefer last" measured worse), but when MULTIPLE DISTINCT letters
  // appear the pick is inherently uncertain and must not be trusted at
  // full confidence -- see evaluate.py's _evaluate_objective for the real
  // wrong-mark bug this fixes.
  final distinct = <String>[];
  for (final m in _optionAnswerPattern.allMatches(answer.toUpperCase())) {
    final letter = m.group(1)!;
    if (!distinct.contains(letter)) distinct.add(letter);
  }
  if (distinct.isNotEmpty) {
    chosen = distinct.first;
    ambiguous = distinct.length > 1;
  }

  if (key.isEmpty) {
    // 0 marks, so 'noCredit' (see the no-marking-points branch in evaluateAnswer).
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'noCredit',
      confidence: 0.0,
      reasoning: 'No correct option recorded in the marking scheme — teacher must set the key.',
      ocrWarnings: ocrFlags,
      needsReview: true,
    );
  }
  if (chosen.isEmpty) {
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'noCredit',
      confidence: 0.45,
      reasoning: 'Could not identify which option the student selected.',
      ocrWarnings: ocrFlags,
      needsReview: true,
    );
  }

  final correct = chosen == key;
  var confidence = ocrFlags.isEmpty ? 0.93 : 0.6;
  if (ambiguous) {
    // Below reviewThreshold (0.75) so needsReview below picks it up through
    // the same mechanism as every other uncertain read.
    confidence = confidence < 0.5 ? confidence : 0.5;
  }
  final point = scheme.markingPoints.isNotEmpty ? scheme.markingPoints.first : null;
  final outcomes = <MarkingPointOutcome>[];
  if (point != null) {
    outcomes.add(MarkingPointOutcome(
      markingPointId: point.id,
      description: point.description,
      awarded: correct,
      marks: correct ? maxMarks : 0,
      reason: 'student selected $chosen; key is $key',
      similarity: correct ? 1.0 : 0.0,
    ));
  }
  var reasoning = correct
      ? 'Selected option $chosen, which matches the key.'
      : 'Selected option $chosen; the correct option is $key.';
  if (ambiguous) {
    reasoning += ' Multiple option letters appeared in the transcribed answer '
        '(${distinct.join(", ")}) — $chosen was taken as the final selection, '
        'but this is uncertain and needs a human check.';
  }
  return LocalEvaluation(
    questionId: question.id,
    awardedMarks: correct ? maxMarks : 0,
    maxMarks: maxMarks,
    verdict: correct ? 'fullCredit' : 'noCredit',
    confidence: confidence,
    reasoning: reasoning,
    markingPoints: outcomes,
    strengths: correct && point != null ? [point.description] : [],
    gaps: correct ? [] : ['Correct option was $key'],
    ocrWarnings: ocrFlags,
    needsReview: confidence < reviewThreshold,
  );
}

LocalEvaluation _evaluateDescriptive(
    Question question, AnswerScheme scheme, String answer, int maxMarks, List<String> ocrFlags) {
  final words = _normalise(answer);
  final low = answer.toLowerCase();
  final outcomes = scheme.markingPoints.map((p) => _matchPoint(p, words, low)).toList();
  var awarded = outcomes.fold<int>(0, (sum, o) => sum + o.marks);
  awarded = awarded > maxMarks ? maxMarks : awarded;

  String verdict;
  if (awarded >= maxMarks) {
    verdict = 'fullCredit';
  } else if (awarded > 0) {
    verdict = 'partialCredit';
  } else {
    verdict = 'noCredit';
  }

  // A marking point whose keyword and synonyms are all empty cannot be matched
  // against anything, so "not awarded" says nothing about the answer. CBE and
  // SQP schemes carry the official value point as a description only, and so
  // do 1,248 of the 2,544 descriptive board-paper questions in the bundled
  // corpus (measured 2026-09-22). The confidence formula below gives a total
  // miss the same 0.9 as a full match, so such a scheme used to report 0 marks
  // at 0.9 confidence with no review flag. Treat it as unscorable and hand it
  // to the teacher instead. The verdict stays 'noCredit' because verdicts are
  // parsed into EvaluationVerdict, which has no review value; needsReview and
  // the low confidence carry the signal.
  // evaluateAnswer has already returned for an empty markingPoints list, so
  // `every` here is never vacuously true.
  final unscorable = scheme.markingPoints.every((p) =>
      p.keyword.trim().isEmpty && p.synonyms.every((s) => s.trim().isEmpty));
  if (unscorable) {
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'noCredit',
      confidence: 0.2,
      reasoning: 'The marking scheme has no keywords to match, so this answer '
          'could not be scored automatically. Mark it by hand against the '
          "official value point: '${scheme.markingPoints.first.description}'.",
      // Fresh outcomes rather than _matchPoint's: its miss reason would read
      // "no mention of '' or its variants" once per point in the review UI,
      // which blames the answer for a gap in the scheme.
      markingPoints: [
        for (final p in scheme.markingPoints)
          MarkingPointOutcome(
            markingPointId: p.id,
            description: p.description,
            awarded: false,
            marks: 0,
            reason: 'no keyword in the scheme; mark by hand',
            similarity: 0.0,
          ),
      ],
      ocrWarnings: ocrFlags,
      needsReview: true,
    );
  }

  final matched = outcomes.where((o) => o.awarded).length;
  final totalPoints = outcomes.isNotEmpty ? outcomes.length : 1;
  final ratio = matched / totalPoints;
  var confidence = 0.9 - 0.5 * (1 - (2 * ratio - 1).abs());
  if (answer.length < 25) confidence -= 0.1;
  if (ocrFlags.isNotEmpty) confidence -= 0.25;
  confidence = confidence.clamp(0.05, 0.95);
  confidence = double.parse(confidence.toStringAsFixed(2));

  return LocalEvaluation(
    questionId: question.id,
    awardedMarks: awarded,
    maxMarks: maxMarks,
    verdict: verdict,
    confidence: confidence,
    reasoning: _reason(outcomes, awarded, maxMarks),
    markingPoints: outcomes,
    strengths: outcomes.where((o) => o.awarded).map((o) => o.description).toList(),
    gaps: outcomes.where((o) => !o.awarded).map((o) => o.description).toList(),
    ocrWarnings: ocrFlags,
    needsReview: confidence < reviewThreshold || ocrFlags.isNotEmpty,
  );
}

String _reason(List<MarkingPointOutcome> outcomes, int awarded, int maxMarks) {
  final missing = outcomes.where((o) => !o.awarded).map((o) => o.description).toList();
  if (missing.isEmpty) {
    return 'All marking points addressed ($awarded/$maxMarks).';
  }
  if (awarded == 0) {
    return 'None of the expected marking points were found: '
        '${missing.take(3).join("; ")}.';
  }
  return '$awarded/$maxMarks. Missing: ${missing.take(3).join("; ")}.';
}
