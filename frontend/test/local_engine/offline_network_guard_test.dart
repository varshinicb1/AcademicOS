// The offline phone's network promise, enforced: until the teacher opts in
// to sync, no request built by the app's real Dio wiring can leave the
// device, and none of the Dio-backed APIs (AuthApi, CurriculumApi,
// ConsentApi) is even registered.
//
// Why the interceptor guard AND the registration check, instead of the
// simpler "no registered API holds a Dio": LocalApiClient and
// LocalPillarApi extend the Dio-backed ApiClient/PillarApi and pass a bare
// Dio() to super, so every offline API holds a Dio by construction -- that
// assertion is false on the correct build. What matters is whether a
// request can get out, so this drives registerNetworkClients() -- the exact
// function initDependencies() calls -- with `offline: true` and a
// transport that counts what reaches it. No --dart-define needed: the
// offline flag is passed in, so this runs in every plain `flutter test`.
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:academicos/core/di/service_locator.dart';
import 'package:academicos/core/sync/network_policy.dart';
import 'package:academicos/data/datasources/api/auth_api.dart';
import 'package:academicos/data/datasources/api/consent_api.dart';
import 'package:academicos/data/datasources/api/curriculum_api.dart';

import '../support/real_di.dart';
import '../support/recording_http_adapter.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late RealTestEnv env;
  late GetIt sl;
  late RecordingHttpAdapter transport;

  setUpAll(() async {
    env = await RealTestEnv.init('offline_network_guard_test_');
  });

  tearDownAll(() async {
    await env.dispose();
  });

  setUp(() async {
    await env.cacheBox.clear();
    sl = GetIt.asNewInstance();
    transport = RecordingHttpAdapter();
  });

  group('offline build, sync off (the default)', () {
    setUp(() => registerNetworkClients(sl, offline: true, httpClientAdapter: transport));

    test('sync is off on a fresh device', () {
      expect(SyncSettings.enabled, isFalse);
    });

    test('registers no Dio-backed API', () {
      expect(sl.isRegistered<AuthApi>(), isFalse);
      expect(sl.isRegistered<CurriculumApi>(), isFalse);
      expect(sl.isRegistered<ConsentApi>(), isFalse,
          reason: 'a consent record is a minor\'s personal data; it must have no way off the device');
    });

    test('a request through the shared Dio is stopped before it reaches the transport', () async {
      await expectLater(
        sl<Dio>().post('/consent', data: {'studentId': 'stu_1', 'guardianName': 'A. Parent'}),
        throwsA(isA<DioException>().having((e) => e.error, 'error', isA<NetworkDisabledException>())),
      );
      expect(transport.requests, isEmpty);
    });

    test('the same Dio carries a request once the teacher opts in', () async {
      // The guard is the switch, not a deleted client: Task 405's opt-in
      // sync must be able to turn the network on without rewiring DI.
      SyncSettings.enabled = true;
      await sl<Dio>().get('/my-schedule');
      expect(transport.requests.map((r) => r.path), ['/my-schedule']);
    });
  });

  group('web build', () {
    setUp(() => registerNetworkClients(sl, offline: false, httpClientAdapter: transport));

    test('keeps every Dio-backed API -- it is a thin client', () {
      expect(sl.isRegistered<AuthApi>(), isTrue);
      expect(sl.isRegistered<CurriculumApi>(), isTrue);
      expect(sl.isRegistered<ConsentApi>(), isTrue);
    });

    test('is never blocked by the sync switch', () async {
      expect(SyncSettings.enabled, isFalse);
      await sl<Dio>().get('/consent');
      expect(transport.requests, hasLength(1));
    });
  });
}
