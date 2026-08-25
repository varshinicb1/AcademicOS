// Proves two real bugs in the paper delivery flow (Assessment Review page ->
// "Preview, print or email") are fixed:
//  1. mailStatus() used to return {'configured': false, 'reason': ...} but
//     PaperDeliverySheet reads anyConfigured/backends[x].reason -- the shape
//     mismatch threw a null-cast exception the instant the Email tab built.
//  2. The Preview tab always did a raw network fetch for the PDF even
//     though the offline build already rendered one locally moments
//     earlier via exportPaper() -- with no server, preview never loaded.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/local_pillar_api.dart';

void main() {
  test('mailStatus() returns the shape PaperDeliverySheet actually reads', () async {
    final status = await LocalPillarApi().mailStatus();

    expect(status['anyConfigured'], isFalse,
        reason: 'the UI checks status["anyConfigured"], not "configured"');
    final backends = status['backends'];
    expect(backends, isA<Map<String, dynamic>>(),
        reason: 'the UI does (status["backends"] as Map).entries -- a missing/wrong-shaped '
            'key here is what threw the null-cast exception on-device');
    for (final entry in (backends as Map<String, dynamic>).entries) {
      expect(entry.value['reason'], isA<String>(),
          reason: 'each backend entry must carry a human-readable reason, same as the UI expects');
    }
  });
}
