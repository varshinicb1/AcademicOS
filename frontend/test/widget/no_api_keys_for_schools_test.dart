// Question-bank API keys and their webhooks are the operator's (ours), not a school's. No
// role's navigation offers them.
import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('no role sees API keys in its navigation', () {
    for (final role in ['principal', 'teacher', 'student', 'parent', '']) {
      final labels = [for (final i in navItemsFor(role)) i.label.toLowerCase()];
      expect(labels.where((l) => l.contains('api')), isEmpty, reason: role);
    }
    final granted = [for (final i in navItemsFor('teacher', grants: {'users', 'leave', 'exams', 'qbank_review'})) i.label.toLowerCase()];
    expect(granted.where((l) => l.contains('api')), isEmpty, reason: 'even a teacher with admin grants');
  });
}
