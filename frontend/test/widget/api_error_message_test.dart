// apiErrorMessage (pillar_api.dart): what the grading, scanning and practice
// pages show a teacher when a call fails. The case that motivated it: the
// server refuses to grade a student with no recorded parental consent (409,
// src/academicos/assessment/authz.py require_consent), and the page must show
// that sentence -- it names the fix -- rather than Dio's generic
// "DioException [bad response]" text. DioExceptions are built directly; no
// network and no mocking library (mocktail was removed, see pubspec.yaml).
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/pillar_api.dart';

DioException _refused(int status, Object? data) {
  final options = RequestOptions(path: '/evaluations/sheet');
  return DioException.badResponse(
    statusCode: status,
    requestOptions: options,
    response: Response(requestOptions: options, statusCode: status, data: data),
  );
}

void main() {
  test('a consent refusal shows the server\'s own sentence', () {
    const detail = 'no recorded parental consent for student s_1; '
        'record it under Classes before grading';
    expect(apiErrorMessage(_refused(409, {'detail': detail})), detail);
  });

  test('a 422 validation list is not shown as if it were a sentence', () {
    final e = _refused(422, {
      'detail': [
        {'loc': ['body', 'studentId'], 'msg': 'field required'},
      ],
    });
    expect(apiErrorMessage(e), e.toString());
  });

  test('a response with no body falls back to the error itself', () {
    final e = _refused(502, null);
    expect(apiErrorMessage(e), e.toString());
  });

  test('a non-Dio error falls back to its own text', () {
    expect(apiErrorMessage(StateError('offline')), StateError('offline').toString());
  });
}
