import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../core/session/current_session.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../paper_builder/pages/paper_builder_page.dart' show newPaperLocation;
import '../../shared/widgets/shell.dart';
import '../../workspace/ops_api.dart';

/// A signed-in teacher's first screen on the web: today's periods and the
/// lessons planned for them, what is waiting on them, and their recent
/// papers, with one main action, a new paper.
///
/// It replaced, online, the v2 home (review 2026-10-01), which read only the
/// device's own store: on the web its "recent assessments" never showed the
/// papers on the server, today's lessons sat behind a "My Schedule" link, and
/// two full-width filled tiles competed as the main action. The offline build
/// keeps the v2 home, whose data lives on the device.
class TodayPage extends StatefulWidget {
  const TodayPage({super.key, DateTime? now}) : _now = now;

  final DateTime? _now;

  @override
  State<TodayPage> createState() => _TodayPageState();
}

/// One card's data: loading (null), loaded, or the reason it could not load.
class _Load<T> {
  const _Load.ok(this.value) : error = null;
  const _Load.failed(this.error) : value = null;
  final T? value;
  final String? error;
}

class _TodayPageState extends State<TodayPage> {
  late final DateTime _now = widget._now ?? DateTime.now();
  _Load<List<Map<String, dynamic>>>? _periods, _lessons, _reviews, _homework, _papers;

  String get _day =>
      '${_now.year}-${_now.month.toString().padLeft(2, '0')}-${_now.day.toString().padLeft(2, '0')}';

  static const _weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  static const _months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'];
  String get _longDate => '${_weekdays[_now.weekday - 1]}, ${_now.day} ${_months[_now.month - 1]}';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<_Load<List<Map<String, dynamic>>>> _fetch(Future<List<Map<String, dynamic>>> call) async {
    try {
      return _Load.ok(await call);
    } catch (e) {
      return _Load.failed(serverErrorMessage(e));
    }
  }

  Future<void> _load() async {
    setState(() => _periods = _lessons = _reviews = _homework = _papers = null);
    final results = await Future.wait([
      _fetch(Ops.list('/curriculum/my-day', query: {'date': _day})),
      _fetch(Ops.list('/curriculum/my-schedule', query: {'start_date': _day, 'end_date': _day})),
      _fetch(Ops.list('/paper-reviews', query: {'state': 'pending'})),
      _fetch(Ops.list('/homework')),
      _fetch(Ops.list('/assessments', query: {'teacher_id': CurrentSession.userId})),
    ]);
    if (!mounted) return;
    setState(() {
      _periods = results[0];
      _lessons = results[1];
      _reviews = results[2];
      _homework = results[3];
      _papers = results[4];
    });
  }

