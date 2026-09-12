import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// Real login/register for the online (server-connected) build -- the
/// missing half of the identity system evaluation_page.dart's reviewerId
/// gap and the principal-approval workflow both depend on. The offline
/// build's equivalent is Settings > Profile (LocalStore.teacherName/
/// teacherRole) -- see that page's docstring for why a single-device app
/// gets a lighter-weight "who's using this device" concept instead of a
/// real login, and users.py's docstring for the "first registrant per
/// school becomes principal" bootstrap rule this register form relies on.
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
  bool _registering = false;
  bool _submitting = false;
  bool _registeringAsStudent = false;
  String? _error;

  @override
  void dispose() {
    _schoolId.dispose();
    _name.dispose();
    _email.dispose();
    _password.dispose();
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
            )
          : await api.login(email: _email.text.trim(), password: _password.text);
      LocalStore.instance.authToken = result.token;
      LocalStore.instance.authUser = result.user.toJson();
      if (!mounted) return;
      // A student has nothing behind this page worth returning to --
      // wherever they came from is the teacher/principal-oriented shell
      // (see student_schedule_page.dart's own doc comment on why it's
      // deliberately outside MainShell's nav). Everyone else keeps the
      // original "return to whatever screen opened Sign in" behavior.
      if (result.user.isStudent) {
        context.go('/student/schedule');
      } else {
        context.pop();
      }
    } on AuthException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Something went wrong: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(_registering ? 'Create account' : 'Sign in')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _registering
                          ? 'The first person to register for a school becomes its '
                              'principal automatically; everyone after that is a teacher.'
                          : 'Sign in with the account you registered.',
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                      ),
                    if (_registering) ...[
                      TextFormField(
                        controller: _schoolId,
                        decoration: const InputDecoration(labelText: 'School ID', border: OutlineInputBorder()),
                        validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _name,
                        decoration: const InputDecoration(labelText: 'Your name', border: OutlineInputBorder()),
                        validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                      ),
                      const SizedBox(height: 12),
                      // §18: a student registers the same way, just marked
                      // as one -- the server never lets this (or any other
                      // client-supplied field) grant "principal", only a
                      // real principal_key does that.
                      SegmentedButton<bool>(
                        segments: const [
                          ButtonSegment(value: false, label: Text('Teacher')),
                          ButtonSegment(value: true, label: Text('Student')),
                        ],
                        selected: {_registeringAsStudent},
                        onSelectionChanged: (sel) => setState(() => _registeringAsStudent = sel.first),
                      ),
                      const SizedBox(height: 12),
                    ],
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder()),
                      validator: (v) => (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _password,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder()),
                      validator: (v) => (v == null || v.length < 8) ? 'At least 8 characters' : null,
                    ),
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _submitting ? null : _submit,
                      child: _submitting
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                          : Text(_registering ? 'Create account' : 'Sign in'),
                    ),
                    const SizedBox(height: 8),
                    TextButton(
                      onPressed: _submitting
                          ? null
                          : () => setState(() {
                                _registering = !_registering;
                                _error = null;
                              }),
                      child: Text(_registering
                          ? 'Already have an account? Sign in'
                          : "New school? Create an account"),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
