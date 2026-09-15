import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../../domain/repositories/requests.dart';
import 'pdf_text_safety.dart';

/// Real, on-device CBSE-format question paper PDF -- not the full fidelity
/// of the server's ReportLab renderer (src/academicos/assessment/pdf.py),
/// but a genuine rendering of the actual generated paper: school name,
/// student-info fields, general instructions, numbered sections, MCQ
/// options, and real blank answer space for descriptive questions -- saved
/// as a real file the user can open. No network call.
class LocalPdfExporter {
  // Objective question types where the student picks/writes a short answer
  // inline (no reserved blank space needed) -- everything else gets real
  // lined space proportional to its marks. Matches QuestionType in
  // domain/entities/enums.dart; kept as plain strings here since
  // GeneratedQuestion.type is the enum's .name string, not the enum itself.
  static const _objectiveTypes = {'mcq', 'assertionReason'};

  /// The pdf package's base Helvetica font is WinAnsi/Latin-1, not full
  /// Unicode -- real teacher-typed titles and corpus text can genuinely
  /// contain em-dashes, en-dashes, bullets, or smart quotes (the demo
  /// seeder's own assessment titles do), and any of those silently render
  /// as a missing glyph rather than throwing. Normalize to ASCII-safe
  /// equivalents on every user-supplied string before it reaches pw.Text.
  static String _safe(String text) => pdfSafe(text);

