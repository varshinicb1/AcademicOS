import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
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

/// The app bar of a page the navigation opens (a destination in
/// [navSectionsFor]): the menu on a phone and no back arrow on any screen.
///
/// The school workspace's pages are nested under '/school', so go_router
/// leaves the overview beneath each one: Flutter drew a back arrow to it, and
/// on a phone no page had the menu at all -- a student or parent could not
/// get from Today to their homework or exams except through the overview
/// (E2E run on production's commit, 2026-10-01). A page pushed over a
/// destination (a homework, an exam, a child's progress) keeps its back arrow
/// by using a plain [AppBar].
AppBar destinationAppBar(BuildContext context,
        {required Widget title, List<Widget>? actions, PreferredSizeWidget? bottom}) =>
    AppBar(
      leading: forceShellLeading(context),
      automaticallyImplyLeading: false,
      title: title,
      actions: actions,
      bottom: bottom,
    );

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

/// A group of destinations under an optional heading.
typedef NavSection = ({String? title, List<NavItem> items});

NavItem _item(IconData icon, IconData selected, String label, String path, [String? match]) =>
    (icon: icon, selectedIcon: selected, label: label, path: path, match: match ?? path);

final _inbox = _item(Icons.notifications_outlined, Icons.notifications, 'Inbox', '/school/inbox');

