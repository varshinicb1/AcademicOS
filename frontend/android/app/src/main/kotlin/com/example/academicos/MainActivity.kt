package com.example.academicos

import io.flutter.embedding.android.FlutterFragmentActivity

// local_auth's biometric prompt needs a FragmentActivity to attach its
// dialog to -- plain FlutterActivity throws at runtime the first time the
// Biometric Auth toggle in Settings actually tries to authenticate.
class MainActivity : FlutterFragmentActivity()
