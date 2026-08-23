import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'core/di/service_locator.dart';
import 'core/local_engine/demo_seeder.dart';
import 'core/local_engine/secure_box.dart';
import 'core/local_server/local_server_manager.dart';
import 'core/theme/app_theme.dart';
import 'core/routing/app_router.dart';
import 'presentation/blocs/assessment_bloc.dart';
import 'presentation/blocs/scanner_bloc.dart';
import 'presentation/blocs/evaluation_bloc.dart';
import 'presentation/blocs/mastery_bloc.dart';
import 'presentation/blocs/analytics_bloc.dart';
import 'presentation/blocs/reports_bloc.dart';

final sl = GetIt.instance;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // On a packaged Windows desktop build this launches the bundled local
  // backend and waits for it to answer, so the app is fully self-contained
  // on the user's machine -- no-op everywhere else (web/mobile keep using
  // whatever ACADEMICOS_API was set at build time).
  await LocalServerManager.ensureRunning();
  LocalServerManager.watchShutdownSignals();

  // Initialize Hive -- encrypted at rest (see secure_box.dart). This is the
  // box every real assessment/evaluation/mastery record in the offline
  // build lives in; a device with disk access previously saw plain JSON.
  await Hive.initFlutter();
  await SecureBox.openEncrypted('academicos_cache');

  // Initialize dependencies
  await initDependencies();

  // A brand-new offline install with zero data is the exact thing that
  // sinks a principal demo -- nothing to look at, and "generate your first
  // paper" as the very first thing a skeptical visitor sees is a bad pitch.
  // BUT a real Play-Store-bound release for actual schools must never show
  // synthetic seeded content as if it were a real class's data -- opt-in
  // only (a separate flag from ACADEMICOS_OFFLINE, off by default), for a
  // deliberate sales-demo build. A default install shows the app's real
  // honest empty state ("No assessments yet") instead.
  const offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
  const seedDemoData = bool.fromEnvironment('ACADEMICOS_SEED_DEMO', defaultValue: false);

  runApp(const ProviderScope(child: AcademicOSApp()));

  if (offlineMode && seedDemoData) {
    // Real fix for a real crash-on-open report on a demo-seed build: this
    // used to be `await`ed directly above, before runApp() -- so any
    // exception during seeding (5 real corpus-backed paper generations +
    // 50 real evaluations, exercised here for the first time in this exact
    // build configuration) crashed the app before a single frame ever
    // rendered, and even without an exception, that much synchronous work
    // ahead of the first frame risked looking like a hang/crash on cold
    // start. Seeding now runs after the UI is already up, with its own
    // error handling, so a slow or failed seed degrades to the app's real
    // empty state instead of an unusable launch.
    unawaited(Future(() async {
      try {
        await DemoSeeder.seedIfEmpty();
      } catch (e, stack) {
        debugPrint('DemoSeeder.seedIfEmpty failed (app continues normally): $e\n$stack');
      }
    }));
  }
}

class AcademicOSApp extends ConsumerWidget {
  const AcademicOSApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (context) => sl<AssessmentBloc>()),
        BlocProvider(create: (context) => sl<ScannerBloc>()),
        BlocProvider(create: (context) => sl<EvaluationBloc>()),
        BlocProvider(create: (context) => sl<MasteryBloc>()),
        BlocProvider(create: (context) => sl<AnalyticsBloc>()),
        BlocProvider(create: (context) => sl<ReportsBloc>()),
      ],
      child: MaterialApp.router(
        title: 'AcademicOS',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routerConfig: router,
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [
          Locale('en', ''),
          Locale('hi', ''),
          Locale('ta', ''),
          Locale('te', ''),
          Locale('bn', ''),
          Locale('mr', ''),
          Locale('gu', ''),
          Locale('kn', ''),
          Locale('ml', ''),
          Locale('or', ''),
          Locale('pa', ''),
          Locale('as', ''),
          Locale('ur', ''),
        ],
        builder: (context, child) {
          return MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(
                MediaQuery.of(context).textScaler.scale(1.0).clamp(0.85, 1.3),
              ),
            ),
            child: child!,
          );
        },
      ),
    );
  }
}