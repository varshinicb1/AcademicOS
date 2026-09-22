import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart' show serverErrorMessage;
import '../../shared/widgets/common_widgets.dart';

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
/// Online build only: the offline single-device build has no server
/// accounts and never shows the admin console's server-backed roster.
class InvitesPanel extends StatefulWidget {
  const InvitesPanel({super.key, this.api});

  /// Injected in tests; the app uses the registered AuthApi.
  final AuthApi? api;

  @override
  State<InvitesPanel> createState() => _InvitesPanelState();
}

class _InvitesPanelState extends State<InvitesPanel> {
  late final AuthApi _api = widget.api ?? GetIt.I<AuthApi>();
  final _email = TextEditingController();
  String _role = 'teacher';
  int _days = 14;
  bool _busy = false;
  String? _error;
  List<Invite>? _invites;

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

  Future<void> _create() => _run(() async {
        final invite = await _api.createInvite(
          role: _role, email: _email.text.trim(), expiresInDays: _days);
        _email.clear();
        if (!mounted) return;
        await showDialog<void>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('Invite created'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Give this code to the ${invite.role}${invite.email != null ? ' (${invite.email})' : ''}. '
                    'It works once and expires ${_date(invite.expiresAt)}.'),
                const Gap(12),
                SelectableText(invite.code,
                    style: Theme.of(ctx).textTheme.titleMedium?.copyWith(fontFamily: 'monospace')),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Clipboard.setData(ClipboardData(text: invite.code)),
                child: const Text('Copy'),
              ),
              FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
            ],
          ),
        );
      });

  Future<void> _revoke(Invite invite) => _run(() async {
        await _api.revokeInvite(invite.code);
      });

  static String _date(String iso) {
    final d = DateTime.tryParse(iso)?.toLocal();
    if (d == null) return iso;
    return '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
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
        Text('Teachers and students join your school only with a code you issue here. '
            'Each code works once.', style: muted),
        const Gap(12),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'teacher', label: Text('Teacher')),
                  ButtonSegment(value: 'student', label: Text('Student')),
                ],
                selected: {_role},
                onSelectionChanged: _busy ? null : (s) => setState(() => _role = s.first),
              ),
              const Gap(12),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'Email (optional)',
                  hintText: 'Only this person can use the code',
                  border: OutlineInputBorder(),
                ),
              ),
              const Gap(12),
              DropdownButtonFormField<int>(
                initialValue: _days,
                decoration: const InputDecoration(labelText: 'Expires after', border: OutlineInputBorder()),
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
                onPressed: _busy ? null : _create,
                style: phoneTapTarget,
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
          Text('No invites yet. Create one above for each teacher or student who should join.',
              style: muted)
        else if (_invites != null)
          AppCard(
            child: Column(
              children: [
                for (final i in _invites!)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(i.role == 'student' ? Icons.person_outline : Icons.co_present_outlined),
                    title: Text('${i.role}${i.email != null ? ' · ${i.email}' : ''}'),
                    subtitle: Text(switch (i.status) {
                      'used' => 'Used ${_date(i.usedAt ?? '')}',
                      'revoked' => 'Withdrawn ${_date(i.revokedAt ?? '')}',
                      'expired' => 'Expired ${_date(i.expiresAt)}',
                      _ => 'Open · expires ${_date(i.expiresAt)} · ${i.code}',
                    }),
                    trailing: i.isOpen
                        ? TextButton(
                            onPressed: _busy ? null : () => _revoke(i),
                            style: phoneTapTarget,
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
