// The browse screens show the classes this release serves, and no others.
//
// Audit D22 (2026-09-27): the live Question Bank and Syllabus pages set their
// list straight from GET /catalog, so they offered class 12's 510 questions
// over 35 subjects -- a class nobody can set a paper for -- beside classes
// 6-10. Fed here the real served bank's catalog (captured by
// scripts/capture_paper_builder_fixtures.py), 68 rows of which 33 are classes
// 6-10 with 4,916 questions.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/constants/release_scope.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/presentation/question_bank/pages/question_bank_page.dart';
import 'package:academicos/presentation/syllabus/pages/syllabus_page.dart';

import '../support/fake_server.dart';

Map<String, dynamic> _catalog() => Map<String, dynamic>.from(jsonDecode(
    File('test/paper_builder/fixtures/catalog.json').readAsStringSync()) as Map);

void main() {
  tearDown(() => GetIt.instance.reset());

  final catalog = Catalog.fromJson(_catalog());
  final inScope = releaseEntries(catalog.entries);

  test('the captured catalog is the real one, and the rule keeps classes 6-10', () {
    expect(catalog.entries.any((e) => e.grade == 12), isTrue);
    expect(inScope.length, 33);
    expect(inScope.fold<int>(0, (s, e) => s + e.questionCount), 4916);
    expect(inScope.map((e) => e.grade).toSet(), {6, 7, 8, 9, 10});
  });

  testWidgets('Question Bank counts and lists classes 6-10 only', (tester) async {
    final first = inScope.first;
    final server = FakeServer({
      'GET /catalog': (200, _catalog()),
      'POST /questions/search': (200, <Object>[]),
    });
    GetIt.instance.registerSingleton<PillarApi>(PillarApi(fakeDio(server)));
    tester.view.physicalSize = const Size(1280, 8000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: QuestionBankPage()));
    await tester.pumpAndSettle();

    expect(find.text('4916 questions'), findsOneWidget);
    for (final grade in [11, 12]) {
      expect(find.text('Class $grade'), findsNothing, reason: 'class $grade');
    }
    expect(find.text('Class ${first.grade}'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Syllabus offers classes 6-10 only', (tester) async {
    final science = inScope.firstWhere((e) => e.subject == 'Science');
    final server = FakeServer({
      'GET /catalog': (200, _catalog()),
      'GET /catalog/Science/${science.grade}/chapters': (200, <Object>[]),
    });
    GetIt.instance.registerSingleton<PillarApi>(PillarApi(fakeDio(server)));
    tester.view.physicalSize = const Size(1280, 2000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(home: SyllabusPage()));
    await tester.pumpAndSettle();

    final dropdown = tester.widget<DropdownButton<String>>(find.byType(DropdownButton<String>));
    final values = [for (final item in dropdown.items!) item.value!];
    expect(values.length, 33);
    expect(values.where((v) => !releaseGrades.contains(int.parse(v.split('|').last))), isEmpty);
    expect(tester.takeException(), isNull);
  });
}
