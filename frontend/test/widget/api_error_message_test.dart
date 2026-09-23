// serverErrorMessage (api_error.dart): the one place a failed web API call
// becomes a sentence a teacher or principal can act on (Task 802).
//
// Before this there were three mappers -- curriculum_api's serverErrorMessage,
// pillar_api's apiErrorMessage and auth_api's _asAuthException -- and most
// screens used none of them and showed `'$e'`, which for a DioException reads
// "DioException [bad response]: This exception was thrown because the
// response has a status code of 422...". A FastAPI validation 422 (detail is
// a list) showed only "HTTP 422", and invites_panel told a principal "Could
// not reach the server" for a 500 the server had plainly answered.
//
// DioExceptions are built directly; no network and no mocking library
// (mocktail was removed, see pubspec.yaml).
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/api_error.dart';

DioException _refused(int status, Object? data) {
  final options = RequestOptions(path: '/evaluations/sheet');
  return DioException.badResponse(
    statusCode: status,
    requestOptions: options,
    response: Response(requestOptions: options, statusCode: status, data: data),
  );
}

DioException _noAnswer(DioExceptionType type) =>
    DioException(requestOptions: RequestOptions(path: '/catalog'), type: type);

void main() {
  group('serverErrorMessage', () {
    test("a string detail is the server's own sentence, shown as it is", () {
      const detail = 'no recorded parental consent for student s_1; '
          'record it under Classes before grading';
      expect(serverErrorMessage(_refused(409, {'detail': detail})), detail);
    });

    test('a Pydantic 422 list is summarised field by field, not shown as "HTTP 422"', () {
      final e = _refused(422, {
        'detail': [
          {'loc': ['body', 'newDate'], 'msg': 'Field required', 'type': 'missing'},
          {'loc': ['query', 'marks'], 'msg': 'Input should be a valid integer', 'type': 'int_parsing'},
        ],
      });
      expect(serverErrorMessage(e),
          'newDate: Field required; marks: Input should be a valid integer');
    });

    test('a 422 entry for a nested field names the whole path, and one with no field just its message', () {
      final e = _refused(422, {
        'detail': [
          {'loc': ['body', 'sections', 0, 'marks'], 'msg': 'must be positive'},
          {'loc': ['body'], 'msg': 'Invalid JSON'},
        ],
      });
      expect(serverErrorMessage(e), 'sections.0.marks: must be positive; Invalid JSON');
    });

    test('a detail object carrying a message shows the message, not the report around it', () {
      // generate-from-template's 400/409: the sentence sits beside the whole
      // availability report, which the scope step draws separately (Task 803,
      // where this branch moved out of paper_builder_api's own mapper).
      final e = _refused(400, {
        'detail': {
          'message': 'no question in the bank fits this template',
          'availability': {'sections': []},
        },
      });
      expect(serverErrorMessage(e), 'no question in the bank fits this template');
    });

    test("a model validator's message loses pydantic's 'Value error, ' prefix", () {
      final e = _refused(422, {
        'detail': [
          {'loc': ['body'], 'msg': 'Value error, sections add up to 22 marks but the total is 25'},
        ],
      });
      expect(serverErrorMessage(e), 'sections add up to 22 marks but the total is 25');
    });

    test('401 says the session is over, whatever the body says', () {
      expect(serverErrorMessage(_refused(401, null)), "You're signed out — sign in again");
      expect(serverErrorMessage(_refused(401, {'detail': 'Not authenticated'})),
          "You're signed out — sign in again");
    });

    test('403 with no detail says the account lacks access', () {
      expect(serverErrorMessage(_refused(403, null)), "You don't have access to that");
      expect(serverErrorMessage(_refused(403, {'detail': ''})), "You don't have access to that");
    });

    test('403 with a detail keeps the server\'s reason (it names what to do)', () {
      const detail = 'principal only';
      expect(serverErrorMessage(_refused(403, {'detail': detail})), detail);
    });

    test('no answer at all (connection error, any timeout) blames the connection', () {
      for (final type in [
        DioExceptionType.connectionError,
        DioExceptionType.connectionTimeout,
        DioExceptionType.receiveTimeout,
        DioExceptionType.sendTimeout,
        DioExceptionType.unknown,
      ]) {
        expect(serverErrorMessage(_noAnswer(type)),
            "Couldn't reach the server — check your connection", reason: '$type');
      }
    });

    test('a 5xx with no detail says the server failed, never the connection', () {
      final message = serverErrorMessage(_refused(500, null));
      expect(message, contains('HTTP 500'));
      expect(message, isNot(contains('connection')));
    });

    test('an answer the server gave with no usable body still names its status', () {
      expect(serverErrorMessage(_refused(409, '<html>conflict</html>')), contains('HTTP 409'));
    });

    test("a plain Exception shows its message without Dart's 'Exception: ' prefix", () {
      expect(serverErrorMessage(Exception('Question bank is empty')), 'Question bank is empty');
      expect(serverErrorMessage(StateError('offline')), StateError('offline').toString());
    });
  });

  group('isRetryable', () {
    test('a request that never got an answer, or a server failure, is worth retrying', () {
      expect(isRetryable(_noAnswer(DioExceptionType.connectionError)), isTrue);
      expect(isRetryable(_noAnswer(DioExceptionType.receiveTimeout)), isTrue);
      expect(isRetryable(_refused(500, null)), isTrue);
      expect(isRetryable(_refused(503, null)), isTrue);
    });

    test('a refusal the same request will get again is not', () {
      expect(isRetryable(_refused(401, null)), isFalse);
      expect(isRetryable(_refused(403, null)), isFalse);
      expect(isRetryable(_refused(409, {'detail': 'x'})), isFalse);
      expect(isRetryable(_refused(422, {'detail': []})), isFalse);
      expect(isRetryable(StateError('x')), isFalse);
    });
  });
}
