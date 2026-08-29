import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:printing/printing.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';

// Same per-file pattern as settings_page.dart/home_page.dart/etc. -- this
// build variant has no server, so it structurally can never have a
// configured mail backend. Real fix for a real dead end: the Email tab used
// to always be shown and always fail with "No email backend is configured
// yet", because there is no way to configure one on this build short of the
// user hand-editing config/secrets.env on a server that doesn't exist here.
// Rather than show a permanently-broken tab, don't offer email at all in
// this build -- Preview & Print (which is fully real and fully offline) is
// the only delivery path that can actually work.
const _offlineBuild = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

/// Preview / print / email a generated paper.
///
/// This is where a teacher actually finishes the job, so all three actions live
/// together: see the real PDF, print it for the exam hall, or send it to the
/// exam coordinator. Sending is explicit — nothing leaves the school without a
/// deliberate tap and a visible recipient list. In the offline build, email
/// isn't offered at all (see _offlineBuild above) -- only preview/print.
class PaperDeliverySheet extends StatefulWidget {
  final String paperId;
  final String paperTitle;
  final String subject;
  final int grade;
  final String schoolName;

  /// Absolute on-device path of an already-exported copy of this paper
  /// (offline builds always have one -- exportPaper() renders locally
  /// before this sheet ever opens). When set, Preview reads these bytes
  /// directly instead of re-fetching the PDF from a server that, in the
  /// offline build, doesn't exist -- fixes a real dead end where the
  /// Preview tab hung/failed even though the paper had just been exported.
  final String? localFilePath;

  const PaperDeliverySheet({
    super.key,
    required this.paperId,
    required this.paperTitle,
    required this.subject,
    required this.grade,
    this.schoolName = 'AcademicOS School',
    this.localFilePath,
  });

  @override
  State<PaperDeliverySheet> createState() => _PaperDeliverySheetState();
}

class _PaperDeliverySheetState extends State<PaperDeliverySheet> {
  final _recipients = TextEditingController();
  final _note = TextEditingController();
  bool _includeKey = true;
  bool _sending = false;
  String? _error;
  String? _success;
  Map<String, dynamic>? _mailStatus;

  @override
  void initState() {
    super.initState();
    if (!_offlineBuild) _loadMailStatus();
  }

