import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../core/local_engine/local_store.dart';
import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';

/// Thin calls to the school-operations API (homework, progress, parents,
/// cover, exams, notifications, admin tools). The shared Dio already carries
/// the base URL (`.../api/v1`) and the session token, so paths here are
/// relative to it. Every failure becomes an [OpsError] whose message is the
/// server's own `detail`, which is written for the person using the app.
class Ops {
  Ops._();

  static Dio get _dio => GetIt.I<Dio>();

  /// When the last read was answered from this device's saved copy because
  /// the server could not be reached; null when the last read was live.
  static final ValueNotifier<DateTime?> offlineSince = ValueNotifier(null);

  /// A read. Its answer is saved on the device, per signed-in user; when the
  /// server cannot be reached at all, the saved answer is returned instead
  /// (TA-8, SA-8: a phone without signal still shows today's timetable,
  /// homework and progress). Writes are never answered from the cache.
  static Future<dynamic> get(String path, {Map<String, dynamic>? query}) {
    final key = _cacheKey(path, query);
    return _reading.putIfAbsent(key, () => _fetchAndSave(path, query, key).whenComplete(() {
          // A block, not `=> remove(key)`: remove returns this very future, and whenComplete waits
          // for whatever its callback returns, so the read would wait on itself for ever.
          _reading.remove(key);
        }));
  }

  /// The reads under way, by what they ask. Two widgets asking for the same page in the same
  /// moment (the School page and the checklist card both ask for setup-status; a page and its
  /// header both ask for the profile) share one request instead of sending two. Any write
  /// empties it first, so a read that follows a change never joins a read that began before it.
  static final Map<String, Future<dynamic>> _reading = {};

  static Future<dynamic> _fetchAndSave(String path, Map<String, dynamic>? query, String key) async {
    try {
      final data = await _call(() => _dio.get(path, queryParameters: query));
      _save(key, data);
      offlineSince.value = null;
      if (pending.value > 0) syncNow();       // the connection is back: send what waited
      return data;
    } on OpsError catch (e) {
      if (e.status != null) rethrow;          // the server answered: a real refusal, not "offline"
      final saved = _load(key);
      if (saved == null) rethrow;
      offlineSince.value = DateTime.tryParse(saved['at'] as String? ?? '');
      return saved['data'];
    }
  }

  static String _cacheKey(String path, Map<String, dynamic>? query) {
    final q = (query ?? const {}).entries.map((e) => '${e.key}=${e.value}').toList()..sort();
    return 'ops_cache:$_who:$path?${q.join('&')}';
  }

  /// Whose saved copies and waiting changes these are: the signed-in user,
  /// and for an owner (ROLE-4) the school it is acting in too. An owner is
  /// one user id across several schools, so keyed by the id alone one
  /// school's saved page would be shown, offline, inside another, and a
  /// change made in one would be sent to the other after a switch.
  static String get _who =>
      CurrentSession.isOwner ? '${CurrentSession.userId}@${CurrentSession.schoolId}' : CurrentSession.userId;

  static void _save(String key, dynamic data) {
    if (data is! Map && data is! List) return;   // text (CSV, calendars) is not worth keeping offline
    try {
      LocalStore.instance.box.put(key, jsonEncode({'at': DateTime.now().toIso8601String(), 'data': data}));
    } catch (_) {
      // not-a-failure: the live answer is already in hand; only its offline copy was not kept
    }
  }

  static Map<String, dynamic>? _load(String key) {
    final raw = LocalStore.instance.box.get(key);
    return raw is String ? Map<String, dynamic>.from(jsonDecode(raw) as Map) : null;
  }

  static Future<dynamic> post(String path, {Object? body, Map<String, dynamic>? query}) =>
      _change(() => _dio.post(path, data: body, queryParameters: query));

  static Future<dynamic> put(String path, {Object? body, Map<String, dynamic>? query}) =>
      _change(() => _dio.put(path, data: body, queryParameters: query));

  static Future<dynamic> patch(String path, {Object? body}) => _change(() => _dio.patch(path, data: body));

  static Future<dynamic> delete(String path) => _change(() => _dio.delete(path));

  static Future<dynamic> _change(Future<Response<dynamic>> Function() send) {
    // Cleared when the write is sent and again when it ends: a read started
    // while the write was in flight may hold what was there before it, and a
    // reload right after `await post(...)` must not join that read.
    _reading.clear();
    return _call(send).whenComplete(_reading.clear);
  }

