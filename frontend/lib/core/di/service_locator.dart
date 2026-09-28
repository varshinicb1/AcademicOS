import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show kIsWeb, kDebugMode;
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

import '../../data/datasources/api/api_client.dart';
import '../../data/datasources/api/auth_api.dart';
import '../../data/datasources/api/consent_api.dart';
import '../../data/datasources/api/curriculum_api.dart';
import '../../data/datasources/api/paper_builder_api.dart';
import '../../data/datasources/api/pillar_api.dart';
import '../../data/datasources/local/app_database.dart';
import '../download/pdf_saver.dart';
import '../local_engine/corpus_repository.dart';
import '../local_engine/local_api_client.dart';
import '../local_engine/local_pillar_api.dart';
import '../local_engine/local_store.dart';
import '../../data/repositories/assessment_repository_impl.dart';
import '../../data/repositories/repositories_impl.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/usecases/assessment_usecases.dart';
import '../../presentation/blocs/assessment_bloc.dart';

final sl = GetIt.instance;

Future<void> initDependencies() async {
  // Core
  // path_provider has no web platform implementation registered in this project
  // (pubspec.lock has no path_provider_web) — getApplicationDocumentsDirectory()
  // throws on web before Flutter renders anything. Hive's web backend (IndexedDB)
  // doesn't need a filesystem path, and the local drift DB is unused on web (see
  // connection_web.dart), so skip path_provider entirely on web.
  String dbPath = 'academicos.db';
  if (kIsWeb) {
    await Hive.initFlutter();
  } else {
    final appDir = await getApplicationDocumentsDirectory();
    dbPath = p.join(appDir.path, 'academicos.db');
    await Hive.initFlutter(appDir.path);
  }

  // Database
  sl.registerLazySingleton<AppDatabase>(() => AppDatabase(dbPath));

  // Hive
  final cacheBox = await Hive.openBox('academicos_cache');
  sl.registerSingleton<Box>(cacheBox);
  
  const offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
  registerNetworkClients(sl, offline: offlineMode);
  // Where a downloaded paper / answer-key PDF goes: a browser download on
  // the web, the share sheet elsewhere (core/download/pdf_saver.dart).
  // Not a network client, so it stays outside registerNetworkClients().
  sl.registerLazySingleton<PdfSaver>(() => PdfSaver.platform());

  // API Client
  // ACADEMICOS_OFFLINE=true is set only by the standalone-Android build --
  // routes every API call through the on-device engine (real corpus, real
  // paper-selection/evaluation algorithms ported from the Python backend,
  // see core/local_engine/) instead of Dio/HTTP. Every other build
  // (web, desktop, normal dev) is untouched by this flag and keeps talking
  // to a real server exactly as before.
  if (offlineMode) {
    await CorpusRepository.instance.ensureLoaded();
    sl.registerLazySingleton<ApiClient>(() => LocalApiClient());
    sl.registerLazySingleton<PillarApi>(() => LocalPillarApi());
  } else {
    sl.registerLazySingleton<ApiClient>(() => ApiClient(sl<Dio>()));
    sl.registerLazySingleton<PillarApi>(() => PillarApi(sl<Dio>()));
  }
  
  // Repositories
  sl.registerLazySingleton<AssessmentRepository>(
    () => AssessmentRepositoryImpl(apiClient: sl<ApiClient>()),
  );
  sl.registerLazySingleton<BlueprintRepository>(
    () => BlueprintRepositoryImpl(apiClient: sl<ApiClient>()),
  );
  sl.registerLazySingleton<QuestionRepository>(
    () => QuestionRepositoryImpl(apiClient: sl<ApiClient>()),
  );
  sl.registerLazySingleton<PaperGenerationRepository>(
    () => PaperGenerationRepositoryImpl(apiClient: sl<ApiClient>()),
  );
  // 2026-09-17: AnswerSheetRepository, EvaluationRepository,
  // MasteryRepository, AnalyticsRepository, ReportRepository, and
  // NotificationRepository registrations removed -- their implementations
  // were deleted (every method called a backend route that never existed,
  // zero live callers through any path in either build; see
  // repositories_impl.dart's note). These were constructed at startup
  // (wasted lazy-singleton setup) but never resolved by anything, matching
  // the AssessmentBloc comment just below about the equivalent dead blocs.
  sl.registerLazySingleton<PracticeRepository>(
    () => PracticeRepositoryImpl(apiClient: sl<ApiClient>()),
  );

  // Use Cases
  sl.registerLazySingleton(() => CreateAssessmentUseCase(sl<AssessmentRepository>(), sl<BlueprintRepository>()));
  sl.registerLazySingleton(() => SelectQuestionsUseCase(sl<QuestionRepository>()));
  sl.registerLazySingleton(() => GeneratePaperUseCase(sl<PaperGenerationRepository>()));

  // Blocs
  //
  // AssessmentBloc is the only one actually consumed by the app -- every
  // page dispatches its events directly (see assessment_list_page.dart,
  // assessment_create_page.dart, assessment_review_page.dart,
  // daily_planner_page.dart). Scanner/Evaluation/Mastery/Analytics/Reports
  // blocs used to be registered here and provided in main.dart's
  // MultiBlocProvider, but no page has ever read any of them -- every
  // screen that does scanning, evaluation, mastery, analytics, or reports
  // work calls GetIt.I<PillarApi>() directly instead (see mobile_scan_page,
  // evaluation_page, mastery_dashboard, gap_analysis, classes_page). This
  // was confirmed independently twice: this file's own audit (grepped every
  // presentation file for each bloc's name -- zero hits outside the dead
  // bloc's own source) and docs/compliance.md's six-dimension audit ("D5",
  // 2026-08-19), which reached the same conclusion from the Python/route
  // side. Removed rather than left wired-but-unused, since a live-looking
  // BlocProvider for a feature that silently does nothing is exactly the
  // kind of dead end this app had too many of. Their UseCase/Repository
  // definitions in assessment_usecases.dart and repositories_impl.dart are
  // left in place as-is, just no longer constructed by anything.
  sl.registerLazySingleton(() => AssessmentBloc(
    createAssessment: sl<CreateAssessmentUseCase>(),
    selectQuestions: sl<SelectQuestionsUseCase>(),
    generatePaper: sl<GeneratePaperUseCase>(),
    assessmentRepository: sl<AssessmentRepository>(),
    paperRepository: sl<PaperGenerationRepository>(),
  ));
}

