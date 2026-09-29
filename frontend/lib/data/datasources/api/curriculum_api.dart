/// Client for the curriculum/schedule endpoints
/// (src/academicos/curriculum/routes.py) -- mainly the teacher-facing
/// slice: "what do I teach today" (`GET /my-schedule`), plus a read-only
/// Topic/Subtopic lookup the Assessment Designer's subtopic picker uses
/// (topicsForSyllabusChapter). Not the full admin curriculum-authoring surface
/// (extraction/approval/calendar), which has no Flutter UI yet. Same
/// plain-class, no-freezed style as auth_api.dart/pillar_api.dart --
/// read-mostly data, no codegen needed.
library;

import 'package:dio/dio.dart';

// The Reschedule and Calendar tabs import serverErrorMessage from here; it now
// lives in api_error.dart, the one error path every screen shares (Task 802).
export 'api_error.dart';

/// The two answers `_require_student_enrollment` (curriculum/routes.py) gives
/// `my-progress` and `my-class-schedule` for an account that is not an
/// enrolled student, verbatim. test/widget/no_silent_failures_stored_test.dart
/// fails if routes.py stops sending either one.
const notAStudentDetail = 'this endpoint is for students only';
const notEnrolledDetail = 'you are not enrolled in a class yet -- ask your principal to enroll you';

/// The status alone is not enough to read either answer. FastAPI answers 404
/// "Not Found" for a path it does not serve (a web build ahead of its
/// backend, a wrong proxy prefix) and the route-policy layer answers its own
/// 403s; read as "not linked" or "not enrolled", either showed an
/// honest-looking empty screen over a failure, the pattern Task 802 removed.
/// So these match the status AND the sentence.
bool _answered(Object e, int status, String detail) {
  if (e is! DioException) return false;
  final data = e.response?.data;
  return e.response?.statusCode == status && data is Map && data['detail'] == detail;
}

/// The server's 403: the signed-in account is not a student at all (for the
/// parent portal, a parent account not yet linked to a child).
bool isNotAStudentAnswer(Object e) => _answered(e, 403, notAStudentDetail);

/// The server's 404: a student account with no class enrollment yet.
bool isNotEnrolledAnswer(Object e) => _answered(e, 404, notEnrolledDetail);

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

/// A term the school declared for an academic year.
class TermInfo {
  final String id;
  final String name;
  final String startDate;
  final String endDate;

  TermInfo.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        name = j['name'] as String? ?? '',
        startDate = j['startDate'] as String,
        endDate = j['endDate'] as String;
}

/// One class of a grade in a year ("10-B"): what a student is enrolled in
/// (M1.1). Every grade has at least one; a school with one class per grade
/// has "10-A".
class SectionSummary {
  final String id;
  final String academicYearId;
  final String gradeId;
  final int gradeNumber;
  final String name;
  final String? classTeacherId;
  final int studentCount;

  SectionSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        academicYearId = j['academicYearId'] as String,
        gradeId = j['gradeId'] as String,
        gradeNumber = j['gradeNumber'] as int,
        name = j['name'] as String,
        classTeacherId = j['classTeacherId'] as String?,
        studentCount = j['studentCount'] as int? ?? 0;

  /// "10-B".
  String get label => '$gradeNumber-$name';
}

/// What setting up one CBSE class created.
class SeedSummary {
  final String academicYearId;
  final String gradeId;
  final int grade;
  final int subjectsSeeded;
  final int chaptersSeeded;
  final List<String> subjectsSkipped;

  SeedSummary.fromJson(Map<String, dynamic> j)
      : academicYearId = j['academicYearId'] as String,
        gradeId = j['gradeId'] as String,
        grade = j['grade'] as int,
        subjectsSeeded = j['subjectsSeeded'] as int? ?? 0,
        chaptersSeeded = j['chaptersSeeded'] as int? ?? 0,
        subjectsSkipped = List<String>.from(j['subjectsSkipped'] as List? ?? const []);
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

/// A book (edition) of a subject. `selected` is whether it is the subject's
/// edition for the year (PRD 12.7: one per subject per year, chosen by the
/// school) -- the book every screen must use, never `books.first`.
class BookSummary {
  final String id;
  final String subjectId;
  final String boardId;
  final String title;
  final String? publisher;
  final bool selected;
  BookSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        subjectId = j['subjectId'] as String,
        boardId = j['boardId'] as String? ?? '',
        title = j['title'] as String,
        publisher = j['publisher'] as String?,
        selected = j['selected'] as bool? ?? false;

