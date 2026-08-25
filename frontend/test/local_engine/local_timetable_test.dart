// Proves the Planner's "AI-suggested weekly timetable" is real offline:
// syllabus()/timetable() only ever existed on the base PillarApi as real
// HTTP calls before this -- LocalPillarApi never overrode them, so this
// live, reachable feature (daily_planner_page.dart's _TimetableSheet) made
// a network call with no server to answer it in the offline build.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/local_engine/corpus_repository.dart';
import 'package:academicos/core/local_engine/local_pillar_api.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tmpDir;
  late Box cacheBox;

  setUpAll(() async {
    tmpDir = Directory.systemTemp.createTempSync('timetable_test_');
    Hive.init(tmpDir.path);
    cacheBox = await Hive.openBox('academicos_cache');
    await CorpusRepository.instance.ensureLoaded();
  });

  tearDownAll(() async {
    await cacheBox.close();
    tmpDir.deleteSync(recursive: true);
  });

  test('syllabus() builds real units from real corpus chapters, honestly labeled', () async {
    final api = LocalPillarApi();
    final syllabus = await api.syllabus('Science', 10);

    expect(syllabus.units, isNotEmpty);
    expect(syllabus.totalMarks, greaterThan(0));
    // Real, not fabricated as official CBSE weightage -- must say so.
    expect(syllabus.source, contains('not official CBSE unit weightage'));
  });

  test('timetable() allocates periods proportionally and conserves the full period budget', () async {
    final api = LocalPillarApi();
    const periodsPerWeek = 6, weeks = 20;
    final tt = await api.timetable('Science', 10, periodsPerWeek: periodsPerWeek, weeks: weeks);

    expect(tt.allocations, isNotEmpty);
    final totalAllocated = tt.allocations.fold<int>(0, (s, a) => s + a.suggestedPeriods);
    expect(totalAllocated, periodsPerWeek * weeks,
        reason: 'every period in the real budget must be accounted for, none invented or dropped');

    // Proportionality is real: the highest-marks unit must get at least as
    // many periods as the lowest-marks unit.
    final byMarks = [...tt.allocations]..sort((a, b) => a.marks.compareTo(b.marks));
    expect(byMarks.first.suggestedPeriods, lessThanOrEqualTo(byMarks.last.suggestedPeriods));

    expect(tt.schedule, isNotEmpty);
    for (final slot in tt.schedule) {
      expect(slot.week, inInclusiveRange(1, weeks));
    }
  });

  test('a subject with no corpus data fails honestly instead of a raw network error', () async {
    final api = LocalPillarApi();
    expect(
      () => api.syllabus('A Subject That Does Not Exist', 10),
      throwsA(isA<OfflineUnsupportedException>()),
    );
  });
}
