// Proves corpus_downloader.dart's real behavior: checksum acceptance and
// rejection, malformed-JSON rejection, network-failure fallback, and that
// two concurrent downloads don't corrupt state (same KeyedMutex proof
// pattern as keyed_mutex_test.dart). All HTTP is faked -- zero real
// network calls, this runs with no server and no internet.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:academicos/core/local_engine/corpus_downloader.dart';

/// Serves canned bytes for exact URL matches; anything else 404s. Good
/// enough for this downloader's two-request shape (hash, then file).
class _FakeAdapter implements HttpClientAdapter {
  final Map<String, List<int>> responses;
  final Map<String, int> statusCodes;
  final Exception? throwOn;
  int callCount = 0;

  _FakeAdapter(this.responses, {this.statusCodes = const {}, this.throwOn});

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
      RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    callCount++;
    if (throwOn != null) throw throwOn!;
    final url = options.uri.toString();
    final body = responses[url];
    if (body == null) {
      return ResponseBody.fromBytes(utf8.encode('not found'), 404);
    }
    return ResponseBody.fromBytes(body, statusCodes[url] ?? 200, headers: {
      Headers.contentLengthHeader: ['${body.length}'],
    });
  }
}

Dio _dioWith(Map<String, List<int>> responses, {Map<String, int> statusCodes = const {}}) {
  final dio = Dio();
  dio.httpClientAdapter = _FakeAdapter(responses, statusCodes: statusCodes);
  return dio;
}

const _base = 'https://fake.test/corpus';

List<int> _validCorpusBytes() => utf8.encode(jsonEncode({
      'questions': [
        {'id': 'q1', 'subject': 'Science'}
      ],
      'exportedCount': 1,
    }));

void main() {
  late Directory tmpDir;

  setUp(() {
    tmpDir = Directory.systemTemp.createTempSync('corpus_dl_test_');
    CorpusDownloader.debugDirectoryOverride = tmpDir;
  });

  tearDown(() {
    CorpusDownloader.debugDirectoryOverride = null;
    tmpDir.deleteSync(recursive: true);
  });

  test('valid download with matching checksum is accepted and persisted', () async {
    final bytes = _validCorpusBytes();
    final hash = sha256.convert(bytes).toString();
    final dio = _dioWith({
      '$_base/questions.json.sha256': utf8.encode(hash),
      '$_base/questions.json': bytes,
    });

    final result = await CorpusDownloader.download(dio: dio, baseUrl: _base);

    expect(result.success, isTrue);
    expect(result.byteSize, bytes.length);

    final accepted = await CorpusDownloader.currentDownloadedFile();
    expect(accepted, isNotNull);
    expect(await accepted!.readAsBytes(), bytes);
  });

  test('checksum mismatch is rejected -- corrupted data never replaces good data', () async {
    final bytes = _validCorpusBytes();
    final wrongHash = sha256.convert(utf8.encode('not the real content')).toString();
    final dio = _dioWith({
      '$_base/questions.json.sha256': utf8.encode(wrongHash),
      '$_base/questions.json': bytes,
    });

    final result = await CorpusDownloader.download(dio: dio, baseUrl: _base);

    expect(result.success, isFalse);
    expect(result.error, contains('checksum mismatch'));
    expect(await CorpusDownloader.currentDownloadedFile(), isNull);
  });

  test('malformed JSON that still matches its own checksum is rejected', () async {
    final bytes = utf8.encode('not valid json at all');
    final hash = sha256.convert(bytes).toString();
    final dio = _dioWith({
      '$_base/questions.json.sha256': utf8.encode(hash),
      '$_base/questions.json': bytes,
    });

    final result = await CorpusDownloader.download(dio: dio, baseUrl: _base);

    expect(result.success, isFalse);
    expect(result.error, contains('not valid JSON'));
  });

  test('a prior good download is untouched after a later failed download', () async {
    final goodBytes = _validCorpusBytes();
    final goodHash = sha256.convert(goodBytes).toString();
    final goodDio = _dioWith({
      '$_base/questions.json.sha256': utf8.encode(goodHash),
      '$_base/questions.json': goodBytes,
    });
    final first = await CorpusDownloader.download(dio: goodDio, baseUrl: _base);
    expect(first.success, isTrue);

    final badDio = _dioWith({
      '$_base/questions.json.sha256': utf8.encode('bad'),
    }); // no questions.json entry -> 404 on the file fetch
    final second = await CorpusDownloader.download(dio: badDio, baseUrl: _base);
    expect(second.success, isFalse);

    final stillAccepted = await CorpusDownloader.currentDownloadedFile();
    expect(stillAccepted, isNotNull);
    expect(await stillAccepted!.readAsBytes(), goodBytes,
        reason: 'a failed download must never touch the previously-accepted file');
  });

  test('network failure returns a clean result, never throws', () async {
    final dio = Dio()..httpClientAdapter = _FakeAdapter({}, throwOn: Exception('no network'));

    final result = await CorpusDownloader.download(dio: dio, baseUrl: _base);

    expect(result.success, isFalse);
    expect(result.error, isNotNull);
  });

  test('two concurrent downloads for the same corpus are serialized, not racing', () async {
    final bytes = _validCorpusBytes();
    final hash = sha256.convert(bytes).toString();
    final dio = _dioWith({
      '$_base/questions.json.sha256': utf8.encode(hash),
      '$_base/questions.json': bytes,
    });

    final results = await Future.wait([
      CorpusDownloader.download(dio: dio, baseUrl: _base),
      CorpusDownloader.download(dio: dio, baseUrl: _base),
    ]);

    expect(results.every((r) => r.success), isTrue);
    final accepted = await CorpusDownloader.currentDownloadedFile();
    expect(await accepted!.readAsBytes(), bytes, reason: 'file must end up fully intact, not interleaved/corrupted');
  });
}
