import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import '../shared/widgets/shell.dart';
import 'ops_api.dart';
import 'strings.dart';

String _when(String iso) {
  final t = DateTime.tryParse(iso)?.toLocal();
  if (t == null) return '';
  final now = DateTime.now();
  final hm = '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
  if (t.year == now.year && t.month == now.month && t.day == now.day) return hm;
  return '${t.day}/${t.month} $hm';
}

/// Teacher-parent messages (MSG-1): a parent's conversations with their
/// children's teachers, or a teacher's with parents. A parent starts one
/// with New message; a teacher answers from here or from the inbox.
class MessagesPage extends StatefulWidget {
  const MessagesPage({super.key});

  @override
  State<MessagesPage> createState() => _MessagesPageState();
}

class _MessagesPageState extends State<MessagesPage> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/conversations');

  void _reload() => setState(() => _future = Ops.list('/conversations'));

  Future<void> _new() async {
    final id = await showDialog<String>(context: context, builder: (_) => const _NewMessageDialog());
    if (!mounted) return;
    _reload();
    if (id != null) context.push('/school/messages/$id');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final parent = CurrentSession.role == 'parent';
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('Messages'))),
      floatingActionButton: parent
          ? FloatingActionButton.extended(
              key: const ValueKey('new-message'),
              onPressed: _new,
              icon: const Icon(Icons.edit_outlined),
              label: Text(tr('New message')))
          : null,
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
          final items = snap.data!;
          if (items.isEmpty) {
            return EmptyState(icon: Icons.forum_outlined, title: tr('No messages yet'),
                message: parent
                    ? tr("Write to your child's class teacher or subject teachers with New message.")
                    : tr('Messages from parents of the students you teach appear here.'));
          }
          return RefreshIndicator(
            onRefresh: () async => _reload(),
            child: ListView.separated(
              itemCount: items.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) {
                final c = items[i];
                final unread = (c['unread'] as int? ?? 0) > 0;
                return ListTile(
                  key: ValueKey('conversation-${c['id']}'),
                  leading: const Icon(Icons.forum_outlined),
                  title: Text('${c['withName']} · ${tr('about')} ${c['studentName']}',
                      style: TextStyle(fontWeight: unread ? FontWeight.w600 : FontWeight.normal)),
                  subtitle: Text('${c['lastMessage'] ?? ''}', maxLines: 2, overflow: TextOverflow.ellipsis),
                  trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(_when('${c['lastAt']}'), style: theme.textTheme.bodySmall),
                        if (unread) ChipTag(label: '${c['unread']} ${tr('new')}'),
                      ]),
                  onTap: () async {
                    await context.push('/school/messages/${c['id']}');
                    if (mounted) _reload();
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}

/// A parent picks a child and one of the child's teachers, then writes.
/// Returns the conversation's id once sent.
class _NewMessageDialog extends StatefulWidget {
  const _NewMessageDialog();

  @override
  State<_NewMessageDialog> createState() => _NewMessageDialogState();
}

class _NewMessageDialogState extends State<_NewMessageDialog> {
  List<Map<String, dynamic>>? _children;
  List<Map<String, dynamic>>? _contacts;
  String? _child, _to, _error;
  final _body = TextEditingController();
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    Ops.list('/my-children').then((kids) {
      if (!mounted) return;
      setState(() => _children = kids);
      if (kids.isNotEmpty) _pickChild(kids.first['studentId'] as String);
    }, onError: (Object e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    });
  }

  @override
  void dispose() {
    _body.dispose();
    super.dispose();
  }

  Future<void> _pickChild(String id) async {
    setState(() {
      _child = id;
      _contacts = null;
      _to = null;
    });
    try {
      final c = await Ops.list('/children/$id/contacts');
      if (mounted && _child == id) setState(() => _contacts = c);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _send() async {
    if (_child == null || _to == null || _body.text.trim().isEmpty) {
      setState(() => _error = tr('Choose a teacher and write your message.'));
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final r = await Ops.post('/conversations', body: {'studentId': _child, 'withId': _to, 'body': _body.text.trim()});
      if (mounted) Navigator.of(context).pop((r as Map)['id'] as String);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final kids = _children;
    final contacts = _contacts;
    return AlertDialog(
      title: Text(tr('New message')),
      content: SizedBox(
        width: 420,
        child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (kids == null && _error == null) const SizedBox(height: 80, child: LoadingIndicator()),
          if (kids != null && kids.isEmpty) Text(tr('Ask the school to link your account to your child.')),
          if (kids != null && kids.length > 1)
            DropdownButtonFormField<String>(
              initialValue: _child,
              decoration: InputDecoration(labelText: tr('About')),
              items: [for (final k in kids) DropdownMenuItem(value: k['studentId'] as String, child: Text('${k['name']}'))],
              onChanged: (v) => v == null ? null : _pickChild(v),
            ),
          if (contacts != null)
            DropdownButtonFormField<String>(
              key: const ValueKey('message-to'),
              initialValue: _to,
              decoration: InputDecoration(labelText: tr('To')),
              items: [
                for (final c in contacts)
                  DropdownMenuItem(value: c['userId'] as String, child: Text('${c['name']} (${c['role']})')),
              ],
              onChanged: (v) => setState(() => _to = v),
            ),
          const SizedBox(height: 12),
          TextField(
            key: const ValueKey('message-body'),
            controller: _body,
            minLines: 3,
            maxLines: 6,
            maxLength: 2000,
            decoration: InputDecoration(labelText: tr('Message'), border: const OutlineInputBorder()),
          ),
          if (_error != null)
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ])),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(tr('Cancel'))),
        FilledButton(key: const ValueKey('send-message'), onPressed: _sending ? null : _send, child: Text(tr('Send'))),
      ],
    );
  }
}

