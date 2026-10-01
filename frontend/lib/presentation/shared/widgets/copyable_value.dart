import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/theme/emergera.dart';
import '../../../data/datasources/api/api_error.dart';

/// A code, key or password the principal has to pass on: shown in the app's
/// own typeface so it can be read out or written down, selectable, with a
/// Copy button that says when it has copied.
///
/// The invite and API-key dialogs showed only Copy buttons (QA S-07,
/// 2026-10-01): their value was a SelectableText in `fontFamily: 'monospace'`,
/// a family the web build does not bundle, so where the browser could not
/// fetch a fallback face the value painted as nothing. Copy then gave no
/// sign it had worked, and an API key is shown once: a blocked clipboard lost
/// it for good.
class CopyableValue extends StatefulWidget {
  const CopyableValue({super.key, required this.value, required this.copiedMessage, this.copyLabel = 'Copy'});

  final String value;

  /// The snackbar's sentence once it is copied ("Invite code copied.").
  final String copiedMessage;
  final String copyLabel;

  @override
  State<CopyableValue> createState() => _CopyableValueState();
}

class _CopyableValueState extends State<CopyableValue> {
  bool _copied = false;

  Future<void> _copy() async {
    final ok = await copyWithNotice(context, widget.value, widget.copiedMessage);
    if (mounted && ok) setState(() => _copied = true);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final em = EmSurfaces.of(theme.brightness);
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 6, 6, 6),
      decoration: BoxDecoration(
        color: em.fill2,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: em.rimLine),
      ),
      child: Row(children: [
        Expanded(
          child: SelectableText(
            widget.value,
            key: const ValueKey('copyable-value'),
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600, letterSpacing: 0.6),
          ),
        ),
        const SizedBox(width: 8),
        TextButton.icon(
          key: const ValueKey('copyable-copy'),
          onPressed: _copy,
          icon: Icon(_copied ? Icons.check : Icons.copy, size: 18),
          label: Text(_copied ? 'Copied' : widget.copyLabel),
        ),
      ]),
    );
  }
}

/// Puts [text] on the clipboard and says so in a snackbar; when the browser
/// refuses, says that instead, so nobody believes a value was copied that
/// was not. True when it was copied.
Future<bool> copyWithNotice(BuildContext context, String text, String copiedMessage) async {
  final messenger = ScaffoldMessenger.maybeOf(context);
  try {
    await Clipboard.setData(ClipboardData(text: text));
  } catch (e) {
    messenger?.showSnackBar(SnackBar(
        content: Text('Could not copy (${serverErrorMessage(e)}). Select the text and copy it by hand.')));
    return false;
  }
  // A second copy (the code, then its link) replaces the first notice
  // rather than waiting behind it.
  messenger
    ?..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(copiedMessage)));
  return true;
}

/// Asks before a one-tap action that cannot be quietly undone -- revoking an
/// API key, withdrawing an invite, taking away an admin area (QA S-18) --
/// naming what will happen. True only when the person confirms.
Future<bool> confirmAction(BuildContext context,
    {required String title, required String message, required String confirmLabel}) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (dialog) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('Cancel')),
        FilledButton(
          key: const ValueKey('confirm-action'),
          style: FilledButton.styleFrom(backgroundColor: Theme.of(dialog).colorScheme.error),
          onPressed: () => Navigator.pop(dialog, true),
          child: Text(confirmLabel),
        ),
      ],
    ),
  );
  return ok == true;
}
