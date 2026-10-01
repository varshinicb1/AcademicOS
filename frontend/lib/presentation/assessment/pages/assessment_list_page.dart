import 'package:flutter/foundation.dart' show ValueListenable;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/wording.dart';
import '../../../core/session/current_session.dart';
import '../../../data/datasources/api/api_client.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';
import '../../paper_builder/pages/paper_builder_page.dart' show newPaperLocation;
import '../widgets/paper_actions.dart';
import 'package:academicos/core/theme/app_theme.dart';

/// The teacher's papers (the principal's: the school's), newest first as
/// the server sends them, each with its class, printed marks, author and
/// date.
class AssessmentListPage extends StatefulWidget {
  const AssessmentListPage({super.key});

  @override
  State<AssessmentListPage> createState() => _AssessmentListPageState();
}

class _AssessmentListPageState extends State<AssessmentListPage> {
  GoRouter? _router;

  /// Whether this list was the page on screen at the last route change.
  bool _shown = true;

  late final ValueListenable<Set<String>> _grants = myGrants();

  @override
  void initState() {
    super.initState();
    _grants.addListener(_grantsChanged);
    _reload();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final router = GoRouter.maybeOf(context);
    if (router != _router) {
      _router?.routerDelegate.removeListener(_routeChanged);
      _router = router;
      _router?.routerDelegate.addListener(_routeChanged);
    }
  }

  @override
  void dispose() {
    _router?.routerDelegate.removeListener(_routeChanged);
    _grants.removeListener(_grantsChanged);
    super.dispose();
  }

  void _grantsChanged() {
    if (mounted) setState(() {});
  }

  void _reload() =>
      context.read<AssessmentBloc>().add(AssessmentEvent.loadAssessmentsBySchool(CurrentSession.schoolId));

