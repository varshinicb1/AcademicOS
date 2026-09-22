// No `catch` on a web screen may swallow a failure (Task 802).
//
// The 2026-09-22 re-audit of the live release kept finding screens that failed
// silently: the subtopic picker turned every failed topic fetch into "no
// subtopics", the principal's subject dropdowns stayed empty after a failed
// load, a parent portal whose progress call failed showed a blank term, and a
// teacher who recorded parental consent was told "Consent recorded" while the
// server call was fire-and-forget -- grading then refused the student for want
// of consent. Each was fixed; this makes the pattern fail a test.
//
// Every `catch` block (and `.catchError` handler) under lib/presentation/ must
// rethrow/throw, or pass the error through serverErrorMessage (api_error.dart),
// the one path that turns it into a sentence. A block that is genuinely not a
// failure the user needs to hear about carries a `// not-a-failure: <why>`
// comment, and every such exemption is also counted in [_exempt] below with
// the reason, so adding one means editing this file in review.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Files allowed `// not-a-failure:` exemptions, how many, and why.
const _exempt = {
  // The mail-backend status is advisory: it only decides whether to show the
  // "no mail backend configured" hint. A failed fetch leaves the hint off and
  // the Send button's own error path (serverErrorMessage) reports a real
  // failure to send. Blocking preview/print on it would be worse.
  'lib/presentation/assessment/widgets/paper_delivery_sheet.dart': 1,
  // The offline Android build's first-run demo seeding. It never runs on the
  // web (guarded by ACADEMICOS_OFFLINE) and the app is fully usable unseeded;
  // the failure is logged with its stack.
  'lib/presentation/home/pages/home_page.dart': 1,
};

const _marker = '// not-a-failure:';

/// A handler passes: it rethrows, throws, or calls the shared error path.
final _handled = RegExp(r'\brethrow\b|\bthrow\b|\bserverErrorMessage\(');

/// `catch (e)`, `on X catch (e, st)` -- and `.catchError(`, handled separately.
final _catchClause = RegExp(r'(?<![.\w])catch\s*\(');
final _catchError = RegExp(r'\.catchError\s*\(');

/// An `on SomeException {` clause with no `catch` names no error to report.
final _bareOn = RegExp(r'\}\s*on\s+[A-Z]\w*(<[^>]*>)?\s*\{');

/// Showing a FutureBuilder's raw error is the `'$e'` pattern in another form.
final _rawSnapshotError = RegExp(r'\$\{\s*(snap|snapshot)\.error\s*!?\s*\}');

/// Index just past the bracket matching the one at [open].
int _matching(String src, int open, String o, String c) {
  var depth = 0;
  for (var i = open; i < src.length; i++) {
    final ch = src[i];
    if (ch == o) depth++;
    if (ch == c) {
      depth--;
      if (depth == 0) return i + 1;
    }
  }
  return src.length;
}

String _stripLineComments(String block) =>
    block.split('\n').map((l) {
      final i = l.indexOf('//');
      return i < 0 ? l : l.substring(0, i);
    }).join('\n');

int _lineOf(String src, int index) => '\n'.allMatches(src.substring(0, index)).length + 1;

/// True when [index] sits after a `//` on its own line, i.e. in a comment.
bool _inComment(String src, int index) =>
    src.substring(src.lastIndexOf('\n', index) + 1, index).contains('//');

/// Every handler body in [src], with the line it starts on.
Iterable<(int, String)> _handlers(String src) sync* {
  for (final m in _catchClause.allMatches(src)) {
    if (_inComment(src, m.start)) continue;
    final afterParams = _matching(src, src.indexOf('(', m.start), '(', ')');
    final open = src.indexOf('{', afterParams);
    yield (_lineOf(src, m.start), src.substring(open, _matching(src, open, '{', '}')));
  }
  for (final m in _catchError.allMatches(src)) {
    if (_inComment(src, m.start)) continue;
    final open = src.indexOf('(', m.start);
    yield (_lineOf(src, m.start), src.substring(open, _matching(src, open, '(', ')')));
  }
  for (final m in _bareOn.allMatches(src)) {
    if (_inComment(src, m.start)) continue;
    final open = src.indexOf('{', m.start + 1);
    yield (_lineOf(src, m.start), src.substring(open, _matching(src, open, '{', '}')));
  }
}

/// (offences, exemptions used) for one file's source.
(List<String>, int) _scan(String rel, String src) {
  final offences = <String>[];
  var exemptions = 0;
  for (final (line, body) in _handlers(src)) {
    final markerAt = body.indexOf(_marker);
    if (markerAt >= 0) {
      final reason = body.substring(markerAt + _marker.length).split('\n').first.trim();
      if (reason.length < 10) {
        offences.add('$rel:$line: `$_marker` needs a reason');
      }
      exemptions++;
      continue;
    }
    if (!_handled.hasMatch(_stripLineComments(body))) {
      offences.add('$rel:$line: neither rethrows nor calls serverErrorMessage()');
    }
  }
  final lines = src.split('\n');
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].trimLeft().startsWith('//')) continue;
    if (_rawSnapshotError.hasMatch(lines[i])) {
      offences.add('$rel:${i + 1}: shows a raw snapshot error; use serverErrorMessage()');
    }
  }
  return (offences, exemptions);
}

void main() {
  test('every catch under lib/presentation reports its failure or rethrows it', () {
    final offences = <String>[];
    final used = <String, int>{};
    final files = Directory('lib/presentation')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'))
        .where((f) => !f.path.endsWith('.g.dart') && !f.path.endsWith('.freezed.dart'));
    for (final file in files) {
      final rel = file.path.replaceAll('\\', '/');
      final (found, exemptions) = _scan(rel, file.readAsStringSync());
      offences.addAll(found);
      if (exemptions > 0) used[rel] = exemptions;
    }
    expect(offences, isEmpty, reason: offences.join('\n'));
    expect(used, _exempt,
        reason: 'a `$_marker` exemption must be listed, with its reason, in _exempt');
  });

  group('the scan itself (guards against a scan that matches nothing)', () {
    test('flags a swallowing catch, a raw error, a bare on-clause and a silent catchError', () {
      const src = '''
Future<void> a() async {
  try { await f(); } catch (_) { setState(() => _loading = false); }
  try { await f(); } catch (e) { setState(() => _error = '\$e'); }
  try { await f(); } on DioException { }
  f().catchError((Object e) { print(e); });
  return Text('\${snap.error}');
}
''';
      final (offences, _) = _scan('x.dart', src);
      expect(offences, hasLength(5), reason: offences.join('\n'));
    });

    test('passes a reported, rethrown or exempted catch', () {
      const src = '''
Future<void> a() async {
  try { await f(); } catch (e) { setState(() => _error = serverErrorMessage(e)); }
  try { await f(); } on DioException catch (e) { if (x) return null; rethrow; }
  try { await f(); } catch (_) {
    // not-a-failure: advisory status, the send path reports real failures
  }
  // a comment naming catch (e) is not code
}
''';
      final (offences, exemptions) = _scan('x.dart', src);
      expect(offences, isEmpty, reason: offences.join('\n'));
      expect(exemptions, 1);
    });

    test('a comment mentioning serverErrorMessage does not count as calling it', () {
      const src = '''
void a() {
  try { f(); } catch (_) {
    // should call serverErrorMessage(e) here
  }
}
''';
      expect(_scan('x.dart', src).$1, hasLength(1));
    });
  });
}
