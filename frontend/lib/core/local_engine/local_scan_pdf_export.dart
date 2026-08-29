import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'local_store.dart';
import 'pdf_text_safety.dart';

/// Real on-device PDF export for a finished Scan & Grade session -- a
/// genuine feature gap found by audit: LocalScanEngine.finalizeSession()
/// always returned empty rawPdfUrl/correctedPdfUrl (honestly, not faked),
/// and downloadScanPdf() threw OfflineUnsupportedException unconditionally.
/// The real backend (src/academicos/assessment/mobile_scan.py,
/// export_corrected_pdf/export_raw_booklet_pdf) already builds this
/// server-side; this ports the same real data -- per-question marks,
/// which marking points were met, the teacher's own comment where they
/// edited the AI's score -- to a real on-device PDF, no server required.
///
/// Not literal red-pen-on-the-scanned-image annotation: the backend's own
/// version deliberately avoids check/cross glyphs (confirmed there that
/// neither Segoe UI nor Arial has U+2713/U+2717, so those print as tofu
/// boxes) in favour of plain "[Awarded]"/"[Not awarded]" text. This port
/// keeps that same real, tested decision, adding red/green colour as a
/// genuine enhancement plain text can't fake -- a real distinguishing
/// signal for a page that says only "Not awarded" repeatedly.
class LocalScanPdfExporter {
  static String _safe(String text) => pdfSafe(text);

  static Future<Directory> _scanReportsDir() async {
    final dir = await getApplicationDocumentsDirectory();
    final reportsDir = Directory('${dir.path}/academicos_scan_exports');
    if (!await reportsDir.exists()) await reportsDir.create(recursive: true);
    return reportsDir;
  }

