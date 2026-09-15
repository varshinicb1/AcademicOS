import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:printing/printing.dart';

import '../../../core/local_engine/local_report_card.dart';
import '../../../core/local_engine/local_report_card_pdf_export.dart';
import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/consent_api.dart';
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
  late Future<List<(String id, String name, StudentMastery? mastery, bool fetchFailed)>> _future;

  @override
  void initState() {
    super.initState();
    _future = _loadRoster();
  }

  // Real bug found by audit: a fetch failure (network error on the
  // server-connected build -- knowledge() never throws offline, it returns
  // a zeroed StudentMastery for a genuinely un-evaluated student) used to
  // be swallowed and shown identically to "no mastery data yet". A teacher
  // scrolling the roster during a network hiccup saw some students silently
  // marked "no data" with no way to tell that from a real absence of data.
  //
  // Real gap found in front of a real school demo: the roster only ever
  // listed students with mastery evidence (allStudentIdsWithMastery) --
  // there was no way to add a student before their first evaluation, so a
  // teacher trying to add their own real class saw nowhere to do it.
  // allNamedStudentIds() includes every student who has a name on file,
  // evaluated or not, so a freshly-added student shows up immediately.
  Future<List<(String id, String name, StudentMastery? mastery, bool fetchFailed)>> _loadRoster() async {
    final ids = LocalStore.instance.allNamedStudentIds()..sort();
    final api = GetIt.I<PillarApi>();
    final rows = <(String, String, StudentMastery?, bool)>[];
    for (final id in ids) {
      StudentMastery? m;
      var fetchFailed = false;
      try {
        m = await api.knowledge(id);
      } catch (_) {
        m = null;
        fetchFailed = true;
      }
      rows.add((id, LocalStore.instance.studentName(id), m, fetchFailed));
    }
    return rows;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Classes')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _addStudent(context),
        icon: const Icon(Icons.person_add_alt_1),
        label: const Text('Add student'),
      ),
      body: FutureBuilder<List<(String, String, StudentMastery?, bool)>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const LoadingIndicator(message: 'Loading roster…');
          }
          final roster = snap.data ?? const [];
          if (roster.isEmpty) {
            return EmptyState(
              icon: Icons.groups_outlined,
              title: 'No students yet',
              message: 'Add your class roster, or students appear here automatically once '
                  'you evaluate their first answer sheet.',
              actionLabel: 'Add student',
              onAction: () => _addStudent(context),
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
              for (final (id, name, mastery, fetchFailed) in roster)
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
                      if (mastery != null && mastery.concepts.isEmpty)
                        // A real 0% here (mastery != null, no concepts at
                        // all) means genuinely never evaluated, not "failing"
                        // -- a red "0% mastery" badge for a freshly-added
                        // student reads as broken/alarming for no reason.
                        const ChipTag(label: 'not yet evaluated', color: Colors.blueGrey)
                      else if (mastery != null)
                        ChipTag(
                          label: '${(mastery.overallMastery * 100).round()}% mastery',
                          color: mastery.overallMastery < 0.4
                              ? Colors.red
                              : (mastery.overallMastery < 0.7 ? Colors.orange : Colors.green),
                        )
                      else if (fetchFailed)
                        const ChipTag(label: 'couldn\'t load', color: Colors.orange)
                      else
                        const ChipTag(label: 'no data'),
                      const SizedBox(width: 4),
                      if (!LocalStore.instance.isDemoStudent(id))
                        IconButton(
                          tooltip: LocalStore.instance.hasConsent(id)
                              ? 'Parental consent on file'
                              : 'Parental consent required — tap to record',
                          icon: Icon(
                            LocalStore.instance.hasConsent(id) ? Icons.verified_user : Icons.privacy_tip_outlined,
                            color: LocalStore.instance.hasConsent(id) ? Colors.green : Colors.orange,
                          ),
                          onPressed: () => _recordConsent(context, id, name),
                        ),
                      IconButton(
                        tooltip: 'Report card',
                        icon: const Icon(Icons.description_outlined),
                        onPressed: () => _showReportCard(context, id, name),
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

  // Real gap found in front of a real school demo: there was no way to add
  // a real student to the roster at all -- only students who'd already
  // been evaluated ever appeared. Persists via the same LocalStore.
  // setStudentName every other real screen (Mastery, Scan & Grade) already
  // reads from, so an added student is immediately usable everywhere, not
  // just here.
  Future<void> _addStudent(BuildContext context) async {
    final nameController = TextEditingController();
    final rollController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    final added = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Add student'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: nameController,
                autofocus: true,
                decoration: const InputDecoration(labelText: 'Student name *'),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: rollController,
                decoration: const InputDecoration(
                  labelText: 'Roll no. / ID (optional)',
                  helperText: 'Leave blank to generate one automatically',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) Navigator.pop(dialogContext, true);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );

    if (added != true) return;
    final roll = rollController.text.trim();
    final studentId = roll.isNotEmpty ? roll : 'stu_${DateTime.now().millisecondsSinceEpoch}';
    LocalStore.instance.setStudentName(studentId, nameController.text.trim());

    if (!context.mounted) return;
    setState(() {
      _future = _loadRoster();
    });
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text('${nameController.text.trim()} added to the roster')));
  }

  // DPDP Act 2023: every CBSE student is a minor, and this is the point real
  // student data (name + real evaluated marks) actually leaves the device as
  // a document. Demo students are exempt -- they're synthetic, not real
  // children -- but a real student without a recorded consent step is
  // blocked here rather than silently exported, matching the same
  // mandatory-flag-before-write pattern already used for document ingestion
  // (see docs/compliance.md's "New ingestion source" checklist item).
  Future<void> _recordConsent(BuildContext context, String studentId, String studentName) async {
    final existing = LocalStore.instance.getConsent(studentId);
    final guardianController = TextEditingController(text: existing?['guardianName'] as String? ?? '');
    final methodController = TextEditingController(text: existing?['method'] as String? ?? '');
    final formKey = GlobalKey<FormState>();

    final recorded = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text('Parental consent — $studentName'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Record that a real, verifiable consent step already happened outside this '
                'app (a signed admission-form clause naming this specific use, or a confirmed '
                'call/message to the parent/guardian) — this screen logs the record, it does '
                'not itself verify consent.',
                style: TextStyle(fontSize: 12.5),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: guardianController,
                decoration: const InputDecoration(labelText: 'Parent/guardian name *'),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: methodController,
                decoration: const InputDecoration(
                  labelText: 'How consent was obtained *',
                  helperText: 'e.g. "Signed admission form, clause 4" or "Phone call, 12 Aug"',
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) Navigator.pop(dialogContext, true);
            },
            child: const Text('Record consent'),
          ),
        ],
      ),
    );

    if (recorded != true) return;
    final guardianName = guardianController.text.trim();
    final method = methodController.text.trim();

    LocalStore.instance.setConsent(
      studentId,
      method: method,
      guardianName: guardianName,
    );

    // Sync to backend if online and client is registered
    try {
      if (GetIt.I.isRegistered<ConsentApi>()) {
        GetIt.I<ConsentApi>().recordConsent(
          studentId: studentId,
          guardianName: guardianName,
          method: method,
        ).ignore();
      }
    } catch (_) {}

    if (!context.mounted) return;
    setState(() {});
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text('Consent recorded for $studentName')));
  }

  // Real report-card generation -- was a requested feature never built.
  // Aggregates this student's actual evaluated assessments and mastery
  // record (LocalReportCardService, no invented data) into a real PDF the
  // teacher can view immediately.
  Future<void> _showReportCard(BuildContext context, String studentId, String studentName) async {
    if (!LocalStore.instance.isDemoStudent(studentId) && !LocalStore.instance.hasConsent(studentId)) {
      final proceed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Parental consent required'),
          content: Text(
            'No recorded parental consent for $studentName. This report contains real, '
            'identifiable student data — record consent first (the shield icon on their row) '
            'before exporting it.',
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancel')),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Record consent now'),
            ),
          ],
        ),
      );
      if (proceed == true && context.mounted) {
        await _recordConsent(context, studentId, studentName);
      }
      return;
    }
    if (!context.mounted) return;
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
