import '../../../data/datasources/api/api_error.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/session/current_session.dart';
import '../../../core/theme/emergera.dart';

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
    // With no colour: the brand's ember chip (.em-chip--ember).
    final em = EmSurfaces.of(Theme.of(context).brightness);
    final bgColor = color ?? em.chipEmberBg;
    final textColor = color != null ? Colors.white : em.chipEmberFg;

    final chip = Chip(
      label: Text(label,
          softWrap: false,
          overflow: TextOverflow.visible,
          style: TextStyle(color: textColor, fontSize: 12, fontWeight: FontWeight.w500)),
      avatar: icon != null ? Icon(icon, size: 14, color: textColor) : null,
      backgroundColor: bgColor,
      side: color == null ? BorderSide(color: em.chipEmberRim) : BorderSide.none,
      shape: const StadiumBorder(),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
      labelPadding: const EdgeInsets.symmetric(horizontal: 4),
      deleteIcon: onDeleted != null ? Icon(Icons.close, size: 14, color: textColor) : null,
      onDeleted: onDeleted,
      visualDensity: VisualDensity.compact,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
    if (onDeleted != null) return chip;
    // A tag is read, not pressed: Chip reports a selected state, which the
    // web build announced as a checkbox ("Ready", "1m", "CBQ"; QA P-28).
    return Semantics(container: true, label: label, excludeSemantics: true, child: chip);
  }
}

/// The sentences the server and the pages answer with when the school has no
/// academic year, calendar, term or bell yet. A brand-new school met one of
/// these as a red "Error" with a Retry on Term report, Exams, Timetable,
/// Lesson plans and more (school's screenshots, 2026-10-01).
const _notSetUpPhrases = [
  'no academic year', // "... covers today", "... contains the exam's start date", "... of this school contains that date"
  'academic year set up yet', // the pages' own "Your school has no academic year set up yet."
  'set up an academic year first',
  'no term of this school covers',
  'today is in no term',
  'no calendar configured for this academic year',
  'create a calendar for this academic year first',
];

/// True when [message] says the school has not been set up yet.
bool isSchoolNotSetUp(String message) {
  final m = message.toLowerCase();
  return _notSetUpPhrases.any(m.contains);
}

/// Where the setup wizard lives.
const schoolSetupPath = '/school/setup';

bool get _signedInAsPrincipal {
  try {
    return CurrentSession.role == 'principal';
  } catch (_) {
    // not-a-failure: no session store (a page mounted alone in a test): say what to do, without the button
    return false;
  }
}

/// What a page shows instead of an error when the school is not set up: one
/// sentence, and for the principal the button to the setup wizard. Anyone else
/// is told to ask the principal, the only one who can set it up.
class SchoolNotSetUp extends StatelessWidget {
  /// Null: read from the signed-in session.
  final bool? isPrincipal;

  /// What this place needs from the setup ("An exam goes inside the school
  /// year, and there is none yet."). Null: the general sentence.
  final String? why;

  /// Called just before the wizard opens, so a dialog can close itself first.
  final VoidCallback? beforeOpen;

  const SchoolNotSetUp({super.key, this.isPrincipal, this.why, this.beforeOpen});

  @override
  Widget build(BuildContext context) {
    final principal = isPrincipal ?? _signedInAsPrincipal;
    final theme = Theme.of(context);
    return Center(
      key: const ValueKey('school-not-set-up'),
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.largePadding),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.school_outlined, size: 44, color: theme.colorScheme.primary),
            const SizedBox(height: 12),
            Text("Your school isn't set up yet", style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
            const SizedBox(height: 6),
            Text(
              [
                if (why != null) why!,
                principal
                    ? 'Set up the year, classes, terms and bell in a few steps.'
                    : 'Ask your principal to set up the school.',
              ].join(' '),
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
            if (principal) ...[
              const SizedBox(height: 20),
              FilledButton.icon(
                key: const ValueKey('school-not-set-up-action'),
                style: phoneTapTarget(context),
                onPressed: () {
                  final router = GoRouter.maybeOf(context);
                  beforeOpen?.call();
                  router?.push(schoolSetupPath);
                },
                icon: const Icon(Icons.rocket_launch_outlined),
                label: const Text('Set up your school'),
              ),
            ],
          ]),
        ),
      ),
    );
  }
}

/// The heading [ErrorDisplay] puts over a failure's sentence.
const errorDisplayTitle = "This didn't load";

class ErrorDisplay extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  final String? retryLabel;

  const ErrorDisplay({super.key, required this.message, this.onRetry, this.retryLabel});

  @override
  Widget build(BuildContext context) {
    // A school with no year, term or bell is not a fault to show in red: it
    // is the next thing to do.
    if (isSchoolNotSetUp(message)) return const SchoolNotSetUp();
    // A feature that is not switched on yet is not a fault: calm, no Retry.
    if (isComingSoonMessage(message)) {
      final theme = Theme.of(context);
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.largePadding),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Icon(Icons.schedule_outlined, size: 56, color: theme.colorScheme.primary),
            const SizedBox(height: 16),
            Text(comingSoonPrefix, key: const ValueKey('coming-soon'),
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Text(message.substring(comingSoonPrefix.length).replaceFirst(RegExp(r'^:\s*'), ''),
                style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                textAlign: TextAlign.center),
          ]),
        ),
      );
    }
    // Until 2026-10-04 this was a 64 px red icon over a red "Error": a page
    // that could not load looked broken, whatever the sentence under it said.
    // Now one calm heading that says what happened, the sentence, and Retry.
    final theme = Theme.of(context);
    final offline = message == unreachableMessage;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.largePadding),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(offline ? Icons.cloud_off_outlined : Icons.info_outline,
                  size: 40, color: theme.colorScheme.onSurfaceVariant),
              const SizedBox(height: 12),
              Text(errorDisplayTitle, key: const ValueKey('error-display-title'),
                  style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
              const SizedBox(height: 6),
              Text(message,
                  style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  textAlign: TextAlign.center),
              if (onRetry != null) ...[
                const SizedBox(height: 20),
                FilledButton.icon(
                    style: phoneTapTarget(context),
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh),
                    label: Text(retryLabel ?? 'Retry')),
              ],
            ],
          ),
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
              // The title wraps rather than pushing the action off a phone's
              // screen (a long or Hindi title overflowed at 390 px).
              Expanded(
                child: Text(title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600)),
              ),
              if (action != null) ...[const SizedBox(width: 8), action!],
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