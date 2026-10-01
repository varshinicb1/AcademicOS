// Getting back in, and the one language setting (QA 2026-10-01).
//
// S-05: the sign-in page had no "Forgot password?", answered a wrong
// password with the server's raw "incorrect email or password", and there
// was nowhere to choose a new password after a reset.
// S-20: an invite link opened in a tab already on Sign in did not fill in
// the code until a reload.
// S-16: the School page offered Hindi while Settings, Language listed
// English only, "not translated yet".
//
// Run as the web build (the default); the offline build has no accounts.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/presentation/auth/pages/login_page.dart';
import 'package:academicos/presentation/settings/pages/settings_page.dart';
import 'package:academicos/presentation/workspace/strings.dart';

import '../support/real_di.dart';

class _Auth extends Interceptor {
  final List<String> calls = [];
  Object? lastBody;

  void _answer(RequestInterceptorHandler h, RequestOptions o, int status, Object? body) {
    final r = Response(requestOptions: o, statusCode: status, data: body);
    status < 400
        ? h.resolve(r)
        : h.reject(DioException.badResponse(statusCode: status, requestOptions: o, response: r));
  }

  @override
  void onRequest(RequestOptions o, RequestInterceptorHandler h) {
    calls.add('${o.method} ${o.path}');
    lastBody = o.data;
    switch ((o.method, o.path)) {
      case ('GET', '/auth/providers'):
        return _answer(h, o, 200, {'google': null, 'emailCode': false});
      case ('POST', '/auth/login'):
        return _answer(h, o, 401, {'detail': 'incorrect email or password'});
      case ('POST', '/auth/password'):
        final body = o.data as Map;
        if (body['currentPassword'] != 'k7mq-x2rw-9tpd') {
          return _answer(h, o, 400, {'detail': 'the current password is not right'});
        }
        return _answer(h, o, 200, {'ok': true, 'token': 'token-after-change'});
    }
    _answer(h, o, 404, {'detail': 'not served here'});
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late RealTestEnv env;
  late _Auth auth;

  setUpAll(() async {
    env = await RealTestEnv.init('password_and_language_test_');
    PackageInfo.setMockInitialValues(appName: 'AcademicOS', packageName: 'com.vidyuthlabs.academicos',
        version: '1.0.0', buildNumber: '1', buildSignature: '');
  });

  tearDownAll(() async => env.dispose());

  setUp(() async {
    auth = _Auth();
    final dio = Dio(BaseOptions(baseUrl: 'http://auth.test/api/v1'))..interceptors.add(auth);
    GetIt.instance.registerSingleton<Dio>(dio);
    GetIt.instance.registerSingleton<AuthApi>(AuthApi(dio));
  });

  tearDown(() async => GetIt.instance.reset());

  group('sign in', () {
    testWidgets('"Forgot password?" says who gives a password back', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('forgot-password')));
      await tester.pumpAndSettle();
      expect(find.text('Forgot your password?'), findsOneWidget);
      expect(find.textContaining('ask your principal'), findsOneWidget);
      expect(find.textContaining('Students and parents'), findsOneWidget);
      expect(find.textContaining('Change password'), findsOneWidget);
      // No school email here, so no emailed code is offered.
      expect(find.byKey(const Key('forgot-email-code')), findsNothing);
      await tester.tap(find.text('OK'));
      await tester.pumpAndSettle();
      expect(find.text('Forgot your password?'), findsNothing);
    });

    testWidgets("a wrong password reads as a sentence, not the server's lower-case text", (tester) async {
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));
      await tester.pumpAndSettle();
      await tester.enterText(find.widgetWithText(TextFormField, 'Email'), 'meera@x.in');
      await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'wrong-password');
      await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
      await tester.pumpAndSettle();
      expect(find.text('Incorrect email or password.'), findsOneWidget);
      expect(find.text('incorrect email or password'), findsNothing);
    });

    testWidgets('an invite link opened on the open Sign in page fills in the code', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('register-invite-code')), findsNothing);
      // go_router rebuilds the same page with the link's query.
      await tester.pumpWidget(const MaterialApp(home: LoginPage(inviteCode: 'NEW-invite-code')));
      await tester.pumpAndSettle();
      final field = tester.widget<TextFormField>(find.byKey(const Key('register-invite-code')));
      expect(field.controller!.text, 'NEW-invite-code');
      // And a school-setup link, the same way.
      await tester.pumpWidget(const MaterialApp(home: LoginPage(schoolId: 'qa-fresh-school2')));
      await tester.pumpAndSettle();
      final school = tester.widget<TextFormField>(find.byKey(const Key('register-school-id')));
      expect(school.controller!.text, 'qa-fresh-school2');
    });
  });

  group('settings', () {
    Future<void> pumpSettings(WidgetTester tester) async {
      tester.view.physicalSize = const Size(1080, 12000);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(wrapForTest(const SettingsPage()));
      await tester.pumpAndSettle();
    }

    testWidgets('Language offers Hindi, the same setting as the School page, and says what it covers',
        (tester) async {
      await pumpSettings(tester);
      expect(find.text(hindiCoverage), findsOneWidget);
      expect(find.textContaining('not translated yet'), findsNothing);
      await tester.tap(find.text('English'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('हिन्दी (Hindi)').last);
      await tester.pumpAndSettle();
      expect(uiHindi, isTrue);
      expect(tr('My week'), 'मेरा सप्ताह');
      setUiLanguage('en');
    });

    // Last in the file: it writes the session to the Hive box inside the
    // test's fake clock, and a later setUp's box call can wait on that write
    // for ever (the hive lock-queue flake RealTestEnv.dispose names).
    testWidgets('Change password keeps this device signed in with the new token', (tester) async {
      LocalStore.instance.signIn('token-before', {'id': 't_meera', 'schoolId': 's', 'name': 'Meera Iyer',
        'email': 'meera@x.in', 'role': 'teacher'});
      await pumpSettings(tester);
      await tester.tap(find.text('Change password'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('password-current')), 'not-it');
      await tester.enterText(find.byKey(const Key('password-new')), 'meera-new-pass');
      await tester.enterText(find.byKey(const Key('password-again')), 'meera-new-pass');
      await tester.tap(find.byKey(const Key('password-save')));
      await tester.pumpAndSettle();
      expect(find.text('The current password is not right.'), findsOneWidget);
      expect(LocalStore.instance.authToken, 'token-before');

      await tester.enterText(find.byKey(const Key('password-again')), 'something-else');
      await tester.enterText(find.byKey(const Key('password-current')), 'k7mq-x2rw-9tpd');
      await tester.tap(find.byKey(const Key('password-save')));
      await tester.pumpAndSettle();
      expect(find.text('The two new passwords are not the same.'), findsOneWidget);

      await tester.enterText(find.byKey(const Key('password-again')), 'meera-new-pass');
      await tester.tap(find.byKey(const Key('password-save')));
      await tester.pumpAndSettle();
      expect(auth.lastBody, {'currentPassword': 'k7mq-x2rw-9tpd', 'newPassword': 'meera-new-pass'});
      expect(LocalStore.instance.authToken, 'token-after-change',
          reason: 'the server ended the old session; the next request needs the new token');
      expect(LocalStore.instance.authUser?['id'], 't_meera');
      expect(find.textContaining('Password changed.'), findsOneWidget);
      LocalStore.instance.clearAuth();
    });
  });
}