  /// The builder and a paper open above this page, which stays alive under
  /// them: it loaded once, so a paper saved in the builder was missing until
  /// a browser reload (QA P-06). It is read again whenever it is the page on
  /// screen once more -- back from the builder or a paper, or the sidebar.
  void _routeChanged() {
    // The top route, not the configuration's uri: a push (the builder, a
    // paper) leaves the uri at the page it was pushed from.
    final routes = _router?.routerDelegate.currentConfiguration;
    final shown = routes != null && routes.isNotEmpty && routes.last.matchedLocation == '/assessment';
    if (shown && !_shown && mounted) _reload();
    _shown = shown;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Papers'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            // On a phone these actions are thumb-sized (Task 801); an
            // IconButton keeps the minimum on a desktop density too (see
            // test/responsive/assessment_list_responsive_test.dart).
            style: IconButton.styleFrom(minimumSize: const Size(48, 48)),
            onPressed: _reload,
          ),
          // A word, not a bare icon: two icons with only tooltips sat beside
          // "New paper", and one of them was the same thing (QA P-14).
          Tooltip(
            message: 'Quick paper (CBSE pattern)',
            child: TextButton.icon(
              key: const ValueKey('quick-paper'),
              // A TextButton, unlike an IconButton, takes the theme's
              // density: a desktop browser's `compact` drew it 40 px tall.
              style: TextButton.styleFrom(minimumSize: const Size(48, 48), visualDensity: VisualDensity.standard),
              icon: const Icon(Icons.flash_on),
              label: const Text('Quick paper'),
              // Online, the quick paper is the builder on the class's CBSE
              // annual pattern (Task 902); the offline build keeps its dialog.
              onPressed: () => newPaperLocation(quick: true) == '/assessment/create'
                  ? _showQuickPaperDialog(context)
                  : context.push(newPaperLocation(quick: true)),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocBuilder<AssessmentBloc, AssessmentState>(
        builder: (context, state) {
          return state.maybeWhen(
            loading: () => const Center(child: CircularProgressIndicator()),
            assessmentsLoaded: (assessments) => RefreshIndicator(
              onRefresh: () async {
                final bloc = context.read<AssessmentBloc>();
                _reload();
                await bloc.stream.firstWhere((s) => s.maybeMap(loading: (_) => false, orElse: () => true));
              },
              child: _buildList(context, assessments),
            ),
            error: (message) => ErrorDisplay(message: message, onRetry: _reload),
            // Any other state (e.g. left over from the create flow) isn't a
            // list result — re-fetch rather than rendering a misleading empty list.
            orElse: () {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (mounted) _reload();
              });
              return const Center(child: CircularProgressIndicator());
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(newPaperLocation()),
        icon: const Icon(Icons.assignment_add),
        label: const Text('New paper'),
      ),
    );
  }

  Widget _buildList(BuildContext context, List<Assessment> assessments) {
    if (assessments.isEmpty) {
      // Scrollable, so pulling down to refresh works on an empty list too.
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: const [
          Padding(
            padding: EdgeInsets.fromLTRB(24, 120, 24, 24),
            child: Text('No papers yet. Start one with New paper.', textAlign: TextAlign.center),
          ),
        ],
      );
    }
    final theme = Theme.of(context);
    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
      itemCount: assessments.length,
      itemBuilder: (context, index) {
        final a = assessments[index];
        return AppCard(
          key: ValueKey('paper-${a.id}'),
          onTap: () => context.push('/assessment/${a.id}', extra: {'assessment': a}),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(a.title, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    // The printed total: 79 once a question is removed, not
                    // the template's 80 (QA P-16).
                    Text('${a.subject} · Class ${a.grade} · ${marksText(paperMarksOf(a))}',
                        style: theme.textTheme.bodySmall),
                    Text(paperByline(a),
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  ],
                ),
              ),
              ChipTag(label: a.status.label),
              _rowMenu(context, a),
            ],
          ),
        );
      },
    );
  }

  /// Rename and Delete on the row, for whoever may (QA P-07, P-09); the
  /// list is read again after either.
  Widget _rowMenu(BuildContext context, Assessment a) {
    final can = PaperPermissions.of(a, grants: _grants.value);
    final items = <PopupMenuEntry<String>>[
      if (paperIsEditable(a) && can.mayChange) const PopupMenuItem(value: 'rename', child: Text('Rename')),
      if (can.mayDelete) const PopupMenuItem(value: 'delete', child: Text('Delete')),
    ];
    if (items.isEmpty) return const SizedBox(width: 8);
    return PopupMenuButton<String>(
      tooltip: 'Actions for ${a.title}',
      itemBuilder: (_) => items,
      onSelected: (v) async {
        final changed = v == 'rename' ? await renamePaper(context, a) != null : await deletePaper(context, a);
        if (changed && mounted) _reload();
      },
    );
  }

  static List<String> _quickPaperSubjectsForGrade(int grade) {
    if (grade >= 11) {
      return const [
        'Physics',
        'Chemistry',
        'Biology',
        'Mathematics',
        'Accountancy',
        'Business Studies',
        'Economics',
        'History',
        'Political Science',
        'Geography',
        'English',
        'Hindi',
      ];
    }
    return const [
      'Science',
      'Mathematics',
      'Social Science',
      'English',
      'Hindi',
    ];
  }

  Future<void> _showQuickPaperDialog(BuildContext context) async {
    int selectedGrade = 10;
    String selectedSubject = 'Science';
    String selectedPreset = 'class_test';
    String selectedTier = 'standard';
    int setCount = 1;
    bool generating = false;
    String? dialogError;

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Row(
                children: [
                  Icon(Icons.flash_on, color: AppColors.warning),
                  SizedBox(width: 8),
                  Text('1-Click Quick Paper'),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Instantly compile a PARAKH / CBSE standard assessment with competency questions and parallel sets.',
                      style: TextStyle(fontSize: 13),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<int>(
                      value: selectedGrade,
                      decoration: const InputDecoration(labelText: 'Class'),
                      items: const [
                        DropdownMenuItem(value: 12, child: Text('Class 12')),
                        DropdownMenuItem(value: 11, child: Text('Class 11')),
                        DropdownMenuItem(value: 10, child: Text('Class 10')),
                        DropdownMenuItem(value: 9, child: Text('Class 9')),
                        DropdownMenuItem(value: 8, child: Text('Class 8')),
                        DropdownMenuItem(value: 7, child: Text('Class 7')),
                        DropdownMenuItem(value: 6, child: Text('Class 6')),
                      ],
                      onChanged: (v) => setDialogState(() {
                        selectedGrade = v!;
                        final validSubjects = _quickPaperSubjectsForGrade(selectedGrade);
                        if (!validSubjects.contains(selectedSubject)) {
                          selectedSubject = validSubjects.first;
                        }
                      }),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      key: ValueKey('quick_subject_${selectedGrade}_$selectedSubject'),
                      value: selectedSubject,
                      decoration: const InputDecoration(labelText: 'Subject'),
                      items: _quickPaperSubjectsForGrade(selectedGrade)
                          .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                          .toList(),
                      onChanged: (v) => setDialogState(() => selectedSubject = v!),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: selectedPreset,
                      decoration: const InputDecoration(labelText: 'Exam Format'),
                      items: const [
                        DropdownMenuItem(value: 'class_test', child: Text('Class Test (25 marks · 45m)')),
                        DropdownMenuItem(value: 'weekly_test', child: Text('Weekly Test (40 marks · 90m)')),
                        DropdownMenuItem(value: 'monthly_test', child: Text('Monthly Test (50 marks · 120m)')),
                        DropdownMenuItem(value: 'board', child: Text('Board Exam (80 marks · 180m)')),
                      ],
                      onChanged: (v) => setDialogState(() => selectedPreset = v!),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: selectedTier,
                      decoration: const InputDecoration(labelText: 'Student Differentiation Tier'),
                      items: const [
                        DropdownMenuItem(value: 'foundation', child: Text('Foundation / Remedial (Easy 55%)')),
                        DropdownMenuItem(value: 'standard', child: Text('Standard (Easy 30%, Medium 50%)')),
                        DropdownMenuItem(value: 'advanced', child: Text('Advanced / HOTS (Hard 40%)')),
                      ],
                      onChanged: (v) => setDialogState(() => selectedTier = v!),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<int>(
                      initialValue: setCount,
                      decoration: const InputDecoration(labelText: 'Parallel Sets (Invariant Difficulty)'),
                      items: const [
                        DropdownMenuItem(value: 1, child: Text('1 Set (Single Paper)')),
                        DropdownMenuItem(value: 2, child: Text('2 Sets (Set A & Set B)')),
                        DropdownMenuItem(value: 3, child: Text('3 Sets (Set A, B, C)')),
                      ],
                      onChanged: (v) => setDialogState(() => setCount = v!),
                    ),
                    if (dialogError != null) ...[
                      const SizedBox(height: 12),
                      Text(dialogError!, style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12)),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: generating ? null : () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton.icon(
                  onPressed: generating
                      ? null
                      : () async {
                          setDialogState(() {
                            generating = true;
                            dialogError = null;
                          });
                          try {
                            final totalMarks = switch (selectedPreset) {
                              'class_test' => 25,
                              'weekly_test' => 40,
                              'monthly_test' => 50,
                              'board' => 80,
                              _ => 40,
                            };
                            final req = QuickPaperRequest(
                              subject: selectedSubject,
                              grade: selectedGrade,
                              examType: selectedPreset,
                              tier: selectedTier,
                              totalMarks: totalMarks,
                              setCount: setCount,
                              title: '$selectedSubject ${selectedPreset.replaceAll('_', ' ').toUpperCase()} ($selectedTier)',
                            );
                            final result = await GetIt.I<ApiClient>().quickGenerateWithWarnings(req);
                            final paper = result.paper;
                            if (!dialogContext.mounted) return;
                            Navigator.of(dialogContext).pop();
                            if (!context.mounted) return;
                            // The warnings print above the paper on the review
                            // page: a short paper must say it is short.
                            context.push('/assessment/${paper.assessmentId}', extra: {
                              'paper': paper,
                              'warnings': result.warnings,
                            });
                          } catch (e) {
                            setDialogState(() {
                              generating = false;
                              dialogError = serverErrorMessage(e);
                            });
                          }
                        },
                  icon: generating
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.flash_on),
                  label: Text(generating ? 'Generating…' : 'Generate Paper'),
                ),
              ],
            );
          },
        );
      },
    );
  }
}
