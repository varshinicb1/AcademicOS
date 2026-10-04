import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../core/local_engine/local_store.dart';
import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../../data/datasources/api/auth_api.dart';
import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/shell.dart';

/// Schools whose agreement this run has seen accepted, by user, so the shell
/// rebuilding (every page change) does not ask the server again.
final Set<String> _acceptedFor = {};

/// Forget what this run has seen (tests).
@visibleForTesting
void resetPilotAgreementRun() => _acceptedFor.clear();

/// The Phase 1 pilot agreement comes before everything else for a principal
/// whose school has not accepted it: the console shows the agreement in place
/// of its pages until it is accepted. Everyone else, and a principal whose
/// school has accepted, goes straight to the page. If the server cannot be
/// asked (offline, or a server without the agreement), the pages open: the
/// acceptance is a record, not a lock on the school's own data.
class PilotAgreementGate extends StatefulWidget {
  const PilotAgreementGate({super.key, required this.child, this.role, this.userId});

  final Widget child;

  /// Who is signed in; the session's when null (tests pass them).
  final String? role;
  final String? userId;

  @override
  State<PilotAgreementGate> createState() => _PilotAgreementGateState();
}

class _PilotAgreementGateState extends State<PilotAgreementGate> {
  Map<String, dynamic>? _pending;
  bool _checking = false;

  String get _user => widget.userId ?? (Hive.isBoxOpen('academicos_cache') ? CurrentSession.userId : '');

  @override
  void initState() {
    super.initState();
    final role = widget.role ?? signedInRole();
    if (role != 'principal' || _user.isEmpty || _acceptedFor.contains(_user) || !GetIt.I.isRegistered<Dio>()) {
      return;
    }
    _checking = true;
    _check();
  }

