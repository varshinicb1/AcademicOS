import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../core/download/pdf_saver.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';
import 'teacher_homework.dart' show TeachingContext;
import '../shared/widgets/shell.dart';

/// The term at a glance (ADM-2) for the principal or a reports admin:
/// syllabus against plan, exams and papers, time saved (estimated),
/// homework, cover, the question bank's gaps and how students are doing --
/// filtered by class, section or subject, and downloadable as Excel or PDF
/// (ADM-4). Aggregates only: no student or teacher is named.
class TermReportPage extends StatefulWidget {
  const TermReportPage({super.key});

  @override
  State<TermReportPage> createState() => _TermReportPageState();
}

class _TermReportPageState extends State<TermReportPage> {
  TeachingContext? _ctx;
  String? _filtersError;
  List<Map<String, dynamic>> _terms = const [];
  String? _term;
  String? _termsError;
  int? _grade;
  String? _section;
  String? _subject;
  late Future<Map<String, dynamic>> _future = _fetch();
  bool _downloading = false;

  @override
  void initState() {
    super.initState();
    TeachingContext.load().then((c) async {
      if (mounted) setState(() => _ctx = c);
      // The terms of the same year, so any term can be reported (N-67-7).
      try {
        final terms = await Ops.list('/curriculum/academic-years/${c.yearId}/terms');
        if (mounted) setState(() => _terms = terms);
      } catch (e) {
        if (mounted) setState(() => _termsError = serverErrorMessage(e));
      }
    }, onError: (Object e) {
      if (mounted) setState(() => _filtersError = serverErrorMessage(e));
    });
  }

  Map<String, dynamic> get _query => {
        if (_term != null) 'termId': _term,
        if (_grade != null) 'grade': _grade,
        if (_section != null) 'sectionId': _section,
        if (_subject != null) 'subject': _subject,
      };

  Future<Map<String, dynamic>> _fetch() => Ops.map('/dashboard/term', query: _query);

  void _reload() => setState(() { _future = _fetch(); });