/// One conversation: the messages, oldest first, and a reply box.
class ConversationPage extends StatefulWidget {
  final String conversationId;
  const ConversationPage({super.key, required this.conversationId});

  @override
  State<ConversationPage> createState() => _ConversationPageState();
}

class _ConversationPageState extends State<ConversationPage> {
  Map<String, dynamic>? _c;
  String? _error;
  final _reply = TextEditingController();
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _reply.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final c = await Ops.map('/conversations/${widget.conversationId}');
      if (mounted) setState(() => _c = c);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _send() async {
    final text = _reply.text.trim();
    if (text.isEmpty) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final c = await Ops.post('/conversations/${widget.conversationId}/messages', body: {'body': text});
      if (!mounted) return;
      _reply.clear();
      setState(() => _c = Map<String, dynamic>.from(c as Map));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = _c;
    return Scaffold(
      appBar: AppBar(title: Text(c == null ? tr('Messages') : '${c['withName']} · ${c['studentName']}')),
      body: c == null
          ? (_error != null ? ErrorDisplay(message: _error!, onRetry: _load) : const LoadingIndicator())
          : Column(children: [
              Expanded(
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  for (final m in (c['messages'] as List).cast<Map>())
                    Align(
                      alignment: m['mine'] == true ? Alignment.centerRight : Alignment.centerLeft,
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 480),
                        child: Card(
                          color: m['mine'] == true ? theme.colorScheme.primaryContainer : null,
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text('${m['body']}'),
                              const SizedBox(height: 4),
                              Text('${m['senderName']} · ${_when('${m['createdAt']}')}', style: theme.textTheme.bodySmall),
                            ]),
                          ),
                        ),
                      ),
                    ),
                ]),
              ),
              if (_error != null)
                Padding(padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
              SafeArea(
                top: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  child: Row(children: [
                    Expanded(
                      child: TextField(
                        key: const ValueKey('reply-body'),
                        controller: _reply,
                        minLines: 1,
                        maxLines: 4,
                        maxLength: 2000,
                        decoration: InputDecoration(hintText: tr('Write a reply'), counterText: ''),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton.filled(
                      key: const ValueKey('send-reply'),
                      tooltip: tr('Send'),
                      onPressed: _sending ? null : _send,
                      icon: const Icon(Icons.send),
                    ),
                  ]),
                ),
              ),
            ]),
    );
  }
}
