import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/local_store.dart';
import '../../../core/theme/emergera.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/theme_toggle.dart';
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
            Text(
                _emailCode
                    ? 'Principals, students and parents can sign in with a code sent to their email instead '
                        'of a password.'
                    : 'Principals: your password is reset by AcademicOS. Contact them.',
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

  /// Sign in with a one-time code sent by email (principals, students and
  /// parents): ask for a code, type it, signed in. The code field takes the
  /// focus once it is sent, Enter moves on at each step, and a code that did
  /// not arrive can be sent again or sent to another address.
  Future<void> _signInWithCode() async {
    final email = TextEditingController(text: _email.text.trim());
    final code = TextEditingController();
    var sent = false;
    var busy = false;
    String? message;
    var isError = false;
    final result = await showDialog<Map<String, dynamic>>(context: context, builder: (ctx) => StatefulBuilder(
      builder: (ctx, set) {
        final theme = Theme.of(ctx);
        // A request still out when the dialog closes must not rebuild it.
        void update(VoidCallback change) {
          if (ctx.mounted) set(change);
        }

        Future<void> send() async {
          if (busy) return;
          final address = email.text.trim();
          if (!address.contains('@')) {
            update(() {
              message = 'Type the email address of your AcademicOS account.';
              isError = true;
            });
            return;
          }
          update(() => busy = true);
          try {
            final r = await GetIt.I<Dio>().post('/auth/code/request', data: {'email': address});
            update(() {
              sent = true;
              code.clear();
              message = (r.data as Map)['detail'] as String?;
              isError = false;
            });
          } on DioException catch (e) {
            update(() {
              message = serverErrorMessage(e);
              isError = true;
            });
          } finally {
            update(() => busy = false);
          }
        }

        Future<void> verify() async {
          if (busy) return;
          if (!RegExp(r'^\d{6}$').hasMatch(code.text.trim())) {
            update(() {
              message = 'The code is the 6 digits in the email.';
              isError = true;
            });
            return;
          }
          update(() => busy = true);
          try {
            final r = await GetIt.I<Dio>()
                .post('/auth/code/verify', data: {'email': email.text.trim(), 'code': code.text.trim()});
            if (ctx.mounted) Navigator.pop(ctx, Map<String, dynamic>.from(r.data as Map));
          } on DioException catch (e) {
            update(() {
              message = serverErrorMessage(e);
              isError = true;
              busy = false;
            });
          }
        }

        return AlertDialog(
          title: const Text('Sign in with a code'),
          content: SizedBox(
            width: 400,
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Text(
                sent
                    ? 'Check the inbox of ${email.text.trim()} (and its spam folder) for an email from AcademicOS.'
                    : 'We email you a 6-digit code. It works once, for 10 minutes. For principals, students '
                        'and parents.',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              TextField(
                key: const Key('code-email'),
                controller: email,
                enabled: !sent && !busy,
                autofocus: !sent,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => send(),
                decoration: const InputDecoration(labelText: 'Email'),
              ),
              if (sent) ...[
                const SizedBox(height: 8),
                TextField(
                  key: const Key('code-digits'),
                  controller: code,
                  autofocus: true,
                  enabled: !busy,
                  keyboardType: TextInputType.number,
                  autofillHints: const [AutofillHints.oneTimeCode],
                  maxLength: 6,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => verify(),
                  decoration: const InputDecoration(labelText: '6-digit code from the email', counterText: ''),
                ),
                Wrap(spacing: 4, children: [
                  TextButton(onPressed: busy ? null : send, child: const Text('Send a new code')),
                  TextButton(
                    onPressed: busy
                        ? null
                        : () => set(() {
                              sent = false;
                              message = null;
                            }),
                    child: const Text('Use another email'),
                  ),
                ]),
              ],
              if (message != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(message!,
                      style: theme.textTheme.bodySmall?.copyWith(
                          color: isError ? theme.colorScheme.error : theme.colorScheme.onSurfaceVariant)),
                ),
            ]),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            FilledButton(
              key: const Key('code-submit'),
              onPressed: busy ? null : (sent ? verify : send),
              child: busy
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(sent ? 'Sign in' : 'Send code'),
            ),
          ],
        );
      },
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
    // Wide screens show the brand beside the form; a phone shows a compact
    // header and the form, with no dead space above it (owner, 2026-10-04:
    // "the login page looks so shit with too much empty space").
    final wide = MediaQuery.sizeOf(context).width >= 900;
    final form = _formColumn(theme, colors, wide: wide);
    return Scaffold(
      body: SafeArea(
        child: Stack(children: [
          if (wide)
            Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              const Expanded(flex: 11, child: _BrandPanel()),
              Expanded(
                flex: 9,
                child: Center(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 32),
                    child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 420), child: form),
                  ),
                ),
              ),
            ])
          else
            Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
                child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 440), child: form),
              ),
            ),
          // Light or dark before signing in, as on every page after (the
          // brand template's theme toggle).
          const Positioned(top: 4, right: 4, child: ThemeToggleButton()),
        ]),
      ),
    );
  }

  Widget _formColumn(ThemeData theme, ColorScheme colors, {required bool wide}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (wide)
          Text(_registering ? 'Create your account' : 'Welcome back',
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700, color: colors.onSurface))
        else
          Padding(
            // Room for the theme toggle in the corner.
            padding: const EdgeInsets.only(right: 36, bottom: 10),
            child: Row(children: [
              Image.asset('assets/brand/academicos_mark.png',
                  width: 48, height: 48, filterQuality: FilterQuality.medium, semanticLabel: 'AcademicOS'),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('AcademicOS',
                      style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800, color: colors.onSurface)),
                  Text('Run your CBSE school in one place',
                      style: theme.textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
                ]),
              ),
            ]),
          ),
        const SizedBox(height: 6),
        Text(
          _registering
              ? 'Create your school account to get started.'
              : 'Sign in to your school to continue.',
          style: theme.textTheme.bodyMedium?.copyWith(color: colors.onSurfaceVariant),
        ),
        const SizedBox(height: 18),
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
        const SizedBox(height: 14),
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
                            style: theme.textTheme.bodyMedium?.copyWith(color: colors.onErrorContainer),
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
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                  ],
                  TextFormField(
                    controller: _name,
                    textInputAction: TextInputAction.next,
                    autofillHints: const [AutofillHints.name],
                    decoration: const InputDecoration(
                      labelText: 'Your name',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                    validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
                  ),
                  const SizedBox(height: 12),
                ],
                TextFormField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  autofillHints: const [AutofillHints.email],
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.email_outlined),
                  ),
                  validator: (v) => (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _password,
                  obscureText: _obscurePassword,
                  textInputAction: TextInputAction.done,
                  autofillHints: [_registering ? AutofillHints.newPassword : AutofillHints.password],
                  onFieldSubmitted: (_) => _submit(),
                  decoration: InputDecoration(
                    labelText: 'Password',
                    helperText: _registering ? 'At least 8 characters' : null,
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      tooltip: _obscurePassword ? 'Show password' : 'Hide password',
                      icon: Icon(_obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                  validator: (v) => (v == null || v.length < 8) ? 'At least 8 characters' : null,
                ),
                const SizedBox(height: 18),
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
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(_registering ? 'Create account' : 'Sign in'),
                  ),
                ),
                if (!_registering && _googleClientId != null) ...[
                  const SizedBox(height: 12),
                  Row(children: [
                    const Expanded(child: Divider()),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      child: Text('or', style: theme.textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
                    ),
                    const Expanded(child: Divider()),
                  ]),
                  const SizedBox(height: 10),
                  Center(
                    child: GoogleSignInButton(
                      clientId: _googleClientId!,
                      onCredential: _signInWithGoogle,
                      onProblem: (message) => setState(() => _error = message),
                    ),
                  ),
                ],
                if (!_registering) ...[
                  const SizedBox(height: 6),
                  Wrap(alignment: WrapAlignment.center, spacing: 4, children: [
                    TextButton(
                      key: const Key('forgot-password'),
                      onPressed: _submitting ? null : _forgotPassword,
                      child: const Text('Forgot password?'),
                    ),
                    if (_emailCode)
                      TextButton(
                        // Principals, students and parents may sign in without a password
                        // (ROLE-2; principals since the Phase 1 pilot). Teachers use theirs.
                        key: const Key('email-code'),
                        onPressed: _submitting ? null : _signInWithCode,
                        child: const Text('Email me a sign-in code'),
                      ),
                  ]),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        Text(
          _registering
              ? (_firstPrincipal
                  ? 'The principal key works once per school. Lost it? Ask AcademicOS.'
                  : 'Your school and role come from your invite. '
                      'Ask your principal for one if you do not have it.')
              : 'One sign-in for principals, teachers, students and parents: '
                  'each sees their own pages.',
          style: theme.textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Center(
          child: TextButton.icon(
            key: const Key('how-joining-works'),
            onPressed: () => showDialog<void>(context: context, builder: (_) => const _HowJoiningWorks()),
            icon: const Icon(Icons.help_outline, size: 18),
            label: const Text('New to AcademicOS? How your school joins'),
          ),
        ),
      ],
    );
  }
}

