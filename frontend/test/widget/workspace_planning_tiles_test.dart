// The School workspace's ways in to the planning screens: "Lesson plans" sits
// beside Timetable and "Periods owed" beside Attendance & cover, for the
// principal and for a teacher the principal made an admin for that area
// (timetable, leave) -- the same people the routes behind them accept.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/workspace_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

class _Backend implements HttpClientAdapter {
  List<String> grants = const [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    final answer = switch (o.path) {
      '/notifications' => {'items': <dynamic>[], 'unreadCount': 0},
      '/my-grants' => {'capabilities': grants},
      _ => null,
    };
    if (answer == null) {
      return ResponseBody.fromString(jsonEncode({'detail': 'not served here'}), 404, headers: _json);
    }
    return ResponseBody.fromString(jsonEncode(answer), 200, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  useAppFonts();
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('workspace_planning_tiles_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
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
      print('workspace_planning_tiles_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pumpAs(WidgetTester tester, String role) async {
    LocalStore.instance.authUser = {'id': 'u_1', 'schoolId': 'school_1', 'role': role, 'name': 'Ana'};
    await pumpPage(tester, const WorkspacePage(), laptopScreen);
  }

  testWidgets('a teacher given the timetable and leave areas sees both planning screens', (tester) async {
    backend.grants = ['timetable', 'leave'];
    await pumpAs(tester, 'teacher');
    expect(find.text('Lesson plans'), findsOneWidget);
    expect(find.text('Periods owed'), findsOneWidget);
    expectNoOverflow(tester);
  });

  testWidgets('a teacher without those areas sees neither', (tester) async {
    await pumpAs(tester, 'teacher');
    expect(find.text('My day'), findsOneWidget);
    expect(find.text('Lesson plans'), findsNothing);
    expect(find.text('Periods owed'), findsNothing);
  });
}
