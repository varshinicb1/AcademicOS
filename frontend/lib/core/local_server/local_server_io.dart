import 'dart:async';
import 'dart:io';

/// Spawns the bundled local backend (server/academicos_server.exe, a
/// PyInstaller-frozen copy of the same FastAPI app the web deployment runs)
/// as a child process on the user's own machine, and waits for it to answer
/// before the UI starts making requests.
///
/// Layout expected next to the running academicos.exe:
///   app/academicos.exe        <- this process (Platform.resolvedExecutable)
///   server/academicos_server.exe
///   academicos-data/          <- question corpus; server resolves this via cwd
///
/// Deliberately Windows-only for now (the packaging work this supports is
/// Windows desktop) -- no-ops everywhere else, including web, so the hosted
/// deployment's own ACADEMICOS_API build-time URL is completely untouched.
class LocalServerManager {
  static Process? _process;
  static bool _weStartedIt = false;

  static const _port = 8010;
  static const _healthUrl = 'http://127.0.0.1:$_port/docs';

  static bool get isManaged => _weStartedIt;

  /// Returns true once something is answering on localhost:8010 -- either
  /// because we just launched it, or because it was already running.
  static Future<bool> ensureRunning() async {
    if (!Platform.isWindows) return false;

    if (await _isHealthy()) return true;

    final exeDir = File(Platform.resolvedExecutable).parent;
    final rootDir = exeDir.parent; // desktop_dist/, sibling of app/ and server/
    final serverExe = File('${rootDir.path}\\server\\academicos_server.exe');
    if (!await serverExe.exists()) {
      // Not packaged as a standalone build (e.g. running via `flutter run`
      // during development) -- fall back to whatever ACADEMICOS_API was
      // dart-defined, same as before this change.
      return false;
    }

    try {
      _process = await Process.start(
        serverExe.path,
        ['$_port'],
        workingDirectory: rootDir.path,
        mode: ProcessStartMode.detachedWithStdio,
      );
      _weStartedIt = true;
    } catch (_) {
      return false;
    }

    // Local process startup, not a 3GB cold-boot download -- should be a
    // couple of seconds, but give it real headroom on a slow first launch.
    const timeout = Duration(seconds: 30);
    final deadline = DateTime.now().add(timeout);
    while (DateTime.now().isBefore(deadline)) {
      if (await _isHealthy()) return true;
      await Future.delayed(const Duration(milliseconds: 300));
    }
    return false;
  }

  static Future<bool> _isHealthy() async {
    try {
      final client = HttpClient()..connectionTimeout = const Duration(seconds: 1);
      final req = await client.getUrl(Uri.parse(_healthUrl));
      final resp = await req.close().timeout(const Duration(seconds: 2));
      await resp.drain();
      client.close();
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Best-effort cleanup. Dart has no portable "kill child if parent dies"
  /// hook on Windows without native Job Object FFI, so an ungraceful exit
  /// (task-killed, crash) can leave the local server running in the
  /// background -- harmless (localhost-only, no data it didn't already
  /// have), but callers should still invoke this on normal shutdown paths.
  static void stop() {
    if (_weStartedIt) {
      _process?.kill();
      _weStartedIt = false;
    }
  }

  static bool _watching = false;

  /// Ctrl+C / SIGTERM cleanup. Doesn't cover every exit path (see [stop]
  /// doc) but catches the common ones without pulling in a window-manager
  /// close-intercept dependency for this.
  static void watchShutdownSignals() {
    if (_watching || !Platform.isWindows) return;
    _watching = true;
    try {
      ProcessSignal.sigint.watch().listen((_) => stop());
    } catch (_) {}
  }
}