  String get label => publisher == null || publisher!.isEmpty ? title : '$title ($publisher)';
}

class BoardSummary {
  final String id;
  final String name;
  BoardSummary.fromJson(Map<String, dynamic> j) : id = j['id'] as String, name = j['name'] as String;
}

/// SelectBookResponse (schemas.py). `warning` is set when any other edition
/// of the subject -- not only the one chosen just before -- still has lessons
/// scheduled this year or teachers assigned to it. Neither is moved to the
/// new book, so the warning is what the principal is told; it already names
/// each old book and its counts.
class BookSelectionResult {
  final BookSummary book;
  final String? previousBookId;
  final int previousBookScheduledLessons;
  final String? warning;
  BookSelectionResult.fromJson(Map<String, dynamic> j)
      : book = BookSummary.fromJson(Map<String, dynamic>.from(j['book'] as Map)),
        previousBookId = j['previousBookId'] as String?,
        previousBookScheduledLessons = j['previousBookScheduledLessons'] as int? ?? 0,
        warning = j['warning'] as String?;
}

/// The school has no curriculum to filter by yet, and the server said what
/// to do about it. Carried as its own type (not a bare DioException) because
/// the picker must show [message] verbatim: "no subtopics exist for this
/// chapter" and "your school has not set this class up" are different facts
/// with different actions, and an empty list says neither.
class CurriculumNotSetUp implements Exception {
  final String message;
  CurriculumNotSetUp(this.message);
  @override
  String toString() => message;
}

/// One real, admin-approved Subtopic under a Topic -- the finest-grained
/// unit a question can be tagged against (qmap.py::map_subtopics).
class SubtopicSummary {
  final String id;
  final String name;

  /// How many questions the school has actually tagged to this subtopic.
  ///
  /// `POST /questions/search` intersects the chapter's questions with
  /// `question_subtopic_links`, so 0 here means picking this subtopic
  /// produces an EMPTY paper, not a narrowed one. No client writes that
  /// table yet (its only writer is `POST /chapters/{id}/questions/tag`), so
  /// on real school data this is 0 everywhere -- which is exactly why the
  /// picker has to show it instead of letting a teacher find out at
  /// generation time. Null from an older backend that does not send it.
  final int? taggedQuestionCount;

  SubtopicSummary.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        name = j['name'] as String,
        taggedQuestionCount = (j['taggedQuestionCount'] as num?)?.toInt();
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

/// One still-unapproved Topic proposal, with its proposed Subtopics nested.
/// `description` carries the source's own reference where there is one (an
/// NCERT section number, "NCERT section 2.2.1") -- the thing a principal
/// actually checks the proposal against.
class ProposedTopic {
  final String id;
  final String name;
  final String? description;
  final List<ProposedTopic> subtopics;

  ProposedTopic({required this.id, required this.name, this.description,
      this.subtopics = const []});
}

/// A chapter's pending decomposition proposals, from one extraction run.
///
/// Seeding a grade applies the committed decomposition template (school_1's
/// approved Class 10 work, or the NCERT textbooks' own numbered headings) as
/// PENDING proposals -- never as this school's approved curriculum. This is
/// what the principal reviews before it becomes real; `provenance` is the
/// run's promptVersion, e.g. `template:ncert-textbook-headings`.
class ChapterTopicProposals {
  final String runId;
  final String status;
  final String provenance;
  final List<ProposedTopic> topics;

  ChapterTopicProposals({required this.runId, required this.status,
      required this.provenance, required this.topics});

  bool get isTemplate => provenance.startsWith('template:');

  /// "approved for Class 10 by another school" / "the textbook's own section
  /// headings" -- plain words, because `template:school_1-approved` means
  /// nothing to a principal.
  String get sourceLabel {
    switch (provenance) {
      case 'template:school_1-approved':
        return 'a CBSE school\'s approved Class 10 decomposition';
      case 'template:ncert-textbook-headings':
        return 'the NCERT textbook\'s own numbered section headings';
      default:
        return provenance.startsWith('template:') ? provenance : 'an AI draft';
    }
  }

