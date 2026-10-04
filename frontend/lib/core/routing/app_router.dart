import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:get_it/get_it.dart';

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
import '../../presentation/paper_builder/pages/paper_builder_page.dart';
import '../../domain/entities/entities.dart';
import '../../domain/repositories/requests.dart';
import '../../presentation/evaluation/pages/evaluation_page.dart';
import '../../presentation/mobile_scan/pages/mobile_scan_page.dart';
import '../../presentation/mobile_scan/pages/scan_history_page.dart';
import '../../presentation/practice/pages/practice_session_page.dart';
import '../../presentation/schedule/pages/my_schedule_page.dart';
import '../../presentation/student/pages/student_schedule_page.dart';
import '../../presentation/parent/pages/parent_portal_page.dart';
import '../../presentation/admin/pages/principal_admin_page.dart';
import '../../presentation/settings/pages/settings_page.dart';
import '../../presentation/settings/pages/template_maker_page.dart';
import '../../presentation/settings/pages/profile_page.dart';
import '../../presentation/settings/pages/classes_page.dart';
import '../../presentation/settings/pages/legal_page.dart';
import '../../presentation/auth/pages/login_page.dart';
import '../../presentation/shared/widgets/shell.dart';
import '../../presentation/guide/guide_page.dart';
import '../../presentation/guide/guide_welcome.dart';
import '../../presentation/workspace/admin_pages.dart';
import '../../presentation/workspace/app_mode.dart';
import '../../presentation/workspace/class_progress_page.dart';
import '../../presentation/workspace/question_bank_console.dart';
import '../../presentation/workspace/term_report_page.dart';
import '../../presentation/workspace/cover_pages.dart';
import '../../presentation/workspace/exams_page.dart';
import '../../presentation/workspace/family_page.dart';
import '../../presentation/workspace/inbox_page.dart';
import '../../presentation/workspace/marks_page.dart';
import '../../presentation/workspace/practice_page.dart';
import '../../presentation/workspace/student_pages.dart';
import '../../presentation/workspace/student_today_page.dart';
import '../../presentation/workspace/teacher_homework.dart';
import '../../presentation/workspace/week_page.dart';
import '../../presentation/workspace/workspace_page.dart';
import '../../presentation/workspace/timetable_admin_page.dart';
import '../../presentation/workspace/lesson_plan_page.dart';
import '../../presentation/workspace/periods_owed_page.dart';
import '../../presentation/workspace/school_profile_page.dart';
import '../../presentation/onboarding/pages/setup_wizard_page.dart';
import '../../presentation/workspace/report_cards_page.dart';
import '../../presentation/workspace/owner_pages.dart';
import '../session/current_session.dart';
import '../local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final router = GoRouter(
    initialLocation: (const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false) ||
            LocalStore.instance.authToken != null)
        ? '/home'
        : '/login',
    redirect: (context, state) => authRedirect(
          state.matchedLocation,
          signedIn: LocalStore.instance.authToken != null,
          offlineBuild: const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false),
        ) ??
        pageForRole(
          state.matchedLocation,
          role: LocalStore.instance.authToken != null ? CurrentSession.role : '',
          offlineBuild: const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false),
        ) ??
        roleLanding(
          state.matchedLocation,
          role: LocalStore.instance.authToken != null ? CurrentSession.role : '',
          offlineBuild: const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false),
          mode: appMode,
        ),
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => LoginPage(
            inviteCode: state.uri.queryParameters['invite'],
            schoolId: state.uri.queryParameters['school']),
      ),
      ShellRoute(
        // The teacher and student app builds get a phone shell (app_mode.dart).
        // GuideWelcome greets a person the first time they sign in here.
        builder: (context, state, child) => GuideWelcome(
          child: appMode == AppMode.console
              ? MainShell(child: child)
              : AppModeShell(mode: appMode, role: CurrentSession.role, child: child),
        ),
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
          // School insights is a page of its own, not a child of '/analytics':
          // nested there, the Mastery dashboard was built underneath it on every
          // visit and asked for the demo student's knowledge, a 404 for every
          // real school (QA S-15). Declared first so '/analytics' does not
          // claim the path.
          GoRoute(
            path: '/analytics/school',
            name: 'principal',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: PrincipalPage(),
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
                redirect: (context, state) => legacyCreateRedirect(
                  offlineBuild: const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false),
                ),
                builder: (context, state) => const AssessmentCreatePage(),
              ),
              // The guided builder (Task 902): the teacher's main way to a
              // paper on the web build. `?quick=1` is "Quick paper (CBSE
              // pattern)" -- the builder with the class's CBSE preset chosen.
              // Declared before ':id' so "build" is never read as an id.
              GoRoute(
                path: 'build',
                name: 'paper-builder',
                builder: (context, state) =>
                    PaperBuilderPage(quick: state.uri.queryParameters['quick'] == '1'),
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
            path: '/parent',
            name: 'parent-portal',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ParentPortalPage(),
            ),
          ),
          // ROLE-4: an owner's schools side by side, before it opens one.
          GoRoute(
            path: '/owner',
            pageBuilder: (context, state) => const NoTransitionPage(child: OwnerOverviewPage()),
          ),
          // The school workspace: day-to-day tools per role (homework,
          // progress, parents, cover, exams, notifications, admin tools).
          GoRoute(
            path: '/school',
            name: 'school',
            pageBuilder: (context, state) => const NoTransitionPage(child: WorkspacePage()),
            routes: [
              GoRoute(path: 'inbox', builder: (context, state) => const InboxPage()),
              GoRoute(path: 'my-homework', builder: (context, state) => const MyHomeworkPage()),
              GoRoute(path: 'my-homework/:id',
                  builder: (context, state) => HomeworkDetailPage(homeworkId: state.pathParameters['id']!)),
              GoRoute(path: 'my-learning', builder: (context, state) => const LearningPage()),
              GoRoute(path: 'my-exams', builder: (context, state) => const MyExamsPage()),
              GoRoute(path: 'my-day', builder: (context, state) => const MyDayPage()),
              GoRoute(path: 'homework', builder: (context, state) => const TeacherHomeworkPage()),
              GoRoute(path: 'homework/:id',
                  builder: (context, state) => TeacherHomeworkDetailPage(homeworkId: state.pathParameters['id']!)),
              GoRoute(path: 'family', builder: (context, state) => const FamilyPage()),
              GoRoute(path: 'cover', builder: (context, state) => const CoverPage()),
              GoRoute(path: 'exams', builder: (context, state) => const ExamsPage()),
              GoRoute(path: 'reviews', builder: (context, state) => const ReviewsPage()),
              GoRoute(path: 'import', builder: (context, state) => const ImportPage()),
              // Question-bank API keys and their webhooks are the operator's, not a school's:
              // there is no school route to them. They are managed by the operator
              // through the server, not in this app.
              GoRoute(path: 'grants', builder: (context, state) => const GrantsPage()),
              GoRoute(path: 'timetable', builder: (context, state) => const TimetableAdminPage()),
              GoRoute(path: 'lesson-plans', builder: (context, state) => const LessonPlanPage()),
              GoRoute(path: 'periods-owed', builder: (context, state) => const PeriodsOwedPage()),
              GoRoute(path: 'school-profile', builder: (context, state) => const SchoolProfilePage()),
              GoRoute(path: 'setup', builder: (context, state) => const SetupWizardPage()),
              GoRoute(path: 'report-cards', builder: (context, state) => const ReportCardsPage()),
              GoRoute(path: 'my-report-card', builder: (context, state) =>
                  StudentReportCardPage(studentId: CurrentSession.userId, name: CurrentSession.name)),
              GoRoute(path: 'today', builder: (context, state) => const StudentTodayPage()),
              GoRoute(path: 'week', builder: (context, state) => const WeekPage()),
              GoRoute(path: 'class-progress', builder: (context, state) => const ClassProgressPage()),
              GoRoute(path: 'question-bank',
                  builder: (context, state) => QuestionBankConsolePage(canReview: state.uri.queryParameters['review'] == '1')),
              GoRoute(path: 'term-report', builder: (context, state) => const TermReportPage()),
              // The Guide: each role's common jobs, step by step (guide_page.dart).
              GoRoute(path: 'guide', builder: (context, state) => const GuidePage()),
              GoRoute(path: 'practice/:id',
                  builder: (context, state) => PracticePage(practiceId: state.pathParameters['id']!)),
              GoRoute(path: 'marks/:paperId',
                  builder: (context, state) => MarksPage(
                      paperId: state.pathParameters['paperId']!,
                      grade: (state.extra as Map<String, dynamic>?)?['grade'] as int?)),
            ],
          ),
          GoRoute(
            path: '/admin',
            name: 'principal-admin',
            // ?tab=calendar-setup opens Calendar & Setup, where terms are
            // declared: the link the time-saved guidance gives (audit D43).
            // Keyed by the tab, so the menu's Calendar and terms opens that
            // tab even from the console's other tabs (the page reads it once).
            builder: (context, state) => PrincipalAdminPage(
                key: ValueKey('admin:${state.uri.queryParameters['tab'] ?? ''}'),
                initialTab: state.uri.queryParameters['tab']),
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
              // Its own name: two routes named 'login' fail go_router's
              // duplicate-name assertion, so a debug build (and any test
              // that builds this router) could not start.
              GoRoute(
                path: 'login',
                // Not 'login' again: go_router asserts route names are
                // unique, so a debug build (and any test that builds this
                // router) failed before the first frame.
                name: 'settings-login',
                builder: (context, state) => LoginPage(
            inviteCode: state.uri.queryParameters['invite'],
            schoolId: state.uri.queryParameters['school']),
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
            const Icon(Icons.error_outline, size: 64, color: AppColors.danger),
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
  // Service_locator.dart's global session-keeper routes back to /settings/login
  // on a dead-session 401 via GetIt -- make this router reachable from there.
  // Guarded: this provider re-runs per ProviderScope (per widget test), and
  // GetIt is process-global -- re-registering would throw.
  if (!GetIt.instance.isRegistered<GoRouter>()) {
    GetIt.instance.registerSingleton<GoRouter>(router);
  }
  return router;
});