  static Future<String> exportCorrected(String sessionId) async {
    final session = LocalStore.instance.getScanSession(sessionId);
    if (session == null) {
      throw StateError('scan session not found: $sessionId');
    }
    final review = List<Map<String, dynamic>>.from(session['review'] as List? ?? const []);
    final studentName = (session['studentName'] as String? ?? '').trim();
    final studentId = (session['studentId'] as String? ?? '').trim();
    final assessmentId = session['assessmentId'] as String? ?? '';
    final assessment = LocalStore.instance.getAssessment(assessmentId);
    final subject = assessment?['subject'] as String? ?? '';
    final schoolId = assessment?['schoolId'] as String?;
    final schoolNameStr = schoolId != null && schoolId.isNotEmpty
        ? LocalStore.instance.schoolName(schoolId)
        : 'AcademicOS School';

    final totalAwarded = review.fold<int>(0, (s, r) => s + ((r['finalMarks'] as num?)?.toInt() ?? 0));
    final totalMax = review.fold<int>(0, (s, r) => s + ((r['maxMarks'] as num?)?.toInt() ?? 0));
    final sorted = [...review]
      ..sort((a, b) => ((a['displayNumber'] as num?)?.toInt() ?? 0)
          .compareTo((b['displayNumber'] as num?)?.toInt() ?? 0));

    final doc = pw.Document();
    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(28),
        header: (context) => context.pageNumber == 1
            ? pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.center,
                children: [
                  pw.Text(_safe(schoolNameStr),
                      style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
                  pw.SizedBox(height: 2),
                  pw.Text('Corrected Answer Sheet', style: const pw.TextStyle(fontSize: 12)),
                  pw.SizedBox(height: 6),
                  pw.Row(
                    mainAxisAlignment: pw.MainAxisAlignment.center,
                    children: [
                      pw.Text(_safe(studentName.isEmpty ? 'Unnamed student' : studentName),
                          style: const pw.TextStyle(fontSize: 10)),
                      if (studentId.isNotEmpty) ...[
                        pw.Text('  |  Roll/ID: ${_safe(studentId)}',
                            style: const pw.TextStyle(fontSize: 10)),
                      ],
                      if (subject.isNotEmpty)
                        pw.Text('  |  Subject: ${_safe(subject)}',
                            style: const pw.TextStyle(fontSize: 10)),
                    ],
                  ),
                  pw.SizedBox(height: 4),
                  pw.Text('Total: $totalAwarded / $totalMax',
                      style: pw.TextStyle(fontSize: 13, fontWeight: pw.FontWeight.bold)),
                  pw.Divider(thickness: 1),
                ],
              )
            : pw.Container(),
        footer: (context) => pw.Text('Generated on-device by AcademicOS -- not an official CBSE document.',
            style: const pw.TextStyle(fontSize: 7, color: PdfColors.grey600)),
        build: (context) => [
          for (final item in sorted) _questionBlock(item),
        ],
      ),
    );

    final reportsDir = await _scanReportsDir();
    final file = File('${reportsDir.path}/${sessionId}_corrected.pdf');
    await file.writeAsBytes(await doc.save());
    return file.path;
  }

  static pw.Widget _questionBlock(Map<String, dynamic> item) {
    final displayNumber = item['displayNumber'];
    final stem = (item['stem'] as String? ?? '').trim();
    final finalMarks = (item['finalMarks'] as num?)?.toInt() ?? 0;
    final maxMarks = (item['maxMarks'] as num?)?.toInt() ?? 0;
    final full = maxMarks > 0 && finalMarks >= maxMarks;
    final zero = finalMarks <= 0;
    final markColor = full ? PdfColors.green800 : (zero ? PdfColors.red700 : PdfColors.orange800);
    final markingPoints = List<Map<String, dynamic>>.from(item['markingPoints'] as List? ?? const []);
    final status = item['status'] as String? ?? 'pending';
    final teacherComment = (item['teacherComment'] as String? ?? '').trim();
    final awardedByTeacher = item['teacherMarks'] as num?;

    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 10),
      padding: const pw.EdgeInsets.only(top: 6),
      decoration: const pw.BoxDecoration(
        border: pw.Border(top: pw.BorderSide(color: PdfColors.grey300, width: 0.6)),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Expanded(
                child: pw.Text('Q$displayNumber. ${_safe(stem.length > 160 ? '${stem.substring(0, 160)}...' : stem)}',
                    style: pw.TextStyle(fontSize: 9.5, fontWeight: pw.FontWeight.bold)),
              ),
              pw.SizedBox(width: 8),
              pw.Text('$finalMarks / $maxMarks',
                  style: pw.TextStyle(fontSize: 10.5, fontWeight: pw.FontWeight.bold, color: markColor)),
            ],
          ),
          for (final mp in markingPoints)
            pw.Padding(
              padding: const pw.EdgeInsets.only(left: 10, top: 2),
              child: pw.Text(
                '${(mp['awarded'] as bool? ?? false) ? '[Awarded]' : '[Not awarded]'} '
                '${_safe((mp['description'] as String? ?? '').trim())} -- '
                '${_safe((mp['reason'] as String? ?? '').trim())} (${mp['marks']} mark)',
                style: pw.TextStyle(
                  fontSize: 8.5,
                  color: (mp['awarded'] as bool? ?? false) ? PdfColors.green800 : PdfColors.red700,
                ),
              ),
            ),
          if (status == 'edited')
            pw.Padding(
              padding: const pw.EdgeInsets.only(left: 10, top: 3),
              child: pw.Text(
                teacherComment.isNotEmpty
                    ? "Teacher's note: ${_safe(teacherComment)}"
                    : 'Teacher adjusted the AI\'s score${awardedByTeacher != null ? " to $awardedByTeacher" : ""}.',
                style: const pw.TextStyle(fontSize: 8.5, color: PdfColors.orange900),
              ),
            ),
        ],
      ),
    );
  }

  /// Assembles every captured page photo into one PDF -- the permanent,
  /// shareable record of what the student actually wrote, same real gap
  /// (never wired offline) as the corrected sheet above.
  static Future<String> exportRawBooklet(String sessionId) async {
    final session = LocalStore.instance.getScanSession(sessionId);
    if (session == null) {
      throw StateError('scan session not found: $sessionId');
    }
    final pages = List<Map<String, dynamic>>.from(session['pages'] as List? ?? const []);
    if (pages.isEmpty) {
      throw StateError('no captured pages to export for session: $sessionId');
    }
    final studentName = (session['studentName'] as String? ?? '').trim();

    final doc = pw.Document();
    for (final page in pages) {
      final path = page['imagePath'] as String?;
      if (path == null) continue;
      final file = File(path);
      if (!await file.exists()) continue;
      final bytes = await file.readAsBytes();
      final image = pw.MemoryImage(bytes);
      doc.addPage(
        pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.all(12),
          build: (context) => pw.Column(
            children: [
              if (studentName.isNotEmpty)
                pw.Text(_safe(studentName), style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey700)),
              pw.Expanded(child: pw.Image(image, fit: pw.BoxFit.contain)),
            ],
          ),
        ),
      );
    }

    final reportsDir = await _scanReportsDir();
    final file = File('${reportsDir.path}/${sessionId}_raw.pdf');
    await file.writeAsBytes(await doc.save());
    return file.path;
  }
}