  /// The wire shape is a flat proposal list where a subtopic points at its
  /// parent topic proposal (`proposedParent`), because neither exists as a
  /// real row yet and so neither has a real id to nest under.
  factory ChapterTopicProposals.fromJson(Map<String, dynamic> j) {
    final run = Map<String, dynamic>.from(j['run'] as Map);
    final rows = (j['proposals'] as List? ?? const [])
        .map((e) => Map<String, dynamic>.from(e))
        .toList();
    final children = <String, List<ProposedTopic>>{};
    for (final p in rows.where((p) => p['entityType'] == 'subtopic')) {
      children.putIfAbsent(p['proposedParent'] as String? ?? '', () => []).add(ProposedTopic(
            id: p['id'] as String,
            name: (p['editedName'] ?? p['proposedName']) as String,
            description: p['proposedDescription'] as String?,
          ));
    }
    return ChapterTopicProposals(
      runId: run['id'] as String,
      status: run['status'] as String,
      provenance: run['promptVersion'] as String,
      topics: rows.where((p) => p['entityType'] == 'topic').map((p) {
        final id = p['id'] as String;
        return ProposedTopic(
          id: id,
          name: (p['editedName'] ?? p['proposedName']) as String,
          description: p['proposedDescription'] as String?,
          subtopics: children[id] ?? const [],
        );
      }).toList(),
    );
  }
}

/// What "Approve all for this chapter" actually created.
class ApproveChapterTopicsResult {
  final int runsApproved;
  final int topicsCreated;
  final int subtopicsCreated;

  ApproveChapterTopicsResult.fromJson(Map<String, dynamic> j)
      : runsApproved = j['runsApproved'] as int,
        topicsCreated = j['topicsCreated'] as int,
        subtopicsCreated = j['subtopicsCreated'] as int;

  String get summary => topicsCreated == 0
      ? 'Nothing left to approve for this chapter.'
      : 'Approved $topicsCreated topics and $subtopicsCreated subtopics.';
}

/// PushScheduleResponse (schemas.py). The count field is `lessonsPushed`:
/// the Reschedule tab used to read a nonexistent `pushedCount` and would
/// have reported "0 lessons shifted" on every success. `lessonsDropped`
/// are lessons that no longer fit before the academic year's last teaching
/// day -- the server reports them rather than placing them past the end.
class PushScheduleResult {
  final int lessonsPushed;
  final List<String> lessonsDropped;
  final int periodsPerWeek;

  PushScheduleResult.fromJson(Map<String, dynamic> j)
      : lessonsPushed = j['lessonsPushed'] as int,
        lessonsDropped = (j['lessonsDropped'] as List? ?? const []).cast<String>().toList(),
        periodsPerWeek = j['periodsPerWeek'] as int;

  String get summary {
    String lessons(int n) => n == 1 ? '1 lesson' : '$n lessons';
    final pushed = 'Schedule pushed: ${lessons(lessonsPushed)} shifted.';
    if (lessonsDropped.isEmpty) return pushed;
    return '$pushed ${lessons(lessonsDropped.length)} no longer fit before the year ends.';
  }
}

class CurriculumApi {
  final Dio _dio;
  CurriculumApi(this._dio);

  /// Used by the student view to find its own school's current academic
  /// year rather than guessing or hardcoding one. Signed-in only, like every
  /// curriculum read here (the bearer token rides on the shared Dio's
  /// sessionInterceptor): `schoolId` must be the caller's own school -- the
  /// server answers 403 for any other, never that school's years.
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

