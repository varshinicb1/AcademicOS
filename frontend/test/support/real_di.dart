// Shared real (never mocked) dependency wiring for widget-level UI tests.
//
// Two pages this app actually ships (assessment_review_page.dart via
// _reopen(), daily_planner_page.dart, assessment_list_page.dart) read
// GetIt.I<ApiClient>() directly, and the one Bloc this app uses
// (AssessmentBloc, see service_locator.dart's long comment on why it's the
// only one) is provided at the widget tree root via BlocProvider, not GetIt,
// in the real app (main.dart). A widget test that exercises either path
// needs both wired to something real -- this file builds the exact same
// object graph service_locator.dart's initDependencies() builds, minus the
// GetIt registrations that file does for repositories/use-cases (those are
// constructed directly here, since only ApiClient/PillarApi are ever read
// via GetIt.I from a page -- see the audit comment in service_locator.dart).
//
// Every repository built here is a REAL implementation talking to a REAL
// LocalApiClient(), which reads/writes the REAL Hive-backed LocalStore --
// consistent with this whole test suite's "no fake data" rule.
//
// 2026-09-23: no AppDatabase is built any more. The three repositories that
// took one never read it (four unused-field warnings in repositories_impl.dart,
// now gone with the parameter), and this file had to construct, track and
// close a real drift database per test only to satisfy the constructor -- the
// same databases whose unclosed handles once cost a confirmed 12-minute hang
// in classes_page_test.dart's tearDownAll. Nothing to close means nothing to
// leak.
import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/core/local_engine/local_pillar_api.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/data/repositories/assessment_repository_impl.dart';
import 'package:academicos/data/repositories/repositories_impl.dart';
import 'package:academicos/domain/usecases/assessment_usecases.dart';
import 'package:academicos/presentation/blocs/assessment_bloc.dart';

class FakePathProvider extends PathProviderPlatform with MockPlatformInterfaceMixin {
  final Directory dir;
  FakePathProvider(this.dir);
  @override
  Future<String?> getApplicationDocumentsPath() async => dir.path;
}

/// Real Hive + fake-filesystem test environment, matching the pattern
/// already established in local_report_card_test.dart/local_scan_pdf_export_test.dart.
/// Call from setUpAll; call [RealTestEnv.dispose] from tearDownAll.
class RealTestEnv {
  final Directory tmpDir;
  final Box cacheBox;

  RealTestEnv._(this.tmpDir, this.cacheBox);

  static Future<RealTestEnv> init(String prefix) async {
    final tmpDir = Directory.systemTemp.createTempSync(prefix);
    Hive.init(tmpDir.path);
    final cacheBox = await Hive.openBox('academicos_cache');
    PathProviderPlatform.instance = FakePathProvider(tmpDir);
    return RealTestEnv._(tmpDir, cacheBox);
  }

  /// Registers real GetIt.I<ApiClient>()/GetIt.I<PillarApi>() as the same
  /// offline implementations the real APK uses -- required by any page that
  /// reads GetIt directly (assessment_review_page._reopen(), classes_page,
  /// mastery_dashboard, mobile_scan_page, etc.).
  void registerGetIt() {
    final sl = GetIt.instance;
    if (!sl.isRegistered<ApiClient>()) sl.registerLazySingleton<ApiClient>(() => LocalApiClient());
    if (!sl.isRegistered<PillarApi>()) sl.registerLazySingleton<PillarApi>(() => LocalPillarApi());
  }

  /// Builds a real AssessmentBloc wired to a real (offline) ApiClient --
  /// same object graph as service_locator.dart's initDependencies(), just
  /// constructed directly instead of through GetIt. A fresh one per call, so
  /// tests stay independent.
  AssessmentBloc buildAssessmentBloc() {
    final apiClient = LocalApiClient();

    final assessmentRepository = AssessmentRepositoryImpl(apiClient: apiClient);
    final blueprintRepository = BlueprintRepositoryImpl(apiClient: apiClient);
    final questionRepository = QuestionRepositoryImpl(apiClient: apiClient);
    final paperRepository = PaperGenerationRepositoryImpl(apiClient: apiClient);

    return AssessmentBloc(
      createAssessment: CreateAssessmentUseCase(assessmentRepository, blueprintRepository),
      selectQuestions: SelectQuestionsUseCase(questionRepository),
      generatePaper: GeneratePaperUseCase(paperRepository),
      assessmentRepository: assessmentRepository,
      paperRepository: paperRepository,
    );
  }

  // Real, root-caused flake: instrumented dispose() line-by-line to find it
  // (print output from a real hung run, not guessed) -- cacheBox.close() can
  // hang indefinitely. It never happens with this file run alone; it does
  // happen after some other real_di.dart-based test file already ran in the
  // same process (confirmed: right after assessment_review_page_test.dart).
  // Traced into the hive package itself: VM StorageBackend.close() runs
  // through a `_sync.syncReadWrite()` lock queue (hive-2.2.3's
  // storage_backend_vm.dart) -- if an earlier queued operation on that lock
  // is ever abandoned rather than completed, every later close() on it waits
  // forever for a turn that never comes. LocalStore hardcodes the box name
  // ('academicos_cache'), so a per-file unique box name isn't an option
  // here. Bounding the close with a timeout can't fix hive's internal lock,
  // but it stops one flaky close from taking the whole suite down with it.
  Future<void> dispose() async {
    await GetIt.instance.reset();
    try {
      await cacheBox.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('RealTestEnv.dispose(): cacheBox.close() did not return within 10s '
          '(known hive lock-queue flake) -- proceeding without it.');
    }
    try {
      tmpDir.deleteSync(recursive: true);
    } on FileSystemException {
      // A timed-out cacheBox.close() above (the same flake) means the box's
      // underlying file genuinely is still open, so Windows refuses this
      // delete -- a leaked OS temp directory is a real but minor cost, and
      // far better than failing (or hanging) the test over it.
      // ignore: avoid_print
      print('RealTestEnv.dispose(): could not delete $tmpDir (file still locked) -- leaving it behind.');
    }
  }
}

/// Wraps [child] the way main.dart does: MaterialApp + (optionally) the one
/// real BlocProvider the app actually uses.
///
/// [theme] defaults to Flutter's, which is *not* what main.dart ships -- the
/// callers here are checking behaviour (what a page does, what it calls),
/// and behaviour does not depend on padding. A caller measuring layout has
/// to pass AppTheme.lightTheme, because the shipped theme's button padding,
/// filled form fields and chip styles decide whether a row fits a phone
/// (test/responsive/responsive_harness.dart's appForTest).
Widget wrapForTest(Widget child, {AssessmentBloc? bloc, ThemeData? theme}) {
  final body = bloc != null
      ? BlocProvider<AssessmentBloc>.value(value: bloc, child: child)
      : child;
  return MaterialApp(theme: theme, home: body);
}