  @override
  void dispose() {
    _recipients.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _loadMailStatus() async {
    try {
      final s = await GetIt.I<PillarApi>().mailStatus();
      if (mounted) setState(() => _mailStatus = s);
    } catch (_) {
      // Status is advisory; failing to fetch it must not block preview/print.
    }
  }

  Future<Uint8List> _fetchPdf() async {
    if (widget.localFilePath != null) {
      return File(widget.localFilePath!).readAsBytes();
    }
    final dio = GetIt.I<Dio>();
    final r = await dio.get<List<int>>(
      '/papers/${widget.paperId}/file',
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(r.data ?? const []);
  }

  List<String> _parseRecipients() => _recipients.text
      .split(RegExp(r'[,;\s]+'))
      .map((e) => e.trim())
      .where((e) => e.isNotEmpty)
      .toList();

  Future<void> _send() async {
    final to = _parseRecipients();
    if (to.isEmpty) {
      setState(() => _error = 'Add at least one recipient email address.');
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
      _success = null;
    });
    try {
      final res = await GetIt.I<PillarApi>().sendPaper(
        paperId: widget.paperId,
        recipients: to,
        subjectName: widget.subject,
        grade: widget.grade,
        paperTitle: widget.paperTitle,
        schoolName: widget.schoolName,
        note: _note.text,
        includeAnswerKey: _includeKey,
      );
      setState(() => _success =
          'Sent via ${res['backend']} to ${(res['recipients'] as List).join(', ')}');
    } catch (e) {
      setState(() => _error = _readableError(e));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  String _readableError(Object e) {
    if (e is DioException) {
      final data = e.response?.data;
      if (data is Map && data['detail'] != null) return data['detail'].toString();
    }
    return e.toString();
  }

  bool get _mailReady => (_mailStatus?['anyConfigured'] as bool?) ?? false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DefaultTabController(
      length: _offlineBuild ? 1 : 2,
      child: Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: SizedBox(
          height: MediaQuery.of(context).size.height * 0.86,
          child: Column(
            children: [
              const Gap(10),
              Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: theme.colorScheme.outlineVariant,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const Gap(10),
              Text(widget.paperTitle,
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              Text('${widget.subject} · Class ${widget.grade}',
                  style: theme.textTheme.bodySmall),
              const Gap(8),
              const TabBar(tabs: [
                Tab(icon: Icon(Icons.picture_as_pdf), text: 'Preview & Print'),
                if (!_offlineBuild) Tab(icon: Icon(Icons.mail_outline), text: 'Email'),
              ]),
              Expanded(
                child: TabBarView(
                  children: [_previewTab(), if (!_offlineBuild) _emailTab(theme)],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _previewTab() {
    return PdfPreview(
      build: (_) => _fetchPdf(),
      allowPrinting: true,
      allowSharing: true,
      canChangePageFormat: false,
      canChangeOrientation: false,
      canDebug: false,
      pdfFileName: '${widget.paperId}.pdf',
      loadingWidget: const LoadingIndicator(message: 'Rendering paper…'),
    );
  }

  Widget _emailTab(ThemeData theme) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (_mailStatus != null && !_mailReady)
          AppCard(
            color: Colors.orange.withValues(alpha: 0.10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  const Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                  const Gap(8),
                  Expanded(
                    child: Text('No email backend is configured yet',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w600)),
                  ),
                ]),
                const Gap(6),
                for (final entry
                    in (_mailStatus!['backends'] as Map<String, dynamic>).entries)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text('• ${entry.key}: ${entry.value['reason']}',
                        style: theme.textTheme.bodySmall),
                  ),
                const Gap(6),
                Text(
                  'Set COMPOSIO_API_KEY (or SMTP_*) in config/secrets.env and '
                  'restart the server. You can still preview and print above.',
                  style: theme.textTheme.bodySmall,
                ),
              ],
            ),
          ),
        TextField(
          controller: _recipients,
          decoration: const InputDecoration(
            labelText: 'Recipients',
            hintText: 'coordinator@school.edu, principal@school.edu',
            helperText: 'Comma or space separated',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.person_outline),
          ),
          minLines: 1,
          maxLines: 3,
        ),
        const Gap(12),
        TextField(
          controller: _note,
          decoration: const InputDecoration(
            labelText: 'Note (optional)',
            hintText: 'Please review before Monday.',
            border: OutlineInputBorder(),
          ),
          minLines: 2,
          maxLines: 4,
        ),
        const Gap(4),
        SwitchListTile(
          value: _includeKey,
          onChanged: (v) => setState(() => _includeKey = v),
          title: const Text('Attach answer key & marking scheme'),
          subtitle: const Text('Send only to staff, never to students'),
          contentPadding: EdgeInsets.zero,
        ),
        if (_error != null) ...[
          const Gap(8),
          AppCard(
            color: theme.colorScheme.errorContainer.withValues(alpha: 0.35),
            child: Text(_error!, style: TextStyle(color: theme.colorScheme.onErrorContainer)),
          ),
        ],
        if (_success != null) ...[
          const Gap(8),
          AppCard(
            color: Colors.green.withValues(alpha: 0.12),
            child: Row(children: [
              const Icon(Icons.check_circle, color: Colors.green),
              const Gap(8),
              Expanded(child: Text(_success!)),
            ]),
          ),
        ],
        const Gap(16),
        FilledButton.icon(
          onPressed: _sending ? null : _send,
          icon: _sending
              ? const SizedBox(
                  width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.send),
          label: Text(_sending ? 'Sending…' : 'Send paper'),
          style: FilledButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
        ),
        const Gap(8),
        Text(
          'The PDF is sent as an attachment from your school\'s connected mail account.',
          style: theme.textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