  static Future<List<Map<String, dynamic>>> list(String path, {Map<String, dynamic>? query}) async {
    final data = await get(path, query: query);
    return (data as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Future<Map<String, dynamic>> map(String path, {Map<String, dynamic>? query}) async =>
      Map<String, dynamic>.from(await get(path, query: query) as Map);

  /// A file the server builds (an Excel workbook, a PDF), fetched with the
  /// session token -- a bare link would reach the route without it. Never
  /// answered from the offline copy.
  static Future<Uint8List> bytes(String path, {Map<String, dynamic>? query}) async {
    final data = await _call(() => _dio.get<List<int>>(path, queryParameters: query,
        options: Options(responseType: ResponseType.bytes)));
    return Uint8List.fromList(data as List<int>);
  }

  static Future<dynamic> _call(Future<Response<dynamic>> Function() send) async {
    try {
      return (await send()).data;
    } on DioException catch (e) {
      throw OpsError.from(e);
    }
  }

  // ---------------------------------------------------------------- queued writes (TA-8)

  /// How many changes are waiting on this phone to be sent.
  static final ValueNotifier<int> pending = ValueNotifier(0);

  /// Changes the server refused when they were finally sent, with its reason,
  /// kept until the person has seen them.
  static final ValueNotifier<List<Map<String, dynamic>>> refused = ValueNotifier(const []);

  /// Why the last attempt to send could not finish (not a refusal: the
  /// phone's own storage, say); null when it did.
  static final ValueNotifier<String?> syncProblem = ValueNotifier(null);

  static bool _flushing = false;

  /// Send what waits without holding up the caller; a failure is shown in
  /// the banner, not dropped.
  static void syncNow() {
    flush().then((_) => syncProblem.value = null,
        onError: (Object e) => syncProblem.value = serverErrorMessage(e));
  }

  /// A write that may wait: sent now when the server can be reached; with no
  /// connection at all it is kept on this phone, per signed-in user, and
  /// [OpsQueued] is thrown so the screen can say so. Only for writes that
  /// mean the same thing when sent later -- marking a lesson taught, saving
  /// marks, handing in answers, answering a cover request, reading a
  /// notification -- never for one whose time is the point (checking in).
  /// A later change to the same thing replaces the waiting one.
  static Future<dynamic> send(String method, String path,
      {Object? body, Map<String, dynamic>? query, required String label}) async {
    _reading.clear();
    try {
      final data = await _call(() => _dio.request(path, data: body, queryParameters: query,
          options: Options(method: method))).whenComplete(_reading.clear);
      if (pending.value > 0) syncNow();
      return data;
    } on OpsError catch (e) {
      if (e.status != null) rethrow;               // the server answered: a real refusal
      _enqueue({'method': method, 'path': path, 'body': body, 'query': query, 'label': label,
          'at': DateTime.now().toIso8601String()});
      throw OpsQueued(label);
    }
  }

  static String get _queueKey => 'ops_queue:$_who';
  static String get _refusedKey => 'ops_refused:$_who';

  static List<Map<String, dynamic>> _read(String key) {
    final raw = LocalStore.instance.box.get(key);
    if (raw is! String) return [];
    return (jsonDecode(raw) as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static void _write(String key, List<Map<String, dynamic>> items) =>
      LocalStore.instance.box.put(key, jsonEncode(items));

  static String _sameThing(Map item) => '${item['method']} ${item['path']} ${jsonEncode(item['query'])}';

  static void _enqueue(Map<String, dynamic> item) {
    final queue = _read(_queueKey)..removeWhere((q) => _sameThing(q) == _sameThing(item));
    _write(_queueKey, queue..add(item));
    pending.value = queue.length;
  }

  /// Load this user's waiting and refused changes (on start, after sign-in)
  /// and try to send what waits.
  static void loadSyncState() {
    try {
      pending.value = _read(_queueKey).length;
      refused.value = _read(_refusedKey);
    } catch (_) {
      // not-a-failure: before the local store opens (tests, first frame) nothing can be waiting
      return;
    }
    if (pending.value > 0) syncNow();
  }

  /// Send what is waiting, oldest first. It stops at the first change that
  /// still cannot reach the server (or meets a server error, 5xx), so order
  /// is kept; a change the server refuses (4xx) moves to [refused] with the
  /// server's reason, and the rest carry on.
  static Future<void> flush() async {
    if (_flushing) return;
    _flushing = true;
    try {
      var queue = _read(_queueKey);
      final refusedNow = _read(_refusedKey);
      while (queue.isNotEmpty) {
        final item = queue.first;
        try {
          await _call(() => _dio.request(item['path'] as String, data: item['body'],
              queryParameters: (item['query'] as Map?)?.cast<String, dynamic>(),
              options: Options(method: item['method'] as String)));
        } on OpsError catch (e) {
          if (e.status == null || e.status! >= 500) break;     // still offline, or try again later
          refusedNow.add({...item, 'reason': serverErrorMessage(e)});
        }
        queue = queue.sublist(1);
        _write(_queueKey, queue);
      }
      _write(_refusedKey, refusedNow);
      pending.value = queue.length;
      refused.value = refusedNow;
    } finally {
      _flushing = false;
    }
  }

  /// The person has read why a change was refused.
  static void clearRefused() {
    _write(_refusedKey, const []);
    refused.value = const [];
  }
}

/// A write kept on this phone to be sent when the connection is back; its
/// message is what the screen shows.
class OpsQueued extends OpsError {
  final String label;
  OpsQueued(this.label)
      : super(null, 'No connection: "$label" is saved on this phone and will be sent when you are back online.');
}

class OpsError implements Exception {
  final int? status;
  final String message;

  /// The server's whole `detail`, when it said more than one sentence: a
  /// timetable 409 carries `{message, clashes: [...]}`, every clash named.
  final Object? detail;
  OpsError(this.status, this.message, {this.detail});

  factory OpsError.from(DioException e) {
    var data = e.response?.data;
    // A file download (Ops.bytes) gets its error body as bytes too; the
    // server's sentence is JSON inside them.
    if (data is List<int>) {
      try {
        data = jsonDecode(utf8.decode(data));
      } on FormatException {
        data = null; // not-a-failure: not JSON, so the generic sentence below
      }
    }
    // With no sentence from the server: the connection only when nothing
    // answered; a 500 or a bare 403 says what it was (serverErrorMessage).
    String msg = e.response == null
        ? 'Something went wrong. Check your connection and try again.'
        : serverErrorMessage(e);
    Object? detail;
    if (data is Map && data['detail'] != null) {
      final d = data['detail'];
      detail = d;
      if (d is String) {
        msg = d;
      } else if (d is Map && d['message'] != null) {
        msg = d['message'].toString();
      } else if (d is List && d.isNotEmpty && d.first is Map) {
        msg = (d.first as Map)['msg']?.toString() ?? msg;
      }
    }
    // 501 is a feature not switched on yet: "Coming soon", not an error (api_error.dart).
    if (e.response?.statusCode == 501) {
      msg = comingSoonMessage(code: data is Map ? data['code'] as String? : null, detail: detail is String ? detail : null);
    }
    return OpsError(e.response?.statusCode, msg, detail: detail);
  }

  /// Every problem the server listed with its refusal (`detail.clashes`);
  /// empty when it gave one sentence.
  List<String> get clashes {
    final d = detail;
    if (d is Map && d['clashes'] is List) return [for (final c in d['clashes'] as List) '$c'];
    return const [];
  }

  @override
  String toString() => message;
}

/// "2026-06-03" from a DateTime, the school's own calendar date.
String isoDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// "Offline: showing what was saved at 09:12" while reads come from the
/// device's saved copies; "2 changes waiting to send" while writes wait
/// (TA-8: a clear sync state); and any change the school refused when it
/// was finally sent, with the reason.
class OfflineBanner extends StatefulWidget {
  const OfflineBanner({super.key});

  @override
  State<OfflineBanner> createState() => _OfflineBannerState();
}

class _OfflineBannerState extends State<OfflineBanner> {
  @override
  void initState() {
    super.initState();
    Ops.loadSyncState();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([Ops.offlineSince, Ops.pending, Ops.refused, Ops.syncProblem]),
      builder: (context, _) {
        final at = Ops.offlineSince.value;
        final waiting = Ops.pending.value;
        final refused = Ops.refused.value;
        final hhmm = at == null
            ? ''
            : '${at.toLocal().hour.toString().padLeft(2, '0')}:${at.toLocal().minute.toString().padLeft(2, '0')}';
        return Column(mainAxisSize: MainAxisSize.min, children: [
          if (at != null)
            MaterialBanner(
              leading: const Icon(Icons.cloud_off),
              content: Text('Offline: showing what was saved at $hhmm on ${at.toLocal().day}/${at.toLocal().month}. '
                  'Changes wait on this phone until you are back online.'),
              actions: [TextButton(onPressed: () => Ops.offlineSince.value = null, child: const Text('OK'))],
            ),
          if (waiting > 0)
            MaterialBanner(
              leading: const Icon(Icons.cloud_upload_outlined),
              content: Text((waiting == 1 ? '1 change is waiting to be sent.' : '$waiting changes are waiting to be sent.') +
                  (Ops.syncProblem.value == null ? '' : ' The last try did not finish: ${Ops.syncProblem.value}')),
              actions: const [TextButton(onPressed: Ops.syncNow, child: Text('Send now'))],
            ),
          if (refused.isNotEmpty)
            MaterialBanner(
              leading: Icon(Icons.error_outline, color: Theme.of(context).colorScheme.error),
              content: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(refused.length == 1
                    ? 'The school did not accept a change made offline:'
                    : 'The school did not accept ${refused.length} changes made offline:'),
                for (final r in refused) Text('• ${r['label']}: ${r['reason']}'),
              ]),
              actions: const [TextButton(onPressed: Ops.clearRefused, child: Text('Got it'))],
            ),
        ]);
      },
    );
  }
}
