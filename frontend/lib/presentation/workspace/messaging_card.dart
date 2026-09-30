import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import 'ops_api.dart';
import 'strings.dart';

/// A person's own mobile number for SMS and WhatsApp, and their consent per
/// channel (REQUIREMENTS INT-2, NTF-1). Staff and parents only: a student's
/// messages go to their parent. Nothing is sent without the tick for that
/// channel, and removing the number withdraws both.
class MessagingCard extends StatefulWidget {
  const MessagingCard({super.key});

  /// Roles that may add a number (a student is a minor, DPDP Act 2023).
  static bool appliesTo(String role) => const {'teacher', 'principal', 'parent'}.contains(role);

  @override
  State<MessagingCard> createState() => _MessagingCardState();
}

class _MessagingCardState extends State<MessagingCard> {
  final _phone = TextEditingController();
  bool _sms = false, _whatsapp = false, _busy = false, _loaded = false;
  bool _smsAvailable = false, _whatsappAvailable = false, _hasNumber = false;
  String? _error, _note;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _phone.dispose();
    super.dispose();
  }

  void _take(Map<String, dynamic> c) {
    _phone.text = (c['phone'] as String?) ?? '';
    _hasNumber = c['phone'] != null;
    _sms = c['smsOk'] == true;
    _whatsapp = c['whatsappOk'] == true;
    _smsAvailable = c['smsAvailable'] == true;
    _whatsappAvailable = c['whatsappAvailable'] == true;
    _loaded = true;
  }

  Future<void> _load() async {
    try {
      final c = await Ops.map('/me/contact');
      if (mounted) setState(() => _take(c));
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    }
  }

  Future<void> _save({bool remove = false}) async {
    if (!remove && _phone.text.trim().isEmpty) {
      setState(() => _error = tr('Give your mobile number, or leave both boxes unticked.'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _note = null;
    });
    try {
      final c = await Ops.put('/me/contact', body: remove
          ? {'phone': null}
          : {'phone': _phone.text.trim(), 'smsOk': _sms, 'whatsappOk': _whatsapp});
      if (!mounted) return;
      setState(() {
        _take(Map<String, dynamic>.from(c as Map));
        _note = remove ? tr('Number removed. No SMS or WhatsApp will be sent.') : tr('Saved.');
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!MessagingCard.appliesTo(CurrentSession.role)) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    if (!_loaded) {
      return _error != null
          ? Text(_error!, style: TextStyle(color: theme.colorScheme.error))
          : const LinearProgressIndicator();
    }
    final off = [
      if (!_smsAvailable) 'SMS',
      if (!_whatsappAvailable) 'WhatsApp',
    ];
    return Column(key: const ValueKey('messaging-card'), crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(tr('SMS and WhatsApp'), style: theme.textTheme.titleSmall),
      const Gap(4),
      Text(tr('For cover requests, leave decisions, homework due, exams, duties and holidays. '
          'Only to your own number, only on the channels you tick, and never in your quiet hours.'), style: muted),
      if (off.isNotEmpty) ...[
        const Gap(4),
        Text(key: const ValueKey('messaging-off'),
            '${tr('The school has not switched on')} ${off.join(' / ')} ${tr('yet; your choice is kept for when it does.')}',
            style: muted),
      ],
      const Gap(8),
      TextField(
        key: const ValueKey('messaging-phone'),
        controller: _phone,
        keyboardType: TextInputType.phone,
        decoration: InputDecoration(labelText: tr('Mobile number'), hintText: '98765 43210'),
      ),
      CheckboxListTile(
        key: const ValueKey('messaging-sms'),
        contentPadding: EdgeInsets.zero,
        value: _sms,
        onChanged: _busy ? null : (v) => setState(() => _sms = v ?? false),
        title: Text(tr('I agree to receive these notices by SMS')),
      ),
      CheckboxListTile(
        key: const ValueKey('messaging-whatsapp'),
        contentPadding: EdgeInsets.zero,
        value: _whatsapp,
        onChanged: _busy ? null : (v) => setState(() => _whatsapp = v ?? false),
        title: Text(tr('I agree to receive these notices on WhatsApp')),
      ),
      if (_error != null) Text(_error!, key: const ValueKey('messaging-error'),
          style: TextStyle(color: theme.colorScheme.error)),
      if (_note != null) Text(_note!, style: muted),
      const Gap(4),
      Wrap(spacing: 8, children: [
        FilledButton(key: const ValueKey('messaging-save'), onPressed: _busy ? null : _save, child: Text(tr('Save'))),
        if (_hasNumber)
          TextButton(key: const ValueKey('messaging-remove'), onPressed: _busy ? null : () => _save(remove: true),
              child: Text(tr('Remove my number'))),
      ]),
    ]);
  }
}
