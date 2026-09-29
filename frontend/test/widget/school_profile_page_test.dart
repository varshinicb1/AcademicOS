// The school's own name and logo (EX-5, audit D41): until a principal set a
// name, every paper printed "Default CBSE Template" where the school's name
// goes. The page says so, saves the name, and uploads and removes the logo;
// the fake backend answers in the server's shapes and records what is sent.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/presentation/workspace/school_profile_page.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

const _phone = Size(375, 812);
// A 1x1 PNG.
final _png = Uint8List.fromList(base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='));

class _Backend implements HttpClientAdapter {
  Map<String, dynamic> profile = {'name': null, 'address': null, 'affiliation': null, 'hasLogo': false};
  final List<(String, String, dynamic)> sent = [];
  static const _json = {Headers.contentTypeHeader: ['application/json']};

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<List<int>>? body, Future<void>? cancel) async {
    if (o.method != 'GET') sent.add((o.method, o.path, o.data));
    switch ((o.method, o.path)) {
      case ('GET', '/curriculum/school-profile'):
        return ResponseBody.fromString(jsonEncode(profile), 200, headers: _json);
      case ('PUT', '/curriculum/school-profile'):
        profile = {...profile, ...Map<String, dynamic>.from(o.data as Map)};
        return ResponseBody.fromString(jsonEncode(profile), 200, headers: _json);
      case ('GET', '/curriculum/school-profile/logo'):
        if (profile['hasLogo'] != true) {
          return ResponseBody.fromString('{"detail":"the school has no logo"}', 404, headers: _json);
        }
        return ResponseBody.fromBytes(_png, 200, headers: {Headers.contentTypeHeader: ['image/png']});
      case ('POST', '/curriculum/school-profile/logo'):
        profile = {...profile, 'hasLogo': true};
        return ResponseBody.fromString(jsonEncode(profile), 200, headers: _json);
      case ('DELETE', '/curriculum/school-profile/logo'):
        profile = {...profile, 'hasLogo': false};
        return ResponseBody.fromString(jsonEncode(profile), 200, headers: _json);
    }
    return ResponseBody.fromString('{"detail":"no route"}', 404, headers: _json);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  late Directory tmp;
  late _Backend backend;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('school_profile_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() {
    backend = _Backend();
    GetIt.instance.registerSingleton<Dio>(Dio()..httpClientAdapter = backend);
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
      print('school_profile_page_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  Future<void> pump(WidgetTester tester, {Future<(Uint8List, String, String)?> Function()? pick}) async {
    tester.view.physicalSize = _phone;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(home: SchoolProfilePage(pickLogo: pick)));
    await tester.pumpAndSettle();
  }

  Future<void> tapKey(WidgetTester tester, String key) async {
    await tester.ensureVisible(find.byKey(ValueKey(key)));
    await tester.tap(find.byKey(ValueKey(key)));
    await tester.pumpAndSettle();
  }

  testWidgets('an unnamed school is told, and cannot add a logo before a name', (tester) async {
    await pump(tester);
    expect(find.byKey(const ValueKey('profile-unnamed')), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('profile-logo-upload'))).onPressed, isNull);
    expect(tester.takeException(), isNull, reason: 'fits a phone');
  });

  testWidgets('an empty name is caught; a name is saved as papers will print it', (tester) async {
    await pump(tester);
    await tapKey(tester, 'profile-save');
    expect(find.text('Give the school its name, as it should print on papers.'), findsOneWidget);
    expect(backend.sent, isEmpty);

    await tester.enterText(find.byKey(const ValueKey('profile-name')), 'Sunrise Public School');
    await tester.enterText(find.byKey(const ValueKey('profile-affiliation')), 'CBSE Affiliation No. 1234567');
    await tapKey(tester, 'profile-save');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('PUT', '/curriculum/school-profile'));
    expect(body, {'name': 'Sunrise Public School', 'address': null, 'affiliation': 'CBSE Affiliation No. 1234567'});
    expect(find.text('Saved. New papers print this name.'), findsOneWidget);
    expect(find.byKey(const ValueKey('profile-unnamed')), findsNothing);
  });

  testWidgets('a logo is uploaded as a PNG file, shown, and removed', (tester) async {
    backend.profile = {'name': 'Sunrise Public School', 'hasLogo': false};
    await pump(tester, pick: () async => (_png, 'logo.png', 'image/png'));
    await tapKey(tester, 'profile-logo-upload');
    final (method, path, body) = backend.sent.single;
    expect((method, path), ('POST', '/curriculum/school-profile/logo'));
    final file = (body as FormData).files.single;
    expect((file.key, file.value.filename, file.value.contentType.toString()), ('file', 'logo.png', 'image/png'));
    expect(find.byKey(const ValueKey('profile-logo')), findsOneWidget);

    await tester.tap(find.text('Remove the logo'));
    await tester.pumpAndSettle();
    expect(backend.sent.last.$1, 'DELETE');
    expect(find.byKey(const ValueKey('profile-logo')), findsNothing);
  });
}
