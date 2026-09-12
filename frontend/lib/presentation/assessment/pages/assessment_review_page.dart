import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:printing/printing.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/local_engine/local_api_client.dart'
    show AssessmentLockedException, editableAssessmentStatuses;
import '../../../data/datasources/api/api_client.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import '../widgets/paper_delivery_sheet.dart';

class AssessmentReviewPage extends StatefulWidget {
  final String assessmentId;
  final Assessment? assessment;
  final GeneratedPaper? paper;
  final List<String> gaps;
  final List<String> warnings;

  const AssessmentReviewPage({
    super.key,
    required this.assessmentId,
    this.assessment,
    this.paper,
    this.gaps = const [],
    this.warnings = const [],
  });

  @override
  State<AssessmentReviewPage> createState() => _AssessmentReviewPageState();
}

class _AssessmentReviewPageState extends State<AssessmentReviewPage> {
  bool _exporting = false;
  String? _exportedUrl;
  String? _error;

  Assessment? _fetchedAssessment;
  GeneratedPaper? _fetchedPaper;
  bool _reopening = false;
  String? _reopenError;

  bool _approving = false;
  String? _approveError;

  @override
  void initState() {
    super.initState();
    if (widget.assessment == null || widget.paper == null) {
      _reopen();
    }
  }

