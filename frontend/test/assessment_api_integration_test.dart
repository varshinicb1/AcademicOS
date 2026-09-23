// Exercises the real ApiClient (the exact class the app's blocs call) against
// the live AssessmentOS backend on localhost:8000. Verifies the backend's
// JSON deserializes cleanly into the app's own freezed/json_serializable
// models — the one layer flutter analyze and raw curl testing can't check.
//
// Requires: `python -m academicos.cli serve --port 8000` running with the
// Class X Science pilot corpus ingested.
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/api_client.dart';
import 'package:academicos/domain/entities/entities.dart';
import 'package:academicos/domain/repositories/requests.dart';

void main() {
  late ApiClient api;

  setUpAll(() {
    final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000/api/v1'));
    api = ApiClient(dio);
  });

  test('full Assessment Designer chain: create -> search -> optimize -> generate -> export', () async {
    final assessment = await api.createAssessment(const CreateAssessmentRequest(
      teacherId: 'test_teacher',
      schoolId: 'test_school',
      title: 'Integration Test Paper',
      subject: 'Science',
      grade: 10,
      chapterIds: [],
      blueprint: BlueprintRequest(
        totalMarks: 30,
        durationMinutes: 60,
        difficulty: DifficultyDistribution(easy: 0.3, medium: 0.5, hard: 0.2),
        bloom: BloomDistribution(remember: 0.2, understand: 0.25, apply: 0.3, analyze: 0.15, evaluate: 0.05, create: 0.05),
        chapterWeights: ChapterWeights(weights: {}),
        competencyWeights: CompetencyWeights(weights: {}),
        sections: [],
      ),
    ));
    expect(assessment.id, isNotEmpty);
    expect(assessment.subject, 'Science');
    expect(assessment.blueprint.sections, isNotEmpty, reason: 'backend should fill in default CBSE sections');
    // ignore: avoid_print
    print('created assessment ${assessment.id} with ${assessment.blueprint.sections.length} sections');

    final candidates = await api.searchQuestions(const QuestionSearchParams(
      subject: 'Science', grade: 10, limit: 200,
    ));
    expect(candidates, isNotEmpty, reason: 'pilot question pool should have real Class X Science questions');
    expect(candidates.every((q) => q.subject == 'Science'), isTrue);
    expect(candidates.map((q) => q.id).toSet().length, candidates.length, reason: 'no duplicate question ids');
    // ignore: avoid_print
    print('found ${candidates.length} candidate questions');

    final optimized = await api.optimizeQuestions(QuestionOptimizationRequest(
      candidates: candidates, blueprint: assessment.blueprint,
    ));
    expect(optimized.selectedQuestions, isNotEmpty);
    // ignore: avoid_print
    print('selected ${optimized.selectedQuestions.length} questions, gaps: ${optimized.gaps}');

    final paper = await api.generatePaper(PaperGenerationRequest(
      assessmentId: assessment.id,
      blueprint: assessment.blueprint,
      selectedQuestions: optimized.selectedQuestions,
      template: const SchoolTemplate(
        id: 'default', schoolId: 'test_school', name: 'Default', headerHtml: '', footerHtml: '',
        logoUrl: '', marginTop: 20, marginBottom: 20, marginLeft: 20, marginRight: 20,
        fontFamily: 'Helvetica', fontSize: 11, lineHeight: 1.4, sectionFormatting: {}, isDefault: true,
      ),
    ));
    expect(paper.sections, isNotEmpty);
    expect(paper.sections.first.label, 'A');
    final totalQuestions = paper.sections.fold<int>(0, (sum, s) => sum + s.questions.length);
    expect(totalQuestions, optimized.selectedQuestions.length);
    // ignore: avoid_print
    print('generated paper ${paper.id} with sections: ${paper.sections.map((s) => '${s.label}(${s.questions.length}q)').join(', ')}');

    final url = await api.exportPaper(paper.id, ExportFormat.pdf);
    expect(url, contains(paper.id));
    // ignore: avoid_print
    print('exported PDF at $url');

    final fetched = await api.getAssessment(assessment.id);
    expect(fetched.id, assessment.id);
    expect(fetched.title, 'Integration Test Paper');
    // 'live-backend': needs the server named in the header above, so the CI
    // gate excludes it (frontend/dart_test.yaml declares the tag). Run it
    // with `flutter test --tags live-backend` once the backend is up.
  }, timeout: const Timeout(Duration(seconds: 30)), tags: 'live-backend');
}
