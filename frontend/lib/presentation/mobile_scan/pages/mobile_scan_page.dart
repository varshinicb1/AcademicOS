import 'dart:io';

import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:printing/printing.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

enum _Stage { setup, capturing, processing, reviewing, complete }

/// Pillar 2 on a phone: a teacher selects the test and the student, photographs
/// each page, and the app crops, enhances, OCRs, and AI-scores every answer
/// before the teacher ever sees it — then they swipe through approving or
/// correcting each one. This is the mobile counterpart to the desktop
/// Evaluate screen's demo flow, but working from a real photographed booklet
/// instead of synthetic sample answers.
class MobileScanPage extends StatefulWidget {
  const MobileScanPage({super.key});

  @override
  State<MobileScanPage> createState() => _MobileScanPageState();
}

class _MobileScanPageState extends State<MobileScanPage> {
  final _api = GetIt.I<PillarApi>();
  final _picker = ImagePicker();

  _Stage _stage = _Stage.setup;
  String? _error;

  // Setup
  List<Map<String, dynamic>> _assessments = [];
  Map<String, dynamic>? _selectedAssessment;
  final _studentName = TextEditingController();
  final _studentId = TextEditingController();
  bool _loadingAssessments = true;

  // Capture
  ScanSession? _session;
  final List<CapturedPageResult> _pages = [];
  bool _uploadingPage = false;

  // Review
  List<ScanReviewItem> _review = [];
  int _index = 0;
  final Map<String, ScanReviewItem> _decided = {};

  // Complete
  ScanFinalizeResult? _result;

  @override
  void initState() {
    super.initState();
    _loadAssessments();
    // "Start capturing" is disabled until a name is entered, but nothing
    // rebuilds the button on keystrokes without this — TextEditingController
    // notifies its own listeners, not the widget tree.
    _studentName.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _studentName.dispose();
    _studentId.dispose();
    super.dispose();
  }

  Future<void> _loadAssessments() async {
    setState(() => _loadingAssessments = true);
    try {
      final list = await _api.listAssessmentsForSchool('school_1');
      // Only papers that actually have a generated question set can be
      // marked against — a blueprint-only assessment has nothing to match
      // segmented answers to.
      final withPapers = list.where((a) => a['generatedPaperId'] != null).toList();
      setState(() {
        _assessments = withPapers;
        _selectedAssessment = withPapers.isNotEmpty ? withPapers.first : null;
        _loadingAssessments = false;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _loadingAssessments = false;
      });
    }
  }

