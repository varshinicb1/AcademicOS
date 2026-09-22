import 'dart:convert';
import 'dart:io';

import 'package:academicos/domain/entities/question.dart';
import 'package:flutter_test/flutter_test.dart';

// The bundled corpus is the served bank written by merge_question_banks.py
// (board + CBE + SQP + Exemplar). Question.fromJson is strict -- a missing
// required field throws -- so one malformed merged row would otherwise only
// surface on a device. 3,286 is the board-only bank before the merge: a
// count at or below it means the merged bank never reached the asset.
void main() {
  test('every row of the bundled corpus decodes with Question.fromJson', () {
    final raw = File('assets/corpus/questions.json').readAsStringSync();
    final rows = (jsonDecode(raw) as Map<String, dynamic>)['questions'] as List;
    final failures = <String>[];
    for (final e in rows) {
      try {
        Question.fromJson(Map<String, dynamic>.from(e as Map));
      } catch (err) {
        failures.add('${(e as Map)['id']}: $err');
      }
    }
    expect(failures, isEmpty, reason: failures.take(5).join('\n'));
    expect(rows.length, greaterThan(3286));
  });
}
