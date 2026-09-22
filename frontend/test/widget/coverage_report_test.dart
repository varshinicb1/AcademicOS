// CoverageReport.fromJson on a payload the backend really returned.
//
// The 2026-09-21 product audit found the Coverage & Pace screen reading
// field names GET /curriculum/reporting/coverage never sends
// (coveragePercent, totalCount, completedCount, plannedCount, pacePercent;
// the backend sends coveragePct, totalLessons, completedLessons,
// plannedToDate, pacePct). Every figure parsed to its `?? 0` default, so every
// subject showed '0.0% covered' and '0/0 lessons', and the headline pace fell
// back to 100% for a school 89 lessons behind.
//
// test/fixtures/coverage_report.json is captured from the real route through
// TestClient by tests/test_curriculum_coverage_fixture.py, which also fails
// if the route's output drifts from it -- so these assertions track the live
// contract, not a hand-written guess at it.
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';

Map<String, dynamic> _fixture() =>
    jsonDecode(File('test/fixtures/coverage_report.json').readAsStringSync()) as Map<String, dynamic>;

void main() {
  group('CoverageReport.fromJson on the captured backend payload', () {
    late CoverageReport rep;
    setUp(() => rep = CoverageReport.fromJson(_fixture()));

    test('report-level figures are the backend values, not 0', () {
      expect(rep.schoolId, 'school_1');
      expect(rep.academicYearId, 'academicYear_1');
      expect(rep.asOfDate, '2026-09-14');
      expect(rep.totalLessons, 9);
      expect(rep.completedLessons, 2);
      expect(rep.skippedLessons, 1);
      expect(rep.plannedToDate, 6);
      expect(rep.completedToDate, 2);
      expect(rep.overallCoveragePct, 22.22);
      expect(rep.overallPacePct, 33.33);
      expect(rep.overallVariance, -4);
      expect(rep.overallPace, 33.33, reason: "the backend's own pace figure, not a client recomputation");
    });

    test('a subject behind schedule parses every figure, its grade and teacher', () {
      final maths = rep.subjects.firstWhere((s) => s.subjectName == 'Mathematics');
      expect(maths.subjectId, 'subject_1');
      expect(maths.gradeNumber, 7);
      expect(maths.bookId, 'book_1');
      expect(maths.bookTitle, 'Mathematics 7');
      expect(maths.teacherId, 'teacher_1');
      expect(maths.teacherName, 'Tara Teacher');
      expect(maths.totalLessons, 7);
      expect(maths.completedLessons, 2);
      expect(maths.skippedLessons, 1);
      expect(maths.plannedToDate, 6);
      expect(maths.completedToDate, 2);
      expect(maths.coveragePct, 28.57);
      expect(maths.pacePct, 33.33);
      expect(maths.variance, -4);
      expect(maths.pace, 33.33);
    });

    test('chapters parse their lesson counts and coverage', () {
      final maths = rep.subjects.firstWhere((s) => s.subjectName == 'Mathematics');
      expect(maths.chapters.map((c) => c.chapterName), ['Fractions', 'Integers']);
      final integers = maths.chapters[1];
      expect(integers.chapterId, 'chapter_2');
      expect(integers.totalLessons, 3);
      expect(integers.completedLessons, 2);
      expect(integers.skippedLessons, 0);
      expect(integers.coveragePct, 66.67);
    });

    test('a subject with an unassigned teacher parses null, not a crash', () {
      final science = rep.subjects.firstWhere((s) => s.subjectName == 'Science');
      expect(science.gradeNumber, 10);
      expect(science.teacherId, isNull);
      expect(science.teacherName, isNull);
    });
  });

  group('pace when nothing was planned to date', () {
    test('a subject with no lessons due yet has no pace, though the backend sends 100.0', () {
      final science = CoverageReport.fromJson(_fixture()).subjects.firstWhere((s) => s.subjectName == 'Science');
      expect(science.plannedToDate, 0);
      expect(science.pacePct, 100.0, reason: 'the raw backend value is kept as sent');
      expect(science.pace, isNull, reason: 'no lesson was due: 100% would be fabricated optimism');
    });

    test('a report with no lessons due yet has no overall pace', () {
      final json = _fixture()
        ..['plannedToDate'] = 0
        ..['completedToDate'] = 0
        ..['overallPacePct'] = 100.0;
      final rep = CoverageReport.fromJson(json);
      expect(rep.overallPace, isNull);
    });
  });
}
