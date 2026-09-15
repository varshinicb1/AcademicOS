import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The front door of the online (server-connected) build: the router sends
/// every signed-out visitor here before any other page loads, so nobody
/// ever meets a raw 401 error screen again. Handles both sign-in and
/// registration (teacher / student / principal-by-key); the offline build
/// never shows this page at all -- its equivalent is Settings > Profile
/// (LocalStore.teacherName/teacherRole), since a single-device app gets a
/// lighter-weight "who's using this device" concept instead of a real
/// login. See users.py's docstring for how a school-issued principal key
/// (not registration order) is what actually grants "principal".
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _schoolId = TextEditingController();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _principalKey = TextEditingController();
  bool _registering = false;
  bool _submitting = false;
  bool _registeringAsStudent = false;
  bool _obscurePassword = true;
  String? _error;

  @override
  void dispose() {
    _schoolId.dispose();
    _name.dispose();
    _email.dispose();
    _password.dispose();
    _principalKey.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final api = GetIt.I<AuthApi>();
      final result = _registering
          ? await api.register(
              schoolId: _schoolId.text.trim(), name: _name.text.trim(),
              email: _email.text.trim(), password: _password.text,
              role: _registeringAsStudent ? 'student' : null,
              principalKey: _principalKey.text.trim(),
            )
          : await api.login(email: _email.text.trim(), password: _password.text);
      LocalStore.instance.authToken = result.token;
      LocalStore.instance.authUser = result.user.toJson();
      if (!mounted) return;
      // A student has nothing behind this page worth returning to --
      // wherever they came from is the teacher/principal-oriented shell
      // (see student_schedule_page.dart's own doc comment on why it's
      // deliberately outside MainShell's nav). Everyone else goes back to
      // whatever screen opened Sign in -- or home when Sign in WAS the
      // first screen (fresh launch lands here via the router guard, with
      // nothing to pop back to).
      if (result.user.isStudent) {
        context.go('/student/schedule');
      } else {
        context.go('/home');
      }
    } on AuthException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } catch (_) {
      // Never surface raw exceptions (Dio internals, parse errors) on the
      // front door -- the AuthException path above already carries the
      // friendly, user-actionable messages.
      if (!mounted) return;
      setState(() => _error = 'Could not reach the server. Check your connection and try again.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Scaffold(
      backgroundColor: colors.surfaceContainerLowest,
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 24),
                  Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      color: colors.primaryContainer,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(Icons.school, size: 36, color: colors.onPrimaryContainer),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'AcademicOS',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: colors.onSurface,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _registering
                        ? 'Create your school account to get started.'
                        : 'Sign in to your school to continue.',
                    style: theme.textTheme.bodyMedium?.copyWith(color: colors.onSurfaceVariant),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  SegmentedButton<bool>(
                    segments: const [
                      ButtonSegment(value: false, label: Text('Sign in')),
                      ButtonSegment(value: true, label: Text('Create account')),
                    ],
                    selected: {_registering},
                    onSelectionChanged: _submitting
                        ? null
                        : (sel) => setState(() {
                              _registering = sel.first;
                              _error = null;
                            }),
                  ),
                  const SizedBox(height: 16),
                  AppCard(
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (_error != null)
                            Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: colors.errorContainer,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(Icons.error_outline, color: colors.onErrorContainer),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _error!,
                                      style: theme.textTheme.bodyMedium
                                          ?.copyWith(color: colors.onErrorContainer),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          if (_registering) ...[
                            TextFormField(
                              controller: _schoolId,
                              textInputAction: TextInputAction.next,
                              decoration: const InputDecoration(
                                labelText: 'School ID',
                                hintText: 'The ID your school gave you',
                                prefixIcon: Icon(Icons.apartment_outlined),
                                border: OutlineInputBorder(),
                              ),
                              validator: (v) =>
                                  (v == null || v.trim().isEmpty) ? 'Required' : null,
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _name,
                              textInputAction: TextInputAction.next,
                              decoration: const InputDecoration(
                                labelText: 'Your name',
                                prefixIcon: Icon(Icons.person_outline),
                                border: OutlineInputBorder(),
                              ),
                              validator: (v) =>
                                  (v == null || v.trim().isEmpty) ? 'Required' : null,
                            ),
                            const SizedBox(height: 12),
                            // A student registers the same way, just marked
                            // as one -- the server never lets this (or any
                            // other client-supplied field) grant "principal";
                            // only a real principal key does that (below).
                            SegmentedButton<bool>(
                              segments: const [
                                ButtonSegment(value: false, label: Text('Teacher')),
                                ButtonSegment(value: true, label: Text('Student')),
                              ],
                              selected: {_registeringAsStudent},
                              onSelectionChanged: (sel) =>
                                  setState(() => _registeringAsStudent = sel.first),
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _principalKey,
                              textInputAction: TextInputAction.next,
                              decoration: const InputDecoration(
                                labelText: 'Principal key (optional)',
                                hintText: 'Only if your school issued you one',
                                prefixIcon: Icon(Icons.key_outlined),
                                border: OutlineInputBorder(),
                              ),
                            ),
                            const SizedBox(height: 12),
                          ],
                          TextFormField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.next,
                            decoration: const InputDecoration(
                              labelText: 'Email',
                              prefixIcon: Icon(Icons.email_outlined),
                              border: OutlineInputBorder(),
                            ),
                            validator: (v) =>
                                (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _password,
                            obscureText: _obscurePassword,
                            textInputAction: TextInputAction.done,
                            onFieldSubmitted: (_) => _submit(),
                            decoration: InputDecoration(
                              labelText: 'Password',
                              prefixIcon: const Icon(Icons.lock_outline),
                              border: const OutlineInputBorder(),
                              suffixIcon: IconButton(
                                icon: Icon(_obscurePassword
                                    ? Icons.visibility_outlined
                                    : Icons.visibility_off_outlined),
                                onPressed: () =>
                                    setState(() => _obscurePassword = !_obscurePassword),
                              ),
                            ),
                            validator: (v) =>
                                (v == null || v.length < 8) ? 'At least 8 characters' : null,
                          ),
                          const SizedBox(height: 20),
                          FilledButton(
                            onPressed: _submitting ? null : _submit,
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4),
                              child: _submitting
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(strokeWidth: 2),
                                    )
                                  : Text(_registering ? 'Create account' : 'Sign in'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Teachers approve papers, students track their schedule -- '
                    'your role is picked up automatically after you sign in.',
                    style: theme.textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
