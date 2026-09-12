import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'core/di/service_locator.dart';
import 'core/local_engine/app_lock.dart';
import 'core/local_engine/secure_box.dart';
import 'core/local_server/local_server_manager.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/theme_controller.dart';
import 'core/routing/app_router.dart';
import 'presentation/blocs/assessment_bloc.dart';

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

  runApp(const ProviderScope(child: AcademicOSApp()));
}

class AcademicOSApp extends ConsumerWidget {
  const AcademicOSApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    
    return MultiBlocProvider(
      // AssessmentBloc is the only bloc any page actually reads -- see the
      // long comment in service_locator.dart's initDependencies() for why
      // Scanner/Evaluation/Mastery/Analytics/Reports blocs were removed
      // from here rather than left registered-but-silently-unused.
      providers: [
        BlocProvider(create: (context) => sl<AssessmentBloc>()),
      ],
      child: ValueListenableBuilder<ThemeMode>(
        valueListenable: ThemeController.mode,
        builder: (context, themeMode, _) => MaterialApp.router(
        title: 'AcademicOS',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: themeMode,
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
            child: AppLockGate(child: child!),
          );
        },
        ),
      ),
    );
  }
}