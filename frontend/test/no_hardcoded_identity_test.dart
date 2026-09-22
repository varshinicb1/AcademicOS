// The web app works for whoever signed in, not for a demo school (Task 604).
//
// The 2026-09-22 re-audit of the live release found the web client hard-wired
// to `AppConstants.currentSchoolId = 'demo_school'` and a literal
// 'teacher_1': for a real school the assessment list, planner and scan list
// came back silently empty, the principal dashboard answered 403, and custom
// paper creation failed with 403 fetching another school's templates. The
// signed-in user's school and id (CurrentSession, from the login response)
// are the only identity a screen may use.
//
// This scans frontend/lib for an identity literal and for the removed
// constants. Whole-line comments are skipped (they may name the history). The
// allow-list is only the offline build's own device identity and the demo
// seeder: neither runs on the web (CurrentSession returns the offline identity
// only when the on-device engine is serving the data).
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Files allowed to spell an identity literal, and why.
const _allowed = {
  // The single device identity of the offline Android build (no server, no
  // login); CurrentSession uses it only when the on-device engine is wired.
  'lib/core/local_engine/offline_identity.dart',
  // Seeds the "(Demo)" department into the offline build's local store; its
  // personas carry their own ids ('demo_teacher_1', 'demo_stu_4').
  'lib/core/local_engine/demo_seeder.dart',
};

/// A quoted school/teacher/principal/student/user id such as 'school_1',
/// "teacher_1" or 'demo_school'.
final _idLiteral = RegExp(
    r'''['"](demo_school|(demo_)?(school|teacher|principal|student|user)_[0-9]+)['"]''');

/// The constants that carried a fixed identity before this task.
final _removedConstant = RegExp(r'\b(currentSchoolId|currentTeacherId)\b');

void main() {
  test('frontend/lib names no fixed school or user id outside the offline identity', () {
    final offences = <String>[];
    final files = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'))
        .where((f) => !f.path.endsWith('.g.dart') && !f.path.endsWith('.freezed.dart'));
    for (final file in files) {
      final rel = file.path.replaceAll('\\', '/');
      if (_allowed.contains(rel)) continue;
      final lines = file.readAsLinesSync();
      for (var i = 0; i < lines.length; i++) {
        final line = lines[i];
        if (line.trimLeft().startsWith('//')) continue;
        if (_idLiteral.hasMatch(line) || _removedConstant.hasMatch(line)) {
          offences.add('$rel:${i + 1}: ${line.trim()}');
        }
      }
    }
    expect(offences, isEmpty,
        reason: 'use CurrentSession.schoolId / CurrentSession.userId instead:\n'
            '${offences.join('\n')}');
  });

  test('the scan itself catches a hard-coded id (guards against a scan that matches nothing)', () {
    expect(_idLiteral.hasMatch("const schoolId = 'demo_school';"), isTrue);
    expect(_idLiteral.hasMatch("teacherId: 'teacher_1',"), isTrue);
    expect(_idLiteral.hasMatch('store.defaultFor("school_1")'), isTrue);
    expect(_removedConstant.hasMatch('AppConstants.currentSchoolId'), isTrue);
    expect(_idLiteral.hasMatch("'school_database'"), isFalse);
  });
}
