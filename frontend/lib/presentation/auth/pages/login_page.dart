import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../workspace/profiles.dart';
import '../widgets/google_button.dart';

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
  /// Opened from an invite link (`/login?invite=<code>`) or a school-setup
  /// link (`/login?school=<id>`): the form starts on that path, pre-filled.
  const LoginPage({super.key, this.inviteCode, this.schoolId});

  final String? inviteCode;
  final String? schoolId;

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
  // The Google client id when this deployment has Google sign-in (INT-1).
  String? _googleClientId;
  // Whether this deployment can email a sign-in code. Offered only once the
  // server says so: with no school email set up, a tap answered 503 (N-8-9).
  bool _emailCode = false;

  @override
  void initState() {
    super.initState();
    _applyLink();
    if (!GetIt.I.isRegistered<Dio>()) return;     // a widget test with no server
    GetIt.I<Dio>().get('/auth/providers').then((r) {
      final data = r.data as Map;
      final g = data['google'];
      if (!mounted) return;
      setState(() {
        if (g is Map) _googleClientId = g['clientId'] as String?;
        _emailCode = data['emailCode'] == true;
      });
    }, onError: (Object e) {
      // Without the answer the page offers the password, which works
      // regardless; the other ways in are shown only when the server has them.
      if (mounted) setState(() => _googleClientId = null);
      debugPrint('sign-in providers: ${serverErrorMessage(e)}');
    });
  }

  /// An invite link (`?invite=`) or a school-setup link (`?school=`) opens
  /// its path with the code or school filled in.
  void _applyLink() {
    final invite = widget.inviteCode?.trim() ?? '';
    final school = widget.schoolId?.trim() ?? '';
    if (invite.isNotEmpty) {
      _registering = true;
      _firstPrincipal = false;
      _inviteCode.text = invite;
    } else if (school.isNotEmpty) {
      _registering = true;
      _firstPrincipal = true;
      _schoolId.text = school;
    }
  }

  /// A link opened in a tab where the app is already on Sign in: go_router
  /// rebuilds this same page with the new query, and until 2026-10-01 only
  /// initState read it, so the code was not filled in until a reload
  /// (QA S-20).
  @override
  void didUpdateWidget(LoginPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.inviteCode != widget.inviteCode || oldWidget.schoolId != widget.schoolId) {
      setState(() {
        _error = null;
        _applyLink();
      });
    }
  }

  /// There is no self-service reset (no school email is needed to run the
  /// app), so this says who gives a forgotten password back (QA S-05): the
  /// principal resets anyone's from Staff and access, and the emailed
  /// sign-in code is offered where the school has email.
  Future<void> _forgotPassword() async {
    final theme = Theme.of(context);
    final useCode = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Forgot your password?'),
        content: SizedBox(
          width: 420,
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Teachers and staff: ask your principal. They reset it under Staff and access and give '
                'you a one-time password.'),
            const SizedBox(height: 8),
            const Text('Students and parents: tell your class teacher or the principal. The principal, or a '
                'teacher who manages people, gives you a one-time password.'),
            const SizedBox(height: 8),
            const Text('Sign in with the one-time password, then choose your own under Settings, '
                'Change password.'),
            const SizedBox(height: 8),
            Text('Principals: your password is reset by AcademicOS. Contact them.',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ]),
        ),
        actions: [
          if (_emailCode)
            TextButton(
              key: const Key('forgot-email-code'),
              onPressed: () => Navigator.pop(dialog, true),
              child: const Text('Email me a sign-in code'),
            ),
          FilledButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('OK')),
        ],
      ),
    );
    if (useCode == true && mounted) await _signInWithCode();
  }

  Future<void> _signInWithGoogle(String credential) async {
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final r = await GetIt.I<Dio>().post('/auth/google', data: {'credential': credential});
      final result = Map<String, dynamic>.from(r.data as Map);
      LocalStore.instance.signIn(result['token'] as String, Map<String, dynamic>.from(result['user'] as Map));
      if (mounted) context.go('/home');
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

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
    LocalStore.instance.signIn(result['token'] as String, Map<String, dynamic>.from(result['user'] as Map));
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
      } else if (_inviteCode.text.trim().startsWith('own_')) {
        // ROLE-4: an owner link code a school's principal issued makes an
        // owner account over that school (and later others), not a member.
        result = await api.registerOwner(
          code: _inviteCode.text.trim(), name: _name.text.trim(),
          email: _email.text.trim(), password: _password.text,
        );
      } else {
        result = await api.register(
          inviteCode: _inviteCode.text.trim(), name: _name.text.trim(),
          email: _email.text.trim(), password: _password.text,
        );
      }
      LocalStore.instance.signIn(result.token, result.user.toJson());
      if (!mounted) return;
      // Home, where the router's roleLanding sends students to their School
      // page and parents to their children (and the phone apps to their
      // own first page).
      context.go('/home');
    } on AuthException catch (e) {
      if (!mounted) return;
      // AuthApi already ran every DioException through the shared error
      // path, so this is the server's (or the connection's) own sentence.
      var message = serverErrorMessage(e);
      if (_registering && _firstPrincipal && message.toLowerCase().contains('principal key not accepted')) {
        message = 'That principal key was not accepted. Copy it again in full -- it is '
            'case-sensitive -- and check the school ID with AcademicOS.';
      }
      setState(() => _error = message);
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

  /// How this person is joining: with an invite (teachers, students and
  /// parents -- the default, and the only path that cannot name a school), or
  /// as the first principal of a new school, once, with the school ID and
  /// principal key from AcademicOS. Until 2026-10-01 the second was a
  /// collapsed row under the password, and principals stopped at the invite
  /// code's "Required" without finding it.
  Widget _joinChoice(ThemeData theme) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      SegmentedButton<bool>(
        key: const Key('register-path'),
        showSelectedIcon: false,
        segments: const [
          ButtonSegment(value: false, icon: Icon(Icons.confirmation_number_outlined),
              label: Text('I have an invite code')),
          ButtonSegment(value: true, icon: Icon(Icons.apartment_outlined),
              label: Text('Set up my school')),
        ],
        selected: {_firstPrincipal},
        onSelectionChanged: _submitting
            ? null
            : (sel) => setState(() {
                  _firstPrincipal = sel.first;
                  _error = null;
                }),
      ),
      const SizedBox(height: 8),
      Text(
        _firstPrincipal
            ? 'For the principal, once: enter the school ID and principal key AcademicOS '
                'gave you. Then invite your teachers and students from Setup, Invite people.'
            : 'Teachers, students and parents: use the invite code or link your principal sent you.',
        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
      ),
      const SizedBox(height: 12),
    ]);
  }

  List<Widget> _principalFields() => [
        TextFormField(
          key: const Key('register-school-id'),
          controller: _schoolId,
          textInputAction: TextInputAction.next,
          decoration: const InputDecoration(
            labelText: 'School ID',
            hintText: 'From AcademicOS, e.g. stmarys-hyd',
            prefixIcon: Icon(Icons.apartment_outlined),
          ),
          validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
        ),
        const SizedBox(height: 12),
        TextFormField(
          key: const Key('register-principal-key'),
          controller: _principalKey,
          obscureText: true,
          textInputAction: TextInputAction.next,
          decoration: const InputDecoration(
            labelText: 'Principal key',
            hintText: 'Paste it exactly as you received it',
            prefixIcon: Icon(Icons.key_outlined),
          ),
          validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
        ),
        const SizedBox(height: 12),
      ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Scaffold(
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
                  Center(
                    child: Image.asset('assets/brand/academicos_mark.png',
                        width: 72, height: 72, filterQuality: FilterQuality.medium, semanticLabel: 'AcademicOS'),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'AcademicOS',
                    style: theme.textTheme.headlineMedium?.copyWith(color: colors.onSurface),
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
                          // A shared family phone: continue as a child or parent already signed in (SA-8).
                          if (!_registering) const SavedProfiles(),
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
                            _joinChoice(theme),
                            if (_firstPrincipal) ..._principalFields(),
                            if (!_firstPrincipal) ...[
                              TextFormField(
                                key: const Key('register-invite-code'),
                                controller: _inviteCode,
                                textInputAction: TextInputAction.next,
                                decoration: const InputDecoration(
                                  labelText: 'Invite code',
                                  hintText: 'The code your principal gave you',
                                  helperText: 'An owner of several schools enters the owner link code here',
                                  prefixIcon: Icon(Icons.confirmation_number_outlined),
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
                              suffixIcon: IconButton(tooltip: _obscurePassword ? 'Show password' : 'Hide password', 
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
                              key: const Key('forgot-password'),
                              onPressed: _submitting ? null : _forgotPassword,
                              child: const Text('Forgot password?'),
                            ),
                          if (!_registering && _emailCode)
                            TextButton(
                              // Students and parents may sign in without a password (ROLE-2).
                              onPressed: _submitting ? null : _signInWithCode,
                              child: const Text('Student or parent? Email me a sign-in code'),
                            ),
                          if (!_registering && _googleClientId != null)
                            Center(
                              child: GoogleSignInButton(
                                clientId: _googleClientId!,
                                onCredential: _signInWithGoogle,
                                onProblem: (message) => setState(() => _error = message),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _registering
                        ? (_firstPrincipal
                            ? 'The principal key works once per school. Lost it? Ask AcademicOS.'
                            : 'Your school and role come from your invite. '
                                'Ask your principal for one if you do not have it.')
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
