import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:path_provider/path_provider.dart';
import 'package:printing/printing.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Real gap this fixes: there was no way to look back at a scanned/corrected
/// answer sheet after leaving the Scan & Grade flow -- MobileScanPage always
/// starts a brand-new capture (no sessionId param), and the review-queue
/// count on Today only ever surfaces sessions still awaiting review. Once a
/// sheet was approved, it effectively vanished from the UI even though the
/// real data was still sitting in LocalStore. This lists every real scan
/// session ever created on this device (LocalStore.allScanSessions -- the
/// exact same source Today's "Needs your review" count already reads) and
/// lets a teacher reopen any of them.
class ScanHistoryPage extends StatelessWidget {
  const ScanHistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sessions = LocalStore.instance.allScanSessions();

    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Scan history')),
      body: sessions.isEmpty
          ? _empty(theme)
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: sessions.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _sessionTile(context, theme, sessions[i]),
              ),
            ),
    );
  }

  Widget _empty(ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history_edu_outlined, size: 48, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(height: 12),
            Text('No scanned answer sheets yet',
                style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
            const SizedBox(height: 6),
            Text(
              'Every sheet you scan with Scan & Grade -- reviewed or still pending -- will show up here.',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _sessionTile(BuildContext context, ThemeData theme, Map<String, dynamic> session) {
    final review = List<Map<String, dynamic>>.from(session['review'] as List? ?? const []);
    final totalAwarded = review.fold<int>(0, (s, r) => s + ((r['finalMarks'] as num?)?.toInt() ?? 0));
    final totalMax = review.fold<int>(0, (s, r) => s + ((r['maxMarks'] as num?)?.toInt() ?? 0));
    final status = session['status'] as String? ?? 'capturing';
    final assessment = LocalStore.instance.getAssessment(session['assessmentId'] as String? ?? '');
    final subject = assessment?['subject'] as String? ?? '';
    final hasPages = (session['pages'] as List? ?? const []).isNotEmpty;

    return AppCard(
      onTap: review.isEmpty ? null : () => _openSheetChooser(context, session, hasPages),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  (session['studentName'] as String? ?? '').isEmpty
                      ? 'Unnamed student'
                      : session['studentName'] as String,
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  subject.isEmpty ? 'Scan session' : subject,
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  overflow: TextOverflow.ellipsis,
                ),
                if (review.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text('$totalAwarded / $totalMax',
                      style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              ChipTag(label: status),
              if (!hasPages) ...[
                const SizedBox(height: 4),
                Text('no photo saved',
                    style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ],
            ],
          ),
        ],
      ),
    );
  }

  // Real gap this fixed: tapping a session used to jump straight to the
  // flattened text/marks report -- a teacher had no way to look back at the
  // actual photographed booklet, exactly the "correction against the real
  // scanned image, not a blind digital transcript" complaint that drove the
  // review-screen fix in mobile_scan_page.dart. Both PDFs are real exports
  // of the same session (local_scan_pdf_export.dart); this just gives a
  // teacher a choice instead of only ever seeing the corrected one.
  Future<void> _openSheetChooser(BuildContext context, Map<String, dynamic> session, bool hasPages) async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (hasPages)
              ListTile(
                leading: const Icon(Icons.document_scanner_outlined),
                title: const Text('Raw scanned booklet'),
                subtitle: const Text('The actual photographed pages, as captured'),
                onTap: () => Navigator.of(sheetContext).pop('raw-pdf'),
              ),
            ListTile(
              leading: const Icon(Icons.fact_check_outlined),
              title: const Text('Corrected sheet'),
              subtitle: const Text('Marks and reasoning, question by question'),
              onTap: () => Navigator.of(sheetContext).pop('corrected-pdf'),
            ),
          ],
        ),
      ),
    );
    if (choice == null || !context.mounted) return;
    await _openPdf(context, session, choice);
  }

  Future<void> _openPdf(BuildContext context, Map<String, dynamic> session, String endpoint) async {
    final title = endpoint == 'raw-pdf' ? 'Raw booklet' : 'Corrected sheet';
    final api = GetIt.I<PillarApi>();
    try {
      final dir = await getTemporaryDirectory();
      final savePath = '${dir.path}/${endpoint}_${session['id']}.pdf';
      await api.downloadScanPdf('/scan/sessions/${session['id']}/$endpoint', savePath);
      if (!context.mounted) return;
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => Scaffold(
          appBar: AppBar(title: Text(title)),
          body: PdfPreview(build: (format) => File(savePath).readAsBytes()),
        ),
      ));
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not open the $title: $e')),
      );
    }
  }
}
