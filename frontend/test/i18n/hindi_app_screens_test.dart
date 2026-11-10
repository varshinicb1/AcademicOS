// R-B5 (NFR-6, TA-9): every string a teacher, student or parent reads on the
// phone apps' screens goes through tr()/trf() and has a Hindi entry. The test
// reads the screens' source: a visible English literal that bypasses tr(), or a
// tr()/trf() key with no Hindi, fails it, naming the file and the string.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/presentation/workspace/strings.dart';

/// The files that build the apps' tabs (app_mode.dart) and what they open.
const appScreens = [
  'lib/presentation/workspace/inbox_page.dart',
  'lib/presentation/workspace/student_pages.dart',
  'lib/presentation/workspace/student_today_page.dart',
  'lib/presentation/workspace/cover_pages.dart',
  'lib/presentation/workspace/teacher_homework.dart',
  'lib/presentation/workspace/family_page.dart',
  'lib/presentation/workspace/workspace_page.dart',
  'lib/presentation/workspace/week_page.dart',
  'lib/presentation/workspace/period_line.dart',
  'lib/presentation/assessment/pages/assessment_list_page.dart',
];

/// Strings that are rightly not translated: a language's own name.
const untranslatable = {'English', 'हिन्दी'};

const _lit = r"""'(?:[^'\\]|\\.)*'""";

String _unescape(String lit) =>
    lit.substring(1, lit.length - 1).replaceAllMapped(RegExp(r'\\(.)'), (m) => m.group(1)!);

/// The words of a literal, interpolations taken out: data such as
/// '${a.subject} · ${a.grade}' has none. The literal pattern stops at a quote
/// inside an interpolation ('${e['marks']}'), so one left open runs to the end.
bool _hasWords(String text) {
  final out = StringBuffer();
  var depth = 0;
  for (var i = 0; i < text.length; i++) {
    if (text.startsWith(r'${', i)) {
      depth++;
      i++;
    } else if (depth > 0) {
      if (text[i] == '{') depth++;
      if (text[i] == '}') depth--;
    } else {
      out.write(text[i]);
    }
  }
  return RegExp('[A-Za-z]{2}').hasMatch(out.toString().replaceAll(RegExp(r'\$\w+'), ''));
}

void main() {
  test('every visible string on the app screens goes through tr()', () {
    // A literal a user reads: Text('...'), or a label, title, tooltip, hint or
    // message argument. One right after tr( or trf( is translated.
    final visible = RegExp(
        r"(?<!tr\()(?<!trf\()(?:\bText\(\s*|\b(?:label|title|tooltip|hintText|labelText|helperText|message|subtitle"
        "|semanticLabel)\\s*:\\s*)($_lit)");
    final bare = <String>[];
    for (final path in appScreens) {
      for (final m in visible.allMatches(File(path).readAsStringSync())) {
        final text = _unescape(m.group(1)!);
        if (_hasWords(text) && !untranslatable.contains(text)) bare.add('$path: $text');
      }
    }
    expect(bare, isEmpty, reason: 'wrap these in tr() or trf() and give them Hindi');
  });

  test('every tr() and trf() key on the app screens has a Hindi entry', () {
    // A key may be several adjacent literals ('a ' 'b'); one built at runtime
    // (tr(x)) is checked where its words are written, not here.
    final call = RegExp(r'\btrf?\(\s*((?:' + _lit + r'\s*)+)[,)]');
    final missing = <String>{};
    for (final path in appScreens) {
      for (final m in call.allMatches(File(path).readAsStringSync())) {
        final key = RegExp(_lit).allMatches(m.group(1)!).map((x) => _unescape(x.group(0)!)).join();
        if (key.contains(r'$')) continue;
        if (!hasHindi(key)) missing.add('$path: $key');
      }
    }
    expect(missing, isEmpty);
  });

  test('trf fills a translated template with its values', () {
    expect(trf('Due {date}', {'date': '2026-10-20'}), 'Due 2026-10-20');
    expect(hasHindi('Due {date}'), isTrue);
  });
}