/// Registers the shared HTTP client and the Dio-backed APIs.
/// Extracted from initDependencies() so a test can build exactly this wiring
/// with `offline: true` -- the ACADEMICOS_OFFLINE flag is a compile-time
/// const, so without this seam the offline wiring could only be tested under
/// a dart-define the default `flutter test` run never passes.
/// [httpClientAdapter] replaces the transport, so a test can count the
/// requests that would have reached the network.
void registerNetworkClients(GetIt sl, {required bool offline, HttpClientAdapter? httpClientAdapter}) {
  // Port 8010 by default: 8000 is commonly taken by other local services.
  // Override at build time with --dart-define=ACADEMICOS_API=http://host:port/api/v1
  const apiBase = String.fromEnvironment(
    'ACADEMICOS_API',
    defaultValue: 'http://localhost:8010/api/v1',
  );
  // 90s not 30s: the deployed backend is on Render's free tier, which spins
  // the container down after ~15min idle — measured cold-start (pulling the
  // 3.3GB image + booting opencv/pymupdf) takes close to 60s, so 30s errored
  // out mid-boot. Once warm, real responses are ~1-2s.
  final dio = Dio(BaseOptions(
    baseUrl: apiBase,
    connectTimeout: const Duration(seconds: 90),
    receiveTimeout: const Duration(seconds: 90),
    headers: {'Content-Type': 'application/json'},
  ));
  // Full request/response bodies include real student names, answers, and
  // scores. Logging that in a distributed release build means it lands in
  // whatever OS/crash-reporting log capture is running on the machine this
  // is installed on -- fine for local dev, a real PII leak for a standalone
  // desktop build handed to a school. Debug-only.
  if (kDebugMode) {
    dio.interceptors.add(PrettyDioLogger(
      requestHeader: true,
      requestBody: true,
      responseHeader: false,
      responseBody: true,
      error: true,
    ));
  }
  // The real session keeper -- extracted as sessionInterceptor() (below) so
  // tests drive the exact production token-attach + 401-recovery logic
  // against a live backend instead of a copy of it.
  dio.interceptors.add(sessionInterceptor());
  // The 90s timeout above covers a cold Render container finishing boot, but
  // that's still a single roll of the dice: if the container spins down again
  // right before a request (rare, but real — e.g. a keep-alive-ping gap), the
  // user eats the full 90s wait and lands on a dead-end error screen even
  // though a near-immediate retry would now succeed, since the first attempt
  // already gave the cold start 90s to finish. One silent retry turns that
  // into a recovered request instead of a support ticket.
  const retryableTypes = {
    DioExceptionType.connectionTimeout,
    DioExceptionType.sendTimeout,
    DioExceptionType.receiveTimeout,
    DioExceptionType.connectionError,
  };
  dio.interceptors.add(QueuedInterceptorsWrapper(onError: (err, handler) async {
    final alreadyRetried = err.requestOptions.extra['retried'] == true;
    if (alreadyRetried || !retryableTypes.contains(err.type)) {
      return handler.next(err);
    }
    try {
      final opts = err.requestOptions..extra['retried'] = true;
      final response = await dio.fetch(opts);
      return handler.resolve(response);
    } catch (_) {
      return handler.next(err);
    }
  }));
  if (httpClientAdapter != null) dio.httpClientAdapter = httpClientAdapter;
  sl.registerSingleton<Dio>(dio);
  // Registered unconditionally (even in offline mode, where it's simply
  // never read) -- keeps this section's registration order matching every
  // other Dio-backed client below rather than special-casing one.
  sl.registerLazySingleton<AuthApi>(() => AuthApi(sl<Dio>()));
  // Same reasoning: the curriculum/schedule module has no offline-engine
  // counterpart yet (no local mirror of Topic/Subtopic/ScheduledLesson
  // data), so my_schedule_page.dart itself checks ACADEMICOS_OFFLINE
  // before ever calling this -- registered here anyway so the DI wiring
  // stays uniform rather than conditionally skipping one client.
  sl.registerLazySingleton<CurriculumApi>(() => CurriculumApi(sl<Dio>()));
  sl.registerLazySingleton<ConsentApi>(() => ConsentApi(sl<Dio>()));
  // The guided paper builder's template/availability/swap API. Server-only:
  // the offline build never routes to the builder (see newPaperLocation).
  sl.registerLazySingleton<PaperBuilderApi>(() => PaperBuilderApi(sl<Dio>()));
}

