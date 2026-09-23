// The classes the builder offers must be the classes the release serves.
//
// The first release covers 6-10 (the user, 2026-09-23: "skip 11 and 12 for
// now"). The bank behind it holds nothing for class 11 and cannot build a
// Maths or Science paper for 12, so quick-generate answers 400 "Unable to find
// sufficient questions" -- a dead end a teacher reaches only after choosing a
// class, a subject and a template.
import 'package:academicos/presentation/paper_builder/paper_builder_controller.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('the builder offers classes 6-10 and no class it cannot serve', () {
    expect(builderGrades, [6, 7, 8, 9, 10]);
  });

  test('every offered class has subjects to offer', () {
    for (final grade in builderGrades) {
      expect(builderSubjects(grade), isNotEmpty, reason: 'class $grade');
    }
  });
}
