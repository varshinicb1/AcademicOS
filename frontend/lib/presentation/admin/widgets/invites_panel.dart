import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart' show serverErrorMessage;
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/copyable_value.dart';

/// Where a principal lets people into their school. Since 2026-09-21 an
/// account can only be created with an invite code (users.py): the server
/// takes the new account's school and role from the invite, so this panel is
/// the only way a teacher or student joins. Before that, anyone who typed a
/// school's id on the register screen became its teacher.
///
/// Create (role, optional email, expiry), list every invite with who used it,
/// and withdraw an unused one. Everything is scoped server-side to the
/// principal's own school; nothing here sends a school id.
///
/// A parent's invite names their child (QA S-06, 2026-10-01): it goes through
/// POST /students/{id}/guardian-invites, so the account made with it is
/// linked to that child. Until then a parent could be invited only by a bulk
/// "parents" import.
///
/// Online build only: the offline single-device build has no server
/// accounts and never shows the admin console's server-backed roster.
class InvitesPanel extends StatefulWidget {
  const InvitesPanel({super.key, this.api});

  /// Injected in tests; the app uses the registered AuthApi.
  final AuthApi? api;

  @override
  State<InvitesPanel> createState() => _InvitesPanelState();
}

const _roleNames = {'teacher': 'Teacher', 'student': 'Student', 'parent': 'Parent'};

