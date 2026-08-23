// Proves the exact mechanism local_scan_engine.dart's uploadPage/
// processSession/submitReviewDecision/finalizeSession now rely on to avoid
// the lost-page race an audit found: two concurrent async read-modify-write
// operations against the same key must not interleave.
import 'package:flutter_test/flutter_test.dart';
import 'package:academicos/core/local_engine/keyed_mutex.dart';

void main() {
  test('two concurrent operations on the same key never interleave', () async {
    final mutex = KeyedMutex();
    final log = <String>[];

    Future<void> op(String label) => mutex.synchronized('session_1', () async {
          log.add('$label start');
          await Future.delayed(const Duration(milliseconds: 20));
          log.add('$label end');
        });

    // Fired "simultaneously" -- the real scenario a fast double-tap on
    // "capture page" produces: two calls entering uploadPage before either
    // has written back.
    await Future.wait([op('A'), op('B')]);

    expect(log, ['A start', 'A end', 'B start', 'B end'],
        reason: 'B must not start until A has fully finished (read+await+write)');
  });

  test('a shared, real, read-modify-write list is never corrupted under concurrency', () async {
    // Simulates exactly what uploadPage does: read a list, append after an
    // await, write back. Without the mutex this drops writes; with it,
    // every one of N concurrent "page captures" survives.
    final mutex = KeyedMutex();
    final store = <String, List<int>>{'session_1': []};

    Future<void> capturePage(int page) => mutex.synchronized('session_1', () async {
          final current = List<int>.from(store['session_1']!);
          await Future.delayed(Duration(milliseconds: 5 + (page % 3)));
          current.add(page);
          store['session_1'] = current;
        });

    await Future.wait(List.generate(10, capturePage));

    expect(store['session_1']!.length, 10,
        reason: 'every concurrent capture must survive -- this is exactly the bug the audit found');
    expect(store['session_1']!.toSet(), {0, 1, 2, 3, 4, 5, 6, 7, 8, 9});
  });

  test('different keys never block each other', () async {
    final mutex = KeyedMutex();
    final order = <String>[];

    final a = mutex.synchronized('session_a', () async {
      await Future.delayed(const Duration(milliseconds: 30));
      order.add('a');
    });
    final b = mutex.synchronized('session_b', () async {
      order.add('b'); // should NOT wait for session_a's lock
    });

    await Future.wait([a, b]);
    expect(order.first, 'b', reason: 'a different session id must not be blocked by session_a\'s lock');
  });
}
