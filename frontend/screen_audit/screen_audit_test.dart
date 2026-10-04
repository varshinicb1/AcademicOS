// Screen audit: every screen of each role, in the real app against a real backend.
//
// Not part of `flutter test` (it lives outside test/ on purpose): it needs a seeded local backend and
// writes files. Run it with
//
//   flutter test screen_audit/screen_audit_test.dart \
//     --dart-define=ACADEMICOS_API=http://127.0.0.1:8010/api/v1
//
// Environment:
//   SCREEN_AUDIT_OUT    where screenshots and report.json go        (default build/screen_audit)
//   SCREEN_AUDIT_ROLES  comma list of roles to walk                 (default principal,teacher,student,parent)
//   SCREEN_AUDIT_LOGINS a file of `role name email password` lines  (default ~/academicos-audit-school-logins.txt)
//   AUDIT_PW            a password that overrides the file's, for every role (or AUDIT_PW_PRINCIPAL etc.)
//
// For each role it signs in through the real AuthApi, then opens each screen through the real router at
// a desktop and a phone size, waits for the screen's own requests, and records: where the router landed,
// every request and its status, any text on screen that reads like an error, any layout exception, and a
// screenshot. It asserts nothing: the report is the output, read by a person.
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:academicos/core/di/service_locator.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/routing/app_router.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/data/repositories/assessment_repository_impl.dart';
import 'package:academicos/data/repositories/repositories_impl.dart';
import 'package:academicos/core/download/pdf_saver.dart';
import 'package:academicos/domain/repositories/repositories.dart';
import 'package:academicos/domain/usecases/assessment_usecases.dart';
import 'package:academicos/main.dart' show AcademicOSApp;
import 'package:academicos/presentation/blocs/assessment_bloc.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';

import '../test/support/real_di.dart' show FakePathProvider;

const _desktop = Size(1280, 900);
const _phone = Size(390, 844);

/// The screens each role opens, as paths the router understands. The principal's and teacher's lists are
/// the destinations in shell.dart's navigation plus the pages those lead to.
const _screens = <String, List<String>>{
  'principal': [
    '/home', '/school', '/assessment', '/assessment/build', '/school/exams', '/school/timetable',
    '/school/lesson-plans', '/school/cover', '/school/term-report', '/school/reviews', '/analytics/school',
    '/school/periods-owed', '/school/homework', '/school/class-progress', '/school/question-bank',
    '/school/setup', '/admin', '/admin?tab=calendar-setup', '/school/grants', '/school/school-profile',
    '/school/import', '/school/report-cards', '/school/inbox', '/school/guide', '/settings', '/settings/profile',
    '/settings/classes', '/settings/template',
  ],
  'teacher': [
    '/home', '/school', '/school/my-day', '/school/week', '/assessment', '/assessment/build',
    '/school/homework', '/evaluation', '/school/class-progress', '/questions', '/school/reviews',
    '/school/my-exams', '/school/inbox', '/school/guide', '/settings', '/settings/profile',
    '/settings/classes', '/scan', '/scan-history', '/analytics/mastery', '/my-schedule',
  ],
  'student': [
    '/school', '/school/today', '/school/week', '/school/my-homework', '/school/my-learning',
    '/school/my-exams', '/school/my-report-card', '/school/inbox', '/school/guide', '/settings',
    '/settings/profile',
  ],
  'parent': ['/school/family', '/school', '/school/inbox', '/school/guide', '/settings'],
};

/// Text that reads like a failure the person would see.
final _errorText = RegExp(
    r'went wrong|not found|forbidden|refus|can see only|error|failed|could not|couldn.t|exception|dioexception|'
    r'unauthori[sz]ed|not allowed|try again|null|undefined|\b(40[0-9]|50[0-9])\b',
    caseSensitive: false);

class _Call {
  final String method, path;
  final int? status;
  _Call(this.method, this.path, this.status);
  Map<String, Object?> toJson() => {'m': method, 'path': path, 'status': status};
}

final _calls = <_Call>[];

String _slug(String route) =>
    route.replaceAll(RegExp(r'[^A-Za-z0-9]+'), '_').replaceAll(RegExp(r'^_+|_+$'), '').toLowerCase().padLeft(1, 'x');