/// The brand beside the form on a wide screen: what AcademicOS does, in the
/// school's words, and how a school joins.
class _BrandPanel extends StatelessWidget {
  const _BrandPanel();

  static const _features = <(IconData, String, String)>[
    (Icons.description_outlined, 'Question papers in minutes',
        'Board-pattern papers with answer keys, from the NCERT books your school uses.'),
    (Icons.calendar_month_outlined, 'Timetable, cover and lesson plans',
        'Built from your calendar, and kept right when a teacher is away.'),
    (Icons.fact_check_outlined, 'Homework, marks and term reports',
        'Every class at a glance, with report cards for parents.'),
    (Icons.groups_outlined, 'One place for everyone',
        'Principal, teachers, students and parents each see what they need.'),
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dark = theme.brightness == Brightness.dark;
    final ink = dark ? const Color(0xFFF5F5F7) : const Color(0xFF1D1D1F);
    final muted = dark ? const Color(0xFFA1A3B3) : const Color(0xFF5F5F6A);
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.fromLTRB(44, 40, 44, 32),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(Em.radiusLg + 4),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: dark
              ? const [Color(0xFF151A30), Color(0xFF0E1120), Color(0xFF2A1408)]
              : const [Color(0xFFFFF7F2), Color(0xFFFFFFFF), Color(0xFFFFE9DC)],
        ),
        border: Border.all(color: dark ? const Color(0x22FFFFFF) : const Color(0x1AC2410C)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Image.asset('assets/brand/academicos_mark.png',
              width: 56, height: 56, filterQuality: FilterQuality.medium, semanticLabel: 'AcademicOS'),
          const SizedBox(width: 14),
          Text('AcademicOS',
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800, color: ink)),
        ]),
        const Spacer(flex: 2),
        Text('Run your CBSE school\nin one place.',
            style: theme.textTheme.displaySmall?.copyWith(
                fontWeight: FontWeight.w800, height: 1.15, color: ink, letterSpacing: -0.5)),
        const SizedBox(height: 12),
        Text('Papers, timetables, lesson plans, homework and reports for classes 6 to 10, '
            'from the NCERT books.',
            style: theme.textTheme.titleMedium?.copyWith(color: muted, height: 1.4)),
        const SizedBox(height: 28),
        for (final (icon, title, line) in _features)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Em.ember.withValues(alpha: dark ? 0.18 : 0.10),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, size: 22, color: dark ? Em.ember : Em.emberDeep),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(title, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700, color: ink)),
                  const SizedBox(height: 2),
                  Text(line, style: theme.textTheme.bodyMedium?.copyWith(color: muted, height: 1.35)),
                ]),
              ),
            ]),
          ),
        const Spacer(flex: 2),
        Text('For CBSE schools · Classes 6 to 10 · Your data stays your school\'s',
            style: theme.textTheme.bodySmall?.copyWith(color: muted)),
      ]),
    );
  }
}

/// How a school and its people get in: the onboarding, in three steps, on
/// the sign-in page before anyone has an account.
class _HowJoiningWorks extends StatelessWidget {
  const _HowJoiningWorks();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Widget step(int n, String title, String body) => Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: Em.ember.withValues(alpha: 0.14),
              child: Text('$n', style: const TextStyle(color: Em.emberDeep, fontWeight: FontWeight.w800)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(body, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ]),
            ),
          ]),
        );
    return AlertDialog(
      title: const Text('How your school joins'),
      content: SizedBox(
        width: 460,
        child: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            step(1, 'The principal opens the school link',
                'AcademicOS sends your principal a one-time link. It opens Create account with the school '
                    'filled in: they add their name, email and a password.'),
            step(2, 'A guided setup',
                'Six short steps: the school name and logo, classes and sections, the year and bell, '
                    'teachers, periods, and a first real question paper. The Guide stays in the menu after.'),
            step(3, 'Everyone else is invited',
                'The principal sends each teacher, student and parent an invite link from Setup, '
                    'Invite people. They open it and create their account; their role comes with it.'),
            step(4, 'Already have an account?',
                'Sign in with your email and password, or with Google if your school uses it.'),
          ]),
        ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Got it'))],
    );
  }
}
