/// Web/no-`dart:io` build: nothing to launch, the app talks to whatever
/// ACADEMICOS_API was baked in at build time (the deployed backend, for the
/// hosted web app -- untouched by the desktop packaging work).
class LocalServerManager {
  static Future<bool> ensureRunning() async => false;
  static void stop() {}
  static void watchShutdownSignals() {}
  static bool get isManaged => false;
}