Map<String, (String, String)> _logins() {
  final file = File(Platform.environment['SCREEN_AUDIT_LOGINS'] ??
      '${Platform.environment['USERPROFILE'] ?? Platform.environment['HOME']}/academicos-audit-school-logins.txt');
  final out = <String, (String, String)>{};
  if (!file.existsSync()) return out;
  final rx = RegExp(r'^\s*(principal|teacher|student|parent)\s+.+?\s+(\S+@\S+)\s+(\S+)\s*$');
  for (final line in file.readAsLinesSync()) {
    final m = rx.firstMatch(line);
    if (m != null) out.putIfAbsent(m[1]!, () => (m[2]!, m[3]!));
  }
  return out;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final outDir = Directory(Platform.environment['SCREEN_AUDIT_OUT'] ?? 'build/screen_audit')..createSync(recursive: true);
  final roles = (Platform.environment['SCREEN_AUDIT_ROLES'] ?? 'principal,teacher,student,parent').split(',');
  final report = <Map<String, Object?>>[];
  late Directory tmp;
  final sl = GetIt.instance;

  setUpAll(() async {
    // The test binding replaces dart:io's HttpClient with one that answers 400 to everything.
    HttpOverrides.global = null;
    tmp = Directory.systemTemp.createTempSync('screen_audit_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
    PathProviderPlatform.instance = FakePathProvider(tmp);
    // ignore: invalid_use_of_visible_for_testing_member
    PackageInfo.setMockInitialValues(
        appName: 'AcademicOS', packageName: 'app', version: '1.0.0', buildNumber: '1', buildSignature: '');
    final loader = FontLoader('Inter');
    for (final w in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
      loader.addFont(rootBundle.load('assets/fonts/Inter-$w.ttf'));
    }
    await loader.load();
    // Without the icon font every icon is a box.
    final icons = FontLoader('MaterialIcons')..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
    await icons.load();

    registerNetworkClients(sl, offline: false);
    sl<Dio>().interceptors.add(InterceptorsWrapper(
      onResponse: (r, h) {
        _calls.add(_Call(r.requestOptions.method, r.requestOptions.path, r.statusCode));
        h.next(r);
      },
      onError: (e, h) {
        _calls.add(_Call(e.requestOptions.method, e.requestOptions.path, e.response?.statusCode));
        h.next(e);
      },
    ));
    sl.registerLazySingleton<PdfSaver>(() => PdfSaver.platform());
    sl.registerLazySingleton<ApiClient>(() => ApiClient(sl<Dio>()));
    sl.registerLazySingleton<PillarApi>(() => PillarApi(sl<Dio>()));
    sl.registerLazySingleton<AssessmentRepository>(() => AssessmentRepositoryImpl(apiClient: sl<ApiClient>()));
    sl.registerLazySingleton<BlueprintRepository>(() => BlueprintRepositoryImpl(apiClient: sl<ApiClient>()));
    sl.registerLazySingleton<QuestionRepository>(() => QuestionRepositoryImpl(apiClient: sl<ApiClient>()));
    sl.registerLazySingleton<PaperGenerationRepository>(() => PaperGenerationRepositoryImpl(apiClient: sl<ApiClient>()));
    // A factory: the app's BlocProvider closes the bloc when its screen goes, and each visit builds the app anew.
    sl.registerFactory(() => AssessmentBloc(
          createAssessment: CreateAssessmentUseCase(sl<AssessmentRepository>(), sl<BlueprintRepository>()),
          selectQuestions: SelectQuestionsUseCase(sl<QuestionRepository>()),
          generatePaper: GeneratePaperUseCase(sl<PaperGenerationRepository>()),
          assessmentRepository: sl<AssessmentRepository>(),
          paperRepository: sl<PaperGenerationRepository>(),
        ));
  });

  tearDownAll(() async {
    File('${outDir.path}/report.json').writeAsStringSync(const JsonEncoder.withIndent(' ').convert(report));
    try {
      await Hive.close().timeout(const Duration(seconds: 5));
    } catch (_) {
      // the known hive lock-queue flake on Windows
    }
  });

  Future<Map<String, Object?>> visit(WidgetTester tester, String role, String route, String sizeName, Size size) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1.0;
    final key = GlobalKey();
    final container = ProviderContainer();
    final router = container.read(appRouterProvider);
    final firstCall = _calls.length;
    final collected = <String>[];
    final previous = FlutterError.onError;
    FlutterError.onError = (details) => collected.add(details.exceptionAsString().split('\n').first);
    router.go(route);
    await tester.pumpWidget(RepaintBoundary(
        key: key, child: UncontrolledProviderScope(container: container, child: const AcademicOSApp())));
    // Real I/O needs real time; the widgets then need frames to show what came back.
    for (var i = 0; i < 4; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 600)));
      await tester.pump(const Duration(milliseconds: 100));
    }
    // A screen still showing a spinner has not finished loading (the shared local backend can be slow):
    // give it up to 20 more seconds so the screenshot shows the screen, not its loading state.
    for (var i = 0; i < 20 && find.byType(CircularProgressIndicator).evaluate().isNotEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 1)));
      await tester.pump(const Duration(milliseconds: 100));
    }
    await tester.pump(const Duration(milliseconds: 400));
    final landed = router.routerDelegate.currentConfiguration.uri.toString();

    final texts = <String>[
      for (final t in tester.widgetList<Text>(find.byType(Text)))
        if ((t.data ?? t.textSpan?.toPlainText() ?? '').trim().isNotEmpty) (t.data ?? t.textSpan!.toPlainText()).trim(),
    ];
    final errors = {for (final t in texts) if (_errorText.hasMatch(t)) t};
    final exception = tester.takeException();

    final file = '${outDir.path}/$role/${_slug(route)}_$sizeName.png';
    File(file).parent.createSync(recursive: true);
    try {
      final boundary = tester.renderObject<RenderRepaintBoundary>(find.byKey(key));
      final image = await tester.runAsync(() => boundary.toImage(pixelRatio: 1.0));
      final bytes = await tester.runAsync(() => image!.toByteData(format: ui.ImageByteFormat.png));
      File(file).writeAsBytesSync(Uint8List.view(bytes!.buffer));
    } catch (e) {
      File('$file.txt').writeAsStringSync('screenshot failed: $e');
    }

    final mine = _calls.sublist(firstCall);
    final entry = <String, Object?>{
      'role': role,
      'route': route,
      'size': sizeName,
      'landed': landed,
      'requests': mine.length,
      'failed': [for (final c in mine) if ((c.status ?? 0) >= 400 || c.status == null) c.toJson()],
      'errorTexts': errors.toList(),
      'exception': exception?.toString().split('\n').first,
      'shows': texts.take(14).toList(),
      'screenshot': file,
    };
    // Close the page and let its timers run out so the next screen starts clean.
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(minutes: 2));
    container.dispose();
    FlutterError.onError = previous;
    if (collected.isNotEmpty) entry['flutterErrors'] = collected.toSet().take(4).toList();
    return entry;
  }

  final logins = _logins();
  for (final role in roles) {
    testWidgets('screens as $role', (tester) async {
      final pw = Platform.environment['AUDIT_PW_${role.toUpperCase()}'] ??
          Platform.environment['AUDIT_PW'] ??
          logins[role]?.$2;
      final email = Platform.environment['AUDIT_EMAIL_${role.toUpperCase()}'] ?? logins[role]?.$1;
      expect(email != null && pw != null, isTrue, reason: 'no sign-in for $role: set SCREEN_AUDIT_LOGINS or AUDIT_PW');
      final result = await tester.runAsync(() => sl<AuthApi>().login(email: email!, password: pw!));
      LocalStore.instance.signIn(result!.token, result.user.toJson());
      for (final route in _screens[role]!) {
        for (final (name, size) in [('desktop', _desktop), ('phone', _phone)]) {
          final e = await visit(tester, role, route, name, size);
          report.add(e);
          final flags = [
            if (e['landed'] != route && !'${e['landed']}'.startsWith(route.split('?').first)) 'landed ${e['landed']}',
            if ((e['failed'] as List).isNotEmpty) '${(e['failed'] as List).length} failed',
            if ((e['errorTexts'] as List).isNotEmpty) 'text: ${(e['errorTexts'] as List).take(2)}',
            if (e['exception'] != null) 'EXC ${e['exception']}',
            if (e['flutterErrors'] != null) 'FLUTTER ${(e['flutterErrors'] as List).first}',
          ];
          // ignore: avoid_print
          print('AUDIT ${role.padRight(9)} ${name.padRight(7)} ${route.padRight(30)} ${flags.isEmpty ? 'ok' : flags.join(' | ')}');
        }
      }
      LocalStore.instance.clearAuth();
    }, timeout: const Timeout(Duration(minutes: 40)));
  }
}
