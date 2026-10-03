import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show ValueListenable;
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/session/current_session.dart';
import '../../../core/session/owner_session.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../guide/guide_page.dart';
import '../device_memory.dart';
import 'theme_toggle.dart';

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
///
/// Its last actions, for a signed-in person, are the light/dark toggle and
/// the Guide's question mark ([SignedInBarActions]); the Guide's own page
/// passes [guide] false.
AppBar destinationAppBar(BuildContext context,
        {required Widget title, List<Widget>? actions, PreferredSizeWidget? bottom, bool guide = true}) =>
    AppBar(
      leading: forceShellLeading(context),
      automaticallyImplyLeading: false,
      title: title,
      actions: [...?actions, SignedInBarActions(guide: guide)],
      bottom: bottom,
    );

/// The end of a signed-in page's app bar: the light/dark toggle
/// ([ThemeToggleButton]) and, unless [guide] is false, the Guide's question
/// mark. Nothing when no one is signed in to the online product (the offline
/// build, or a test that mounts a page alone).
class SignedInBarActions extends StatelessWidget {
  const SignedInBarActions({super.key, this.guide = true});

  final bool guide;

  @override
  Widget build(BuildContext context) {
    if (!guideAvailableFor(signedInRole())) return const SizedBox.shrink();
    return Row(mainAxisSize: MainAxisSize.min, children: [
      const ThemeToggleButton(),
      if (guide) const GuideButton(),
    ]);
  }
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
/// selects it (the longest match wins), [path] where a tap goes. A [match]
/// with a query ('/admin?tab=calendar-setup') selects only that exact
/// location.
typedef NavItem = ({IconData icon, IconData selectedIcon, String label, String path, String match});

/// A group of destinations under an optional heading. A [collapsible] group
/// folds away behind its heading; [openByDefault] is how it starts on a
/// device that has not opened or closed it yet (SideNav remembers).
typedef NavSection = ({String? title, List<NavItem> items, bool collapsible, bool openByDefault});

NavItem _item(IconData icon, IconData selected, String label, String path, [String? match]) =>
    (icon: icon, selectedIcon: selected, label: label, path: path, match: match ?? path);

/// The destinations always on show, under no heading.
NavSection _core(List<NavItem> items) => (title: null, items: items, collapsible: false, openByDefault: true);

/// A group that folds away behind its heading.
NavSection _group(String title, List<NavItem> items, {bool open = false}) =>
    (title: title, items: items, collapsible: true, openByDefault: open);

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
///
/// The principal's list was eighteen destinations under three headings, and
/// the first school to use it found it confusing ("too many options",
/// 2026-10-01). It now shows the eight pages a principal uses every week,
/// with the rest folded under More and Setup; every page is still listed.
/// A teacher's is folded the same way.
List<NavSection> navSectionsFor(String role, {Set<String> grants = const {}}) {
  switch (role) {
    case 'principal':
      return [
        _core([
          _item(Icons.space_dashboard_outlined, Icons.space_dashboard, 'Overview', '/school'),
          _item(Icons.assignment_outlined, Icons.assignment, 'Papers', '/assessment'),
          _item(Icons.event_note_outlined, Icons.event_note, 'Exams', '/school/exams'),
          _item(Icons.table_chart_outlined, Icons.table_chart, 'Timetable', '/school/timetable'),
          _item(Icons.menu_book_outlined, Icons.menu_book, 'Lesson plans', '/school/lesson-plans'),
          _item(Icons.how_to_reg_outlined, Icons.how_to_reg, 'Attendance and cover', '/school/cover'),
          _item(Icons.assessment_outlined, Icons.assessment, 'Term report', '/school/term-report'),
          _inbox,
        ]),
        _group('More', [
          _item(Icons.rate_review_outlined, Icons.rate_review, 'Paper reviews', '/school/reviews'),
          _item(Icons.insights_outlined, Icons.insights, 'School insights', '/analytics/school'),
          _item(Icons.restore_outlined, Icons.restore, 'Periods owed', '/school/periods-owed'),
          _item(Icons.assignment_turned_in_outlined, Icons.assignment_turned_in, 'Homework', '/school/homework'),
          _item(Icons.trending_up_outlined, Icons.trending_up, 'Class progress', '/school/class-progress'),
          _item(Icons.library_books_outlined, Icons.library_books, 'Question bank', '/school/question-bank'),
        ]),
        _group('Setup', [
          // The guided setup (onboarding/pages/setup_wizard_page.dart): the whole
          // first-run in one flow, reopenable any time.
          _item(Icons.auto_fix_high_outlined, Icons.auto_fix_high, 'Set up your school', '/school/setup'),
          // The principal's first task: teachers join only with a code issued here
          // (the admin console's Invite people). It was reachable only through
          // School insights or a bulk import (handover review, 2026-10-01).
          _item(Icons.person_add_alt_1_outlined, Icons.person_add_alt_1, 'Invite people', '/admin'),
          _item(Icons.admin_panel_settings_outlined, Icons.admin_panel_settings, 'Staff and access', '/school/grants'),
          _item(Icons.badge_outlined, Icons.badge, 'School profile', '/school/school-profile'),
          _item(Icons.upload_file_outlined, Icons.upload_file, 'Import and export', '/school/import'),
          // The calendar rules, terms, period length and holidays: the admin
          // console's Calendar & Setup tab, until now reached only by its tab.
          _item(Icons.calendar_month_outlined, Icons.calendar_month, 'Calendar and terms',
              '/admin?tab=calendar-setup'),
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
        _core([
          _item(Icons.today_outlined, Icons.today, 'Today', '/home'),
          // The day's periods, lessons to mark taught, cover asked of the
          // teacher and their leave: the teacher app's first tab. It was
          // listed as "Leave", which is one card on it.
          _item(Icons.wb_sunny_outlined, Icons.wb_sunny, 'My day', '/school/my-day'),
          _item(Icons.calendar_view_week_outlined, Icons.calendar_view_week, 'My week', '/school/week'),
          _item(Icons.assignment_outlined, Icons.assignment, 'Papers', '/assessment'),
          _item(Icons.assignment_turned_in_outlined, Icons.assignment_turned_in, 'Homework', '/school/homework'),
          _item(Icons.fact_check_outlined, Icons.fact_check, 'Mark answer sheets', '/evaluation'),
          _item(Icons.trending_up_outlined, Icons.trending_up, 'Class progress', '/school/class-progress'),
          _inbox,
        ]),
        _group('More', [
          _item(Icons.quiz_outlined, Icons.quiz, 'Question bank', '/questions'),
          _item(Icons.rate_review_outlined, Icons.rate_review, 'Paper reviews', '/school/reviews'),
          _item(Icons.event_available_outlined, Icons.event_available, 'Exam duties', '/school/my-exams'),
        ]),
        // What the principal handed this teacher: open until they fold it.
        if (admin.isNotEmpty) _group('Admin', admin, open: true),
      ];
    case 'student':
      return [
        _core([
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
        _core([
          _item(Icons.family_restroom_outlined, Icons.family_restroom, 'My children', '/school/family', '/school'),
          _inbox,
        ]),
      ];
    case 'owner':
      // ROLE-4, before the owner has chosen a school: its schools side by
      // side. Choosing one (the switcher above the navigation) makes it that
      // school's principal, with the principal's navigation.
      return [
        _core([
          _item(Icons.domain_outlined, Icons.domain, 'All schools', '/owner'),
        ]),
      ];
    default:
      return [
        _core([
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
///
/// [location] may carry a query: it then picks a destination whose match
/// names that query exactly, and otherwise is read by its path alone.
int navIndexFor(List<NavItem> items, String location) {
  final q = location.indexOf('?');
  final path = q < 0 ? location : location.substring(0, q);
  var best = -1, bestLength = -1;
  for (var i = 0; i < items.length; i++) {
    final m = items[i].match;
    final hit = m.contains('?') ? location == m : (path == m || path.startsWith('$m/'));
    if (hit && m.length > bestLength) {
      best = i;
      bestLength = m.length;
    }
  }
  return best;
}

/// The signed-in role, or '' when there is no local store to read it from
/// (a widget test that mounts the shell alone).
String signedInRole() => Hive.isBoxOpen('academicos_cache') ? CurrentSession.role : '';

/// An owner over several schools (ROLE-4); false with no local store.
bool _signedInIsOwner() => Hive.isBoxOpen('academicos_cache') && CurrentSession.isOwner;

/// The signed-in teacher's admin capabilities (`/my-grants`), loaded once per
/// session; empty until they arrive, offline, and for every other role. A
/// page that offers an admin's action -- the exams admin's changes to a
/// colleague's paper -- reads them here instead of asking the server again.
ValueListenable<Set<String>> myGrants() {
  // The offline build has no accounts and asks no server.
  if (!const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false)) {
    _Grants.ensureLoaded(signedInRole());
  }
  return _Grants.caps;
}

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
    return ValueListenableBuilder<int>(
      valueListenable: OwnerSession.switched,
      builder: (context, _, __) => _build(context, width, isMobile),
    );
  }

  Widget _build(BuildContext context, double width, bool isMobile) {
    final role = signedInRole();
    final owner = _signedInIsOwner();
    _Grants.ensureLoaded(role);
    return ValueListenableBuilder<Set<String>>(
      valueListenable: _Grants.caps,
      builder: (context, grants, _) {
        final sections = navSectionsFor(role, grants: role == 'teacher' ? grants : const {});
        final uri = GoRouterState.of(context).uri;
        final items = [for (final s in sections) ...s.items];
        final selected = navIndexFor(items, uri.toString());
        return _ShellDrawerScope(
          openDrawer: () => _scaffoldKey.currentState?.openDrawer(),
          child: Scaffold(
            key: _scaffoldKey,
            drawer: isMobile
                ? Drawer(child: SafeArea(child: SideNav(sections: sections, selected: selected, inDrawer: true,
                    schoolSwitcher: owner)))
                : null,
            body: Row(
              children: [
                if (!isMobile)
                  SideNav(sections: sections, selected: selected, compact: width < 1000, schoolSwitcher: owner),
                // Each page owns its own AppBar (shellLeading() gives it the
                // menu button on a phone), so the shell renders none.
                //
                // A semantics container of its own: every page route in
                // the nested navigator lays a modal barrier, which blocks
                // the semantics of whatever was painted before it in the
                // same container -- the whole desktop sidebar. A screen
                // reader found no Papers, Question bank or any other item
                // there; the phone's drawer, a route of its own, was fine
                // (QA P-28, S-22).
                Expanded(child: Semantics(container: true, child: child)),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Whether a collapsible menu group is open on this device: what the person
/// last chose, or the group's default ([NavSection.openByDefault]).
abstract final class NavGroups {
  static String _key(String title) => 'nav_group_open:$title';

  static bool isOpen(NavSection s) => DeviceMemory.read(_key(s.title!)) as bool? ?? s.openByDefault;

  static void setOpen(NavSection s, bool open) => DeviceMemory.write(_key(s.title!), open);
}

/// The side navigation: the product mark, the role's grouped destinations
/// and Settings. Full width with labels on a laptop, icons with
/// tooltips between the phone breakpoint and 1000 px, and the same list in
/// the drawer on a phone. It scrolls, so a long list fits a short window.
///
/// A collapsible group ([NavSection.collapsible]) shows only its heading
/// until it is opened, and the device remembers it open or closed. A group
/// holding the page on screen opens by itself, so the selected destination
/// is never hidden by a fold the person did not make on this page.
class SideNav extends StatefulWidget {
  const SideNav({super.key, required this.sections, required this.selected,
      this.compact = false, this.inDrawer = false, this.schoolSwitcher = false});

  final List<NavSection> sections;
  final int selected;
  final bool compact;
  final bool inDrawer;

  /// Show the owner's school switcher under the product mark (ROLE-4). Only
  /// an owner account gets it.
  final bool schoolSwitcher;

  @override
  State<SideNav> createState() => _SideNavState();
}

class _SideNavState extends State<SideNav> {
  /// Groups closed here while they hold the page on screen: kept closed
  /// until the page changes, instead of springing open again.
  final Set<String> _closedHere = {};

  @override
  void didUpdateWidget(SideNav old) {
    super.didUpdateWidget(old);
    if (old.selected != widget.selected) _closedHere.clear();
  }

  void _toggle(NavSection s, bool open) {
    setState(() {
      NavGroups.setOpen(s, !open);
      if (open) {
        _closedHere.add(s.title!);
      } else {
        _closedHere.remove(s.title!);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final compact = widget.compact, inDrawer = widget.inDrawer, selected = widget.selected;
    var index = 0;
    final rows = <Widget>[];
    for (final s in widget.sections) {
      final first = index;
      index += s.items.length;
      if (s.collapsible) {
        final holdsPage = selected >= first && selected < index;
        final open = NavGroups.isOpen(s) || (holdsPage && !_closedHere.contains(s.title));
        rows.add(_NavGroupHeader(
            title: s.title!, open: open, compact: compact, inDrawer: inDrawer, onToggle: () => _toggle(s, open)));
        if (!open) continue;
      } else if (s.title != null) {
        rows.add(compact
            ? Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Divider(indent: 16, endIndent: 16, color: colors.outlineVariant))
            : Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 12, 6),
                child: Text(s.title!, style: theme.textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant)),
              ));
      }
      for (var i = 0; i < s.items.length; i++) {
        rows.add(_NavRow(item: s.items[i], selected: first + i == selected, compact: compact, inDrawer: inDrawer));
      }
    }
    final location = GoRouterState.of(context).uri.path;
    final settings = _NavRow(
      item: _item(Icons.settings_outlined, Icons.settings, 'Settings', '/settings'),
      selected: location.startsWith('/settings'),
      compact: compact,
      inDrawer: inDrawer,
    );
    final guideRow = guideAvailableFor(signedInRole())
        ? _NavRow(
            item: _item(Icons.help_outline, Icons.help, 'Guide', guidePath),
            selected: GoRouterState.of(context).uri.path == guidePath,
            compact: compact,
            inDrawer: inDrawer,
          )
        : null;
    final body = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: EdgeInsets.fromLTRB(compact ? 0 : 20, 18, 12, 14),
          child: Row(
            mainAxisAlignment: compact ? MainAxisAlignment.center : MainAxisAlignment.start,
            children: [
              // The AcademicOS mark: the open book with the sun rising from its
              // spine (brand_logo/, the small variant drawn for 16-48 px).
              Image.asset('assets/brand/academicos_mark_small.png',
                  width: 30, height: 30, filterQuality: FilterQuality.medium, semanticLabel: 'AcademicOS'),
              if (!compact) ...[
                const SizedBox(width: 10),
                Text('AcademicOS', style: theme.textTheme.titleSmall),
              ],
            ],
          ),
        ),
        if (widget.schoolSwitcher)
          Padding(
            padding: EdgeInsets.fromLTRB(compact ? 4 : 12, 0, compact ? 4 : 12, 8),
            child: SchoolSwitcher(compact: compact, inDrawer: inDrawer),
          ),
        Expanded(child: ListView(padding: const EdgeInsets.symmetric(horizontal: 8), children: rows)),
        if (guideRow != null) Padding(padding: const EdgeInsets.fromLTRB(8, 4, 8, 0), child: guideRow),
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

/// The heading of a collapsible menu group: its name and a chevron, which
/// opens or folds the group. Between the phone breakpoint and 1000 px (icons
/// only) it is a chevron button named after the group.
class _NavGroupHeader extends StatelessWidget {
  const _NavGroupHeader({required this.title, required this.open, required this.compact, required this.inDrawer,
      required this.onToggle});

  final String title;
  final bool open;
  final bool compact;
  final bool inDrawer;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final chevron = Icon(open ? Icons.expand_less : Icons.expand_more, size: 20);
    if (compact) {
      return Column(children: [
        Padding(padding: const EdgeInsets.only(top: 8), child: Divider(indent: 16, endIndent: 16, color: colors.outlineVariant)),
        IconButton(
          key: ValueKey('nav-group-$title'),
          tooltip: open ? 'Hide $title' : 'Show $title',
          style: IconButton.styleFrom(foregroundColor: colors.onSurfaceVariant, minimumSize: const Size(48, 44)),
          icon: chevron,
          onPressed: onToggle,
        ),
      ]);
    }
    return Semantics(
      expanded: open,
      child: Padding(
        padding: const EdgeInsets.only(top: 10),
        child: ListTile(
          key: ValueKey('nav-group-$title'),
          dense: !inDrawer,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12),
          title: Text(title, style: theme.textTheme.labelLarge?.copyWith(color: colors.onSurfaceVariant)),
          trailing: chevron,
          onTap: onToggle,
        ),
      ),
    );
  }
}

/// The owner's school switcher (ROLE-4): which linked school the session
/// acts in, and the others to switch to, or back to all schools. Choosing a
/// school makes the session that school's principal; the page then reloads
/// for it (MainShell keys the page by school).
class SchoolSwitcher extends StatefulWidget {
  const SchoolSwitcher({super.key, this.compact = false, this.inDrawer = false});

  final bool compact;
  final bool inDrawer;

  @override
  State<SchoolSwitcher> createState() => _SchoolSwitcherState();
}

class _SchoolSwitcherState extends State<SchoolSwitcher> {
  late Future<List<Map<String, dynamic>>> _schools = OwnerSession.schools();

  static const _all = '';

  Future<void> _switch(String schoolId) async {
    final router = GoRouter.of(context);
    final messenger = ScaffoldMessenger.of(context);
    if (widget.inDrawer) Navigator.of(context).pop();
    try {
      if (schoolId == _all) {
        await OwnerSession.leave();
        router.go('/owner');
      } else {
        await OwnerSession.choose(schoolId);
        router.go('/school');
      }
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
      if (mounted) setState(() { _schools = OwnerSession.schools(); });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _schools,
      builder: (context, snap) {
        final schools = snap.data ?? const <Map<String, dynamic>>[];
        final current = CurrentSession.schoolId;
        final active = schools.where((s) => s['schoolId'] == current).firstOrNull;
        final label = current.isEmpty
            ? 'All schools'
            : (active?['name'] as String?) ?? (active?['schoolId'] as String?) ?? 'School';
        final menu = PopupMenuButton<String>(
          key: const Key('school-switcher'),
          tooltip: 'Switch school ($label)',
          onSelected: _switch,
          onOpened: () => setState(() { _schools = OwnerSession.schools(); }),
          itemBuilder: (_) => [
            for (final s in schools)
              CheckedPopupMenuItem<String>(
                value: s['schoolId'] as String,
                checked: s['schoolId'] == current,
                child: Text((s['name'] as String?) ?? (s['schoolId'] as String)),
              ),
            if (schools.isNotEmpty) const PopupMenuDivider(),
            CheckedPopupMenuItem<String>(value: _all, checked: current.isEmpty, child: const Text('All schools')),
          ],
          child: widget.compact
              ? const Padding(padding: EdgeInsets.all(12), child: Icon(Icons.swap_horiz))
              : Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    border: Border.all(color: theme.colorScheme.outlineVariant),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(children: [
                    const Icon(Icons.domain, size: 18),
                    const SizedBox(width: 8),
                    Expanded(child: Text(label, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodyMedium)),
                    const Icon(Icons.unfold_more, size: 18),
                  ]),
                ),
        );
        return Semantics(label: 'School: $label', button: true, child: menu);
      },
    );
  }
}
