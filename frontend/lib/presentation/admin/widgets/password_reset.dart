import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart' show serverErrorMessage;
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/copyable_value.dart';

/// A teacher, student or parent who forgot their password had no way back in
/// (QA S-05, 2026-10-01): no reset, and the emailed sign-in code is off where
/// the school has no email set up. The principal (or a teacher with the
/// people admin area) now resets it here: the server sets a one-time
/// password, signs the person out everywhere, and answers with the password,
/// which is shown once, plainly, to read out or copy. The person then
/// chooses their own under Settings.
///
/// Online build only: the offline build has no accounts, and no AuthApi is
/// registered there, so [canResetPasswords] is false and the action is not
/// offered.
bool get canResetPasswords => GetIt.I.isRegistered<AuthApi>();

/// Asks, resets [name]'s password, then shows the temporary password.
Future<void> resetPasswordFlow(BuildContext context,
    {required String userId, required String name, AuthApi? api}) async {
  final ok = await confirmAction(context,
      title: "Reset $name's password?",
      message: '$name is signed out on every device and their current password stops working. '
          'You will see a one-time password to give them; they sign in with it and then choose '
          'their own under Settings, Change password.',
      confirmLabel: 'Reset password');
  if (!ok || !context.mounted) return;
  final PasswordReset reset;
  try {
    reset = await (api ?? GetIt.I<AuthApi>()).resetPassword(userId);
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
    return;
  }
  if (!context.mounted) return;
  await showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (dialog) => AlertDialog(
      title: Text('Temporary password for ${reset.name}'),
      content: SizedBox(
        width: 440,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('It is shown only now. Give it to them in person or by phone, not in a group message. '
              'It works until they choose their own password.'),
          const Gap(12),
          CopyableValue(value: reset.temporaryPassword, copiedMessage: 'Temporary password copied.'),
        ]),
      ),
      actions: [FilledButton(onPressed: () => Navigator.pop(dialog), child: const Text('Done'))],
    ),
  );
}

const _roleNames = {'teacher': 'Teacher', 'student': 'Student', 'parent': 'Parent'};

/// Find anyone at the school by name or email and reset their password from
/// their ⋮ menu -- students and parents included, who appear on no other
/// list with one.
class PasswordResetCard extends StatefulWidget {
  const PasswordResetCard({super.key, this.api});

  /// Injected in tests; the app uses the registered AuthApi.
  final AuthApi? api;

  @override
  State<PasswordResetCard> createState() => _PasswordResetCardState();
}

class _PasswordResetCardState extends State<PasswordResetCard> {
  late final AuthApi _api = widget.api ?? GetIt.I<AuthApi>();
  final _query = TextEditingController();
  List<AuthUser>? _people;
  String? _error;

  static const _shown = 8;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final everyone = await _api.usersForSchool();
      final people = everyone.where((u) => _roleNames.containsKey(u.role)).toList()
        ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
      if (mounted) setState(() => _people = people);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load the people of your school: ${serverErrorMessage(e)}');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final q = _query.text.trim().toLowerCase();
    final matches = (_people ?? const <AuthUser>[])
        .where((u) => q.isEmpty || u.name.toLowerCase().contains(q) || u.email.toLowerCase().contains(q))
        .toList();
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Text('Forgotten passwords', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
      const Gap(4),
      Text('A teacher, student or parent who cannot sign in: find them and choose Reset password from '
          'their ⋮ menu. You get a one-time password to give them.',
          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
      const Gap(12),
      AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          TextField(
            key: const ValueKey('reset-search'),
            controller: _query,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              labelText: 'Find a person',
              hintText: 'Name or email',
              prefixIcon: Icon(Icons.search),
            ),
          ),
          const Gap(8),
          if (_error != null)
            Text(_error!, style: TextStyle(color: theme.colorScheme.error))
          else if (_people == null)
            const LinearProgressIndicator()
          else if (matches.isEmpty)
            Text(q.isEmpty ? 'Nobody has joined yet.' : 'No one matches "${_query.text.trim()}".',
                style: theme.textTheme.bodySmall)
          else ...[
            for (final u in matches.take(_shown))
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(u.name),
                subtitle: Text('${_roleNames[u.role]} · ${u.email}'),
                trailing: PopupMenuButton<String>(
                  key: ValueKey('reset-more-${u.id}'),
                  tooltip: 'More for ${u.name}',
                  onSelected: (_) => resetPasswordFlow(context, userId: u.id, name: u.name, api: _api),
                  itemBuilder: (_) => const [PopupMenuItem(value: 'reset', child: Text('Reset password'))],
                ),
              ),
            if (matches.length > _shown)
              Text('${matches.length - _shown} more: type part of a name to narrow the list.',
                  style: theme.textTheme.bodySmall),
          ],
        ]),
      ),
    ]);
  }
}
