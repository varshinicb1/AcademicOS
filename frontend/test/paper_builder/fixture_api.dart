// The builder's fake API: a Dio adapter that answers each request with the
// response the real backend gave to the same request, captured in-process on
// a temp data root with the real served bank by
//
//   PYTHONPATH=src PYTHONIOENCODING=utf-8 python scripts/capture_paper_builder_fixtures.py
//
// (see fixtures/manifest.json for every request, its body and status). The
// real PaperBuilderApi parses these, so a field the server renames breaks
// here the way it would break in a browser. A request with no captured
// answer -- a scope nobody captured, a route the builder should not call --
// is answered 501 and recorded, never guessed at.
//
// The one thing not replayed byte for byte is the PDF body: the capture
// recorded its real size (56 KB paper, 49 KB key) and that it starts with
// "%PDF-"; the tests check that both downloads happen, not their pages.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import 'package:academicos/data/datasources/api/paper_builder_api.dart';

Map<String, dynamic> fixtureJson(String name) => Map<String, dynamic>.from(
    jsonDecode(File('test/paper_builder/fixtures/$name.json').readAsStringSync()) as Map);

List<Map<String, dynamic>> fixtureJsonList(String name) =>
    (_fixtureAny(name) as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();

/// The DioException Dio raises for a response with this status and body.
DioException dioError(Map<String, dynamic> body, int status) {
  final o = RequestOptions(path: '/');
  return DioException.badResponse(statusCode: status, requestOptions: o,
      response: Response(requestOptions: o, statusCode: status, data: body));
}

Object _fixtureAny(String name) =>
    jsonDecode(File('test/paper_builder/fixtures/$name.json').readAsStringSync()) as Object;

/// The teacher the fixtures were captured as (the templates they own say so).
String get fixtureTeacherId => fixtureJson('create_template_ok')['ownerId'] as String;

/// The chapter ids the half-yearly availability fixture was captured with.
List<String> get halfYearChapters =>
    List<String>.from((((_manifest()['responses'] as List).firstWhere((r) =>
        r['file'] == 'availability_10_science_half.json') as Map)['body'] as Map)['scope']['chapterIds'] as List);

Map<String, dynamic> _manifest() => fixtureJson('manifest');

class Recorded {
  final String method;
  final String path;
  final Map<String, dynamic> query;
  final Object? body;
  final int status;
  Recorded(this.method, this.path, this.query, this.body, this.status);
  @override
  String toString() => '$status $method $path ${body ?? ''}';
}

class FixtureAdapter implements HttpClientAdapter {
  final List<Recorded> requests = [];
  bool _created = false;

  static const _v1 = '/api/v1';

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final path = o.uri.path.startsWith(_v1) ? o.uri.path.substring(_v1.length) : o.uri.path;
    final body = o.data is String ? jsonDecode(o.data as String) : o.data;
    final (status, payload) = _answer(o.method, path, o.uri.queryParameters, body);
    requests.add(Recorded(o.method, path, o.uri.queryParameters, body, status));
    if (payload is Uint8List) {
      return ResponseBody.fromBytes(payload, status, headers: {
        Headers.contentTypeHeader: ['application/pdf'],
      });
    }
    return ResponseBody.fromString(jsonEncode(payload), status, headers: {
      Headers.contentTypeHeader: ['application/json'],
    });
  }

  (int, Object) _answer(String method, String path, Map<String, String> q, Object? body) {
    final scope = body is Map && body['scope'] is Map
        ? List<String>.from((body['scope'] as Map)['chapterIds'] as List? ?? const [])
        : const <String>[];
    bool sameScope(List<String> captured) =>
        scope.length == captured.length && scope.toSet().containsAll(captured);

    if (method == 'GET' && path.endsWith('/teacher-templates')) {
      if (q['grade'] == '10' && q['subject'] == 'Science') {
        return (200, fixtureJson(_created ? 'templates_10_science_after_create' : 'templates_10_science'));
      }
      if (q['grade'] == '7' && q['subject'] == 'Mathematics') return (200, fixtureJson('templates_7_maths'));
    }
    if (method == 'GET' && path == '/catalog/Science/10/chapters') return (200, _fixtureAny('chapters_10_science'));
    if (method == 'GET' && path == '/catalog/Mathematics/7/chapters') return (200, _fixtureAny('chapters_7_maths'));

    if (method == 'POST' && path.endsWith('/availability')) {
      final id = Uri.decodeComponent(path.split('/teacher-templates/').last.replaceAll('/availability', ''));
      if (id == 'preset:cbse:10:science:half_yearly') {
        if (scope.isEmpty) return (200, fixtureJson('availability_10_science_all'));
        if (sameScope(halfYearChapters)) return (200, fixtureJson('availability_10_science_half'));
      }
      if (id == 'preset:cbse:10:science:annual' && scope.isEmpty) {
        return (200, fixtureJson('availability_10_science_annual_all'));
      }
      if (id == 'preset:cbse:7:mathematics:unit_test') {
        if (scope.isEmpty) return (200, fixtureJson('availability_7_maths_all'));
        if (sameScope(const ['integers', 'fractions-and-decimals'])) {
          return (200, fixtureJson('availability_7_maths_two'));
        }
      }
      if (id == fixtureJson('create_template_ok')['id'] && scope.isEmpty) {
        return (200, fixtureJson('availability_created_all'));
      }
    }
    if (method == 'POST' && path == '/papers/generate-from-template' && body is Map) {
      // "Make another like this": captured with the questions of the paper
      // as the flow leaves it (swap, pick, remove) -- answered only when the
      // builder sends exactly that list.
      if (body['avoidQuestionIds'] != null) {
        final captured = ((_manifest()['responses'] as List)
            .firstWhere((r) => r['file'] == 'generate_10_science_another.json') as Map)['body'] as Map;
        final sent = List<String>.from(body['avoidQuestionIds'] as List);
        if (body['templateId'] == captured['templateId'] &&
            sent.join(',') == List<String>.from(captured['avoidQuestionIds'] as List).join(',')) {
          return (200, fixtureJson('generate_10_science_another'));
        }
        return (501, {'detail': 'no captured response for this avoidQuestionIds list'});
      }
      if (body['templateId'] == 'preset:cbse:10:science:half_yearly' && scope.isEmpty) {
        return (200, fixtureJson('generate_10_science'));
      }
      if (body['templateId'] == 'preset:cbse:7:mathematics:unit_test') {
        return (400, fixtureJson('generate_7_maths_refused'));
      }
    }
    if (method == 'POST' && path.endsWith('/teacher-templates') && body is Map) {
      final sum = (body['sections'] as List).fold<int>(0, (s, x) => s + (x['questionCount'] as int) * (x['marksEach'] as int));
      if (sum != body['totalMarks']) return (422, fixtureJson('create_template_mismatch'));
      _created = true;
      return (200, fixtureJson('create_template_ok'));
    }
    final paperId = fixtureJson('generate_10_science')['paper']['id'] as String;
    if (method == 'POST' && path == '/papers/$paperId/questions/1/swap') return (200, fixtureJson('swap_10_science'));
    if (method == 'POST' && path == '/papers/$paperId/questions/27') return (200, fixtureJson('pick_10_science'));
    final removed = fixtureJson('remove_10_science')['slot'] as String;
    if (method == 'DELETE' && path == '/papers/$paperId/questions/$removed') {
      return (200, fixtureJson('remove_10_science'));
    }
    if (method == 'GET' && path == '/papers/${paperId}_set_B') return (200, fixtureJson('paper_10_science_set_b'));
    if (method == 'POST' && path == '/questions/search') return (200, _fixtureAny('search_10_science_3m'));
    for (final (id, tag) in [(paperId, ''), ('${paperId}_set_B', '_set_b')]) {
      if (method == 'POST' && path == '/papers/$id/export/pdf') return (200, fixtureJson('export_10_science${tag}_pdf'));
      if (method == 'POST' && path == '/papers/$id/export/answer-key') {
        return (200, fixtureJson('export_10_science${tag}_answer_key'));
      }
      if (method == 'GET' && path == '/papers/$id/file') {
        return (200, Uint8List.fromList(utf8.encode('%PDF-1.4 $id ${q['format'] ?? 'paper'}')));
      }
    }
    return (501, {'detail': 'no captured response for $method $path'});
  }

  @override
  void close({bool force = false}) {}
}

/// The real [PaperBuilderApi] talking to [adapter].
///
/// Typed as the Dio interface, not [FixtureAdapter]: the error tests
/// (builder_errors_test.dart) wrap the fixtures in an adapter that refuses
/// chosen routes, and it is the same real client that has to parse the
/// refusal.
///
/// [interceptors] are added in order, as service_locator.dart adds them to
/// the app's Dio. The default is none, because most tests are about what a
/// step shows and an interceptor only adds noise -- but a test about a 401
/// must pass the real `sessionInterceptor()`: without it, the builder's 401
/// branch would read the same in a build where the interceptor had been
/// dropped and the teacher was left on a dead screen.
PaperBuilderApi fixtureApi(HttpClientAdapter adapter,
    {List<Interceptor> interceptors = const []}) {
  // SyncTransformer: Dio's default decodes large JSON (the 170 KB generated
  // paper) on a background isolate, which a widget test's fake clock never
  // waits for -- the spinner would spin until pumpAndSettle times out.
  final dio = Dio(BaseOptions(baseUrl: 'http://fixture.test/api/v1'))
    ..httpClientAdapter = adapter
    ..transformer = SyncTransformer();
  dio.interceptors.addAll(interceptors);
  return PaperBuilderApi(dio);
}
