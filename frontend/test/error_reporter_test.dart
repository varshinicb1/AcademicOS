// Errors the app catches are reported to the server (NFR-7): at most a few a
// session, the same one once, never throwing, and chained after whatever
// handler was there before.
import 'package:academicos/core/errors/error_reporter.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('a report carries the message, the top of the stack and the build, nothing else', () {
    final r = ErrorReporter(source: 'web', send: (_) async {});
    final stack = StackTrace.fromString(List.generate(40, (i) => '#$i frame$i').join('\n'));
    final body = r.bodyFor(StateError('Bad state: no section'), stack, route: '/school/timetable');
    expect(body.keys.toSet(), {'source', 'message', 'stack', 'route', 'appVersion'});
    expect(body['source'], 'web');
    expect(body['message'], 'Bad state: Bad state: no section');
    expect((body['stack'] as String).split('\n'), hasLength(30));
    expect(body['route'], '/school/timetable');
  });

  test('the same error is sent once, and a session sends at most its limit', () async {
    final sent = <Map<String, dynamic>>[];
    final r = ErrorReporter(source: 'android', send: (b) async => sent.add(b), maxPerSession: 3);
    final stack = StackTrace.fromString('#0 build (page.dart:1)');
    await r.report(Exception('one'), stack);
    await r.report(Exception('one'), stack);
    await r.report(Exception('two'), stack);
    await r.report(Exception('three'), stack);
    await r.report(Exception('four'), stack);
    expect(sent.map((b) => b['message']), ['Exception: one', 'Exception: two', 'Exception: three']);
  });

  test('a report that cannot be sent is dropped, not raised', () async {
    final r = ErrorReporter(source: 'web', send: (_) async => throw StateError('offline'));
    await r.report(Exception('x'), null);   // must complete without throwing
  });

  test('installing keeps the handler that was there before', () async {
    final sent = <Map<String, dynamic>>[];
    final before = FlutterError.onError;
    var previousCalled = false;
    FlutterError.onError = (_) => previousCalled = true;
    addTearDown(() => FlutterError.onError = before);
    ErrorReporter.install(ErrorReporter(source: 'web', send: (b) async => sent.add(b)));
    FlutterError.onError!(FlutterErrorDetails(exception: Exception('layout'), stack: StackTrace.current));
    await Future<void>.delayed(Duration.zero);
    expect(previousCalled, isTrue);
    expect(sent.single['message'], 'Exception: layout');
  });
}
