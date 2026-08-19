/// Faithful Dart port of src/academicos/assessment/selection.py --
/// deterministic, rule-based question selection. No LLM in this path on the
/// Python side either (see the module docstring there); porting it exactly
/// means the on-device paper generator produces the same kind of result the
/// live API does, not an approximation.
library;

import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';

// (label, name, marksPerQuestion, shareOfTotalMarks, allowedDifficulties)
const _layout = [
  ('A', 'MCQ', 1, 0.25, [Difficulty.easy, Difficulty.medium]),
  ('B', 'Very Short Answer', 2, 0.20, [Difficulty.easy, Difficulty.medium]),
  ('C', 'Short Answer', 3, 0.25, [Difficulty.medium, Difficulty.hard]),
  ('D', 'Long Answer', 5, 0.20, [Difficulty.medium, Difficulty.hard]),
  ('E', 'Case Study', 4, 0.10, [Difficulty.medium, Difficulty.hard]),
];

/// Port of templates.py's default_sections() -- scales the standard CBSE
/// A(MCQ)->B->C->D->E layout proportionally to the blueprint's total marks.
List<SectionBlueprint> defaultSections(int totalMarks) {
  final sections = <SectionBlueprint>[];
  var allocated = 0;
  for (var i = 0; i < _layout.length; i++) {
    final (label, name, marksPerQ, share, difficulties) = _layout[i];
    final isLast = i == _layout.length - 1;
    var sectionMarks = isLast ? (totalMarks - allocated) : (totalMarks * share).round();
    sectionMarks = sectionMarks < 0 ? 0 : sectionMarks;
    final count = sectionMarks > 0 ? (sectionMarks / marksPerQ).round().clamp(1, 1 << 30) : 0;
    if (count == 0) continue;
    final actualMarks = count * marksPerQ;
    allocated += actualMarks;
    sections.add(SectionBlueprint(
      id: 'section-${label.toLowerCase()}',
      label: label,
      name: name,
      marksPerQuestion: marksPerQ,
      questionCount: count,
      totalMarks: actualMarks,
      allowedBloomLevels: const [],
      allowedDifficulties: difficulties,
      hasInternalChoice: label == 'D' || label == 'E',
      internalChoiceCount: (label == 'D' || label == 'E') ? 1 : 0,
    ));
  }
  return sections;
}

double _score(Question q, Map<String, double> chapterWeights, Map<String, int> usedChapters) {
  var score = q.qualityScore;
  if (chapterWeights.isNotEmpty) {
    for (final cid in q.chapterIds) {
      score += (chapterWeights[cid] ?? 0.0) * 0.5;
    }
  }
  for (final cid in q.chapterIds) {
    score -= 0.05 * (usedChapters[cid] ?? 0);
  }
  return score;
}

bool _fitsSection(Question q, SectionBlueprint section) {
  if (q.marks != section.marksPerQuestion) return false;
  if (section.allowedDifficulties.isNotEmpty &&
      !section.allowedDifficulties.contains(q.difficulty)) {
    return false;
  }
  if (section.allowedBloomLevels.isNotEmpty &&
      !section.allowedBloomLevels.contains(q.bloomLevel)) {
    return false;
  }
  return true;
}

/// Port of selection.py's optimize(): greedily fills each section from
/// `candidates` (ranked by quality + chapter-weight match), and -- the fix
/// for the real "0-question paper" bug found earlier -- backfills any
/// section a narrow chapter pick can't fill from `fallbackCandidates`
/// (the wider subject+grade pool), clearly flagged in `gaps` either way.
QuestionOptimizationResult optimize(
  List<Question> candidates,
  Blueprint blueprint, {
  List<Question>? fallbackCandidates,
}) {
  final sections = blueprint.sections.isNotEmpty ? blueprint.sections : defaultSections(blueprint.totalMarks);
  final chapterWeights = blueprint.chapterWeights.weights;

  final remaining = List<Question>.from(candidates);
  final seenIds = candidates.map((q) => q.id).toSet();
  final fallbackRemaining =
      (fallbackCandidates ?? const <Question>[]).where((q) => !seenIds.contains(q.id)).toList();
  final selected = <Question>[];
  final usedChapters = <String, int>{};
  final warnings = <String>[];
  final gaps = <String>[];

  for (final section in sections) {
    var pool = remaining.where((q) => _fitsSection(q, section)).toList();
    final shortfall = section.questionCount - pool.length;
    if (shortfall > 0) {
      gaps.add(
        'Section ${section.label} (${section.name}): needs ${section.questionCount} '
        'questions worth ${section.marksPerQuestion} marks each, only ${pool.length} '
        'available in the selected chapters.',
      );
      final extra = fallbackRemaining.where((q) => _fitsSection(q, section)).toList()
        ..sort((a, b) => _score(b, chapterWeights, usedChapters)
            .compareTo(_score(a, chapterWeights, usedChapters)));
      if (extra.isNotEmpty) {
        final borrowed = extra.take(shortfall).toList();
        pool = [...pool, ...borrowed];
        gaps.add(
          'Section ${section.label}: filled ${borrowed.length} of the shortfall from '
          'outside the selected chapters so the section isn\'t left blank.',
        );
      }
    }
    pool.sort((a, b) =>
        _score(b, chapterWeights, usedChapters).compareTo(_score(a, chapterWeights, usedChapters)));
    final take = pool.take(section.questionCount).toList();
    for (final q in take) {
      selected.add(q);
      remaining.removeWhere((r) => r.id == q.id);
      fallbackRemaining.removeWhere((r) => r.id == q.id);
      for (final cid in q.chapterIds) {
        usedChapters[cid] = (usedChapters[cid] ?? 0) + 1;
      }
    }
  }

  final selectedIds = selected.map((q) => q.id).toSet();
  final rejected = candidates.where((q) => !selectedIds.contains(q.id)).toList();

  final chapterCoverage = <String, int>{};
  final bloomHist = <String, int>{};
  final difficultyHist = <String, int>{};
  for (final q in selected) {
    for (final cid in q.chapterIds) {
      chapterCoverage[cid] = (chapterCoverage[cid] ?? 0) + 1;
    }
    bloomHist[q.bloomLevel.name] = (bloomHist[q.bloomLevel.name] ?? 0) + 1;
    difficultyHist[q.difficulty.name] = (difficultyHist[q.difficulty.name] ?? 0) + 1;
  }

  if (selected.isNotEmpty) {
    final distinctChapters = chapterCoverage.length;
    if (distinctChapters == 1 && selected.length > 3) {
      warnings.add('Selected paper is concentrated in a single chapter — weak coverage.');
    }
  }
  final totalMarksSelected = selected.fold<int>(0, (sum, q) => sum + q.marks);
  if (totalMarksSelected != blueprint.totalMarks) {
    warnings.add(
      'Selected paper totals $totalMarksSelected marks, blueprint target is ${blueprint.totalMarks}.',
    );
  }

  return QuestionOptimizationResult(
    selectedQuestions: selected,
    rejectedQuestions: rejected,
    optimizationMetrics: {
      'totalMarksSelected': totalMarksSelected,
      'questionCount': selected.length,
      'chapterCoverage': chapterCoverage,
      'bloomDistribution': bloomHist,
      'difficultyDistribution': difficultyHist,
    },
    warnings: warnings,
    gaps: gaps,
  );
}
