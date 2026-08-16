import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/api_client.dart';

void main() {
  test('assessment list from live backend deserializes', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000/api/v1'));
    final api = ApiClient(dio);
    final list = await api.getAssessmentsByTeacher('teacher_1');
    // ignore: avoid_print
    print('parsed ${list.length} assessments');
    for (final a in list) {
      // ignore: avoid_print
      print('  ${a.id} | ${a.title} | ${a.status} | sections=${a.blueprint.sections.length}');
    }
    expect(list, isNotEmpty);
  }, timeout: const Timeout(Duration(seconds: 20)));
}
