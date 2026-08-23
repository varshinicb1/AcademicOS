/// Optional, opt-in accuracy upgrade over on_device_ocr.dart's ML Kit
/// default: Sarvam Vision (assessment/vision.py's real, working
/// doc-digitization API), a VLM-based OCR engine genuinely stronger on real
/// handwriting than a lightweight on-device model. Requires internet and
/// the teacher's own Sarvam API key (Settings) -- same BYOK pattern
/// llm/sarvam.py's SarvamLLM already uses. Never the default: this is a
/// batch job API (create -> upload -> poll -> download a ZIP), not a
/// synchronous per-page call, so it only runs once at "process session"
/// time over all captured pages, not per-capture the way ML Kit does.
///
/// Ported from vision.py's real job pipeline and its two learned fixes:
/// hallucination scrubbing (a VLM asked to OCR a blank margin sometimes
/// narrates about "historical Indic scripts" instead of returning nothing)
/// and treating any transport/API failure as "not available", never a
/// crash -- the caller always has the already-captured ML Kit text to fall
/// back to.
///
/// Scoped down from vision.py's 3-pass majority-vote per page: one real
/// pass per page here, not three, to keep a mobile "process this booklet"
/// step to a reasonable time/data budget on the teacher's own connection.
/// A real accuracy/cost tradeoff, not an oversight -- worth revisiting if
/// single-pass accuracy turns out insufficient in practice.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:archive/archive.dart';
import 'package:dio/dio.dart';

class SarvamVisionResult {
  final String text;
  final bool hallucinationStripped;
  SarvamVisionResult({required this.text, required this.hallucinationStripped});
}

class SarvamVisionUnavailable implements Exception {
  final String reason;
  SarvamVisionUnavailable(this.reason);
  @override
  String toString() => reason;
}

const _baseUrl = 'https://api.sarvam.ai/doc-digitization/job/v1';
const _pollIntervalSec = 5;
const _pollMaxAttempts = 36; // 3 minutes -- a mobile session shouldn't hang longer than that

final _hallucinationMarkers = [
  'i am an expert ocr engine',
  'i cannot perform the requested task',
  'does not contain any human-readable text',
  'the provided image is a qr code',
  'as an ai language model',
];

bool _looksHallucinated(String text) {
  final low = text.toLowerCase();
  return _hallucinationMarkers.any((m) => low.contains(m));
}

(String, bool) _stripHallucinations(String text) {
  final blocks = text.split('\n\n');
  final kept = <String>[];
  var found = false;
  for (final b in blocks) {
    if (_looksHallucinated(b)) {
      found = true;
      continue;
    }
    kept.add(b);
  }
  return (kept.join('\n\n').trim(), found);
}

class SarvamVisionOcr {
  final Dio _dio;
  final String apiKey;
  SarvamVisionOcr(this.apiKey) : _dio = Dio(BaseOptions(connectTimeout: const Duration(seconds: 20)));

  /// OCRs one page image via a real Sarvam Vision job. Throws
  /// SarvamVisionUnavailable on ANY failure (no network, bad key, timeout,
  /// API error) -- callers must catch this and fall back to the
  /// already-captured on-device OCR text, never propagate it as a hard error.
  Future<SarvamVisionResult> ocrPage(String imagePath, {String language = 'en-IN'}) async {
    if (apiKey.trim().isEmpty) {
      throw SarvamVisionUnavailable('no Sarvam API key configured');
    }
    final headers = {'api-subscription-key': apiKey};
    final jsonHeaders = {...headers, 'Content-Type': 'application/json'};

    try {
      final createResp = await _dio.post(_baseUrl,
          options: Options(headers: jsonHeaders),
          data: {'job_parameters': {'language': language, 'output_format': 'md'}});
      final jobId = createResp.data['job_id'] as String;

      final fileName = imagePath.split(RegExp(r'[\\/]')).last;
      final uploadResp = await _dio.post('$_baseUrl/upload-files',
          options: Options(headers: jsonHeaders),
          data: {'job_id': jobId, 'files': [fileName]});
      final putUrl = _firstUploadUrl(uploadResp.data as Map<String, dynamic>, fileName);

      final bytes = await File(imagePath).readAsBytes();
      await _dio.put(putUrl,
          options: Options(headers: {'x-ms-blob-type': 'BlockBlob'}), data: Stream.fromIterable([bytes]));

      await _dio.post('$_baseUrl/$jobId/start', options: Options(headers: jsonHeaders), data: {});

      for (var attempt = 0; attempt < _pollMaxAttempts; attempt++) {
        await Future.delayed(const Duration(seconds: _pollIntervalSec));
        final statusResp = await _dio.get('$_baseUrl/$jobId/status', options: Options(headers: headers));
        final state = (statusResp.data['job_state'] as String? ?? '').toLowerCase();
        if (state == 'completed' || state == 'succeeded' || state == 'success') {
          final raw = await _downloadText(jobId, headers, jsonHeaders);
          final (cleaned, stripped) = _stripHallucinations(raw);
          return SarvamVisionResult(text: cleaned, hallucinationStripped: stripped);
        }
        if (state == 'failed' || state == 'error') {
          throw SarvamVisionUnavailable('vision job $jobId failed: ${statusResp.data['error_message']}');
        }
      }
      throw SarvamVisionUnavailable('vision job $jobId timed out');
    } on SarvamVisionUnavailable {
      rethrow;
    } catch (e) {
      throw SarvamVisionUnavailable('Sarvam Vision unavailable: $e');
    }
  }

  String _firstUploadUrl(Map<String, dynamic> payload, String fname) {
    final urls = payload['upload_urls'] ?? payload['files'] ?? {};
    dynamic entry;
    if (urls is Map) {
      entry = urls[fname] ?? (urls.isNotEmpty ? urls.values.first : null);
    } else if (urls is List && urls.isNotEmpty) {
      entry = urls.first;
    }
    if (entry == null) throw SarvamVisionUnavailable('no upload url in response');
    if (entry is String) return entry;
    final url = entry['file_url'] ?? entry['url'] ?? entry['upload_url'];
    if (url == null) throw SarvamVisionUnavailable('could not read upload url');
    return url as String;
  }

  Future<String> _downloadText(String jobId, Map<String, String> headers, Map<String, String> jsonHeaders) async {
    final resp = await _dio.post('$_baseUrl/$jobId/download-files',
        options: Options(headers: jsonHeaders), data: {'job_id': jobId});
    final downloads = resp.data['download_urls'] as Map<String, dynamic>? ?? {};
    if (downloads.isEmpty) throw SarvamVisionUnavailable('no download urls returned');
    final entry = downloads.values.first;
    final url = entry is Map ? (entry['file_url'] as String) : entry as String;

    final fileResp = await _dio.get<List<int>>(url, options: Options(responseType: ResponseType.bytes));
    final archive = ZipDecoder().decodeBytes(Uint8List.fromList(fileResp.data!));
    final parts = <String>[];
    for (final file in archive.files) {
      if (file.isFile &&
          (file.name.endsWith('.md') || file.name.endsWith('.txt') || file.name.endsWith('.html'))) {
        parts.add(utf8.decode(file.content as List<int>, allowMalformed: true));
      }
    }
    return parts.join('\n\n').trim();
  }
}
