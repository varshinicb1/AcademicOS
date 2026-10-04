import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';
import 'messaging_card.dart';
import '../shared/widgets/shell.dart';

/// The caller's notifications (NTF-1): newest first, unread marked, and the
/// settings -- quiet hours, language, and push/email per kind.
class InboxPage extends StatefulWidget {
  const InboxPage({super.key});

  @override
  State<InboxPage> createState() => _InboxPageState();
}

class _InboxPageState extends State<InboxPage> {
  late Future<Map<String, dynamic>> _future = Ops.map('/notifications');

  void _reload() => setState(() { _future = Ops.map('/notifications'); });

  Future<void> _open(Map<String, dynamic> n) async {
    if (n['read'] != true) {
      try {
        await Ops.send('POST', '/notifications/${n['id']}/read', label: 'Mark a notification read');
      } catch (_) {
        // not-a-failure: marking as read is a courtesy; opening the notification must not wait on it
      }
    }
    final link = n['link'] as String?;
    if (!mounted) return;
    _reload();
    final target = _route(link);
    if (target != null) context.push(target);
  }

  /// A notification's link names a server page; this is the app's page for
  /// it. Leave decisions, timetable changes, holidays and digests went
  /// nowhere (v3 audit N-4-6): every link the server sends has a page here.
  String? _route(String? link) => inboxRoute(link, CurrentSession.role);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Notifications')), actions: [
        TextButton(
          onPressed: () async {
            final messenger = ScaffoldMessenger.of(context);
            try {
              await Ops.send('POST', '/notifications/read-all', label: 'Mark all notifications read');
              _reload();
            } catch (e) {
              messenger.showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
            }
          },
          child: Text(tr('Mark all read')),
        ),
        IconButton(
          tooltip: 'Notification settings',
          icon: const Icon(Icons.tune),
          onPressed: () => showDialog(context: context, builder: (_) => const _PreferencesDialog()),
        ),
        // The teacher and student apps had no way to sign out or change the
        // theme: Settings was reachable only from the web's side navigation
        // (v3 audit N-4-7). The inbox is in every app's bottom bar.
        IconButton(
          tooltip: 'Settings and sign out',
          icon: const Icon(Icons.account_circle_outlined),
          onPressed: () => context.push('/settings'),
        ),
      ]),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          final items = (snap.data!['items'] as List).cast<Map>();
          if (items.isEmpty) {
            return const EmptyState(icon: Icons.notifications_none, title: 'Nothing yet',
                message: 'Homework, cover duties, marks and exam news will appear here.');
          }
          return RefreshIndicator(
            onRefresh: () async => _reload(),
            child: ListView.separated(
              itemCount: items.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) {
                final n = Map<String, dynamic>.from(items[i]);
                final unread = n['read'] != true;
                return ListTile(
                  leading: Icon(unread ? Icons.circle : Icons.circle_outlined, size: 12,
                      color: unread ? theme.colorScheme.primary : theme.disabledColor),
                  title: Text(n['title'] ?? '', style: TextStyle(fontWeight: unread ? FontWeight.w600 : FontWeight.normal)),
                  subtitle: Text(n['body'] ?? ''),
                  trailing: Text(_when(n['createdAt'] as String?), style: theme.textTheme.bodySmall),
                  onTap: () => _open(n),
                );
              },
            ),
          );
        },
      ),
    );
  }

  String _when(String? iso) {
    final t = iso == null ? null : DateTime.tryParse(iso)?.toLocal();
    if (t == null) return '';
    final d = DateTime.now().difference(t);
    if (d.inMinutes < 1) return 'now';
    if (d.inHours < 1) return '${d.inMinutes}m';
    if (d.inDays < 1) return '${d.inHours}h';
    return '${t.day}/${t.month}';
  }
}

class _PreferencesDialog extends StatefulWidget {
  const _PreferencesDialog();

  @override
  State<_PreferencesDialog> createState() => _PreferencesDialogState();
}

class _PreferencesDialogState extends State<_PreferencesDialog> {
  Map<String, dynamic>? _prefs;
  String? _error;