  Future<void> _download(String format) async {
    setState(() => _downloading = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final bytes = await Ops.bytes('/dashboard/term/export', query: {..._query, 'format': format});
      await GetIt.I<PdfSaver>().save(bytes, 'term-report.$format');
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Term report')), actions: [
        IconButton(tooltip: tr('Download Excel'), onPressed: _downloading ? null : () => _download('xlsx'),
            icon: const Icon(Icons.grid_on_outlined)),
        IconButton(tooltip: tr('Download PDF'), onPressed: _downloading ? null : () => _download('pdf'),
            icon: const Icon(Icons.picture_as_pdf_outlined)),
      ]),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            _filters(),
            ..._report(context, snap.data!),
          ]);
        },
      ),
    );
  }

  Widget _filters() {
    final ctx = _ctx;
    if (_filtersError != null) {
      return Text('${tr('Filters are not available')}: $_filtersError',
          style: TextStyle(color: Theme.of(context).colorScheme.error));
    }
    if (ctx == null) return const SizedBox.shrink();
    int gradeOf(String label) => int.tryParse(label.split('-').first) ?? 0;
    final grades = {for (final l in ctx.sectionLabels.values) gradeOf(l)}.toList()..sort();
    final sections = ctx.sectionLabels.entries.where((e) => _grade == null || gradeOf(e.value) == _grade).toList()
      ..sort((a, b) => a.value.compareTo(b.value));
    final subjects = ctx.subjectNames.values.toSet().toList()..sort();
    return Wrap(spacing: 12, runSpacing: 8, children: [
      if (_termsError != null)
        Text('${tr('Terms are not available')}: $_termsError',
            style: TextStyle(color: Theme.of(context).colorScheme.error)),
      if (_terms.isNotEmpty)
        DropdownButton<String?>(
          key: const Key('term-picker'),
          value: _term,
          hint: Text(tr('This term')),
          items: [
            DropdownMenuItem(value: null, child: Text(tr('This term'))),
            for (final t in _terms) DropdownMenuItem(value: t['id'] as String, child: Text(t['name'] as String)),
          ],
          onChanged: (t) {
            _term = t;
            _reload();
          },
        ),
      DropdownButton<int?>(
        value: _grade,
        hint: Text(tr('All classes')),
        items: [
          DropdownMenuItem(value: null, child: Text(tr('All classes'))),
          for (final g in grades) DropdownMenuItem(value: g, child: Text('${tr('Class')} $g')),
        ],
        onChanged: (g) {
          _grade = g;
          _section = null;
          _reload();
        },
      ),
      DropdownButton<String?>(
        value: _section,
        hint: Text(tr('All sections')),
        items: [
          DropdownMenuItem(value: null, child: Text(tr('All sections'))),
          for (final s in sections) DropdownMenuItem(value: s.key, child: Text(s.value)),
        ],
        onChanged: (s) {
          _section = s;
          _reload();
        },
      ),
      DropdownButton<String?>(
        value: _subject,
        hint: Text(tr('All subjects')),
        items: [
          DropdownMenuItem(value: null, child: Text(tr('All subjects'))),
          for (final s in subjects) DropdownMenuItem(value: s, child: Text(s)),
        ],
        onChanged: (s) {
          _subject = s;
          _reload();
        },
      ),
    ]);
  }

  List<Widget> _report(BuildContext context, Map<String, dynamic> d) {
    final theme = Theme.of(context);
    final scope = d['scope'] as Map;
    final syllabus = d['syllabus'] as Map;
    final exams = d['exams'] as Map;
    final time = d['timeSaved'] as Map;
    final homework = d['homework'] as Map;
    final cover = d['cover'] as Map;
    final behind = (syllabus['rows'] as List).cast<Map>().where((r) => r['behind'] == true).toList();
    final gaps = (d['bank'] as List).cast<Map>()
        .where((b) => b['questions'] == 0 || (b['chaptersWithoutQuestions'] as List).isNotEmpty).toList();
    Widget stat(String label, Object value) => SizedBox(
          width: 170,
          child: Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [Text('$value', style: theme.textTheme.headlineSmall), Text(label, style: theme.textTheme.bodySmall)]))),
        );
    return [
      const SizedBox(height: 12),
      Text('${scope['name']} · ${scope['startDate']} – ${scope['endDate']}', style: theme.textTheme.titleMedium),
      Text('${tr('As of')} ${scope['asOf']}', style: theme.textTheme.bodySmall),
      if (scope['note'] != null)
        Padding(padding: const EdgeInsets.only(top: 6), child: Text(scope['note'] as String, style: theme.textTheme.bodySmall)),
      // The page that does what the note asks, not a description of it (audit D43).
      if (scope['noteLink'] is String)
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            key: const Key('term-report-setup'),
            onPressed: () => context.go(scope['noteLink'] as String),
            icon: const Icon(Icons.arrow_forward),
            label: Text(tr('Declare terms')),
          ),
        ),
      const SizedBox(height: 12),
      Wrap(spacing: 8, runSpacing: 8, children: [
        stat(tr('Lessons taught / planned'), '${syllabus['taughtToDate']} / ${syllabus['plannedToDate']}'),
        stat(tr('Classes behind plan'), syllabus['behind']),
        stat(tr('Papers set'), exams['papersSet']),
        stat(tr('Minutes saved (estimated)'), time['minutesTotal']),
        stat(tr('Homework handed in'), '${homework['handedIn']} / ${homework['expected']}'),
        stat(tr('Unfilled cover'), cover['unfilled']),
        stat(tr('Periods still owed'), cover['owed']),
      ]),
      SectionHeader(title: tr('Behind the plan'), subtitle: tr('Lessons taught against the plan to date')),
      if (behind.isEmpty) Text(tr('Every class is on plan.')),
      for (final r in behind)
        ListTile(dense: true, title: Text('${r['sectionName'] ?? '${tr('Class')} ${r['grade']}'} · ${r['subject']}'),
            subtitle: Text('${r['taughtToDate']} ${tr('of')} ${r['plannedToDate']} ${tr('lessons')} · ${r['variance']}')),
      SectionHeader(title: tr('Exams'), subtitle: tr('Scheduled this term, and classes with no paper yet')),
      for (final e in (exams['scheduled'] as List).cast<Map>())
        ListTile(dense: true, title: Text(e['name']), subtitle: Text('${e['startDate']} – ${e['endDate']} · ${e['status']}')),
      if ((exams['notYet'] as List).isNotEmpty)
        Padding(padding: const EdgeInsets.symmetric(vertical: 6), child: Text(
            '${tr('No paper yet')}: ${(exams['notYet'] as List).cast<Map>().map((c) => '${c['grade']} ${c['subject']}').join(', ')}')),
      // The bank's gap, apart from the teachers' (audit D117).
      if ((exams['noQuestions'] as List? ?? const []).isNotEmpty)
        Padding(padding: const EdgeInsets.symmetric(vertical: 6), child: Text(
            key: const Key('term-report-no-questions'),
            '${tr('The question bank has no questions for these classes yet')}: '
            '${(exams['noQuestions'] as List).cast<Map>().map((c) => '${c['grade']} ${c['subject']}').join(', ')}')),
      Text('${tr('Time saved is an estimate')}: ${time['minutesPerPaper']} min × ${time['papers']} · '
          '${time['papersWithTeacherTime'] ?? 0} ${tr('of')} ${time['papers']} ${tr('less the teacher\'s measured time')} · '
          '${time['baselineProvenance']}',
          style: theme.textTheme.bodySmall),
      SectionHeader(title: tr('Homework'), subtitle: tr('Issued this term and handed in')),
      for (final h in (homework['rows'] as List).cast<Map>())
        ListTile(dense: true, title: Text('${tr('Class')} ${h['grade']} · ${h['subject']}'),
            subtitle: Text('${h['issued']} ${tr('set')} · ${h['handedIn']} / ${h['expected']} ${tr('handed in')} · ${h['marked']} ${tr('marked')}')),
      SectionHeader(title: tr('Cover'), subtitle: tr('Substitutions and lost periods')),
      Text('${cover['requested']} ${tr('requested')} · ${cover['filled']} ${tr('filled')} · ${cover['supervised']} '
          '${tr('supervised')} · ${cover['unfilled']} ${tr('unfilled')} · ${cover['lost']} ${tr('lost')} · '
          '${cover['compensated']} ${tr('made up')}'),
      SectionHeader(title: tr('Question bank gaps'), subtitle: tr('Chapters of your classes with no questions yet')),
      if (gaps.isEmpty) Text(tr('No gaps for these classes.')),
      for (final b in gaps)
        ListTile(dense: true, title: Text('${tr('Class')} ${b['grade']} · ${b['subject']} · ${b['questions']} '
            '${tr(b['questions'] == 1 ? 'question' : 'questions')}'),
            subtitle: Text(b['chapters'] == 0
                ? tr('No questions for this class yet')
                : (b['chaptersWithoutQuestions'] as List).join(', '))),
      SectionHeader(title: tr('How students are doing'), subtitle: tr('Chapters at each level, from marked work')),
      if ((d['progress'] as List).isEmpty) Text(tr('No marked work yet')),
      for (final p in (d['progress'] as List).cast<Map>())
        ListTile(dense: true, title: Text('${tr('Class')} ${p['grade']} · ${p['subject']} · ${p['studentsWithEvidence']} ${tr('students')}'),
            subtitle: Text('${p['mastered']} ${tr('mastered')} · ${p['developing']} ${tr('developing')} · '
                '${p['needsWork']} ${tr('needs work')} · ${p['early']} ${tr('too early to say')}')),
    ];
  }
}
