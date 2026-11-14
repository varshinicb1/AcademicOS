import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../core/download/pdf_saver.dart';
import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// One student's report card for the term today falls in (REQUIREMENTS EX-8):
/// each subject's papers, total, percentage and CBSE grade band, and the
/// term overall, as the server built it from the marks entered. For the
/// student, and for a parent from My children. The PDF is the same card.
class StudentReportCardPage extends StatefulWidget {
  final String studentId;
  final String name;
  const StudentReportCardPage({super.key, required this.studentId, required this.name});

  @override
  State<StudentReportCardPage> createState() => _StudentReportCardPageState();
}

class _StudentReportCardPageState extends State<StudentReportCardPage> {
  late Future<Map<String, dynamic>> _future = Ops.map('/report-cards/students/${widget.studentId}');
  bool _saving = false;
  String? _error;

  Future<void> _download() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final bytes = await Ops.bytes('/report-cards/students/${widget.studentId}/pdf');
      await GetIt.I<PdfSaver>().save(bytes, 'report-card.pdf');
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _n(Object? v) {
    if (v == null) return '-';
    final d = (v as num).toDouble();
    return d == d.roundToDouble() ? d.toInt().toString() : d.toStringAsFixed(1);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text('${tr('Report card')}: ${widget.name}'), actions: [
        IconButton(key: const ValueKey('card-pdf'), tooltip: tr('Download PDF'),
            onPressed: _saving ? null : _download, icon: const Icon(Icons.picture_as_pdf_outlined)),
      ]),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = Ops.map('/report-cards/students/${widget.studentId}'); }));
          }
          final c = snap.data!;
          final subjects = (c['subjects'] as List).cast<Map>();
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text('${c['termName']}${(c['yearLabel'] as String? ?? '').isEmpty ? '' : ', ${c['yearLabel']}'}'
                ' · ${tr('Class')} ${c['section']}', style: theme.textTheme.titleSmall),
            if (_error != null) ...[const Gap(8), Text(_error!, style: TextStyle(color: theme.colorScheme.error))],
            const Gap(12),
            if (subjects.isEmpty) Text(tr('No marks have been entered for this term yet.')),
            for (final s in subjects)
              AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(child: Text(s['subject'] as String, style: theme.textTheme.titleSmall)),
                  Text('${_n(s['obtained'])}/${s['maximum']}  ${_n(s['percent'])}%  ${s['band'] ?? '-'}',
                      key: ValueKey('card-subject-${s['subject']}')),
                ]),
                const Gap(4),
                for (final p in (s['papers'] as List).cast<Map>())
                  Text('${p['examTypeLabel']}: ${p['absent'] == true ? tr('absent') : p['incomplete'] == true ? tr('incomplete') : _n(p['obtained'])}/${p['maximum']}',
                      style: theme.textTheme.bodySmall),
              ])),
            const Gap(8),
            if (subjects.isNotEmpty)
              Text('${tr('Overall')}: ${_n(c['obtained'])}/${c['maximum']}  ${_n(c['percent'])}%  ${c['band'] ?? '-'}',
                  key: const ValueKey('card-overall'), style: theme.textTheme.titleSmall),
            if ((c['remark'] as String? ?? '').isNotEmpty) ...[
              const Gap(12),
              AppCard(key: const ValueKey('card-remark'), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(tr("Class teacher's remark"), style: theme.textTheme.titleSmall),
                const Gap(4),
                Text(c['remark'] as String),
              ])),
            ],
            const Gap(8),
            Text(c['note'] as String? ?? '', style: theme.textTheme.bodySmall),
          ]);
        },
      ),
    );
  }
}

/// For the principal, a teacher given reports, and a class teacher: a term
/// and a section, and the section's report cards as one PDF, a page each.
class ReportCardsPage extends StatefulWidget {
  const ReportCardsPage({super.key});

  @override
  State<ReportCardsPage> createState() => _ReportCardsPageState();
}

class _ReportCardsPageState extends State<ReportCardsPage> {
  late Future<(List<Map<String, dynamic>>, List<Map<String, dynamic>>)> _future = _load();
  String? _termId, _sectionId, _error, _note;
  bool _saving = false;

