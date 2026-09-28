// The Web build must never be compiled with ACADEMICOS_OFFLINE.
//
// The flag swaps the whole API layer for the on-device engine
// (service_locator.dart) and turns off the network guard's web exemption
// (network_policy.dart). A web bundle built with it would be a thin client
// with no server behind it: every action silently served from a question
// bank the web pipeline strips out after the build (deploy-gcp.yml). Nothing
// stopped a copy-pasted `--dart-define=ACADEMICOS_OFFLINE=true` landing on
// the web build step; this reads every workflow and fails if one does.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Every `flutter build web` command in [workflowYaml] that passes
/// ACADEMICOS_OFFLINE, as one line each. Comments are dropped first (the
/// real deploy-gcp.yml explains the flag in a comment right under its web
/// build) and backslash continuations are joined, so a flag on the third
/// line of a multi-line command is still caught.
List<String> webBuildsPassingOfflineFlag(String workflowYaml) {
  final logical = <String>[];
  var pending = '';
  for (final raw in workflowYaml.split('\n')) {
    final line = raw.replaceAll('\r', '').replaceFirst(RegExp(r'(^|\s)#.*$'), '').trimRight();
    if (line.endsWith('\\')) {
      pending += '${line.substring(0, line.length - 1)} ';
      continue;
    }
    logical.add(pending + line);
    pending = '';
  }
  if (pending.isNotEmpty) logical.add(pending);
  return logical
      .where((l) => RegExp(r'flutter\s+build\s+web\b').hasMatch(l) && l.contains('ACADEMICOS_OFFLINE'))
      .map((l) => l.trim())
      .toList();
}

void main() {
  // flutter test runs with the package root (frontend/) as cwd.
  final workflows = Directory('../.github/workflows')
      .listSync()
      .whereType<File>()
      .where((f) => f.path.endsWith('.yml') || f.path.endsWith('.yaml'))
      .toList();

  test('the repository has workflows to check, and at least one builds the web app', () {
    expect(workflows, isNotEmpty);
    final buildsWeb = workflows.any((f) => RegExp(r'flutter\s+build\s+web\b').hasMatch(f.readAsStringSync()));
    expect(buildsWeb, isTrue, reason: 'the check below would pass vacuously');
  });

  test('no workflow builds the web app with ACADEMICOS_OFFLINE', () {
    final offenders = {
      for (final f in workflows)
        if (webBuildsPassingOfflineFlag(f.readAsStringSync()).isNotEmpty)
          f.path: webBuildsPassingOfflineFlag(f.readAsStringSync()),
    };
    expect(offenders, isEmpty);
  });

  group('the detector itself', () {
    test('catches the flag on a continuation line of a web build', () {
      const yaml = '''
      - run: |
          flutter build web --release \\
            --dart-define=ACADEMICOS_API=https://x/api/v1 \\
            --dart-define=ACADEMICOS_OFFLINE=true
''';
      expect(webBuildsPassingOfflineFlag(yaml), hasLength(1));
    });

    test('ignores the flag on the APK build and in comments', () {
      const yaml = '''
      # flutter build web ... never with ACADEMICOS_OFFLINE
      - run: flutter build apk --release --dart-define=ACADEMICOS_OFFLINE=true
      - run: flutter build web --release  # not ACADEMICOS_OFFLINE
''';
      expect(webBuildsPassingOfflineFlag(yaml), isEmpty);
    });
  });
}
