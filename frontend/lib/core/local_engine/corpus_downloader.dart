/// Downloads a fresher CBSE corpus after install, from a real, public,
/// free host: a GitHub Release on the dedicated public data repo
/// varshinicb1/academicos-cbse-data (no app source code there, just data --
/// AcademicOS itself is private, so its own release assets 404 for an
/// unauthenticated download, confirmed live before choosing this repo).
///
/// The bundled asset (assets/corpus/questions.json, baked into the APK at
/// build time) is always the fallback -- this never needs to succeed for
/// the app to work. A corrupted or interrupted download must never replace
/// good data with bad: every download is checksum-verified against a
/// published .sha256 before being accepted, written to a .tmp path and
/// renamed only after full verified success, and two concurrent download
/// calls are serialized through the same KeyedMutex pattern
/// local_scan_engine.dart already uses for its own concurrency safety.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

import 'keyed_mutex.dart';

const corpusDownloadBaseUrl =
    'https://github.com/varshinicb1/academicos-cbse-data/releases/download/corpus-data';
const _lockKey = 'corpus_download';

class CorpusDownloadProgress {
  final int received;
  final int total;
  double get fraction => total > 0 ? received / total : 0;
  const CorpusDownloadProgress(this.received, this.total);
}

class CorpusDownloadResult {
  final bool success;
  final String? error;
  final int? byteSize;
  const CorpusDownloadResult({required this.success, this.error, this.byteSize});
}

class CorpusDownloader {
  static final KeyedMutex _mutex = KeyedMutex();

  /// Overridable in tests (getApplicationSupportDirectory needs a real
  /// platform channel path_provider has no plugin for in plain `flutter
  /// test`) -- production callers never set this.
  static Directory? debugDirectoryOverride;

  static Future<File> _targetFile() async {
    final dir = debugDirectoryOverride ?? await getApplicationSupportDirectory();
    return File('${dir.path}/corpus_downloaded.json');
  }

  /// The currently-accepted downloaded corpus, if one exists and still
  /// passes its own checksum re-verification (a corrupted local file must
  /// never be trusted, even if it was good when written -- disk corruption,
  /// a killed write mid-rename, etc.). Returns null if none, falling back
  /// to the bundled asset is the caller's job (corpus_repository.dart).
  static Future<File?> currentDownloadedFile() async {
    final file = await _targetFile();
    final hashFile = File('${file.path}.sha256');
    if (!await file.exists() || !await hashFile.exists()) return null;
    final expected = (await hashFile.readAsString()).trim().toLowerCase();
    final actual = sha256.convert(await file.readAsBytes()).toString();
    if (actual != expected) return null;
    return file;
  }

  /// [dio] and [baseUrl] are test seams -- production callers never pass
  /// them, real calls always go to the real corpusDownloadBaseUrl with a
  /// real Dio instance.
  static Future<CorpusDownloadResult> download({
    void Function(CorpusDownloadProgress)? onProgress,
    Dio? dio,
    String? baseUrl,
  }) =>
      _mutex.synchronized(_lockKey, () => _downloadUnlocked(onProgress, dio, baseUrl));

  static Future<CorpusDownloadResult> _downloadUnlocked(
    void Function(CorpusDownloadProgress)? onProgress,
    Dio? injectedDio,
    String? injectedBaseUrl,
  ) async {
    final dio = injectedDio ?? Dio(BaseOptions(connectTimeout: const Duration(seconds: 20)));
    final base = injectedBaseUrl ?? corpusDownloadBaseUrl;
    try {
      final hashResp = await dio.get<String>(
        '$base/questions.json.sha256',
        options: Options(responseType: ResponseType.plain),
      );
      final expectedHash = (hashResp.data ?? '').trim().toLowerCase();
      if (!RegExp(r'^[0-9a-f]{64}$').hasMatch(expectedHash)) {
        return const CorpusDownloadResult(success: false, error: 'published checksum looks malformed');
      }

      final target = await _targetFile();
      final tmpFile = File('${target.path}.tmp');
      final bytesBuilder = BytesBuilder(copy: false);

      final response = await dio.get<ResponseBody>(
        '$base/questions.json',
        options: Options(responseType: ResponseType.stream),
        onReceiveProgress: (received, total) {
          if (onProgress != null) onProgress(CorpusDownloadProgress(received, total));
        },
      );
      final stream = response.data!.stream;
      await for (final chunk in stream) {
        bytesBuilder.add(chunk);
      }
      final bytes = bytesBuilder.takeBytes();

      final actualHash = sha256.convert(bytes).toString();
      if (actualHash != expectedHash) {
        return CorpusDownloadResult(
          success: false,
          error: 'checksum mismatch (expected $expectedHash, got $actualHash) -- '
              'download was corrupted or incomplete, keeping existing data',
        );
      }

      // Validate it actually parses as the expected shape before accepting
      // it -- a byte-for-byte-correct-but-malformed file (e.g. an upstream
      // publishing mistake) must not silently replace working data either.
      try {
        final decoded = jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>;
        if (decoded['questions'] is! List || (decoded['questions'] as List).isEmpty) {
          return const CorpusDownloadResult(
              success: false, error: 'downloaded file has no questions -- keeping existing data');
        }
      } catch (e) {
        return CorpusDownloadResult(
            success: false, error: 'downloaded file is not valid JSON: $e -- keeping existing data');
      }

      await tmpFile.writeAsBytes(bytes, flush: true);
      await tmpFile.rename(target.path);
      await File('${target.path}.sha256').writeAsString(actualHash, flush: true);

      return CorpusDownloadResult(success: true, byteSize: bytes.length);
    } on DioException catch (e) {
      return CorpusDownloadResult(success: false, error: 'network error: ${e.message}');
    } catch (e) {
      return CorpusDownloadResult(success: false, error: 'unexpected error: $e');
    }
  }
}
