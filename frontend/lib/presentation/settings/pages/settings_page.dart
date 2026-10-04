import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/session/current_session.dart';
import '../../../core/local_engine/app_lock.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/auth_api.dart';
import '../../../core/local_engine/corpus_downloader.dart'
    show CorpusDownloader;
import '../../../core/local_engine/corpus_repository.dart';
import '../../../core/local_engine/corpus_status.dart';
import '../../../core/local_engine/demo_seeder.dart';
import '../../../core/local_engine/local_store.dart';
import '../../../core/sync/network_policy.dart' show kOfflineBuildHasInternet;
import '../../../core/sync/sync_service.dart';
import '../../../core/theme/theme_controller.dart';
import '../../onboarding/pages/app_tour_page.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import '../../workspace/strings.dart';

const _kOfflineBuild = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  String _appVersion = '';
  // Persisted to LocalStore, so leaving the screen does not discard it. Notifications and Auto
  // Sync were toggles here until 2026-10-04: nothing read either, so they are gone.
  bool _biometricAuth = LocalStore.instance.box.get('pref_biometric_auth', defaultValue: false) as bool;
  String _selectedTheme = LocalStore.instance.themeModeName;
  // The one language setting: the School page's language button changes the
  // same value (strings.dart). Settings used to keep its own 'pref_language',
  // which nothing read, and offered English only while the School page
  // offered Hindi (QA S-16).
  String _selectedLanguage = uiHindi ? 'hi' : 'en';

  // Only what is translated is offered. This once listed 13 languages that
  // no string was translated into; Hindi now covers the School pages and
  // the phone apps (strings.dart), and the subtitle says which screens stay
  // in English.
  static const _languageNames = {'en': 'English', 'hi': 'हिन्दी (Hindi)'};

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
    final schoolId = CurrentSession.schoolId;
    final result = SyncService.instance.getLastSyncResult(schoolId);
    if (result != null && mounted) {
      setState(() => _lastSyncResult = result);
    }
  }

  SyncResult? _lastSyncResult;

  /// A student or a parent has no classes to manage, no paper template and no assessments to
  /// sync: those tiles opened pages the server refuses them.
  bool get _isStaff => CurrentSession.role != 'student' && CurrentSession.role != 'parent';

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
            if (_isStaff) ...[
              _buildListTile(Icons.school, 'School branding', 'Logo, colors, and paper template',
                  () => context.push('/settings/template')),
              _buildListTile(Icons.people, 'Classes', 'Manage classes & students',
                  () => context.push('/settings/classes')),
            ],
            // Real login, only meaningful for the server-connected build --
            // the offline build's identity is Settings > Profile above
            // instead (see login_page.dart's docstring for why). Drives
            // the real reviewerId on review/finalize and gates the
            // principal-approve action (auth_routes.require_principal).
            if (!_kOfflineBuild) _buildAuthTile(),
            // QA S-05: after a reset, the person chooses their own password.
            if (!_kOfflineBuild && LocalStore.instance.authUser != null)
              _buildListTile(Icons.password, 'Change password', 'Choose a new password for this account',
                  _changePassword),
            // The device lock is the phone's; a browser has no fingerprint to ask.
            if (!kIsWeb)
            _buildSwitchTile(Icons.fingerprint, 'Biometric Auth', 'Lock the app behind your fingerprint or face', _biometricAuth, (v) async {
              if (v) {
                final ok = await AppLock.confirmCanEnable();
                if (!ok) {
                  // The build method's own context, not State.context: the
                  // SnackBar is shown through the one this closure captured,
                  // so that is the one that has to still be mounted after
                  // AppLock's await (use_build_context_synchronously).
                  if (!context.mounted) return;
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
              setUiLanguage(v);
            }, subtitle: hindiCoverage),
            // Real fix: "Offline Mode" was a toggle with nothing behind it --
            // this exact build is offline-only at compile time
            // (ACADEMICOS_OFFLINE), so switching it "off" implied an online
            // mode that structurally doesn't exist in this build variant.
            // Shown as a real, honest status line instead of a fake switch.
            if (_kOfflineBuild)
              _buildInfoTile('Offline Mode', 'Always on -- this build has no server-connected mode'),
            // Real fix 2026-09-17: this tile (and _downloadCorpusData below)
            // referenced CorpusRepository unconditionally, unlike every
            // sibling tile in this build-variant switch -- the one leak
            // keeping the 6.8 MB bundled question bank (assets/corpus/
            // questions.json) reachable, and therefore un-tree-shakeable,
            // from the Web build's compiled main.dart.js. Web already has a
            // real live API path for question search (ApiClient.
            // searchQuestions -> POST /questions/search) and never needed
            // this tile at all. It needs INTERNET, which the release APK's
            // manifest does not declare, so it is hidden rather than left to
            // fail with an error the teacher cannot fix (network_policy.dart).
            if (_kOfflineBuild && kOfflineBuildHasInternet)
              _buildListTile(Icons.download, 'Download Data',
                  corpusSourceLineFor(CorpusRepository.instance), _downloadCorpusData),
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
          // No "Server URL" field: nothing ever read it (SyncService takes its
          // base from the ACADEMICOS_API dart-define), and its default was a
          // localhost address shipped in every web bundle. The offline build
          // has no server to sync with until the teacher opts in (Task 405),
          // so it shows no sync section at all.
          if (!_kOfflineBuild && _isStaff) ...[
            _buildSection('Server & Sync', [
              _buildListTile(Icons.cloud_sync, 'Manual Sync', 'Sync now with server', _manualSync),
              if (_lastSyncResult != null)
                _buildInfoTile(
                  'Sync History',
                  _lastSyncResult!.success
                      ? 'Last sync: ${_formatDateTime(_lastSyncResult!.timestamp)} — pushed ${_lastSyncResult!.pushedCount}, pulled ${_lastSyncResult!.pulledCount}'
                      : 'Last sync failed: ${_lastSyncResult!.error}',
                )
              else
                _buildInfoTile('Sync History', 'No sync performed yet'),
            ]),
            const SizedBox(height: 24),
          ],
          _buildSection('Data & Privacy', [
            // Local, so in every build.
            _buildListTile(Icons.backup, 'Backup & Restore', 'Save all local data to a file', _backupData),
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
      subtitle: Text(switch (role) {
            'principal' => 'Principal',
            'student' => 'Student',
            'parent' => 'Parent',
            _ => 'Teacher',
          },
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

  /// The signed-in person's own password (QA S-05). The server ends every
  /// session, this one too, and answers with a new token for this device,
  /// which replaces the stored one -- the next request would be a 401
  /// otherwise.
  Future<void> _changePassword() async {
    final current = TextEditingController();
    final fresh = TextEditingController();
    final again = TextEditingController();
    String? error;
    var busy = false;
    final changed = await showDialog<bool>(
      context: context,
      builder: (dialog) => StatefulBuilder(builder: (dialog, set) {
        Future<void> submit() async {
          if (fresh.text.length < 8) {
            set(() => error = 'The new password needs at least 8 characters.');
            return;
          }
          if (fresh.text != again.text) {
            set(() => error = 'The two new passwords are not the same.');
            return;
          }
          set(() {
            busy = true;
            error = null;
          });
          try {
            final token = await GetIt.I<AuthApi>()
                .changePassword(currentPassword: current.text, newPassword: fresh.text);
            final user = LocalStore.instance.authUser;
            if (user != null) LocalStore.instance.signIn(token, user);
            if (dialog.mounted) Navigator.pop(dialog, true);
          } catch (e) {
            set(() {
              busy = false;
              error = serverErrorMessage(e);
            });
          }
        }

        return AlertDialog(
          title: const Text('Change password'),
          content: SizedBox(
            width: 400,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(key: const Key('password-current'), controller: current, obscureText: true,
                  decoration: const InputDecoration(labelText: 'Current password',
                      helperText: 'Or the one-time password the school gave you')),
              const SizedBox(height: 12),
              TextField(key: const Key('password-new'), controller: fresh, obscureText: true,
                  decoration: const InputDecoration(labelText: 'New password', helperText: 'At least 8 characters')),
              const SizedBox(height: 12),
              TextField(key: const Key('password-again'), controller: again, obscureText: true,
                  onSubmitted: (_) => busy ? null : submit(),
                  decoration: const InputDecoration(labelText: 'New password again')),
              if (error != null) ...[
                const SizedBox(height: 12),
                Text(error!, key: const Key('password-error'),
                    style: TextStyle(color: Theme.of(dialog).colorScheme.error)),
              ],
            ]),
          ),
          actions: [
            TextButton(onPressed: busy ? null : () => Navigator.pop(dialog, false), child: const Text('Cancel')),
            FilledButton(key: const Key('password-save'), onPressed: busy ? null : submit,
                child: const Text('Change password')),
          ],
        );
      }),
    );
    if (changed == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Password changed. You stay signed in here; every other device is signed out.')));
    }
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
      showDialog(context: context, builder: (dialog) => AlertDialog(
        title: const Text('Backup saved'),
        content: Text('Saved to:\n${file.path}\n\nCopy this file with a file manager to restore '
            'it on another device, or keep it as a safety copy.'),
        actions: [FilledButton(onPressed: () => Navigator.pop(dialog), child: const Text('OK'))],
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Backup failed: ${serverErrorMessage(e)}')));
    }
  }

  void _manualSync() async {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Syncing…')));
    final schoolId = CurrentSession.schoolId;
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
        content: Text('Sync error: ${serverErrorMessage(e)}'),
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
    // The dialog is on the root navigator; this page is inside the shell's.
    Navigator.of(context, rootNavigator: true).pop(); // close progress dialog

    if (result.success) {
      await CorpusRepository.instance.reload();
      if (!mounted) return;
      setState(() {});
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        // Not a flat "Corpus updated": a download reload() refused, or one
        // that lost rows, has to say so here or the teacher never learns it.
        content: Text(corpusReloadMessageFor(CorpusRepository.instance)),
      ));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Download failed: ${result.error}. Keeping existing data -- nothing was lost.'),
      ));
    }
  }

  void _confirmClearDemoData() {
    showDialog(context: context, builder: (dialog) => AlertDialog(
      title: const Text('Clear Demo Data'),
      content: const Text('Removes the sample Class X Science class this app started with. '
          'Do this before setting up a real school so demo and real data never mix.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Cancel')),
        FilledButton(
          onPressed: () async {
            await DemoSeeder.clearDemoData();
            if (dialog.mounted) Navigator.pop(dialog);
            if (!mounted) return;
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
    showDialog(context: context, builder: (dialog) => AlertDialog(
      title: const Text('Clear All Local Data'),
      content: const Text(
          'This permanently deletes every assessment, evaluation, mastery record, and '
          'setting stored on this device -- including real (non-demo) data. This cannot '
          'be undone.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Cancel')),
        FilledButton(
          onPressed: () async {
            await LocalStore.instance.box.clear();
            if (dialog.mounted) Navigator.pop(dialog);
            if (!mounted) return;
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
    showDialog(context: context, builder: (dialog) => AlertDialog(
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
        TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Close')),
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
        SnackBar(content: Text('Could not open email app: ${serverErrorMessage(e)}')),
      );
    }
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