/// Where `/assessment/create` goes: on the web build, the guided builder.
///
/// The create screen carries the web's only Foundation/Standard/Advanced
/// control, and the bank judges no difficulty in any class 6-10 cell
/// (Task 125: tiersAvailable false in 14 of 14), so it offered three versions
/// that print the same paper; the builder says why no version is offered. It
/// was reachable on the web only by URL. The offline build keeps the screen:
/// it has no builder.
String? legacyCreateRedirect({required bool offlineBuild}) =>
    offlineBuild ? null : '/assessment/build';

/// Auth-gate decision for the router's `redirect` above. Returns the
/// location to send the user to, or null to stay where they are.
///
/// Rules:
/// - Offline (single-device) builds have no accounts: never redirect.
/// - Signed-out users may only be on the sign-in screen itself (both the
///   current `/login` and the legacy `/settings/login` the interceptor
///   used to target) or a legal doc; everywhere else bounces to `/login`
///   BEFORE any page fires an authenticated call -- no raw 401 screens.
/// - Signed-in users are never bounced anywhere by this function (the
///   login page navigates them home itself on success).
String? authRedirect(String location,
    {required bool signedIn, required bool offlineBuild}) {
  if (offlineBuild) return null;
  final isPublic = location == '/login' ||
      location == '/settings/login' ||
      location.startsWith('/settings/legal/');
  if (!signedIn) return isPublic ? null : '/login';
  return null;
}

