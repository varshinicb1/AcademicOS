/// Client for the curriculum/schedule endpoints
/// (src/academicos/curriculum/routes.py) -- mainly the teacher-facing
/// slice: "what do I teach today" (`GET /my-schedule`), plus a read-only
/// Topic/Subtopic lookup the Assessment Designer's subtopic picker uses
/// (topicsForChapter). Not the full admin curriculum-authoring surface
/// (extraction/approval/calendar), which has no Flutter UI yet. Same
/// plain-class, no-freezed style as auth_api.dart/pillar_api.dart --
/// read-mostly data, no codegen needed.
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

/// Just enough of Grade/Subject/Book to populate the admin picker
/// dropdowns -- the same real curriculum hierarchy every other screen
/// this session built reads, not a separate representation.
class GradeSummary {
  final String id;
  final int number;
  final String? section;
  GradeSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String, number = j['number'] as int, section = j['section'] as String?;
  String get label => section == null ? 'Grade $number' : 'Grade $number$section';
}

class SubjectSummary {
  final String id;
  final String name;
  SubjectSummary.fromJson(Map<String, dynamic> j) : id = j['id'] as String, name = j['name'] as String;
}

class BookSummary {
  final String id;
  final String subjectId;
  final String title;
  BookSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String, subjectId = j['subjectId'] as String, title = j['title'] as String;
}

/// One real, admin-approved Subtopic under a Topic -- the finest-grained
/// unit a question can be tagged against (qmap.py::map_subtopics).
class SubtopicSummary {
  final String id;
  final String name;
  SubtopicSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String, name = j['name'] as String;
}

/// A chapter's real Topic, with its real, approved Subtopics already
/// nested (the backend's `GET /chapters/{chapterId}/topics` returns both in
/// one call -- no separate per-topic fetch needed).
class TopicWithSubtopics {
  final String id;
  final String name;
  final List<SubtopicSummary> subtopics;
  TopicWithSubtopics.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        name = j['name'] as String,
        subtopics = (j['subtopics'] as List? ?? const [])
            .map((e) => SubtopicSummary.fromJson(Map<String, dynamic>.from(e)))
            .toList();
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

