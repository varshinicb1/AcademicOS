import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:printing/printing.dart';

import '../../../core/local_engine/local_report_card.dart';
import '../../../core/local_engine/local_report_card_pdf_export.dart';
import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Real class roster -- was a dead `() {}` button before this. Lists every
/// student with real mastery evidence (LocalStore.allStudentIdsWithMastery,
/// the same real data source Mastery's picker now uses) and their real
/// overall mastery percentage, tapping through to their full Mastery view.
class ClassesPage extends StatefulWidget {
  const ClassesPage({super.key});

  @override
  State<ClassesPage> createState() => _ClassesPageState();
}

class _ClassesPageState extends State<ClassesPage> {
  late Future<List<(String id, String name, StudentMastery? mastery)>> _future;

  @override
  void initState() {
    super.initState();
    _future = _loadRoster();
  }

  Future<List<(String id, String name, StudentMastery? mastery)>> _loadRoster() async {
    final ids = LocalStore.instance.allStudentIdsWithMastery()..sort();
    final api = GetIt.I<PillarApi>();
    final rows = <(String, String, StudentMastery?)>[];
    for (final id in ids) {
      StudentMastery? m;
      try {
        m = await api.knowledge(id);
      } catch (_) {
        m = null;
      }
      rows.add((id, LocalStore.instance.studentName(id), m));
    }
    return rows;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Classes')),
      body: FutureBuilder<List<(String, String, StudentMastery?)>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Loading roster…');
          }
          final roster = snap.data ?? const [];
          if (roster.isEmpty) {
            return const EmptyState(
              icon: Icons.groups_outlined,
              title: 'No students yet',
              message: 'Students appear here once you evaluate their first answer sheet.',
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('Class X — ${roster.length} student${roster.length == 1 ? '' : 's'}',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text('Real mastery from every evaluated answer sheet, not a placeholder.',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const SizedBox(height: 16),
              for (final (id, name, mastery) in roster)
                AppCard(
                  onTap: () => context.push('/analytics/mastery', extra: {'studentId': id}),
                  child: Row(
                    children: [
                      CircleAvatar(
                        backgroundColor: theme.colorScheme.secondaryContainer,
                        child: Text(name.isNotEmpty ? name[0].toUpperCase() : '?',
                            style: TextStyle(color: theme.colorScheme.onSecondaryContainer, fontWeight: FontWeight.w700)),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(name, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                            Text(id, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                          ],
                        ),
                      ),
                      if (mastery != null)
                        ChipTag(
                          label: '${(mastery.overallMastery * 100).round()}% mastery',
                          color: mastery.overallMastery < 0.4
                              ? Colors.red
                              : (mastery.overallMastery < 0.7 ? Colors.orange : Colors.green),
                        )
                      else
                        const ChipTag(label: 'no data'),
                      const SizedBox(width: 4),
                      IconButton(
                        tooltip: 'Report card',
                        icon: const Icon(Icons.description_outlined),
                        onPressed: () => _showReportCard(context, id),
                      ),
                    ],
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  // Real report-card generation -- was a requested feature never built.
  // Aggregates this student's actual evaluated assessments and mastery
  // record (LocalReportCardService, no invented data) into a real PDF the
  // teacher can view immediately.
  Future<void> _showReportCard(BuildContext context, String studentId) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    try {
      final data = LocalReportCardService.generate(studentId);
      final path = await LocalReportCardPdfExporter.export(data);
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop(); // close loading dialog
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => Scaffold(
          appBar: AppBar(title: Text('Report Card — ${data.studentName}')),
          body: PdfPreview(build: (format) => File(path).readAsBytes()),
        ),
      ));
    } catch (e) {
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not generate report card: $e')));
    }
  }
}
