import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// "What do I teach today" -- §15 of the master build prompt, the first
/// teacher-facing screen for the new curriculum/calendar/scheduling work
/// this backend now does for real (src/academicos/curriculum/scheduling.py).
/// Also where §15's completion tracking lives: tapping a lesson opens a
/// deliberately trivial YES/NO + optional note sheet -- no curriculum
/// re-selection, per the transcript's own instruction.
///
/// Online-only for now: the offline on-device engine
/// (core/local_engine/) has no local mirror of curriculum/schedule data at
/// all -- there is no Topic/Subtopic/ScheduledLesson concept in Hive, only
/// in the real server's SQLite store. Every other online-only screen in
/// this app degrades to a local equivalent; this one has none yet, so it
/// honestly says so rather than pretending to work offline. A real
/// day-by-day navigator: the default view is today, with simple
/// forward/back arrows to check other days (e.g. tomorrow's prep, or
/// yesterday's coverage) -- no calendar picker yet, since a teacher's real
/// question is almost always "today" or "the next couple of days".
class MySchedulePage extends StatefulWidget {
  const MySchedulePage({super.key});

  @override
  State<MySchedulePage> createState() => _MySchedulePageState();
}

class _MySchedulePageState extends State<MySchedulePage> {
  DateTime _date = DateTime.now();
  late Future<List<MyScheduleEntry>> _future;

  static const _offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  String get _isoDate =>
      '${_date.year.toString().padLeft(4, '0')}-${_date.month.toString().padLeft(2, '0')}-${_date.day.toString().padLeft(2, '0')}';

  Future<List<MyScheduleEntry>> _load() {
    return GetIt.I<CurriculumApi>().mySchedule(startDate: _isoDate, endDate: _isoDate);
  }

