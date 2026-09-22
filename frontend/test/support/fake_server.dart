// A real Dio whose interceptor answers instead of the network, the technique
// of schedule_mark_error_test.dart (no mocking library, see pubspec.yaml).
// Shared by the Task 802 silent-failure tests so every one of them feeds a
// screen the same shape of failure the real Dio would raise: a
// DioException.badResponse for a 4xx/5xx, a DioException with no response
// for a request that never got an answer.
import 'package:dio/dio.dart';

/// Answers `(method, path)` with [routes]' `(status, body)`; a route mapped
/// to a [DioExceptionType] is a request that never got an answer. A request
/// with no route fails the test loudly rather than hanging on the network.
class FakeServer extends Interceptor {
  final Map<String, Object> routes;

  /// Every `METHOD /path` this server was asked for, in order -- lets a test
  /// assert that a call was (or was not) made.
  final List<String> requests = [];

  FakeServer(this.routes);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final key = '${options.method} ${options.path}';
    requests.add(key);
    final route = routes[key];
    if (route == null) {
      throw StateError('FakeServer has no route for $key (routes: ${routes.keys.join(', ')})');
    }
    if (route is DioExceptionType) {
      handler.reject(DioException(requestOptions: options, type: route));
      return;
    }
    final (status, body) = route as (int, Object?);
    final response = Response(requestOptions: options, statusCode: status, data: body);
    if (status < 400) {
      handler.resolve(response);
    } else {
      handler.reject(DioException.badResponse(
          statusCode: status, requestOptions: options, response: response));
    }
  }
}

/// A Dio pointed at an address that can never resolve, answered by [server].
Dio fakeDio(FakeServer server) =>
    Dio(BaseOptions(baseUrl: 'http://backend.invalid/api/v1'))..interceptors.add(server);
