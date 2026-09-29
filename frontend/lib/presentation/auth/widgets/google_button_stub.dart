import 'package:flutter/widgets.dart';

/// Not the web: the phone apps sign in with a password or an emailed code
/// until Google sign-in is set up for Android.
Widget googleButton({required String clientId, required void Function(String credential) onCredential,
        required void Function(String message) onProblem}) =>
    const SizedBox.shrink();
