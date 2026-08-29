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
// consistent with this whole test suite's "no fake data" rule. The one
// exception is AppDatabase: BlueprintRepositoryImpl/QuestionRepositoryImpl/
// PaperGenerationRepositoryImpl all require one, but `flutter analyze`
// confirms `_localDb` is an unused field in every one of them (this file's
// own repositories_impl.dart) -- so a real AppDatabase pointed at a real
// temp-dir path is constructed (never a mock), but since drift's
// LazyDatabase defers opening the native connection until first query, and
// nothing here ever queries it, no native sqlite3 binary is ever touched.
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'package:academicos/core/local_engine/local_api_client.dart';
import 'package:academicos/core/local_engine/local_pillar_api.dart';
import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/data/datasources/api/pillar_api.dart';
import 'package:academicos/data/datasources/local/app_database.dart';
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
  /// constructed directly instead of through GetIt. A fresh AppDatabase is
  /// built per call (see file header for why this is safe without native
  /// sqlite3) rather than shared, so tests stay independent.
  AssessmentBloc buildAssessmentBloc() {
    final apiClient = LocalApiClient();
    final localDb = AppDatabase(p.join(tmpDir.path, 'test_${DateTime.now().microsecondsSinceEpoch}.db'));

    final assessmentRepository = AssessmentRepositoryImpl(apiClient: apiClient);
    final blueprintRepository = BlueprintRepositoryImpl(apiClient: apiClient, localDb: localDb);
    final questionRepository = QuestionRepositoryImpl(apiClient: apiClient, localDb: localDb, cache: cacheBox);
    final paperRepository = PaperGenerationRepositoryImpl(apiClient: apiClient, localDb: localDb);

    return AssessmentBloc(
      createAssessment: CreateAssessmentUseCase(assessmentRepository, blueprintRepository),
      selectQuestions: SelectQuestionsUseCase(questionRepository),
      generatePaper: GeneratePaperUseCase(paperRepository),
      assessmentRepository: assessmentRepository,
      paperRepository: paperRepository,
    );
  }

  Future<void> dispose() async {
    await GetIt.instance.reset();
    await cacheBox.close();
    tmpDir.deleteSync(recursive: true);
  }
}

/// Wraps [child] the same way main.dart does: MaterialApp + (optionally) the
/// one real BlocProvider the app actually uses.
Widget wrapForTest(Widget child, {AssessmentBloc? bloc}) {
  final body = bloc != null
      ? BlocProvider<AssessmentBloc>.value(value: bloc, child: child)
      : child;
  return MaterialApp(home: body);
}
