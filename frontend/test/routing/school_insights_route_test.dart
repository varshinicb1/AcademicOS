// QA S-15 (2026-10-01): every visit to School insights sent a hidden
// `GET /knowledge/stu_meera`, a 404. '/analytics/school' was a child of
// '/analytics', whose page is the Mastery dashboard, so go_router built that
// dashboard underneath the insights page and it asked for the offline demo
// student. School insights is its own route now, and the dashboard asks the
// server for no demo student on the web.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/routing/app_router.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/presentation/analytics/pages/mastery_dashboard.dart';
import 'package:academicos/presentation/analytics/pages/principal_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// The path of every page go_router builds for [location], outermost first.
List<String> _pagesBuilt(GoRouter router, String location) {
  final paths = <String>[];
  void walk(List<RouteMatchBase> matches) {
    for (final m in matches) {
      if (m is ShellRouteMatch) {
        walk(m.matches);
      } else if (m.route is GoRoute) {
        paths.add((m.route as GoRoute).path);
      }
    }
  }

  walk(router.configuration.findMatch(Uri.parse(location)).matches);
  return paths;
}

class _Server implements HttpClientAdapter {
  final List<String> asked = [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    asked.add(o.path);
    if (o.path == '/insights/school/school_1') {
      return ResponseBody.fromString(
          '{"students":4,"studentsWithEvidence":1,"assessments":0,"averageMastery":0.78,'
          '"subjects":[],"interventions":[]}',
          200,
          headers: _json);
    }
    return ResponseBody.fromString('{"detail":"not found"}', 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Server server;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('school_insights_route_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    server = _Server();
    GetIt.instance.registerSingleton<PillarApi>(PillarApi(Dio()..httpClientAdapter = server));
    LocalStore.instance.authUser = {'id': 'p_1', 'schoolId': 'school_1', 'role': 'principal', 'name': 'Priya'};
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('school_insights_route_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  test('School insights is built alone, with no Mastery dashboard beneath it', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final router = container.read(appRouterProvider);
    expect(_pagesBuilt(router, '/analytics/school'), ['/analytics/school']);
    expect(_pagesBuilt(router, '/analytics/gaps'), ['/analytics', 'gaps'], reason: 'the other pages keep their place');
  });

  testWidgets('the insights page asks only for the school; enrolled and with-evidence are both said (S-04)',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PrincipalPage()));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
    expect(server.asked, ['/insights/school/school_1']);
    expect(find.text('Students'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);
    expect(find.textContaining('4 students are enrolled; with evidence: 1'), findsOneWidget);
  });

  testWidgets('on the web the Mastery dashboard asks the server for no demo student', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: MasteryDashboard()));
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 200)));
    await tester.pumpAndSettle();
    expect(server.asked, isEmpty);
    expect(find.text('No knowledge yet'), findsOneWidget);
  });
}
