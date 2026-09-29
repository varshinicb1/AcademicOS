// The young learners' home (SA-7): four large pictures with one word each,
// big enough to tap on a small phone, and read out by a screen reader.
import 'package:academicos/presentation/workspace/young_home.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('four large picture tiles, one word each, at 375 px', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final semantics = tester.ensureSemantics();
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: YoungHome())));
    for (final label in ['Today', 'Homework', 'How I am doing', 'Messages']) {
      expect(find.text(label), findsOneWidget);
      expect(find.bySemanticsLabel(label), findsWidgets);
    }
    final tile = tester.getSize(find.ancestor(of: find.text('Today'), matching: find.byType(InkWell)));
    expect(tile.width, greaterThan(140), reason: 'a young child needs a big target');
    expect(tile.height, greaterThan(140));
    expect(find.byIcon(Icons.backpack_rounded), findsOneWidget);
    semantics.dispose();
  });
}
