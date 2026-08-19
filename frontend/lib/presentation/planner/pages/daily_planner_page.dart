import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../../data/datasources/api/api_client.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../../domain/entities/entities.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

const _teacherId = 'teacher_1';
// Only Class X has real official CBSE syllabus data loaded (see
// cbse_syllabus.py) -- these are the 4 subjects it covers.
const _timetableSubjects = ['Mathematics', 'Science', 'Social Science', 'English'];

/// Assessment schedule — the real exam calendar, built from the assessments
/// this teacher has created rather than an invented study plan.
class PlannerPage extends StatefulWidget {
  const PlannerPage({super.key});

  @override
  State<PlannerPage> createState() => _PlannerPageState();
}

class _PlannerPageState extends State<PlannerPage> {
  DateTime _focused = DateTime.now();
  DateTime? _selected = DateTime.now();

  @override
  void initState() {
    super.initState();
    context.read<AssessmentBloc>().add(const AssessmentEvent.loadAssessments(_teacherId));
  }

  DateTime _dayOf(Assessment a) => a.scheduledAt ?? a.createdAt;

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: forceShellLeading(context),
        title: const Text('Assessment Schedule'),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome),
            tooltip: 'AI weekly timetable',
            onPressed: () => _showTimetableSheet(context),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context
                .read<AssessmentBloc>()
                .add(const AssessmentEvent.loadAssessments(_teacherId)),
          ),
        ],
      ),
      body: BlocBuilder<AssessmentBloc, AssessmentState>(
        builder: (context, state) {
          final assessments = state.maybeWhen(
            assessmentsLoaded: (list) => list,
            orElse: () => const <Assessment>[],
          );
          final loading = state.maybeWhen(loading: () => true, orElse: () => false);
          return Column(
            children: [
              Card(
                margin: const EdgeInsets.all(12),
                child: TableCalendar<Assessment>(
                  firstDay: DateTime.now().subtract(const Duration(days: 365)),
                  lastDay: DateTime.now().add(const Duration(days: 365)),
                  focusedDay: _focused,
                  selectedDayPredicate: (d) =>
                      _selected != null && _sameDay(d, _selected!),
                  eventLoader: (day) =>
                      assessments.where((a) => _sameDay(_dayOf(a), day)).toList(),
                  calendarFormat: CalendarFormat.month,
                  availableCalendarFormats: const {CalendarFormat.month: 'Month'},
                  onDaySelected: (sel, foc) => setState(() {
                    _selected = sel;
                    _focused = foc;
                  }),
                  calendarStyle: CalendarStyle(
                    markerDecoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ),
              Expanded(child: loading ? const LoadingIndicator() : _dayList(assessments)),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/assessment/create'),
        icon: const Icon(Icons.add),
        label: const Text('Schedule assessment'),
      ),
    );
  }

  Widget _dayList(List<Assessment> all) {
    final day = _selected ?? DateTime.now();
    final today = all.where((a) => _sameDay(_dayOf(a), day)).toList();
    if (all.isEmpty) {
      return const EmptyState(
        icon: Icons.event_note_outlined,
        title: 'No assessments yet',
        message: 'Create an assessment and it will appear on this calendar.',
      );
    }
    if (today.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'Nothing scheduled for ${day.day}/${day.month}/${day.year}.\n'
            '${all.length} assessment(s) on other dates.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      );
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      children: today
          .map((a) => AppCard(
                onTap: () =>
                    context.push('/assessment/${a.id}', extra: {'assessment': a}),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(a.title,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall
                                  ?.copyWith(fontWeight: FontWeight.w600)),
                          const Gap(4),
                          Text(
                              '${a.subject} · Class ${a.grade} · '
                              '${a.blueprint.totalMarks} marks · '
                              '${a.blueprint.durationMinutes} min',
                              style: Theme.of(context).textTheme.bodySmall),
                          if (a.scheduledAt != null) ...[
                            const Gap(4),
                            if (a.metadata['googleCalendarEventId'] != null)
                              Row(children: [
                                const Icon(Icons.event_available, size: 14, color: Colors.green),
                                const Gap(4),
                                Text(
                                  'Synced to Google Calendar',
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.green.shade700),
                                ),
                              ])
                            else
                              Row(children: [
                                Icon(Icons.event_busy, size: 14, color: Colors.orange.shade700),
                                const Gap(4),
                                Text(
                                  'Not synced to Google Calendar',
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.orange.shade700),
                                ),
                              ]),
                          ],
                        ],
                      ),
                    ),
                    ChipTag(label: a.status.name),
                    IconButton(
                      icon: const Icon(Icons.edit_calendar_outlined),
                      tooltip: 'Set date & time',
                      onPressed: () => _pickSchedule(a),
                    ),
                  ],
                ),
              ))
          .toList(),
    );
  }

  Future<void> _pickSchedule(Assessment a) async {
    final date = await showDatePicker(
      context: context,
      initialDate: a.scheduledAt ?? DateTime.now(),
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: a.scheduledAt != null
          ? TimeOfDay.fromDateTime(a.scheduledAt!)
          : const TimeOfDay(hour: 9, minute: 0),
    );
    if (time == null || !mounted) return;
    final scheduledAt = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    try {
      // Backend syncs this to the school's Google Calendar (via Composio)
      // as part of saving the update — see routes.py's update_assessment.
      await GetIt.I<ApiClient>().updateAssessment(a.id, a.copyWith(scheduledAt: scheduledAt));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Scheduled — syncing to Google Calendar')),
      );
      context.read<AssessmentBloc>().add(const AssessmentEvent.loadAssessments(_teacherId));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not schedule: $e')),
      );
    }
  }

  void _showTimetableSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => const _TimetableSheet(),
    );
  }
}

