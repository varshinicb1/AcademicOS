import '../../data/datasources/api/api_client.dart';
import 'pdf_saver.dart';

/// Downloads an exported paper (or its answer key) from the server and hands
/// it to [saver]. The bytes come through [api]'s Dio, which carries the
/// session token; see ApiClient.downloadPaperPdf for why a bare link cannot.
///
/// [filename] names the file the teacher gets (see [paperFileName]); without
/// one it is the paper's id.
Future<void> downloadPaperPdf(ApiClient api, PdfSaver saver, String paperId,
    {bool answerKey = false, String? filename}) async {
  final bytes = await api.downloadPaperPdf(paperId, answerKey: answerKey);
  await saver.save(bytes, filename ?? (answerKey ? '${paperId}_answer_key.pdf' : '$paperId.pdf'));
}

/// A file name a teacher can find in Downloads:
/// "class_10_mathematics_half_yearly_examination_set_b_answer_key.pdf",
/// the builder's naming (PaperBuilderController._fileBase). The class and
/// subject are added unless the title already says the class. [kind] is
/// `paper` or `answer_key`; [set] is given only when the paper has several.
/// It used to be `paper_fafce43ab953.docx` (QA P-24).
String paperFileName({
  required String title,
  required int grade,
  required String subject,
  String? set,
  String kind = 'paper',
  String extension = 'pdf',
}) {
  final named = title.toLowerCase().contains('class $grade') ? title : 'Class $grade $subject $title';
  final slug = [named, if (set != null && set.isNotEmpty) 'set $set', kind]
      .join(' ')
      .toLowerCase()
      .replaceAll(RegExp(r'[^a-z0-9]+'), '_')
      .replaceAll(RegExp(r'^_+|_+$'), '');
  return '${slug.isEmpty ? 'paper' : slug}.$extension';
}
