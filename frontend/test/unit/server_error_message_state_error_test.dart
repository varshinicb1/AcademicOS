// A StateError's sentence is shown as it is written, not as "Bad state: ..." (the live sign-in page
// read "Bad state: Google sign-in could not load." on 2026-10-04).
import 'package:academicos/data/datasources/api/api_error.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('a StateError reads as its own sentence', () {
    expect(serverErrorMessage(StateError('Google sign-in could not load. Check the connection, or use your password.')),
        'Google sign-in could not load. Check the connection, or use your password.');
  });

  test('an Exception still loses its prefix', () {
    expect(serverErrorMessage(Exception('Choose a class first.')), 'Choose a class first.');
  });
}
