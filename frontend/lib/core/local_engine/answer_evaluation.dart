/// Faithful Dart port of src/academicos/assessment/evaluate.py -- the
/// deterministic (no LLM, no network) marking-point/keyword evaluation
/// engine. This is the real scoring logic, not a simplified stand-in: every
/// mark still traces to a named marking point, confidence still gates
/// needsReview, MCQ vs descriptive still branch the same way.
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

final _wordPattern = RegExp(r'[A-Za-z][A-Za-z0-9\-]+');
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

  final hasAlnum = answer.split('').any((c) => RegExp(r'[a-zA-Z0-9]').hasMatch(c));
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
    return LocalEvaluation(
      questionId: question.id,
      awardedMarks: 0,
      maxMarks: maxMarks,
      verdict: 'partialCredit',
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
