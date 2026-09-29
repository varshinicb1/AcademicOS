// Profiles on a shared family phone (SA-8): each student and parent signed
// in is kept with their own session, switching makes one active, signing
// out forgets only that one, "add someone" forgets nobody, and staff
// accounts are never kept for switching.
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

Map<String, dynamic> _u(String id, String role) => {'id': id, 'name': id, 'role': role, 'schoolId': 'school_1'};

void main() {
  late Directory tmp;
  final store = LocalStore.instance;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('profiles_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    for (final p in store.profiles) {
      store.forgetProfile((p['user'] as Map)['id'] as String);
    }
    store.stepAway();
  });

  tearDownAll(() async {
    await Hive.close();
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  test('students and parents are kept; switching makes one active with its own session', () {
    store.signIn('tok-asha', _u('asha', 'student'));
    store.signIn('tok-ravi', _u('ravi', 'student'));
    store.signIn('tok-mum', _u('mum', 'parent'));
    expect(store.profiles.map((p) => (p['user'] as Map)['id']), ['asha', 'ravi', 'mum']);
    expect(store.authUser!['id'], 'mum');

    expect(store.switchTo('asha'), isTrue);
    expect(store.authUser!['id'], 'asha');
    expect(store.authToken, 'tok-asha');
    expect(store.switchTo('nobody'), isFalse);
    expect(store.authUser!['id'], 'asha');
  });

  test('a new sign-in of the same person replaces their saved session', () {
    store.signIn('old', _u('asha', 'student'));
    store.signIn('new', _u('asha', 'student'));
    expect(store.profiles.single['token'], 'new');
  });

  test('signing out forgets only that profile; stepping away forgets nobody', () {
    store.signIn('tok-asha', _u('asha', 'student'));
    store.signIn('tok-mum', _u('mum', 'parent'));
    store.stepAway();
    expect(store.authToken, isNull);
    expect(store.profiles, hasLength(2));

    store.switchTo('mum');
    store.clearAuth();
    expect(store.authToken, isNull);
    expect(store.profiles.map((p) => (p['user'] as Map)['id']), ['asha']);
  });

  test('a teacher or principal is signed in but not kept for switching', () {
    store.signIn('tok-asha', _u('asha', 'student'));
    store.signIn('tok-ana', _u('ana', 'teacher'));
    expect(store.authUser!['id'], 'ana');
    expect(store.profiles.map((p) => (p['user'] as Map)['id']), ['asha']);
  });
}
