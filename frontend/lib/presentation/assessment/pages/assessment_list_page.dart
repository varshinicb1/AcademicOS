import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../data/datasources/api/api_client.dart';
import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

class AssessmentListPage extends StatefulWidget {
  const AssessmentListPage({super.key});

  @override
  State<AssessmentListPage> createState() => _AssessmentListPageState();
}

class _AssessmentListPageState extends State<AssessmentListPage> {
  @override
  void initState() {
    super.initState();
    context.read<AssessmentBloc>().add(const AssessmentEvent.loadAssessmentsBySchool(AppConstants.currentSchoolId));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Assessments'),
        actions: [
          IconButton(
            tooltip: '1-Click Quick Paper',
            icon: const Icon(Icons.flash_on),
            onPressed: () => _showQuickPaperDialog(context),
          ),
          IconButton(
            tooltip: 'Create assessment',
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/assessment/create'),
          ),
        ],
      ),
      body: BlocBuilder<AssessmentBloc, AssessmentState>(
        builder: (context, state) {
          return state.maybeWhen(
            loading: () => const Center(child: CircularProgressIndicator()),
            assessmentsLoaded: (assessments) => _buildList(context, assessments),
            error: (message) => ErrorDisplay(
              message: message,
              onRetry: () => context
                  .read<AssessmentBloc>()
                  .add(const AssessmentEvent.loadAssessmentsBySchool(AppConstants.currentSchoolId)),
            ),
            // Any other state (e.g. left over from the create flow) isn't a
            // list result — re-fetch rather than rendering a misleading empty list.
            orElse: () {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (mounted) {
                  context
                      .read<AssessmentBloc>()
                      .add(const AssessmentEvent.loadAssessmentsBySchool(AppConstants.currentSchoolId));
                }
              });
              return const Center(child: CircularProgressIndicator());
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/assessment/create'),
        icon: const Icon(Icons.assignment_add),
        label: const Text('New Assessment'),
      ),
    );
  }

  Widget _buildList(BuildContext context, List<Assessment> assessments) {
    if (assessments.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'No assessments yet.\nTap "New Assessment" to build one with the AI Assessment Designer.',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: assessments.length,
      itemBuilder: (context, index) {
        final a = assessments[index];
        return AppCard(
          onTap: () => context.push('/assessment/${a.id}', extra: {'assessment': a}),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(a.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Text('${a.subject} · Grade ${a.grade} · ${a.blueprint.totalMarks} marks',
                        style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
              ChipTag(label: a.status.name),
            ],
          ),
        );
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
                  Icon(Icons.flash_on, color: Colors.amber),
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
                      decoration: const InputDecoration(labelText: 'Grade'),
                      items: const [
                        DropdownMenuItem(value: 12, child: Text('Grade 12')),
                        DropdownMenuItem(value: 11, child: Text('Grade 11')),
                        DropdownMenuItem(value: 10, child: Text('Grade 10')),
                        DropdownMenuItem(value: 9, child: Text('Grade 9')),
                        DropdownMenuItem(value: 8, child: Text('Grade 8')),
                        DropdownMenuItem(value: 7, child: Text('Grade 7')),
                        DropdownMenuItem(value: 6, child: Text('Grade 6')),
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
                            final paper = await GetIt.I<ApiClient>().quickGeneratePaper(req);
                            if (!dialogContext.mounted) return;
                            Navigator.of(dialogContext).pop();
                            if (!context.mounted) return;
                            context.push('/assessment/${paper.assessmentId}', extra: {
                              'paper': paper,
                            });
                          } catch (e) {
                            setDialogState(() {
                              generating = false;
                              dialogError = '$e';
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
