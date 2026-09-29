import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';

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

  @override
  void initState() {
    super.initState();
    _loadUnread();
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
    const inbox = (icon: Icons.notifications_outlined, title: 'Notifications', subtitle: 'Your inbox, quiet hours and alerts', path: '/school/inbox');
    switch (role) {
      case 'student':
        return const [
          (icon: Icons.assignment_outlined, title: 'My homework', subtitle: 'Due work, answers and marks', path: '/school/my-homework'),
          (icon: Icons.insights_outlined, title: 'My progress', subtitle: 'Subjects, chapters and what to revise', path: '/school/my-learning'),
          (icon: Icons.event_note_outlined, title: 'My exams', subtitle: 'Your datesheet', path: '/school/my-exams'),
          inbox,
        ];
      case 'parent':
        return const [
          (icon: Icons.family_restroom_outlined, title: 'My children', subtitle: 'Timetable, homework, progress and consent', path: '/school/family'),
          inbox,
        ];
      case 'principal':
        return const [
          (icon: Icons.how_to_reg_outlined, title: 'Attendance & cover', subtitle: 'Mark absences, leave and substitutions', path: '/school/cover'),
          (icon: Icons.assignment_outlined, title: 'Homework', subtitle: 'Set, mark and follow up', path: '/school/homework'),
          (icon: Icons.event_note_outlined, title: 'Exams', subtitle: 'Datesheets and invigilation', path: '/school/exams'),
          (icon: Icons.rate_review_outlined, title: 'Paper reviews', subtitle: 'Papers waiting for review or approval', path: '/school/reviews'),
          (icon: Icons.upload_file_outlined, title: 'Import & export', subtitle: 'Sections, people, allocations, holidays', path: '/school/import'),
          (icon: Icons.key_outlined, title: 'API keys', subtitle: 'Question bank API access', path: '/school/api-keys'),
          (icon: Icons.admin_panel_settings_outlined, title: 'Staff permissions', subtitle: 'Make a teacher an admin for one area', path: '/school/grants'),
          inbox,
        ];
      default:
        // A teacher the principal made an admin sees those tools too (M1.4).
        return [
          if (_caps.contains('leave'))
            (icon: Icons.how_to_reg_outlined, title: 'Attendance & cover', subtitle: 'You manage leave and cover', path: '/school/cover'),
          if (_caps.contains('exams'))
            (icon: Icons.event_note_outlined, title: 'Exams', subtitle: 'You manage exam planning', path: '/school/exams'),
          if (_caps.contains('users'))
            (icon: Icons.upload_file_outlined, title: 'Import & export', subtitle: 'You manage people', path: '/school/import'),
          (icon: Icons.today_outlined, title: 'My day', subtitle: 'Periods, duties and check-in', path: '/school/my-day'),
          (icon: Icons.assignment_outlined, title: 'Homework', subtitle: 'Set, mark and follow up', path: '/school/homework'),
          (icon: Icons.rate_review_outlined, title: 'Paper reviews', subtitle: 'Papers others asked you to review', path: '/school/reviews'),
          (icon: Icons.event_note_outlined, title: 'My exam duties', subtitle: 'Invigilation roster', path: '/school/my-exams'),
          inbox,
        ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tiles = _tiles(CurrentSession.role);
    return Scaffold(
      appBar: AppBar(title: const Text('School')),
      body: RefreshIndicator(
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
      ),
    );
  }
}
