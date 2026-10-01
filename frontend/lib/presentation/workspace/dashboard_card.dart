import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'package:academicos/core/theme/app_theme.dart';

/// Today at a glance for the principal (or a reports admin): staff and
/// cover, the week's homework, exams coming up, students needing help.
class DashboardCard extends StatelessWidget {
  const DashboardCard({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<Map<String, dynamic>>(
      future: Ops.map('/dashboard/summary'),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const SizedBox(height: 120, child: LoadingIndicator());
        }
        if (snap.hasError) return const SizedBox.shrink();   // not an admin for reports: no card
        final d = snap.data!;
        final c = Map<String, dynamic>.from(d['cover'] as Map);
        final h = Map<String, dynamic>.from(d['homework'] as Map);
        final exams = (d['exams'] as List).cast<Map>();
        final concerns = (d['studentsNeedingHelp'] as List).cast<Map>();
        // Staff counts the principal: 1 is a school no teacher has joined yet,
        // where "1 Attendance not marked" was the principal herself (QA S-09).
        final noTeachers = (c['staff'] as num? ?? 0) <= 1;
        Widget stat(String label, String value, IconData icon, Color color, String path) => SizedBox(
              width: 220,
              child: InkWell(onTap: () => context.push(path),
                  child: StatCard(label: label, value: value, icon: icon, color: color)),
            );
        return AppCard(
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Today · ${d['date']}', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            Wrap(spacing: 12, runSpacing: 12, children: [
              if (noTeachers)
                stat('Teachers who have joined', '0', Icons.person_add_alt_1_outlined, AppColors.warning, '/admin')
              else ...[
                stat('Absent / on leave', '${c['absent']} / ${c['onLeave']}', Icons.person_off_outlined,
                    theme.colorScheme.primary, '/school/cover'),
                stat('Attendance not marked', '${c['unmarked']}', Icons.how_to_reg_outlined,
                    c['unmarked'] > 0 ? AppColors.warning : AppColors.success, '/school/cover'),
                stat('Periods needing cover', '${c['uncovered']} of ${c['periodsToCover']}', Icons.swap_horiz,
                    c['uncovered'] > 0 ? theme.colorScheme.error : AppColors.success, '/school/cover'),
              ],
              stat('Homework this week', '${h['submitted']}/${h['submissionsExpected']} in · ${h['set']} set',
                  Icons.assignment_outlined, theme.colorScheme.primary, '/school/homework'),
              stat('Waiting to be marked', '${h['waitingToMark']}', Icons.rule, AppColors.warning, '/school/homework'),
            ]),
            if (exams.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text('Exams: ${exams.map((e) => '${e['name']} (${e['startDate']})').join(', ')}',
                  style: theme.textTheme.bodySmall),
            ],
            if (concerns.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text('Students needing help', style: theme.textTheme.titleSmall),
              for (final s in concerns.take(5))
                Text('${s['name']}${s['sectionName'] != null ? ' (${s['sectionName']})' : ''}: '
                    '${s['needsWork']} chapters need work, ${s['overdue']} homework overdue',
                    style: theme.textTheme.bodySmall),
            ],
          ]),
        );
      },
    );
  }
}

/// Copies the caller's private calendar link, for Google Calendar or a phone.
Future<void> copyCalendarLink(BuildContext context) async {
  try {
    final r = await Ops.map('/calendar-feed');
    await Clipboard.setData(ClipboardData(text: r['url'] as String));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Calendar link copied. In Google Calendar: Other calendars → From URL.')));
    }
  } catch (e) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
  }
}
