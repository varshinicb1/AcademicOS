// Question-bank API keys and their webhooks are the operator's (ours), not a school's. No
// role's navigation offers them, no page asks a teacher for a key, and no screen tells a
// teacher to edit a server file.
import 'dart:io';

import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('no role sees API keys in its navigation', () {
    for (final role in ['principal', 'teacher', 'student', 'parent', '']) {
      final labels = [for (final i in navItemsFor(role)) i.label.toLowerCase()];
      expect(labels.where((l) => l.contains('api')), isEmpty, reason: role);
    }
    final granted = [for (final i in navItemsFor('teacher', grants: {'users', 'leave', 'exams', 'qbank_review'})) i.label.toLowerCase()];
    expect(granted.where((l) => l.contains('api')), isEmpty, reason: 'even a teacher with admin grants');
  });

  test('no screen asks for, lists or explains an API key', () {
    // What a person reads on screen. The local store's own field and the offline OCR engine's
    // key plumbing are code, not a screen, and are not scanned for.
    const forbidden = [
      "tr('API keys')",
      'Sarvam API Key',
      'COMPOSIO_API_KEY',
      'secrets.env',
      'New API key',
      'X-API-Key',
      'ApiKeysPage',
      'WebhooksPage',
      "'/school/api-keys",
      "'/api-keys",
    ];
    final offenders = <String>[];
    for (final file in Directory('lib/presentation').listSync(recursive: true).whereType<File>()) {
      if (!file.path.endsWith('.dart')) continue;
      // Comments are for developers; only what compiles into a screen is scanned.
      final text = file.readAsLinesSync().where((l) => !l.trimLeft().startsWith('//')).join('\n');
      for (final needle in forbidden) {
        if (text.contains(needle)) offenders.add('${file.path}: $needle');
      }
    }
    expect(offenders, isEmpty);
  });
}
