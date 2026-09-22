import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';

// 2026-09-17: removed 42 methods that called backend routes which never
// existed (confirmed exhaustively dead -- no screen, bloc, use case, or DI
// resolution reaches any of them, in either build variant; see
// docs/system-review.html and tests/test_frontend_backend_contract.py's
// former KNOWN_GAPS, now empty). This is the surface the review called
// "a parallel, partially-fictional view" of the backend. Only the methods a
// real screen actually calls remain below.
class ApiClient {
  final Dio _dio;

  ApiClient(Dio dio) : _dio = dio;

  // Assessment
  Future<Assessment> createAssessment(CreateAssessmentRequest request) async {
    final response = await _dio.post('/assessments', data: request.toJson());
    return Assessment.fromJson(response.data);
  }

  Future<Assessment> getAssessment(String id) async {
    final response = await _dio.get('/assessments/$id');
    return Assessment.fromJson(response.data);
  }

  Future<List<Assessment>> getAssessmentsByTeacher(String teacherId) async {
    final response = await _dio.get('/assessments', queryParameters: {'teacher_id': teacherId});
    return (response.data as List).map((e) => Assessment.fromJson(e)).toList();
  }

  Future<List<Assessment>> getAssessmentsBySchool(String schoolId) async {
    final response = await _dio.get('/assessments', queryParameters: {'school_id': schoolId});
    return (response.data as List).map((e) => Assessment.fromJson(e)).toList();
  }

  Future<Assessment> updateAssessment(String id, Assessment assessment) async {
    final response = await _dio.put('/assessments/$id', data: assessment.toJson());
    return Assessment.fromJson(response.data);
  }

  Future<void> deleteAssessment(String id) async {
    await _dio.delete('/assessments/$id');
  }

  Future<Assessment> updateStatus(String id, Map<String, dynamic> status) async {
    final response = await _dio.patch('/assessments/$id/status', data: status);
    return Assessment.fromJson(response.data);
  }

  /// Server-side principal-approval action (auth_routes.require_principal
  /// gated) -- the real workflow docs/compliance.md called for, now that a
  /// real login exists to authenticate as a principal with. The logged-in
  /// user's token rides on every Dio request via the interceptor registered
  /// in service_locator.dart; a 403 here means "logged in, but not as this
  /// school's principal," and a 401 means "not logged in at all."
  Future<Assessment> approveAssessment(String id) async {
    final response = await _dio.patch('/assessments/$id/approve');
    return Assessment.fromJson(response.data);
  }

  // Blueprint
  Future<Blueprint> generateBlueprint(BlueprintRequest request) async {
    final response = await _dio.post('/blueprints/generate', data: request.toJson());
    return Blueprint.fromJson(response.data);
  }

  Future<List<SectionBlueprint>> getSchoolTemplates(String schoolId) async {
    final response = await _dio.get('/schools/$schoolId/templates');
    return (response.data as List).map((e) => SectionBlueprint.fromJson(e)).toList();
  }

  // Questions
  Future<List<Question>> searchQuestions(QuestionSearchParams params) async {
    final response = await _dio.post('/questions/search', data: params.toJson());
    return (response.data as List).map((e) => Question.fromJson(e)).toList();
  }

  Future<QuestionOptimizationResult> optimizeQuestions(QuestionOptimizationRequest request) async {
    final response = await _dio.post('/questions/optimize', data: request.toJson());
    return QuestionOptimizationResult.fromJson(response.data);
  }

  // Paper Generation
  Future<GeneratedPaper> generatePaper(PaperGenerationRequest request) async {
    final response = await _dio.post('/papers/generate', data: request.toJson());
    return GeneratedPaper.fromJson(response.data);
  }

  Future<GeneratedPaper> quickGeneratePaper(QuickPaperRequest request) async =>
      (await quickGenerateWithWarnings(request)).paper;

  /// The quick paper plus the server's `warnings` about it -- above all a
  /// paper holding fewer marks than asked for, section by section. The live
  /// release dropped them: English 10 asked for 80 marks came back holding 20
  /// and nothing on screen said so (re-audit, 2026-09-22). GeneratedPaper
  /// (freezed) has no field for them, so they travel beside it.
  Future<({GeneratedPaper paper, List<String> warnings})> quickGenerateWithWarnings(
      QuickPaperRequest request) async {
    final response = await _dio.post('/papers/quick-generate', data: request.toJson());
    final data = Map<String, dynamic>.from(response.data as Map);
    return (
      paper: GeneratedPaper.fromJson(data),
      warnings: (data['warnings'] as List? ?? const []).map((w) => '$w').toList(),
    );
  }

  Future<GeneratedPaper> generateFromIds(GenerateFromIdsRequest request) async {
    final response = await _dio.post('/papers/generate-from-ids', data: request.toJson());
    return GeneratedPaper.fromJson(response.data);
  }

  /// The next best question for one printed slot ("7", or "7_OR" for its
  /// OR alternative), saved onto the paper and every set by the server
  /// (POST /papers/{id}/questions/{slot}/swap). Returns the updated paper.
  /// The review page's "swap one" on a pair of hand-picked questions that
  /// look alike calls this for the later of the two.
  Future<GeneratedPaper> swapPaperQuestion(String paperId, String slot) async {
    final response = await _dio.post(
        '/papers/${Uri.encodeComponent(paperId)}/questions/${Uri.encodeComponent(slot)}/swap');
    return GeneratedPaper.fromJson(response.data['paper'] as Map<String, dynamic>);
  }

  Future<GeneratedPaper> getPaper(String paperId) async {
    final response = await _dio.get('/papers/$paperId');
    return GeneratedPaper.fromJson(response.data);
  }

  Future<String> exportPaper(String paperId, ExportFormat format) async {
    final response = await _dio.post('/papers/$paperId/export/${format.name}');
    return response.data['url'] as String;
  }

  /// The exported PDF's bytes (the paper, or its answer key), fetched on this
  /// client's Dio so the session interceptor attaches the bearer token.
  /// /papers/{id}/file is staff-only: the live release opened it with
  /// launchUrl, a browser tab sends no token, and teachers got a 401 page
  /// instead of the answer key (re-audit, 2026-09-22).
  Future<Uint8List> downloadPaperPdf(String paperId, {bool answerKey = false}) async {
    final response = await _dio.get<List<int>>(
      '/papers/$paperId/file',
      queryParameters: {if (answerKey) 'format': 'answer-key'},
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(response.data ?? const []);
  }

  Future<List<SchoolTemplate>> getSchoolPaperTemplates(String schoolId) async {
    // `/paper-templates` is a dead stub that always returns a hardcoded
    // "Default CBSE Template" and never touches the TemplateStore — it was
    // silently discarding every school's real branded template on every
    // paper generation. `/school-templates` is the store-backed endpoint
    // template_maker_page.dart actually saves to.
    final response = await _dio.get('/schools/$schoolId/school-templates');
    return (response.data as List).map((e) => SchoolTemplate.fromJson(e)).toList();
  }

  // Practice
  Future<PracticeResult> submitPractice(PracticeSubmission submission) async {
    final response = await _dio.post('/practice/submit', data: submission.toJson());
    return PracticeResult.fromJson(response.data);
  }
}