class _InvitesPanelState extends State<InvitesPanel> {
  late final AuthApi _api = widget.api ?? GetIt.I<AuthApi>();
  final _email = TextEditingController();
  String _role = 'teacher';
  int _days = 14;
  bool _busy = false;
  String? _error;
  List<Invite>? _invites;
  // A parent's invite: whose parent, and how they are related.
  List<AuthUser>? _students;
  String? _studentsError;
  String? _childId;
  String _relation = 'mother';

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      final rows = await _api.invites();
      if (mounted) setState(() => _invites = rows);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load invites: ${serverErrorMessage(e)}');
    }
  }

  /// The students a parent's invite can name, read the first time Parent is
  /// chosen.
  Future<void> _loadStudents() async {
    if (_students != null) return;
    try {
      final rows = await _api.usersForSchool(role: 'student');
      rows.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
      if (mounted) setState(() => _students = rows);
    } catch (e) {
      if (mounted) setState(() => _studentsError = 'Could not load the students: ${serverErrorMessage(e)}');
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
      await _refresh();
    } catch (e) {
      // An AuthException's own message, or -- for anything else, which is
      // not only the network (a response that fails to parse lands here
      // too) -- what actually failed. This said "Could not reach the server"
      // for all of it until Task 802.
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _create() async {
    if (_role == 'parent' && _childId == null) {
      setState(() => _error = 'Choose the child this parent is for.');
      return;
    }
    await _run(() async {
      final email = _email.text.trim();
      final String code, expiresAt, who;
      if (_role == 'parent') {
        final child = _students!.firstWhere((s) => s.id == _childId);
        final invite = await _api.createGuardianInvite(
            studentId: child.id, relation: _relation, email: email, expiresInDays: _days);
        code = invite.code;
        expiresAt = invite.expiresAt;
        who = "${child.name}'s ${invite.relation}${invite.email != null ? ' (${invite.email})' : ''}";
      } else {
        final invite = await _api.createInvite(role: _role, email: email, expiresInDays: _days);
        code = invite.code;
        expiresAt = invite.expiresAt;
        who = '${invite.role}${invite.email != null ? ' (${invite.email})' : ''}';
      }
      _email.clear();
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Invite created'),
          content: SizedBox(
            width: 440,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Give this code to the $who. It works once and expires ${_date(expiresAt)}.'
                    '${_role == 'parent' ? ' The account made with it is linked to their child.' : ''}'),
                const Gap(12),
                CopyableValue(value: code, copiedMessage: 'Invite code copied.', copyLabel: 'Copy code'),
              ],
            ),
          ),
          actions: [
            // A link opens Create account with the code already filled in,
            // so nobody types a 22-character code.
            TextButton(
              key: const ValueKey('invite-copy-link'),
              onPressed: () => copyWithNotice(ctx, inviteLink(code), 'Invite link copied.'),
              child: const Text('Copy invite link'),
            ),
            FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
          ],
        ),
      );
    });
  }

  Future<void> _revoke(Invite invite) async {
    final ok = await confirmAction(context,
        title: 'Withdraw this invite?',
        message: 'The code ${invite.code} stops working at once, and whoever you gave it to cannot '
            'create their account with it. You can create a new invite later.',
        confirmLabel: 'Withdraw invite');
    if (!ok || !mounted) return;
    await _run(() async {
      await _api.revokeInvite(invite.code);
    });
  }

  static String _date(String iso) {
    final d = DateTime.tryParse(iso)?.toLocal();
    if (d == null) return iso;
    return '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
  }

  Widget _childPicker(ThemeData theme) {
    final students = _students;
    if (_studentsError != null) {
      return Text(_studentsError!, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error));
    }
    if (students == null) return const LinearProgressIndicator();
    if (students.isEmpty) {
      return Text('No students have joined yet. Invite the student first; then invite their parents.',
          style: theme.textTheme.bodySmall);
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      DropdownMenu<String>(
        key: const ValueKey('invite-child'),
        initialSelection: _childId,
        enableFilter: true,
        requestFocusOnTap: true,
        expandedInsets: EdgeInsets.zero,
        label: const Text('Child'),
        hintText: 'Type a name',
        dropdownMenuEntries: [
          for (final s in students) DropdownMenuEntry(value: s.id, label: s.name),
        ],
        onSelected: _busy ? null : (id) => setState(() => _childId = id),
      ),
      const Gap(12),
      DropdownButtonFormField<String>(
        key: const ValueKey('invite-relation'),
        initialValue: _relation,
        decoration: const InputDecoration(labelText: 'Relation'),
        items: [
          for (final r in guardianRelations)
            DropdownMenuItem(value: r, child: Text(r[0].toUpperCase() + r.substring(1))),
        ],
        onChanged: _busy ? null : (v) => setState(() => _relation = v ?? 'guardian'),
      ),
      const Gap(12),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Invite people', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const Gap(4),
        Text('Teachers, students and parents join your school only with a code you issue here. '
            'Each code works once.', style: muted),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SegmentedButton<String>(
                key: const ValueKey('invite-role'),
                segments: [
                  for (final e in _roleNames.entries) ButtonSegment(value: e.key, label: Text(e.value)),
                ],
                selected: {_role},
                onSelectionChanged: _busy
                    ? null
                    : (s) {
                        setState(() {
                          _role = s.first;
                          _error = null;
                        });
                        if (_role == 'parent') _loadStudents();
                      },
              ),
              const Gap(12),
              if (_role == 'parent') _childPicker(theme),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'Email (optional)',
                  hintText: 'Only this person can use the code',
                ),
              ),
              const Gap(12),
              DropdownButtonFormField<int>(
                initialValue: _days,
                decoration: const InputDecoration(labelText: 'Expires after'),
                items: const [
                  DropdownMenuItem(value: 7, child: Text('7 days')),
                  DropdownMenuItem(value: 14, child: Text('14 days')),
                  DropdownMenuItem(value: 30, child: Text('30 days')),
                  DropdownMenuItem(value: 90, child: Text('90 days')),
                ],
                onChanged: _busy ? null : (v) => setState(() => _days = v ?? 14),
              ),
              const Gap(12),
              FilledButton.icon(
                key: const ValueKey('invite-create'),
                onPressed: _busy ? null : _create,
                style: phoneTapTarget(context),
                icon: const Icon(Icons.add),
                label: const Text('Create invite'),
              ),
              if (_error != null) ...[
                const Gap(8),
                Text(_error!, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error)),
              ],
            ],
          ),
        ),
        const Gap(12),
        if (_invites == null && _error == null)
          const Padding(padding: EdgeInsets.all(12), child: Center(child: CircularProgressIndicator()))
        else if (_invites != null && _invites!.isEmpty)
          Text('No invites yet. Create one above for each teacher, student or parent who should join.',
              style: muted)
        else if (_invites != null)
          AppCard(
            child: Column(
              children: [
                for (final i in _invites!)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(switch (i.role) {
                      'student' => Icons.person_outline,
                      'parent' => Icons.family_restroom_outlined,
                      _ => Icons.co_present_outlined,
                    }),
                    title: Text('${_roleNames[i.role] ?? i.role}${i.email != null ? ' · ${i.email}' : ''}'),
                    subtitle: Text(switch (i.status) {
                      'used' => 'Used ${_date(i.usedAt ?? '')}',
                      'revoked' => 'Withdrawn ${_date(i.revokedAt ?? '')}',
                      'expired' => 'Expired ${_date(i.expiresAt)}',
                      _ => 'Open · expires ${_date(i.expiresAt)} · ${i.code}',
                    }),
                    trailing: i.isOpen
                        ? TextButton(
                            onPressed: _busy ? null : () => _revoke(i),
                            style: phoneTapTarget(context),
                            child: const Text('Withdraw'),
                          )
                        : null,
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

/// The link that opens Create account with [code] filled in: this site's
/// own address, so it is right on any deployment. Off the web (a desktop
/// build, a test) there is no origin to name, and the path alone is given:
/// `Uri.origin` throws for a file: address.
String inviteLink(String code) {
  final base = Uri.base;
  final origin = base.scheme == 'http' || base.scheme == 'https' ? base.origin : '';
  return '$origin/#/login?invite=${Uri.encodeQueryComponent(code)}';
}