  static Future<String> exportPaper(GeneratedPaper paper) async {
    final doc = pw.Document();
    final meta = paper.metadata;

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(28),
        header: (context) => context.pageNumber == 1
            ? _firstPageHeader(meta)
            : _continuationHeader(meta),
        footer: (context) => pw.Align(
          alignment: pw.Alignment.centerRight,
          child: pw.Text('Page ${context.pageNumber} of ${context.pagesCount}',
              style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
        ),
        build: (context) => [
          for (final section in paper.sections) ...[
            pw.Container(
              width: double.infinity,
              padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              margin: const pw.EdgeInsets.only(top: 14, bottom: 6),
              color: PdfColors.grey200,
              child: pw.Text(
                _safe('Section ${section.label} - ${section.name} (${section.totalMarks} marks)'),
                style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold),
              ),
            ),
            for (final q in section.questions) _questionBlock(q),
          ],
          pw.SizedBox(height: 20),
          pw.Text(_safe('Generated on-device by AcademicOS - ${meta.generatedBy}'),
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

  static Future<String> exportAnswerKey(GeneratedPaper paper) async {
    final doc = pw.Document();
    final meta = paper.metadata;
    final setStr = meta.setLabel != null && meta.setLabel!.isNotEmpty ? ' (SET ${meta.setLabel})' : '';

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(28),
        header: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.center,
          children: [
            pw.Text(_safe(meta.schoolName),
                style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 4),
            pw.Text(_safe('${meta.assessmentTitle}$setStr - Answer Key & Marking Scheme'),
                style: pw.TextStyle(fontSize: 13, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 2),
            pw.Text(_safe('Class ${meta.grade} - ${meta.subject} | Max Marks: ${meta.totalMarks}'),
                style: const pw.TextStyle(fontSize: 10)),
            pw.SizedBox(height: 4),
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
            pw.Container(
              width: double.infinity,
              padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              margin: const pw.EdgeInsets.only(top: 10, bottom: 6),
              color: PdfColors.grey200,
              child: pw.Text(
                _safe('Section ${section.label} - ${section.name}'),
                style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold),
              ),
            ),
            for (final q in section.questions) ...[
              pw.Padding(
                padding: const pw.EdgeInsets.symmetric(vertical: 4),
                child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Row(
                      crossAxisAlignment: pw.CrossAxisAlignment.start,
                      children: [
                        pw.SizedBox(
                          width: 24,
                          child: pw.Text('Q${q.displayNumber}.',
                              style: pw.TextStyle(fontSize: 10, fontWeight: pw.FontWeight.bold)),
                        ),
                        pw.Expanded(
                          child: pw.Text(_safe(q.stem),
                              maxLines: 2,
                              style: const pw.TextStyle(fontSize: 9.5, color: PdfColors.grey800)),
                        ),
                        pw.SizedBox(width: 8),
                        pw.Text('[${q.marks}m]',
                            style: pw.TextStyle(fontSize: 9.5, fontWeight: pw.FontWeight.bold)),
                      ],
                    ),
                    pw.Padding(
                      padding: const pw.EdgeInsets.only(left: 24, top: 3),
                      child: pw.Container(
                        padding: const pw.EdgeInsets.all(6),
                        decoration: pw.BoxDecoration(
                          border: pw.Border.all(color: PdfColors.grey300, width: 0.5),
                          borderRadius: const pw.BorderRadius.all(pw.Radius.circular(4)),
                        ),
                        child: pw.Column(
                          crossAxisAlignment: pw.CrossAxisAlignment.start,
                          children: [
                            pw.Text('Step-Wise Value Points / Marking Scheme:',
                                style: pw.TextStyle(fontSize: 8.5, fontWeight: pw.FontWeight.bold, color: PdfColors.blueGrey800)),
                            pw.SizedBox(height: 2),
                            pw.Text(
                              _safe(paper.answerKey[q.questionId]?.toString() ?? 'Full marks for correct steps with proper reasoning.'),
                              style: const pw.TextStyle(fontSize: 9),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ],
      ),
    );

    final dir = await getApplicationDocumentsDirectory();
    final papersDir = Directory('${dir.path}/academicos_papers');
    if (!await papersDir.exists()) {
      await papersDir.create(recursive: true);
    }
    final file = File('${papersDir.path}/${paper.id}_answer_key.pdf');
    await file.writeAsBytes(await doc.save());
    return file.path;
  }

  static pw.Widget _firstPageHeader(PaperMetadata meta) {
    final setStr = meta.setLabel != null && meta.setLabel!.isNotEmpty ? ' (SET ${meta.setLabel})' : '';
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.center,
      children: [
        pw.Text(_safe(meta.schoolName),
            style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 4),
        pw.Text(_safe('${meta.assessmentTitle}$setStr'),
            style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 2),
        pw.Text(_safe('Class ${meta.grade} - ${meta.subject}'), style: const pw.TextStyle(fontSize: 11)),
        pw.SizedBox(height: 8),
        pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text('Time: ${meta.durationMinutes} min', style: const pw.TextStyle(fontSize: 10)),
            pw.Text('Max Marks: ${meta.totalMarks}', style: const pw.TextStyle(fontSize: 10)),
          ],
        ),
        pw.SizedBox(height: 8),
        pw.Row(
          children: [
            pw.Expanded(child: _blankField('Name')),
            pw.SizedBox(width: 16),
            pw.Expanded(child: _blankField('Roll No.')),
            pw.SizedBox(width: 16),
            pw.Expanded(child: _blankField('Date')),
          ],
        ),
        pw.SizedBox(height: 8),
        pw.Container(
          width: double.infinity,
          padding: const pw.EdgeInsets.all(6),
          decoration: pw.BoxDecoration(border: pw.Border.all(width: 0.5, color: PdfColors.grey600)),
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text('General Instructions:',
                  style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 2),
              for (final line in const [
                'All questions are compulsory unless an internal choice is indicated.',
                'Read each question carefully before attempting.',
                'Marks for each question are indicated against it.',
                'Write your answers neatly in the space provided.',
              ])
                pw.Text('- $line', style: const pw.TextStyle(fontSize: 8)),
            ],
          ),
        ),
        pw.SizedBox(height: 4),
        pw.Divider(thickness: 1),
      ],
    );
  }

  static pw.Widget _continuationHeader(PaperMetadata meta) {
    final setStr = meta.setLabel != null && meta.setLabel!.isNotEmpty ? ' (SET ${meta.setLabel})' : '';
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.center,
      children: [
        pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text(_safe(meta.schoolName), style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey700)),
            pw.Text(_safe('${meta.subject}$setStr - Class ${meta.grade}'),
                style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey700)),
          ],
        ),
        pw.Divider(thickness: 0.5),
      ],
    );
  }

  static pw.Widget _blankField(String label) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text(label, style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey700)),
        pw.SizedBox(height: 10),
        pw.Container(height: 0.75, color: PdfColors.grey600),
      ],
    );
  }

  static pw.Widget _questionBlock(GeneratedQuestion q) {
    // Real math content typically lives in stemLatex; without a LaTeX
    // rendering engine wired up, prefer the plain stem (which is always
    // readable text) rather than surface raw LaTeX markup to the student.
    final displayText = q.stem.isNotEmpty ? q.stem : q.stemLatex;
    final isObjective = _objectiveTypes.contains(q.type);
    final options = q.parts.isNotEmpty ? q.parts.first.options : null;

    return pw.Padding(
      padding: const pw.EdgeInsets.only(bottom: 10),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.SizedBox(
                width: 24,
                child: pw.Text('${q.displayNumber}.', style: const pw.TextStyle(fontSize: 10)),
              ),
              pw.Expanded(
                child: pw.Text(_safe(displayText), style: const pw.TextStyle(fontSize: 10)),
              ),
              pw.SizedBox(width: 8),
              pw.Text('[${q.marks}]', style: const pw.TextStyle(fontSize: 10)),
            ],
          ),
          if (q.internalChoiceText != null && q.internalChoiceText!.isNotEmpty) ...[
            pw.Padding(
              padding: const pw.EdgeInsets.symmetric(vertical: 4),
              child: pw.Center(
                child: pw.Text('OR', style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold, color: PdfColors.blueGrey800)),
              ),
            ),
            pw.Padding(
              padding: const pw.EdgeInsets.only(left: 24),
              child: pw.Text(_safe(q.internalChoiceText!), style: pw.TextStyle(fontSize: 10, fontStyle: pw.FontStyle.italic)),
            ),
          ],
          if (isObjective && options != null && options.isNotEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(left: 24, top: 4),
              child: pw.Wrap(
                spacing: 16,
                runSpacing: 4,
                children: [
                  for (var i = 0; i < options.length; i++)
                    pw.Text(_safe('(${String.fromCharCode(97 + i)}) ${options[i]}'),
                        style: const pw.TextStyle(fontSize: 9.5)),
                ],
              ),
            ),
          if (!isObjective) _answerSpace(q.marks),
        ],
      ),
    );
  }

  /// Reserves real blank lined space for a handwritten answer, roughly
  /// proportional to marks -- the single biggest visual gap the bare-bones
  /// version had (zero reserved space regardless of question weight).
  static pw.Widget _answerSpace(int marks) {
    final heightPt = (marks * 12).clamp(20, 140).toDouble();
    final lineCount = (heightPt / 14).floor().clamp(1, 10);
    return pw.Padding(
      padding: const pw.EdgeInsets.only(left: 24, top: 4),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          for (var i = 0; i < lineCount; i++)
            pw.Container(
              margin: const pw.EdgeInsets.only(bottom: 10),
              height: 0.5,
              color: PdfColors.grey400,
            ),
        ],
      ),
    );
  }
}