  String get _greeting {
    final h = _now.hour;
    final hello = h < 12 ? 'Good morning' : (h < 17 ? 'Good afternoon' : 'Good evening');
    final name = (LocalStore.instance.authUser?['name'] as String? ?? '').trim().split(' ').first;
    return name.isEmpty ? hello : '$hello, $name';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final wide = MediaQuery.sizeOf(context).width >= 1100;
    final day = _dayCard(context);
    final needs = _needsCard(context);
    final papers = _papersCard(context);
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Today'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: FilledButton.icon(
              onPressed: () => context.push(newPaperLocation()),
              icon: const Icon(Icons.add, size: 18),
              label: const Text('New paper'),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
          children: [
            Text(_greeting, style: theme.textTheme.headlineMedium),
            const SizedBox(height: 2),
            Text(_longDate,
                style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 20),
            if (wide)
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Expanded(flex: 3, child: Column(children: [day, const SizedBox(height: 16), papers])),
                const SizedBox(width: 16),
                Expanded(flex: 2, child: needs),
              ])
            else ...[
              day,
              const SizedBox(height: 16),
              needs,
              const SizedBox(height: 16),
              papers,
            ],
          ],
        ),
      ),
    );
  }

  // ---------------- your day ----------------

  Widget _dayCard(BuildContext context) {
    final periods = _periods, lessons = _lessons;
    Widget body;
    if (periods == null || lessons == null) {
      body = const _Loading();
    } else if (periods.error != null && lessons.error != null) {
      body = _Problem(message: periods.error!, onRetry: _load);
    } else {
      final rows = [...?periods.value]..sort((a, b) => (a['period'] as num).compareTo(b['period'] as num));
      final planned = lessons.value ?? const [];
      if (rows.isEmpty && planned.isEmpty) {
        body = const _Quiet(text: 'No periods or lessons today.');
      } else {
        body = Column(children: [
          for (final r in rows) _PeriodRow(row: r),
          if (planned.isNotEmpty) ...[
            if (rows.isNotEmpty) const Divider(height: 1),
            for (final l in planned) _LessonRow(lesson: l),
          ],
        ]);
      }
    }
    return _Card(
      title: 'Your day',
      action: TextButton(onPressed: () => context.go('/school/week'), child: const Text('Week view')),
      child: body,
    );
  }

  // ---------------- needs you ----------------

  Widget _needsCard(BuildContext context) {
    final reviews = _reviews, homework = _homework;
    Widget body;
    if (reviews == null || homework == null) {
      body = const _Loading();
    } else {
      final items = <Widget>[
        for (final r in reviews.value ?? const <Map<String, dynamic>>[])
          _NeedRow(
            title: 'Review: ${(r['title'] as String?)?.isNotEmpty == true ? r['title'] : 'a paper'}',
            detail: (r['requestNote'] as String?)?.isNotEmpty == true
                ? r['requestNote'] as String
                : 'A colleague asked for your review',
            action: 'Review',
            onTap: () => context.push('/assessment/${r['assessmentId']}'),
          ),
        for (final h in homework.value ?? const <Map<String, dynamic>>[])
          if (((h['submitted'] as num?) ?? 0) > ((h['graded'] as num?) ?? 0))
            _NeedRow(
              title: 'Mark ${((h['submitted'] as num) - ((h['graded'] as num?) ?? 0)).toInt()} submissions',
              detail: '${(h['sectionNames'] as List?)?.join(', ') ?? ''} · ${h['title']}',
              action: 'Mark',
              onTap: () => context.push('/school/homework/${h['id']}'),
            ),
      ];
      final failed = [reviews.error, homework.error].whereType<String>().toList();
      body = Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        ...items,
        if (items.isEmpty && failed.isEmpty) const _Quiet(text: 'Nothing is waiting for you.'),
        for (final f in failed) _Problem(message: f, onRetry: _load),
      ]);
    }
    return _Card(title: 'Needs you', child: body);
  }

  // ---------------- recent papers ----------------

  Widget _papersCard(BuildContext context) {
    final papers = _papers;
    Widget body;
    if (papers == null) {
      body = const _Loading();
    } else if (papers.error != null) {
      body = _Problem(message: papers.error!, onRetry: _load);
    } else {
      final list = [...papers.value!]
        ..sort((a, b) => (b['updatedAt'] as String? ?? '').compareTo(a['updatedAt'] as String? ?? ''));
      body = list.isEmpty
          ? const _Quiet(text: 'Your papers will appear here. Start one with New paper.')
          : Column(children: [for (final a in list.take(5)) _PaperRow(paper: a)]);
    }
    return _Card(
      title: 'Recent papers',
      action: TextButton(onPressed: () => context.go('/assessment'), child: const Text('All papers')),
      child: body,
    );
  }
}

// ---------------- pieces ----------------

class _Card extends StatelessWidget {
  const _Card({required this.title, required this.child, this.action});

  final String title;
  final Widget child;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.outlineVariant),
      ),
      child: Material(
        type: MaterialType.transparency,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 8, 12),
            child: Row(children: [
              Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
              if (action != null) action!,
            ]),
          ),
          Divider(height: 1, color: colors.outlineVariant),
          child,
        ]),
      ),
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading();

  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
      );
}