  Future<void> _check() async {
    final user = _user;
    try {
      final r = await GetIt.I<Dio>().get('/pilot-agreement');
      final data = Map<String, dynamic>.from(r.data as Map);
      if (data['accepted'] != null) {
        _acceptedFor.add(user);
      } else {
        _pending = data;
      }
    } catch (e) {
      debugPrint('pilot agreement: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final pending = _pending;
    if (pending == null) return widget.child;
    return PilotAgreementPage(
      initial: pending,
      gate: true,
      onAccepted: () => setState(() {
        _acceptedFor.add(_user);
        _pending = null;
      }),
    );
  }
}

/// The agreement itself: its text, who accepted it and when, and for a
/// principal whose school has not, the form to accept it. Opened by the gate
/// above, and from Settings at any time.
class PilotAgreementPage extends StatefulWidget {
  const PilotAgreementPage({super.key, this.initial, this.gate = false, this.onAccepted});

  /// The server's answer, when the gate already has it; loaded when null.
  final Map<String, dynamic>? initial;

  /// Shown before the console: no way back, but a way to sign out.
  final bool gate;
  final VoidCallback? onAccepted;

  @override
  State<PilotAgreementPage> createState() => _PilotAgreementPageState();
}

class _PilotAgreementPageState extends State<PilotAgreementPage> {
  Map<String, dynamic>? _data;
  String? _loadError;
  final _legalName = TextEditingController();
  final _signatory = TextEditingController();
  final _designation = TextEditingController(text: 'Principal');
  bool _read = false;
  bool _authorised = false;
  bool _submitting = false;
  String? _submitError;

  @override
  void initState() {
    super.initState();
    _signatory.text = Hive.isBoxOpen('academicos_cache') ? CurrentSession.name : '';
    for (final c in [_legalName, _signatory, _designation]) {
      c.addListener(() => setState(() {}));
    }
    final initial = widget.initial;
    if (initial != null) {
      _show(initial);
    } else {
      _load();
    }
  }

  @override
  void dispose() {
    _legalName.dispose();
    _signatory.dispose();
    _designation.dispose();
    super.dispose();
  }

  void _show(Map<String, dynamic> data) {
    _data = data;
    if (_legalName.text.isEmpty) _legalName.text = (data['schoolName'] as String?) ?? '';
  }

  Future<void> _load() async {
    setState(() => _loadError = null);
    try {
      final r = await GetIt.I<Dio>().get('/pilot-agreement');
      if (mounted) setState(() => _show(Map<String, dynamic>.from(r.data as Map)));
    } catch (e) {
      if (mounted) setState(() => _loadError = serverErrorMessage(e));
    }
  }

  bool get _complete =>
      _read && _authorised && _legalName.text.trim().length >= 2 && _signatory.text.trim().length >= 2 &&
      _designation.text.trim().length >= 2;

  Future<void> _accept() async {
    final data = _data!;
    setState(() {
      _submitting = true;
      _submitError = null;
    });
    try {
      final r = await GetIt.I<Dio>().post('/pilot-agreement/accept', data: {
        'version': data['version'],
        'sha256': data['sha256'],
        'schoolLegalName': _legalName.text.trim(),
        'signatoryName': _signatory.text.trim(),
        'designation': _designation.text.trim(),
        'agree': true,
      });
      if (!mounted) return;
      setState(() => _data = Map<String, dynamic>.from(r.data as Map));
      widget.onAccepted?.call();
    } catch (e) {
      if (mounted) setState(() => _submitError = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _signOut() async {
    await GetIt.I<AuthApi>().logout();
    LocalStore.instance.clearAuth();
    if (mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final data = _data;
    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: !widget.gate,
        leading: widget.gate ? null : shellLeading(context),
        title: const Text('Phase 1 pilot agreement'),
        actions: [
          if (widget.gate)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: TextButton(onPressed: _signOut, child: const Text('Sign out')),
            ),
        ],
      ),
      body: data == null
          ? (_loadError != null
              ? ErrorDisplay(message: _loadError!, onRetry: _load)
              : const Center(child: CircularProgressIndicator()))
          : Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 820),
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 48),
                  children: [
                    if (widget.gate && data['accepted'] == null) _intro(theme),
                    if (data['accepted'] != null) _acceptedCard(theme, Map<String, dynamic>.from(data['accepted'] as Map)),
                    Card(
                      margin: const EdgeInsets.only(top: 16),
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
                        child: SelectionArea(child: AgreementText(text: data['text'] as String? ?? '')),
                      ),
                    ),
                    if (data['accepted'] == null)
                      signedInRole() == 'principal' || widget.gate
                          ? _acceptForm(theme)
                          : Padding(
                              padding: const EdgeInsets.only(top: 16),
                              child: Text('Your principal accepts this agreement for the school.',
                                  style: theme.textTheme.bodyMedium),
                            ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _intro(ThemeData theme) => Card(
        color: theme.colorScheme.primaryContainer,
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Icon(Icons.handshake_outlined, color: theme.colorScheme.onPrimaryContainer, size: 28),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Welcome to the AcademicOS Phase 1 pilot',
                    style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700, color: theme.colorScheme.onPrimaryContainer)),
                const SizedBox(height: 6),
                Text(
                  'Before your school starts, please read and accept the pilot agreement. It covers how '
                  'Phase 1 runs, confidentiality on both sides, and how your school\'s data is shared and '
                  'protected. It takes about five minutes to read, and you can open it again any time '
                  'from Settings.',
                  style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onPrimaryContainer),
                ),
              ]),
            ),
          ]),
        ),
      );

  Widget _acceptedCard(ThemeData theme, Map<String, dynamic> a) => Card(
        margin: EdgeInsets.zero,
        child: ListTile(
          leading: Icon(Icons.verified_outlined, color: theme.colorScheme.primary),
          title: Text('Accepted for ${a['schoolLegalName']}'),
          subtitle: Text('By ${a['signatoryName']}, ${a['designation']}, on ${_when(a['acceptedAt'] as String?)} '
              '(${a['acceptedEmail']}). Version ${a['version']}.'),
        ),
      );

  Widget _acceptForm(ThemeData theme) {
    final school = _legalName.text.trim().isEmpty ? 'the school' : _legalName.text.trim();
    return Card(
      margin: const EdgeInsets.only(top: 16),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text('Accept for your school', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          TextField(
            key: const Key('pilot-legal-name'),
            controller: _legalName,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'School\'s legal name',
              helperText: 'As registered, for example as on the CBSE affiliation letter',
            ),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(builder: (context, c) {
            final name = TextField(
              key: const Key('pilot-signatory'),
              controller: _signatory,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Your full name'),
            );
            final role = TextField(
              key: const Key('pilot-designation'),
              controller: _designation,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Your designation'),
            );
            if (c.maxWidth < 480) return Column(children: [name, const SizedBox(height: 12), role]);
            return Row(children: [Expanded(child: name), const SizedBox(width: 12), Expanded(child: role)]);
          }),
          const SizedBox(height: 12),
          CheckboxListTile(
            key: const Key('pilot-read'),
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _read,
            onChanged: (v) => setState(() => _read = v ?? false),
            title: const Text('I have read the whole agreement, including confidentiality (Part B) and data '
                'sharing (Part C).'),
          ),
          CheckboxListTile(
            key: const Key('pilot-authorised'),
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _authorised,
            onChanged: (v) => setState(() => _authorised = v ?? false),
            title: Text('I am authorised to accept it for $school.'),
          ),
          if (_submitError != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(_submitError!, style: TextStyle(color: theme.colorScheme.error)),
            ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.icon(
              key: const Key('pilot-agree'),
              onPressed: _complete && !_submitting ? _accept : null,
              icon: _submitting
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.check),
              label: const Text('I agree'),
            ),
          ),
        ]),
      ),
    );
  }
}

const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

String _when(String? iso) {
  final t = iso == null ? null : DateTime.tryParse(iso)?.toLocal();
  if (t == null) return iso ?? '';
  String two(int n) => n.toString().padLeft(2, '0');
  return '${t.day} ${_months[t.month - 1]} ${t.year}, ${two(t.hour)}:${two(t.minute)}';
}

/// The agreement's text as the server sends it: a title line ("# "), part
/// headings ("## ") and numbered clauses whose first sentence is their name.
class AgreementText extends StatelessWidget {
  const AgreementText({super.key, required this.text});

  final String text;

  static final _clause = RegExp(r'^(\d+)\. ([^.]+\.) (.*)$');

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final body = theme.textTheme.bodyMedium?.copyWith(height: 1.5);
    final children = <Widget>[];
    for (final raw in text.split('\n')) {
      final line = raw.trim();
      if (line.isEmpty) continue;
      if (line.startsWith('## ')) {
        children.add(Padding(
          padding: const EdgeInsets.only(top: 20, bottom: 8),
          child: Text(line.substring(3), style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
        ));
      } else if (line.startsWith('# ')) {
        children.add(Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(line.substring(2), style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
        ));
      } else {
        final m = _clause.firstMatch(line);
        children.add(Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: m == null
              ? Text(line, style: body)
              : Text.rich(TextSpan(style: body, children: [
                  TextSpan(text: '${m.group(1)}. ${m.group(2)} ', style: const TextStyle(fontWeight: FontWeight.w700)),
                  TextSpan(text: m.group(3)),
                ])),
        ));
      }
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: children);
  }
}