/// The app's session-keeping interceptor. Attaches the logged-in session
/// token (see auth_api.dart) to every request once one exists -- no
/// interceptor existed before this, so a logged-in caller's identity never
/// actually reached the server; every auth-gated route (principal-approve,
/// review/finalize's real reviewerId) depends on this running before the
/// request goes out. Its onError half is the global session keeper: the
/// server 401s (never 403) when the attached token is absent/expired -- at
/// that point the session is worthless, so it's cleared locally and the
/// user is sent back to Sign in instead of being stuck on a dead error
/// screen. A 403 is LEFT untouched: the token is still valid, the caller
/// just isn't allowed to do that thing.
InterceptorsWrapper sessionInterceptor() => InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = LocalStore.instance.authToken;
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (err, handler) {
        if (isDeadSession(err)) {
          bounceToLogin();
        }
        handler.next(err);
      },
    );

/// True when the server is telling us the attached session died -- a 401 on
/// any call whose whole point is being authenticated. The auth endpoints
/// themselves are the one exception: login/register legitimately return 401
/// for wrong credentials (and logout's 401, if any, needs no recovery), so
/// neither is a reason to wipe the session or bounce the screen -- a
/// teacher mid-form seeing "Incorrect email or password" then getting
/// shoved into Sign in again would be the wrong quarter.
bool isDeadSession(DioException err) {
  if (err.response?.statusCode != 401) return false;
  final path = err.requestOptions.path;
  return !(path == '/auth/login' || path == '/auth/register' || path == '/auth/logout');
}

/// Clears the dead session and routes back to the Sign in page. Guards on
/// having actually held a token: a 401 for an already-signed-out client
/// (nothing to clear, already on some public screen) must not hijack the
/// navigation. The router lookup is best-effort -- during early startup
/// initDependencies() builds this Dio before app_router.dart has registered
/// it, in which case the token is already cleared and the next user action
/// lands on the login flow anyway.
void bounceToLogin() {
  final hadToken = LocalStore.instance.authToken != null;
  LocalStore.instance.clearAuth();
  if (!hadToken) return;
  try {
    sl<GoRouter>().go('/login');
  } catch (_) {
    // Router not registered yet -- see docstring above.
  }
}