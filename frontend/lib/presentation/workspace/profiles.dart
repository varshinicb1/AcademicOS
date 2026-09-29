import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/local_engine/local_store.dart';
import '../../core/session/current_session.dart';
import 'ops_api.dart';
import 'strings.dart';

/// Profiles on a shared family phone (SA-8): the students and parents
/// signed in on this device, one tap apart. See LocalStore.signIn.

String _roleLabel(String? role) => role == 'parent' ? tr('Parent') : tr('Student');

void _open(BuildContext context, String userId) {
  if (!LocalStore.instance.switchTo(userId)) return;
  Ops.loadSyncState();                 // that person's waiting changes, not the last one's
  context.go('/home');
}

/// The sheet behind the School page's switch button.
Future<void> showProfileSwitcher(BuildContext context) => showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheet) {
        final current = CurrentSession.userId;
        final profiles = LocalStore.instance.profiles;
        return SafeArea(
          child: ListView(shrinkWrap: true, children: [
            ListTile(title: Text(tr('Who is using the phone?'), style: Theme.of(sheet).textTheme.titleMedium)),
            for (final p in profiles)
              ListTile(
                leading: CircleAvatar(child: Text(((p['user'] as Map)['name'] as String? ?? '?').characters.first)),
                title: Text((p['user'] as Map)['name'] as String? ?? ''),
                subtitle: Text(_roleLabel((p['user'] as Map)['role'] as String?)),
                trailing: (p['user'] as Map)['id'] == current
                    ? const Icon(Icons.check)
                    : IconButton(
                        tooltip: tr('Remove from this phone'),
                        icon: const Icon(Icons.close),
                        onPressed: () {
                          LocalStore.instance.forgetProfile((p['user'] as Map)['id'] as String);
                          Navigator.pop(sheet);
                        }),
                onTap: (p['user'] as Map)['id'] == current
                    ? () => Navigator.pop(sheet)
                    : () {
                        Navigator.pop(sheet);
                        _open(context, (p['user'] as Map)['id'] as String);
                      },
              ),
            ListTile(
              leading: const Icon(Icons.person_add_alt_1_outlined),
              title: Text(tr('Add someone')),
              subtitle: Text(tr('Sign in another child or parent on this phone')),
              onTap: () {
                Navigator.pop(sheet);
                LocalStore.instance.stepAway();
                context.go('/login');
              },
            ),
          ]),
        );
      },
    );

/// "On this phone" on the sign-in page: continue as a saved profile.
class SavedProfiles extends StatelessWidget {
  const SavedProfiles({super.key});

  @override
  Widget build(BuildContext context) {
    List<Map<String, dynamic>> profiles;
    try {
      profiles = LocalStore.instance.profiles;
    } catch (_) {
      // not-a-failure: before the local store opens (widget tests) there are no saved profiles
      profiles = const [];
    }
    if (profiles.isEmpty) return const SizedBox.shrink();
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Text(tr('On this phone'), style: Theme.of(context).textTheme.titleSmall),
      for (final p in profiles)
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: CircleAvatar(child: Text(((p['user'] as Map)['name'] as String? ?? '?').characters.first)),
          title: Text('${tr('Continue as')} ${(p['user'] as Map)['name']}'),
          subtitle: Text(_roleLabel((p['user'] as Map)['role'] as String?)),
          onTap: () => _open(context, (p['user'] as Map)['id'] as String),
        ),
      const Divider(height: 24),
    ]);
  }
}
