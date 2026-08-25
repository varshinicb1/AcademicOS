// Proves two things about the shared mastery-update helper that replaced
// two independently-duplicated copies of this arithmetic (found by a
// codebase audit): the blend math is correct, and the real behavioral
// divergence the audit caught between the two old copies -- one of them
// never assigned 'proficient' to a brand-new concept even at a high score --
// is actually fixed now that both call sites share one implementation.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/mastery_engine.dart';

void main() {
  group('updatedConceptMastery', () {
    test('a brand-new concept takes the observed score directly, no blending', () {
      final result = updatedConceptMastery(conceptId: 'c1', existing: null, observed: 0.9);
      expect(result['mastery'], 0.9);
      expect(result['evidenceCount'], 1);
    });

    test('regression: a brand-new concept scored >=0.8 is "proficient", not stuck at "developing"', () {
      // This is exactly the case the two old duplicated implementations
      // disagreed on: local_api_client.dart's copy special-cased new
      // concepts to only ever emit 'needsReview' or 'developing'.
      final result = updatedConceptMastery(conceptId: 'c1', existing: null, observed: 0.95);
      expect(result['status'], 'proficient');
      expect(result['isWeak'], isFalse);
    });

    test('an existing concept blends prior*0.7 + observed*0.3', () {
      final existing = {'mastery': 0.4, 'evidenceCount': 3};
      final result = updatedConceptMastery(conceptId: 'c1', existing: existing, observed: 1.0);
      expect(result['mastery'], closeTo(0.4 * 0.7 + 1.0 * 0.3, 1e-9));
      expect(result['evidenceCount'], 4);
    });

    test('status thresholds: <0.5 needsReview, <0.8 developing, else proficient', () {
      expect(updatedConceptMastery(conceptId: 'c', existing: null, observed: 0.3)['status'], 'needsReview');
      expect(updatedConceptMastery(conceptId: 'c', existing: null, observed: 0.6)['status'], 'developing');
      expect(updatedConceptMastery(conceptId: 'c', existing: null, observed: 0.85)['status'], 'proficient');
    });
  });
}
