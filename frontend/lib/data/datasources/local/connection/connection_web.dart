import 'package:drift/drift.dart';

/// Web build never reads or writes this database — confirmed by grep: every
/// repository's `_localDb` field is assigned in the constructor and never
/// read anywhere (the app calls PillarApi directly for everything). The
/// native connection (drift/native.dart) pulls in package:sqlite3's FFI
/// bindings, which fail to compile for web outright — that's what this
/// file avoids. LazyDatabase only opens on the first actual query, which
/// should never happen here; if it somehow does, fail loudly instead of
/// silently behaving like a working database it isn't.
LazyDatabase openConnection(String dbPath) {
  return LazyDatabase(() async {
    throw UnsupportedError(
      'AppDatabase has no web-compatible backing store. If you are seeing '
      'this, something started actually querying the local drift database '
      'on web — it needs a real web executor (drift/wasm.dart) added.',
    );
  });
}
