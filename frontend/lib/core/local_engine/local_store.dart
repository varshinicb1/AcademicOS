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

  // Real bug found by audit: this used to catch everything (including a
  // corrupted-cache FormatException from jsonDecode inside allAssessments())
  // identically to a genuine "no such assessment" StateError from
  // firstWhere, so a teacher hitting local data corruption saw the same
  // "Assessment X not found on this device" message as one who'd simply
  // mistyped an id -- a real, more actionable problem was hidden behind a
  // misleading one. Only the genuine not-found case returns null now;
  // anything else (corruption) propagates so the caller sees what actually
  // happened.
  Map<String, dynamic>? getAssessment(String id) {
    try {
      return allAssessments().firstWhere((a) => a['id'] == id);
    } on StateError {
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

  /// Replaces one student's sheet within an assessment's evaluations (found
  /// by studentId), or appends it if no sheet exists yet -- same
  /// find-or-append shape as [upsertAssessment]. Used to persist a teacher's
  /// review-stage marks correction back into the same record [addEvaluations]
  /// created, instead of a second unrelated entry piling up.
  void replaceEvaluationSheet(String assessmentId, Map<String, dynamic> sheetResult) {
    final items = evaluationsFor(assessmentId);
    final idx = items.indexWhere((s) => s['studentId'] == sheetResult['studentId']);
    if (idx >= 0) {
      items[idx] = sheetResult;
    } else {
      items.add(sheetResult);
    }
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

  // ---- Student roster (id -> display name) ----
  // Real gap found on-device: student display names only ever lived inside
  // demo_seeder.dart's private list, never persisted anywhere queryable --
  // every screen that shows a student (Mastery's picker, Teacher Insights'
  // "at risk" list) could only show a raw id like "demo_stu_1".
  String studentName(String studentId) =>
      _box.get('student_name_$studentId') as String? ?? studentId;

  void setStudentName(String studentId, String name) =>
      _box.put('student_name_$studentId', name);

  /// Every student who has ever been named, real or demo, for a roster view.
  List<String> allNamedStudentIds() {
    return _box.keys
        .whereType<String>()
        .where((k) => k.startsWith('student_name_'))
        .map((k) => k.substring('student_name_'.length))
        .toList();
  }

  // ---- Parental consent (DPDP Act 2023 -- every CBSE student is a minor) ----
  // This app cannot itself perform identity verification (no OTP/DigiLocker
  // integration exists) -- what it CAN honestly do is require the school to
  // record that a real, verifiable consent step happened (a signed admission
  // form, a confirmed call to the parent, etc.) before a real student's data
  // leaves the device as a report, and keep an append-only record of that.
  // Recording a method here is not itself "verification" -- it's the
  // administrative gate docs/compliance.md calls for, honestly labeled.
  bool isDemoStudent(String studentId) => studentId.startsWith('demo_stu_');

  Map<String, dynamic>? getConsent(String studentId) {
    final raw = _box.get('consent_$studentId') as String?;
    if (raw == null) return null;
    return Map<String, dynamic>.from(jsonDecode(raw) as Map);
  }

  bool hasConsent(String studentId) => getConsent(studentId) != null;

  void setConsent(String studentId, {required String method, required String guardianName}) {
    final record = {
      'method': method,
      'guardianName': guardianName,
      'recordedAt': DateTime.now().toIso8601String(),
    };
    _box.put('consent_$studentId', jsonEncode(record));
    appendAuditLog(
      action: 'parental_consent_recorded',
      assessmentId: '-',
      studentId: studentId,
      details: record,
    );
  }

  // ---- Practice sets (personalized targeted practice) ----
  void savePracticeSet(String setId, Map<String, dynamic> set) {
    _box.put('local_practice_$setId', jsonEncode(set));
  }

  Map<String, dynamic>? getPracticeSet(String setId) {
    final raw = _box.get('local_practice_$setId') as String?;
    if (raw == null) return null;
    return Map<String, dynamic>.from(jsonDecode(raw) as Map);
  }

  // ---- Demo-seed lifecycle ----
  Future<void> markDemoSeeded() => _box.put('demo_seeded_v1', true);
  Future<void> clearDemoSeededFlag() => _box.delete('demo_seeded_v1');
  bool get isDemoSeeded => _box.get('demo_seeded_v1', defaultValue: false) as bool;

  // ---- First-run app tour (see app_tour_page.dart) ----
  Future<void> markAppTourSeen() => _box.put('app_tour_seen_v1', true);
  Future<void> clearAppTourSeenFlag() => _box.delete('app_tour_seen_v1');
  bool get hasSeenAppTour => _box.get('app_tour_seen_v1', defaultValue: false) as bool;

  // ---- Teacher role (offline identity, continued) ----
  // Real gap found on-device: every review/finalize/approve action's
  // "reviewerId"/actor was permanently blank -- teacherName (above) already
  // existed for display purposes (papers/reports), but nothing read it as an
  // *identity* for audit-log purposes, and there was no role concept at all.
  // A real login system (passwords, sessions) doesn't fit a single-device
  // offline app the way it fits a shared server -- physical access is
  // already gated by AppLock's biometric/PIN check (see app_lock.dart) --
  // so this reuses the existing name field and adds only what was missing:
  // a self-declared role, used to gate the principal-approval action below.
  // This mirrors the real server's users.py identity concept but is NOT the
  // same trust model: server-side, a role is issued at registration and
  // enforced by a password; here it can only ever be "this device says its
  // holder is a principal," the honest limit of what's enforceable without
  // a server, not a security bypass of one.
  String get teacherRole => _box.get('teacher_profile_role', defaultValue: 'teacher') as String;
  set teacherRole(String v) => _box.put('teacher_profile_role', v);

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
    String? actor,
  }) {
    final entries = _list('audit_log');
    entries.add({
      'timestamp': DateTime.now().toIso8601String(),
      'action': action,
      'assessmentId': assessmentId,
      'studentId': studentId,
      'details': details,
      // Real gap closed: every entry used to carry no actor at all -- who
      // did this was simply not recorded. Falls back to the device's
      // current-user profile when the caller doesn't pass one explicitly.
      'actor': actor ?? teacherName,
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

  // ---- App preferences (theme, etc.) ----
  // Real gap found on-device: Settings' Theme toggle updated only local
  // widget state, was never persisted, and was never actually connected to
  // MaterialApp's themeMode (hardcoded to ThemeMode.system in main.dart) --
  // switching to Dark visibly did nothing and reset on next visit.
  String get themeModeName => _box.get('theme_mode') as String? ?? 'system';
  set themeModeName(String v) => _box.put('theme_mode', v);

  // ---- Teacher profile (this device's user) ----
  // No real auth/login system exists yet, so this is deliberately a single
  // "whoever is using this device" profile, not a multi-account store --
  // matches the offline, single-teacher-per-device shape everything else in
  // this build (AppConstants.currentSchoolId, etc.) already assumes.
  String get teacherName => _box.get('teacher_profile_name') as String? ?? '';
  set teacherName(String v) => _box.put('teacher_profile_name', v.trim());

  String get teacherSubject => _box.get('teacher_profile_subject') as String? ?? '';
  set teacherSubject(String v) => _box.put('teacher_profile_subject', v.trim());

  // ---- Server-side session (online/multi-device build only) ----
  // Same box the Sarvam Vision BYOK key already lives in (below), AES-
  // encrypted at rest -- a session token is comparably sensitive, so it
  // gets the same treatment rather than a separate secure-storage path.
  String? get authToken => _box.get('auth_token') as String?;
  set authToken(String? v) => v == null ? _box.delete('auth_token') : _box.put('auth_token', v);

  Map<String, dynamic>? get authUser {
    final raw = _box.get('auth_user') as String?;
    if (raw == null) return null;
    return Map<String, dynamic>.from(jsonDecode(raw) as Map);
  }

  set authUser(Map<String, dynamic>? v) =>
      v == null ? _box.delete('auth_user') : _box.put('auth_user', jsonEncode(v));

  void clearAuth() {
    _box.delete('auth_token');
    _box.delete('auth_user');
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

  void deleteScanSession(String sessionId) {
    _box.delete('local_scan_$sessionId');
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
  // ---- School identity ----
  // Not modeled as a full School entity yet -- just enough for the PDF
  // exporter and report cards to show a real name instead of leaving the
  // header blank. Defaults to a clearly-placeholder string so an
  // unconfigured school never silently prints something that looks like a
  // real institution's name.
  String schoolName(String schoolId) =>
      _box.get('school_name_$schoolId') as String? ?? 'School Name Not Set';

  void setSchoolName(String schoolId, String name) =>
      _box.put('school_name_$schoolId', name);

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