  void _shiftDay(int delta) {
    setState(() {
      _date = _date.add(Duration(days: delta));
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('My Schedule')),
      body: _offlineMode
          ? const EmptyState(
              icon: Icons.cloud_off,
              title: 'Needs a connection',
              message: 'Your teaching schedule lives on the school\'s server and isn\'t '
                  'available in this offline app yet.',
            )
          : Column(
              children: [
                _dayNav(theme),
                const Divider(height: 1),
                Expanded(
                  child: FutureBuilder<List<MyScheduleEntry>>(
                    future: _future,
                    builder: (context, snap) {
                      if (snap.connectionState != ConnectionState.done) {
                        return const LoadingIndicator(message: 'Loading your schedule…');
                      }
                      if (snap.hasError) {
                        return ErrorDisplay(
                          message: 'Could not load your schedule. Check your connection.',
                          onRetry: () => setState(() => _future = _load()),
                        );
                      }
                      final lessons = snap.data ?? const [];
                      if (lessons.isEmpty) {
                        return EmptyState(
                          icon: Icons.event_available_outlined,
                          title: 'No lessons scheduled',
                          message: _isToday(_date)
                              ? 'Nothing scheduled for you today -- either a free '
                                'period, or your subjects haven\'t been scheduled yet.'
                              : 'Nothing scheduled for you on this day.',
                        );
                      }
                      return RefreshIndicator(
                        onRefresh: () async => setState(() => _future = _load()),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: lessons.length,
                          itemBuilder: (context, i) => _lessonCard(context, theme, lessons[i]),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Widget _dayNav(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Row(
        children: [
          IconButton(icon: const Icon(Icons.chevron_left), onPressed: () => _shiftDay(-1)),
          Expanded(
            child: Center(
              child: Text(
                _isToday(_date) ? 'Today, ${_formatDate(_date)}' : _formatDate(_date),
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
              ),
            ),
          ),
          IconButton(icon: const Icon(Icons.chevron_right), onPressed: () => _shiftDay(1)),
        ],
      ),
    );
  }

  Widget _lessonCard(BuildContext context, ThemeData theme, MyScheduleEntry lesson) {
    return AppCard(
      onTap: () => _openMarkSheet(context, lesson),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, shape: BoxShape.circle),
            child: Icon(_statusIcon(lesson.status), color: theme.colorScheme.onPrimaryContainer, size: 22),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lesson.subtopicName,
                    style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(2),
                Text(
                  [lesson.subjectName, lesson.chapterName, lesson.topicName]
                      .where((s) => s.isNotEmpty)
                      .join(' · '),
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
                if (lesson.note != null && lesson.note!.isNotEmpty) ...[
                  const Gap(6),
                  Text('"${lesson.note}"',
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant, fontStyle: FontStyle.italic)),
                ],
              ],
            ),
          ),
          ChipTag(label: lesson.status, color: _statusColor(theme, lesson.status)),
        ],
      ),
    );
  }

  IconData _statusIcon(String status) {
    switch (status) {
      case 'completed':
        return Icons.check_circle_outline;
      case 'skipped':
        return Icons.remove_circle_outline;
      default:
        return Icons.menu_book_outlined;
    }
  }

  Color? _statusColor(ThemeData theme, String status) {
    switch (status) {
      case 'completed':
        return Colors.green.shade600;
      case 'skipped':
        return theme.colorScheme.error;
      default:
        return null; // ChipTag's own default (primaryContainer)
    }
  }

  /// The §15 deliverable itself: YES/NO + optional note, nothing else --
  /// no re-picking the subtopic, no editing the schedule. Reloads the day
  /// on success so the card reflects the real, persisted mark rather than
  /// an optimistic local guess.
  Future<void> _openMarkSheet(BuildContext context, MyScheduleEntry lesson) async {
    final noteController = TextEditingController(text: lesson.note ?? '');
    var saving = false;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
            Future<void> mark(String status) async {
              setSheetState(() => saving = true);
              try {
                final note = noteController.text.trim();
                await GetIt.I<CurriculumApi>()
                    .markLesson(lesson.lessonId, status: status, note: note.isEmpty ? null : note);
                if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                if (mounted) setState(() => _future = _load());
              } catch (_) {
                setSheetState(() => saving = false);
                if (sheetContext.mounted) {
                  ScaffoldMessenger.of(sheetContext).showSnackBar(
                    const SnackBar(content: Text('Could not save -- check your connection and try again.')),
                  );
                }
              }
            }

            final theme = Theme.of(sheetContext);
            return Padding(
              padding: EdgeInsets.only(
                left: 20, right: 20, top: 20,
                bottom: 20 + MediaQuery.of(sheetContext).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(lesson.subtopicName, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                  const Gap(4),
                  Text('Did you teach this?', style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  const Gap(16),
                  TextField(
                    controller: noteController,
                    decoration: const InputDecoration(
                      labelText: 'Note (optional)',
                      border: OutlineInputBorder(),
                    ),
                    maxLines: 2,
                    enabled: !saving,
                  ),
                  const Gap(16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: saving ? null : () => mark('skipped'),
                          icon: const Icon(Icons.close),
                          label: const Text('No'),
                        ),
                      ),
                      const Gap(12),
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: saving ? null : () => mark('completed'),
                          icon: saving
                              ? const SizedBox(width: 16, height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Icon(Icons.check),
                          label: const Text('Yes'),
                        ),
                      ),
                    ],
                  ),
                  if (lesson.status != 'scheduled') ...[
                    const Gap(8),
                    Center(
                      child: TextButton(
                        onPressed: saving ? null : () => mark('scheduled'),
                        child: const Text('Undo mark'),
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        );
      },
    );
  }

  static bool _isToday(DateTime d) {
    final now = DateTime.now();
    return d.year == now.year && d.month == now.month && d.day == now.day;
  }

  static String _formatDate(DateTime d) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    return '${days[d.weekday - 1]}, ${months[d.month - 1]} ${d.day}';
  }
}
