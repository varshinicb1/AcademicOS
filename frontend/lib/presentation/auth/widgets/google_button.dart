import 'package:flutter/widgets.dart';

import 'google_button_stub.dart' if (dart.library.js_interop) 'google_button_web.dart' as impl;

/// "Sign in with Google" (INT-1): Google's own button, rendered by Google
/// Identity Services on the web. It hands back an ID token for the server to
/// check (`POST /auth/google`); nothing from Google is kept on the device.
/// Shown only when the server says Google sign-in is set up
/// (`/auth/providers`); elsewhere than the web it is empty.
class GoogleSignInButton extends StatelessWidget {
  final String clientId;
  final void Function(String credential) onCredential;
  final void Function(String message) onProblem;

  const GoogleSignInButton({super.key, required this.clientId, required this.onCredential, required this.onProblem});

  @override
  Widget build(BuildContext context) =>
      impl.googleButton(clientId: clientId, onCredential: onCredential, onProblem: onProblem);
}