  @override
  void initState() {
    super.initState();
    Ops.map('/notification-preferences').then((p) => setState(() => _prefs = p),
        onError: (e) => setState(() => _error = serverErrorMessage(e)));
  }

  Future<void> _save(Map<String, dynamic> body) async {
    try {
      final p = await Ops.put('/notification-preferences', body: body);
      setState(() {
        _prefs = Map<String, dynamic>.from(p as Map);
        _error = null;
      });
    } catch (e) {
      setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _pickTime(String field) async {
    final parts = ((_prefs![field] as String?) ?? '19:00').split(':');
    final t = await showTimePicker(context: context,
        initialTime: TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1])));
    if (t != null) {
      await _save({field: '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}'});
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = _prefs;
    return AlertDialog(
      title: const Text('Notification settings'),
      content: SizedBox(
        width: 520,
        child: p == null
            ? (_error != null ? Text(_error!) : const SizedBox(height: 80, child: LoadingIndicator()))
            : SingleChildScrollView(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Quiet hours'),
                    subtitle: const Text('No push notifications in this window; they arrive after it.'),
                    trailing: Wrap(spacing: 8, children: [
                      OutlinedButton(onPressed: () => _pickTime('quietStart'), child: Text('From ${p['quietStart']}')),
                      OutlinedButton(onPressed: () => _pickTime('quietEnd'), child: Text('To ${p['quietEnd']}')),
                    ]),
                  ),
                  // SA-5: one message a day instead of each as it comes.
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Daily digest'),
                    subtitle: Text(p['digestAt'] == null
                        ? 'Off: push and email come as things happen.'
                        : 'One push and one email a day at ${p['digestAt']}. The inbox still shows everything at once; '
                            'cover requests still come straight away.'),
                    value: p['digestAt'] != null,
                    onChanged: (on) => on ? _pickTime('digestAt') : _save({'digestAt': ''}),
                  ),
                  if (p['digestAt'] != null)
                    Align(alignment: Alignment.centerLeft, child: OutlinedButton(
                        onPressed: () => _pickTime('digestAt'), child: Text('Send it at ${p['digestAt']}'))),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Language'),
                    trailing: SegmentedButton<String>(
                      segments: const [ButtonSegment(value: 'en', label: Text('English')),
                        ButtonSegment(value: 'hi', label: Text('हिन्दी'))],
                      selected: {p['language'] as String},
                      onSelectionChanged: (s) => _save({'language': s.first}),
                    ),
                  ),
                  // INT-2: the person's own number and consent for SMS and WhatsApp.
                  const MessagingCard(),
                  const Divider(),
                  for (final k in (p['kinds'] as List).cast<Map>())
                    Row(children: [
                      Expanded(child: Text(k['label'] as String)),
                      const Text('Push'),
                      Checkbox(value: k['push'] as bool,
                          onChanged: (v) => _save({'kinds': [{'kind': k['kind'], 'push': v}]})),
                      const Text('Email'),
                      Checkbox(value: k['email'] as bool,
                          onChanged: (v) => _save({'kinds': [{'kind': k['kind'], 'email': v}]})),
                    ]),
                ]),
              ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Done'))],
    );
  }
}

/// The app's page for a notification's server link, by the reader's role.
String? inboxRoute(String? link, String role) {
  if (link == null) return null;
  final path = link.split('?').first;
  final staffCover = role == 'principal' ? '/school/cover' : '/school/my-day';
  if (path.startsWith('/my-homework')) return '/school$path';
  if (path.startsWith('/homework/')) return '/school$path';
  if (path == '/homework') return '/school/homework';
  if (path.startsWith('/my-day') || path == '/leave') return '/school/my-day';
  if (path.startsWith('/cover')) return staffCover;
  if (path.startsWith('/my-exams')) return '/school/my-exams';
  if (path == '/week' || path == '/my-timetable') return '/school/week';
  if (path == '/my-children') return '/school/family';
  if (path == '/my-learning') return '/school/my-learning';
  if (path == '/dashboard') return '/school';
  if (path.startsWith('/assessments/')) return '/assessment/${path.substring('/assessments/'.length)}';
  if (path.startsWith('/school/')) return path;
  return null;
}
