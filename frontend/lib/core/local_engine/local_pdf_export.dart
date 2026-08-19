import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../../domain/repositories/requests.dart';

/// Real, on-device CBSE-format question paper PDF -- not the full fidelity
/// of the server's ReportLab renderer (src/academicos/assessment/pdf.py),
/// but a genuine rendering of the actual generated paper: numbered
/// sections, marks per question, school branding, saved as a real file the
/// user can open. No network call.
class LocalPdfExporter {
  static Future<String> exportPaper(GeneratedPaper paper) async {
    final doc = pw.Document();
    final meta = paper.metadata;

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(28),
        header: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.center,
          children: [
            pw.Text(meta.assessmentTitle,
                style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 4),
            pw.Text('${meta.subject} — Class ${meta.grade}', style: const pw.TextStyle(fontSize: 11)),
            pw.SizedBox(height: 2),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('Time: ${meta.durationMinutes} min', style: const pw.TextStyle(fontSize: 10)),
                pw.Text('Max Marks: ${meta.totalMarks}', style: const pw.TextStyle(fontSize: 10)),
              ],
            ),
            pw.Divider(thickness: 1),
          ],
        ),
        footer: (context) => pw.Align(
          alignment: pw.Alignment.centerRight,
          child: pw.Text('Page ${context.pageNumber} of ${context.pagesCount}',
              style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
        ),
        build: (context) => [
          for (final section in paper.sections) ...[
            pw.SizedBox(height: 10),
            pw.Text('Section ${section.label} — ${section.name} (${section.totalMarks} marks)',
                style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 6),
            for (final q in section.questions)
              pw.Padding(
                padding: const pw.EdgeInsets.only(bottom: 8),
                child: pw.Row(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.SizedBox(
                      width: 24,
                      child: pw.Text('${q.displayNumber}.', style: const pw.TextStyle(fontSize: 10)),
                    ),
                    pw.Expanded(
                      child: pw.Text(q.stem, style: const pw.TextStyle(fontSize: 10)),
                    ),
                    pw.SizedBox(width: 8),
                    pw.Text('[${q.marks}]', style: const pw.TextStyle(fontSize: 10)),
                  ],
                ),
              ),
          ],
          pw.SizedBox(height: 20),
          pw.Text('Generated on-device by AcademicOS — ${meta.generatedBy}',
              style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
        ],
      ),
    );

    final dir = await getApplicationDocumentsDirectory();
    final papersDir = Directory('${dir.path}/academicos_papers');
    if (!await papersDir.exists()) {
      await papersDir.create(recursive: true);
    }
    final file = File('${papersDir.path}/${paper.id}.pdf');
    await file.writeAsBytes(await doc.save());
    return file.path;
  }
}