/// The web console's side navigation for a role, grouped.
///
/// Until 2026-10-01 the side navigation was the v2 teacher tools (a mastery
/// page that asked for a student id, class gaps that asked for an
/// assessment id, an assessment calendar called "Planner", bank coverage
/// called "Syllabus") while the v3 day-to-day pages -- my day, homework,
/// class progress, reviews, exams, the inbox and every principal tool -- sat
/// one level down as tiles under "School" (review 2026-10-01). It now lists
/// what each role actually uses, the same destinations as the School tiles
/// (presentation/workspace/workspace_page.dart). A teacher also sees the
/// admin tools the principal has given them ([grants], `/my-grants`).
///
/// An unknown role -- the offline build, which has no accounts and no
/// school server, or a test with no account -- keeps the pages that work on
/// the device.
List<NavSection> navSectionsFor(String role, {Set<String> grants = const {}}) {
  switch (role) {
    case 'principal':
      return [
        (title: null, items: [
          _item(Icons.space_dashboard_outlined, Icons.space_dashboard, 'Overview', '/school'),
          _item(Icons.assignment_outlined, Icons.assignment, 'Papers', '/assessment'),
          _item(Icons.rate_review_outlined, Icons.rate_review, 'Paper reviews', '/school/reviews'),
          _item(Icons.assessment_outlined, Icons.assessment, 'Term report', '/school/term-report'),
          _item(Icons.insights_outlined, Icons.insights, 'School insights', '/analytics/school'),
          _inbox,
        ]),
        (title: 'Run the school', items: [
          _item(Icons.event_note_outlined, Icons.event_note, 'Exams', '/school/exams'),
          _item(Icons.table_chart_outlined, Icons.table_chart, 'Timetable', '/school/timetable'),
          _item(Icons.menu_book_outlined, Icons.menu_book, 'Lesson plans', '/school/lesson-plans'),
          _item(Icons.how_to_reg_outlined, Icons.how_to_reg, 'Attendance and cover', '/school/cover'),
          _item(Icons.restore_outlined, Icons.restore, 'Periods owed', '/school/periods-owed'),
          _item(Icons.assignment_turned_in_outlined, Icons.assignment_turned_in, 'Homework', '/school/homework'),
          _item(Icons.trending_up_outlined, Icons.trending_up, 'Class progress', '/school/class-progress'),
          _item(Icons.library_books_outlined, Icons.library_books, 'Question bank', '/school/question-bank'),
        ]),
        (title: 'Setup', items: [
          // The principal's first task: teachers join only with a code issued here
          // (the admin console's Invite people). It was reachable only through
          // School insights or a bulk import (handover review, 2026-10-01).
          _item(Icons.person_add_alt_1_outlined, Icons.person_add_alt_1, 'Invite people', '/admin'),
          _item(Icons.admin_panel_settings_outlined, Icons.admin_panel_settings, 'Staff and access', '/school/grants'),
          _item(Icons.upload_file_outlined, Icons.upload_file, 'Import and export', '/school/import'),
          _item(Icons.badge_outlined, Icons.badge, 'School profile', '/school/school-profile'),
          _item(Icons.key_outlined, Icons.key, 'API keys', '/school/api-keys'),
        ]),
      ];
    case 'teacher':
      final admin = <NavItem>[
        if (grants.contains('leave'))
          _item(Icons.how_to_reg_outlined, Icons.how_to_reg, 'Attendance and cover', '/school/cover'),
        if (grants.contains('leave'))
          _item(Icons.restore_outlined, Icons.restore, 'Periods owed', '/school/periods-owed'),
        if (grants.contains('exams')) _item(Icons.event_note_outlined, Icons.event_note, 'Exams', '/school/exams'),
        if (grants.contains('timetable'))
          _item(Icons.table_chart_outlined, Icons.table_chart, 'Timetable', '/school/timetable'),
        if (grants.contains('timetable'))
          _item(Icons.menu_book_outlined, Icons.menu_book, 'Lesson plans', '/school/lesson-plans'),
        if (grants.contains('users'))
          _item(Icons.upload_file_outlined, Icons.upload_file, 'Import and export', '/school/import'),
        if (grants.contains('reports'))
          _item(Icons.assessment_outlined, Icons.assessment, 'Term report', '/school/term-report'),
        if (grants.contains('qbank_review'))
          _item(Icons.library_books_outlined, Icons.library_books, 'Review answers', '/school/question-bank'),
      ];
      return [
        (title: null, items: [
          _item(Icons.today_outlined, Icons.today, 'Today', '/home'),
          _item(Icons.calendar_view_week_outlined, Icons.calendar_view_week, 'My week', '/school/week'),
          _item(Icons.assignment_outlined, Icons.assignment, 'Papers', '/assessment'),
          _item(Icons.assignment_turned_in_outlined, Icons.assignment_turned_in, 'Homework', '/school/homework'),
          _item(Icons.fact_check_outlined, Icons.fact_check, 'Mark answer sheets', '/evaluation'),
          _item(Icons.trending_up_outlined, Icons.trending_up, 'Class progress', '/school/class-progress'),
          _inbox,
        ]),
        (title: 'Resources', items: [
          _item(Icons.quiz_outlined, Icons.quiz, 'Question bank', '/questions'),
          _item(Icons.rate_review_outlined, Icons.rate_review, 'Paper reviews', '/school/reviews'),
          _item(Icons.event_available_outlined, Icons.event_available, 'Exam duties', '/school/my-exams'),
          _item(Icons.event_busy_outlined, Icons.event_busy, 'Leave', '/school/my-day'),
        ]),
        if (admin.isNotEmpty) (title: 'Admin', items: admin),
      ];
    case 'student':
      return [
        (title: null, items: [
          _item(Icons.today_outlined, Icons.today, 'Today', '/school/today', '/school'),
          _item(Icons.calendar_view_week_outlined, Icons.calendar_view_week, 'My week', '/school/week'),
          _item(Icons.assignment_outlined, Icons.assignment, 'Homework', '/school/my-homework'),
          _item(Icons.trending_up_outlined, Icons.trending_up, 'Progress', '/school/my-learning'),
          _item(Icons.event_note_outlined, Icons.event_note, 'Exams', '/school/my-exams'),
          _inbox,
        ]),
      ];
    case 'parent':
      return [
        (title: null, items: [
          _item(Icons.family_restroom_outlined, Icons.family_restroom, 'My children', '/school/family', '/school'),
          _inbox,
        ]),
      ];
    default:
      return [
        (title: null, items: [
          _item(Icons.today_outlined, Icons.today, 'Today', '/home'),
          _item(Icons.assignment_outlined, Icons.assignment, 'Papers', '/assessment'),
          _item(Icons.quiz_outlined, Icons.quiz, 'Question bank', '/questions'),
          _item(Icons.fact_check_outlined, Icons.fact_check, 'Evaluate', '/evaluation'),
          _item(Icons.calendar_today_outlined, Icons.calendar_today, 'Planner', '/planner/daily', '/planner'),
          _item(Icons.menu_book_outlined, Icons.menu_book, 'Syllabus', '/syllabus'),
          _item(Icons.psychology_outlined, Icons.psychology, 'Mastery', '/analytics/mastery', '/analytics'),
          _item(Icons.insights_outlined, Icons.insights, 'Class gaps', '/analytics/gaps'),
          _item(Icons.account_balance_outlined, Icons.account_balance, 'School insights', '/analytics/school'),
          _item(Icons.school_outlined, Icons.school, 'School', '/school'),
        ]),
      ];
  }
}

/// Every destination of [navSectionsFor], in order.
List<NavItem> navItemsFor(String role, {Set<String> grants = const {}}) =>
    [for (final s in navSectionsFor(role, grants: grants)) ...s.items];

