import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';
import '../shared/widgets/shell.dart';
import 'period_line.dart';

/// A student's day (SA-1): the periods as they will actually run --
/// substitutes, cancelled and make-up periods marked -- then homework due
/// soon and the next exam. After school hours it shows tomorrow.
class StudentTodayPage extends StatefulWidget {
  const StudentTodayPage({super.key});

  @override
  State<StudentTodayPage> createState() => _StudentTodayPageState();
}

class _StudentTodayPageState extends State<StudentTodayPage> {
  static const _afterSchoolHour = 15;
  late DateTime _day = DateTime.now().hour >= _afterSchoolHour
      ? DateTime.now().add(const Duration(days: 1))
      : DateTime.now();
  List<Map<String, dynamic>>? _rows;

  /// "Next: period 3 at 10:00 · Science (in 25 min)" on today's page.
  String? get _nextLine => _rows == null || isoDate(_day) != isoDate(DateTime.now())
      ? null
      : nextPeriodLine(_rows!.cast<Map>(), DateTime.now(), what: (r) => r['subjectName'] as String? ?? '');
  List<Map<String, dynamic>> _due = [];
  Map<String, dynamic>? _exam;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final rows = (await Ops.get('/curriculum/my-day', query: {'date': isoDate(_day)}) as List)
          .map((e) => Map<String, dynamic>.from(e as Map)).toList();
      final homework = await Ops.list('/my-homework');
      final exams = await Ops.map('/my-exams');
      final today = isoDate(DateTime.now());
      final soon = isoDate(DateTime.now().add(const Duration(days: 3)));
      Map<String, dynamic>? next;
      for (final e in (exams['exams'] as List).cast<Map>()) {
        for (final p in (e['papers'] as List).cast<Map>()) {
          if ((p['date'] as String).compareTo(today) >= 0 &&
              (next == null || (p['date'] as String).compareTo(next['date'] as String) < 0)) {
            next = {...Map<String, dynamic>.from(p), 'exam': e['name']};
          }
        }
      }
      setState(() {
        _rows = rows..sort((a, b) => (a['period'] as int).compareTo(b['period'] as int));
        _due = homework.where((h) => h['myStatus'] == 'not_submitted' && (h['dueDate'] as String).compareTo(soon) <= 0).toList();
        _exam = next;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  String _kind(String k) => switch (k) {
        'substitute' => tr('Substitute teacher'),
        'supervised' => tr('Supervised'),
        'combined' => tr('Combined class'),
        'lost' => tr('Cancelled'),
        'uncovered' => tr('No teacher yet'),
        'makeup' => tr('Extra period'),
        _ => '',
      };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isToday = isoDate(_day) == isoDate(DateTime.now());
    return Scaffold(
      appBar: AppBar(
        leading: isToday ? forceShellLeading(context) : null,
        automaticallyImplyLeading: !isToday,
        title: Text(isToday ? tr('Today') : tr('Tomorrow')), actions: [
        IconButton(
          tooltip: isToday ? 'Tomorrow' : 'Today',
          icon: Icon(isToday ? Icons.arrow_forward : Icons.arrow_back),
          onPressed: () {
            setState(() {
              _day = isToday ? DateTime.now().add(const Duration(days: 1)) : DateTime.now();
              _rows = null;
            });
            _load();
          },
        ),
      ]),
      body: _error != null
          ? ErrorDisplay(message: _error!, onRetry: _load)
          : _rows == null
              ? const LoadingIndicator()
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(padding: const EdgeInsets.all(16), children: [
                    if (_exam != null)
                      AppCard(
                        margin: const EdgeInsets.only(bottom: 12),
                        color: theme.colorScheme.tertiaryContainer,
                        onTap: () => context.push('/school/my-exams'),
                        child: Row(children: [
                          const Icon(Icons.event_note),
                          const SizedBox(width: 12),
                          Expanded(child: Text('${tr('Next exam')}: ${_exam!['subjectName']} · ${_exam!['date']} '
                              '${_exam!['startTime']} (${_exam!['exam']})')),
                        ]),
                      ),
                    for (final h in _due)
                      AppCard(
                        margin: const EdgeInsets.only(bottom: 8),
                        onTap: () => context.push('/school/my-homework/${h['id']}'),
                        child: Row(children: [
                          const Icon(Icons.assignment_late_outlined),
                          const SizedBox(width: 12),
                          Expanded(child: Text('${h['title']} · ${h['subjectName']} · ${tr('due')} ${h['dueDate']}')),
                        ]),
                      ),
                    if (_nextLine != null)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Text(_nextLine!, style: Theme.of(context).textTheme.titleSmall),
                      ),
                    const SizedBox(height: 8),
                    if (_rows!.isEmpty)
                      EmptyState(icon: Icons.weekend_outlined, title: tr('No classes'),
                          message: tr('A holiday, a weekly off, or no timetable yet.')),
                    for (final r in _rows!)
                      ListTile(
                        leading: CircleAvatar(child: Text('${r['period']}')),
                        title: Text(r['subjectName'] ?? '', style: TextStyle(
                            decoration: r['kind'] == 'lost' ? TextDecoration.lineThrough : null)),
                        subtitle: Text([
                          if (periodWhenWhere(r).isNotEmpty) periodWhenWhere(r),
                          if (r['teacherName'] != null && r['kind'] != 'lost') r['teacherName'],
                          if (_kind(r['kind'] as String).isNotEmpty) _kind(r['kind'] as String),
                        ].join(' · ')),
                        trailing: r['changed'] == true ? ChipTag(label: tr('Changed')) : null,
                      ),
                  ]),
                ),
    );
  }
}