  Future<(List<Map<String, dynamic>>, List<Map<String, dynamic>>)> _load() async {
    final years = await Ops.list('/curriculum/academic-years', query: {'school_id': CurrentSession.schoolId});
    if (years.isEmpty) throw OpsError(409, tr('Your school has no academic year set up yet.'));
    years.sort((a, b) => (a['startDate'] as String).compareTo(b['startDate'] as String));
    final yearId = years.last['id'] as String;
    final terms = await Ops.list('/curriculum/academic-years/$yearId/terms');
    final sections = await Ops.list('/curriculum/academic-years/$yearId/sections');
    final today = DateTime.now().toIso8601String().substring(0, 10);
    _termId = terms.where((t) => (t['startDate'] as String).compareTo(today) <= 0
        && (t['endDate'] as String).compareTo(today) >= 0).firstOrNull?['id'] as String?
        ?? terms.lastOrNull?['id'] as String?;
    return (terms, sections);
  }

  Future<void> _download() async {
    setState(() {
      _saving = true;
      _error = null;
      _note = null;
    });
    try {
      final bytes = await Ops.bytes('/report-cards/sections/$_sectionId/pdf', query: {'termId': _termId});
      await GetIt.I<PdfSaver>().save(bytes, 'report-cards.pdf');
      if (mounted) setState(() => _note = tr('Downloaded.'));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(tr('Report cards'))),
      body: FutureBuilder(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = _load(); }));
          }
          final (terms, sections) = snap.data!;
          if (terms.isEmpty) {
            return EmptyState(icon: Icons.date_range_outlined, title: tr('No terms yet'),
                message: tr('Declare the school\'s terms on Calendar & Setup: a report card is for a term.'));
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text(tr('Every student of a section, one page each: the term\'s marks by subject, with CBSE grades.'),
                style: theme.textTheme.bodySmall),
            const Gap(12),
            DropdownButtonFormField<String>(
              key: const ValueKey('rc-term'),
              initialValue: _termId,
              isExpanded: true,
              decoration: InputDecoration(labelText: tr('Term'), border: const OutlineInputBorder()),
              items: [for (final t in terms) DropdownMenuItem(value: t['id'] as String, child: Text(t['name'] as String))],
              onChanged: (v) => setState(() => _termId = v),
            ),
            const Gap(12),
            DropdownButtonFormField<String>(
              key: const ValueKey('rc-section'),
              initialValue: _sectionId,
              isExpanded: true,
              decoration: InputDecoration(labelText: tr('Section'), border: const OutlineInputBorder()),
              items: [
                for (final s in sections)
                  DropdownMenuItem(value: s['id'] as String, child: Text('${s['gradeNumber']}-${s['name']}')),
              ],
              onChanged: (v) => setState(() => _sectionId = v),
            ),
            if (_error != null) ...[const Gap(8), Text(_error!, style: TextStyle(color: theme.colorScheme.error))],
            if (_note != null) ...[const Gap(8), Text(_note!, style: theme.textTheme.bodySmall)],
            const Gap(12),
            FilledButton.icon(
              key: const ValueKey('rc-download'),
              onPressed: _saving || _termId == null || _sectionId == null ? null : _download,
              style: phoneTapTarget(context),
              icon: const Icon(Icons.picture_as_pdf_outlined),
              label: Text(tr('Download the report cards (PDF)')),
            ),
            const Gap(8),
            OutlinedButton.icon(
              key: const ValueKey('rc-remarks'),
              onPressed: _termId == null || _sectionId == null
                  ? null
                  : () => Navigator.of(context).push(MaterialPageRoute<void>(
                      builder: (_) => ReportRemarksPage(sectionId: _sectionId!, termId: _termId!))),
              style: phoneTapTarget(context),
              icon: const Icon(Icons.edit_note_outlined),
              label: Text(tr('Write the remarks')),
            ),
          ]);
        },
      ),
    );
  }
}

/// The class teacher's remark for each student of a section (EX-8). Each
/// box opens on the saved remark, or on a draft the server made from the
/// student's marks, so a class is read, corrected and saved in one go rather
/// than written from nothing. Only what is saved reaches the cards.
class ReportRemarksPage extends StatefulWidget {
  final String sectionId;
  final String termId;
  const ReportRemarksPage({super.key, required this.sectionId, required this.termId});

