// The privacy policy says what the school product does (audit 2026-10-04). It described the old
// offline app -- "nothing is uploaded anywhere" -- while the web product keeps everything on a server,
// and its rights section never said that nothing deletes data automatically.
import 'package:academicos/presentation/settings/pages/legal_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<String> privacyText(WidgetTester tester) async {
  tester.view.physicalSize = const Size(900, 9000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(const MaterialApp(home: LegalPage(doc: 'privacy')));
  return tester.widgetList<Text>(find.byType(Text)).map((t) => t.data ?? '').join('\n');
}

void main() {
  testWidgets('it says where the data is and who else receives it', (tester) async {
    final t = await privacyText(tester);
    expect(t, contains('Google Cloud in Mumbai'));
    expect(t, contains('Sarvam AI'));
    expect(t, contains('Groq'));
    expect(t, contains('unpkg.com'));
    expect(t, contains('each studentʼs progress'));
  });

  testWidgets('it does not promise deletion on a schedule, and says nothing deletes automatically', (tester) async {
    final t = await privacyText(tester);
    expect(t, contains('does not delete data automatically'));
    for (final promised in ['deleted after', 'automatically deleted', 'after one year', 'retention period of']) {
      expect(t.toLowerCase(), isNot(contains(promised)), reason: promised);
    }
  });

  testWidgets('it no longer claims what is false for the school product', (tester) async {
    final t = await privacyText(tester);
    expect(t, isNot(contains('Nothing is uploaded anywhere unless you explicitly')));
    expect(t, isNot(contains('does not perform behavioral profiling')));
    expect(t, isNot(contains('app store listing')));
    // The offline phone build's own promise stays, labelled as that build's.
    expect(t, contains('The phone app without a school server'));
  });

  testWidgets('the terms describe the whole school, not Class X teachers', (tester) async {
    tester.view.physicalSize = const Size(900, 9000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: LegalPage(doc: 'terms')));
    final t = tester.widgetList<Text>(find.byType(Text)).map((x) => x.data ?? '').join('\n');
    expect(t, contains('classes 1 to 10'));
    expect(t, isNot(contains('Class X teachers')));
  });
}
