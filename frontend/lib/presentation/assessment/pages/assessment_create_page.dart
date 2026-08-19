import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

const _scienceChapters = [
  'Chemical Reactions and Equations',
  'Acids, Bases and Salts',
  'Metals and Non-metals',
  'Carbon and its Compounds',
  'Life Processes',
  'Control and Coordination',
  'How do Organisms Reproduce',
  'Heredity',
  'Light – Reflection and Refraction',
  'The Human Eye and the Colourful World',
  'Electricity',
  'Magnetic Effects of Electric Current',
  'Our Environment',
];

const _defaultChapters = ['Chapter selection depends on subject — pick Science for the pilot question bank.'];

class AssessmentCreatePage extends StatefulWidget {
  const AssessmentCreatePage({super.key});

  @override
  State<AssessmentCreatePage> createState() => _AssessmentCreatePageState();
}

class _AssessmentCreatePageState extends State<AssessmentCreatePage> {
  final _formKey = GlobalKey<FormState>();
  int _currentStep = 0;
  bool _submitting = false;
  String? _submitError;
  final _titleController = TextEditingController(text: 'Class X Science Unit Test');
  int _selectedGrade = 10;
  String _selectedSubject = 'Science';
  final List<String> _selectedChapters = [];
  BlueprintRequest _blueprint = const BlueprintRequest(
    totalMarks: 40,
    durationMinutes: 90,
    difficulty: DifficultyDistribution(easy: 0.3, medium: 0.5, hard: 0.2),
    bloom: BloomDistribution(remember: 0.2, understand: 0.25, apply: 0.3, analyze: 0.15, evaluate: 0.05, create: 0.05),
    chapterWeights: ChapterWeights(weights: {}),
    competencyWeights: CompetencyWeights(weights: {}),
    sections: [],
  );

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Create Assessment'),
      ),
      body: Stepper(
        currentStep: _currentStep,
        onStepContinue: _nextStep,
        onStepCancel: _previousStep,
        onStepTapped: (i) => setState(() => _currentStep = i),
        controlsBuilder: (context, details) {
          // Last step has its own "Create Assessment" action button.
          if (_currentStep == 4) {
            return _currentStep > 0
                ? Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: OutlinedButton(onPressed: _previousStep, child: const Text('Back')),
                  )
                : const SizedBox.shrink();
          }
          return Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Row(
              children: [
                FilledButton(onPressed: _nextStep, child: const Text('Next')),
                const SizedBox(width: 12),
                if (_currentStep > 0)
                  OutlinedButton(onPressed: _previousStep, child: const Text('Back')),
              ],
            ),
          );
        },
        steps: [
          _buildStep1BasicInfo(),
          _buildStep2Blueprint(),
          _buildStep3ChapterSelection(),
          _buildStep4QuestionSelection(),
          _buildStep5ReviewGenerate(),
        ],
      ),
    );
  }

  Step _buildStep1BasicInfo() {
    return Step(
      title: const Text('Basic Information'),
      subtitle: const Text('Assessment title, subject, grade'),
      content: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(labelText: 'Assessment Title *', hintText: 'e.g., Term 1 Science Exam'),
              validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<int>(
                    initialValue: _selectedGrade,
                    decoration: const InputDecoration(labelText: 'Grade *'),
                    items: List.generate(12, (i) => i + 1).map((g) => DropdownMenuItem(value: g, child: Text('Grade $g'))).toList(),
                    onChanged: (v) => setState(() => _selectedGrade = v!),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _selectedSubject,
                    decoration: const InputDecoration(labelText: 'Subject *'),
                    items: ['Science', 'Mathematics', 'English', 'Hindi', 'Social Science', 'Sanskrit', 'Computer Science']
                        .map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                    onChanged: (v) => setState(() {
                      _selectedSubject = v!;
                      _selectedChapters.clear();
                    }),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (_selectedSubject != 'Science')
              Text(
                'Only Class X Science has real questions ingested for this pilot.',
                style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12),
              ),
          ],
        ),
      ),
      isActive: _currentStep >= 0,
    );
  }

  Step _buildStep2Blueprint() {
    return Step(
      title: const Text('Blueprint'),
      subtitle: const Text('Marks, duration, difficulty, Bloom distribution'),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  initialValue: _blueprint.totalMarks.toString(),
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Total Marks'),
                  onChanged: (v) => setState(() => _blueprint = _blueprint.copyWith(totalMarks: int.tryParse(v) ?? 80)),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextFormField(
                  initialValue: _blueprint.durationMinutes.toString(),
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Duration (minutes)'),
                  onChanged: (v) => setState(() => _blueprint = _blueprint.copyWith(durationMinutes: int.tryParse(v) ?? 180)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text('Difficulty Distribution', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          _buildDistributionSliders(
            'Easy', _blueprint.difficulty.easy,
            'Medium', _blueprint.difficulty.medium,
            'Hard', _blueprint.difficulty.hard,
            (e, m, h) => setState(() => _blueprint = _blueprint.copyWith(difficulty: DifficultyDistribution(easy: e, medium: m, hard: h))),
          ),
          const SizedBox(height: 16),
          Text('Bloom\'s Taxonomy Distribution', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          _buildBloomSliders(),
        ],
      ),
    );
  }

  Widget _buildDistributionSliders(String l1, double v1, String l2, double v2, String l3, double v3, Function(double, double, double) onChange) {
    double v1Local = v1, v2Local = v2, v3Local = v3;
    return Column(
      children: [
        _buildSliderRow(l1, v1Local, (v) { v1Local = v; onChange(v1Local, v2Local, v3Local); }),
        _buildSliderRow(l2, v2Local, (v) { v2Local = v; onChange(v1Local, v2Local, v3Local); }),
        _buildSliderRow(l3, v3Local, (v) { v3Local = v; onChange(v1Local, v2Local, v3Local); }),
        Text('Sum: ${(v1Local + v2Local + v3Local).toStringAsFixed(2)}', style: TextStyle(color: (v1Local + v2Local + v3Local - 1.0).abs() < 0.01 ? Colors.green : Colors.red)),
      ],
    );
  }

  Widget _buildSliderRow(String label, double value, Function(double) onChanged) {
    return Row(
      children: [
        SizedBox(width: 60, child: Text(label, style: const TextStyle(fontWeight: FontWeight.w500))),
        Expanded(child: Slider(value: value, min: 0, max: 1, divisions: 20, label: '${(value * 100).round()}%', onChanged: onChanged)),
        SizedBox(width: 50, child: Text('${(value * 100).round()}%', textAlign: TextAlign.end)),
      ],
    );
  }

  Widget _buildBloomSliders() {
    final levels = [
      ('Remember', _blueprint.bloom.remember, Colors.grey),
      ('Understand', _blueprint.bloom.understand, Colors.blue),
      ('Apply', _blueprint.bloom.apply, Colors.green),
      ('Analyze', _blueprint.bloom.analyze, Colors.orange),
      ('Evaluate', _blueprint.bloom.evaluate, Colors.purple),
      ('Create', _blueprint.bloom.create, Colors.red),
    ];
    return Column(
      children: levels.map((l) {
        return _buildSliderRow(l.$1, l.$2, (v) {
          setState(() {
            final b = _blueprint.bloom;
            final sum = b.remember + b.understand + b.apply + b.analyze + b.evaluate + b.create - l.$2 + v;
            if (sum > 1.0) return;
            _blueprint = _blueprint.copyWith(bloom: switch (l.$1) {
              'Remember' => b.copyWith(remember: v),
              'Understand' => b.copyWith(understand: v),
              'Apply' => b.copyWith(apply: v),
              'Analyze' => b.copyWith(analyze: v),
              'Evaluate' => b.copyWith(evaluate: v),
              'Create' => b.copyWith(create: v),
              _ => b,
            });
          });
        });
      }).toList(),
    );
  }

  Step _buildStep3ChapterSelection() {
    final chapters = _selectedSubject == 'Science' ? _scienceChapters : _defaultChapters;
    return Step(
      title: const Text('Chapters'),
      subtitle: const Text('Select chapters to include (leave empty to draw from all chapters)'),
      content: Column(
        children: chapters.map((c) => CheckboxListTile(
          title: Text(c),
          value: _selectedChapters.contains(c),
          onChanged: _selectedSubject == 'Science'
              ? (v) => setState(() => v! ? _selectedChapters.add(c) : _selectedChapters.remove(c))
              : null,
        )).toList(),
      ),
    );
  }

  Step _buildStep4QuestionSelection() {
    return Step(
      title: const Text('AI Question Selection'),
      subtitle: const Text('AI will select optimal questions matching your blueprint'),
      content: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('When you create the assessment, AssessmentOS will:', style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 8),
            ...[
              'Search the question bank for matching questions',
              'Filter and rank by blueprint match (difficulty, Bloom, marks)',
              'Fill each section, avoiding duplicate chapters where possible',
              'Flag any sections it could not fully fill',
              'Generate a formatted, sectioned paper',
            ].map((s) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(children: [const Icon(Icons.check_circle, size: 16, color: Colors.green), const SizedBox(width: 8), Expanded(child: Text(s))]),
            )),
          ],
        ),
      ),
    );
  }

  Step _buildStep5ReviewGenerate() {
    return Step(
      title: const Text('Review & Generate'),
      subtitle: const Text('Review your assessment and generate the paper'),
      content: Column(
        children: [
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Review Summary', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                _buildSummaryRow('Title', _titleController.text),
                _buildSummaryRow('Grade', 'Grade $_selectedGrade'),
                _buildSummaryRow('Subject', _selectedSubject),
                _buildSummaryRow('Chapters', _selectedChapters.isEmpty ? 'All chapters' : _selectedChapters.join(', ')),
                _buildSummaryRow('Total Marks', _blueprint.totalMarks.toString()),
                _buildSummaryRow('Duration', '${_blueprint.durationMinutes} minutes'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (_submitError != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(_submitError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          FilledButton.icon(
            onPressed: _submitting ? null : _createAssessment,
            icon: _submitting
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.assignment_add),
            label: Text(_submitting ? 'Generating…' : 'Create Assessment'),
            style: FilledButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text('$label: ', style: TextStyle(fontWeight: FontWeight.w500, color: Theme.of(context).colorScheme.onSurfaceVariant)),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }

  void _nextStep() {
    if (_currentStep < 4) setState(() => _currentStep++);
  }

  void _previousStep() {
    if (_currentStep > 0) setState(() => _currentStep--);
  }

  /// Waits for the next terminal (non-loading) state emitted by the bloc.
  Future<AssessmentState> _nextResult(AssessmentBloc bloc) {
    return bloc.stream.firstWhere(
      (s) => !s.maybeMap(loading: (_) => true, orElse: () => false),
    );
  }

  Future<void> _createAssessment() async {
    setState(() {
      _submitting = true;
      _submitError = null;
    });
    final bloc = context.read<AssessmentBloc>();
    const teacherId = 'teacher_1';
    const schoolId = 'school_1';

    try {
      bloc.add(AssessmentEvent.createAssessment(CreateAssessmentRequest(
        teacherId: teacherId,
        schoolId: schoolId,
        title: _titleController.text,
        subject: _selectedSubject,
        grade: _selectedGrade,
        chapterIds: _selectedChapters,
        blueprint: _blueprint,
      )));
      final created = await _nextResult(bloc);
      final assessment = created.mapOrNull(assessmentCreated: (s) => s.assessment);
      if (assessment == null) {
        throw Exception(created.mapOrNull(error: (s) => s.message) ?? 'Failed to create assessment');
      }

      bloc.add(AssessmentEvent.selectQuestions(
        blueprint: assessment.blueprint,
        params: QuestionSearchParams(
          subject: assessment.subject,
          grade: assessment.grade,
          chapterIds: _selectedChapters.isEmpty ? null : assessment.chapterIds,
          limit: 200,
        ),
      ));
      final optimized = await _nextResult(bloc);
      final optResult = optimized.mapOrNull(questionsSelected: (s) => s.result);
      if (optResult == null) {
        throw Exception(optimized.mapOrNull(error: (s) => s.message) ?? 'Failed to select questions');
      }

      bloc.add(AssessmentEvent.generatePaper(
        assessmentId: assessment.id,
        blueprint: assessment.blueprint,
        questions: optResult.selectedQuestions,
        schoolId: schoolId,
      ));
      final paperState = await _nextResult(bloc);
      final paper = paperState.mapOrNull(paperGenerated: (s) => s.paper);
      if (paper == null) {
        throw Exception(paperState.mapOrNull(error: (s) => s.message) ?? 'Failed to generate paper');
      }

      if (!mounted) return;
      context.go('/assessment/${assessment.id}', extra: {
        'assessment': assessment.copyWith(status: AssessmentStatus.paperGenerated, generatedPaperId: paper.id),
        'paper': paper,
        'gaps': optResult.gaps,
        'warnings': optResult.warnings,
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _submitError = e.toString();
        _submitting = false;
      });
    }
  }
}
