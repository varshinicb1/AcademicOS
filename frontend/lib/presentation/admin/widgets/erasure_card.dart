import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/auth_api.dart';
import '../../../data/datasources/api/curriculum_api.dart' show serverErrorMessage;
import '../../shared/widgets/common_widgets.dart';

/// Where the principal erases a student's or a parent's data on the school's
/// written request (DPDP; NFR-1; src/academicos/assessment/erasure.py). The
/// server does the work; this card picks the person, shows what would be
/// deleted and what stays, and asks whose request it was, the day it arrived
/// and the person's name typed out, because an erasure cannot be undone.
///
/// Closed students and parents are listed too: an erasure that could not
/// finish leaves the account closed, and is finished by running it again.
class ErasureCard extends StatefulWidget {
  const ErasureCard({super.key, this.api, this.today});

  /// Injected in tests; the app uses the registered AuthApi.
  final AuthApi? api;

  /// Injected in tests; the device's date otherwise. The server refuses a
  /// date after the school's own today (IST).
  final DateTime? today;

  @override
  State<ErasureCard> createState() => _ErasureCardState();
}

const _roles = {'student': 'Student', 'parent': 'Parent', 'left:student': 'Closed student', 'left:parent': 'Closed parent'};

String _nothingHeld(int places) => places == 1
    ? 'Nothing is held in the one other place checked.'
    : 'Nothing is held in the other $places places checked.';

class _ErasureCardState extends State<ErasureCard> {
  late final AuthApi _api = widget.api ?? GetIt.I<AuthApi>();
  List<AuthUser>? _people;
  String? _personId;
  ErasurePreview? _preview;
  bool _busy = false;
  String? _error;
  String? _done;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final active = await _api.usersForSchool();
      final closed = await _api.usersForSchool(role: 'left');
      final byId = <String, AuthUser>{
        for (final u in [...active, ...closed])
          if (_roles.containsKey(u.role)) u.id: u,
      };
      final people = byId.values.toList()..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
      if (mounted) setState(() => _people = people);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load the students and parents: ${serverErrorMessage(e)}');
    }
  }

  Future<void> _showPreview(String id) async {
    setState(() {
      _personId = id;
      _preview = null;
      _error = null;
      _done = null;
      _busy = true;
    });
    try {
      final preview = await _api.erasurePreview(id);
      if (mounted) setState(() => _preview = preview);
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _erase(ErasurePreview preview) async {
    final today = widget.today ?? DateTime.now();
    final answer = await showDialog<(String, DateTime, String)>(
      context: context,
      builder: (ctx) => _ConfirmErasure(preview: preview, today: today),
    );
    if (answer == null) return;
    final (requestedBy, receivedOn, typedName) = answer;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final parts = await _api.erase(preview.userId,
          requestedBy: requestedBy, requestReceivedOn: receivedOn, confirmName: typedName);
      final total = parts.fold<int>(0, (n, p) => n + p.count);
      if (!mounted) return;
      setState(() {
        _done = "${preview.name}'s data is erased: $total records and files deleted. "
            'The audit log keeps a record of the erasure, without their name.';
        _preview = null;
        _personId = null;
        _people = null;
      });
      await _load();
    } catch (e) {
      // A 503 says which parts are left; the account stays closed. The
      // preview is counted again, so it shows what is left, not what was.
      final message = serverErrorMessage(e);
      if (mounted) await _load();
      if (mounted) await _showPreview(preview.userId);
      if (mounted) setState(() => _error = message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    final people = _people;
    final preview = _preview;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("Erase a student's or parent's data", style: theme.textTheme.titleSmall),
          const Gap(4),
          Text('Only on a written request to the school (from the parent, the student, or the school itself). '
              'Everything AcademicOS holds of the person is deleted: their account, work, marks, photos, '
              'scans, progress and notifications. It cannot be undone. A member of staff who left is closed '
              'on Staff permissions instead.', style: muted),
          const Gap(12),
          if (people == null && _error == null)
            const LinearProgressIndicator()
          else if (people != null && people.isEmpty)
            Text('No students or parents have accounts yet.', style: muted)
          else if (people != null)
            DropdownButtonFormField<String>(
              key: ValueKey('erase-person-${people.length}-$_personId'),
              initialValue: _personId,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Student or parent'),
              items: [
                for (final u in people)
                  // Name and role first: on a phone the email is what gets cut.
                  DropdownMenuItem(value: u.id, child: Text('${u.name} · ${_roles[u.role]} (${u.email})',
                      overflow: TextOverflow.ellipsis)),
              ],
              onChanged: _busy
                  ? null
                  : (id) {
                      if (id != null) _showPreview(id);
                    },
            ),
          if (_busy) const Padding(padding: EdgeInsets.only(top: 12), child: LinearProgressIndicator()),
          if (_error != null) ...[
            const Gap(12),
            Text(_error!, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.error)),
          ],
          if (_done != null) ...[
            const Gap(12),
            Row(children: [
              Icon(Icons.check_circle_outline, color: theme.colorScheme.primary),
              const Gap(8),
              Expanded(child: Text(_done!)),
            ]),
          ],
          if (preview != null) ...[
            const Gap(16),
            Text('What would be deleted', style: theme.textTheme.labelLarge),
            const Gap(4),
            // Only what is held: most people have nothing in most places, and
            // a column of zeros hides the rows that matter.
            for (final p in preview.parts.where((p) => p.count > 0))
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Row(children: [
                  Expanded(child: Text(p.label)),
                  Text('${p.count}', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                ]),
              ),
            if (preview.parts.any((p) => p.count == 0))
              Text(_nothingHeld(preview.parts.where((p) => p.count == 0).length), style: muted),
            const Gap(12),
            Text('What stays', style: theme.textTheme.labelLarge),
            const Gap(4),
            for (final (what, why) in preview.kept)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('$what: $why', style: muted),
              ),
            const Gap(16),
            FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: theme.colorScheme.error,
                  foregroundColor: theme.colorScheme.onError),
              onPressed: _busy ? null : () => _erase(preview),
              icon: const Icon(Icons.delete_forever_outlined),
              label: Text("Erase ${preview.name}'s data"),
            ),
          ],
        ],
      ),
    );
  }
}