  Future<void> _startCapture() async {
    if (_selectedAssessment == null || _studentName.text.trim().isEmpty) return;
    setState(() => _error = null);
    try {
      final session = await _api.createScanSession(
        assessmentId: _selectedAssessment!['id'],
        studentId: _studentId.text.trim().isEmpty
            ? 'stu_${DateTime.now().millisecondsSinceEpoch}'
            : _studentId.text.trim(),
        studentName: _studentName.text.trim(),
      );
      setState(() {
        _session = session;
        _stage = _Stage.capturing;
      });
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  Future<void> _capturePhoto() async {
    final photo = await _picker.pickImage(source: ImageSource.camera, imageQuality: 90);
    if (photo != null) await _uploadPage(photo.path);
  }

  /// Alternative to the camera for a page already photographed elsewhere
  /// (or, on desktop, the only capture path available at all — there is no
  /// system camera app to launch).
  Future<void> _importPhoto() async {
    final result = await FilePicker.pickFiles(
      type: FileType.image,
      allowMultiple: true,
    );
    if (result == null) return;
    for (final f in result.files) {
      if (f.path != null) await _uploadPage(f.path!);
    }
  }

  Future<void> _uploadPage(String path) async {
    setState(() => _uploadingPage = true);
    try {
      final page = await _api.uploadScanPage(_session!.id, path);
      setState(() {
        _pages.add(page);
        _uploadingPage = false;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _uploadingPage = false;
      });
    }
  }

  Future<void> _processCapturedPages() async {
    setState(() {
      _stage = _Stage.processing;
      _error = null;
    });
    try {
      final queue = await _api.processScanSession(_session!.id);
      setState(() {
        _review = queue.items;
        _index = 0;
        _decided.clear();
        _stage = _Stage.reviewing;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _stage = _Stage.capturing;
      });
    }
  }

  Future<void> _approve(ScanReviewItem item) async {
    final updated = await _api.submitReviewDecision(_session!.id, item.questionId, action: 'approve');
    _decided[item.questionId] = updated;
    _advance();
  }

  Future<void> _editAndAdvance(ScanReviewItem item, int marks, String comment) async {
    final updated = await _api.submitReviewDecision(_session!.id, item.questionId,
        action: 'edit', marks: marks, comment: comment);
    _decided[item.questionId] = updated;
    _advance();
  }

  void _advance() {
    if (_index < _review.length - 1) {
      setState(() => _index++);
    } else {
      _finalize();
    }
  }

  Future<void> _finalize() async {
    setState(() => _stage = _Stage.processing);
    try {
      final result = await _api.finalizeScanSession(_session!.id);
      setState(() {
        _result = result;
        _stage = _Stage.complete;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _stage = _Stage.reviewing;
      });
    }
  }

  Future<void> _viewPdf(String relativePath, String title) async {
    final dir = await getTemporaryDirectory();
    final savePath = '${dir.path}/$title.pdf';
    await _api.downloadScanPdf(relativePath, savePath);
    if (!mounted) return;
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => Scaffold(
        appBar: AppBar(title: Text(title)),
        body: PdfPreview(build: (format) => File(savePath).readAsBytes()),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Scan & Grade')),
      body: switch (_stage) {
        _Stage.setup => _setupView(),
        _Stage.capturing => _captureView(),
        _Stage.processing => LoadingIndicator(
            message: _review.isEmpty
                ? 'Grading each answer with AI — this checks every question '
                    'individually, so a full booklet can take a minute or two…'
                : 'Saving the corrected sheet…',
          ),
        _Stage.reviewing => _reviewView(),
        _Stage.complete => _completeView(),
      },
    );
  }

  // ---- Setup ----

  Widget _setupView() {
    final theme = Theme.of(context);
    if (_loadingAssessments) return const LoadingIndicator(message: 'Loading assessments…');
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Select the test', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              const Gap(10),
              if (_assessments.isEmpty)
                const Text('No generated papers yet. Create and generate an assessment first.')
              else
                DropdownButtonFormField<Map<String, dynamic>>(
                  initialValue: _selectedAssessment,
                  isExpanded: true,
                  decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
                  items: _assessments
                      .map((a) => DropdownMenuItem(
                            value: a,
                            child: Text('${a['title']} · ${a['subject']} · Class ${a['grade']}',
                                overflow: TextOverflow.ellipsis),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _selectedAssessment = v),
                ),
            ],
          ),
        ),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Student', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              const Gap(10),
              TextField(
                controller: _studentName,
                decoration: const InputDecoration(
                    labelText: 'Student name', border: OutlineInputBorder(), isDense: true),
              ),
              const Gap(10),
              TextField(
                controller: _studentId,
                decoration: const InputDecoration(
                    labelText: 'Roll no. / ID (optional)', border: OutlineInputBorder(), isDense: true),
              ),
            ],
          ),
        ),
        if (_error != null)
          AppCard(
            color: theme.colorScheme.errorContainer.withValues(alpha: 0.35),
            child: Text(_error!),
          ),
        const Gap(8),
        FilledButton.icon(
          onPressed: (_assessments.isEmpty || _studentName.text.trim().isEmpty) ? null : _startCapture,
          icon: const Icon(Icons.camera_alt_outlined),
          label: const Text('Start capturing pages'),
        ),
      ],
    );
  }

  // ---- Capture ----

  Widget _captureView() {
    final theme = Theme.of(context);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  '${_selectedAssessment?['title'] ?? ''} — ${_studentName.text}',
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              ChipTag(label: '${_pages.length} page(s)'),
            ],
          ),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: AppCard(
              color: theme.colorScheme.errorContainer.withValues(alpha: 0.35),
              child: Text(_error!),
            ),
          ),
        Expanded(
          child: _pages.isEmpty
              ? const EmptyState(
                  icon: Icons.document_scanner_outlined,
                  title: 'No pages yet',
                  message: 'Photograph or import each page of the answer booklet.',
                )
              : GridView.builder(
                  padding: const EdgeInsets.all(16),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3, crossAxisSpacing: 10, mainAxisSpacing: 10, childAspectRatio: 0.75),
                  itemCount: _pages.length,
                  itemBuilder: (context, i) {
                    final p = _pages[i];
                    return Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: theme.colorScheme.outlineVariant),
                        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                      ),
                      padding: const EdgeInsets.all(8),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(children: [
                            Text('Page ${p.pageNo}',
                                style: theme.textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600)),
                            const Spacer(),
                            if (p.warnings.isNotEmpty)
                              Icon(Icons.warning_amber, size: 15, color: Colors.orange.shade700),
                          ]),
                          const Gap(4),
                          Expanded(
                            child: Text(p.ocrPreview,
                                style: theme.textTheme.bodySmall, maxLines: 6, overflow: TextOverflow.fade),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _uploadingPage ? null : _capturePhoto,
                        icon: const Icon(Icons.camera_alt),
                        label: const Text('Take photo'),
                      ),
                    ),
                    const Gap(10),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _uploadingPage ? null : _importPhoto,
                        icon: const Icon(Icons.photo_library_outlined),
                        label: const Text('Import photo'),
                      ),
                    ),
                  ],
                ),
                const Gap(10),
                if (_uploadingPage) const LinearProgressIndicator(minHeight: 3),
                if (_uploadingPage) const Gap(10),
                FilledButton.icon(
                  onPressed: (_pages.isEmpty || _uploadingPage) ? null : _processCapturedPages,
                  icon: const Icon(Icons.auto_awesome),
                  label: Text('Done — grade ${_pages.length} page(s)'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // ---- Review (swipe) ----

  Widget _reviewView() {
    final theme = Theme.of(context);
    final item = _review[_index];
    return Column(
      children: [
        LinearProgressIndicator(value: (_index + 1) / _review.length, minHeight: 3),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: Row(
            children: [
              Text('Question ${_index + 1} of ${_review.length}',
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const Spacer(),
              Text('Swipe right to approve, left to edit', style: theme.textTheme.bodySmall),
            ],
          ),
        ),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Dismissible(
              key: ValueKey(item.questionId),
              background: Container(
                alignment: Alignment.centerLeft,
                padding: const EdgeInsets.only(left: 24),
                decoration: BoxDecoration(color: Colors.green, borderRadius: BorderRadius.circular(16)),
                child: const Icon(Icons.check_circle, color: Colors.white, size: 32),
              ),
              secondaryBackground: Container(
                alignment: Alignment.centerRight,
                padding: const EdgeInsets.only(right: 24),
                decoration: BoxDecoration(color: Colors.orange, borderRadius: BorderRadius.circular(16)),
                child: const Icon(Icons.edit, color: Colors.white, size: 32),
              ),
              confirmDismiss: (direction) async {
                if (direction == DismissDirection.startToEnd) {
                  await _approve(item);
                } else {
                  await _showEditSheet(item);
                }
                return false; // we manage the card change ourselves via _advance()
              },
              child: SingleChildScrollView(child: _reviewCard(item, theme)),
            ),
          ),
        ),
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _showEditSheet(item),
                    icon: const Icon(Icons.edit_outlined),
                    label: const Text('Edit'),
                  ),
                ),
                const Gap(10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: () => _approve(item),
                    icon: const Icon(Icons.check),
                    label: const Text('Approve'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _reviewCard(ScanReviewItem item, ThemeData theme) {
    return Column(
      children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Question', style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const Gap(4),
              Text(item.stem, style: theme.textTheme.bodyMedium),
              if (item.pageImageUrls.isNotEmpty) ...[
                const Gap(12),
                Text('Scanned page', style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                const Gap(4),
                SizedBox(
                  height: 220,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: item.pageImageUrls.length,
                    separatorBuilder: (_, __) => const Gap(8),
                    itemBuilder: (context, i) => ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: InkWell(
                        onTap: () => _showFullPageImage(
                            context, '${GetIt.I<PillarApi>().serverOrigin}${item.pageImageUrls[i]}'),
                        child: Image.network(
                          '${GetIt.I<PillarApi>().serverOrigin}${item.pageImageUrls[i]}',
                          height: 220,
                          fit: BoxFit.contain,
                          loadingBuilder: (context, child, progress) => progress == null
                              ? child
                              : const SizedBox(width: 160, height: 220, child: Center(child: CircularProgressIndicator())),
                          errorBuilder: (context, error, stack) => const SizedBox(
                            width: 160,
                            height: 220,
                            child: Center(child: Icon(Icons.broken_image_outlined)),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
              const Gap(12),
              Text("Student's answer (from photo)",
                  style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const Gap(4),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(item.studentAnswer.isEmpty ? '(no answer found)' : item.studentAnswer,
                    style: theme.textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic)),
              ),
            ],
          ),
        ),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text('${item.awardedMarks} / ${item.maxMarks}',
                      style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
                  const Gap(12),
                  ChipTag(label: item.verdict, color: _verdictColor(item.verdict)),
                  const Spacer(),
                  ChipTag(
                    label: '${(item.confidence * 100).round()}% confident',
                    color: item.needsReview ? Colors.orange : Colors.green,
                  ),
                ],
              ),
              const Gap(10),
              Text(item.reasoning),
              if (item.ocrWarnings.isNotEmpty) ...[
                const Gap(8),
                Row(children: [
                  const Icon(Icons.flag, size: 15, color: Colors.orange),
                  const Gap(6),
                  Expanded(child: Text(item.ocrWarnings.join('; '), style: theme.textTheme.bodySmall)),
                ]),
              ],
            ],
          ),
        ),
        if (item.markingPoints.isNotEmpty)
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Marking points', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(6),
                ...item.markingPoints.map((m) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(m.awarded ? Icons.check_circle : Icons.cancel,
                              size: 17, color: m.awarded ? Colors.green : Colors.red),
                          const Gap(8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(m.description),
                                Text(m.reason, style: theme.textTheme.bodySmall),
                              ],
                            ),
                          ),
                          Text('${m.marks}', style: const TextStyle(fontWeight: FontWeight.w600)),
                        ],
                      ),
                    )),
              ],
            ),
          ),
      ],
    );
  }

  void _showFullPageImage(BuildContext context, String url) {
    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        insetPadding: const EdgeInsets.all(16),
        child: InteractiveViewer(
          minScale: 0.5,
          maxScale: 4,
          child: Image.network(url, fit: BoxFit.contain),
        ),
      ),
    );
  }

  Future<void> _showEditSheet(ScanReviewItem item) async {
    var marks = item.finalMarks.toDouble();
    final comment = TextEditingController(text: item.teacherComment);
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
            left: 16, right: 16, top: 16, bottom: MediaQuery.of(context).viewInsets.bottom + 16),
        child: StatefulBuilder(
          builder: (context, setSheetState) => Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Adjust Q${item.displayNumber}', style: Theme.of(context).textTheme.titleMedium),
              const Gap(12),
              Text('Marks: ${marks.round()} / ${item.maxMarks}'),
              Slider(
                value: marks.clamp(0, item.maxMarks.toDouble()),
                min: 0,
                max: item.maxMarks.toDouble(),
                divisions: item.maxMarks == 0 ? 1 : item.maxMarks,
                label: '${marks.round()}',
                onChanged: (v) => setSheetState(() => marks = v),
              ),
              TextField(
                controller: comment,
                decoration: const InputDecoration(labelText: 'Comment (optional)', border: OutlineInputBorder()),
                maxLines: 2,
              ),
              const Gap(16),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Save & next'),
              ),
            ],
          ),
        ),
      ),
    );
    if (saved == true) {
      await _editAndAdvance(item, marks.round(), comment.text.trim());
    }
  }

  Color _verdictColor(String v) => switch (v) {
        'fullCredit' => Colors.green,
        'partialCredit' => Colors.orange,
        'blank' => Colors.grey,
        _ => Colors.red,
      };

  // ---- Complete ----

  Widget _completeView() {
    final theme = Theme.of(context);
    final result = _result!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.celebration_outlined, color: Colors.green, size: 28),
                const Gap(10),
                Text('Review complete', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              ]),
              const Gap(10),
              Text('${_studentName.text}: ${result.totalAwarded} / ${result.totalMax}',
                  style: theme.textTheme.headlineSmall),
            ],
          ),
        ),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Exports', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const Gap(10),
              OutlinedButton.icon(
                onPressed: () => _viewPdf('/scan/sessions/${_session!.id}/raw-pdf', 'Raw booklet'),
                icon: const Icon(Icons.picture_as_pdf_outlined),
                label: const Text('View raw booklet PDF'),
              ),
              const Gap(8),
              OutlinedButton.icon(
                onPressed: () => _viewPdf('/scan/sessions/${_session!.id}/corrected-pdf', 'Corrected sheet'),
                icon: const Icon(Icons.fact_check_outlined),
                label: const Text('View corrected sheet PDF'),
              ),
            ],
          ),
        ),
        const Gap(8),
        FilledButton.icon(
          onPressed: () {
            setState(() {
              _stage = _Stage.setup;
              _session = null;
              _pages.clear();
              _review = [];
              _result = null;
              _studentName.clear();
              _studentId.clear();
            });
          },
          icon: const Icon(Icons.add),
          label: const Text('Scan another student'),
        ),
      ],
    );
  }
}
