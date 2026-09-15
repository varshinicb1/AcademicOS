/// Client for the parental consent endpoints
/// (src/academicos/assessment/consent_routes.py) — DPDP Act 2023 compliance.
library;

import 'package:dio/dio.dart';

class ConsentRecord {
  final String id;
  final String schoolId;
  final String studentId;
  final String guardianName;
  final String guardianRelationship;
  final String method;
  final String status;
  final String? notes;
  final String recordedBy;
  final String recordedAt;

  ConsentRecord.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        schoolId = j['schoolId'] as String,
        studentId = j['studentId'] as String,
        guardianName = j['guardianName'] as String,
        guardianRelationship = (j['guardianRelationship'] as String?) ?? 'parent',
        method = j['method'] as String,
        status = (j['status'] as String?) ?? 'granted',
        notes = j['notes'] as String?,
        recordedBy = j['recordedBy'] as String,
        recordedAt = j['recordedAt'] as String;

  bool get isGranted => status == 'granted';
}

class ConsentApi {
  final Dio _dio;
  ConsentApi(this._dio);

  Future<ConsentRecord> recordConsent({
    required String studentId,
    required String guardianName,
    String guardianRelationship = 'parent',
    required String method,
    String? notes,
  }) async {
    final res = await _dio.post('/consent', data: {
      'studentId': studentId,
      'guardianName': guardianName,
      'guardianRelationship': guardianRelationship,
      'method': method,
      if (notes != null) 'notes': notes,
    });
    return ConsentRecord.fromJson(Map<String, dynamic>.from(res.data as Map));
  }

  Future<bool> checkConsent(String studentId) async {
    try {
      final res = await _dio.get('/consent/students/$studentId');
      final data = Map<String, dynamic>.from(res.data as Map);
      return data['hasConsent'] == true;
    } catch (_) {
      return false;
    }
  }

  Future<List<ConsentRecord>> listConsents() async {
    final res = await _dio.get('/consent');
    final list = res.data as List;
    return list.map((e) => ConsentRecord.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<bool> revokeConsent(String studentId) async {
    final res = await _dio.delete('/consent/students/$studentId');
    final data = Map<String, dynamic>.from(res.data as Map);
    return data['hasConsent'] == false;
  }
}
