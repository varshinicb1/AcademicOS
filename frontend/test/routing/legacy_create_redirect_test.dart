// Task 125, step 11: on the web build the legacy "create assessment" screen
// sends the teacher to the guided builder.
//
// That screen (assessment_create_page.dart) carries the web's only
// Foundation/Standard/Advanced control, and the bank judges no difficulty in
// any class 6-10 cell (tiersAvailable false in 14 of 14), so it offered three
// versions that print the same paper. The builder says why no version is
// offered instead. The offline build keeps the screen (it has no builder).
import 'package:academicos/core/routing/app_router.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('the web build sends /assessment/create to the builder', () {
    expect(legacyCreateRedirect(offlineBuild: false), '/assessment/build');
  });

  test('the offline build keeps the create screen', () {
    expect(legacyCreateRedirect(offlineBuild: true), isNull);
  });
}
