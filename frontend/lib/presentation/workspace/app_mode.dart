import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'ops_api.dart';
import 'strings.dart';

/// Which product this build is (M4, M5). One codebase, three online faces:
///
/// - the web console (default): the full admin and teaching navigation;
/// - the teacher app (`--dart-define=ACADEMICOS_APP=teacher`): my day,
///   homework, papers, reviews and the inbox in a phone's bottom bar;
/// - the student app (`--dart-define=ACADEMICOS_APP=student`): today,
///   homework, progress, exams and the inbox (a parent signs in to the same
///   app and lands on their children).
///
/// The offline Android build (`ACADEMICOS_OFFLINE`) is a separate product and
/// ignores this flag.
enum AppMode { console, teacher, student }

const _appModeName = String.fromEnvironment('ACADEMICOS_APP', defaultValue: '');

AppMode get appMode => switch (_appModeName) {
      'teacher' => AppMode.teacher,
      'student' => AppMode.student,
      _ => AppMode.console,
    };

/// Where an app build opens after sign-in.
String appHome(AppMode mode, {String role = ''}) => switch (mode) {
      AppMode.teacher => '/school/my-day',
      AppMode.student => role == 'parent' ? '/school/family' : '/school/my-homework',
      AppMode.console => '/home',
    };

typedef AppTab = ({IconData icon, IconData selected, String label, String path});

List<AppTab> appTabs(AppMode mode, {String role = ''}) => switch (mode) {
      AppMode.teacher => [
          (icon: Icons.today_outlined, selected: Icons.today, label: tr('My day'), path: '/school/my-day'),
          (icon: Icons.assignment_outlined, selected: Icons.assignment, label: tr('Homework'), path: '/school/homework'),
          (icon: Icons.description_outlined, selected: Icons.description, label: tr('Papers'), path: '/assessment'),
          (icon: Icons.notifications_outlined, selected: Icons.notifications, label: tr('Inbox'), path: '/school/inbox'),
          (icon: Icons.apps_outlined, selected: Icons.apps, label: tr('More'), path: '/school'),
        ],
      AppMode.student => role == 'parent'
          ? [
              (icon: Icons.family_restroom_outlined, selected: Icons.family_restroom, label: tr('Children'), path: '/school/family'),
              (icon: Icons.notifications_outlined, selected: Icons.notifications, label: tr('Inbox'), path: '/school/inbox'),
            ]
          : [
              (icon: Icons.today_outlined, selected: Icons.today, label: tr('Today'), path: '/student/schedule'),
              (icon: Icons.assignment_outlined, selected: Icons.assignment, label: tr('Homework'), path: '/school/my-homework'),
              (icon: Icons.insights_outlined, selected: Icons.insights, label: tr('Progress'), path: '/school/my-learning'),
              (icon: Icons.event_note_outlined, selected: Icons.event_note, label: tr('Exams'), path: '/school/my-exams'),
              (icon: Icons.notifications_outlined, selected: Icons.notifications, label: tr('Inbox'), path: '/school/inbox'),
            ],
      AppMode.console => <AppTab>[],
    };

/// The index of the tab a location belongs to: the longest tab path that
/// prefixes it ("/school/my-homework/abc" is Homework, not More).
int tabIndexFor(List<AppTab> tabs, String location) {
  var best = 0;
  var bestLen = -1;
  for (var i = 0; i < tabs.length; i++) {
    final p = tabs[i].path;
    if ((location == p || location.startsWith('$p/')) && p.length > bestLen) {
      best = i;
      bestLen = p.length;
    }
  }
  return best;
}

/// The phone shell of the teacher and student apps: the page, and a bottom
/// navigation bar of at most five tabs.
class AppModeShell extends StatelessWidget {
  final Widget child;
  final AppMode mode;
  final String role;
  const AppModeShell({super.key, required this.child, required this.mode, required this.role});

  @override
  Widget build(BuildContext context) {
    final tabs = appTabs(mode, role: role);
    if (tabs.length < 2) return child;
    final index = tabIndexFor(tabs, GoRouterState.of(context).uri.path);
    return Scaffold(
      body: Column(children: [const OfflineBanner(), Expanded(child: child)]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => context.go(tabs[i].path),
        destinations: [
          for (final t in tabs) NavigationDestination(icon: Icon(t.icon), selectedIcon: Icon(t.selected), label: t.label),
        ],
      ),
    );
  }
}
