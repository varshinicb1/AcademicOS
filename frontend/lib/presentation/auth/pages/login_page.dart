import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The front door of the online (server-connected) build: the router sends
/// every signed-out visitor here before any other page loads, so nobody
/// ever meets a raw 401 error screen again. Handles both sign-in and
/// registration; the offline build
/// never shows this page at all -- its equivalent is Settings > Profile
/// (LocalStore.teacherName/teacherRole), since a single-device app gets a
/// lighter-weight "who's using this device" concept instead of a real
/// login.
///
/// Registration is by invite (users.py, 2026-09-21): the form asks for the
/// code a principal issued and nothing else about the school, because the
/// server takes the school and role from the invite. Until then this form
/// asked for a school id and a teacher/student choice, and the server
/// believed both, so anyone who knew a school's id could join it. The
/// operator's path for a NEW school's first principal (school id + principal
/// key) is kept, collapsed and clearly separate, so nobody mistakes it for
/// the normal way in.
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _inviteCode = TextEditingController();
  final _schoolId = TextEditingController();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _principalKey = TextEditingController();
  bool _registering = false;
  bool _submitting = false;
  // Registering as a new school's first principal instead of by invite.
  bool _firstPrincipal = false;
  bool _obscurePassword = true;
  String? _error;

  @override
  void dispose() {
    _inviteCode.dispose();
    _schoolId.dispose();
    _name.dispose();
    _email.dispose();
    _password.dispose();
    _principalKey.dispose();
    super.dispose();
  }

  /// Sign in with a one-time code sent by email (students and parents).
  Future<void> _signInWithCode() async {
    final email = TextEditingController(text: _email.text.trim());
    final code = TextEditingController();
    var sent = false;
    String? message;
    final result = await showDialog<Map<String, dynamic>>(context: context, builder: (ctx) => StatefulBuilder(
      builder: (ctx, set) => AlertDialog(
        title: const Text('Sign in with a code'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: email, enabled: !sent, keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(labelText: 'Email')),
          if (sent)
            TextField(controller: code, keyboardType: TextInputType.number, maxLength: 6,
                decoration: const InputDecoration(labelText: '6-digit code from the email')),
          if (message != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(message!)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              final dio = GetIt.I<Dio>();
              try {
                if (!sent) {
                  final r = await dio.post('/auth/code/request', data: {'email': email.text.trim()});
                  set(() {
                    sent = true;
                    message = (r.data as Map)['detail'] as String?;
                  });
                } else {
                  final r = await dio.post('/auth/code/verify', data: {'email': email.text.trim(), 'code': code.text.trim()});
                  if (ctx.mounted) Navigator.pop(ctx, Map<String, dynamic>.from(r.data as Map));
                }
              } on DioException catch (e) {
                set(() => message = serverErrorMessage(e));
              }
            },
            child: Text(sent ? 'Sign in' : 'Send code'),
          ),
        ],
      ),
    ));
    if (result == null || !mounted) return;
    LocalStore.instance.authToken = result['token'] as String;
    LocalStore.instance.authUser = Map<String, dynamic>.from(result['user'] as Map);
    context.go('/home');
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final api = GetIt.I<AuthApi>();
      final AuthResult result;
      if (!_registering) {
        result = await api.login(email: _email.text.trim(), password: _password.text);
      } else if (_firstPrincipal) {
        result = await api.registerFirstPrincipal(
          schoolId: _schoolId.text.trim(), principalKey: _principalKey.text.trim(),
          name: _name.text.trim(), email: _email.text.trim(), password: _password.text,
        );
      } else {
        result = await api.register(
          inviteCode: _inviteCode.text.trim(), name: _name.text.trim(),
          email: _email.text.trim(), password: _password.text,
        );
      }
      LocalStore.instance.authToken = result.token;
      LocalStore.instance.authUser = result.user.toJson();
      if (!mounted) return;
      // Home, where the router's roleLanding sends students to their School
      // page and parents to their children (and the phone apps to their
      // own first page).
      context.go('/home');
    } on AuthException catch (e) {
      if (!mounted) return;
      // AuthApi already ran every DioException through the shared error
      // path, so this is the server's (or the connection's) own sentence.
      setState(() => _error = serverErrorMessage(e));
    } catch (e) {
      // Not a request failure -- AuthApi turns every one into an
      // AuthException -- but something like a response that failed to
      // parse. This used to say "Could not reach the server", sending a
      // teacher to check a connection that worked (Task 802 audit).
      if (!mounted) return;
      setState(() => _error = 'Sign-in failed unexpectedly (${serverErrorMessage(e)}). '
          'Try again, and tell your school admin if it keeps happening.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  /// Collapsed by default: this is the operator's one-time path for a school
  /// that has no principal yet, not an alternative to an invite. The server
  /// refuses it once the school has a principal.
  Widget _firstPrincipalSection(ThemeData theme) {
    return Theme(
      data: theme.copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        key: const Key('register-first-principal'),
        tilePadding: EdgeInsets.zero,
        childrenPadding: EdgeInsets.zero,
        initiallyExpanded: _firstPrincipal,
        onExpansionChanged: (open) => setState(() {
          _firstPrincipal = open;
          _error = null;
        }),
        title: Text('First principal of a new school', style: theme.textTheme.titleSmall),
        subtitle: Text(
          'Only with the principal key your AcademicOS operator gave you, '
          'and only if your school has no principal yet.',
          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
        ),
        children: [
          const SizedBox(height: 8),
          TextFormField(
            key: const Key('register-school-id'),
            controller: _schoolId,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              labelText: 'School ID',
              hintText: "The new school's ID, from your operator",
              prefixIcon: Icon(Icons.apartment_outlined),
              border: OutlineInputBorder(),
            ),
            validator: (v) =>
                (_firstPrincipal && (v == null || v.trim().isEmpty)) ? 'Required' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            key: const Key('register-principal-key'),
            controller: _principalKey,
            obscureText: true,
            textInputAction: TextInputAction.done,
            decoration: const InputDecoration(
              labelText: 'Principal key',
              prefixIcon: Icon(Icons.key_outlined),
              border: OutlineInputBorder(),
            ),
            validator: (v) =>
                (_firstPrincipal && (v == null || v.trim().isEmpty)) ? 'Required' : null,
          ),
          const SizedBox(height: 4),
        ],
      ),
    );
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
                    // This switch is how a teacher gets from Sign in to the
                    // invite form at all, so it has to take a thumb. Not
                    // `phoneTapTarget`: a SegmentedButton drops the minimum
                    // height out of any style it is given, so the size has to
                    // be built from padding -- see [phoneSegmentTapTarget].
                    style: phoneSegmentTapTarget(context),
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
                            if (!_firstPrincipal) ...[
                              TextFormField(
                                key: const Key('register-invite-code'),
                                controller: _inviteCode,
                                textInputAction: TextInputAction.next,
                                decoration: const InputDecoration(
                                  labelText: 'Invite code',
                                  hintText: 'The code your principal gave you',
                                  prefixIcon: Icon(Icons.confirmation_number_outlined),
                                  border: OutlineInputBorder(),
                                ),
                                validator: (v) =>
                                    (v == null || v.trim().isEmpty) ? 'Required' : null,
                              ),
                              const SizedBox(height: 12),
                            ],
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
                          if (_registering) ...[
                            const SizedBox(height: 8),
                            _firstPrincipalSection(theme),
                          ],
                          const SizedBox(height: 20),
                          FilledButton(
                            // The form's one submit.
                            style: phoneTapTarget(context),
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
                          if (!_registering)
                            TextButton(
                              // Students and parents may sign in without a password (ROLE-2).
                              onPressed: _submitting ? null : _signInWithCode,
                              child: const Text('Student or parent? Email me a sign-in code'),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _registering
                        ? 'Your school and role come from your invite. '
                            'Ask your principal for one if you do not have it.'
                        : 'Teachers approve papers, students track their schedule -- '
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
