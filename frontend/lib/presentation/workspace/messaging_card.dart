import 'package:flutter/material.dart';
import 'package:gap/gap.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import 'ops_api.dart';
import 'strings.dart';

/// A person's own mobile number for SMS and WhatsApp, and their consent per
/// channel (REQUIREMENTS INT-2, NTF-1). Staff and parents only: a student's
/// messages go to their parent. The number is confirmed by a one-time code
/// sent to it before anything else is; nothing is sent without the tick
/// for that channel, and removing the number (or unticking both) withdraws
/// both.
class MessagingCard extends StatefulWidget {
  const MessagingCard({super.key});

  /// Roles that may add a number (a student is a minor, DPDP Act 2023).
  static bool appliesTo(String role) => const {'teacher', 'principal', 'parent'}.contains(role);

  @override
  State<MessagingCard> createState() => _MessagingCardState();
}

class _MessagingCardState extends State<MessagingCard> {
  final _phone = TextEditingController();
  final _code = TextEditingController();
  bool _sms = false, _whatsapp = false, _busy = false, _loaded = false;
  bool _smsAvailable = false, _whatsappAvailable = false, _hasNumber = false, _verified = false;
  String? _error, _note, _codeNote;

  @override
  void initState() {
    super.initState();
    // A student never has a number: the route refuses them, so do not ask.
    if (MessagingCard.appliesTo(CurrentSession.role)) _load();
  }

  @override
  void dispose() {
    _phone.dispose();
    _code.dispose();
    super.dispose();
  }

  void _take(Map<String, dynamic> c) {
    _phone.text = (c['phone'] as String?) ?? '';
    _hasNumber = c['phone'] != null;
    _verified = c['verified'] == true;
    _sms = c['smsOk'] == true;
    _whatsapp = c['whatsappOk'] == true;
    _smsAvailable = c['smsAvailable'] == true;
    _whatsappAvailable = c['whatsappAvailable'] == true;
    final via = c['codeSentVia'] as String?;
    _codeNote = via != null
        ? '${tr('A code was sent by')} ${via == 'whatsapp' ? 'WhatsApp' : 'SMS'}. ${tr('Type it below to confirm the number.')}'
        : c['codeError'] as String?;
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
        _note = remove
            ? tr('Number removed. No SMS or WhatsApp will be sent.')
            : !_hasNumber
                ? tr('Nothing ticked, so your number is not kept.')
                : tr('Saved.');
      });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _confirm() async {
    setState(() {
      _busy = true;
      _error = null;
      _note = null;
    });
    try {
      final c = await Ops.post('/me/contact/verify', body: {'code': _code.text.trim()});
      if (!mounted) return;
      setState(() {
        _take(Map<String, dynamic>.from(c as Map));
        _code.clear();
        _note = tr('Number confirmed.');
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
    final what = CurrentSession.role == 'parent'
        ? tr('About your children: homework due, an exam tomorrow and holidays.')
        : tr('For cover requests, leave decisions, invigilation duties and holidays.');
    return Column(key: const ValueKey('messaging-card'), crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(tr('SMS and WhatsApp'), style: theme.textTheme.titleSmall),
      const Gap(4),
      Text('$what ${tr('Only to your own number once you confirm it, only on the channels you tick, '
          'and never in your quiet hours.')}', key: const ValueKey('messaging-what'), style: muted),
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
        decoration: InputDecoration(labelText: tr('Mobile number'), hintText: '98765 43210',
            border: const OutlineInputBorder(),
            helperText: _hasNumber ? (_verified ? tr('Confirmed') : tr('Not confirmed yet')) : null),
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
      if (_hasNumber && !_verified) ...[
        if (_codeNote != null) Text(_codeNote!, key: const ValueKey('messaging-code-note'), style: muted),
        const Gap(4),
        Row(children: [
          Expanded(
            child: TextField(
              key: const ValueKey('messaging-code'),
              controller: _code,
              keyboardType: TextInputType.number,
              maxLength: 6,
              decoration: InputDecoration(labelText: tr('Code'), border: const OutlineInputBorder(),
                  counterText: ''),
            ),
          ),
          const Gap(8),
          FilledButton.tonal(key: const ValueKey('messaging-confirm'), onPressed: _busy ? null : _confirm,
              child: Text(tr('Confirm'))),
        ]),
        TextButton(key: const ValueKey('messaging-resend'), onPressed: _busy ? null : _save,
            child: Text(tr('Send the code again'))),
      ],
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