/// The destination [location] belongs to: the longest [NavItem.match] it
/// equals or sits under, or -1 when none does (a page reached another way,
/// such as a detail screen of a destination that is not listed).
int navIndexFor(List<NavItem> items, String location) {
  var best = -1, bestLength = -1;
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

/// A teacher's admin capabilities (`/my-grants`), fetched once per session
/// and shared by every shell build; empty until they arrive, or offline.
class _Grants {
  static final ValueNotifier<Set<String>> caps = ValueNotifier(const {});
  static String? _loadedFor;

  static void ensureLoaded(String role) {
    final user = Hive.isBoxOpen('academicos_cache') ? CurrentSession.userId : '';
    if (role != 'teacher' || user.isEmpty || _loadedFor == user || !GetIt.I.isRegistered<Dio>()) return;
    _loadedFor = user;
    GetIt.I<Dio>().get('/my-grants').then((r) {
      caps.value = ((r.data as Map)['capabilities'] as List).cast<String>().toSet();
    }, onError: (Object _) {
      // not-a-failure: without its grants a teacher sees no admin section; each admin page reports its own errors
      _loadedFor = null;
    });
  }
}

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  static final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isMobile = width < AppConstants.mobileBreakpoint;
    final role = _signedInRole();
    _Grants.ensureLoaded(role);
    return ValueListenableBuilder<Set<String>>(
      valueListenable: _Grants.caps,
      builder: (context, grants, _) {
        final sections = navSectionsFor(role, grants: role == 'teacher' ? grants : const {});
        final location = GoRouterState.of(context).uri.path;
        final items = [for (final s in sections) ...s.items];
        final selected = navIndexFor(items, location);
        return _ShellDrawerScope(
          openDrawer: () => _scaffoldKey.currentState?.openDrawer(),
          child: Scaffold(
            key: _scaffoldKey,
            drawer: isMobile
                ? Drawer(child: SafeArea(child: SideNav(sections: sections, selected: selected, inDrawer: true)))
                : null,
            body: Row(
              children: [
                if (!isMobile)
                  SideNav(sections: sections, selected: selected, compact: width < 1000),
                // Each page owns its own AppBar (shellLeading() gives it the
                // menu button on a phone), so the shell renders none.
                Expanded(child: child),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// The side navigation: the product mark, the role's grouped destinations
/// and Settings. Full width with labels on a laptop, icons with tooltips
/// between the phone breakpoint and 1000 px, and the same list in the
/// drawer on a phone. It scrolls, so a principal's fifteen destinations fit
/// a short window.
class SideNav extends StatelessWidget {
  const SideNav({super.key, required this.sections, required this.selected,
      this.compact = false, this.inDrawer = false});

  final List<NavSection> sections;
  final int selected;
  final bool compact;
  final bool inDrawer;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    var index = 0;
    final rows = <Widget>[];
    for (final s in sections) {
      if (s.title != null) {
        rows.add(compact
            ? Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Divider(indent: 16, endIndent: 16, color: colors.outlineVariant))
            : Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 12, 6),
                child: Text(s.title!, style: theme.textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant)),
              ));
      }
      for (final item in s.items) {
        final i = index++;
        rows.add(_NavRow(item: item, selected: i == selected, compact: compact, inDrawer: inDrawer));
      }
    }
    final settings = _NavRow(
      item: _item(Icons.settings_outlined, Icons.settings, 'Settings', '/settings'),
      selected: GoRouterState.of(context).uri.path.startsWith('/settings'),
      compact: compact,
      inDrawer: inDrawer,
    );
    final body = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: EdgeInsets.fromLTRB(compact ? 0 : 20, 18, 12, 14),
          child: Row(
            mainAxisAlignment: compact ? MainAxisAlignment.center : MainAxisAlignment.start,
            children: [
              Container(
                width: 28,
                height: 28,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: colors.primary, borderRadius: BorderRadius.circular(8)),
                child: Text('A', style: theme.textTheme.labelLarge?.copyWith(color: colors.onPrimary, fontWeight: FontWeight.w600)),
              ),
              if (!compact) ...[
                const SizedBox(width: 10),
                Text('AcademicOS', style: theme.textTheme.titleSmall),
              ],
            ],
          ),
        ),
        Expanded(child: ListView(padding: const EdgeInsets.symmetric(horizontal: 8), children: rows)),
        Padding(padding: const EdgeInsets.fromLTRB(8, 4, 8, 12), child: settings),
      ],
    );
    if (inDrawer) return body;
    // A Material, not a coloured box: the tiles paint their selection and
    // ink on it.
    return Material(
      color: colors.surface,
      child: Container(
        width: compact ? 72 : 232,
        decoration: BoxDecoration(border: Border(right: BorderSide(color: colors.outlineVariant))),
        child: body,
      ),
    );
  }
}

class _NavRow extends StatelessWidget {
  const _NavRow({required this.item, required this.selected, required this.compact, required this.inDrawer});

  final NavItem item;
  final bool selected;
  final bool compact;
  final bool inDrawer;

  void _go(BuildContext context) {
    if (inDrawer) Navigator.of(context).pop();
    context.go(item.path);
  }

  @override
  Widget build(BuildContext context) {
    final icon = Icon(selected ? item.selectedIcon : item.icon, size: 20);
    if (compact) {
      final colors = Theme.of(context).colorScheme;
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: IconButton(
          tooltip: item.label,
          isSelected: selected,
          style: IconButton.styleFrom(
            backgroundColor: selected ? colors.primaryContainer : null,
            foregroundColor: selected ? colors.onPrimaryContainer : colors.onSurfaceVariant,
            minimumSize: const Size(48, 44),
          ),
          icon: icon,
          onPressed: () => _go(context),
        ),
      );
    }
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: ListTile(
        dense: !inDrawer,
        leading: icon,
        minLeadingWidth: 20,
        horizontalTitleGap: 12,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12),
        title: Text(item.label),
        selected: selected,
        onTap: () => _go(context),
      ),
    );
  }
}
