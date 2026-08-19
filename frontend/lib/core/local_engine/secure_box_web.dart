import 'dart:convert';
import 'dart:html' as html;

import 'package:hive_flutter/hive_flutter.dart';

/// Web key storage: `path_provider`'s `getApplicationSupportDirectory()` and
/// `dart:io`'s `File` have no web implementation -- calling either crashed
/// the entire app on startup before any UI rendered (MissingPluginException
/// from path_provider's platform channel, confirmed via a real browser
/// console check against the deployed build). Browser `localStorage` is the
/// real, standard, already-origin-sandboxed equivalent on web: each site's
/// storage is isolated by the browser itself, matching the same "private to
/// this app, not readable by others" property the native file gave.
Future<List<int>> getOrCreateSecureKey(String keyFileName) async {
  final existing = html.window.localStorage[keyFileName];
  if (existing != null) {
    return base64Decode(existing);
  }
  final key = Hive.generateSecureKey();
  html.window.localStorage[keyFileName] = base64Encode(key);
  return key;
}