  /// The subject's chosen edition, or null when it has no book, or several
  /// and none chosen (the server's 404). Callers scheduling, assigning or
  /// reordering use this -- `books(...).first` was SQLite row order.
  Future<BookSummary?> selectedBook(String subjectId) async {
    try {
      final r = await _dio.get('/curriculum/subjects/$subjectId/selected-book');
      return BookSummary.fromJson(Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  /// Principal-only. Adding a book is not choosing it.
  Future<BookSummary> addBook(String subjectId,
      {required String title, String? publisher, required String boardId}) async {
    final r = await _dio.post('/curriculum/subjects/$subjectId/books',
        data: {'title': title, 'publisher': publisher, 'boardId': boardId});
    return BookSummary.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Principal-only: makes [bookId] the subject's edition for its year.
  Future<BookSelectionResult> selectBook(String subjectId, String bookId) async {
    final r = await _dio.put('/curriculum/subjects/$subjectId/selected-book', data: {'bookId': bookId});
    return BookSelectionResult.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<List<BoardSummary>> boards() async {
    final r = await _dio.get('/curriculum/boards');
    return (r.data as List).map((e) => BoardSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// §15's missing link: which teacher teaches which real book.
  /// Principal-gated server-side.
  Future<void> assignTeacher({required String teacherId, required String bookId}) async {
    await _dio.post('/curriculum/teacher-assignments', data: {'teacherId': teacherId, 'bookId': bookId});
  }

  /// §18's missing link: which real class a student belongs to.
  /// Principal-gated server-side.
  /// Principal-only. Enrolls the student in one section (M1.1); enrolling
  /// again moves them.
  Future<void> enrollStudent({required String studentId, required String sectionId}) async {
    await _dio.post('/curriculum/student-enrollments', data: {'studentId': studentId, 'sectionId': sectionId});
  }

  /// Principal-only: the school's name as papers print it (EX-5, audit D41).
  /// Keeps the address, affiliation line and logo already set.
  Future<void> setSchoolName(String name) async {
    final current = await _dio.get('/curriculum/school-profile');
    final p = Map<String, dynamic>.from(current.data as Map);
    await _dio.put('/curriculum/school-profile',
        data: {'name': name, 'address': p['address'], 'affiliation': p['affiliation']});
  }

  /// Every section of the year in class order, with its student count.
  /// Staff only.
  Future<List<SectionSummary>> sections(String academicYearId) async {
    final r = await _dio.get('/curriculum/academic-years/$academicYearId/sections');
    return (r.data as List).map((e) => SectionSummary.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// Principal-only. A name the class already has, in any case, is a 422
  /// whose detail says so.
  Future<SectionSummary> createSection(String gradeId, {required String name, String? classTeacherId}) async {
    final r = await _dio.post('/curriculum/grades/$gradeId/sections',
        data: {'name': name, if (classTeacherId != null) 'classTeacherId': classTeacherId});
    return SectionSummary.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Principal-only. Renames the section; with [changeClassTeacher] also sets
  /// its class teacher to [classTeacherId] (null clears it). Without it the
  /// class teacher is not sent, so the server leaves it as it is: a class
  /// teacher this screen does not list (the principal) survives a rename.
  Future<SectionSummary> updateSection(String sectionId,
      {required String name, bool changeClassTeacher = false, String? classTeacherId}) async {
    final r = await _dio.patch('/curriculum/sections/$sectionId',
        data: {'name': name, if (changeClassTeacher) 'classTeacherId': classTeacherId});
    return SectionSummary.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Principal-only. A 409 while students are enrolled in it, or when it is
  /// its class's last section.
  Future<void> deleteSection(String sectionId) async {
    await _dio.delete('/curriculum/sections/$sectionId');
  }

  /// Principal-only: the ids of the students enrolled in this section.
  Future<List<String>> sectionStudentIds(String sectionId) async {
    final r = await _dio.get('/curriculum/sections/$sectionId/students');
    return [for (final e in r.data as List) (e as Map)['studentId'] as String];
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

  // `GET /curriculum/chapters/{chap_id}/topics` (the id-keyed sibling of the
  // by-slug route below) had a wrapper here until 2026-09-23. Nothing in this
  // app can call it: every screen that knows about a chapter knows it by its
  // syllabus slug, not by the school's own `chap_` id, which is why the
  // subtopic picker was broken in the first place. The route still exists and
  // is tested on the backend; an untested Dart wrapper with no callers is not
  // worth keeping alive for a caller that may never appear.

  /// Real Topics + nested Subtopics, found from the SYLLABUS chapter slug the
  /// Assessment Designer actually holds -- what feeds its subtopic picker
  /// (assessment_create_page.dart), so a teacher can narrow question search
  /// to specific subtopics via `QuestionSearchParams.subtopicIds` instead of
  /// a whole chapter.
  ///
  /// The picker's chapter ids come from `GET /catalog/{subject}/{grade}/
  /// chapters` and are syllabus slugs (`chemical-reactions-equations`).
  /// Until 2026-09-23 they were passed to `/chapters/{chap_id}/topics`, which
  /// wants a `chap_` id: that answered `200 []` and later 404, the page swallowed it,
  /// and the picker had never once found a subtopic. The server resolves the
  /// slug against the caller's own school and its chosen book edition.
  ///
  /// A school that has not set this class/subject up is a 404 carrying the
  /// server's own instruction, surfaced as [CurriculumNotSetUp] -- the
  /// picker shows that sentence instead of looking empty.
  Future<List<TopicWithSubtopics>> topicsForSyllabusChapter({
    required String subject,
    required int grade,
    required String chapterSlug,
  }) async {
    final path = '/curriculum/chapters/by-slug/${Uri.encodeComponent(subject)}'
        '/$grade/${Uri.encodeComponent(chapterSlug)}/topics';
    try {
      final r = await _dio.get(path);
      return (r.data as List)
          .map((e) => TopicWithSubtopics.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        final data = e.response?.data;
        final detail = data is Map ? data['detail'] : null;
        // The route always sends a detail, and it is role-aware (a teacher
        // is told to ask her principal, a principal is told which screen to
        // open). This fallback is for a 404 with no body at all, so it says
        // only what is certainly true rather than naming a screen the
        // reader may not be allowed to act on -- or, as it once did, a
        // "Curriculum" destination that does not exist in the app.
        throw CurriculumNotSetUp(detail is String && detail.isNotEmpty
            ? detail
            : 'Class $grade $subject is not set up for subtopic filtering yet');
      }
      rethrow;
    }
  }

  /// A chapter's still-unapproved decomposition proposals -- what the seed
  /// proposed from the committed template and nobody has accepted yet. Empty
  /// once they are approved (they become real topics) and for a chapter whose
  /// subject/grade no template covers.
  Future<List<ChapterTopicProposals>> proposedTopics(String chapterId) async {
    final r = await _dio.get('/curriculum/chapters/$chapterId/proposed-topics');
    return (r.data as List)
        .map((e) => ChapterTopicProposals.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  /// Principal-only: accepts every pending TEMPLATE proposal for one chapter at
  /// once. A fresh Class 10 seed proposes topics for 46 chapters; approving
  /// those proposal by proposal is what stops a school finishing setup at all.
  /// Safe to repeat -- a run already approved is not approved twice.
  Future<ApproveChapterTopicsResult> approveAllTopics(String chapterId) async {
    final r = await _dio.post('/curriculum/chapters/$chapterId/topics/approve-all');
    return ApproveChapterTopicsResult.fromJson(Map<String, dynamic>.from(r.data));
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

  /// §14 ADJUST: move one lesson to `newDate` (yyyy-MM-dd), a real working
  /// day. Field names match AdjustLessonRequest in schemas.py -- until
  /// 2026-09-21 this sent `targetDate` and every call 422'd. The server
  /// answers 409 when that day already holds this book's lesson(s) for
  /// every period the subject has then.
  Future<void> rescheduleLesson(String lessonId, {required String newDate, required String reason}) async {
    await _dio.post('/curriculum/scheduled-lessons/$lessonId/reschedule', data: {
      'newDate': newDate,
      'reason': reason,
    });
  }

  /// §14 PUSH: shift every still-to-teach lesson on/after `fromDate` one
  /// teaching slot later (completed/skipped lessons keep their dates).
  /// `academic_year_id` is a query parameter on the route, not a body
  /// field; `periodsPerWeek` is sent only when the admin set one -- the
  /// server otherwise uses the subject's stored period allocation.
  Future<PushScheduleResult> pushSchedule({
    required String bookId,
    required String academicYearId,
    required String fromDate,
    required String reason,
    int? periodsPerWeek,
  }) async {
    final r = await _dio.post('/curriculum/books/$bookId/schedule/push',
        queryParameters: {'academic_year_id': academicYearId},
        data: {
          'fromDate': fromDate,
          'reason': reason,
          if (periodsPerWeek != null) 'periodsPerWeek': periodsPerWeek,
        });
    return PushScheduleResult.fromJson(Map<String, dynamic>.from(r.data));
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
  ///
  /// `weeklyOffDays` are full weekday names ('sunday') -- the backend's
  /// CreateCalendarRequest is `list[str]`. This sent `[7]` until 2026-09-22,
  /// so every create from the Calendar & Setup tab was a 422.
  /// `alternateSaturdayRule`: 'none' | 'all' | 'second_fourth' |
  /// 'first_third' | ordinals like '2nd,4th'; anything else is a 422.
  Future<CalendarInfo> createCalendar(String academicYearId,
      {List<String> weeklyOffDays = const ['sunday'], String alternateSaturdayRule = 'none'}) async {
    final r = await _dio.post('/curriculum/academic-years/$academicYearId/calendar', data: {
      'weeklyOffDays': weeklyOffDays,
      'alternateSaturdayRule': alternateSaturdayRule,
    });
    return CalendarInfo.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Corrects an existing calendar (a second create is a 409). Same body
  /// and validation as [createCalendar].
  Future<CalendarInfo> updateCalendar(String academicYearId,
      {required List<String> weeklyOffDays, required String alternateSaturdayRule}) async {
    final r = await _dio.put('/curriculum/academic-years/$academicYearId/calendar', data: {
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

  /// `kind`: 'public' | 'school' | 'emergency' | 'holiday' |
  /// 'unexpected_closure' remove teaching days; 'event' marks a day that
  /// still teaches. A date outside the academic year is a 422.
  Future<HolidayInfo> addHoliday(String academicYearId, {required String date, required String label, String kind = 'public', String? endDate}) async {
    final r = await _dio.post('/curriculum/academic-years/$academicYearId/holidays', data: {
      'date': date,
      'label': label,
      'kind': kind,
      if (endDate != null) 'endDate': endDate,
    });
    return HolidayInfo.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Removes a holiday entered by mistake, so that day teaches again.
  Future<void> deleteHoliday(String academicYearId, String holidayId) async {
    await _dio.delete('/curriculum/academic-years/$academicYearId/holidays/$holidayId');
  }

  Future<List<HolidayInfo>> listHolidays(String academicYearId) async {
    final r = await _dio.get('/curriculum/academic-years/$academicYearId/holidays');
    return (r.data as List).map((e) => HolidayInfo.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// The school's terms for the year, in date order. Exam coverage and time
  /// saved are measured per term (PRD decision 11); until the web could
  /// declare one, a school set up the documented way had none (audit D27).
  Future<List<TermInfo>> terms(String academicYearId) async {
    final r = await _dio.get('/curriculum/academic-years/$academicYearId/terms');
    return (r.data as List).map((e) => TermInfo.fromJson(Map<String, dynamic>.from(e))).toList();
  }

  /// Principal-only. A term outside the year, overlapping another by even
  /// one day, or sharing another's name is a 422 whose detail says which.
  Future<TermInfo> createTerm(String academicYearId,
      {required String name, required String startDate, required String endDate}) async {
    final r = await _dio.post('/curriculum/academic-years/$academicYearId/terms',
        data: {'name': name, 'startDate': startDate, 'endDate': endDate});
    return TermInfo.fromJson(Map<String, dynamic>.from(r.data));
  }

  /// Principal-only; replaces name and dates, keeps the term's baseline.
  Future<TermInfo> updateTerm(String termId,
      {required String name, required String startDate, required String endDate}) async {
    final r = await _dio.put('/curriculum/terms/$termId',
        data: {'name': name, 'startDate': startDate, 'endDate': endDate});
    return TermInfo.fromJson(Map<String, dynamic>.from(r.data));
  }

  Future<void> deleteTerm(String termId) async {
    await _dio.delete('/curriculum/terms/$termId');
  }

  /// Principal-only: sets up one CBSE class (6-12) as this school's year,
  /// its subjects, books, units and chapters. Idempotent: running it again
  /// for the same year reuses what is there.
  Future<SeedSummary> seedCbseClass(
      {required int grade, required String yearLabel, required String startDate, required String endDate}) async {
    final r = await _dio.post('/curriculum/seed/cbse', data: {
      'grade': grade,
      'academicYearLabel': yearLabel,
      'startDate': startDate,
      'endDate': endDate,
    });
    return SeedSummary.fromJson(Map<String, dynamic>.from(r.data));
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

// Coverage & Pace (§17, §32): mirrors CoverageReportResponse and its nested
// Subject/ChapterCoverageResponse in src/academicos/curriculum/schemas.py
// field for field. These used to read coveragePercent / totalCount /
// completedCount / plannedCount / pacePercent -- names the backend never
// sends -- so every figure fell to its `?? 0` default and the screen showed
// 0% everywhere (audit 2026-09-21). test/fixtures/coverage_report.json is a
// captured real payload, drift-checked by tests/test_curriculum_coverage_fixture.py.

/// The backend's pace figure, or null when nothing was planned to date. The
/// backend reports 100.0 for that case; shown as-is it tells a principal a
/// subject nobody has started is on track.
double? _paceOrNull(int plannedToDate, double pacePct) => plannedToDate > 0 ? pacePct : null;

class ChapterCoverage {
  final String chapterId;
  final String chapterName;
  final int totalLessons;
  final int completedLessons;
  final int skippedLessons;
  final double coveragePct;

  ChapterCoverage.fromJson(Map<String, dynamic> j)
      : chapterId = j['chapterId'] as String? ?? '',
        chapterName = j['chapterName'] as String? ?? '',
        totalLessons = j['totalLessons'] as int? ?? 0,
        completedLessons = j['completedLessons'] as int? ?? 0,
        skippedLessons = j['skippedLessons'] as int? ?? 0,
        coveragePct = (j['coveragePct'] as num?)?.toDouble() ?? 0.0;
}

class SubjectCoverage {
  final String subjectId;
  final String subjectName;
  final int gradeNumber;
  final String bookId;
  final String bookTitle;
  final String? teacherId;
  final String? teacherName;
  final int totalLessons;
  final int completedLessons;
  final int skippedLessons;
  final int plannedToDate;
  final int completedToDate;
  final double coveragePct;
  final double pacePct;
  final int variance;
  final List<ChapterCoverage> chapters;

  SubjectCoverage.fromJson(Map<String, dynamic> j)
      : subjectId = j['subjectId'] as String? ?? '',
        subjectName = j['subjectName'] as String? ?? '',
        gradeNumber = j['gradeNumber'] as int? ?? 0,
        bookId = j['bookId'] as String? ?? '',
        bookTitle = j['bookTitle'] as String? ?? '',
        teacherId = j['teacherId'] as String?,
        teacherName = j['teacherName'] as String?,
        totalLessons = j['totalLessons'] as int? ?? 0,
        completedLessons = j['completedLessons'] as int? ?? 0,
        skippedLessons = j['skippedLessons'] as int? ?? 0,
        plannedToDate = j['plannedToDate'] as int? ?? 0,
        completedToDate = j['completedToDate'] as int? ?? 0,
        coveragePct = (j['coveragePct'] as num?)?.toDouble() ?? 0.0,
        pacePct = (j['pacePct'] as num?)?.toDouble() ?? 0.0,
        variance = j['variance'] as int? ?? 0,
        chapters = ((j['chapters'] as List?) ?? const [])
            .map((e) => ChapterCoverage.fromJson(Map<String, dynamic>.from(e)))
            .toList();

  /// [pacePct] when any lesson was due by the as-of date, else null.
  double? get pace => _paceOrNull(plannedToDate, pacePct);
}

class CoverageReport {
  final String schoolId;
  final String academicYearId;
  final String asOfDate;
  final int totalLessons;
  final int completedLessons;
  final int skippedLessons;
  final int plannedToDate;
  final int completedToDate;
  final double overallCoveragePct;
  final double overallPacePct;
  final int overallVariance;
  final List<SubjectCoverage> subjects;

  CoverageReport.fromJson(Map<String, dynamic> j)
      : schoolId = j['schoolId'] as String? ?? '',
        academicYearId = j['academicYearId'] as String? ?? '',
        asOfDate = j['asOfDate'] as String? ?? '',
        totalLessons = j['totalLessons'] as int? ?? 0,
        completedLessons = j['completedLessons'] as int? ?? 0,
        skippedLessons = j['skippedLessons'] as int? ?? 0,
        plannedToDate = j['plannedToDate'] as int? ?? 0,
        completedToDate = j['completedToDate'] as int? ?? 0,
        overallCoveragePct = (j['overallCoveragePct'] as num?)?.toDouble() ?? 0.0,
        overallPacePct = (j['overallPacePct'] as num?)?.toDouble() ?? 0.0,
        overallVariance = j['overallVariance'] as int? ?? 0,
        subjects = ((j['subjects'] as List?) ?? const [])
            .map((e) => SubjectCoverage.fromJson(Map<String, dynamic>.from(e)))
            .toList();

  /// [overallPacePct] when any lesson was due by the as-of date, else null.
  double? get overallPace => _paceOrNull(plannedToDate, overallPacePct);
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
  /// Lower-case weekday names, as the backend stores them ('sunday').
  final List<String> weeklyOffDays;
  final String alternateSaturdayRule;

  CalendarInfo.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        academicYearId = j['academicYearId'] as String,
        weeklyOffDays = (j['weeklyOffDays'] as List? ?? const []).map((e) => e as String).toList(),
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
