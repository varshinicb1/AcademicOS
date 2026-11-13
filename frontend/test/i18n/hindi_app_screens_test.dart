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
  // The apps' shell, and what their tabs and the School page open for a
  // teacher, student or parent (app_router.dart's role pages).
  'lib/presentation/workspace/app_mode.dart',
  'lib/presentation/workspace/ops_api.dart',
  'lib/presentation/workspace/notice.dart',
  'lib/presentation/workspace/calendar_day_notice.dart',
  'lib/presentation/workspace/messaging_card.dart',
  'lib/presentation/workspace/profiles.dart',
  'lib/presentation/workspace/young_home.dart',
  'lib/presentation/workspace/practice_page.dart',
  'lib/presentation/workspace/photos_ui.dart',
  'lib/presentation/workspace/marks_page.dart',
  'lib/presentation/workspace/class_progress_page.dart',
  'lib/presentation/workspace/admin_pages.dart',
  'lib/presentation/workspace/exams_page.dart',
  'lib/presentation/workspace/report_cards_page.dart',
  'lib/presentation/guide/guide_welcome.dart',
];

/// Strings that are rightly not translated: a language's own name, the
/// button back to English (written in the language it switches to), and
/// names that read the same in Hindi.
const untranslatable = {'English', 'हिन्दी', 'Switch to English', 'SMS', 'WhatsApp'};

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
  literalsTest();

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
        // A label: 'Today' in a record or map is translated where it is shown
        // (tr(t.label)); a Text('Today') never is.
        final shownLater = !m.group(0)!.startsWith('Text') && hasHindi(text);
        if (_hasWords(text) && !untranslatable.contains(text) && !shownLater) bare.add('$path: $text');
      }
    }
    expect(bare, isEmpty, reason: 'wrap these in tr() or trf() and give them Hindi:\n${bare.join('\n')}');
  });

  test('every tr() and trf() key on the app screens has a Hindi entry', () {
    // A key may be several adjacent literals ('a ' 'b'); one built at runtime
    // (tr(x)) is checked where its words are written, not here.
    final call = RegExp(r'\btrf?\(\s*((?:' + _lit + r'\s*)+)[,)]');
    final plural = RegExp(r"\bplural\((?:[^()']|\([^()]*\))*?,\s*'([^']+)'(?:\s*,\s*'([^']+)')?\s*\)");
    final missing = <String>{};
    for (final path in appScreens) {
      for (final m in call.allMatches(File(path).readAsStringSync())) {
        final key = RegExp(_lit).allMatches(m.group(1)!).map((x) => _unescape(x.group(0)!)).join();
        if (key.contains(r'$')) continue;
        if (!hasHindi(key)) missing.add('$path: $key');
      }
      // plural(n, 'mark') translates its nouns.
      for (final m in plural.allMatches(File(path).readAsStringSync())) {
        for (final noun in [m.group(1), m.group(2)].whereType<String>()) {
          if (!hasHindi(noun)) missing.add('$path: $noun');
        }
      }
    }
    expect(missing, isEmpty, reason: 'give these Hindi entries:\n${missing.join('\n')}');
  });

  test('trf fills a translated template with its values', () {
    expect(trf('Due {date}', {'date': '2026-10-20'}), 'Due 2026-10-20');
    expect(hasHindi('Due {date}'), isTrue);
  });
}

/// A string literal in a source file: where it starts and ends, its text with
/// each interpolation as \u0001, and how deep in interpolations it sits.
class _Lit {
  final int start, end, depth;
  final String text;
  _Lit(this.start, this.end, this.depth, this.text);
}

