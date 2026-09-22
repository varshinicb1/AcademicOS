import '../../data/datasources/api/api_client.dart';
import 'pdf_saver.dart';

/// Downloads an exported paper (or its answer key) from the server and hands
/// it to [saver]. The bytes come through [api]'s Dio, which carries the
/// session token; see ApiClient.downloadPaperPdf for why a bare link cannot.
Future<void> downloadPaperPdf(ApiClient api, PdfSaver saver, String paperId,
    {bool answerKey = false}) async {
  final bytes = await api.downloadPaperPdf(paperId, answerKey: answerKey);
  await saver.save(bytes, answerKey ? '${paperId}_answer_key.pdf' : '$paperId.pdf');
}