/// Kept so the existing `/planner/daily` route still resolves.
class DailyPlannerPage extends StatelessWidget {
  const DailyPlannerPage({super.key});

  @override
  Widget build(BuildContext context) => const PlannerPage();
}

/// AI-suggested weekly timetable: the school's actual weekly periods for a
/// subject, allocated proportionally to each unit's official CBSE
/// marks-weightage — see timetable.py for why marks-weightage (not made-up
/// hours) is the source signal.
class _TimetableSheet extends StatefulWidget {
  const _TimetableSheet();

  @override
  State<_TimetableSheet> createState() => _TimetableSheetState();
}

class _TimetableSheetState extends State<_TimetableSheet> {
  String _subject = _timetableSubjects.first;
  int _periodsPerWeek = 6;
  int _weeks = 20;
  Timetable? _result;
  bool _loading = false;
  String? _error;

  Future<void> _generate() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final tt = await GetIt.I<PillarApi>().timetable(_subject, 10,
          periodsPerWeek: _periodsPerWeek, weeks: _weeks);
      setState(() => _result = tt);
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) => ListView(
        controller: scrollController,
        padding: const EdgeInsets.all(16),
        children: [
          Row(children: [
            const Icon(Icons.auto_awesome),
            const Gap(8),
            Text('AI weekly timetable', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          ]),
          const Gap(6),
          Text(
            'Allocates the periods you give it per week, proportional to each unit\'s '
            'official CBSE marks-weightage — higher-weighted units get more class time.',
            style: theme.textTheme.bodySmall,
          ),
          const Gap(16),
          DropdownButtonFormField<String>(
            initialValue: _subject,
            decoration: const InputDecoration(labelText: 'Subject (Class X)', border: OutlineInputBorder()),
            items: _timetableSubjects.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
            onChanged: (v) => setState(() => _subject = v ?? _subject),
          ),
          const Gap(12),
          Row(children: [
            Expanded(
              child: TextFormField(
                initialValue: '$_periodsPerWeek',
                decoration: const InputDecoration(labelText: 'Periods / week', border: OutlineInputBorder(), isDense: true),
                keyboardType: TextInputType.number,
                onChanged: (v) => _periodsPerWeek = int.tryParse(v) ?? _periodsPerWeek,
              ),
            ),
            const Gap(12),
            Expanded(
              child: TextFormField(
                initialValue: '$_weeks',
                decoration: const InputDecoration(labelText: 'Weeks remaining', border: OutlineInputBorder(), isDense: true),
                keyboardType: TextInputType.number,
                onChanged: (v) => _weeks = int.tryParse(v) ?? _weeks,
              ),
            ),
          ]),
          const Gap(12),
          FilledButton.icon(
            onPressed: _loading ? null : _generate,
            icon: _loading
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.auto_awesome),
            label: Text(_loading ? 'Generating…' : 'Generate'),
          ),
          if (_error != null) ...[
            const Gap(12),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],
          if (_result != null) ...[
            const Gap(20),
            Text('Unit allocation', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const Gap(8),
            for (final a in _result!.allocations)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(children: [
                  Expanded(child: Text(a.unitName)),
                  ChipTag(label: '${a.marks}m'),
                  const Gap(6),
                  ChipTag(label: '${a.suggestedPeriods} periods', color: theme.colorScheme.primaryContainer),
                ]),
              ),
            const Gap(20),
            Text('Weekly schedule', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const Gap(8),
            for (final weekNum in _result!.schedule.map((s) => s.week).toSet())
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Week $weekNum', style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600)),
                      const Gap(4),
                      for (final s in _result!.schedule.where((s) => s.week == weekNum))
                        Text('${s.unitName} — ${s.periods} period${s.periods == 1 ? '' : 's'}',
                            style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }
}
