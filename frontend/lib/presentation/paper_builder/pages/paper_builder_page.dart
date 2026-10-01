import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../../core/download/pdf_saver.dart' as download;
import '../../../core/session/current_session.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../../shared/widgets/shell.dart';
import '../builder_memory.dart';
import '../paper_builder_controller.dart';
import '../widgets/class_subject_step.dart';
import '../widgets/finish_step.dart';
import '../widgets/hand_pick_step.dart';
import '../widgets/paper_step.dart';
import '../widgets/scope_step.dart';
import '../widgets/template_step.dart';

/// Where to send a teacher who wants a new paper. The builder talks to the
/// server's template API, which the offline Android build does not have; that
/// build keeps the older on-device create flow.
String newPaperLocation({bool quick = false}) {
  const offline = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
  if (offline) return '/assessment/create';
  return quick ? '/assessment/build?quick=1' : '/assessment/build';
}

/// The guided paper builder (Task 902): class and subject, a template, the
/// chapters, generate, fix any question, download. One screen family, so a
/// teacher on a phone browser always sees where they are and the one thing
/// to do next in the bar at the bottom.
class PaperBuilderPage extends StatefulWidget {
  final bool quick;
  final PaperBuilderApi? api;
  final PdfSaver? savePdf;
  final String? schoolId;
  final String? userId;

  const PaperBuilderPage({super.key, this.quick = false, this.api, this.savePdf, this.schoolId, this.userId});

  @override
  State<PaperBuilderPage> createState() => _PaperBuilderPageState();
}

class _PaperBuilderPageState extends State<PaperBuilderPage> {
  late final PaperBuilderController c;

  @override
  void initState() {
    super.initState();
    // Identity from the signed-in session (Task 604), never a demo default;
    // the PDF goes through PdfSaver: a browser download on the web.
    c = PaperBuilderController(
      api: widget.api ?? GetIt.I<PaperBuilderApi>(),
      schoolId: widget.schoolId ?? CurrentSession.schoolId,
      memory: BuilderMemory(widget.userId ?? CurrentSession.userId),
      savePdf: widget.savePdf ?? GetIt.I<download.PdfSaver>().save,
      quick: widget.quick,
    )..start();
  }

  @override
  void dispose() {
    c.dispose();
    super.dispose();
  }

  static const _titles = {
    BuilderStep.classSubject: 'Class & subject',
    BuilderStep.template: 'Template',
    BuilderStep.scope: 'Chapters',
    BuilderStep.paper: 'Review paper',
    BuilderStep.finish: 'Download',
  };

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final theme = Theme.of(context);
        return PopScope(
          canPop: c.step.index == 0,
          onPopInvokedWithResult: (didPop, _) {
            if (!didPop) c.back();
          },
          child: Scaffold(
            appBar: AppBar(
              leading: c.step.index == 0
                  ? shellLeading(context)
                  : IconButton(tooltip: 'Back', icon: const Icon(Icons.arrow_back), onPressed: c.back),
              title: Text(widget.quick ? 'Quick paper (CBSE pattern)' : 'New question paper'),
              bottom: PreferredSize(
                preferredSize: const Size.fromHeight(28),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                  child: Row(children: [
                    Expanded(
                      child: Text(
                          'Step ${c.step.index + 1} of 5 · '
                          '${c.handPicked && c.step == BuilderStep.scope ? 'Questions' : _titles[c.step]}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.labelLarge?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                    ),
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 80,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(value: (c.step.index + 1) / 5, minHeight: 6),
                      ),
                    ),
                  ]),
                ),
              ),
            ),
            body: SafeArea(
              bottom: false,
              child: Align(
                alignment: Alignment.topCenter,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 880),
                  child: switch (c.step) {
                    BuilderStep.classSubject => ClassSubjectStep(c: c),
                    BuilderStep.template => TemplateStep(c: c),
                    BuilderStep.scope => c.handPicked ? HandPickStep(c: c) : ScopeStep(c: c),
                    BuilderStep.paper => PaperStep(c: c),
                    BuilderStep.finish => FinishStep(c: c),
                  },
                ),
              ),
            ),
            bottomNavigationBar: _PrimaryBar(c: c),
          ),
        );
      },
    );
  }
}

/// The one action that moves the paper forward, pinned to the bottom on
/// every width -- a teacher never scrolls to find "Generate".
class _PrimaryBar extends StatelessWidget {
  final PaperBuilderController c;
  const _PrimaryBar({required this.c});

  @override
  Widget build(BuildContext context) {
    final (label, icon, onPressed, busy) = switch (c.step) {
      BuilderStep.classSubject => (
          'Next: choose a template',
          Icons.arrow_forward,
          c.canLeaveClassSubject ? c.confirmClassSubject : null,
          false,
        ),
      BuilderStep.template => (
          c.template == null ? 'Choose a template above' : 'Use "${c.template!.name}"',
          Icons.arrow_forward,
          c.template == null ? null : () => c.useTemplate(c.template!),
          false,
        ),
      BuilderStep.scope when c.handPicked => (
          c.generating
              ? 'Generating…'
              : c.picked.isEmpty
                  ? 'Pick questions to make the paper'
                  : 'Generate paper (${c.picked.length} question${c.picked.length == 1 ? '' : 's'}, '
                      '${c.pickedMarks} marks)',
          Icons.auto_awesome,
          c.canGenerateFromPicked ? c.generateFromPicked : null,
          c.generating,
        ),
      BuilderStep.scope => (
          _generateLabel(c),
          Icons.auto_awesome,
          c.canGenerate ? c.generate : null,
          c.generating || c.checking,
        ),
      BuilderStep.paper => ('Done: download', Icons.download, () => c.goTo(BuilderStep.finish), false),
      BuilderStep.finish => (
          c.downloading ? 'Downloading…' : 'Download paper + answer key',
          Icons.download,
          c.downloading ? null : c.downloadAll,
          c.downloading,
        ),
    };
    return Material(
      elevation: 8,
      color: Theme.of(context).colorScheme.surface,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
          child: Align(
            alignment: Alignment.center,
            heightFactor: 1,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 880),
              child: SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton.icon(
                  key: const ValueKey('builder-primary'),
                  onPressed: onPressed,
                  icon: busy
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : Icon(icon),
                  label: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  static String _generateLabel(PaperBuilderController c) {
    if (c.generating) return 'Generating…';
    if (c.checking) return 'Checking the bank…';
    final a = c.availability;
    if (a == null) return 'Generate paper';
    if (a.nothingFits) return 'Nothing to generate yet';
    final short = a.short.length;
    return short == 0 ? 'Generate paper' : 'Generate anyway ($short section${short == 1 ? '' : 's'} short)';
  }
}
