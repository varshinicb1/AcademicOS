import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
  if (MediaQuery.of(context).size.width >= 800) return null;
  final openDrawer = _ShellDrawerScope.maybeOpenDrawerOf(context);
  if (openDrawer == null) return null;
  return IconButton(icon: const Icon(Icons.menu), tooltip: 'Menu', onPressed: openDrawer);
}

class _ShellDrawerScope extends InheritedWidget {
  final VoidCallback openDrawer;

  const _ShellDrawerScope({required this.openDrawer, required super.child});

  static VoidCallback? maybeOpenDrawerOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<_ShellDrawerScope>()?.openDrawer;

  @override
  bool updateShouldNotify(_ShellDrawerScope oldWidget) => openDrawer != oldWidget.openDrawer;
}

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  static final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  // Shared by the desktop NavigationRail and the mobile Drawer so the two
  // destination lists can't drift out of sync. There are 8 destinations —
  // too many for a Material NavigationBar (designed for 3-5, divides width
  // evenly with no overflow handling), which is why mobile uses a Drawer
  // instead of a bottom nav bar.
  static const _navItems = [
    (icon: Icons.menu_book_outlined, selectedIcon: Icons.menu_book, label: 'Syllabus'),
    (icon: Icons.assignment_outlined, selectedIcon: Icons.assignment, label: 'Assessments'),
    (icon: Icons.calendar_today_outlined, selectedIcon: Icons.calendar_today, label: 'Planner'),
    (icon: Icons.quiz_outlined, selectedIcon: Icons.quiz, label: 'Questions'),
    (icon: Icons.fact_check_outlined, selectedIcon: Icons.fact_check, label: 'Evaluate'),
    (icon: Icons.psychology_outlined, selectedIcon: Icons.psychology, label: 'Mastery'),
    (icon: Icons.insights_outlined, selectedIcon: Icons.insights, label: 'Teacher'),
    (icon: Icons.account_balance_outlined, selectedIcon: Icons.account_balance, label: 'Principal'),
  ];

  @override
  Widget build(BuildContext context) {
    // NavigationRail asserts labelType must be null/none when extended.
    final extended = MediaQuery.of(context).size.width >= 1000;
    final isMobile = MediaQuery.of(context).size.width < 800;
    final selectedIndex = _calculateSelectedIndex(context);
    return _ShellDrawerScope(
      openDrawer: () => _scaffoldKey.currentState?.openDrawer(),
      child: Scaffold(
      key: _scaffoldKey,
      drawer: isMobile
          ? Drawer(
              child: SafeArea(
                child: ListView(
                  padding: EdgeInsets.zero,
                  children: [
                    const SizedBox(height: 8),
                    for (var i = 0; i < _navItems.length; i++)
                      ListTile(
                        leading: Icon(i == selectedIndex ? _navItems[i].selectedIcon : _navItems[i].icon),
                        title: Text(_navItems[i].label),
                        selected: i == selectedIndex,
                        onTap: () {
                          Navigator.of(context).pop();
                          _onDestinationSelected(context, i);
                        },
                      ),
                    const Divider(),
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
            NavigationRail(
              extended: extended,
              selectedIndex: selectedIndex,
              onDestinationSelected: (index) => _onDestinationSelected(context, index),
              labelType: extended ? null : NavigationRailLabelType.all,
              leading: const SizedBox(height: 16),
              // Desktop had no way to reach /settings at all — the gear
              // button only existed in the <800px mobile AppBar, confirmed
              // by reading this file: nothing else references '/settings'
              // in the >=800px branch below.
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
                for (final item in _navItems)
                  NavigationRailDestination(
                    icon: Icon(item.icon),
                    selectedIcon: Icon(item.selectedIcon),
                    label: Text(item.label),
                  ),
              ],
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

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/syllabus')) return 0;
    if (location.startsWith('/assessment')) return 1;
    if (location.startsWith('/planner')) return 2;
    if (location.startsWith('/questions')) return 3;
    if (location.startsWith('/evaluation')) return 4;
    if (location.startsWith('/analytics/gaps')) return 6;
    if (location.startsWith('/analytics/school')) return 7;
    if (location.startsWith('/analytics')) return 5;
    return 0;
  }

  void _onDestinationSelected(BuildContext context, int index) {
    switch (index) {
      case 0:
        context.go('/syllabus');
        break;
      case 1:
        context.go('/assessment');
        break;
      case 2:
        context.go('/planner/daily');
        break;
      case 3:
        context.go('/questions');
        break;
      case 4:
        context.go('/evaluation');
        break;
      case 5:
        context.go('/analytics/mastery');
        break;
      case 6:
        context.go('/analytics/gaps');
        break;
      case 7:
        context.go('/analytics/school');
        break;
    }
  }
}