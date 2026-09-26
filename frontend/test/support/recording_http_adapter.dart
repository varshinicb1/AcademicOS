// A Dio transport that never touches a socket: it records every request
// that reaches it and answers 200 `{}`. Installed under the app's real Dio
// wiring (registerNetworkClients' httpClientAdapter), it turns "did this
// screen make a network call?" into a count -- zero means the request was
// stopped before it could leave the device, not that the network was down.
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

class RecordingHttpAdapter implements HttpClientAdapter {
  final List<RequestOptions> requests = [];

  @override
  Future<ResponseBody> fetch(
      RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    requests.add(options);
    return ResponseBody.fromBytes(
      utf8.encode('{}'),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
