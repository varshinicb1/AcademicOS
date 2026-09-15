// Live end-to-end auth test against the deployed Render backend, driving the
// app's REAL frontend code: the production sessionInterceptor() (token
// attach + 401 dead-session recovery, the exact instance initDependencies()
// installs), the real AuthApi, and the real LocalStore token storage (Hive,
// temp dir) -- the same wiring the Sign in screen uses at runtime.
//
// Run:  flutter test test/live_backend_auth_test.dart
// Requires network access to https://academicos-backend.onrender.com
// (Render free tier cold-starts in ~60s; timeouts below absorb that).
//
// Writes to production: registers one disposable QA teacher under an
// obviously-marked `qa-frontend-live-<ts>` school id, then logs the session
// out at the end. Nothing else is created or mutated.
import 'dart:io';

import 'package:academicos/core/di/service_locator.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

const liveBase = 'https://academicos-backend.onrender.com/api/v1';

void main() {
  late Dio dio;
  late AuthApi auth;
  late Directory hiveDir;

  setUpAll(() async {
    hiveDir = Directory.systemTemp.createTempSync('academicos_qa_hive');
    Hive.init(hiveDir.path);
    await Hive.openBox('academicos_cache');
    // Same BaseOptions as service_locator.dart (90s timeouts for Render
    // cold starts), with the production interceptor installed.
    dio = Dio(BaseOptions(
      baseUrl: liveBase,
      connectTimeout: const Duration(seconds: 90),
      receiveTimeout: const Duration(seconds: 90),
      headers: {'Content-Type': 'application/json'},
    ));
    dio.interceptors.add(sessionInterceptor());
    auth = AuthApi(dio);
  });

  tearDownAll(() async {
    await Hive.close();
    if (hiveDir.existsSync()) hiveDir.deleteSync(recursive: true);
  });

  test('no token: live backend 401s with "missing bearer token" and the '
      'interceptor classifies it as a dead session', () async {
    LocalStore.instance.clearAuth();
    try {
      await dio.get('/assessments');
      fail('expected a 401 without a token');
    } on DioException catch (e) {
      expect(e.response?.statusCode, 401);
      expect((e.response?.data as Map)['detail'], 'missing bearer token');
      expect(isDeadSession(e), isTrue);
      // No token was held, so nothing was wiped and no navigation hijack.
      expect(LocalStore.instance.authToken, isNull);
    }
  }, timeout: const Timeout(Duration(seconds: 120)));

  test('bad login: AuthApi surfaces a friendly AuthException and the '
      'auth-path exception leaves any held session untouched', () async {
    LocalStore.instance.authToken = 'seed-token';
    try {
      await auth.login(
        email: 'nobody-${DateTime.now().microsecondsSinceEpoch}@qa.invalid',
        password: 'wrong-password',
      );
      fail('expected an AuthException for bad credentials');
    } on AuthException catch (e) {
      expect(e.message.toLowerCase(), contains('incorrect email or password'));
    }
    expect(LocalStore.instance.authToken, 'seed-token',
        reason: 'a 401 on /auth/login must never trigger the dead-session bounce');
    LocalStore.instance.clearAuth();
  }, timeout: const Timeout(Duration(seconds: 120)));

  test('full round trip: register -> interceptor attaches token -> me and '
      'assessments 200 -> teacher-on-principal-route 403 keeps the session '
      '-> tampered token wipes it', () async {
    final stamp = DateTime.now().millisecondsSinceEpoch;
    final email = 'qa-teacher-$stamp@academicos.test';
    final schoolId = 'qa-frontend-live-$stamp';
    final result = await auth.register(
      schoolId: schoolId,
      name: 'QA Frontend Teacher',
      email: email,
      password: 'qa-password-$stamp',
      role: 'teacher',
    );
    expect(result.token, isNotEmpty);
    expect(result.user.email, email);
    expect(result.user.role, 'teacher');
    expect(result.user.schoolId, schoolId);

    // Store exactly like the Sign in screen does; every request below must
    // get the token attached by the production interceptor.
    LocalStore.instance.authToken = result.token;

    final me = await auth.me();
    expect(me.email, email);
    expect(me.role, 'teacher');
    expect(me.schoolId, schoolId);

    final assessments = await dio.get('/assessments');
    expect(assessments.statusCode, 200);
    expect(assessments.data, isA<List>());

    // Principal-only roster as a teacher: 403, and the still-valid session
    // must survive it (bounceToLogin is for 401s only).
    try {
      await dio.get('/auth/users');
      fail('expected a 403 for a teacher on the principal-only roster');
    } on DioException catch (e) {
      expect(e.response?.statusCode, 403);
      expect(isDeadSession(e), isFalse);
    }
    expect(LocalStore.instance.authToken, result.token,
        reason: 'a 403 must not wipe a valid session');

    // Dead (tampered) token: 401 -> the interceptor wipes the local session.
    // (GoRouter isn't registered in this test; bounceToLogin's router lookup
    // is best-effort by design, so the wipe is what's asserted.)
    LocalStore.instance.authToken = '${result.token}-tampered';
    try {
      await auth.me();
      fail('expected a 401 for a tampered token');
    } on DioException catch (e) {
      expect(e.response?.statusCode, 401);
      expect(isDeadSession(e), isTrue);
    }
    expect(LocalStore.instance.authToken, isNull,
        reason: 'the interceptor must clear a dead session locally');

    // Server-side cleanup: log the real session out.
    LocalStore.instance.authToken = result.token;
    await auth.logout();
    LocalStore.instance.clearAuth();
  }, timeout: const Timeout(Duration(minutes: 3)));
}
