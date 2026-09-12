import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../presentation/home/pages/home_page.dart';
import '../../presentation/syllabus/pages/syllabus_page.dart';
import '../../presentation/syllabus/pages/chapter_detail_page.dart';
import '../../presentation/planner/pages/daily_planner_page.dart';
import '../../presentation/question_bank/pages/question_bank_page.dart';
import '../../presentation/analytics/pages/mastery_dashboard.dart';
import '../../presentation/analytics/pages/gap_analysis.dart';
import '../../presentation/analytics/pages/principal_page.dart';
import '../../presentation/assessment/pages/assessment_create_page.dart';
import '../../presentation/assessment/pages/assessment_list_page.dart';
import '../../presentation/assessment/pages/assessment_review_page.dart';
import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import '../../presentation/evaluation/pages/evaluation_page.dart';
import '../../presentation/mobile_scan/pages/mobile_scan_page.dart';
import '../../presentation/mobile_scan/pages/scan_history_page.dart';
import '../../presentation/practice/pages/practice_session_page.dart';
import '../../presentation/schedule/pages/my_schedule_page.dart';
import '../../presentation/student/pages/student_schedule_page.dart';
import '../../presentation/settings/pages/settings_page.dart';
import '../../presentation/settings/pages/template_maker_page.dart';
import '../../presentation/settings/pages/profile_page.dart';
import '../../presentation/settings/pages/classes_page.dart';
import '../../presentation/settings/pages/legal_page.dart';
import '../../presentation/auth/pages/login_page.dart';
import '../../presentation/shared/widgets/shell.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/home',
    routes: [
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/home',
            name: 'home',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: HomePage(),
            ),
          ),
          GoRoute(
            path: '/syllabus',
            name: 'syllabus',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: SyllabusPage(),
            ),
            routes: [
              GoRoute(
                path: 'chapter/:chapterId',
                name: 'chapter-detail',
                builder: (context, state) {
                  final extra = state.extra as Map<String, dynamic>?;
                  return ChapterDetailPage(
                    chapterId: state.pathParameters['chapterId']!,
                    subject: extra?['subject'] as String? ?? 'Science',
                    grade: extra?['grade'] as int? ?? 10,
                    chapterName: extra?['chapterName'] as String? ?? '',
                  );
                },
              ),
            ],
          ),
          GoRoute(
            path: '/planner',
            name: 'planner',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: PlannerPage(),
            ),
            routes: [
              GoRoute(
                path: 'daily',
                name: 'daily-planner',
                pageBuilder: (context, state) => const NoTransitionPage(
                  child: DailyPlannerPage(),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/questions',
            name: 'questions',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: QuestionBankPage(),
            ),
          ),
          GoRoute(
            path: '/analytics',
            name: 'analytics',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: MasteryDashboard(),
            ),
            routes: [
              GoRoute(
                path: 'mastery',
                name: 'mastery-dashboard',
                pageBuilder: (context, state) {
                  final extra = state.extra as Map<String, dynamic>?;
                  return NoTransitionPage(
                    child: MasteryDashboard(studentId: extra?['studentId'] as String?),
                  );
                },
              ),
              GoRoute(
                path: 'gaps',
                name: 'gap-analysis',
                pageBuilder: (context, state) => NoTransitionPage(
                  child: GapAnalysisPage(
                    assessmentId: state.uri.queryParameters['assessment'] ?? '',
                  ),
                ),
              ),
              GoRoute(
                path: 'school',
                name: 'principal',
                pageBuilder: (context, state) => const NoTransitionPage(
                  child: PrincipalPage(),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/assessment',
            name: 'assessment-list',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: AssessmentListPage(),
            ),
            routes: [
              GoRoute(
                path: 'create',
                name: 'assessment-create',
                builder: (context, state) => const AssessmentCreatePage(),
              ),
              GoRoute(
                path: ':id',
                name: 'assessment-review',
                builder: (context, state) {
                  final extra = state.extra as Map<String, dynamic>?;
                  return AssessmentReviewPage(
                    assessmentId: state.pathParameters['id']!,
                    assessment: extra?['assessment'] as Assessment?,
                    paper: extra?['paper'] as GeneratedPaper?,
                    gaps: (extra?['gaps'] as List<String>?) ?? const [],
                    warnings: (extra?['warnings'] as List<String>?) ?? const [],
                  );
                },
              ),
            ],
          ),
          GoRoute(
            path: '/evaluation',
            name: 'evaluation-home',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: EvaluationPage(answerSheetId: 'stu_demo'),
            ),
          ),
          GoRoute(
            path: '/evaluation/:answerSheetId',
            name: 'evaluation',
            builder: (context, state) => EvaluationPage(
              answerSheetId: state.pathParameters['answerSheetId']!,
            ),
          ),
          GoRoute(
            path: '/my-schedule',
            name: 'my-schedule',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: MySchedulePage(),
            ),
          ),
          GoRoute(
            path: '/student/schedule',
            name: 'student-schedule',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: StudentSchedulePage(),
            ),
          ),
          GoRoute(
            path: '/scan',
            name: 'mobile-scan',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: MobileScanPage(),
            ),
          ),
          GoRoute(
            path: '/scan-history',
            name: 'scan-history',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ScanHistoryPage(),
            ),
          ),
          GoRoute(
            path: '/practice/:sessionId',
            name: 'practice',
            builder: (context, state) => PracticeSessionPage(
              sessionId: state.pathParameters['sessionId']!,
            ),
          ),
          GoRoute(
            path: '/settings',
            name: 'settings',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: SettingsPage(),
            ),
            routes: [
              GoRoute(
                path: 'template',
                name: 'template-maker',
                builder: (context, state) => const TemplateMakerPage(),
              ),
              GoRoute(
                path: 'profile',
                name: 'profile',
                builder: (context, state) => const ProfilePage(),
              ),
              GoRoute(
                path: 'classes',
                name: 'classes',
                builder: (context, state) => const ClassesPage(),
              ),
              GoRoute(
                path: 'legal/:doc',
                name: 'legal',
                builder: (context, state) => LegalPage(doc: state.pathParameters['doc']!),
              ),
              GoRoute(
                path: 'login',
                name: 'login',
                builder: (context, state) => const LoginPage(),
              ),
            ],
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'Page not found',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(state.error.toString()),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => context.go('/syllabus'),
              child: const Text('Go Home'),
            ),
          ],
        ),
      ),
    ),
  );
});
