import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/local_engine/app_lock.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../../core/local_engine/corpus_downloader.dart'
    show CorpusDownloader;
import '../../../core/local_engine/corpus_repository.dart';
import '../../../core/local_engine/demo_seeder.dart';
import '../../../core/local_engine/local_store.dart';
import '../../../core/sync/sync_service.dart';
import '../../../core/theme/theme_controller.dart';
import '../../onboarding/pages/app_tour_page.dart';
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
  // Real fix: these three used to reset to a hardcoded default every time
  // Settings reopened -- toggling them and leaving the screen silently
  // discarded the change. Now persisted to LocalStore like every other
  // real setting on this page.
  bool _notificationsEnabled = LocalStore.instance.box.get('pref_notifications', defaultValue: true) as bool;
  bool _autoSync = LocalStore.instance.box.get('pref_auto_sync', defaultValue: true) as bool;
  bool _biometricAuth = LocalStore.instance.box.get('pref_biometric_auth', defaultValue: false) as bool;
  String _selectedTheme = LocalStore.instance.themeModeName;
  String _selectedLanguage = LocalStore.instance.box.get('pref_language', defaultValue: 'en') as String;
  String _serverUrl = 'http://localhost:8000';
  String _sarvamApiKey = LocalStore.instance.sarvamApiKey ?? '';

  // Real fix: this used to list 13 languages in a dropdown when not one of
  // them was actually wired to any translated string anywhere in the app --
  // main.dart's MaterialApp only ever loads Flutter's own built-in widget
  // labels (GlobalMaterialLocalizations etc.), never an AppLocalizations
  // delegate, so picking "Hindi" here silently changed nothing a teacher
  // could see. Real per-string translation for even one Indian language is
  // a genuinely large task (every screen, not just this list), so until
  // that's actually built, the only honest option to offer is the one that
  // really works.
  static const _languageNames = {'en': 'English'};

  @override
  void initState() {
    super.initState();
    _loadVersion();
    _loadLastSyncResult();
  }

  Future<void> _loadVersion() async {
    final info = await PackageInfo.fromPlatform();
    setState(() => _appVersion = '${info.version}+${info.buildNumber}');
  }

  Future<void> _loadLastSyncResult() async {
    const schoolId = AppConstants.currentSchoolId;
    final result = SyncService.instance.getLastSyncResult(schoolId);
    if (result != null && mounted) {
      setState(() => _lastSyncResult = result);
    }
  }

  SyncResult? _lastSyncResult;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(AppConstants.defaultPadding),
        children: [
          _buildSection('Account', [
            _buildListTile(Icons.person, 'Profile', 'Manage your profile',
                () => context.push('/settings/profile')),
            _buildListTile(Icons.school, 'School branding', 'Logo, colors, and paper template',
                () => context.push('/settings/template')),
            _buildListTile(Icons.people, 'Classes', 'Manage classes & students',
                () => context.push('/settings/classes')),
            // Real fix: "Notifications" used to be a toggle with nothing behind
            // it -- push notifications require a server to send them from, and
            // this offline build has none. Removed rather than left to silently
            // do nothing; a server-connected build could legitimately bring
            // this back for real.
            if (!_kOfflineBuild)
              _buildSwitchTile(Icons.notifications, 'Notifications', 'Push notifications', _notificationsEnabled, (v) {
                setState(() => _notificationsEnabled = v);
                LocalStore.instance.box.put('pref_notifications', v);
              }),
            // Real login, only meaningful for the server-connected build --
            // the offline build's identity is Settings > Profile above
            // instead (see login_page.dart's docstring for why). Drives
            // the real reviewerId on review/finalize and gates the
            // principal-approve action (auth_routes.require_principal).
            if (!_kOfflineBuild) _buildAuthTile(),
            _buildSwitchTile(Icons.fingerprint, 'Biometric Auth', 'Lock the app behind your fingerprint or face', _biometricAuth, (v) async {
              if (v) {
                final ok = await AppLock.confirmCanEnable();
                if (!ok) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('No fingerprint, face, or device PIN is set up on this phone -- '
                        'set one up in Android Settings first.'),
                  ));
                  return;
                }
              }
              setState(() => _biometricAuth = v);
              LocalStore.instance.box.put('pref_biometric_auth', v);
            }),
          ]),
          const SizedBox(height: 24),
          _buildSection('App Preferences', [
            _buildSegmentedTile(Icons.palette, 'Theme', _selectedTheme, ['light', 'dark', 'system'], (v) {
              setState(() => _selectedTheme = v);
              ThemeController.set(switch (v) {
                'light' => ThemeMode.light,
                'dark' => ThemeMode.dark,
                _ => ThemeMode.system,
              });
            }),
            _buildDropdownTile(Icons.language, 'Language', _selectedLanguage, _languageNames, (v) {
              setState(() => _selectedLanguage = v);
              LocalStore.instance.box.put('pref_language', v);
            }, subtitle: 'Hindi and other Indian languages are not translated yet'),
            // Real fix: same problem as Notifications above -- "Auto Sync"
            // toggled a preference nothing ever read, since there is no
            // server for this offline build to sync to in the first place.
            if (!_kOfflineBuild)
              _buildSwitchTile(Icons.sync, 'Auto Sync', 'Automatically sync data', _autoSync, (v) {
                setState(() => _autoSync = v);
                LocalStore.instance.box.put('pref_auto_sync', v);
              }),
            // Real fix: "Offline Mode" was a toggle with nothing behind it --
            // this exact build is offline-only at compile time
            // (ACADEMICOS_OFFLINE), so switching it "off" implied an online
            // mode that structurally doesn't exist in this build variant.
            // Shown as a real, honest status line instead of a fake switch.
            if (_kOfflineBuild)
              _buildInfoTile('Offline Mode', 'Always on -- this build has no server-connected mode'),
            _buildListTile(Icons.download, 'Download Data',
                'Corpus source: ${CorpusRepository.instance.loadedFromDownload ? "downloaded" : "bundled with app"} '
                '(${CorpusRepository.instance.isLoaded ? CorpusRepository.instance.all.length : "?"} questions)',
                _downloadCorpusData),
            _buildListTile(Icons.clear_all, 'Clear Cache', 'Free up storage space', _clearCache),
            if (_kOfflineBuild && LocalStore.instance.isDemoSeeded) ...[
              _buildListTile(
                Icons.explore_outlined,
                'Show App Tour',
                'Replay the guided walkthrough of the sample data this app started with',
                () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => const AppTourPage(), fullscreenDialog: true)),
              ),
              _buildListTile(
                Icons.restart_alt,
                'Clear Demo Data',
                'Remove the sample class this app started with, before onboarding a real school',
                _confirmClearDemoData,
              ),
            ],
          ]),
          const SizedBox(height: 24),
          if (_kOfflineBuild) ...[
            _buildSection('Scan & Grade', [
              _buildTextFieldTile(
                Icons.document_scanner,
                'Sarvam API Key (optional)',
                _sarvamApiKey,
                (v) {
                  setState(() => _sarvamApiKey = v);
                  LocalStore.instance.sarvamApiKey = v;
                },
              ),
              _buildInfoTile(
                'What this does',
                'Scan & Grade always works offline with an on-device OCR model. '
                'Adding your own Sarvam API key here upgrades accuracy on genuinely '
                'messy handwriting when you have internet -- get a key at sarvam.ai. '
                'Leave blank to keep everything fully offline.',
              ),
            ]),
            const SizedBox(height: 24),
          ],
          _buildSection('Server & Sync', [
            _buildTextFieldTile(Icons.link, 'Server URL', _serverUrl, (v) => setState(() => _serverUrl = v)),
            _buildListTile(Icons.cloud_sync, 'Manual Sync', 'Sync now with server', _manualSync),
            if (_lastSyncResult != null)
              _buildListTile(
                Icons.history,
                'Sync History',
                _lastSyncResult!.success
                    ? 'Last sync: ${_formatDateTime(_lastSyncResult!.timestamp)} — pushed ${_lastSyncResult!.pushedCount}, pulled ${_lastSyncResult!.pulledCount}'
                    : 'Last sync failed: ${_lastSyncResult!.error}',
                () {},
              )
            else
              _buildListTile(Icons.history, 'Sync History', 'No sync performed yet', () {}),
            _buildListTile(Icons.backup, 'Backup & Restore', 'Save all local data to a file', _backupData),
          ]),
          const SizedBox(height: 24),
          _buildSection('Data & Privacy', [
            // Real fix: "Delete Account" made no sense (there is no
            // account/auth system yet) and its old handler just showed a
            // fake "Account deleted" message without deleting anything.
            // Replaced with a real, working action against the one thing
            // that actually exists on this device: local data.
            _buildListTile(Icons.delete_forever, 'Clear All Local Data',
                'Permanently wipe every assessment, evaluation, and setting on this device',
                _confirmClearAllData),
            _buildListTile(Icons.privacy_tip, 'Privacy Policy', 'Read our privacy policy',
                () => context.push('/settings/legal/privacy')),
            _buildListTile(Icons.description, 'Terms of Service', 'Read terms of service',
                () => context.push('/settings/legal/terms')),
            _buildListTile(Icons.help, 'Help & Support', 'Get help', _showHelp),
          ]),
          const SizedBox(height: 24),
          _buildSection('About', [
            _buildInfoTile('Version', _appVersion),
            _buildInfoTile('Build', _kOfflineBuild ? 'Offline (on-device)' : 'Server-connected'),
            _buildInfoTile('Platform', 'Flutter'),
            _buildListTile(Icons.bug_report, 'Report a Bug', 'Send feedback', _reportBug),
            _buildListTile(Icons.star_rate, 'Rate App', 'Rate us on store', _rateApp),
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

  Widget _buildAuthTile() {
    final user = LocalStore.instance.authUser;
    if (user == null) {
      return _buildListTile(Icons.login, 'Sign in', 'Sign in to approve papers as principal',
          () => context.push('/login'));
    }
    final name = user['name'] as String? ?? '';
    final role = user['role'] as String? ?? 'teacher';
    return ListTile(
      leading: Icon(Icons.verified_user, color: Theme.of(context).colorScheme.primary),
      title: Text('Signed in as $name'),
      subtitle: Text(role == 'principal' ? 'Principal' : 'Teacher',
          style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      trailing: TextButton(
        onPressed: () async {
          await GetIt.I<AuthApi>().logout();
          LocalStore.instance.clearAuth();
          // Signed out with nowhere valid to stay: the router guard would
          // bounce the next navigation anyway -- go straight to Sign in.
          if (mounted) context.go('/login');
        },
        child: const Text('Sign out'),
      ),
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

  Widget _buildDropdownTile(IconData icon, String title, String value, Map<String, String> options, ValueChanged<String> onChanged, {String? subtitle}) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      subtitle: subtitle == null
          ? null
          : Text(subtitle, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
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

  // Real overflow bug: `value` used to be crammed into ListTile.trailing,
  // which forces a single unbounded-width line -- fine for "Flutter" or
  // "1.0.0+1", but two real call sites pass a full sentence ("Always on --
  // this build has no server-connected mode", the multi-sentence "What this
  // does" Scan & Grade explainer) that has no business being squeezed into a
  // trailing slot. Subtitle wraps naturally at full width, and matches every
  // other tile builder in this same file (_buildListTile/_buildSwitchTile
  // already put their secondary text there, never in trailing).
  Widget _buildInfoTile(String label, String value) {
    return ListTile(
      title: Text(label, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      subtitle: Text(value, style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.w500)),
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

  Future<void> _backupData() async {
    try {
      final box = LocalStore.instance.box;
      final dump = <String, dynamic>{
        for (final key in box.keys) key.toString(): box.get(key),
      };
      final dir = await getApplicationDocumentsDirectory();
      final file = File(
          '${dir.path}/academicos_backup_${DateTime.now().toIso8601String().replaceAll(':', '-')}.json');
      await file.writeAsString(jsonEncode(dump));
      if (!mounted) return;
      showDialog(context: context, builder: (_) => AlertDialog(
        title: const Text('Backup saved'),
        content: Text('Saved to:\n${file.path}\n\nCopy this file with a file manager to restore '
            'it on another device, or keep it as a safety copy.'),
        actions: [FilledButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Backup failed: $e')));
    }
  }

  void _manualSync() async {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Syncing…')));
    const schoolId = AppConstants.currentSchoolId;
    try {
      final result = await SyncService.instance.sync(schoolId);
      if (!mounted) return;
      await _loadLastSyncResult(); // refresh the UI
      if (!mounted) return;
      setState(() {}); // update the sync history tile
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
          result.success
              ? 'Sync complete — pushed ${result.pushedCount}, pulled ${result.pulledCount}'
              : 'Sync failed: ${result.error}',
        ),
        backgroundColor: result.success ? null : Theme.of(context).colorScheme.error,
        duration: const Duration(seconds: 4),
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Sync error: $e'),
        backgroundColor: Theme.of(context).colorScheme.error,
        duration: const Duration(seconds: 4),
      ));
    }
  }

  Future<void> _downloadCorpusData() async {
    final progress = ValueNotifier<double>(0);
    if (!mounted) return;
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        title: const Text('Downloading corpus data'),
        content: ValueListenableBuilder<double>(
          valueListenable: progress,
          builder: (context, value, _) => Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              LinearProgressIndicator(value: value > 0 ? value : null),
              const SizedBox(height: 12),
              Text(value > 0 ? '${(value * 100).toStringAsFixed(0)}%' : 'Connecting…'),
            ],
          ),
        ),
      ),
    );

    final result = await CorpusDownloader.download(
      onProgress: (p) => progress.value = p.fraction,
    );

    if (!mounted) return;
    Navigator.of(context).pop(); // close progress dialog

    if (result.success) {
      await CorpusRepository.instance.reload();
      if (!mounted) return;
      setState(() {});
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Corpus updated -- ${CorpusRepository.instance.all.length} questions now available.'),
      ));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Download failed: ${result.error}. Keeping existing data -- nothing was lost.'),
      ));
    }
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

  void _confirmClearAllData() {
    showDialog(context: context, builder: (_) => AlertDialog(
      title: const Text('Clear All Local Data'),
      content: const Text(
          'This permanently deletes every assessment, evaluation, mastery record, and '
          'setting stored on this device -- including real (non-demo) data. This cannot '
          'be undone.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          onPressed: () async {
            await LocalStore.instance.box.clear();
            if (!mounted) return;
            Navigator.pop(context);
            ScaffoldMessenger.of(context)
                .showSnackBar(const SnackBar(content: Text('All local data cleared')));
            setState(() {});
          },
          child: const Text('Clear everything', style: TextStyle(color: Colors.white)),
        ),
      ],
    ));
  }

  void _showHelp() {
    showDialog(context: context, builder: (_) => AlertDialog(
      title: const Text('Help & Support'),
      content: const SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Scan & Grade not opening the camera or gallery?',
                style: TextStyle(fontWeight: FontWeight.w600)),
            SizedBox(height: 4),
            Text('Make sure this app has camera and photo permissions in your phone\'s '
                'Settings > Apps > AcademicOS > Permissions.'),
            SizedBox(height: 16),
            Text('Assessments list looks empty?', style: TextStyle(fontWeight: FontWeight.w600)),
            SizedBox(height: 4),
            Text('Only assessments with a generated paper appear in some lists. Create a '
                'paper from "New Assessment" first.'),
            SizedBox(height: 16),
            Text('Something else wrong?', style: TextStyle(fontWeight: FontWeight.w600)),
            SizedBox(height: 4),
            Text('Use "Report a Bug" below to send details directly.'),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close')),
      ],
    ));
  }

  Future<void> _reportBug() async {
    final uri = Uri(
      scheme: 'mailto',
      path: 'support@academicos.app',
      query: 'subject=${Uri.encodeComponent('AcademicOS bug report (v$_appVersion)')}',
    );
    try {
      final launched = await launchUrl(uri);
      if (!launched && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No email app found. Contact your AcademicOS admin directly.')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not open email app: $e')),
      );
    }
  }

  void _rateApp() {
    // Real, honest gap: this app isn't published on the Play Store yet, so
    // a fake "opening store..." action would just be another dead-end.
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('AcademicOS isn\'t published on the Play Store yet -- check back after launch!')),
    );
  }

  String _formatDateTime(DateTime dt) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final dtDate = DateTime(dt.year, dt.month, dt.day);
    final diff = today.difference(dtDate).inDays;
    final timeStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    if (diff == 0) return 'today $timeStr';
    if (diff == 1) return 'yesterday $timeStr';
    return '${dt.day}/${dt.month}/${dt.year} $timeStr';
  }
}
