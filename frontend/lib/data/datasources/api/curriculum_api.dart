/// Client for the curriculum/schedule endpoints
/// (src/academicos/curriculum/routes.py) -- specifically the teacher-facing
/// slice: "what do I teach today" (`GET /my-schedule`), not the full
/// admin curriculum-authoring surface (extraction/approval/calendar), which
/// has no Flutter UI yet. Same plain-class, no-freezed style as
/// auth_api.dart/pillar_api.dart -- read-mostly data, no codegen needed.
library;

import 'package:dio/dio.dart';

/// One real, dated lesson from a teacher's own assigned schedule -- already
/// enriched server-side (subject/chapter/topic/subtopic names resolved),
/// so this screen never has to stitch together multiple curriculum calls
/// just to show a readable lesson card.
class MyScheduleEntry {
  final String lessonId;
  final String date; // ISO date
  final String status; // scheduled | completed | skipped
  final String? note;
  final String bookId;
  final String bookTitle;
  final String subjectName;
  final String chapterName;
  final String topicName;
  final String subtopicId;
  final String subtopicName;

  MyScheduleEntry.fromJson(Map<String, dynamic> j)
      : lessonId = j['lessonId'] as String,
        date = j['date'] as String,
        status = j['status'] as String,
        note = j['note'] as String?,
        bookId = j['bookId'] as String,
        bookTitle = j['bookTitle'] as String? ?? '',
        subjectName = j['subjectName'] as String? ?? '',
        chapterName = j['chapterName'] as String? ?? '',
        topicName = j['topicName'] as String? ?? '',
        subtopicId = j['subtopicId'] as String,
        subtopicName = j['subtopicName'] as String? ?? '';
}

/// One real, dated lesson from a student's own enrolled class -- §18's
/// deliberately reduced subset of MyScheduleEntry: no note, no
/// completedBy. A student sees what's being taught and its status, not a
/// teacher's private remark about it.
class MyClassScheduleEntry {
  final String date; // ISO date
  final String status; // scheduled | completed | skipped
  final String subjectName;
  final String chapterName;
  final String topicName;
  final String subtopicName;

  MyClassScheduleEntry.fromJson(Map<String, dynamic> j)
      : date = j['date'] as String,
        status = j['status'] as String,
        subjectName = j['subjectName'] as String? ?? '',
        chapterName = j['chapterName'] as String? ?? '',
        topicName = j['topicName'] as String? ?? '',
        subtopicName = j['subtopicName'] as String? ?? '';
}

class SubjectProgress {
  final String subjectName;
  final int scheduledCount;
  final int completedCount;
  final int skippedCount;
  final int totalCount;

  SubjectProgress.fromJson(Map<String, dynamic> j)
      : subjectName = j['subjectName'] as String? ?? '',
        scheduledCount = j['scheduledCount'] as int? ?? 0,
        completedCount = j['completedCount'] as int? ?? 0,
        skippedCount = j['skippedCount'] as int? ?? 0,
        totalCount = j['totalCount'] as int? ?? 0;

  double get completionFraction => totalCount == 0 ? 0 : completedCount / totalCount;
}

class MyProgress {
  final String academicYearId;
  final String asOfDate;
  final List<SubjectProgress> subjects;

  MyProgress.fromJson(Map<String, dynamic> j)
      : academicYearId = j['academicYearId'] as String,
        asOfDate = j['asOfDate'] as String,
        subjects = ((j['subjects'] as List?) ?? const [])
            .map((e) => SubjectProgress.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

/// A school's real academic year -- just enough (id, label, dates) for the
/// student progress view to pick "the current one" to query, since a
/// student's class-schedule/progress endpoints need an explicit
/// academicYearId the way every other curriculum endpoint does.
class AcademicYearSummary {
  final String id;
  final String label;
  final String startDate;
  final String endDate;

  AcademicYearSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        label = j['label'] as String? ?? '',
        startDate = j['startDate'] as String,
        endDate = j['endDate'] as String;
}

class CurriculumApi {
  final Dio _dio;
  CurriculumApi(this._dio);

  /// Public, school-scoped (matches the real /catalog-style read routes) --
  /// used by the student view to find its own school's current academic
  /// year rather than guessing or hardcoding one.
  Future<List<AcademicYearSummary>> academicYears(String schoolId) async {
    final r = await _dio.get('/curriculum/academic-years', queryParameters: {'school_id': schoolId});
    return (r.data as List).map((e) => AcademicYearSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// `startDate`/`endDate` are ISO dates (yyyy-MM-dd), inclusive -- pass the
  /// same date for both to get one day's lessons.
  Future<List<MyScheduleEntry>> mySchedule({required String startDate, required String endDate}) async {
    final r = await _dio.get('/curriculum/my-schedule',
        queryParameters: {'start_date': startDate, 'end_date': endDate});
    return (r.data as List).map((e) => MyScheduleEntry.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §15: YES/NO completion tracking -- `status` is one of "scheduled"
  /// (undo), "completed", or "skipped"; `note` is optional and only
  /// meaningful for completed/skipped. Only the teacher actually assigned
  /// to the lesson's book (or a principal of the same school) may call
  /// this -- the server enforces it, this just surfaces whatever it says.
  Future<void> markLesson(String lessonId, {required String status, String? note}) async {
    await _dio.patch('/curriculum/scheduled-lessons/$lessonId',
        data: {'status': status, if (note != null) 'note': note});
  }

  /// §18: a student's own real class schedule -- read-only, reduced
  /// subset. 404s if the caller isn't enrolled in a class yet.
  Future<List<MyClassScheduleEntry>> myClassSchedule({required String startDate, required String endDate}) async {
    final r = await _dio.get('/curriculum/my-class-schedule',
        queryParameters: {'start_date': startDate, 'end_date': endDate});
    return (r.data as List).map((e) => MyClassScheduleEntry.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §18: a student's real per-subject completion progress for an
  /// academic year.
  Future<MyProgress> myProgress({required String academicYearId}) async {
    final r = await _dio.get('/curriculum/my-progress',
        queryParameters: {'academic_year_id': academicYearId});
    return MyProgress.fromJson(Map<String, dynamic>.from(r.data));
  }
}
