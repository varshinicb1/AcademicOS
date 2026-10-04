// What adding a day off did to the lesson plans, in the message the principal
// reads: lessons pushed past the year's end are said, not dropped without a word.
import 'package:academicos/data/datasources/api/curriculum_api.dart';
import 'package:flutter_test/flutter_test.dart';

HolidayInfo _h({int? moved, int? dropped}) => HolidayInfo.fromJson({
      'id': 'h1', 'calendarId': 'c1', 'date': '2027-03-01', 'label': 'Holi', 'kind': 'public',
      'lessonsMoved': moved, 'lessonsDropped': dropped,
    });

void main() {
  test('nothing moved says nothing', () {
    expect(_h().planChange, '');
    expect(_h(moved: 0, dropped: 0).planChange, '');
  });

  test('moved lessons are counted', () {
    expect(_h(moved: 1).planChange, '1 lesson moved to fit it.');
    expect(_h(moved: 5).planChange, '5 lessons moved to fit it.');
  });

  test('lessons past the year end are said, with what to do', () {
    final s = _h(moved: 4, dropped: 2).planChange;
    expect(s, startsWith('4 lessons moved to fit it. 2 lessons no longer fit before the year ends'));
    expect(s, contains('add a period for the subject, or remove a day off'));
    expect(_h(dropped: 1).planChange, startsWith('1 lesson no longer fits before the year ends, so its topic has'));
  });
}
