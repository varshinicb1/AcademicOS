import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/local_engine/demo_seeder.dart';
import '../../../core/local_engine/local_store.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

const _kOfflineBuild = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  String _appVersion = '';
  bool _notificationsEnabled = true;
  bool _autoSync = true;
  bool _offlineMode = true;
  bool _biometricAuth = false;
  String _selectedTheme = 'system';
  String _selectedLanguage = 'en';
  String _serverUrl = 'http://localhost:8000';

  // 13 options doesn't fit a SegmentedButton on a phone-width screen without
  // squeezing each code onto two lines ("e" / "n") — a dropdown scales to
  // any option count and is the conventional pattern for many-option
  // single-select, unlike the 2-3 option Theme row above it.
  static const _languageNames = {
    'en': 'English', 'hi': 'Hindi', 'ta': 'Tamil', 'te': 'Telugu',
    'bn': 'Bengali', 'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada',
    'ml': 'Malayalam', 'or': 'Odia', 'pa': 'Punjabi', 'as': 'Assamese', 'ur': 'Urdu',
  };

  @override
  void initState() {
    super.initState();
    _loadVersion();
  }

  Future<void> _loadVersion() async {
    final info = await PackageInfo.fromPlatform();
    setState(() => _appVersion = '${info.version}+${info.buildNumber}');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(AppConstants.defaultPadding),
        children: [
          _buildSection('Account', [
            _buildListTile(Icons.person, 'Profile', 'Manage your profile', () {}),
            _buildListTile(Icons.school, 'School branding', 'Logo, colors, and paper template',
                () => context.push('/settings/template')),
            _buildListTile(Icons.people, 'Classes', 'Manage classes & students', () {}),
            _buildSwitchTile(Icons.notifications, 'Notifications', 'Push notifications', _notificationsEnabled, (v) => setState(() => _notificationsEnabled = v)),
            _buildSwitchTile(Icons.fingerprint, 'Biometric Auth', 'Use fingerprint/face ID', _biometricAuth, (v) => setState(() => _biometricAuth = v)),
          ]),
          const SizedBox(height: 24),
          _buildSection('App Preferences', [
            _buildSegmentedTile(Icons.palette, 'Theme', _selectedTheme, ['light', 'dark', 'system'], (v) => setState(() => _selectedTheme = v)),
            _buildDropdownTile(Icons.language, 'Language', _selectedLanguage, _languageNames, (v) => setState(() => _selectedLanguage = v)),
            _buildSwitchTile(Icons.sync, 'Auto Sync', 'Automatically sync data', _autoSync, (v) => setState(() => _autoSync = v)),
            _buildSwitchTile(Icons.offline_bolt, 'Offline Mode', 'Work offline, sync when online', _offlineMode, (v) => setState(() => _offlineMode = v)),
            _buildListTile(Icons.download, 'Download Data', 'Download syllabus, questions for offline use', () {}),
            _buildListTile(Icons.clear_all, 'Clear Cache', 'Free up storage space', _clearCache),
            if (_kOfflineBuild && LocalStore.instance.isDemoSeeded)
              _buildListTile(
                Icons.restart_alt,
                'Clear Demo Data',
                'Remove the sample class this app started with, before onboarding a real school',
                _confirmClearDemoData,
              ),
          ]),
          const SizedBox(height: 24),
          _buildSection('Server & Sync', [
            _buildTextFieldTile(Icons.link, 'Server URL', _serverUrl, (v) => setState(() => _serverUrl = v)),
            _buildListTile(Icons.cloud_sync, 'Manual Sync', 'Sync now with server', _manualSync),
            _buildListTile(Icons.history, 'Sync History', 'View recent sync activity', () {}),
            _buildListTile(Icons.backup, 'Backup & Restore', 'Backup local data', () {}),
          ]),
          const SizedBox(height: 24),
          _buildSection('Data & Privacy', [
            _buildListTile(Icons.delete_forever, 'Delete Account', 'Permanently delete your account', _confirmDeleteAccount),
            _buildListTile(Icons.privacy_tip, 'Privacy Policy', 'Read our privacy policy', () {}),
            _buildListTile(Icons.description, 'Terms of Service', 'Read terms of service', () {}),
            _buildListTile(Icons.help, 'Help & Support', 'Get help', () {}),
          ]),
          const SizedBox(height: 24),
          _buildSection('About', [
            _buildInfoTile('Version', _appVersion),
            _buildInfoTile('Build', 'Debug'),
            _buildInfoTile('Platform', 'Flutter'),
            _buildListTile(Icons.bug_report, 'Report a Bug', 'Send feedback', () {}),
            _buildListTile(Icons.star_rate, 'Rate App', 'Rate us on store', () {}),
          ]),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600, color: Theme.of(context).colorScheme.primary)),
        const SizedBox(height: 8),
        AppCard(child: Column(children: children)),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildListTile(IconData icon, String title, String subtitle, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      subtitle: Text(subtitle, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _buildSwitchTile(IconData icon, String title, String subtitle, bool value, ValueChanged<bool> onChanged) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      subtitle: Text(subtitle, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      trailing: Switch(value: value, onChanged: onChanged),
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _buildSegmentedTile(IconData icon, String title, String value, List<String> options, ValueChanged<String> onChanged) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      subtitle: SegmentedButton<String>(
        segments: options.map((o) => ButtonSegment(value: o, label: Text(o))).toList(),
        selected: {value},
        onSelectionChanged: (s) => onChanged(s.first),
        showSelectedIcon: false,
      ),
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _buildDropdownTile(IconData icon, String title, String value, Map<String, String> options, ValueChanged<String> onChanged) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      trailing: DropdownButton<String>(
        value: value,
        underline: const SizedBox.shrink(),
        items: options.entries
            .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
            .toList(),
        onChanged: (v) {
          if (v != null) onChanged(v);
        },
      ),
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _buildTextFieldTile(IconData icon, String title, String value, ValueChanged<String> onChanged) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      subtitle: Text(value, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant, fontFamily: 'monospace')),
      trailing: const Icon(Icons.edit, size: 18),
      onTap: () => _editTextField(title, value, onChanged),
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _buildInfoTile(String label, String value) {
    return ListTile(
      title: Text(label, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      trailing: Text(value, style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.w500)),
      contentPadding: EdgeInsets.zero,
    );
  }

  void _editTextField(String title, String value, ValueChanged<String> onChanged) {
    final controller = TextEditingController(text: value);
    showDialog(context: context, builder: (_) => AlertDialog(
      title: Text(title),
      content: TextField(controller: controller, autofocus: true, decoration: const InputDecoration(hintText: 'Enter value')),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')), FilledButton(onPressed: () { onChanged(controller.text); Navigator.pop(context); }, child: const Text('Save'))],
    ));
  }

  void _clearCache() {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cache cleared')));
  }

  void _manualSync() {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Syncing...')));
  }

  void _confirmClearDemoData() {
    showDialog(context: context, builder: (_) => AlertDialog(
      title: const Text('Clear Demo Data'),
      content: const Text('Removes the sample Class X Science class this app started with. '
          'Do this before setting up a real school so demo and real data never mix.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          onPressed: () async {
            await DemoSeeder.clearDemoData();
            if (!mounted) return;
            Navigator.pop(context);
            ScaffoldMessenger.of(context)
                .showSnackBar(const SnackBar(content: Text('Demo data cleared')));
            setState(() {});
          },
          child: const Text('Clear', style: TextStyle(color: Colors.white)),
        ),
      ],
    ));
  }

  void _confirmDeleteAccount() {
    showDialog(context: context, builder: (_) => AlertDialog(
      title: const Text('Delete Account'),
      content: const Text('This action cannot be undone. All your data will be permanently deleted.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(onPressed: () { Navigator.pop(context); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Account deleted'))); }, child: const Text('Delete', style: TextStyle(color: Colors.white))),
      ],
    ));
  }
}
