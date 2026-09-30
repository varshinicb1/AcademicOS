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
                  Text('${p['examTypeLabel']}: ${p['absent'] == true ? tr('absent') : _n(p['obtained'])}/${p['maximum']}',
                      style: theme.textTheme.bodySmall),
              ])),
            const Gap(8),
            if (subjects.isNotEmpty)
              Text('${tr('Overall')}: ${_n(c['obtained'])}/${c['maximum']}  ${_n(c['percent'])}%  ${c['band'] ?? '-'}',
                  key: const ValueKey('card-overall'), style: theme.textTheme.titleSmall),
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
          ]);
        },
      ),
    );
  }
}
