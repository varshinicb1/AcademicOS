// `setState(() => _future = _load())` hands setState the Future the
// assignment evaluates to; Flutter asserts against that, so in a debug build
// Retry threw instead of retrying (Task 802 review). A block body is required.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('no setState arrow body assigns a Future', () {
    final bad = RegExp(r'setState\(\(\)\s*=>\s*_\w*[fF]uture\w*\s*=');
    final hits = <String>[];
    for (final f in Directory('lib').listSync(recursive: true).whereType<File>()) {
      if (!f.path.endsWith('.dart')) continue;
      final lines = f.readAsLinesSync();
      for (var i = 0; i < lines.length; i++) {
        final line = lines[i].trimLeft();
        if (!line.startsWith('//') && bad.hasMatch(line)) hits.add('${f.path}:${i + 1}');
      }
    }
    expect(hits, isEmpty);
  });
}
