import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:get_it/get_it.dart';

import '../sync/network_policy.dart';

/// The build this app is, for grouping reports by release; set at build time
/// with --dart-define=ACADEMICOS_BUILD=<commit>.
const kBuildId = String.fromEnvironment('ACADEMICOS_BUILD', defaultValue: 'unknown');

/// Sends what Flutter caught -- an error in a widget's build, an uncaught
/// async error -- to the backend's `POST /client-errors` (REQUIREMENTS NFR-7),
/// where it is grouped and written as a Cloud Error Reporting event. Until
/// this, an error in the app was seen only by the person holding it.
///
/// At most [maxPerSession] reports a session, and the same error (message
/// and top frame) once: a crash loop must not flood the school's connection.
/// Sending never throws and never blocks the app. The offline build never
/// sends (it makes no request until sync is on, network_policy.dart).
class ErrorReporter {
  final String source; // web | android | ios
  final Future<void> Function(Map<String, dynamic> body) send;
  final int maxPerSession;
  final Set<String> _seen = {};
  int _sent = 0;

  ErrorReporter({required this.source, required this.send, this.maxPerSession = 20});

  /// The reporter for this app, or null where it should not report: the
  /// offline build, and desktop development builds.
  static ErrorReporter? forApp() {
    if (kOfflineBuild) return null;
    final String source;
    if (kIsWeb) {
      source = 'web';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      source = 'android';
    } else if (defaultTargetPlatform == TargetPlatform.iOS) {
      source = 'ios';
    } else {
      return null;
    }
    return ErrorReporter(
      source: source,
      send: (body) async {
        await GetIt.I<Dio>().post('/client-errors', data: body);
      },
    );
  }

  /// What is sent for [error]: its message, the first 30 lines of the stack,
  /// the page's path on the web, and the build. No user, no data.
  Map<String, dynamic> bodyFor(Object error, StackTrace? stack, {String? route}) {
    final lines = (stack?.toString() ?? '').split('\n').where((l) => l.trim().isNotEmpty).take(30).join('\n');
    final message = error.toString();
    return {
      'source': source,
      'message': message.length > 2000 ? message.substring(0, 2000) : message,
      if (lines.isNotEmpty) 'stack': lines,
      if (route != null && route.isNotEmpty) 'route': route.length > 200 ? route.substring(0, 200) : route,
      'appVersion': kBuildId,
    };
  }

  Future<void> report(Object error, StackTrace? stack, {String? route}) async {
    if (_sent >= maxPerSession) return;
    final body = bodyFor(error, stack, route: route);
    final top = (body['stack'] as String? ?? '').split('\n').first;
    if (!_seen.add('${body['message']}|$top')) return;
    _sent++;
    try {
      await send(body);
    } catch (e) {
      // not-a-failure: a report that cannot be sent (no signal, server down)
      // is dropped rather than raised -- reporting must never break the app.
      debugPrint('error report not sent: $e');
    }
  }

  /// Hook [reporter] into Flutter's error handlers, keeping whatever was
  /// there before (the red screen in debug, the console print).
  static void install(ErrorReporter reporter) {
    final previous = FlutterError.onError;
    FlutterError.onError = (details) {
      previous?.call(details);
      reporter.report(details.exception, details.stack, route: kIsWeb ? Uri.base.path : null);
    };
    final previousPlatform = PlatformDispatcher.instance.onError;
    PlatformDispatcher.instance.onError = (error, stack) {
      reporter.report(error, stack, route: kIsWeb ? Uri.base.path : null);
      return previousPlatform?.call(error, stack) ?? false;
    };
  }
}