/// Every string literal in [s], comments skipped, interpolated ones included.
List<_Lit> _literals(String s) {
  final out = <_Lit>[];
  final ident = RegExp(r'[A-Za-z0-9_]');
  late int Function(int, int, bool) code;
  int string(int start, int depth) {
    final raw = start > 0 && s[start - 1] == 'r' && (start < 2 || !ident.hasMatch(s[start - 2]));
    final q = s[start];
    final close = s.startsWith(q * 3, start) ? q * 3 : q;
    var i = start + close.length;
    final text = StringBuffer();
    while (i < s.length && !s.startsWith(close, i)) {
      if (!raw && s[i] == r'\') {
        text.write(s[i + 1] == 'n' ? '\n' : s[i + 1]);
        i += 2;
      } else if (!raw && s.startsWith(r'${', i)) {
        text.write('\u0001');
        i = code(i + 2, depth + 1, true);
      } else if (!raw && s[i] == r'$' && i + 1 < s.length && RegExp('[A-Za-z_]').hasMatch(s[i + 1])) {
        text.write('\u0001');
        i++;
        while (i < s.length && ident.hasMatch(s[i])) {
          i++;
        }
      } else {
        text.write(s[i]);
        i++;
      }
    }
    out.add(_Lit(start, i + close.length, depth, text.toString()));
    return i + close.length;
  }

  code = (int i, int depth, bool interpolation) {
    var braces = 0;
    while (i < s.length) {
      if (s.startsWith('//', i)) {
        final nl = s.indexOf('\n', i);
        if (nl < 0) return s.length;
        i = nl;
      } else if (s.startsWith('/*', i)) {
        i = s.indexOf('*/', i) + 2;
      } else if (s[i] == "'" || s[i] == '"') {
        i = string(i, depth);
        continue;
      } else if (s[i] == '{') {
        braces++;
      } else if (s[i] == '}') {
        if (interpolation && braces == 0) return i + 1;
        braces--;
      }
      i++;
    }
    return i;
  };
  code(0, 0, false);
  out.sort((a, b) => a.start.compareTo(b.start));
  // Adjacent literals ('a ' 'b') are one string.
  final joined = <_Lit>[];
  for (final l in out) {
    final prev = joined.lastWhere((p) => p.depth == l.depth && p.end <= l.start,
        orElse: () => _Lit(-1, -1, -1, ''));
    if (prev.start >= 0 && joined.last == prev && s.substring(prev.end, l.start).trim().isEmpty) {
      joined[joined.length - 1] = _Lit(prev.start, l.end, l.depth, prev.text + l.text);
    } else {
      joined.add(l);
    }
  }
  return joined;
}

/// Literals on the app screens that a user never reads: request fields and
/// values, lookup keys, file names and log lines. Anything else in English
/// must be translated.
const notShown = <String>{
  'GET', 'POST', 'PUT', 'PATCH', 'DELETE', // HTTP methods
  'ACADEMICOS_APP', // the build flag
  'Leave', // the reason a leave request is sent with when none is typed
  'social science', 'social studies', 'computer science', // subject colour keys (week_page)
  r'$…-template', // a downloaded file's name
};

/// Whether [text] reads as English to a user: words, and either a space or a
/// capital. 'subjectName', 'first_half' and '/school/inbox' are data.
bool _looksEnglish(String text) {
  final t = text.replaceAll('\u0001', '');
  if (!RegExp('[A-Za-z]{2}').hasMatch(t)) return false;
  if (t.startsWith('/') || t.startsWith('.') || t.startsWith('package:')) return false;
  // One lowercase token with no space: a field, key, path or MIME type.
  return !RegExp(r'^[a-z][A-Za-z0-9_\-.:?/]*$').hasMatch(t);
}

void literalsTest() {
  test('every English literal on the app screens is translated', () {
    final left = <String>[];
    for (final path in appScreens) {
      final src = File(path).readAsStringSync();
      for (final l in _literals(src)) {
        if (!_looksEnglish(l.text) || untranslatable.contains(l.text)) continue;
        final before = src.substring(0, l.start).trimRight();
        final line = src.substring(src.lastIndexOf('\n', l.start) + 1, l.start).trimLeft();
        if (line.startsWith('import ') || line.startsWith('export ') || line.startsWith('part ')) continue;
        if (RegExp(r'(Key|debugPrint)\($').hasMatch(before)) continue;
        if (notShown.contains(l.text.replaceAll('\u0001', r'$…'))) continue;
        final translated = RegExp(r'\btrf?\($').hasMatch(before);
        if (l.text.contains('\u0001')) {
          if (!translated) left.add('$path: ${l.text.replaceAll('\u0001', r'$…')}  (use trf with {placeholders})');
          continue;
        }
        if (!hasHindi(l.text)) left.add('$path: ${l.text}');
      }
    }
    expect(left, isEmpty,
        reason: 'translate these (tr/trf and a Hindi entry), or add a data string to notShown:\n${left.join('\n')}');
  });
}
