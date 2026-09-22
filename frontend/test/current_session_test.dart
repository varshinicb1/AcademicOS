// CurrentSession: the web app's identity is the signed-in user (Task 604).
//
// The live release (a153003) asked the server for 'demo_school' whoever had
// signed in. These pin the rule the screens now read: signed in, the login
// response's school/id/role; the on-device engine wired (the offline Android
// build), that device's own identity; neither, nothing -- never a guessed
// school.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/local_engine/offline_identity.dart';
import 'package:academicos/core/session/current_session.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:dio/dio.dart';

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('current_session_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  tearDown(() async {
    LocalStore.instance.clearAuth();
    await GetIt.instance.reset();
  });

  tearDownAll(() async {
    await Hive.close();
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  test('signed in on the web: the login response names the school, user and role', () {
    GetIt.instance.registerSingleton<ApiClient>(ApiClient(Dio()));
    LocalStore.instance.authUser = {
      'id': 'usr_9f2', 'schoolId': 'sunrise_public_school', 'name': 'Asha',
      'email': 'asha@sunrise.example', 'role': 'principal',
    };
    expect(CurrentSession.schoolId, 'sunrise_public_school');
    expect(CurrentSession.userId, 'usr_9f2');
    expect(CurrentSession.role, 'principal');
  });

  test('signed out on the web: no school at all, never a demo one', () {
    GetIt.instance.registerSingleton<ApiClient>(ApiClient(Dio()));
    expect(CurrentSession.schoolId, isEmpty);
    expect(CurrentSession.userId, isEmpty);
  });

  test('the on-device engine keeps the device identity its local data is stored under', () {
    GetIt.instance.registerSingleton<ApiClient>(LocalApiClient());
    expect(CurrentSession.schoolId, OfflineIdentity.schoolId);
    expect(CurrentSession.userId, OfflineIdentity.teacherId);
  });
}
