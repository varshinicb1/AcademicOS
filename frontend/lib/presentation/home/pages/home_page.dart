import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:go_router/go_router.dart';

import '../../../core/local_engine/demo_seeder.dart';
import '../../../core/local_engine/local_store.dart';
import '../../onboarding/pages/app_tour_page.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

const _offlineMode = bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
const _seedDemoData = bool.fromEnvironment('ACADEMICOS_SEED_DEMO', defaultValue: false);

/// The app's real landing screen -- replaces opening cold into Syllabus
/// Coverage with no sense of "what do I actually need to do right now."
/// Every number here is a real query against LocalStore, not placeholder
/// content: pending reviews, recent assessments, a real activity streak
/// computed from the audit log's actual timestamps. Two big one-tap actions
/// (New Assessment, Scan & Grade) put the two things a teacher does most
/// within a single tap of opening the app, instead of three menu levels deep.
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    // Real regression found and fixed on-device: seeding used to be an
    // unawaited fire-and-forget in main.dart, which fixed a real crash-on-
    // launch bug but introduced a new one -- this page reads LocalStore
    // once per build with no listener, so a background seed that finished
    // AFTER this page's first build never appeared without a manual
    // pull-to-refresh. Owning the trigger here, with a real setState() when
    // it completes, keeps the "never blocks/crashes launch" property while
    // actually reflecting the seeded data once it's ready. Confirmed on a
    // real device: without this, "Today" stayed on "No assessments yet"
    // indefinitely despite 5 real assessments existing in LocalStore.
    if (_offlineMode && _seedDemoData) {
      DemoSeeder.seedIfEmpty().then((_) {
        if (mounted) setState(() {});
        _maybeShowTour();
      }).catchError((Object e, StackTrace stack) {
        debugPrint('DemoSeeder.seedIfEmpty failed (app continues normally): $e\n$stack');
        _maybeShowTour();
      });
    }
  }

  // Shown once per install (see LocalStore.hasSeenAppTour) -- deliberately
  // gated on the seeding step above rather than fired unconditionally, so it
  // never covers Home before the demo data it's describing actually exists.
  // Also reachable any time from Settings -> "Show App Tour" (see AppTourPage
  // doc comment), so dismissing it early isn't a dead end for a teacher.
  void _maybeShowTour() {
    if (!mounted || LocalStore.instance.hasSeenAppTour) return;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      await Navigator.of(context)
          .push(MaterialPageRoute(builder: (_) => const AppTourPage(), fullscreenDialog: true));
      await LocalStore.instance.markAppTourSeen();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final store = LocalStore.instance;

    // Real-device robustness, not just tidy code: an assessment record from
    // an older schema/app version missing updatedAt must not crash the
    // app's own landing screen -- a `as String` force-cast would.
    final assessments = store.allAssessments()
      ..sort((a, b) => (b['updatedAt'] as String? ?? '').compareTo(a['updatedAt'] as String? ?? ''));
    final scanSessions = store.allScanSessions();
    final pendingReview = scanSessions.where((s) => s['status'] == 'reviewing').toList();
    final streak = _currentStreak(store.auditLog());

    // Unsynced assessments: those without metadata.serverSyncedAt
    final unsyncedCount = assessments.where((a) {
      final meta = a['metadata'] as Map<String, dynamic>?;
      return meta == null || meta['serverSyncedAt'] == null;
    }).length;

    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Today'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => setState(() {}),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _greeting(theme, streak),
            const Gap(20),
            _quickActions(context, theme),
            const Gap(20),
            // Online-only: the new curriculum/schedule module has no
            // offline mirror yet (see my_schedule_page.dart's own doc
            // comment) -- hidden entirely offline rather than shown and
            // immediately erroring, same posture as the sync card below.
            if (!_offlineMode) ...[
              _myScheduleCard(context, theme),
              const Gap(20),
            ],
            if (pendingReview.isNotEmpty) ...[
              _attentionCard(context, theme, pendingReview.length),
              const Gap(20),
            ],
            // Real fix: this card said "tap to sync now" and, tapped, just
            // navigated to Settings without syncing anything -- and in this
            // offline build there is no server for it to sync to regardless.
            // Shown only in a build that could actually mean it.
            if (!_offlineMode && unsyncedCount > 0) ...[
              _unsyncedCard(context, theme, unsyncedCount),
              const Gap(20),
            ],
            if (scanSessions.isNotEmpty) ...[
              _scanHistoryCard(context, theme, scanSessions.length),
              const Gap(20),
            ],
            Text('Recent assessments', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const Gap(8),
            if (assessments.isEmpty)
              _emptyRecent(context, theme)
            else
              ...assessments.take(4).map((a) => _assessmentTile(context, theme, a)),
          ],
        ),
      ),
    );
  }

  Widget _greeting(ThemeData theme, int streak) {
    final hour = DateTime.now().hour;
    final greeting = hour < 12 ? 'Good morning' : (hour < 17 ? 'Good afternoon' : 'Good evening');
    final date = _formatDate(DateTime.now());
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(greeting, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
              Text(date, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ],
          ),
        ),
        if (streak > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.local_fire_department, size: 18, color: theme.colorScheme.onPrimaryContainer),
                const Gap(4),
                Text('$streak day${streak == 1 ? '' : 's'}',
                    style: theme.textTheme.labelLarge
                        ?.copyWith(color: theme.colorScheme.onPrimaryContainer, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
      ],
    );
  }

  Widget _quickActions(BuildContext context, ThemeData theme) {
    return Row(
      children: [
        Expanded(
          child: _actionButton(
            context, theme,
            icon: Icons.assignment_add,
            label: 'New Assessment',
            onTap: () => context.push('/assessment/create'),
          ),
        ),
        const Gap(12),
        Expanded(
          child: _actionButton(
            context, theme,
            icon: Icons.document_scanner,
            label: 'Scan & Grade',
            onTap: () => context.go('/scan'),
          ),
        ),
      ],
    );
  }

  Widget _actionButton(BuildContext context, ThemeData theme,
      {required IconData icon, required String label, required VoidCallback onTap}) {
    return Material(
      color: theme.colorScheme.primary,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: theme.colorScheme.onPrimary, size: 28),
              const Gap(8),
              Text(label,
                  textAlign: TextAlign.center,
                  style: theme.textTheme.labelLarge
                      ?.copyWith(color: theme.colorScheme.onPrimary, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _myScheduleCard(BuildContext context, ThemeData theme) {
    return AppCard(
      onTap: () => context.push('/my-schedule'),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, shape: BoxShape.circle),
            child: Icon(Icons.today, color: theme.colorScheme.onPrimaryContainer, size: 22),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('My Schedule', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                Text(
                  'What you\'re teaching today, from your real curriculum schedule',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right, color: theme.colorScheme.onSurfaceVariant),
        ],
      ),
    );
  }

  Widget _attentionCard(BuildContext context, ThemeData theme, int count) {
    return AppCard(
      onTap: () => context.go('/scan'),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.errorContainer, shape: BoxShape.circle),
            child: Icon(Icons.rate_review, color: theme.colorScheme.onErrorContainer, size: 22),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Needs your review', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                Text(
                  '$count scanned answer sheet${count == 1 ? '' : 's'} waiting -- AI-graded, needs your approval',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right, color: theme.colorScheme.onSurfaceVariant),
        ],
      ),
    );
  }

  Widget _unsyncedCard(BuildContext context, ThemeData theme, int count) {
    return AppCard(
      onTap: () => context.go('/settings'),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.secondaryContainer, shape: BoxShape.circle),
            child: Icon(Icons.cloud_off, color: theme.colorScheme.onSecondaryContainer, size: 22),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Not synced yet', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                Text(
                  '$count assessment${count == 1 ? '' : 's'} waiting to sync — tap to sync now',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right, color: theme.colorScheme.onSurfaceVariant),
        ],
      ),
    );
  }

  Widget _scanHistoryCard(BuildContext context, ThemeData theme, int count) {
    return AppCard(
      onTap: () => context.push('/scan-history'),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: theme.colorScheme.tertiaryContainer, shape: BoxShape.circle),
            child: Icon(Icons.history_edu_outlined, color: theme.colorScheme.onTertiaryContainer, size: 22),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Scan history', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                Text(
                  '$count scanned answer sheet${count == 1 ? '' : 's'} on this device -- tap to browse',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right, color: theme.colorScheme.onSurfaceVariant),
        ],
      ),
    );
  }

  Widget _emptyRecent(BuildContext context, ThemeData theme) {
    return AppCard(
      onTap: () => context.push('/assessment/create'),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          children: [
            Icon(Icons.assignment_outlined, color: theme.colorScheme.onSurfaceVariant),
            const Gap(12),
            Expanded(
              child: Text('No assessments yet -- tap to build your first one with the AI Assessment Designer.',
                  style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _assessmentTile(BuildContext context, ThemeData theme, Map<String, dynamic> a) {
    final totalMarks = (a['blueprint'] as Map?)?['totalMarks'];
    return AppCard(
      onTap: () => context.push('/assessment/${a['id']}'),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(a['title'] as String? ?? '', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(2),
                Text(
                  '${a['subject']} · Grade ${a['grade']}${totalMarks != null ? ' · $totalMarks marks' : ''}',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          ChipTag(label: (a['status'] as String? ?? '').isEmpty ? 'draft' : a['status'] as String),
        ],
      ),
    );
  }

  /// Real, not gamified fluff: counts back from today (or yesterday, so a
  /// teacher who hasn't opened the app yet today doesn't see their streak
  /// drop to zero mid-morning) through consecutive calendar days that have
  /// at least one real audit_log entry -- an assessment created, a page
  /// scanned, a grade reviewed. Stops at the first gap.
  static int _currentStreak(List<Map<String, dynamic>> auditLog) {
    if (auditLog.isEmpty) return 0;
    final activeDays = auditLog
        .map((e) => DateTime.tryParse(e['timestamp'] as String? ?? ''))
        .whereType<DateTime>()
        .map((d) => DateTime(d.year, d.month, d.day))
        .toSet();
    var cursor = DateTime.now();
    cursor = DateTime(cursor.year, cursor.month, cursor.day);
    if (!activeDays.contains(cursor)) {
      cursor = cursor.subtract(const Duration(days: 1));
      if (!activeDays.contains(cursor)) return 0;
    }
    var streak = 0;
    while (activeDays.contains(cursor)) {
      streak++;
      cursor = cursor.subtract(const Duration(days: 1));
    }
    return streak;
  }

  static String _formatDate(DateTime d) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ];
    return '${days[d.weekday - 1]}, ${months[d.month - 1]} ${d.day}';
  }
}
