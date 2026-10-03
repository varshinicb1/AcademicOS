// The first-time welcome: the first time a person signs in on a device, a
// short dialog offers Show me around (the Guide) or Not now. Whatever they
// choose is remembered for that person on that device, so it is shown once.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/guide/guide_page.dart';
import 'package:academicos/presentation/guide/guide_welcome.dart';
import 'package:academicos/presentation/shared/device_memory.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// The app's pages behind the welcome, as the router wraps them.
Widget _app({required String userId, required String role}) => MaterialApp.router(
      theme: AppTheme.darkTheme,
      routerConfig: GoRouter(initialLocation: '/school', routes: [
        ShellRoute(
          builder: (context, state, child) => GuideWelcome(userId: userId, role: role, child: child),
          routes: [
            GoRoute(path: '/school', builder: (context, state) => const Scaffold(body: Text('Overview'))),
            GoRoute(path: guidePath, builder: (context, state) => GuidePage(role: role)),
          ],
        ),
      ]),
    );

Future<void> _start(WidgetTester tester, {required String userId, String role = 'principal'}) async {
  await tester.pumpWidget(const SizedBox());
  await tester.pumpWidget(_app(userId: userId, role: role));
  await tester.pumpAndSettle();
}

final _welcome = find.byKey(const ValueKey('guide-welcome'));

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('guide_welcome_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    // Not awaited: a write left in the previous test's fake clock would hang it.
    final box = Hive.box('academicos_cache');
    box.deleteAll(box.keys.where((k) => '$k'.startsWith('guide_welcome:')).toList());
    DeviceMemory.resetMemory();
    resetGuideWelcomeRun();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('guide_welcome_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  testWidgets('a first sign-in is welcomed once; Not now is remembered', (tester) async {
    await _start(tester, userId: 'u_principal');
    expect(_welcome, findsOneWidget);
    expect(find.text('Welcome to AcademicOS'), findsOneWidget);
    expect(find.text('Show me around'), findsOneWidget);
    expect(find.text('Not now'), findsOneWidget);

    await tester.tap(find.text('Not now'));
    await tester.pumpAndSettle();
    expect(_welcome, findsNothing);
    expect(find.text('Overview'), findsOneWidget, reason: 'Not now stays on the page');
    expect(Hive.box('academicos_cache').get('guide_welcome:u_principal'), 'later',
        reason: 'the choice is kept in the local store, per user');

    // Signing in again on this device: no second welcome.
    resetGuideWelcomeRun();
    await _start(tester, userId: 'u_principal');
    expect(_welcome, findsNothing);
  });

  testWidgets('Show me around opens the Guide for that role', (tester) async {
    await _start(tester, userId: 'u_teacher', role: 'teacher');
    await tester.tap(find.text('Show me around'));
    await tester.pumpAndSettle();
    expect(find.text('What a teacher does most'), findsOneWidget);
    expect(find.text('Apply for leave'), findsOneWidget);
    expect(Hive.box('academicos_cache').get('guide_welcome:u_teacher'), 'guide');

    resetGuideWelcomeRun();
    await _start(tester, userId: 'u_teacher', role: 'teacher');
    expect(_welcome, findsNothing);
  });

  testWidgets('each person on a shared device is welcomed once', (tester) async {
    await _start(tester, userId: 'u_student_1', role: 'student');
    await tester.tap(find.text('Not now'));
    await tester.pumpAndSettle();

    await _start(tester, userId: 'u_student_2', role: 'student');
    expect(_welcome, findsOneWidget, reason: 'another person on the same device has not seen it');
    // Dismissing it (tapping outside) counts as Not now.
    await tester.tapAt(const Offset(5, 5));
    await tester.pumpAndSettle();
    expect(_welcome, findsNothing);
    expect(Hive.box('academicos_cache').get('guide_welcome:u_student_2'), 'later');
  });

  testWidgets('no welcome without a signed-in person or a guide for the role', (tester) async {
    await _start(tester, userId: '');
    expect(_welcome, findsNothing);
    await _start(tester, userId: 'u_x', role: '');
    expect(_welcome, findsNothing);
  });
}
