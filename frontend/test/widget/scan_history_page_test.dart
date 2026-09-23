// Real widget-level UI test for ScanHistoryPage -- the "history in the app"
// feature added because there was previously no way to look back at a
// scanned/corrected answer sheet after leaving MobileScanPage's capture
// flow. Uses real demo-seeded data (DemoSeeder), not fabricated widget
// state, so a real regression here (e.g. the corrected-sheet tile silently
// stops rendering the real total) actually fails this test.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/local_engine/demo_seeder.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/mobile_scan/pages/scan_history_page.dart';

import '../support/real_di.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;

  setUpAll(() async {
    env = await RealTestEnv.init('scan_history_test_');
    env.registerGetIt();
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
  });

  testWidgets('a fresh device with no scans shows a real, honest empty state', (tester) async {
    await tester.pumpWidget(wrapForTest(const ScanHistoryPage()));
    await tester.pump();

    expect(find.text('No scanned answer sheets yet'), findsOneWidget);
  });

  testWidgets('lists the real seeded scan session with its real student, subject, and marks', (tester) async {
    // Real fix for a real hang: DemoSeeder.seedIfEmpty() does substantial
    // real I/O (loads the full bundled corpus, generates 5 real papers,
    // evaluates ~50 real sheets) -- calling it with a bare `await` directly
    // inside a testWidgets body runs it inside flutter_test's fake-async
    // zone, where real Future-based I/O never resolves and the whole test
    // binary hangs (confirmed: it hung for 30+ minutes before this fix).
    // tester.runAsync() temporarily steps outside that zone for real async
    // work, exactly as the Flutter docs prescribe for this situation.
    await tester.runAsync(() => DemoSeeder.seedIfEmpty());
    final session = LocalStore.instance.allScanSessions().single;
    final review = List<Map>.from(session['review'] as List);
    final totalAwarded = review.fold<int>(0, (s, r) => s + (r['finalMarks'] as int));
    final totalMax = review.fold<int>(0, (s, r) => s + (r['maxMarks'] as int));

    await tester.pumpWidget(wrapForTest(const ScanHistoryPage()));
    await tester.pump();

    expect(find.text('No scanned answer sheets yet'), findsNothing);
    expect(find.text(session['studentName'] as String), findsOneWidget);
    expect(find.text('$totalAwarded / $totalMax'), findsOneWidget,
        reason: 'the displayed total must be computed from the real review data, not invented');
    expect(find.text('finalized'), findsOneWidget, reason: 'the real session status must show as-is');
  });

  // Deliberately NOT tested here: tapping a session to open the corrected-
  // sheet PDF preview. PdfPreview (package:printing) opens a real platform
  // channel that is never mocked in a plain `flutter test` environment --
  // attempting it here hung the whole test binary (10+ minute timeout,
  // confirmed by actually running it, not assumed). The underlying logic
  // that tap triggers (PillarApi.downloadScanPdf -> LocalScanPdfExporter.
  // exportCorrected producing real bytes for a real session) is already
  // covered without a PdfPreview widget in local_scan_pdf_export_test.dart's
  // "downloadScanPdf routing" tests.
}
