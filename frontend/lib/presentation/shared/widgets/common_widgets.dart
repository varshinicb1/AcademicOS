import 'package:flutter/material.dart';

import '../../../core/constants/app_constants.dart';
import 'package:academicos/core/theme/app_theme.dart';

/// The style a main action carries so a thumb can hit it on the phone layout.
///
/// Material's M3 defaults give a button a 40 px minimum height. The 48 px box
/// it is wrapped in (`_InputPadding`) is invisible and only exists on android
/// and iOS, so what a teacher aims at is the 40 px the button paints -- under
/// the 44 px a thumb reliably hits (Task 801). The whole responsive suite
/// used to measure that invisible box and therefore passed on every button,
/// however small; it now measures the painted one, and these are the actions
/// that failed (review of 2026-09-23).
///
/// `visualDensity` is pinned with the minimum because ThemeData hands a
/// desktop-UA browser `VisualDensity.compact`, which takes 8 px off every
/// `minimumSize` *and* 8 px off the top and bottom of the button's padding
/// (`ButtonStyleButton` adds `baseSizeAdjustment` to both). A phone browser
/// reports android and gets `standard` either way; a desktop window narrowed
/// to 375 px -- the one this task's screenshots were taken in -- does not.
///
/// It is width-aware because that pin is wrong above phone width. Task 801
/// asks for 44 px targets "on the phone layout" and for the desktop look to
/// be kept, and applying this style at every width broke the second: with
/// compact density AppTheme's elevated buttons draw 32 px tall, pinning
/// standard makes them 48 and more padded, and even the bare 48 px minimum
/// alone leaves them at 40. That is a visible change to roughly fifteen
/// laptop controls -- Sign in, Create invite, Withdraw, the six console
/// tabs' actions, Yes/No on the mark-taught sheet -- that nobody asked for
/// and no test could see (review of 2026-09-23). Above the breakpoint this
/// resolves to an empty style, which merges into the theme as no change at
/// all.
ButtonStyle phoneTapTarget(BuildContext context) =>
    MediaQuery.sizeOf(context).width < AppConstants.mobileBreakpoint
        ? _phoneTapTarget
        : const ButtonStyle();

const _phoneTapTarget = ButtonStyle(
  minimumSize: WidgetStatePropertyAll(Size(64, 48)),
  visualDensity: VisualDensity.standard,
);

/// [phoneTapTarget] for a [SegmentedButton], whose segments cannot be given a
/// minimum height at all.
///
/// A segment is a real TextButton, so [phoneTapTarget] looks like it should
/// work on one -- it does not, by two separate routes, and the switch on the
/// sign-in page sat at 40 px for it (review of 2026-09-23):
///   * handed to the SegmentedButton directly, the style is rebuilt by
///     `segmentStyleFor` (segmented_button.dart:530) from a fixed list of
///     properties that `minimumSize` is not on;
///   * handed down as a TextButton theme, it is shadowed -- SegmentedButton
///     wraps its own segments in `TextButtonTheme(data: segmentThemeStyle)`
///     (segmented_button.dart:692), which came through the same filter.
///
/// `padding` and `visualDensity` do survive both, so the height has to be
/// built out of those: pin the density a desktop-UA browser would otherwise
/// compact away, then pad the label to the target. 14 px each side of a 14 px
/// label's line box measures 48 against [AppTheme]'s text styles in Inter -- the
/// same height [phoneTapTarget] asks for, and asserted by the sign-in test
/// rather than written down here.
ButtonStyle phoneSegmentTapTarget(BuildContext context) =>
    MediaQuery.sizeOf(context).width < AppConstants.mobileBreakpoint
        ? _phoneSegmentTapTarget
        : const ButtonStyle();

const _phoneSegmentTapTarget = ButtonStyle(
  visualDensity: VisualDensity.standard,
  padding: WidgetStatePropertyAll(EdgeInsets.symmetric(horizontal: 12, vertical: 14)),
);

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final VoidCallback? onTap;
  final Color? color;
  final double elevation;

  const AppCard({
    super.key,
    required this.child,
    this.padding,
    this.margin,
    this.onTap,
    this.color,
    this.elevation = AppConstants.cardElevation,
  });

  @override
  Widget build(BuildContext context) {
    final card = Container(
      margin: margin ?? const EdgeInsets.only(bottom: 12),
      padding: padding ?? const EdgeInsets.all(AppConstants.defaultPadding),
      decoration: BoxDecoration(
        color: color ?? Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(AppConstants.borderRadius),
        boxShadow: elevation > 0 ? [
          BoxShadow(
            color: Theme.of(context).colorScheme.shadow.withValues(alpha: 0.1),
            blurRadius: elevation,
            offset: Offset(0, elevation / 2),
          )
        ] : null,
        // The tokens' hairline (outlineVariant): cards are outlined, not raised.
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      // Real bug found via an on-device integration test: any ListTile (or
      // other Material-ink widget) placed inside AppCard's child triggers
      // Flutter's "background color or ink splashes may be invisible"
      // assertion, because Container/BoxDecoration is not a Material
      // ancestor -- confirmed on Settings, which nests a ListTile per row
      // inside AppCard and threw this on every single row. A transparent
      // Material here gives descendants a real ink surface without
      // changing AppCard's own decoration/appearance at all.
      child: Material(type: MaterialType.transparency, child: child),
    );

    if (onTap != null) {
      return InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppConstants.borderRadius),
        child: card,
      );
    }
    return card;
  }
}

