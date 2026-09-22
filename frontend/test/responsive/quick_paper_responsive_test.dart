// Task 801: "Quick paper (CBSE pattern)" at phone, tablet and laptop widths.
// Online it is the guided builder opened on the class's CBSE annual pattern
// (Task 902), so a teacher with a remembered class is one tap from Generate.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/presentation/paper_builder/builder_memory.dart';

import 'builder_driver.dart';
import 'responsive_harness.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  useInMemoryHive();

  for (final MapEntry(key: name, value: size) in screenSizes.entries) {
    testWidgets('quick paper opens on the CBSE pattern with Generate on screen at $name', (tester) async {
      BuilderMemory(fixtureTeacherId).remember(grade: 10, subject: 'Science');
      final (api, _) = await pumpBuilder(tester, size, quick: true);

      expectNoOverflow(tester);
      expect(find.text('Quick paper (CBSE pattern)'), findsOneWidget);
      expect(find.textContaining('Class 10 Science - Annual Examination'), findsOneWidget);
      expect(builderPrimaryLabel(tester), 'Generate paper');
      expectActionReady(tester, builderPrimary(), size, label: 'Generate paper');
      expect(api.requests.where((r) => r.status >= 400), isEmpty, reason: '${api.requests}');
    });

    testWidgets('quick paper with no remembered class starts at class & subject and fits at $name',
        (tester) async {
      await pumpBuilder(tester, size, quick: true);
      expectNoOverflow(tester);
      expect(find.text('Which class is this paper for?'), findsOneWidget);
      expectActionReady(tester, builderPrimary(), size, label: 'Next: choose a template');
    });
  }
}
