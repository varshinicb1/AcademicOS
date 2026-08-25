import 'local_store.dart';

/// Recency-weighted mastery update shared by LocalPillarApi.evaluateSheet
/// (batch, one call per assessment) and LocalApiClient's single-question
/// evaluation path. Both used to independently reimplement this exact
/// arithmetic; found duplicated -- and silently diverged on one edge case
/// (the single-question path never assigned 'proficient' to a brand-new
/// concept scored >=0.8 on its first evaluation) -- by a codebase audit.
/// Single-sourcing it here means the blend weights/thresholds can only ever
/// disagree with themselves by construction.
///
/// Simple recency-weighted running average -- real FSRS retention math is a
/// further step, not attempted for this first on-device pass.
Map<String, dynamic> updatedConceptMastery({
  required String conceptId,
  required Map<String, dynamic>? existing,
  required double observed,
}) {
  final priorEvidence = (existing?['evidenceCount'] as num?)?.toInt() ?? 0;
  final priorMastery = (existing?['mastery'] as num?)?.toDouble() ?? 0.3;
  final newMastery = priorEvidence == 0 ? observed : (priorMastery * 0.7 + observed * 0.3);
  return {
    'conceptId': conceptId,
    'conceptName': conceptId,
    'mastery': newMastery,
    'retention': 0.9,
    'evidenceCount': priorEvidence + 1,
    'status': newMastery < 0.5 ? 'needsReview' : (newMastery < 0.8 ? 'developing' : 'proficient'),
    'isWeak': newMastery < 0.5,
  };
}

/// Persists the overall/weakConcepts rollup for a student's full concept
/// map, same shape both call sites previously duplicated by hand.
void saveMasteryRollup(String studentId, Iterable<Map<String, dynamic>> concepts) {
  final all = concepts.toList();
  final overall = all.isNotEmpty
      ? all.map((c) => (c['mastery'] as num).toDouble()).reduce((a, b) => a + b) / all.length
      : 0.0;
  LocalStore.instance.saveMastery(studentId, {
    'studentId': studentId,
    'overallMastery': overall,
    'concepts': all,
    'weakConcepts': all.where((c) => c['isWeak'] == true).map((c) => c['conceptName']).toList(),
  });
}