class _Quiet extends StatelessWidget {
  const _Quiet({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Text(text,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      );
}

class _Problem extends StatelessWidget {
  const _Problem({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final status = StatusColors.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 8, 12),
      child: Row(children: [
        Icon(Icons.error_outline, size: 18, color: status.danger),
        const SizedBox(width: 8),
        Expanded(child: Text(message, style: TextStyle(color: status.danger))),
        TextButton(onPressed: onRetry, child: const Text('Try again')),
      ]),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.label, this.fg, this.bg, this.line);

  final String label;
  final Color fg, bg, line;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999), border: Border.all(color: line)),
        child: Text(label, style: Theme.of(context).textTheme.labelMedium?.copyWith(color: fg)),
      );
}

class _PeriodRow extends StatelessWidget {
  const _PeriodRow({required this.row});

  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final s = StatusColors.of(context);
    final kind = row['kind'] as String? ?? 'regular';
    final chip = switch (kind) {
      'substitute' || 'supervised' => _Chip('Cover', s.info, s.infoBg, s.infoBorder),
      'makeup' => _Chip('Make-up', s.info, s.infoBg, s.infoBorder),
      'lost' || 'uncovered' => _Chip('Not held', s.danger, s.dangerBg, s.dangerBorder),
      'away' => _Chip('You are away', s.warning, s.warningBg, s.warningBorder),
      'co_teacher' || 'combined' => _Chip('Shared', s.success, s.successBg, s.successBorder),
      _ => null,
    };
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),
      child: Row(children: [
        SizedBox(width: 72, child: Text('Period ${row['period']}',
            style: theme.textTheme.bodySmall)),
        SizedBox(width: 64, child: Text(row['sectionName'] as String? ?? '', style: theme.textTheme.titleSmall)),
        Expanded(child: Text(row['subjectName'] as String? ?? '', style: theme.textTheme.bodyMedium)),
        if (chip != null) chip,
      ]),
    );
  }
}

class _LessonRow extends StatelessWidget {
  const _LessonRow({required this.lesson});

  final Map<String, dynamic> lesson;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final where = [lesson['sectionName'], lesson['subjectName']].whereType<String>().where((x) => x.isNotEmpty).join(' ');
    final taught = lesson['status'] == 'completed';
    return ListTile(
      dense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 20),
      leading: Icon(taught ? Icons.check_circle_outline : Icons.menu_book_outlined, size: 20),
      title: Text(lesson['subtopicName'] as String? ?? lesson['topicName'] as String? ?? ''),
      subtitle: Text([if (where.isNotEmpty) where, lesson['chapterName']].whereType<String>().join(' · ')),
      trailing: taught ? Text('Taught', style: theme.textTheme.labelMedium) : null,
      onTap: () => context.push('/my-schedule'),
    );
  }
}

class _NeedRow extends StatelessWidget {
  const _NeedRow({required this.title, required this.detail, required this.action, required this.onTap});

  final String title, detail, action;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 10, 12, 10),
      child: Row(children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: theme.textTheme.titleSmall),
            Text(detail, style: theme.textTheme.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis),
          ]),
        ),
        const SizedBox(width: 8),
        OutlinedButton(onPressed: onTap, child: Text(action)),
      ]),
    );
  }
}

class _PaperRow extends StatelessWidget {
  const _PaperRow({required this.paper});

  final Map<String, dynamic> paper;

  @override
  Widget build(BuildContext context) {
    final s = StatusColors.of(context);
    final status = paper['status'] as String? ?? '';
    final chip = switch (status) {
      'underReview' => _Chip('In review', s.warning, s.warningBg, s.warningBorder),
      'paperGenerated' => _Chip('Ready', s.info, s.infoBg, s.infoBorder),
      'draft' || 'blueprintReady' || 'questionsSelected' || 'questionOptimized' =>
        _Chip('Draft', Theme.of(context).colorScheme.onSurfaceVariant, Theme.of(context).colorScheme.surfaceContainer,
            Theme.of(context).colorScheme.outlineVariant),
      _ => _Chip('Approved', s.success, s.successBg, s.successBorder),
    };
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 20),
      title: Text(paper['title'] as String? ?? 'Untitled paper'),
      subtitle: Text('Class ${paper['grade']} · ${paper['subject']}'),
      trailing: chip,
      onTap: () => context.push('/assessment/${paper['id']}'),
    );
  }
}
