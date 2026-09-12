import 'package:flutter/material.dart';
import 'package:local_auth/local_auth.dart';
import 'package:local_auth/error_codes.dart' as auth_error;

import 'local_store.dart';

/// Real fingerprint/face/PIN app lock -- Settings' "Biometric Auth" toggle
/// used to just persist a boolean nothing ever read. `local_auth` needs no
/// server and no new permission dialog beyond what Android already grants
/// for device-credential checks, so there was no real reason for this to
/// stay fake once someone actually looked at it.
class AppLock {
  static final _auth = LocalAuthentication();

  static bool get isEnabled =>
      LocalStore.instance.box.get('pref_biometric_auth', defaultValue: false) as bool;

  /// Run once, right when a teacher flips the Settings toggle on -- refuses
  /// to enable the lock if this phone has no fingerprint, face, or device
  /// PIN/pattern set up, since that would otherwise lock a teacher out of
  /// their own real class/student data with no way back in.
  static Future<bool> confirmCanEnable() async {
    try {
      final supported = await _auth.isDeviceSupported();
      final canCheck = await _auth.canCheckBiometrics;
      if (!supported && !canCheck) return false;
      return await _authenticate('Confirm it\'s you to turn on the app lock');
    } catch (_) {
      return false;
    }
  }

  /// Called by AppLockGate every time the app needs unlocking. `biometricOnly:
  /// false` means a device PIN/pattern/password satisfies this too, not just
  /// a fingerprint sensor -- most Android phones a teacher already owns.
  static Future<bool> _authenticate(String reason) async {
    try {
      return await _auth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(biometricOnly: false, stickyAuth: true),
      );
    } on Exception catch (e) {
      // A real, expected outcome on an emulator or a phone with no
      // fingerprint/PIN configured -- not a bug to surface as a crash.
      if (e.toString().contains(auth_error.notAvailable) ||
          e.toString().contains(auth_error.notEnrolled)) {
        return false;
      }
      return false;
    }
  }

  static Future<bool> unlock() => _authenticate('Unlock AcademicOS');
}

/// Wraps the whole app. When the toggle is on, the real screen underneath is
/// replaced by a lock screen on cold start and every time the app comes back
/// from the background -- the same moment a phone left on a desk between
/// classes is most likely to be picked up by someone who isn't the teacher.
class AppLockGate extends StatefulWidget {
  final Widget child;
  const AppLockGate({super.key, required this.child});

  @override
  State<AppLockGate> createState() => _AppLockGateState();
}

class _AppLockGateState extends State<AppLockGate> with WidgetsBindingObserver {
  bool _unlocked = !AppLock.isEnabled;
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (!_unlocked) _promptUnlock();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused && AppLock.isEnabled) {
      // Real re-lock on backgrounding, not just on a cold start a teacher
      // might only see once a day.
      setState(() => _unlocked = false);
    } else if (state == AppLifecycleState.resumed && !_unlocked) {
      _promptUnlock();
    }
  }

  Future<void> _promptUnlock() async {
    if (_checking) return;
    setState(() => _checking = true);
    final ok = await AppLock.unlock();
    if (!mounted) return;
    setState(() {
      _checking = false;
      if (ok) _unlocked = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_unlocked) return widget.child;

    final theme = Theme.of(context);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: theme,
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.lock_outline, size: 56, color: theme.colorScheme.primary),
                  const SizedBox(height: 20),
                  Text('AcademicOS is locked', style: theme.textTheme.titleLarge),
                  const SizedBox(height: 8),
                  Text(
                    'Unlock with your fingerprint, face, or device PIN to see real student data.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  ),
                  const SizedBox(height: 24),
                  FilledButton.icon(
                    onPressed: _checking ? null : _promptUnlock,
                    icon: _checking
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.fingerprint),
                    label: Text(_checking ? 'Checking…' : 'Unlock'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
