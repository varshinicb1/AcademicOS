import 'package:flutter/material.dart';

import '../../../core/local_engine/local_store.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Real, minimal teacher profile for this device -- there is no login/auth
/// system yet (see AppConstants.currentSchoolId's own comment on the same
/// gap), so this is deliberately "whoever is using this device," not a
/// multi-account switcher. Was a dead `() {}` button before this; a teacher
/// tapping "Profile" from Settings got nothing at all.
class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  late final _name = TextEditingController(text: LocalStore.instance.teacherName);
  late final _subject = TextEditingController(text: LocalStore.instance.teacherSubject);
  late String _role = LocalStore.instance.teacherRole;
  bool _saved = false;

  @override
  void dispose() {
    _name.dispose();
    _subject.dispose();
    super.dispose();
  }

  void _save() {
    LocalStore.instance.teacherName = _name.text;
    LocalStore.instance.teacherSubject = _subject.text;
    LocalStore.instance.teacherRole = _role;
    setState(() => _saved = true);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Center(
            child: CircleAvatar(
              radius: 40,
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(Icons.person, size: 44, color: theme.colorScheme.onPrimaryContainer),
            ),
          ),
          const SizedBox(height: 24),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Your details', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text(
                  'Shown on generated papers and reports where a teacher name is needed.',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _name,
                  onChanged: (_) => setState(() => _saved = false),
                  decoration: const InputDecoration(
                    labelText: 'Your name',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _subject,
                  onChanged: (_) => setState(() => _saved = false),
                  decoration: const InputDecoration(
                    labelText: 'Primary subject you teach',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Your role', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text(
                  'Recorded against every grading action you take on this device, and required '
                  'to approve a finalized paper. This device cannot verify who you really are -- '
                  'it can only record what this device says, the same honest limit as everything '
                  'else in this offline build without a real login system.',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: 12),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'teacher', label: Text('Teacher'), icon: Icon(Icons.person_outline)),
                    ButtonSegment(value: 'principal', label: Text('Principal'), icon: Icon(Icons.verified_user_outlined)),
                  ],
                  selected: {_role},
                  onSelectionChanged: (s) => setState(() {
                    _role = s.first;
                    _saved = false;
                  }),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _save,
            icon: Icon(_saved ? Icons.check : Icons.save),
            label: Text(_saved ? 'Saved' : 'Save'),
          ),
        ],
      ),
    );
  }
}
