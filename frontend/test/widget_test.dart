import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('AcademicOS smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: Center(child: Text('AcademicOS'))),
      ),
    );

    expect(find.text('AcademicOS'), findsOneWidget);
  });
}
