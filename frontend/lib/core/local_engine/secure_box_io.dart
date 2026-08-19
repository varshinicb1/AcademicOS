import 'dart:convert';
import 'dart:io';

import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart';

/// Native (Windows/Android/desktop) key storage: a file in the app's own
/// private data directory. See secure_box.dart for the full rationale.
Future<List<int>> getOrCreateSecureKey(String keyFileName) async {
  final dir = await getApplicationSupportDirectory();
  final file = File('${dir.path}${Platform.pathSeparator}$keyFileName');
  if (await file.exists()) {
    final raw = await file.readAsString();
    return base64Decode(raw);
  }
  final key = Hive.generateSecureKey();
  await dir.create(recursive: true);
  await file.writeAsString(base64Encode(key));
  return key;
}
