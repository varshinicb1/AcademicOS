/// The one place a failed web API call becomes a sentence a teacher or
/// principal can act on (Task 802).
///
/// Until 2026-09-22 there were three mappers (curriculum_api's
/// serverErrorMessage, pillar_api's apiErrorMessage, auth_api's
/// _asAuthException) and most screens used none of them: they showed `'$e'`,
/// which for a DioException is Dio's "DioException [bad response]: This
/// exception was thrown because the response has a status code of 422..."
/// paragraph. The re-audit of the live release found the backend's carefully
/// built reasons (a lesson clash's date, a missing consent, a legacy calendar
/// value) never reaching the screen, a validation 422 shown as "HTTP 422",
/// and a 500 reported as "could not reach the server". Every screen under
/// lib/presentation/ now goes through [serverErrorMessage];
/// test/no_swallowed_errors_test.dart fails a `catch` that does not.
library;

import 'package:dio/dio.dart';

final _valueError = RegExp(r'^Value error, ');

/// What a feature that is not switched on yet is called on screen. The server answers 501
/// (not 503: retrying will never help until it is switched on) with a `code`; the person sees
/// "Coming soon", not an error, and no Retry button.
const comingSoonPrefix = 'Coming soon';

String comingSoonMessage({String? code, String? detail}) => switch (code) {
      'llm_not_enabled' =>
        '$comingSoonPrefix: AI marking and scan reading are not switched on for your school yet.',
      'not_available' when detail != null && detail.trim().isNotEmpty => '$comingSoonPrefix: ${detail.trim()}',
      _ => '$comingSoonPrefix: this is not switched on for your school yet.',
    };

bool isComingSoonMessage(String message) => message.startsWith(comingSoonPrefix);

const _signedOut = "You're signed out — sign in again";
const _noAccess = "You don't have access to that";
const _unreachable = "Couldn't reach the server — check your connection";

/// What to show for [e], most specific first:
///
///  * 401: the session is over. Always this sentence, even with a `detail`:
///    the server's "Not authenticated" tells a teacher nothing about what to
///    do, and the session interceptor is already sending them to Sign in.
///  * the server's `detail` when it is a non-empty string -- the backend
///    writes these to name the fix ("record it under Classes before grading").
///  * `detail.message` when `detail` is an object: the 400/409 of
///    generate-from-template, whose body carries the whole availability report
///    beside the sentence ("no question in the bank fits this template").
///  * a FastAPI/Pydantic 422 list, summarised as `field: message` pairs.
///  * 403 with no detail: the account lacks access.
///  * no response at all (connection error, any timeout): the connection.
///    Said only then -- a server that answered 500 is not a connection fault.
///  * any other status: what it was, so a support report can name it.
///  * anything that is not a DioException: its own text, minus Dart's
///    "Exception: " prefix (screens throw `Exception('<sentence>')`).
String serverErrorMessage(Object e) {
  if (e is! DioException) {
    final text = '$e';
    return text.startsWith('Exception: ') ? text.substring('Exception: '.length) : text;
  }
  final response = e.response;
  final status = response?.statusCode;
  if (status == 401) return _signedOut;
  final data = response?.data;
  final detail = data is Map ? data['detail'] : null;
  if (status == 501) {
    return comingSoonMessage(code: data is Map ? data['code'] as String? : null, detail: detail is String ? detail : null);
  }
  if (detail is String && detail.trim().isNotEmpty) return detail;
  final message = detail is Map ? detail['message'] : null;
  if (message is String && message.trim().isNotEmpty) return message;
  if (detail is List) {
    final summary = _validationSummary(detail);
    if (summary.isNotEmpty) return summary;
  }
  if (status == 403) return _noAccess;
  if (response == null || status == null) return _unreachable;
  if (status == 404) return 'The server has no record of it — it may have been removed';
  if (status >= 500) return 'The server had a problem (HTTP $status) — try again shortly';
  return 'The server refused the request (HTTP $status)';
}

/// True when sending the same request again could succeed: no answer came
/// back, or the server failed (5xx, 408, 429). A 401/403/409/422 will be
/// refused again, so a Retry button there only teaches the user to click it.
bool isRetryable(Object e) {
  if (e is! DioException) return false;
  final status = e.response?.statusCode;
  if (e.response == null || status == null) return true;
  return status >= 500 || status == 408 || status == 429;
}

/// `[{loc: [body, sections, 0, marks], msg: ...}, ...]` ->
/// "sections.0.marks: ...; ...". The first `loc` element names where the
/// field came from (body/query/path/header), which the user never sees.
///
/// Pydantic prefixes a model validator's own message with "Value error, ";
/// the sentence after it is the one the backend wrote for the teacher
/// ("sections add up to 22 marks but the total is 25"), so the prefix goes.
String _validationSummary(List<dynamic> errors) {
  const origins = {'body', 'query', 'path', 'header', 'cookie'};
  final parts = <String>[];
  for (final error in errors) {
    if (error is! Map) continue;
    final msg = '${error['msg'] ?? ''}'.trim().replaceFirst(_valueError, '');
    if (msg.isEmpty) continue;
    final loc = (error['loc'] is List ? error['loc'] as List : const [])
        .map((p) => '$p')
        .toList();
    if (loc.isNotEmpty && origins.contains(loc.first)) loc.removeAt(0);
    parts.add(loc.isEmpty ? msg : '${loc.join('.')}: $msg');
  }
  return parts.join('; ');
}
