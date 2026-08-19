import 'package:get_it/get_it.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show kIsWeb, kDebugMode;
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

import '../../data/datasources/api/api_client.dart';
import '../../data/datasources/api/pillar_api.dart';
import '../../data/datasources/local/app_database.dart';
import '../local_engine/corpus_repository.dart';
import '../local_engine/local_api_client.dart';
import '../local_engine/local_pillar_api.dart';
import '../../data/repositories/assessment_repository_impl.dart';
import '../../data/repositories/repositories_impl.dart';
import '../../domain/repositories/repositories.dart';
import '../../domain/usecases/assessment_usecases.dart';
import '../../presentation/blocs/assessment_bloc.dart';
import '../../presentation/blocs/scanner_bloc.dart';
import '../../presentation/blocs/evaluation_bloc.dart';
import '../../presentation/blocs/mastery_bloc.dart';
import '../../presentation/blocs/analytics_bloc.dart';
import '../../presentation/blocs/reports_bloc.dart';

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
  
  // Dio
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
  sl.registerSingleton<Dio>(dio);

  // API Client
  // ACADEMICOS_OFFLINE=true is set only by the standalone-Android build --
  // routes every API call through the on-device engine (real corpus, real
  // paper-selection/evaluation algorithms ported from the Python backend,
  // see core/local_engine/) instead of Dio/HTTP. Every other build
  // (web, desktop, normal dev) is untouched by this flag and keeps talking
  // to a real server exactly as before.
  const offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
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
    () => BlueprintRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<QuestionRepository>(
    () => QuestionRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
      cache: sl<Box>(),
    ),
  );
  sl.registerLazySingleton<PaperGenerationRepository>(
    () => PaperGenerationRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<AnswerSheetRepository>(
    () => AnswerSheetRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<EvaluationRepository>(
    () => EvaluationRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<MasteryRepository>(
    () => MasteryRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<AnalyticsRepository>(
    () => AnalyticsRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<ReportRepository>(
    () => ReportRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<PracticeRepository>(
    () => PracticeRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  sl.registerLazySingleton<NotificationRepository>(
    () => NotificationRepositoryImpl(
      apiClient: sl<ApiClient>(),
      localDb: sl<AppDatabase>(),
    ),
  );
  
  // Use Cases
  sl.registerLazySingleton(() => CreateAssessmentUseCase(sl<AssessmentRepository>(), sl<BlueprintRepository>()));
  sl.registerLazySingleton(() => SelectQuestionsUseCase(sl<QuestionRepository>()));
  sl.registerLazySingleton(() => GeneratePaperUseCase(sl<PaperGenerationRepository>()));
  sl.registerLazySingleton(() => ScanAnswerSheetUseCase(sl<AnswerSheetRepository>()));
  sl.registerLazySingleton(() => EvaluateAnswerSheetUseCase(sl<EvaluationRepository>()));
  sl.registerLazySingleton(() => TeacherReviewUseCase(sl<EvaluationRepository>()));
  sl.registerLazySingleton(() => FinalizeEvaluationUseCase(sl<EvaluationRepository>(), sl<ReportRepository>(), sl<MasteryRepository>(), sl<NotificationRepository>()));
  sl.registerLazySingleton(() => GetStudentMasteryUseCase(sl<MasteryRepository>()));
  sl.registerLazySingleton(() => GetRecommendationsUseCase(sl<MasteryRepository>()));
  sl.registerLazySingleton(() => CreatePracticeSessionUseCase(sl<PracticeRepository>(), sl<MasteryRepository>()));
  sl.registerLazySingleton(() => SubmitPracticeUseCase(sl<PracticeRepository>(), sl<MasteryRepository>()));
  sl.registerLazySingleton(() => GetAssessmentAnalyticsUseCase(sl<AnalyticsRepository>()));
  sl.registerLazySingleton(() => GenerateStudentReportUseCase(sl<ReportRepository>()));
  sl.registerLazySingleton(() => SendWhatsAppNotificationUseCase(sl<NotificationRepository>()));
  
  // Blocs
  sl.registerLazySingleton(() => AssessmentBloc(
    createAssessment: sl<CreateAssessmentUseCase>(),
    selectQuestions: sl<SelectQuestionsUseCase>(),
    generatePaper: sl<GeneratePaperUseCase>(),
    assessmentRepository: sl<AssessmentRepository>(),
    paperRepository: sl<PaperGenerationRepository>(),
  ));
  sl.registerLazySingleton(() => ScannerBloc(scanAnswerSheetUseCase: sl<ScanAnswerSheetUseCase>()));
  sl.registerLazySingleton(() => EvaluationBloc(
    evaluateUseCase: sl<EvaluateAnswerSheetUseCase>(),
    reviewUseCase: sl<TeacherReviewUseCase>(),
    finalizeUseCase: sl<FinalizeEvaluationUseCase>(),
  ));
  sl.registerLazySingleton(() => MasteryBloc(
    getMastery: sl<GetStudentMasteryUseCase>(),
    getRecommendations: sl<GetRecommendationsUseCase>(),
    createPractice: sl<CreatePracticeSessionUseCase>(),
    submitPractice: sl<SubmitPracticeUseCase>(),
    masteryRepository: sl<MasteryRepository>(),
  ));
  sl.registerLazySingleton(() => AnalyticsBloc(
    getAssessmentAnalytics: sl<GetAssessmentAnalyticsUseCase>(),
    analyticsRepository: sl<AnalyticsRepository>(),
  ));
  sl.registerLazySingleton(() => ReportsBloc(
    generateStudentReport: sl<GenerateStudentReportUseCase>(),
    reportRepository: sl<ReportRepository>(),
  ));
}