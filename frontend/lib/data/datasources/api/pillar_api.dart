/// Client for the Pillar 2-6 endpoints (evaluation, knowledge, remediation,
/// teacher + principal intelligence, school templates).
///
/// Deliberately uses plain maps/classes rather than freezed: these payloads are
/// read-mostly dashboard data, and keeping them codegen-free means the screens
/// can evolve without a build_runner cycle.
library;

import 'package:dio/dio.dart';

class ConceptMastery {
  final String conceptId;
  final String conceptName;
  final double mastery;
  final double retention;
  final int evidenceCount;
  final String status;
  final bool isWeak;

  ConceptMastery.fromJson(Map<String, dynamic> j)
      : conceptId = j['conceptId'] ?? '',
        conceptName = j['conceptName'] ?? '',
        mastery = (j['mastery'] ?? 0).toDouble(),
        retention = (j['retention'] ?? 0).toDouble(),
        evidenceCount = j['evidenceCount'] ?? 0,
        status = j['status'] ?? 'learning',
        isWeak = j['isWeak'] ?? false;
}

class StudentMastery {
  final String studentId;
  final double overallMastery;
  final List<ConceptMastery> concepts;
  final List<String> weakConcepts;

  StudentMastery.fromJson(Map<String, dynamic> j)
      : studentId = j['studentId'] ?? '',
        overallMastery = (j['overallMastery'] ?? 0).toDouble(),
        concepts = ((j['concepts'] ?? []) as List)
            .map((e) => ConceptMastery.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        weakConcepts = List<String>.from(j['weakConcepts'] ?? const []);
}

class MarkingPointResultView {
  final String description;
  final bool awarded;
  final int marks;
  final String reason;

  MarkingPointResultView.fromJson(Map<String, dynamic> j)
      : description = j['description'] ?? '',
        awarded = j['awarded'] ?? false,
        marks = j['marks'] ?? 0,
        reason = j['reason'] ?? '';
}

class AnswerEvaluation {
  final String questionId;
  final String stem;
  final String studentAnswer;
  final int awardedMarks;
  final int maxMarks;
  final double percentage;
  final String verdict;
  final double confidence;
  final String reasoning;
  final List<String> strengths;
  final List<String> gaps;
  final List<String> misconceptions;
  final List<String> ocrWarnings;
  final bool needsReview;
  final List<MarkingPointResultView> markingPoints;

