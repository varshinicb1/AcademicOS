/// Launches and supervises the bundled local backend on desktop so the app
/// never depends on a remote server -- the only network traffic this app
/// makes is the local process's own outgoing calls to genuine third-party
/// services (e.g. Sarvam Vision for OCR), never a call back to us.
///
/// No-op on web/mobile, where there's nothing to spawn.
export 'local_server_stub.dart' if (dart.library.io) 'local_server_io.dart';
