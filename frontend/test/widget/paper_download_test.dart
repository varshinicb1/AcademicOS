// Paper and answer-key PDFs download with the session token (Task 604).
//
// The live release (a153003) opened "Open Paper in browser" and "Open Answer
// Key" with launchUrl on /papers/{id}/file. That route needs a bearer token
// and a browser tab carries none, so the teacher got a 401 page and the answer
// key could not be downloaded on the web at all. The review page now fetches
// the bytes through ApiClient on the shared Dio -- the production
// sessionInterceptor attaches the token -- and hands them to a PdfSaver (a
// blob download on the web).
//
// No mocking library (see pubspec.yaml): a real Dio carrying the real
// sessionInterceptor, then a recorder that answers instead of the network.
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'package:academicos/core/di/service_locator.dart';
import 'package:academicos/core/download/paper_download.dart';
import 'package:academicos/core/download/pdf_saver.dart';
import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/data/datasources/api/api_client.dart';

final _pdf = Uint8List.fromList('%PDF-1.4 fake paper'.codeUnits);

class _Recorder extends Interceptor {
  final requests = <RequestOptions>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    requests.add(options);
    final authed = options.headers['Authorization'] == 'Bearer tok_live_123';
    handler.resolve(Response(
      requestOptions: options,
      statusCode: authed ? 200 : 401,
      data: authed ? _pdf.toList() : const <int>[],
    ));
  }
}

class _FakeSaver implements PdfSaver {
  final saved = <(Uint8List, String)>[];
  @override
  Future<void> save(Uint8List bytes, String filename) async => saved.add((bytes, filename));
}

void main() {
  late Directory tmp;

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('paper_download_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  tearDownAll(() async {
    LocalStore.instance.clearAuth();
    await Hive.close();
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  (ApiClient, _Recorder) api() {
    final rec = _Recorder();
    final dio = Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))
      ..interceptors.add(sessionInterceptor())
      ..interceptors.add(rec);
    return (ApiClient(dio), rec);
  }

  test('the answer key is fetched with the bearer token and handed over as a download', () async {
    LocalStore.instance.authToken = 'tok_live_123';
    final (client, rec) = api();
    final saver = _FakeSaver();

    await downloadPaperPdf(client, saver, 'paper_abc', answerKey: true);

    expect(rec.requests, hasLength(1));
    final req = rec.requests.single;
    expect(req.method, 'GET');
    expect(req.path, '/papers/paper_abc/file');
    expect(req.queryParameters, {'format': 'answer-key'});
    expect(req.headers['Authorization'], 'Bearer tok_live_123');
    expect(req.responseType, ResponseType.bytes);

    expect(saver.saved, hasLength(1));
    expect(saver.saved.single.$1, _pdf);
    expect(saver.saved.single.$2, 'paper_abc_answer_key.pdf');
  });

  test('the paper itself downloads the same way, without the answer-key format', () async {
    LocalStore.instance.authToken = 'tok_live_123';
    final (client, rec) = api();
    final saver = _FakeSaver();

    await downloadPaperPdf(client, saver, 'paper_abc');

    expect(rec.requests.single.queryParameters, isEmpty);
    expect(rec.requests.single.headers['Authorization'], 'Bearer tok_live_123');
    expect(saver.saved.single.$2, 'paper_abc.pdf');
  });
}
