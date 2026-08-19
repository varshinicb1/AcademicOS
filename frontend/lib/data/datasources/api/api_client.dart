import 'package:dio/dio.dart';

import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';

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

  // Blueprint
  Future<Blueprint> generateBlueprint(BlueprintRequest request) async {
    final response = await _dio.post('/blueprints/generate', data: request.toJson());
    return Blueprint.fromJson(response.data);
  }

  Future<Blueprint> getBlueprint(String assessmentId) async {
    final response = await _dio.get('/blueprints/$assessmentId');
    return Blueprint.fromJson(response.data);
  }

  Future<Blueprint> updateBlueprint(String assessmentId, Blueprint blueprint) async {
    final response = await _dio.put('/blueprints/$assessmentId', data: blueprint.toJson());
    return Blueprint.fromJson(response.data);
  }

  Future<List<SectionBlueprint>> getSchoolTemplates(String schoolId) async {
    final response = await _dio.get('/schools/$schoolId/templates');
    return (response.data as List).map((e) => SectionBlueprint.fromJson(e)).toList();
  }

  Future<void> saveTemplate(String schoolId, SectionBlueprint template) async {
    await _dio.post('/schools/$schoolId/templates', data: template.toJson());
  }

  // Questions
  Future<List<Question>> searchQuestions(QuestionSearchParams params) async {
    final response = await _dio.post('/questions/search', data: params.toJson());
    return (response.data as List).map((e) => Question.fromJson(e)).toList();
  }

  Future<Question> getQuestion(String id) async {
    final response = await _dio.get('/questions/$id');
    return Question.fromJson(response.data);
  }

  Future<List<Question>> getQuestionsByIds(List<String> ids) async {
    final response = await _dio.post('/questions/batch', data: {'ids': ids});
    return (response.data as List).map((e) => Question.fromJson(e)).toList();
  }

  Future<Question> createQuestion(Question question) async {
    final response = await _dio.post('/questions', data: question.toJson());
    return Question.fromJson(response.data);
  }

  Future<Question> updateQuestion(String id, Question question) async {
    final response = await _dio.put('/questions/$id', data: question.toJson());
    return Question.fromJson(response.data);
  }

  Future<void> deleteQuestion(String id) async {
    await _dio.delete('/questions/$id');
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

  Future<GeneratedPaper> getPaper(String paperId) async {
    final response = await _dio.get('/papers/$paperId');
    return GeneratedPaper.fromJson(response.data);
  }

  Future<GeneratedPaper> formatPaper(String paperId, SchoolTemplate template) async {
    final response = await _dio.post('/papers/$paperId/format', data: template.toJson());
    return GeneratedPaper.fromJson(response.data);
  }

  Future<String> exportPaper(String paperId, ExportFormat format) async {
    final response = await _dio.post('/papers/$paperId/export/${format.name}');
    return response.data['url'] as String;
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

  // Answer Sheets
  Future<AnswerSheet> uploadAnswerSheet(AnswerSheetUpload upload) async {
    final response = await _dio.post('/answer-sheets', data: upload.toJson());
    return AnswerSheet.fromJson(response.data);
  }

  Future<AnswerSheet> getAnswerSheet(String id) async {
    final response = await _dio.get('/answer-sheets/$id');
    return AnswerSheet.fromJson(response.data);
  }

  Future<List<AnswerSheet>> getAnswerSheets(String assessmentId) async {
    final response = await _dio.get('/answer-sheets', queryParameters: {'assessment_id': assessmentId});
    return (response.data as List).map((e) => AnswerSheet.fromJson(e)).toList();
  }

  Future<AnswerSheet> processScan(ScanRequest request) async {
    final response = await _dio.post('/answer-sheets/${request.answerSheetId}/process', data: request.toJson());
    return AnswerSheet.fromJson(response.data);
  }

  Future<AnswerSheet> segmentAnswerSheet(String answerSheetId) async {
    final response = await _dio.post('/answer-sheets/$answerSheetId/segment');
    return AnswerSheet.fromJson(response.data);
  }

  Future<AnswerSheet> runOcr(String answerSheetId) async {
    final response = await _dio.post('/answer-sheets/$answerSheetId/ocr');
    return AnswerSheet.fromJson(response.data);
  }

  Future<AnswerSheet> runVision(String answerSheetId) async {
    final response = await _dio.post('/answer-sheets/$answerSheetId/vision');
    return AnswerSheet.fromJson(response.data);
  }

  // Evaluation
  Future<EvaluationResult> evaluateQuestion(EvaluationRequest request) async {
    final response = await _dio.post('/evaluations', data: request.toJson());
    return EvaluationResult.fromJson(response.data);
  }

  Future<List<EvaluationResult>> evaluateAnswerSheet(String answerSheetId) async {
    final response = await _dio.post('/answer-sheets/$answerSheetId/evaluate');
    return (response.data as List).map((e) => EvaluationResult.fromJson(e)).toList();
  }

  Future<EvaluationResult> teacherReview(TeacherReviewRequest request) async {
    final response = await _dio.post('/evaluations/review', data: request.toJson());
    return EvaluationResult.fromJson(response.data);
  }

  Future<void> finalizeEvaluation(String answerSheetId) async {
    await _dio.post('/answer-sheets/$answerSheetId/finalize');
  }

  Future<List<EvaluationResult>> getEvaluations(String answerSheetId) async {
    final response = await _dio.get('/answer-sheets/$answerSheetId/evaluations');
    return (response.data as List).map((e) => EvaluationResult.fromJson(e)).toList();
  }

  // Mastery
  Future<StudentMastery> getStudentMastery(String studentId) async {
    final response = await _dio.get('/mastery/$studentId');
    return StudentMastery.fromJson(response.data);
  }

  Future<StudentMastery> updateStudentMastery(StudentMastery mastery) async {
    final response = await _dio.put('/mastery/${mastery.studentId}', data: mastery.toJson());
    return StudentMastery.fromJson(response.data);
  }

  Future<List<ActionableRecommendation>> getRecommendations(String studentId) async {
    final response = await _dio.get('/mastery/$studentId/recommendations');
    return (response.data as List).map((e) => ActionableRecommendation.fromJson(e)).toList();
  }

  Future<void> recordMasteryAttempt(MasteryAttempt attempt) async {
    await _dio.post('/mastery/attempt', data: attempt.toJson());
  }

  Future<List<ConceptMastery>> getWeakConcepts(String studentId, {int limit = 10}) async {
    final response = await _dio.get('/mastery/$studentId/weak-concepts', queryParameters: {'limit': limit});
    return (response.data as List).map((e) => ConceptMastery.fromJson(e)).toList();
  }

  Future<List<MisconceptionFlag>> getMisconceptions(String studentId) async {
    final response = await _dio.get('/mastery/$studentId/misconceptions');
    return (response.data as List).map((e) => MisconceptionFlag.fromJson(e)).toList();
  }

  // Analytics
  Future<AssessmentAnalytics> getAssessmentAnalytics(String assessmentId) async {
    final response = await _dio.get('/analytics/assessment/$assessmentId');
    return AssessmentAnalytics.fromJson(response.data);
  }

  Future<ClassAnalytics> getClassAnalytics(String classId) async {
    final response = await _dio.get('/analytics/class/$classId');
    return ClassAnalytics.fromJson(response.data);
  }

  Future<StudentAnalytics> getStudentAnalytics(String studentId) async {
    final response = await _dio.get('/analytics/student/$studentId');
    return StudentAnalytics.fromJson(response.data);
  }

  Future<SchoolAnalytics> getSchoolAnalytics(String schoolId) async {
    final response = await _dio.get('/analytics/school/$schoolId');
    return SchoolAnalytics.fromJson(response.data);
  }

  // Reports
  Future<StudentReport> generateStudentReport(ReportRequest request) async {
    final response = await _dio.post('/reports/generate', data: request.toJson());
    return StudentReport.fromJson(response.data);
  }

  Future<String> exportReport(String reportId, ExportFormat format) async {
    final response = await _dio.post('/reports/$reportId/export/${format.name}');
    return response.data['url'] as String;
  }

  Future<List<StudentReport>> generateBulkReports(BulkReportRequest request) async {
    final response = await _dio.post('/reports/bulk', data: request.toJson());
    return (response.data as List).map((e) => StudentReport.fromJson(e)).toList();
  }

  Future<ParentReport> generateParentReport(ReportRequest request) async {
    final response = await _dio.get('/reports/parent/${request.studentId}/${request.assessmentId}');
    return ParentReport.fromJson(response.data);
  }

  // Practice
  Future<PracticeSession> createPracticeSession(PracticeRequest request) async {
    final response = await _dio.post('/practice', data: request.toJson());
    return PracticeSession.fromJson(response.data);
  }

  Future<PracticeSession> getPracticeSession(String id) async {
    final response = await _dio.get('/practice/$id');
    return PracticeSession.fromJson(response.data);
  }

  Future<PracticeResult> submitPractice(PracticeSubmission submission) async {
    final response = await _dio.post('/practice/submit', data: submission.toJson());
    return PracticeResult.fromJson(response.data);
  }

  Future<List<PracticeSession>> getStudentPracticeSessions(String studentId) async {
    final response = await _dio.get('/practice/student/$studentId');
    return (response.data as List).map((e) => PracticeSession.fromJson(e)).toList();
  }

  // Notifications
  Future<void> sendNotification(Notification notification) async {
    await _dio.post('/notifications', data: notification.toJson());
  }

  Future<void> sendWhatsAppNotification(WhatsAppDeepLink link) async {
    await _dio.post('/notifications/whatsapp', data: link.toJson());
  }

  Future<List<Notification>> getNotifications(String userId) async {
    final response = await _dio.get('/notifications/$userId');
    return (response.data as List).map((e) => Notification.fromJson(e)).toList();
  }

  Future<void> markAsRead(String notificationId) async {
    await _dio.patch('/notifications/$notificationId/read');
  }
}