class LoadingIndicator extends StatelessWidget {
  final String? message;
  final double size;

  const LoadingIndicator({super.key, this.message, this.size = 40});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: size,
            height: size,
            child: CircularProgressIndicator(
              strokeWidth: 3,
              valueColor: AlwaysStoppedAnimation<Color>(Theme.of(context).colorScheme.primary),
            ),
          ),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(message!, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
          ],
        ],
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;
  /// The action's icon; none by default. It used to be a refresh icon on
  /// every action, "Create" ones included.
  final IconData? actionIcon;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
    this.actionIcon,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.largePadding),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 40, color: Theme.of(context).colorScheme.onSurfaceVariant),
            const SizedBox(height: 12),
            Text(title, style: Theme.of(context).textTheme.titleMedium, textAlign: TextAlign.center),
            const SizedBox(height: 4),
            Text(message, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant), textAlign: TextAlign.center),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 20),
              if (actionIcon != null)
                FilledButton.icon(onPressed: onAction, icon: Icon(actionIcon), label: Text(actionLabel!))
              else
                FilledButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ],
        ),
      ),
    );
  }
}

class ChipTag extends StatelessWidget {
  final String label;
  final Color? color;
  final IconData? icon;
  final VoidCallback? onDeleted;

  const ChipTag({
    super.key,
    required this.label,
    this.color,
    this.icon,
    this.onDeleted,
  });

  @override
  Widget build(BuildContext context) {
    final bgColor = color ?? Theme.of(context).colorScheme.primaryContainer;
    final textColor = color != null ? Colors.white : Theme.of(context).colorScheme.onPrimaryContainer;

    return Chip(
      label: Text(label,
          softWrap: false,
          overflow: TextOverflow.visible,
          style: TextStyle(color: textColor, fontSize: 11, fontWeight: FontWeight.w500)),
      avatar: icon != null ? Icon(icon, size: 14, color: textColor) : null,
      backgroundColor: bgColor,
      side: BorderSide.none,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
      labelPadding: const EdgeInsets.symmetric(horizontal: 4),
      deleteIcon: onDeleted != null ? Icon(Icons.close, size: 14, color: textColor) : null,
      onDeleted: onDeleted,
      visualDensity: VisualDensity.compact,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }
}

class ErrorDisplay extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  final String? retryLabel;

  const ErrorDisplay({super.key, required this.message, this.onRetry, this.retryLabel});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.largePadding),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 16),
            Text('Error', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600, color: Theme.of(context).colorScheme.error)),
            const SizedBox(height: 8),
            Text(message, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant), textAlign: TextAlign.center),
            if (onRetry != null) ...[
              const SizedBox(height: 24),
              FilledButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: Text(retryLabel ?? 'Retry')),
            ],
          ],
        ),
      ),
    );
  }
}

class SectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? action;
  final bool showDivider;

  const SectionHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.action,
    this.showDivider = true,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600)),
              const Spacer(),
              if (action != null) action!,
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(subtitle!, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
          ],
          if (showDivider) const Divider(height: 16),
        ],
      ),
    );
  }
}

class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? trend;

  const StatCard({super.key, required this.label, required this.value, required this.icon, required this.color, this.trend});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(AppConstants.borderRadius)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [Icon(icon, color: color, size: 20), const Spacer(), if (trend != null) Text(trend!, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: trend!.startsWith('+') ? AppColors.success : AppColors.danger))]),
          const SizedBox(height: 8),
          Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700, color: color)),
          Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color.withValues(alpha: 0.8))),
        ],
      ),
    );
  }
}

class ProgressRing extends StatelessWidget {
  final double progress;
  final double size;
  final double strokeWidth;
  final Color? progressColor;
  final Color? backgroundColor;
  final Widget? child;

  const ProgressRing({super.key, required this.progress, this.size = 60, this.strokeWidth = 6, this.progressColor, this.backgroundColor, this.child});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        fit: StackFit.expand,
        children: [
          CircularProgressIndicator(
            value: progress,
            strokeWidth: strokeWidth,
            backgroundColor: backgroundColor ?? Theme.of(context).colorScheme.surfaceContainerHighest,
            valueColor: AlwaysStoppedAnimation<Color>(progressColor ?? Theme.of(context).colorScheme.primary),
          ),
          if (child != null) Center(child: child!),
        ],
      ),
    );
  }
}

class ConfirmDialog extends StatelessWidget {
  final String title;
  final String message;
  final String confirmText;
  final String cancelText;
  final bool isDestructive;
  final VoidCallback onConfirm;

  const ConfirmDialog({super.key, required this.title, required this.message, required this.confirmText, this.cancelText = 'Cancel', this.isDestructive = false, required this.onConfirm});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(cancelText)),
        FilledButton(
          onPressed: () { Navigator.pop(context); onConfirm(); },
          style: FilledButton.styleFrom(backgroundColor: isDestructive ? Theme.of(context).colorScheme.error : null),
          child: Text(confirmText),
        ),
      ],
    );
  }
}

extension StringExtensions on String {
  String get capitalize => '${this[0].toUpperCase()}${substring(1)}';
}