/// Whose request, the day it arrived, and the name typed out. Returns
/// (requestedBy, receivedOn, typedName), or null when cancelled.
class _ConfirmErasure extends StatefulWidget {
  const _ConfirmErasure({required this.preview, required this.today});
  final ErasurePreview preview;
  final DateTime today;

  @override
  State<_ConfirmErasure> createState() => _ConfirmErasureState();
}

class _ConfirmErasureState extends State<_ConfirmErasure> {
  final _name = TextEditingController();
  // Nothing chosen until the principal says: the audit log keeps it.
  String? _by;
  late DateTime _on = DateUtils.dateOnly(widget.today);

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  static String _norm(String s) => s.trim().split(RegExp(r'\s+')).join(' ').toLowerCase();

  @override
  Widget build(BuildContext context) {
    final p = widget.preview;
    final matches = _norm(_name.text) == _norm(p.name);
    final day = MaterialLocalizations.of(context).formatMediumDate(_on);
    return AlertDialog(
      title: Text("Erase ${p.name}'s data?"),
      content: SizedBox(
        width: 460,
        child: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('This deletes everything listed and cannot be undone.'),
            const Gap(12),
            const Text('Whose written request is this?'),
            RadioGroup<String>(
              groupValue: _by,
              onChanged: (v) => setState(() => _by = v),
              child: const Column(mainAxisSize: MainAxisSize.min, children: [
                RadioListTile<String>(dense: true, value: 'parent', title: Text('A parent or guardian')),
                RadioListTile<String>(dense: true, value: 'student', title: Text('The student')),
                RadioListTile<String>(dense: true, value: 'school', title: Text('The school')),
              ]),
            ),
            const Gap(8),
            Row(children: [
              Expanded(child: Text('Request received on $day')),
              TextButton(
                onPressed: () async {
                  final picked = await showDatePicker(context: context, initialDate: _on,
                      firstDate: DateTime(_on.year - 2), lastDate: DateUtils.dateOnly(widget.today));
                  if (picked != null) setState(() => _on = picked);
                },
                child: const Text('Change date'),
              ),
            ]),
            const Gap(8),
            TextField(
              controller: _name,
              autofocus: true,
              decoration: InputDecoration(labelText: 'Type ${p.name} to confirm'),
              onChanged: (_) => setState(() {}),
            ),
          ]),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.error,
              foregroundColor: Theme.of(context).colorScheme.onError),
          onPressed: matches && _by != null ? () => Navigator.pop(context, (_by!, _on, _name.text.trim())) : null,
          child: const Text('Erase'),
        ),
      ],
    );
  }
}
