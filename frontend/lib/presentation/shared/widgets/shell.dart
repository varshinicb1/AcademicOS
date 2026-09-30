import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/session/current_session.dart';

/// Drop into any page's `AppBar(leading: shellLeading(context), ...)`.
///
/// Every route in app_router.dart is nested inside MainShell's ShellRoute, so
/// every page's own Scaffold+AppBar was stacking directly under MainShell's
/// own mobile AppBar — two full-height bars on every screen. MainShell no
/// longer renders its own AppBar; instead pages opt in to a hamburger button
/// via this helper, which only activates when there's a MainShell drawer to
/// open (mobile) and nothing to pop back to (a shell-root page, not a pushed
/// detail/create/review screen). Everywhere else it returns null, letting
/// Flutter's normal automatic leading (back button, or nothing) take over —
/// so desktop pages and pushed sub-pages are visually unchanged.
Widget? shellLeading(BuildContext context) {
  if (Navigator.canPop(context)) return null;
  return forceShellLeading(context);
}

/// Same as [shellLeading] but skips the canPop check — for shell-root pages
/// reached through a nested GoRoute (e.g. '/planner/daily' under '/planner'),
/// where go_router can leave a parent segment on the stack and canPop true
/// even though there's nowhere meaningful to go back to.
Widget? forceShellLeading(BuildContext context) {
  if (MediaQuery.of(context).size.width >= AppConstants.mobileBreakpoint) return null;
  final openDrawer = _ShellDrawerScope.maybeOpenDrawerOf(context);
  if (openDrawer == null) return null;
  return IconButton(
    icon: const Icon(Icons.menu),
    tooltip: 'Menu',
    // The only way to the navigation on a phone, and Material's default
    // leaves it 40 px square -- below the 44 px a thumb reliably hits
    // (Task 801). The AppBar gives its leading 56 px, so 48 fits.
    //
    // No visualDensity needed here, unlike the TextButton on the coverage
    // dashboard: _IconButtonDefaultsM3 pins visualDensity to `standard`
    // (icon_button.dart:1152), so a desktop browser's `compact` theme
    // density never reaches this minimum. Pinned by the desktop-density test
    // in test/responsive/navigation_shell_responsive_test.dart.
    style: IconButton.styleFrom(minimumSize: const Size(48, 48)),
    onPressed: openDrawer,
  );
}

class _ShellDrawerScope extends InheritedWidget {
  final VoidCallback openDrawer;

  const _ShellDrawerScope({required this.openDrawer, required super.child});

  static VoidCallback? maybeOpenDrawerOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<_ShellDrawerScope>()?.openDrawer;

  @override
  bool updateShouldNotify(_ShellDrawerScope oldWidget) => openDrawer != oldWidget.openDrawer;
}

/// One destination in the side navigation: [match] is the path prefix that
/// selects it (the longest match wins), [path] where a tap goes.
typedef NavItem = ({IconData icon, IconData selectedIcon, String label, String path, String match});

/// The destinations a role sees in the web console's side navigation.
///
/// Until 2026-09-30 every signed-in account saw the same ten, "Principal"
/// included, so a student or a parent on the web was shown teacher tools
/// that answered 403. Staff keep the full list (a teacher without the
/// principal's insights); a student and a parent get their own few. An
/// unknown role (the offline build, a test with no account) gets the staff
/// list, as before.
List<NavItem> navItemsFor(String role) {
  const staff = <NavItem>[
    (icon: Icons.today_outlined, selectedIcon: Icons.today, label: 'Today', path: '/home', match: '/home'),
    (icon: Icons.assignment_outlined, selectedIcon: Icons.assignment, label: 'Papers', path: '/assessment', match: '/assessment'),
    (icon: Icons.quiz_outlined, selectedIcon: Icons.quiz, label: 'Question bank', path: '/questions', match: '/questions'),
    (icon: Icons.fact_check_outlined, selectedIcon: Icons.fact_check, label: 'Evaluate', path: '/evaluation', match: '/evaluation'),
    (icon: Icons.calendar_today_outlined, selectedIcon: Icons.calendar_today, label: 'Planner', path: '/planner/daily', match: '/planner'),
    (icon: Icons.menu_book_outlined, selectedIcon: Icons.menu_book, label: 'Syllabus', path: '/syllabus', match: '/syllabus'),
    (icon: Icons.psychology_outlined, selectedIcon: Icons.psychology, label: 'Mastery', path: '/analytics/mastery', match: '/analytics'),
    (icon: Icons.insights_outlined, selectedIcon: Icons.insights, label: 'Class gaps', path: '/analytics/gaps', match: '/analytics/gaps'),
    (icon: Icons.account_balance_outlined, selectedIcon: Icons.account_balance, label: 'School insights', path: '/analytics/school', match: '/analytics/school'),
    (icon: Icons.school_outlined, selectedIcon: Icons.school, label: 'School', path: '/school', match: '/school'),
  ];
  switch (role) {
    case 'student':
      return const [
        (icon: Icons.today_outlined, selectedIcon: Icons.today, label: 'My day', path: '/school', match: '/school'),
        (icon: Icons.assignment_outlined, selectedIcon: Icons.assignment, label: 'Homework', path: '/school/my-homework', match: '/school/my-homework'),
        (icon: Icons.event_outlined, selectedIcon: Icons.event, label: 'Exams', path: '/school/my-exams', match: '/school/my-exams'),
        (icon: Icons.trending_up_outlined, selectedIcon: Icons.trending_up, label: 'Learning', path: '/school/my-learning', match: '/school/my-learning'),
        (icon: Icons.notifications_outlined, selectedIcon: Icons.notifications, label: 'Inbox', path: '/school/inbox', match: '/school/inbox'),
      ];
    case 'parent':
      return const [
        (icon: Icons.family_restroom_outlined, selectedIcon: Icons.family_restroom, label: 'Family', path: '/school/family', match: '/school'),
        (icon: Icons.notifications_outlined, selectedIcon: Icons.notifications, label: 'Inbox', path: '/school/inbox', match: '/school/inbox'),
      ];
    case 'teacher':
      return [for (final i in staff) if (i.path != '/analytics/school') i];
    default:
      return staff;
  }
}

