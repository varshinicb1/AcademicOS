import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../../core/theme/app_theme.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// One step of setting a school up: what it is, where it is done, and
/// whether the school has done it.
typedef SetupStep = ({String key, String title, String subtitle, String path, bool done});

/// A new school's first steps, on the principal's School page: School
/// profile, Classes, Calendar and terms, People, Timetable -- each a link,
/// each ticked once the school's own data shows it done.
///
/// A new principal landed on a dashboard of zeros with no word on what to do
/// first, and class setup was found only by guessing "Invite people" (QA S-09,
/// 2026-10-01). The card goes away once every step is done.
///
/// Every read is one the server answers with 200 for a new school: the
/// calendar itself is not read (a year without one is a 404), so the
/// calendar step counts as done once the year has its terms, which are set
/// on the same Calendar & Setup tab.
class SetupChecklistCard extends StatefulWidget {
  const SetupChecklistCard({super.key});

  /// The steps for what the school has. [hasName]: School profile saved a
  /// name; [hasClasses]: the year has classes; [hasTerms]: the year has
  /// terms; [hasTeachers]: a teacher has joined; [hasTimetable]: a week is
  /// timetabled.
  static List<SetupStep> steps({
    required bool hasName,
    required bool hasClasses,
    required bool hasTerms,
    required bool hasTeachers,
    required bool hasTimetable,
  }) =>
      [
        (key: 'profile', title: 'School profile', subtitle: 'The name, address and logo printed on papers',
          path: '/school/school-profile', done: hasName),
        (key: 'classes', title: 'Classes', subtitle: 'The academic year, its classes and sections',
          path: '/admin', done: hasClasses),
        (key: 'calendar', title: 'Calendar and terms',
          subtitle: 'Weekly off days, the Saturday rule, holidays and the terms, on Calendar & Setup',
          path: '/admin?tab=calendar', done: hasTerms),
        (key: 'people', title: 'People', subtitle: 'Invite your teachers, then your students and parents',
          path: '/admin', done: hasTeachers),
        (key: 'timetable', title: 'Timetable', subtitle: 'Who teaches what, the bell, then generate the week',
          path: '/school/timetable', done: hasTimetable),
      ];

  @override
  State<SetupChecklistCard> createState() => _SetupChecklistCardState();
}

class _SetupChecklistCardState extends State<SetupChecklistCard> {
  late Future<List<SetupStep>> _future = _load();

  static Future<List<SetupStep>> _load() async {
    final profile = await Ops.map('/curriculum/school-profile');
    final staff = await Ops.list('/staff');
    final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
    var hasClasses = false, hasTerms = false, hasTimetable = false;
    if (years.isNotEmpty) {
      years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
      final id = years.last['id'] as String;
      hasClasses = (await Ops.list('/curriculum/academic-years/$id/grades')).isNotEmpty;
      hasTerms = (await Ops.list('/curriculum/academic-years/$id/terms')).isNotEmpty;
      hasTimetable = hasClasses && (await Ops.list('/curriculum/academic-years/$id/timetable')).isNotEmpty;
    }
    return SetupChecklistCard.steps(
      hasName: (profile['name'] as String? ?? '').trim().isNotEmpty,
      hasClasses: hasClasses,
      hasTerms: hasTerms,
      hasTeachers: staff.any((s) => s['role'] == 'teacher'),
      hasTimetable: hasTimetable,
    );
  }

  void _reload() {
    if (!mounted) return;
    setState(() {
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<List<SetupStep>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const SizedBox.shrink();
        if (snap.hasError) {
          return Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Text('${tr('The setup checklist could not load')}: ${serverErrorMessage(snap.error!)}',
                key: const ValueKey('setup-checklist-error'),
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error)),
          );
        }
        final steps = snap.data!;
        final done = steps.where((s) => s.done).length;
        if (done == steps.length) return const SizedBox.shrink();
        final next = steps.firstWhere((s) => !s.done);
        return AppCard(
          key: const ValueKey('setup-checklist'),
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(tr('Set up your school'), style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text('$done ${tr('of')} ${steps.length} ${tr('done')}. ${tr('Next')}: ${tr(next.title)}.',
                style: theme.textTheme.bodySmall),
            const SizedBox(height: 4),
            for (final s in steps)
              ListTile(
                key: ValueKey('setup-step-${s.key}'),
                contentPadding: EdgeInsets.zero,
                leading: Icon(s.done ? Icons.check_circle : Icons.radio_button_unchecked,
                    color: s.done ? AppColors.success : theme.colorScheme.onSurfaceVariant,
                    semanticLabel: s.done ? tr('Done') : tr('Not done yet')),
                title: Text(tr(s.title),
                    style: s.done ? TextStyle(color: theme.colorScheme.onSurfaceVariant) : null),
                subtitle: Text(tr(s.subtitle)),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push(s.path).then((_) => _reload()),
              ),
          ]),
        );
      },
    );
  }
}
