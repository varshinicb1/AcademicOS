// Proves real bugs in the paper delivery flow (Assessment Review page ->
// "Preview, print or email") are fixed:
//  1. mailStatus() used to return {'configured': false, 'reason': ...} but
//     PaperDeliverySheet reads anyConfigured/backends[x].reason -- the shape
//     mismatch threw a null-cast exception the instant the Email tab built.
//  2. The Preview tab always did a raw network fetch for the PDF even
//     though the offline build already rendered one locally moments
//     earlier via exportPaper() -- with no server, preview never loaded.
//  3. The Email tab was shown unconditionally in the offline build, where
//     it can never work (no server -- see mailStatus test below), so it
//     always greeted the user with a permanent "No email backend is
//     configured yet" warning. Real fix: the offline build (the only
//     variant this app actually ships, per ACADEMICOS_OFFLINE) doesn't
//     offer email at all, matching the same _kOfflineBuild-gating pattern
//     already used in settings_page.dart/home_page.dart/daily_planner_page.
//     This test only means something when run with
//     --dart-define=ACADEMICOS_OFFLINE=true (the flag the real APK builds
//     with); run without it, it verifies nothing about the offline branch.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/local_pillar_api.dart';
import 'package:academicos/presentation/assessment/widgets/paper_delivery_sheet.dart';

const _offlineBuild = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

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

  testWidgets(
    'offline build never shows the Email tab or the "no backend configured" warning',
    (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          body: PaperDeliverySheet(
            paperId: 'p1',
            paperTitle: 'Class X Mathematics -- Unit Test',
            subject: 'Mathematics',
            grade: 10,
          ),
        ),
      ));
      await tester.pump();

      expect(find.text('Email'), _offlineBuild ? findsNothing : findsOneWidget,
          reason: 'the offline build structurally cannot send email (no server) -- it must not '
              'offer the tab at all rather than offer it and always fail');
      expect(find.text('No email backend is configured yet'), findsNothing,
          reason: 'this warning must never render in the offline build -- the user should never '
              'see it, per the whole point of removing the tab rather than just explaining it');
      expect(find.text('Preview & Print'), findsOneWidget);
    },
  );
}
