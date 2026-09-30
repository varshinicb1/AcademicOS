import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'dashboard_card.dart';
import 'young_home.dart';
import 'ops_api.dart';
import 'profiles.dart';
import 'strings.dart';

/// The school workspace: every day-to-day tool for the signed-in role on one
/// page -- homework, progress, cover, exams, parents, notifications and the
/// principal's admin tools. Each tile opens its own page under /school.
class WorkspacePage extends StatefulWidget {
  const WorkspacePage({super.key});

  @override
  State<WorkspacePage> createState() => _WorkspacePageState();
}

typedef _Tile = ({IconData icon, String title, String subtitle, String path});

class _WorkspacePageState extends State<WorkspacePage> {
  int _unread = 0;
  Set<String> _caps = {};
  // A class 1-5 student gets the young learners' home (SA-7).
  bool _young = false;

  @override
  void initState() {
    super.initState();
    _loadUnread();
    if (CurrentSession.role == 'student') {
      Ops.map('/curriculum/my-timetable').then((t) {
        final grade = t['grade'] as int?;
        if (mounted) setState(() => _young = grade != null && grade <= 5);
      }, onError: (Object e) {
        // The usual home is shown; say why the simpler one is not.
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
      });
    }
    if (CurrentSession.role == 'teacher') {
      Ops.map('/my-grants').then((g) {
        if (mounted) setState(() => _caps = (g['capabilities'] as List).cast<String>().toSet());
      }, onError: (Object _) {
        // not-a-failure: without its grants a teacher simply sees no admin tiles; every admin page reports its own errors
      });
    }
  }

  Future<void> _loadUnread() async {
    try {
      final inbox = await Ops.map('/notifications', query: {'limit': 1});
      if (mounted) setState(() => _unread = (inbox['unreadCount'] as num?)?.toInt() ?? 0);
    } catch (_) {
      // not-a-failure: the unread badge is a convenience; the inbox page reports a failed load itself
    }
  }