/// The v2 pages that have a v3 replacement, and where a signed-in person on the web build
/// goes instead. They were not in any role's navigation but were open by address: the
/// syllabus, planner and mastery pages ask for a demo student or an assessment id and
/// show an error for a real school.
const _replacedPages = {
  '/syllabus': '/home',
  '/planner': '/home',
  '/planner/daily': '/home',
  '/analytics': '/home',
  '/analytics/gaps': '/home',
  '/student/schedule': '/school/week',
  '/parent': '/school/family',
};

/// Locations a student, and a parent, may open. Every other page is refused by the server
/// for them, so opening one showed a screen of errors with no way to tell why.
const _studentPages = [
  '/school/today', '/school/week', '/school/my-homework', '/school/my-learning', '/school/my-exams',
  '/school/my-report-card', '/school/inbox', '/school/guide', '/school/practice', '/practice', '/settings',
];
const _parentPages = [
  '/school/family', '/school/inbox', '/school/guide', '/school/my-exams', '/school/my-homework', '/settings',
];

/// What a teacher is never offered: the owner's overview, the principal's invitations and
/// the principal's staff permissions.
const _principalOnly = ['/owner', '/admin', '/school/grants'];

bool _under(String location, String page) => location == page || location.startsWith('$page/');

/// Sends a signed-in person away from a page that is not theirs, or that a newer page replaced,
/// to their own home ('/home', which [roleLanding] turns into the role's first page).
/// Null leaves them where they are. Offline builds have no accounts and no roles; an owner and
/// a signed-in person of unknown role are left alone.
String? pageForRole(String location, {required String role, required bool offlineBuild}) {
  if (offlineBuild || role.isEmpty) return null;
  final base = location.split('?').first;
  final replaced = _replacedPages[base];
  if (replaced != null) return replaced;
  switch (role) {
    case 'student':
      if (base == '/home' || base == '/school' || base == '/login') return null;
      return _studentPages.any((p) => _under(base, p)) ? null : '/home';
    case 'parent':
      if (base == '/home' || base == '/school' || base == '/login') return null;
      return _parentPages.any((p) => _under(base, p)) ? null : '/home';
    case 'teacher':
      return _principalOnly.any((p) => _under(base, p)) ? '/home' : null;
    case 'principal':
      return _under(base, '/owner') ? '/home' : null;
  }
  return null;
}

/// Where a signed-in parent or student lands instead of the teacher home:
/// a parent's children, a student's workspace. Everyone else, and every
/// other location, is left alone (null). Offline builds have no roles.
String? roleLanding(String location,
    {required String role, required bool offlineBuild, AppMode mode = AppMode.console}) {
  if (offlineBuild || location != '/home') return null;
  // The teacher and student apps open on their own first page.
  if (mode != AppMode.console && role.isNotEmpty) return appHome(mode, role: role);
  if (role == 'parent') return '/school/family';
  // An owner that has not opened one of its schools sees them all (ROLE-4).
  if (role == 'owner') return '/owner';
  if (role == 'student') return '/school';
  // The principal's first screen is the school at a glance (Overview), not
  // a teacher's day.
  if (role == 'principal') return '/school';
  return null;
}