/// The destination [location] belongs to: the longest [NavItem.match] it
/// starts with, else the first.
int navIndexFor(List<NavItem> items, String location) {
  var best = 0, bestLength = -1;
  for (var i = 0; i < items.length; i++) {
    final m = items[i].match;
    if ((location == m || location.startsWith('$m/')) && m.length > bestLength) {
      best = i;
      bestLength = m.length;
    }
  }
  return best;
}

/// The signed-in role, or '' when there is no local store to read it from
/// (a widget test that mounts the shell alone).
String _signedInRole() => Hive.isBoxOpen('academicos_cache') ? CurrentSession.role : '';

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  static final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    // NavigationRail asserts labelType must be null/none when extended.
    final extended = MediaQuery.of(context).size.width >= 1000;
    final isMobile = MediaQuery.of(context).size.width < AppConstants.mobileBreakpoint;
    // A phone-width drawer and a desktop rail list the same destinations;
    // there are too many for a Material NavigationBar (designed for 3-5).
    final items = navItemsFor(_signedInRole());
    final selectedIndex = navIndexFor(items, GoRouterState.of(context).uri.path);
    final line = Theme.of(context).colorScheme.outlineVariant;
    return _ShellDrawerScope(
      openDrawer: () => _scaffoldKey.currentState?.openDrawer(),
      child: Scaffold(
      key: _scaffoldKey,
      drawer: isMobile
          ? Drawer(
              child: SafeArea(
                child: ListView(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  children: [
                    for (var i = 0; i < items.length; i++)
                      ListTile(
                        leading: Icon(i == selectedIndex ? items[i].selectedIcon : items[i].icon),
                        title: Text(items[i].label),
                        selected: i == selectedIndex,
                        onTap: () {
                          Navigator.of(context).pop();
                          context.go(items[i].path);
                        },
                      ),
                    const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: Divider()),
                    ListTile(
                      leading: const Icon(Icons.settings_outlined),
                      title: const Text('Settings'),
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/settings');
                      },
                    ),
                  ],
                ),
              ),
            )
          : null,
      body: Row(
        children: [
          // Navigation Rail for desktop/wide screens
          if (!isMobile)
            DecoratedBox(
              decoration: BoxDecoration(border: Border(right: BorderSide(color: line))),
              child: NavigationRail(
                extended: extended,
                minExtendedWidth: 232,
                selectedIndex: selectedIndex,
                onDestinationSelected: (index) => context.go(items[index].path),
                labelType: extended ? null : NavigationRailLabelType.all,
                leading: const SizedBox(height: 16),
                // Desktop had no way to reach /settings at all — the gear
                // button only existed in the <800px mobile AppBar.
                trailing: Expanded(
                  child: Align(
                    alignment: Alignment.bottomCenter,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: IconButton(
                        icon: const Icon(Icons.settings_outlined),
                        tooltip: 'Settings',
                        onPressed: () => context.go('/settings'),
                      ),
                    ),
                  ),
                ),
                destinations: [
                  for (final item in items)
                    NavigationRailDestination(
                      icon: Icon(item.icon),
                      selectedIcon: Icon(item.selectedIcon),
                      label: Text(item.label),
                    ),
                ],
              ),
            ),

          // Main content — each page owns its own AppBar (via shellLeading()
          // for the hamburger button on mobile root pages), so MainShell no
          // longer renders a second one here.
          Expanded(child: child),
        ],
      ),
    ),
    );
  }
}