  List<_Tile> _tiles(String role) {
    final inbox = (icon: Icons.notifications_outlined, title: tr('Notifications'), subtitle: tr('Your inbox, quiet hours and alerts'), path: '/school/inbox');
    switch (role) {
      case 'student':
        return [
          (icon: Icons.today_outlined, title: tr('Today'), subtitle: tr('Your periods, homework due and the next exam'), path: '/school/today'),
          (icon: Icons.calendar_view_week_outlined, title: tr('My week'), subtitle: tr('The timetable, with times'), path: '/school/week'),
          (icon: Icons.assignment_outlined, title: tr('My homework'), subtitle: tr('Due work, answers and marks'), path: '/school/my-homework'),
          (icon: Icons.insights_outlined, title: tr('My progress'), subtitle: tr('Subjects, chapters and what to revise'), path: '/school/my-learning'),
          (icon: Icons.event_note_outlined, title: tr('My exams'), subtitle: tr('Your datesheet'), path: '/school/my-exams'),
          inbox,
        ];
      case 'parent':
        return [
          (icon: Icons.family_restroom_outlined, title: tr('My children'), subtitle: tr('Timetable, homework, progress and consent'), path: '/school/family'),
          inbox,
        ];
      case 'principal':
        return [
          (icon: Icons.library_books_outlined, title: tr('Question bank'), subtitle: tr('Coverage by chapter and topic; review answers'), path: '/school/question-bank'),
          (icon: Icons.assessment_outlined, title: tr('Term report'), subtitle: tr('The term by class, section and subject; Excel or PDF'), path: '/school/term-report'),
          (icon: Icons.how_to_reg_outlined, title: tr('Attendance & cover'), subtitle: tr('Mark absences, leave and substitutions'), path: '/school/cover'),
          (icon: Icons.restore_outlined, title: tr('Periods owed'), subtitle: tr('Make up or waive lost periods; close a day at short notice'), path: '/school/periods-owed'),
          (icon: Icons.assignment_outlined, title: tr('Homework'), subtitle: tr('Set, mark and follow up'), path: '/school/homework'),
          (icon: Icons.insights_outlined, title: tr('Class progress'), subtitle: tr('Mastery by section and chapter'), path: '/school/class-progress'),
          (icon: Icons.table_chart_outlined, title: tr('Timetable'), subtitle: tr('Allocations, rooms, the bell; generate and publish'), path: '/school/timetable'),
          (icon: Icons.menu_book_outlined, title: tr('Lesson plans'), subtitle: tr("Date each section's lessons from its book and timetable"), path: '/school/lesson-plans'),
          (icon: Icons.badge_outlined, title: tr('School profile'), subtitle: tr('The name and logo printed on papers'), path: '/school/school-profile'),
          (icon: Icons.event_note_outlined, title: tr('Exams'), subtitle: tr('Datesheets and invigilation'), path: '/school/exams'),
          (icon: Icons.rate_review_outlined, title: tr('Paper reviews'), subtitle: tr('Papers waiting for review or approval'), path: '/school/reviews'),
          (icon: Icons.upload_file_outlined, title: tr('Import & export'), subtitle: tr('Sections, people, allocations, holidays'), path: '/school/import'),
          (icon: Icons.key_outlined, title: tr('API keys'), subtitle: tr('Question bank API access'), path: '/school/api-keys'),
          (icon: Icons.admin_panel_settings_outlined, title: tr('Staff permissions'), subtitle: tr('Make a teacher an admin for one area'), path: '/school/grants'),
          inbox,
        ];
      default:
        // A teacher the principal made an admin sees those tools too (M1.4).
        return [
          if (_caps.contains('leave'))
            (icon: Icons.how_to_reg_outlined, title: tr('Attendance & cover'), subtitle: tr('You manage leave and cover'), path: '/school/cover'),
          if (_caps.contains('leave'))
            (icon: Icons.restore_outlined, title: tr('Periods owed'), subtitle: tr('Make up or waive lost periods'), path: '/school/periods-owed'),
          if (_caps.contains('exams'))
            (icon: Icons.event_note_outlined, title: tr('Exams'), subtitle: tr('You manage exam planning'), path: '/school/exams'),
          if (_caps.contains('timetable'))
            (icon: Icons.table_chart_outlined, title: tr('Timetable'), subtitle: tr('You manage the timetable'), path: '/school/timetable'),
          if (_caps.contains('timetable'))
            (icon: Icons.menu_book_outlined, title: tr('Lesson plans'), subtitle: tr("Date each section's lessons from its book and timetable"), path: '/school/lesson-plans'),
          if (_caps.contains('users'))
            (icon: Icons.upload_file_outlined, title: tr('Import & export'), subtitle: tr('You manage people'), path: '/school/import'),
          if (_caps.contains('qbank_review'))
            (icon: Icons.library_books_outlined, title: tr('Question bank'), subtitle: tr('You review its answers'), path: '/school/question-bank?review=1')
          else
            (icon: Icons.library_books_outlined, title: tr('Question bank'), subtitle: tr('Coverage by chapter and topic'), path: '/school/question-bank'),
          if (_caps.contains('reports'))
            (icon: Icons.assessment_outlined, title: tr('Term report'), subtitle: tr('You manage reports'), path: '/school/term-report'),
          (icon: Icons.today_outlined, title: tr('My day'), subtitle: tr('Periods, duties and check-in'), path: '/school/my-day'),
          (icon: Icons.calendar_view_week_outlined, title: tr('My week'), subtitle: tr('The timetable, with times'), path: '/school/week'),
          (icon: Icons.assignment_outlined, title: tr('Homework'), subtitle: tr('Set, mark and follow up'), path: '/school/homework'),
          (icon: Icons.insights_outlined, title: tr('Class progress'), subtitle: tr('Your sections, and who needs help'), path: '/school/class-progress'),
          (icon: Icons.rate_review_outlined, title: tr('Paper reviews'), subtitle: tr('Papers others asked you to review'), path: '/school/reviews'),
          (icon: Icons.event_note_outlined, title: tr('My exam duties'), subtitle: tr('Invigilation roster'), path: '/school/my-exams'),
          inbox,
        ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tiles = _tiles(CurrentSession.role);
    return Scaffold(
      appBar: AppBar(title: Text(tr('School')), actions: [
        // English / हिन्दी for these pages, per device (TA-9).
        IconButton(
          tooltip: uiHindi ? 'Switch to English' : 'हिन्दी में देखें',
          icon: const Icon(Icons.translate),
          onPressed: () => setState(() => setUiLanguage(uiHindi ? 'en' : 'hi')),
        ),
        // A shared family phone: switch between the children and parents on it (SA-8).
        if (CurrentSession.role == 'student' || CurrentSession.role == 'parent')
          IconButton(tooltip: tr('Switch profile'), icon: const Icon(Icons.switch_account_outlined),
              onPressed: () => showProfileSwitcher(context)),
        if (CurrentSession.role != 'parent')
          IconButton(tooltip: 'Copy my calendar link', icon: const Icon(Icons.event_available),
              onPressed: () => copyCalendarLink(context)),
      ]),
      body: Column(children: [
        const OfflineBanner(),
        // The principal and reports admins see today at a glance (ADM-2).
        if (CurrentSession.role == 'principal' || _caps.contains('reports')) const DashboardCard(),
        if (_young) const Expanded(child: YoungHome()) else
        Expanded(child: RefreshIndicator(
        onRefresh: _loadUnread,
        child: LayoutBuilder(builder: (context, c) {
          final cols = c.maxWidth > 1100 ? 3 : (c.maxWidth > 700 ? 2 : 1);
          return GridView.count(
            padding: const EdgeInsets.all(16),
            crossAxisCount: cols,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: cols == 1 ? 4.2 : 3.0,
            children: [
              for (final t in tiles)
                AppCard(
                  onTap: () => context.push(t.path).then((_) => _loadUnread()),
                  child: Row(children: [
                    Badge(
                      isLabelVisible: t.path == '/school/inbox' && _unread > 0,
                      label: Text('$_unread'),
                      child: Icon(t.icon, size: 32, color: theme.colorScheme.primary),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(t.title, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 4),
                          Text(t.subtitle, style: theme.textTheme.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis),
                        ],
                      ),
                    ),
                  ]),
                ),
            ],
          );
        }),
      )),
      ]),
    );
  }
}