  Future<List<GradeSummary>> grades(String academicYearId) async {
    final r = await _dio.get('/curriculum/academic-years/$academicYearId/grades');
    return (r.data as List).map((e) => GradeSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  Future<List<SubjectSummary>> subjects(String gradeId) async {
    final r = await _dio.get('/curriculum/grades/$gradeId/subjects');
    return (r.data as List).map((e) => SubjectSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  Future<List<BookSummary>> books(String subjectId) async {
    final r = await _dio.get('/curriculum/subjects/$subjectId/books');
    return (r.data as List).map((e) => BookSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §15's missing link: which teacher teaches which real book.
  /// Principal-gated server-side.
  Future<void> assignTeacher({required String teacherId, required String bookId}) async {
    await _dio.post('/curriculum/teacher-assignments', data: {'teacherId': teacherId, 'bookId': bookId});
  }

  /// §18's missing link: which real class a student belongs to.
  /// Principal-gated server-side.
  Future<void> enrollStudent({required String studentId, required String gradeId}) async {
    await _dio.post('/curriculum/student-enrollments', data: {'studentId': studentId, 'gradeId': gradeId});
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

  /// Real Topics + nested Subtopics for one chapter -- feeds the Assessment
  /// Designer's subtopic picker (assessment_create_page.dart), which uses
  /// this to let a teacher filter question search to specific subtopics via
  /// `QuestionSearchParams.subtopicIds` rather than a whole chapter. Any
  /// authenticated user may call this (read-only, server-side unscoped by
  /// school since chapter content isn't school-specific).
  Future<List<TopicWithSubtopics>> topicsForChapter(String chapterId) async {
    final r = await _dio.get('/curriculum/chapters/$chapterId/topics');
    return (r.data as List).map((e) => TopicWithSubtopics.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §17, §32: Coverage and pace variance report for school management.
  Future<CoverageReport> coverageReport({required String academicYearId, String? asOfDate}) async {
    final r = await _dio.get('/curriculum/reporting/coverage', queryParameters: {
      'academic_year_id': academicYearId,
      if (asOfDate != null) 'as_of_date': asOfDate,
    });
    return CoverageReport.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// §17, §32: Overdue scheduled lessons for school management.
  Future<DelayedTopicsReport> delayedTopics({required String academicYearId, String? asOfDate}) async {
    final r = await _dio.get('/curriculum/reporting/delayed-topics', queryParameters: {
      'academic_year_id': academicYearId,
      if (asOfDate != null) 'as_of_date': asOfDate,
    });
    return DelayedTopicsReport.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// §11-14: Reschedule a single lesson (ADJUST) to a new target working day.
  Future<void> rescheduleLesson(String lessonId, {required String targetDate, required String reason}) async {
    await _dio.post('/curriculum/scheduled-lessons/$lessonId/reschedule', data: {
      'targetDate': targetDate,
      'reason': reason,
    });
  }

  /// §11-14: Shift subsequent lessons after an unexpected disruption (PUSH).
  Future<Map<String, dynamic>> pushSchedule({
    required String bookId,
    required String academicYearId,
    required String afterDate,
    required String reason,
  }) async {
    final r = await _dio.post('/curriculum/books/$bookId/schedule/push', data: {
      'academicYearId': academicYearId,
      'afterDate': afterDate,
      'reason': reason,
    });
    return Map<String, dynamic>.from(r.data);
  }

  /// §5-9, §13: Fetch units for a book.
  Future<List<UnitSummary>> units(String bookId) async {
    final r = await _dio.get('/curriculum/books/$bookId/units');
    return (r.data as List).map((e) => UnitSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §5-9, §13: Fetch chapters for a book.
  Future<List<ChapterSummary>> chapters(String bookId) async {
    final r = await _dio.get('/curriculum/books/$bookId/chapters');
    return (r.data as List).map((e) => ChapterSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §13: Sequence reordering endpoints.
  Future<void> setUnitSequence(String unitId, int seq) async {
    await _dio.patch('/curriculum/units/$unitId/sequence', data: {'seq': seq});
  }

  Future<void> setChapterSequence(String chapterId, int seq) async {
    await _dio.patch('/curriculum/chapters/$chapterId/sequence', data: {'seq': seq});
  }

  Future<void> setTopicSequence(String topicId, int seq) async {
    await _dio.patch('/curriculum/topics/$topicId/sequence', data: {'seq': seq});
  }

  Future<void> setSubtopicSequence(String subtopicId, int seq) async {
    await _dio.patch('/curriculum/subtopics/$subtopicId/sequence', data: {'seq': seq});
  }

  /// §8, §10: Academic calendar setup and working days.
  Future<CalendarInfo> createCalendar(String academicYearId, {List<int> weeklyOffDays = const [7], String alternateSaturdayRule = 'none'}) async {
    final r = await _dio.post('/curriculum/academic-years/$academicYearId/calendar', data: {
      'weeklyOffDays': weeklyOffDays,
      'alternateSaturdayRule': alternateSaturdayRule,
    });
    return CalendarInfo.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<CalendarInfo?> getCalendar(String academicYearId) async {
    try {
      final r = await _dio.get('/curriculum/academic-years/$academicYearId/calendar');
      return CalendarInfo.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<HolidayInfo> addHoliday(String academicYearId, {required String date, required String label, String kind = 'public', String? endDate}) async {
    final r = await _dio.post('/curriculum/academic-years/$academicYearId/holidays', data: {
      'date': date,
      'label': label,
      'kind': kind,
      if (endDate != null) 'endDate': endDate,
    });
    return HolidayInfo.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<List<HolidayInfo>> listHolidays(String academicYearId) async {
    final r = await _dio.get('/curriculum/academic-years/$academicYearId/holidays');
    return (r.data as List).map((e) => HolidayInfo.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  Future<void> setPeriodConfiguration(String academicYearId, {required int periodMinutes}) async {
    await _dio.post('/curriculum/academic-years/$academicYearId/period-configuration', data: {
      'periodMinutes': periodMinutes,
    });
  }

  Future<WorkingDaysSummary> getWorkingDays(String academicYearId) async {
    final r = await _dio.get('/curriculum/academic-years/$academicYearId/working-days');
    return WorkingDaysSummary.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// §11-14: School-wide master schedule across all subjects.
  Future<List<ScheduledLessonSummary>> schoolSchedule({required String startDate, required String endDate}) async {
    final r = await _dio.get('/curriculum/schedule', queryParameters: {
      'start_date': startDate,
      'end_date': endDate,
    });
    return (r.data as List).map((e) => ScheduledLessonSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }
}

class ChapterCoverage {
  final String chapterId;
  final String chapterName;
  final int plannedCount;
  final int completedCount;
  final int skippedCount;
  final int totalCount;
  final double coveragePercent;
  final double pacePercent;
  final int variance;

  ChapterCoverage.fromJson(Map<String, dynamic> j)
      : chapterId = j['chapterId'] as String? ?? '',
        chapterName = j['chapterName'] as String? ?? '',
        plannedCount = j['plannedCount'] as int? ?? 0,
        completedCount = j['completedCount'] as int? ?? 0,
        skippedCount = j['skippedCount'] as int? ?? 0,
        totalCount = j['totalCount'] as int? ?? 0,
        coveragePercent = (j['coveragePercent'] as num?)?.toDouble() ?? 0.0,
        pacePercent = (j['pacePercent'] as num?)?.toDouble() ?? 0.0,
        variance = j['variance'] as int? ?? 0;
}

class SubjectCoverage {
  final String subjectId;
  final String subjectName;
  final String? teacherId;
  final String? teacherName;
  final int plannedCount;
  final int completedCount;
  final int skippedCount;
  final int totalCount;
  final double coveragePercent;
  final double pacePercent;
  final int variance;
  final List<ChapterCoverage> chapters;

  SubjectCoverage.fromJson(Map<String, dynamic> j)
      : subjectId = j['subjectId'] as String? ?? '',
        subjectName = j['subjectName'] as String? ?? '',
        teacherId = j['teacherId'] as String?,
        teacherName = j['teacherName'] as String?,
        plannedCount = j['plannedCount'] as int? ?? 0,
        completedCount = j['completedCount'] as int? ?? 0,
        skippedCount = j['skippedCount'] as int? ?? 0,
        totalCount = j['totalCount'] as int? ?? 0,
        coveragePercent = (j['coveragePercent'] as num?)?.toDouble() ?? 0.0,
        pacePercent = (j['pacePercent'] as num?)?.toDouble() ?? 0.0,
        variance = j['variance'] as int? ?? 0,
        chapters = ((j['chapters'] as List?) ?? const [])
            .map((e) => ChapterCoverage.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class CoverageReport {
  final String academicYearId;
  final String asOfDate;
  final List<SubjectCoverage> subjects;

  CoverageReport.fromJson(Map<String, dynamic> j)
      : academicYearId = j['academicYearId'] as String? ?? '',
        asOfDate = j['asOfDate'] as String? ?? '',
        subjects = ((j['subjects'] as List?) ?? const [])
            .map((e) => SubjectCoverage.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class DelayedLesson {
  final String lessonId;
  final String bookId;
  final String subtopicId;
  final String subtopicName;
  final String chapterName;
  final String subjectName;
  final String? teacherId;
  final String? teacherName;
  final String scheduledDate;
  final int daysOverdue;

  DelayedLesson.fromJson(Map<String, dynamic> j)
      : lessonId = j['lessonId'] as String? ?? '',
        bookId = j['bookId'] as String? ?? '',
        subtopicId = j['subtopicId'] as String? ?? '',
        subtopicName = j['subtopicName'] as String? ?? '',
        chapterName = j['chapterName'] as String? ?? '',
        subjectName = j['subjectName'] as String? ?? '',
        teacherId = j['teacherId'] as String?,
        teacherName = j['teacherName'] as String?,
        scheduledDate = j['scheduledDate'] as String? ?? '',
        daysOverdue = j['daysOverdue'] as int? ?? 0;
}

class DelayedTopicsReport {
  final String academicYearId;
  final String asOfDate;
  final int delayedCount;
  final List<DelayedLesson> delayedLessons;

  DelayedTopicsReport.fromJson(Map<String, dynamic> j)
      : academicYearId = j['academicYearId'] as String? ?? '',
        asOfDate = j['asOfDate'] as String? ?? '',
        delayedCount = j['delayedCount'] as int? ?? 0,
        delayedLessons = ((j['delayedLessons'] as List?) ?? const [])
            .map((e) => DelayedLesson.fromJson(Map<String, dynamic>.from(e)))
            .toList();
}

class UnitSummary {
  final String id;
  final String canonicalId;
  final String bookId;
  final String unitNo;
  final String name;
  final int marks;
  final int seq;

  UnitSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        canonicalId = j['canonicalId'] as String? ?? '',
        bookId = j['bookId'] as String? ?? '',
        unitNo = j['unitNo'] as String? ?? '',
        name = j['name'] as String? ?? '',
        marks = j['marks'] as int? ?? 0,
        seq = j['seq'] as int? ?? 0;
}

class ChapterSummary {
  final String id;
  final String canonicalId;
  final String unitId;
  final String name;
  final int seq;

  ChapterSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        canonicalId = j['canonicalId'] as String? ?? '',
        unitId = j['unitId'] as String? ?? '',
        name = j['name'] as String? ?? '',
        seq = j['seq'] as int? ?? 0;
}

class CalendarInfo {
  final String id;
  final String academicYearId;
  final List<int> weeklyOffDays;
  final String alternateSaturdayRule;

  CalendarInfo.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        academicYearId = j['academicYearId'] as String,
        weeklyOffDays = (j['weeklyOffDays'] as List? ?? const []).map((e) => e as int).toList(),
        alternateSaturdayRule = j['alternateSaturdayRule'] as String? ?? 'none';
}

class HolidayInfo {
  final String id;
  final String calendarId;
  final String date;
  final String label;
  final String kind;
  final String? endDate;

  HolidayInfo.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        calendarId = j['calendarId'] as String,
        date = j['date'] as String,
        label = j['label'] as String,
        kind = j['kind'] as String? ?? 'public',
        endDate = j['endDate'] as String?;
}

class WorkingDaysSummary {
  final String academicYearId;
  final int totalDays;
  final int workingDays;
  final int weeklyOffCount;
  final int alternateSaturdayOffCount;
  final int holidayCount;
  final List<String> dates;

  WorkingDaysSummary.fromJson(Map<String, dynamic> j)
      : academicYearId = j['academicYearId'] as String,
        totalDays = j['totalDays'] as int? ?? 0,
        workingDays = j['workingDays'] as int? ?? 0,
        weeklyOffCount = j['weeklyOffCount'] as int? ?? 0,
        alternateSaturdayOffCount = j['alternateSaturdayOffCount'] as int? ?? 0,
        holidayCount = j['holidayCount'] as int? ?? 0,
        dates = (j['dates'] as List? ?? const []).map((e) => e.toString()).toList();
}

class ScheduledLessonSummary {
  final String id;
  final String academicYearId;
  final String bookId;
  final String subtopicId;
  final String scheduledDate;
  final int periodNumber;
  final String status;
  final String? note;
  final String? completedBy;
  final String? completedAt;

  ScheduledLessonSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        academicYearId = j['academicYearId'] as String? ?? '',
        bookId = j['bookId'] as String? ?? '',
        subtopicId = j['subtopicId'] as String? ?? '',
        scheduledDate = j['scheduledDate'] as String? ?? '',
        periodNumber = j['periodNumber'] as int? ?? 1,
        status = j['status'] as String? ?? 'scheduled',
        note = j['note'] as String?,
        completedBy = j['completedBy'] as String?,
        completedAt = j['completedAt'] as String?;
}
