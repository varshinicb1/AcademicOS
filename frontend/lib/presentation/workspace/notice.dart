import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

enum NoticeKind { info, warning, danger, success }

/// A soft, bordered note in one of the tokens' status colours: what a
/// screen has to say about the data in front of it (a shortfall, a refusal
/// with every reason the server gave, a result), not a snackbar that is gone
/// before it is read. [lines] are shown as a list under the [title].
class Notice extends StatelessWidget {
  final NoticeKind kind;
  final String title;
  final List<String> lines;
  final Widget? action;

  const Notice({super.key, required this.kind, required this.title, this.lines = const [], this.action});

  @override
  Widget build(BuildContext context) {
    final s = StatusColors.of(context);
    final (fg, bg, border, icon) = switch (kind) {
      NoticeKind.info => (s.info, s.infoBg, s.infoBorder, Icons.info_outline),
      NoticeKind.warning => (s.warning, s.warningBg, s.warningBorder, Icons.warning_amber_outlined),
      NoticeKind.danger => (s.danger, s.dangerBg, s.dangerBorder, Icons.error_outline),
      NoticeKind.success => (s.success, s.successBg, s.successBorder, Icons.check_circle_outline),
    };
    final text = Theme.of(context).textTheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: bg,
        border: Border.all(color: border),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, size: 20, color: fg),
        const SizedBox(width: 8),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: text.bodyMedium?.copyWith(color: fg, fontWeight: FontWeight.w600)),
            for (final l in lines) ...[
              const SizedBox(height: 4),
              Text('• $l', style: text.bodySmall),
            ],
            if (action != null) ...[const SizedBox(height: 8), action!],
          ]),
        ),
      ]),
    );
  }
}

/// The first [max] of [items], and "and N more" for the rest, so a list of
/// sixty subtopic names does not take the screen.
List<String> firstFew(List<String> items, {int max = 8}) =>
    items.length <= max ? items : [...items.take(max), 'and ${items.length - max} more'];
