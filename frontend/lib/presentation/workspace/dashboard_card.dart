import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'package:academicos/core/theme/app_theme.dart';

const _weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const _months = [
  'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November',
  'December',
];

/// "Sunday 4 October" for an ISO date; the text unchanged when it is not one.
String friendlyDate(String iso) {
  final d = DateTime.tryParse(iso);
  return d == null ? iso : '${_weekdays[d.weekday - 1]} ${d.day} ${_months[d.month - 1]}';
}

/// "20 Oct" for an ISO date; the text unchanged when it is not one.
String shortDate(String iso) {
  final d = DateTime.tryParse(iso);
  return d == null ? iso : '${d.day} ${_months[d.month - 1].substring(0, 3)}';
}

String _plural(num n, String one, String many) => '$n ${n == 1 ? one : many}';

/// How a count reads: calm when there is nothing to do, a colour that asks for attention when there is.
enum Tone { calm, good, attention, urgent }

Color toneColor(BuildContext context, Tone tone) => switch (tone) {
      Tone.calm => Theme.of(context).colorScheme.onSurfaceVariant,
      Tone.good => AppColors.success,
      Tone.attention => AppColors.warning,
      Tone.urgent => Theme.of(context).colorScheme.error,
    };

/// Today at a glance for the principal (or a reports admin): staff and
/// cover, the week's homework, exams coming up, students needing help.
///
/// Redesigned 2026-10-04: the tiles were a fixed 220px wide (one per row on a phone, a gap on the right
/// of a desktop), and orange or red whatever their value, so a day with nothing wrong looked like an
/// alarm. A count of zero is now calm or green, a colour asks for attention only when there is something
/// to do, and the tiles fill the card in two columns on a phone.
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
        final absent = (c['absent'] as num? ?? 0) + (c['onLeave'] as num? ?? 0);
        final unmarked = c['unmarked'] as num? ?? 0;
        final uncovered = c['uncovered'] as num? ?? 0;
        final waiting = h['waitingToMark'] as num? ?? 0;
        final allClear = !noTeachers && unmarked == 0 && uncovered == 0 && waiting == 0;

        final tiles = <_Stat>[
          if (noTeachers)
            const _Stat('Teachers who have joined', '0', Icons.person_add_alt_1_outlined, Tone.attention, '/admin')
          else ...[
            _Stat('Absent / on leave', '${c['absent']} / ${c['onLeave']}', Icons.person_off_outlined,
                absent > 0 ? Tone.attention : Tone.calm, '/school/cover'),
            _Stat('Attendance not marked', '$unmarked', Icons.how_to_reg_outlined,
                unmarked > 0 ? Tone.attention : Tone.good, '/school/cover'),
            _Stat('Periods needing cover', '$uncovered of ${c['periodsToCover']}', Icons.swap_horiz,
                uncovered > 0 ? Tone.urgent : Tone.good, '/school/cover'),
          ],
          _Stat('Homework this week', '${h['submitted']}/${h['submissionsExpected']} in · ${h['set']} set',
              Icons.assignment_outlined, Tone.calm, '/school/homework'),
          _Stat('Waiting to be marked', '$waiting', Icons.rule, waiting > 0 ? Tone.attention : Tone.good,
              '/school/homework'),
        ];

        return AppCard(
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Today', style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            Text(friendlyDate('${d['date']}'),
                style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 14),
            LayoutBuilder(builder: (context, box) {
              final cols = box.maxWidth >= 900 ? 5 : box.maxWidth >= 520 ? 3 : 2;
              const gap = 10.0;
              final w = (box.maxWidth - gap * (cols - 1)) / cols;
              return Wrap(spacing: gap, runSpacing: gap, children: [
                for (final t in tiles)
                  SizedBox(
                    width: w,
                    child: Semantics(
                      button: true,
                      label: '${t.label}: ${t.value}',
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () => context.push(t.path),
                        child: StatCard(label: t.label, value: t.value, icon: t.icon, color: toneColor(context, t.tone)),
                      ),
                    ),
                  ),
              ]);
            }),
            if (allClear) ...[
              const SizedBox(height: 12),
              Row(children: [
                const Icon(Icons.check_circle_outline, size: 18, color: AppColors.success),
                const SizedBox(width: 8),
                Expanded(
                  child: Text('Nothing needs your attention today.',
                      key: const ValueKey('dashboard-all-clear'),
                      style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.success)),
                ),
              ]),
            ],
            if (exams.isNotEmpty) ...[
              const SizedBox(height: 14),
              Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
                Text('Exams', style: theme.textTheme.labelLarge?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                for (final e in exams)
                  Chip(
                    visualDensity: VisualDensity.compact,
                    avatar: const Icon(Icons.event_note_outlined, size: 16),
                    label: Text('${e['name']} · ${shortDate('${e['startDate']}')}'),
                  ),
              ]),
            ],
            if (concerns.isNotEmpty) ...[
              const SizedBox(height: 14),
              Text('Students needing help', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              for (final s in concerns.take(5))
                ListTile(
                  key: ValueKey('help-${s['name']}'),
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  onTap: () => context.push('/school/class-progress'),
                  leading: CircleAvatar(
                    radius: 16,
                    backgroundColor: AppColors.warning.withValues(alpha: 0.12),
                    child: Text(('${s['name']}'.isEmpty ? '?' : '${s['name']}'[0]).toUpperCase(),
                        style: const TextStyle(color: AppColors.warning, fontWeight: FontWeight.w700)),
                  ),
                  title: Text('${s['name']}${s['sectionName'] != null ? ' (${s['sectionName']})' : ''}'),
                  subtitle: Text('${_plural(s['needsWork'] as num? ?? 0, 'chapter needs', 'chapters need')} work · '
                      '${s['overdue']} homework overdue'),
                  trailing: const Icon(Icons.chevron_right, size: 18),
                ),
            ],
          ]),
        );
      },
    );
  }
}

class _Stat {
  final String label, value, path;
  final IconData icon;
  final Tone tone;
  const _Stat(this.label, this.value, this.icon, this.tone, this.path);
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
