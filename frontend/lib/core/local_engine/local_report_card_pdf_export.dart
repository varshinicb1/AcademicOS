import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'local_report_card.dart';
import 'pdf_text_safety.dart';

/// Real report-card PDF -- the report-card generation feature requested
/// but never built. Every figure printed here comes from ReportCardData,
/// which is itself built only from real stored evaluations/mastery (see
/// local_report_card.dart) -- no placeholder marks anywhere.
class LocalReportCardPdfExporter {
  // Same real gap this exporter's sibling (local_pdf_export.dart) found and
  // fixed: the pdf package's base Helvetica font has no Unicode support, so
  // typographic punctuation in a real name/school string would silently
  // render as a missing glyph.
  static String _safe(String text) => pdfSafe(text);

  static Future<String> export(ReportCardData data) async {
    final doc = pw.Document();

    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        build: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Center(
              child: pw.Column(
                children: [
                  pw.Text(_safe(data.schoolName),
                      style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold)),
                  pw.SizedBox(height: 4),
                  pw.Text('Progress Report Card', style: const pw.TextStyle(fontSize: 13)),
                ],
              ),
            ),
            pw.SizedBox(height: 16),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('Name: ${_safe(data.studentName)}', style: const pw.TextStyle(fontSize: 11)),
                pw.Text('Class: ${data.grade}', style: const pw.TextStyle(fontSize: 11)),
              ],
            ),
            pw.SizedBox(height: 2),
            pw.Text('Generated: ${_formatDate(data.generatedAt)}',
                style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey600)),
            pw.SizedBox(height: 16),
            pw.Container(
              width: double.infinity,
              padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              color: PdfColors.grey200,
              child: pw.Text('Subject-wise performance',
                  style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold)),
            ),
            pw.SizedBox(height: 6),
            if (data.subjects.isEmpty)
              pw.Text('No evaluated assessments recorded for this student yet.',
                  style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey700))
            else
              pw.Table(
                border: pw.TableBorder.all(color: PdfColors.grey400, width: 0.5),
                columnWidths: const {
                  0: pw.FlexColumnWidth(2.5),
                  1: pw.FlexColumnWidth(1.5),
                  2: pw.FlexColumnWidth(1.5),
                  3: pw.FlexColumnWidth(1.5),
                },
                children: [
                  pw.TableRow(
                    decoration: const pw.BoxDecoration(color: PdfColors.grey100),
                    children: [
                      _cell('Subject', bold: true),
                      _cell('Assessments', bold: true),
                      _cell('Marks', bold: true),
                      _cell('%', bold: true),
                    ],
                  ),
                  for (final s in data.subjects)
                    pw.TableRow(children: [
                      _cell(_safe(s.subject)),
                      _cell('${s.assessmentCount}'),
                      _cell('${s.totalAwarded}/${s.totalMax}'),
                      _cell(s.percentage.toStringAsFixed(0)),
                    ]),
                  pw.TableRow(
                    decoration: const pw.BoxDecoration(color: PdfColors.grey100),
                    children: [
                      _cell('Overall', bold: true),
                      _cell(''),
                      _cell(''),
                      _cell(data.overallPercentage.toStringAsFixed(0), bold: true),
                    ],
                  ),
                ],
              ),
            pw.SizedBox(height: 20),
            pw.Container(
              width: double.infinity,
              padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              color: PdfColors.grey200,
              child: pw.Text('Learning mastery',
                  style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold)),
            ),
            pw.SizedBox(height: 6),
            pw.Text('Overall concept mastery: ${(data.overallMastery * 100).toStringAsFixed(0)}%',
                style: const pw.TextStyle(fontSize: 10)),
            if (data.weakConcepts.isNotEmpty) ...[
              pw.SizedBox(height: 6),
              pw.Text('Concepts needing attention:', style: const pw.TextStyle(fontSize: 10)),
              pw.SizedBox(height: 2),
              for (final c in data.weakConcepts)
                pw.Text('- ${_safe(c)}', style: const pw.TextStyle(fontSize: 9.5)),
            ],
            pw.Spacer(),
            pw.Divider(thickness: 0.5),
            pw.Text('Generated on-device by AcademicOS. Not an official CBSE document.',
                style: const pw.TextStyle(fontSize: 7.5, color: PdfColors.grey600)),
          ],
        ),
      ),
    );

    final dir = await getApplicationDocumentsDirectory();
    final reportsDir = Directory('${dir.path}/academicos_reports');
    if (!await reportsDir.exists()) {
      await reportsDir.create(recursive: true);
    }
    final file = File('${reportsDir.path}/report_${data.studentId}.pdf');
    await file.writeAsBytes(await doc.save());
    return file.path;
  }

  static pw.Widget _cell(String text, {bool bold = false}) => pw.Padding(
        padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
        child: pw.Text(text,
            style: pw.TextStyle(fontSize: 9.5, fontWeight: bold ? pw.FontWeight.bold : null)),
      );

  static String _formatDate(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
}
