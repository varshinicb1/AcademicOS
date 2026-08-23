/// Serializes async read-modify-write operations against the same key, so
/// two concurrent calls touching the same Hive-backed record (e.g. a fast
/// double-tap on "capture page" firing two `uploadPage` calls for the same
/// scan session) can't interleave their read/await/write and silently drop
/// one write. LocalStore itself has no transactions -- every "read the
/// record, mutate it, write it back" call site needs this if it can be
/// entered concurrently for the same key. Confirmed real via an audit: an
/// unguarded uploadPage could lose a captured page exactly this way.
library;

import 'dart:async';

class KeyedMutex {
  final _last = <String, Completer<void>>{};

  /// Runs [action] only after every previously-queued action for the same
  /// [key] has finished; actions for different keys never block each other.
  Future<T> synchronized<T>(String key, Future<T> Function() action) async {
    final myCompleter = Completer<void>();
    final prior = _last[key];
    _last[key] = myCompleter;

    if (prior != null) await prior.future;
    try {
      return await action();
    } finally {
      myCompleter.complete();
      // Only the most-recently-queued waiter for this key clears the entry
      // -- if someone queued behind us, leave their completer in place.
      if (identical(_last[key], myCompleter)) {
        _last.remove(key);
      }
    }
  }
}