  @override
  State<ReportRemarksPage> createState() => _ReportRemarksPageState();
}

class _ReportRemarksPageState extends State<ReportRemarksPage> {
  Map<String, dynamic>? _data;
  String? _error, _saveError;
  bool _saving = false;
  final Map<String, TextEditingController> _text = {};

  String get _path => '/report-cards/sections/${widget.sectionId}/remarks';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _text.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _take(Map<String, dynamic> d) {
    for (final r in (d['rows'] as List).cast<Map>()) {
      final id = r['studentId'] as String;
      final text = (r['remark'] ?? r['draft'] ?? '') as String;
      (_text[id] ??= TextEditingController()).text = text;
    }
    _data = d;
  }

  Future<void> _load() async {
    setState(() {
      _error = null;
      _data = null;
    });
    try {
      final d = await Ops.map(_path, query: {'termId': widget.termId});
      if (mounted) setState(() => _take(d));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  /// Every box whose text differs from what is saved: a draft kept as it is
  /// is saved too, and an emptied box removes the remark.
  Future<void> _save() async {
    final rows = (_data!['rows'] as List).cast<Map>();
    final changed = [
      for (final r in rows)
        if (_text[r['studentId']]!.text.trim() != ((r['remark'] as String?) ?? ''))
          {'studentId': r['studentId'], 'remark': _text[r['studentId']]!.text.trim()},
    ];
    if (changed.isEmpty) return;
    setState(() {
      _saving = true;
      _saveError = null;
    });
    try {
      final d = Map<String, dynamic>.from(await Ops.put(_path, body: {'remarks': changed},
          query: {'termId': widget.termId}) as Map);
      if (!mounted) return;
      setState(() => _take(d));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(tr('Remarks saved'))));
    } catch (e) {
      if (mounted) setState(() => _saveError = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _n(Object? v) {
    if (v == null) return '-';
    final d = (v as num).toDouble();
    return d == d.roundToDouble() ? d.toInt().toString() : d.toStringAsFixed(1);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final d = _data;
    return Scaffold(
      appBar: AppBar(title: Text(d == null ? tr('Remarks') : '${tr('Remarks')}: ${d['section']}, ${d['termName']}')),
      body: _error != null
          ? ErrorDisplay(message: _error!, onRetry: _load)
          : d == null
              ? const LoadingIndicator()
              : ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 96), children: [
                  Text(tr('A remark not yet saved is drafted from the student\'s marks. Read it, change what you '
                      'would say differently, and save. Only saved remarks are printed on the cards.'),
                      style: theme.textTheme.bodySmall),
                  if (_saveError != null) ...[
                    const Gap(8),
                    Text(_saveError!, style: TextStyle(color: theme.colorScheme.error)),
                  ],
                  const Gap(12),
                  for (final r in (d['rows'] as List).cast<Map>())
                    AppCard(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          Expanded(child: Text(r['studentName'] as String, style: theme.textTheme.titleSmall)),
                          if (r['percent'] != null) Text('${_n(r['percent'])}%  ${r['band'] ?? ''}'),
                        ]),
                        const Gap(4),
                        Text(r['remark'] != null
                                ? tr('Saved')
                                : r['draft'] != null
                                    ? tr('Draft from the marks: not saved yet')
                                    : tr('No marks this term yet: write one, or leave it empty'),
                            style: theme.textTheme.bodySmall),
                        const Gap(6),
                        TextField(
                          key: ValueKey('remark-${r['studentId']}'),
                          controller: _text[r['studentId']],
                          maxLines: null,
                          maxLength: 600,
                          decoration: const InputDecoration(border: OutlineInputBorder()),
                        ),
                      ]),
                    ),
                ]),
      floatingActionButton: d == null
          ? null
          : FloatingActionButton.extended(
              key: const ValueKey('remarks-save'),
              onPressed: _saving ? null : _save,
              icon: const Icon(Icons.save_outlined),
              label: Text(tr('Save remarks')),
            ),
    );
  }
}