  // Router `extra` (widget.assessment/widget.paper) only survives while the
  // in-memory object from the generation flow is still around — reopening an
  // assessment from the list later, or after a reload, arrives with neither.
  // Assessment.generatedPaperId is what links the two back together.
  Future<void> _reopen() async {
    setState(() {
      _reopening = true;
      _reopenError = null;
    });
    try {
      final api = GetIt.I<ApiClient>();
      final assessment = await api.getAssessment(widget.assessmentId);
      final paperId = assessment.generatedPaperId;
      if (paperId == null || paperId.isEmpty) {
        throw Exception('This assessment has no generated paper yet.');
      }
      final paper = await api.getPaper(paperId);
      setState(() {
        _fetchedAssessment = assessment;
        _fetchedPaper = paper;
        _reopening = false;
      });
    } catch (e) {
      setState(() {
        _reopenError = '$e';
        _reopening = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final assessment = widget.assessment ?? _fetchedAssessment;
    final paper = widget.paper ?? _fetchedPaper;

    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: Text(assessment?.title ?? 'Assessment')),
      body: _reopening
          ? const Center(child: CircularProgressIndicator())
          : assessment == null || paper == null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          _reopenError ?? 'This assessment could not be opened.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: _reopen,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildSummaryCard(context, assessment, paper),
                    if (widget.gaps.isNotEmpty) _buildIssuesCard(context, 'Coverage gaps', widget.gaps, Colors.orange),
                    if (widget.warnings.isNotEmpty) _buildIssuesCard(context, 'Warnings', widget.warnings, Colors.red),
                    const SizedBox(height: 8),
                    for (final section in paper.sections) _buildSectionCard(context, section),
                    const SizedBox(height: 16),
                    _buildExportCard(context, assessment),
                  ],
                ),
    );
  }

  Widget _buildSummaryCard(BuildContext context, Assessment assessment, GeneratedPaper paper) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(paper.metadata.assessmentTitle, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
              ),
              ChipTag(label: assessment.status.name, color: Theme.of(context).colorScheme.primaryContainer),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(spacing: 16, runSpacing: 4, children: [
            Text('${paper.metadata.subject} · Grade ${paper.metadata.grade}'),
            Text('${paper.metadata.totalMarks} marks'),
            Text('${paper.metadata.durationMinutes} minutes'),
          ]),
        ],
      ),
    );
  }

  Widget _buildIssuesCard(BuildContext context, String title, List<String> items, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        color: color.withValues(alpha: 0.08),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.w600, color: color)),
            const SizedBox(height: 6),
            for (final item in items)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text('• $item', style: const TextStyle(fontSize: 13)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionCard(BuildContext context, GeneratedSection section) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Section ${section.label} — ${section.name} (${section.totalMarks} marks)',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
            const Divider(),
            for (final q in section.questions)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(width: 28, child: Text('${q.displayNumber}.', style: const TextStyle(fontWeight: FontWeight.w600))),
                    Expanded(child: Text(q.stem)),
                    const SizedBox(width: 8),
                    ChipTag(label: '${q.marks}m'),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildExportCard(BuildContext context, Assessment assessment) {
    final editable = editableAssessmentStatuses.contains(assessment.status);
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Export & Approve', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          if (_error != null) Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              FilledButton.icon(
                onPressed: _exporting ? null : _exportPdf,
                icon: _exporting
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.picture_as_pdf),
                label: Text(_exporting ? 'Exporting…' : 'Export PDF'),
              ),
              if (_exportedUrl != null) ...[
                FilledButton.tonalIcon(
                  onPressed: _openDelivery,
                  icon: const Icon(Icons.outgoing_mail),
                  label: const Text('Preview, print or email'),
                ),
                OutlinedButton.icon(
                  onPressed: () => _openExported(_exportedUrl!),
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Open in browser'),
                ),
              ],
            ],
          ),
          if (editable) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () => context.read<AssessmentBloc>().add(AssessmentEvent.updateStatus(
                assessmentId: widget.assessmentId,
                status: AssessmentStatus.underReview,
              )),
              icon: const Icon(Icons.rate_review),
              label: const Text('Mark as Under Teacher Review'),
            ),
          ],
          if (assessment.status == AssessmentStatus.underReview) ...[
            const Divider(height: 28),
            Text('Principal approval', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            const Text(
              'Approving locks the question selection and paper content — nothing can quietly '
              'change after this without a new, explicitly logged correction. Requires the '
              'Principal role, set in Settings > Profile.',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 10),
            if (_approveError != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(_approveError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ),
            FilledButton.icon(
              onPressed: _approving ? null : () => _approvePaper(assessment),
              icon: _approving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.verified),
              label: Text(_approving ? 'Approving…' : 'Approve & lock paper'),
            ),
          ] else if (!editable) ...[
            const Divider(height: 28),
            Row(children: [
              const Icon(Icons.lock, size: 16, color: Colors.green),
              const SizedBox(width: 8),
              Expanded(child: Text('Approved — paper is locked (${assessment.status.name}).',
                  style: const TextStyle(fontWeight: FontWeight.w600))),
            ]),
          ],
        ],
      ),
    );
  }

  Future<void> _approvePaper(Assessment assessment) async {
    setState(() {
      _approving = true;
      _approveError = null;
    });
    try {
      final api = GetIt.I<ApiClient>();
      // Real gap closed: this used to accept any free-text "principal name"
      // typed into a text field and approve unconditionally -- anyone could
      // type any name. approveAssessment() is gated on a real role (the
      // device's Settings > Profile role offline, a real authenticated
      // principal login online) instead.
      final updated = await api.approveAssessment(assessment.id);
      if (!mounted) return;
      setState(() {
        _fetchedAssessment = updated;
        _approving = false;
      });
      context.read<AssessmentBloc>().add(AssessmentEvent.updateStatus(
            assessmentId: assessment.id,
            status: AssessmentStatus.principalApproved,
          ));
    } on AssessmentLockedException catch (e) {
      if (!mounted) return;
      setState(() {
        _approving = false;
        _approveError = '$e';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _approving = false;
        _approveError = 'Could not approve: $e';
      });
    }
  }

  /// Local (offline-build) exports return an absolute file path, not a URL
  /// -- launchUrl on a raw file:// path throws FileUriExposedException on
  /// Android 7+, so those go through `printing`'s native share/view sheet
  /// instead, which handles the content:// URI dance correctly. Hosted
  /// deployments (http paths) keep using launchUrl exactly as before.
  Future<void> _openExported(String pathOrUrl) async {
    if (pathOrUrl.startsWith('http')) {
      await launchUrl(Uri.parse(pathOrUrl), mode: LaunchMode.externalApplication);
      return;
    }
    final bytes = await File(pathOrUrl).readAsBytes();
    await Printing.sharePdf(bytes: bytes, filename: pathOrUrl.split(RegExp(r'[\\/]')).last);
  }

  // Real dead end found by audit: these used to read widget.paper/
  // widget.assessment directly. Every navigation path except the
  // just-generated flow (assessment_create_page.dart) arrives with those
  // null and relies on _reopen() populating _fetchedAssessment/_fetchedPaper
  // instead -- build() already resolves via `?? _fetched...` (see above),
  // but these two handlers didn't, so Export/Deliver silently no-op'd on
  // every reopened assessment even though the screen displayed correctly.
  void _openDelivery() {
    final paper = widget.paper ?? _fetchedPaper;
    if (paper == null) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: false,
      builder: (_) => PaperDeliverySheet(
        paperId: paper.id,
        paperTitle: paper.metadata.assessmentTitle,
        subject: paper.metadata.subject,
        grade: paper.metadata.grade,
        schoolName: (widget.assessment ?? _fetchedAssessment)?.schoolId ?? 'AcademicOS School',
        localFilePath: (_exportedUrl != null && !_exportedUrl!.startsWith('http')) ? _exportedUrl : null,
      ),
    );
  }

  Future<void> _exportPdf() async {
    final paper = widget.paper ?? _fetchedPaper;
    if (paper == null) return;
    setState(() {
      _exporting = true;
      _error = null;
    });
    try {
      context.read<AssessmentBloc>().add(AssessmentEvent.exportPaper(
        paper: paper,
        templateId: 'default',
        format: ExportFormat.pdf,
      ));
      final result = await context.read<AssessmentBloc>().stream.firstWhere(
        (s) => !s.maybeMap(loading: (_) => true, orElse: () => false),
      );
      final path = result.mapOrNull(paperExported: (s) => s.filePath);
      if (path == null || path.isEmpty) {
        throw Exception('Export did not return a file');
      }
      setState(() {
        _exportedUrl = path.startsWith('http') ? path : '${GetIt.I<PillarApi>().serverOrigin}$path';
        _exporting = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _exporting = false;
      });
    }
  }
}
