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
        bookId = j['bookId'] as String,
        bookTitle = j['bookTitle'] as String? ?? '',
        subjectName = j['subjectName'] as String? ?? '',
        chapterName = j['chapterName'] as String? ?? '',
        topicName = j['topicName'] as String? ?? '',
        subtopicId = j['subtopicId'] as String,
        subtopicName = j['subtopicName'] as String? ?? '';
}

class CurriculumApi {
  final Dio _dio;
  CurriculumApi(this._dio);

  /// `startDate`/`endDate` are ISO dates (yyyy-MM-dd), inclusive -- pass the
  /// same date for both to get one day's lessons.
  Future<List<MyScheduleEntry>> mySchedule({required String startDate, required String endDate}) async {
    final r = await _dio.get('/curriculum/my-schedule',
        queryParameters: {'start_date': startDate, 'end_date': endDate});
    return (r.data as List).map((e) => MyScheduleEntry.fromJson(Map<String, dynamic>.from(e))).toList();
  }
}
