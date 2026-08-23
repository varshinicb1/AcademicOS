import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';

/// Lightweight local persistence for the standalone build -- assessments,
/// generated papers, evaluations, mastery, templates. Backed by the Hive
/// box already opened at startup (real, on-device storage that survives an
/// app restart), storing each record as a JSON string under a namespaced
/// key. Not a full drift migration -- deliberately simple so this ships
/// rather than stalling on a second build_runner cycle for a new schema.
class LocalStore {
  LocalStore._();
  static final LocalStore instance = LocalStore._();

  Box get _box => Hive.box('academicos_cache');

  /// Public accessor for the underlying Hive box -- used by SyncService
  /// to persist last-sync metadata without adding dedicated LocalStore methods.
  Box get box => _box;

  List<Map<String, dynamic>> _list(String key) {
    final raw = _box.get(key) as String?;
    if (raw == null) return [];
    return (jsonDecode(raw) as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  void _saveList(String key, List<Map<String, dynamic>> items) {
    _box.put(key, jsonEncode(items));
  }

  // ---- Assessments ----
  List<Map<String, dynamic>> allAssessments() => _list('local_assessments');

  void upsertAssessment(Map<String, dynamic> assessment) {
    final items = allAssessments();
    final idx = items.indexWhere((a) => a['id'] == assessment['id']);
    if (idx >= 0) {
      items[idx] = assessment;
    } else {
      items.add(assessment);
    }
    _saveList('local_assessments', items);
  }

  Map<String, dynamic>? getAssessment(String id) {
    try {
      return allAssessments().firstWhere((a) => a['id'] == id);
    } catch (_) {
      return null;
    }
  }

  void deleteAssessment(String id) {
    final items = allAssessments()..removeWhere((a) => a['id'] == id);
    _saveList('local_assessments', items);
    _box.delete('local_evaluations_$id');
  }

  // ---- Generated papers ----
  void savePaper(String paperId, Map<String, dynamic> paper) {
    _box.put('local_paper_$paperId', jsonEncode(paper));
  }

  Map<String, dynamic>? getPaper(String paperId) {
    final raw = _box.get('local_paper_$paperId') as String?;
    if (raw == null) return null;
    return Map<String, dynamic>.from(jsonDecode(raw) as Map);
  }

  // ---- Evaluations, keyed by assessmentId ----
  List<Map<String, dynamic>> evaluationsFor(String assessmentId) =>
      _list('local_evaluations_$assessmentId');

  void addEvaluations(String assessmentId, List<Map<String, dynamic>> sheetResults) {
    final items = evaluationsFor(assessmentId)..addAll(sheetResults);
    _saveList('local_evaluations_$assessmentId', items);
  }

  List<String> allAssessmentIdsWithEvaluations() {
    return _box.keys
        .whereType<String>()
        .where((k) => k.startsWith('local_evaluations_'))
        .map((k) => k.substring('local_evaluations_'.length))
        .toList();
  }

  // ---- Mastery, keyed by studentId ----
  Map<String, dynamic>? getMastery(String studentId) {
    final raw = _box.get('local_mastery_$studentId') as String?;
    if (raw == null) return null;
    return Map<String, dynamic>.from(jsonDecode(raw) as Map);
  }

  void saveMastery(String studentId, Map<String, dynamic> mastery) {
    _box.put('local_mastery_$studentId', jsonEncode(mastery));
  }

  List<String> allStudentIdsWithMastery() {
    return _box.keys
        .whereType<String>()
        .where((k) => k.startsWith('local_mastery_'))
        .map((k) => k.substring('local_mastery_'.length))
        .toList();
  }

  void clearMastery(String studentId) {
    _box.delete('local_mastery_$studentId');
  }

  // ---- Demo-seed lifecycle ----
  Future<void> markDemoSeeded() => _box.put('demo_seeded_v1', true);
  Future<void> clearDemoSeededFlag() => _box.delete('demo_seeded_v1');
  bool get isDemoSeeded => _box.get('demo_seeded_v1', defaultValue: false) as bool;

  // ---- Audit log: append-only record of every grading event ----
  // The concrete "corruption resistance" control docs/compliance.md calls
  // for -- every mark written goes into an append-only log (never edited,
  // never deleted by normal app code) so a disputed grade has a real,
  // timestamped history to check instead of a bare "trust the current
  // number." This is deliberately separate from the mutable evaluation
  // records themselves.
  void appendAuditLog({
    required String action,
    required String assessmentId,
    required String studentId,
    Map<String, dynamic> details = const {},
  }) {
    final entries = _list('audit_log');
    entries.add({
      'timestamp': DateTime.now().toIso8601String(),
      'action': action,
      'assessmentId': assessmentId,
      'studentId': studentId,
      'details': details,
    });
    _saveList('audit_log', entries);
  }

  List<Map<String, dynamic>> auditLog({String? assessmentId, String? studentId}) {
    var entries = _list('audit_log');
    if (assessmentId != null) {
      entries = entries.where((e) => e['assessmentId'] == assessmentId).toList();
    }
    if (studentId != null) {
      entries = entries.where((e) => e['studentId'] == studentId).toList();
    }
    return entries;
  }

  // ---- Optional BYOK: Sarvam Vision accuracy upgrade for Scan & Grade ----
  // Stored in this same Hive box, which is AES-encrypted at rest (see
  // secure_box.dart) -- an API key is sensitive the same way any other
  // locally-cached data here is.
  String? get sarvamApiKey => _box.get('sarvam_api_key') as String?;
  set sarvamApiKey(String? key) {
    if (key == null || key.trim().isEmpty) {
      _box.delete('sarvam_api_key');
    } else {
      _box.put('sarvam_api_key', key.trim());
    }
  }

  // ---- Scan sessions (offline Scan & Grade) ----
  Map<String, dynamic>? getScanSession(String sessionId) {
    final raw = _box.get('local_scan_$sessionId') as String?;
    if (raw == null) return null;
    return Map<String, dynamic>.from(jsonDecode(raw) as Map);
  }

  void saveScanSession(String sessionId, Map<String, dynamic> session) {
    _box.put('local_scan_$sessionId', jsonEncode(session));
  }

  /// Every scan session ever created on this device, most-recently-touched
  /// first -- used by the Today screen to surface real "N answer sheets
  /// waiting for your review" counts instead of a guess.
  List<Map<String, dynamic>> allScanSessions() {
    final sessions = _box.keys
        .whereType<String>()
        .where((k) => k.startsWith('local_scan_'))
        .map((k) => Map<String, dynamic>.from(jsonDecode(_box.get(k) as String) as Map))
        .toList();
    sessions.sort((a, b) {
      final aStatus = a['status'] == 'reviewing' ? 0 : 1;
      final bStatus = b['status'] == 'reviewing' ? 0 : 1;
      return aStatus.compareTo(bStatus);
    });
    return sessions;
  }

  // ---- School templates ----
  List<Map<String, dynamic>> templatesFor(String schoolId) => _list('local_templates_$schoolId');

  void saveTemplate(String schoolId, Map<String, dynamic> template) {
    final items = templatesFor(schoolId);
    final idx = items.indexWhere((t) => t['id'] == template['id']);
    if (idx >= 0) {
      items[idx] = template;
    } else {
      items.add(template);
    }
    _saveList('local_templates_$schoolId', items);
  }
}