  AnswerEvaluation.fromJson(Map<String, dynamic> j)
      : questionId = j['questionId'] ?? '',
        stem = j['stem'] ?? '',
        studentAnswer = j['studentAnswer'] ?? '',
        awardedMarks = j['awardedMarks'] ?? 0,
        maxMarks = j['maxMarks'] ?? 0,
        percentage = (j['percentage'] ?? 0).toDouble(),
        verdict = j['verdict'] ?? '',
        confidence = (j['confidence'] ?? 0).toDouble(),
        reasoning = j['reasoning'] ?? '',
        strengths = List<String>.from(j['strengths'] ?? const []),
        gaps = List<String>.from(j['gaps'] ?? const []),
        misconceptions = List<String>.from(j['misconceptions'] ?? const []),
        ocrWarnings = List<String>.from(j['ocrWarnings'] ?? const []),
        needsReview = j['needsReview'] ?? true,
        markingPoints = ((j['markingPoints'] ?? []) as List)
            .map((e) => MarkingPointResultView.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class SheetEvaluation {
  final String studentId;
  final int totalAwarded;
  final int totalMax;
  final double percentage;
  final int needsReviewCount;
  final List<AnswerEvaluation> evaluations;

  SheetEvaluation.fromJson(Map<String, dynamic> j)
      : studentId = j['studentId'] ?? '',
        totalAwarded = j['totalAwarded'] ?? 0,
        totalMax = j['totalMax'] ?? 0,
        percentage = (j['percentage'] ?? 0).toDouble(),
        needsReviewCount = j['needsReviewCount'] ?? 0,
        evaluations = ((j['evaluations'] ?? []) as List)
            .map((e) => AnswerEvaluation.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class ConceptInsight {
  final String conceptName;
  final double classAccuracy;
  final int studentsRated;
  final List<String> atRiskStudents;
  final String recommendation;
  final int estimatedMinutes;

  ConceptInsight.fromJson(Map<String, dynamic> j)
      : conceptName = j['conceptName'] ?? '',
        classAccuracy = (j['classAccuracy'] ?? 0).toDouble(),
        studentsRated = j['studentsRated'] ?? 0,
        atRiskStudents = List<String>.from(j['atRiskStudents'] ?? const []),
        recommendation = j['recommendation'] ?? '',
        estimatedMinutes = j['estimatedMinutes'] ?? 0;
}

class SharedMistake {
  final String markingPoint;
  final String conceptName;
  final int studentsAffected;
  final double percentage;

  SharedMistake.fromJson(Map<String, dynamic> j)
      : markingPoint = j['markingPoint'] ?? '',
        conceptName = j['conceptName'] ?? '',
        studentsAffected = j['studentsAffected'] ?? 0,
        percentage = (j['percentage'] ?? 0).toDouble();
}

class ClassInsights {
  final String headline;
  final int students;
  final double averagePercentage;
  final String? hardestConcept;
  final List<ConceptInsight> concepts;
  final List<SharedMistake> sharedMistakes;

  ClassInsights.fromJson(Map<String, dynamic> j)
      : headline = j['headline'] ?? '',
        students = j['students'] ?? 0,
        averagePercentage = (j['averagePercentage'] ?? 0).toDouble(),
        hardestConcept = j['hardestConcept'],
        concepts = ((j['concepts'] ?? []) as List)
            .map((e) => ConceptInsight.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        sharedMistakes = ((j['sharedMistakes'] ?? []) as List)
            .map((e) => SharedMistake.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class SubjectRollup {
  final String subject;
  final int grade;
  final double averageMastery;
  final int students;
  final String? weakestConcept;
  final double curriculumCoverage;

  SubjectRollup.fromJson(Map<String, dynamic> j)
      : subject = j['subject'] ?? '',
        grade = j['grade'] ?? 0,
        averageMastery = (j['averageMastery'] ?? 0).toDouble(),
        students = j['students'] ?? 0,
        weakestConcept = j['weakestConcept'],
        curriculumCoverage = (j['curriculumCoverage'] ?? 0).toDouble();
}

class SchoolInsights {
  final int students;
  final int assessments;
  final double averageMastery;
  final List<SubjectRollup> subjects;
  final List<String> interventions;

  SchoolInsights.fromJson(Map<String, dynamic> j)
      : students = j['students'] ?? 0,
        assessments = j['assessments'] ?? 0,
        averageMastery = (j['averageMastery'] ?? 0).toDouble(),
        subjects = ((j['subjects'] ?? []) as List)
            .map((e) => SubjectRollup.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        interventions = List<String>.from(j['interventions'] ?? const []);
}

class PracticeItemView {
  final String questionId;
  final String conceptId;
  final String stem;
  final int marks;
  final String difficulty;

  PracticeItemView.fromJson(Map<String, dynamic> j)
      : questionId = j['questionId'] ?? '',
        conceptId = j['conceptId'] ?? '',
        stem = j['stem'] ?? '',
        marks = j['marks'] ?? 0,
        difficulty = j['difficulty'] ?? '';
}

class PracticeSetView {
  final String id;
  final List<PracticeItemView> items;
  final int totalMarks;
  final List<String> warnings;

  PracticeSetView.fromJson(Map<String, dynamic> j)
      : id = j['id'] ?? '',
        items = ((j['items'] ?? []) as List)
            .map((e) => PracticeItemView.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        totalMarks = j['totalMarks'] ?? 0,
        warnings = List<String>.from(j['warnings'] ?? const []);
}

class PracticeOutcomeView {
  final String conceptName;
  final double masteryBefore;
  final double masteryAfter;
  final double delta;
  final bool mastered;

  PracticeOutcomeView.fromJson(Map<String, dynamic> j)
      : conceptName = j['conceptName'] ?? '',
        masteryBefore = (j['masteryBefore'] ?? 0).toDouble(),
        masteryAfter = (j['masteryAfter'] ?? 0).toDouble(),
        delta = (j['delta'] ?? 0).toDouble(),
        mastered = j['mastered'] ?? false;
}

class PracticeResultView {
  final int score;
  final int maxScore;
  final double percentage;
  final List<PracticeOutcomeView> outcomes;
  final String nextAction;

  PracticeResultView.fromJson(Map<String, dynamic> j)
      : score = j['score'] ?? 0,
        maxScore = j['maxScore'] ?? 0,
        percentage = (j['percentage'] ?? 0).toDouble(),
        outcomes = ((j['outcomes'] ?? []) as List)
            .map((e) => PracticeOutcomeView.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        nextAction = j['nextAction'] ?? '';
}

class CatalogEntry {
  final String subject;
  final int grade;
  final int questionCount;
  final int chapters;
  final List<int> marksAvailable;

  CatalogEntry.fromJson(Map<String, dynamic> j)
      : subject = j['subject'] ?? '',
        grade = j['grade'] ?? 0,
        questionCount = j['questionCount'] ?? 0,
        chapters = j['chapters'] ?? 0,
        marksAvailable = List<int>.from(j['marksAvailable'] ?? const []);
}

class Catalog {
  final List<CatalogEntry> entries;
  final int totalQuestions;

  Catalog.fromJson(Map<String, dynamic> j)
      : entries = ((j['entries'] ?? []) as List)
            .map((e) => CatalogEntry.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        totalQuestions = j['totalQuestions'] ?? 0;
}

class ChapterEntry {
  final String chapterId;
  final String chapterName;
  final int questionCount;
  final List<int> marksAvailable;
  final String? unitName;
  final int? syllabusMarks;

  ChapterEntry.fromJson(Map<String, dynamic> j)
      : chapterId = j['chapterId'] ?? '',
        chapterName = j['chapterName'] ?? '',
        questionCount = j['questionCount'] ?? 0,
        marksAvailable = List<int>.from(j['marksAvailable'] ?? const []),
        unitName = j['unitName'],
        syllabusMarks = j['syllabusMarks'];
}

class SyllabusUnit {
  final String unitNo;
  final String name;
  final int marks;
  final List<String> chapterNames;

  SyllabusUnit.fromJson(Map<String, dynamic> j)
      : unitNo = j['unitNo'] ?? '',
        name = j['name'] ?? '',
        marks = j['marks'] ?? 0,
        chapterNames = List<String>.from(j['chapterNames'] ?? const []);
}

class Syllabus {
  final String subject;
  final int grade;
  final int totalMarks;
  final String source;
  final List<SyllabusUnit> units;

  Syllabus.fromJson(Map<String, dynamic> j)
      : subject = j['subject'] ?? '',
        grade = j['grade'] ?? 0,
        totalMarks = j['totalMarks'] ?? 0,
        source = j['source'] ?? '',
        units = ((j['units'] ?? []) as List)
            .map((e) => SyllabusUnit.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class UnitAllocation {
  final String unitName;
  final int marks;
  final int suggestedPeriods;

  UnitAllocation.fromJson(Map<String, dynamic> j)
      : unitName = j['unitName'] ?? '',
        marks = j['marks'] ?? 0,
        suggestedPeriods = j['suggestedPeriods'] ?? 0;
}

class WeekSlot {
  final int week;
  final String unitName;
  final int periods;

  WeekSlot.fromJson(Map<String, dynamic> j)
      : week = j['week'] ?? 0,
        unitName = j['unitName'] ?? '',
        periods = j['periods'] ?? 0;
}

class Timetable {
  final String subject;
  final int grade;
  final int periodsPerWeek;
  final int weeks;
  final List<UnitAllocation> allocations;
  final List<WeekSlot> schedule;

  Timetable.fromJson(Map<String, dynamic> j)
      : subject = j['subject'] ?? '',
        grade = j['grade'] ?? 0,
        periodsPerWeek = j['periodsPerWeek'] ?? 0,
        weeks = j['weeks'] ?? 0,
        allocations = ((j['allocations'] ?? []) as List)
            .map((e) => UnitAllocation.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        schedule = ((j['schedule'] ?? []) as List)
            .map((e) => WeekSlot.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

/// A question as shown in the bank (a trimmed view of the full QuestionSchema).
class BankQuestion {
  final String id;
  final String stem;
  final int marks;
  final String difficulty;
  final String bloomLevel;
  final String type;
  final List<String> chapterIds;
  final List<String> chapterNames;

  BankQuestion.fromJson(Map<String, dynamic> j)
      : id = j['id'] ?? '',
        stem = j['stem'] ?? '',
        marks = j['marks'] ?? 0,
        difficulty = j['difficulty'] ?? 'medium',
        bloomLevel = j['bloomLevel'] ?? 'understand',
        type = j['type'] ?? '',
        chapterIds = List<String>.from(j['chapterIds'] ?? const []),
        chapterNames = List<String>.from(j['tags'] ?? const []);
}

class ScanSession {
  final String id;
  final String assessmentId;
  final String studentId;
  final String studentName;
  final String status;
  final int pagesCaptured;

  ScanSession.fromJson(Map<String, dynamic> j)
      : id = j['id'] ?? '',
        assessmentId = j['assessmentId'] ?? '',
        studentId = j['studentId'] ?? '',
        studentName = j['studentName'] ?? '',
        status = j['status'] ?? '',
        pagesCaptured = j['pagesCaptured'] ?? 0;
}

class CapturedPageResult {
  final int pageNo;
  final bool cropped;
  final String ocrPreview;
  final List<String> warnings;

  CapturedPageResult.fromJson(Map<String, dynamic> j)
      : pageNo = j['pageNo'] ?? 0,
        cropped = j['cropped'] ?? false,
        ocrPreview = j['ocrPreview'] ?? '',
        warnings = List<String>.from(j['warnings'] ?? const []);
}

class ScanMarkingPoint {
  final String id;
  final String description;
  final bool awarded;
  final int marks;
  final String reason;

  ScanMarkingPoint.fromJson(Map<String, dynamic> j)
      : id = j['id'] ?? '',
        description = j['description'] ?? '',
        awarded = j['awarded'] ?? false,
        marks = j['marks'] ?? 0,
        reason = j['reason'] ?? '';
}

class ScanReviewItem {
  final String questionId;
  final int displayNumber;
  final String stem;
  final int maxMarks;
  final String studentAnswer;
  final int awardedMarks;
  final String verdict;
  final double confidence;
  final String reasoning;
  final List<ScanMarkingPoint> markingPoints;
  final List<String> ocrWarnings;
  final bool needsReview;
  final String status;
  final int? teacherMarks;
  final String teacherComment;
  final int finalMarks;
  final List<String> pageImageUrls;

  ScanReviewItem.fromJson(Map<String, dynamic> j)
      : questionId = j['questionId'] ?? '',
        displayNumber = j['displayNumber'] ?? 0,
        stem = j['stem'] ?? '',
        maxMarks = j['maxMarks'] ?? 0,
        studentAnswer = j['studentAnswer'] ?? '',
        awardedMarks = j['awardedMarks'] ?? 0,
        verdict = j['verdict'] ?? '',
        confidence = (j['confidence'] ?? 0).toDouble(),
        reasoning = j['reasoning'] ?? '',
        markingPoints = ((j['markingPoints'] ?? []) as List)
            .map((e) => ScanMarkingPoint.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        ocrWarnings = List<String>.from(j['ocrWarnings'] ?? const []),
        needsReview = j['needsReview'] ?? true,
        status = j['status'] ?? 'pending',
        teacherMarks = j['teacherMarks'],
        teacherComment = j['teacherComment'] ?? '',
        finalMarks = j['finalMarks'] ?? 0,
        pageImageUrls = List<String>.from(j['pageImageUrls'] ?? const []);
}

class ScanReviewQueue {
  final List<ScanReviewItem> items;
  final List<String> warnings;

  ScanReviewQueue.fromJson(Map<String, dynamic> j)
      : items = ((j['items'] ?? []) as List)
            .map((e) => ScanReviewItem.fromJson(Map<String, dynamic>.from(e)))
            .toList(),
        warnings = List<String>.from(j['warnings'] ?? const []);
}

class ScanFinalizeResult {
  final int totalAwarded;
  final int totalMax;
  final String rawPdfUrl;
  final String correctedPdfUrl;

  ScanFinalizeResult.fromJson(Map<String, dynamic> j)
      : totalAwarded = j['totalAwarded'] ?? 0,
        totalMax = j['totalMax'] ?? 0,
        rawPdfUrl = j['rawPdfUrl'] ?? '',
        correctedPdfUrl = j['correctedPdfUrl'] ?? '';
}

class PillarApi {
  final Dio _dio;
  PillarApi(this._dio);

  /// Origin (scheme + host, no path) the Dio client is actually configured
  /// against — used to resolve relative file URLs the backend returns (paper
  /// exports, scan page images). Derived from the real baseUrl rather than a
  /// separate --dart-define, so it can't silently drift out of sync with it
  /// the way a hardcoded 'ACADEMICOS_ORIGIN' default did (it pointed at
  /// localhost:8010 in production because only ACADEMICOS_API was ever
  /// actually passed at build time).
  String get serverOrigin => Uri.parse(_dio.options.baseUrl).origin;

  Future<Catalog> catalog() async {
    final r = await _dio.get('/catalog',
        options: Options(receiveTimeout: const Duration(minutes: 5)));
    return Catalog.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<List<ChapterEntry>> chapters(String subject, int grade) async {
    final r = await _dio.get('/catalog/$subject/$grade/chapters',
        options: Options(receiveTimeout: const Duration(minutes: 5)));
    return (r.data as List)
        .map((e) => ChapterEntry.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  /// Real official CBSE unit/chapter/marks-weightage structure. Currently
  /// only populated for Class X (see cbse_syllabus.py); 404s otherwise.
  Future<Syllabus> syllabus(String subject, int grade) async {
    final r = await _dio.get('/syllabus/$subject/$grade');
    return Syllabus.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// AI-suggested weekly pacing: the given weekly periods allocated
  /// proportionally to each unit's official marks-weightage.
  Future<Timetable> timetable(String subject, int grade,
      {int periodsPerWeek = 6, int weeks = 20}) async {
    final r = await _dio.get('/syllabus/$subject/$grade/timetable', queryParameters: {
      'periods_per_week': periodsPerWeek,
      'weeks': weeks,
    });
    return Timetable.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Raw question JSON — needed when a question must be posted straight back
  /// to the evaluation endpoint, which expects the full schema.
  Future<List<Map<String, dynamic>>> searchQuestionsRaw({
    required String subject,
    required int grade,
    int limit = 50,
  }) async {
    final r = await _dio.post('/questions/search',
        data: {'subject': subject, 'grade': grade, 'limit': limit});
    return (r.data as List).map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<List<BankQuestion>> searchQuestions({
    required String subject,
    required int grade,
    String? keyword,
    int? minMarks,
    int? maxMarks,
    List<String>? chapterIds,
    int limit = 200,
  }) async {
    final r = await _dio.post('/questions/search', data: {
      'subject': subject,
      'grade': grade,
      if (keyword != null) 'keyword': keyword,
      if (minMarks != null) 'minMarks': minMarks,
      if (maxMarks != null) 'maxMarks': maxMarks,
      if (chapterIds != null && chapterIds.isNotEmpty) 'chapterIds': chapterIds,
      'limit': limit,
    });
    return (r.data as List)
        .map((e) => BankQuestion.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<StudentMastery> knowledge(String studentId) async {
    final r = await _dio.get('/knowledge/$studentId');
    return StudentMastery.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<ClassInsights> classInsights(String assessmentId, {String classId = '10A'}) async {
    final r = await _dio.get('/insights/class/$assessmentId',
        queryParameters: {'class_id': classId});
    return ClassInsights.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<SchoolInsights> schoolInsights(String schoolId) async {
    final r = await _dio.get('/insights/school/$schoolId');
    return SchoolInsights.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<PracticeSetView> generatePractice(String studentId, {int perConcept = 2}) async {
    final r = await _dio.post('/practice/generate',
        data: {'studentId': studentId, 'perConcept': perConcept});
    return PracticeSetView.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<PracticeResultView> submitPractice(String setId, Map<String, String> answers) async {
    final r = await _dio.post('/practice/submit',
        data: {'setId': setId, 'answers': answers});
    return PracticeResultView.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<SheetEvaluation> evaluateSheet({
    required String assessmentId,
    required String studentId,
    required List<Map<String, dynamic>> questions,
    required Map<String, String> answers,
    Map<String, String> correctOptions = const {},
  }) async {
    final r = await _dio.post('/evaluations/sheet', data: {
      'assessmentId': assessmentId,
      'studentId': studentId,
      'questions': questions,
      'answers': answers,
      'correctOptions': correctOptions,
    });
    return SheetEvaluation.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<Map<String, dynamic>> mailStatus() async {
    final r = await _dio.get('/mail/status');
    return Map<String, dynamic>.from(r.data);
  }

  Future<Map<String, dynamic>> sendPaper({
    required String paperId,
    required List<String> recipients,
    required String subjectName,
    required int grade,
    required String paperTitle,
    String schoolName = 'AcademicOS School',
    String note = '',
    bool includeAnswerKey = true,
  }) async {
    final r = await _dio.post('/mail/send-paper', data: {
      'paperId': paperId,
      'recipients': recipients,
      'subjectName': subjectName,
      'grade': grade,
      'paperTitle': paperTitle,
      'schoolName': schoolName,
      'note': note,
      'includeAnswerKey': includeAnswerKey,
    });
    return Map<String, dynamic>.from(r.data);
  }

  Future<List<Map<String, dynamic>>> schoolTemplates(String schoolId) async {
    final r = await _dio.get('/schools/$schoolId/school-templates');
    return (r.data as List).map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<List<Map<String, dynamic>>> templateSections(String schoolId, String templateId) async {
    final r = await _dio.get('/schools/$schoolId/school-templates/$templateId/sections');
    return (r.data as List).map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<Map<String, dynamic>> saveTemplate(
      String schoolId, Map<String, dynamic> template, List<Map<String, dynamic>> sections) async {
    final r = await _dio.post('/schools/$schoolId/school-templates',
        data: {'template': template, 'sections': sections});
    return Map<String, dynamic>.from(r.data);
  }

  Future<List<Map<String, dynamic>>> listAssessmentsForSchool(String schoolId) async {
    // `school_id`, not `schoolId`: unlike every camelCase-aliased request body
    // in this API, GET /assessments reads its filter straight off plain
    // FastAPI query parameters, which aren't touched by the Camel/to_camel
    // aliasing — that only applies to Pydantic model fields. Confirmed by
    // testing both spellings directly: camelCase silently matched nothing.
    final r = await _dio.get('/assessments', queryParameters: {'school_id': schoolId});
    return (r.data as List).map((e) => Map<String, dynamic>.from(e)).toList();
  }

  // ---- Mobile scan-and-grade ----

  Future<ScanSession> createScanSession({
    required String assessmentId,
    required String studentId,
    required String studentName,
  }) async {
    final r = await _dio.post('/scan/sessions', data: {
      'assessmentId': assessmentId,
      'studentId': studentId,
      'studentName': studentName,
    });
    return ScanSession.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<CapturedPageResult> uploadScanPage(String sessionId, String imagePath) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(imagePath, filename: imagePath.split(RegExp(r'[\\/]')).last),
    });
    final r = await _dio.post('/scan/sessions/$sessionId/pages', data: form);
    return CapturedPageResult.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<ScanReviewQueue> processScanSession(String sessionId) async {
    // Scores every question with a separate sarvam-105b call, sequentially —
    // confirmed by testing that a real 10-question paper took over 100
    // seconds end to end. The app-wide 30s receiveTimeout (fine for every
    // other endpoint here) aborts this one client-side even though the
    // server keeps working and finishes correctly; the teacher would see a
    // false timeout error on every scan.
    final r = await _dio.post('/scan/sessions/$sessionId/process',
        options: Options(receiveTimeout: const Duration(minutes: 5)));
    return ScanReviewQueue.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<ScanReviewQueue> getScanReview(String sessionId) async {
    final r = await _dio.get('/scan/sessions/$sessionId/review');
    return ScanReviewQueue.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<ScanReviewItem> submitReviewDecision(
    String sessionId,
    String questionId, {
    required String action,
    int? marks,
    String comment = '',
  }) async {
    final r = await _dio.post('/scan/sessions/$sessionId/review/$questionId', data: {
      'action': action,
      if (marks != null) 'marks': marks,
      'comment': comment,
    });
    return ScanReviewItem.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<ScanFinalizeResult> finalizeScanSession(String sessionId) async {
    final r = await _dio.post('/scan/sessions/$sessionId/finalize');
    return ScanFinalizeResult.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Downloads a PDF (raw booklet or corrected sheet) to a local temp file
  /// and returns the path — callers hand this to `printing`/`OpenFile`.
  Future<String> downloadScanPdf(String url, String savePath) async {
    await _dio.download(url, savePath);
    return savePath;
  }
}
