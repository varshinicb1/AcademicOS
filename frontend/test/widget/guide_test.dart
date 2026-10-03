// The Guide (school feedback, 2026-10-01: "too many options to confuse; add
// an interactive user guide"): each role's common jobs, each opening to a few
// numbered steps and a Take me there button. A guide that names a page the
// menu no longer has, or sends someone to a route that does not exist, is
// worse than none -- so the content is held to the real menu and the real
// router here.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/routing/app_router.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/presentation/guide/guide_content.dart';
import 'package:academicos/presentation/guide/guide_page.dart';
import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// The Guide for [role] at /school/guide, and a stand-in page at every route
/// a job can send someone to.
Widget _app(String role) {
  final routes = {for (final r in guideRoles) for (final j in guideJobsFor(r)) Uri.parse(j.route).path};
  return MaterialApp.router(
    theme: AppTheme.darkTheme,
    routerConfig: GoRouter(initialLocation: guidePath, routes: [
      GoRoute(path: guidePath, builder: (context, state) => GuidePage(role: role)),
      for (final path in routes)
        GoRoute(path: path, builder: (context, state) => Scaffold(body: Text('Arrived at ${state.uri}'))),
    ]),
  );
}

Future<void> _open(WidgetTester tester, GuideJob job) async {
  final tile = find.byKey(PageStorageKey('guide-job-${job.id}'));
  await tester.scrollUntilVisible(tile, 200, scrollable: find.byType(Scrollable).first);
  await tester.tap(find.text(job.title));
  await tester.pumpAndSettle();
}

void main() {
  test('every role has its common jobs, each with three to six steps', () {
    final titles = {for (final r in guideRoles) r: [for (final j in guideJobsFor(r)) j.title]};
    expect(titles['principal'], [
      'Set up the school',
      'Invite teachers and students',
      'Give classes their teachers and make the timetable',
      'Plan lessons',
      'Make a question paper and answer key',
      'Publish an exam datesheet',
      'Mark a teacher absent and arrange cover',
      'Read the term report',
    ]);
    expect(titles['teacher'], ['See today\'s classes', 'Mark a lesson taught', 'Set homework',
      'Make a question paper and answer key', 'Enter marks', 'Apply for leave']);
    expect(titles['student'], ['See today', 'Do your homework', 'See your exams and prepare', 'See your progress']);
    expect(titles['parent'], ['See your child\'s week', 'Check homework', 'See the report card']);
    for (final r in guideRoles) {
      for (final j in guideJobsFor(r)) {
        expect(j.steps.length, inInclusiveRange(3, 6), reason: '$r: ${j.title} has ${j.steps.length} steps');
      }
      expect({for (final j in guideJobsFor(r)) j.id}.length, guideJobsFor(r).length, reason: '$r job ids are unique');
    }
    expect(guideJobsFor(''), isEmpty, reason: 'no account, no guide');
  });

  test('every job starts from a menu entry that role really has', () {
    for (final r in guideRoles) {
      final menu = [for (final i in navItemsFor(r)) i.label];
      for (final j in guideJobsFor(r)) {
        expect(menu, contains(j.menu), reason: '$r: "${j.title}" starts from ${j.menu}');
        if (r != 'owner') {
          expect(j.steps.join(' '), contains(j.menu), reason: '$r: "${j.title}" names ${j.menu} in its steps');
        }
      }
    }
  });

  group('against the app\'s own router', () {
    late Directory tmp;

    setUpAll(() async {
      tmp = Directory.systemTemp.createTempSync('guide_test_');
      Hive.init(tmp.path);
      await Hive.openBox('academicos_cache');
    });

    tearDownAll(() async {
      await GetIt.instance.reset();
      try {
        await Hive.close().timeout(const Duration(seconds: 10));
      } on TimeoutException {
        // ignore: avoid_print
        print('guide_test: Hive.close() did not return within 10s -- proceeding.');
      }
      try {
        tmp.deleteSync(recursive: true);
      } on FileSystemException {
        // Windows may still hold the box file; a leaked temp dir is harmless.
      }
    });

    test('every Take me there, and the Guide itself, is a route the app has', () {
      final router = ProviderContainer().read(appRouterProvider);
      for (final location in [guidePath, for (final r in guideRoles) for (final j in guideJobsFor(r)) j.route]) {
        final match = router.configuration.findMatch(Uri.parse(location));
        expect(match.isError, isFalse, reason: '$location is not a route in app_router.dart');
      }
    });
  });

  for (final role in guideRoles) {
    testWidgets('the $role guide lists its jobs, and each opens to numbered steps', (tester) async {
      tester.view.physicalSize = const Size(1280, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(_app(role));
      await tester.pumpAndSettle();

      expect(find.text('What a ${guideRoleName(role)} does most'), findsOneWidget);
      for (final job in guideJobsFor(role)) {
        await _open(tester, job);
        for (var i = 0; i < job.steps.length; i++) {
          expect(find.text(job.steps[i]), findsOneWidget, reason: '${job.title}: step ${i + 1}');
          expect(find.text('${i + 1}'), findsWidgets, reason: '${job.title}: step ${i + 1} is numbered');
        }
        expect(find.byKey(ValueKey('guide-go-${job.id}')), findsOneWidget);
        expect(tester.takeException(), isNull);
        // Fold it again, so the next job's steps are the only ones open.
        await tester.tap(find.text(job.title));
        await tester.pumpAndSettle();
      }
    });
  }

  testWidgets('Take me there goes to the page that does the job', (tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    for (final (role, id, arrived) in [
      ('principal', 'exams', '/school/exams'),
      ('teacher', 'leave', '/school/my-day'),
      ('student', 'homework', '/school/my-homework'),
      ('parent', 'report-card', '/school/family'),
    ]) {
      await tester.pumpWidget(const SizedBox());
      await tester.pumpWidget(_app(role));
      await tester.pumpAndSettle();
      final job = guideJobsFor(role).firstWhere((j) => j.id == id);
      await _open(tester, job);
      final go = find.byKey(ValueKey('guide-go-$id'));
      await tester.ensureVisible(go);
      await tester.pumpAndSettle();
      await tester.tap(go);
      await tester.pumpAndSettle();
      expect(find.text('Arrived at $arrived'), findsOneWidget, reason: '$role: ${job.title}');
    }
  });

  testWidgets('on a phone the guide fits and its button is thumb-sized', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(_app('principal'));
    await tester.pumpAndSettle();
    final job = guideJobsFor('principal').first;
    await _open(tester, job);
    expect(tester.takeException(), isNull, reason: 'no overflow at 375 px');
    final go = find.byKey(ValueKey('guide-go-${job.id}'));
    await tester.ensureVisible(go);
    await tester.pumpAndSettle();
    expect(tester.getSize(go).height, greaterThanOrEqualTo(44));
  });

  testWidgets('with no role there are no jobs, only a sign-in note', (tester) async {
    await tester.pumpWidget(_app(''));
    await tester.pumpAndSettle();
    expect(find.text('Sign in to see the guide for your role.'), findsOneWidget);
  });
}
