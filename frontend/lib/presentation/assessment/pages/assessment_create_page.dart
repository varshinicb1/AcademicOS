import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/local_engine/paper_selection.dart' show sectionsFromCounts;
import '../../../domain/entities/entities.dart';
import '../../../domain/repositories/requests.dart';
import '../../../data/datasources/api/curriculum_api.dart';
import '../../../data/datasources/api/pillar_api.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

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

  // Real school request during the pilot: control exactly how many 1m/2m/
  // 3m/4m/5m questions appear, not just a total-marks + difficulty slider
  // that auto-derives a proportional split. Off by default (existing
  // auto-generated layout, unchanged); switching this on replaces
  // _blueprint.sections with an explicit count-per-mark-value layout via
  // sectionsFromCounts, which the same real selection/generation engine
  // (paper_selection.dart, and its Python mirror) already knows how to
  // honor -- this is a UI gap, not a missing backend feature.
  bool _customQuestionMix = false;
  final Map<int, int> _markCounts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
  String _selectedExamPreset = 'class_test';
  String _selectedTier = 'standard';
  int _setCount = 1;

  int get _customMixTotalMarks => _markCounts.entries.fold(0, (sum, e) => sum + e.key * e.value);

  void _applyCustomMix() {
    final sections = sectionsFromCounts(_markCounts);
    setState(() => _blueprint = _blueprint.copyWith(
          sections: sections,
          totalMarks: _customMixTotalMarks,
        ));
  }

  void _onSelectExamPreset(String preset) {
    setState(() {
      _selectedExamPreset = preset;
      switch (preset) {
        case 'class_test':
          _blueprint = _blueprint.copyWith(
            totalMarks: 25,
            durationMinutes: 45,
            examType: 'class_test',
          );
          break;
        case 'weekly_test':
          _blueprint = _blueprint.copyWith(
            totalMarks: 40,
            durationMinutes: 90,
            examType: 'weekly_test',
          );
          break;
        case 'monthly_test':
          _blueprint = _blueprint.copyWith(
            totalMarks: 50,
            durationMinutes: 120,
            examType: 'monthly_test',
          );
          break;
        case 'board':
          _blueprint = _blueprint.copyWith(
            totalMarks: 80,
            durationMinutes: 180,
            examType: 'board',
          );
          break;
      }
    });
  }

  void _onSelectTier(String tier) {
    setState(() {
      _selectedTier = tier;
      switch (tier) {
        case 'foundation':
          _blueprint = _blueprint.copyWith(
            difficulty: const DifficultyDistribution(easy: 0.55, medium: 0.35, hard: 0.10),
            tier: 'foundation',
          );
          break;
        case 'standard':
          _blueprint = _blueprint.copyWith(
            difficulty: const DifficultyDistribution(easy: 0.30, medium: 0.50, hard: 0.20),
            tier: 'standard',
          );
          break;
        case 'advanced':
          _blueprint = _blueprint.copyWith(
            difficulty: const DifficultyDistribution(easy: 0.15, medium: 0.45, hard: 0.40),
            tier: 'advanced',
          );
          break;
      }
    });
  }

  // Real bug fix: the chapter list used to be a hardcoded, Science-only
  // list of DISPLAY NAMES ("Chemical Reactions and Equations") passed
  // straight through as chapterIds -- but the real corpus keys chapters by
  // slug ("chemical-reactions-equations"), so even selecting a Science
  // "chapter" matched zero real questions, and every other subject showed
  // one disabled placeholder checkbox reading "Chapter selection depends on
  // subject -- pick Science for the pilot question bank." (a real user hit
  // exactly this: selecting a chapter for a non-Science subject dead-ended).
  // Chapters are now loaded for real, the same way syllabus_page.dart does,
  // for every subject the corpus actually has data for.
  List<ChapterEntry> _chapters = [];
  bool _chaptersLoading = false;
  String? _chaptersError;

  // §21's subtopic-level filter: optional, narrows question search below
  // whole-chapter granularity to specific admin-approved Subtopics
  // (backend already supports this via QuestionSearchParams.subtopicIds --
  // this was the missing frontend half). Cached per chapter id so
  // re-expanding the picker doesn't re-fetch chapters already loaded.
  final Map<String, List<TopicWithSubtopics>> _topicsByChapter = {};
  final Set<String> _loadingTopicsForChapter = {};
  final Set<String> _selectedSubtopics = {};

  @override
  void initState() {
    super.initState();
    _loadChapters();
  }

  Future<void> _loadChapters() async {
    setState(() {
      _chaptersLoading = true;
      _chaptersError = null;
    });
    try {
      final chapters = await GetIt.I<PillarApi>().chapters(_selectedSubject, _selectedGrade);
      if (!mounted) return;
      setState(() {
        _chapters = chapters;
        _chaptersLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _chaptersError = '$e';
        _chaptersLoading = false;
      });
    }
  }

  Future<void> _loadTopicsForChapter(String chapterId) async {
    if (_topicsByChapter.containsKey(chapterId) || _loadingTopicsForChapter.contains(chapterId)) return;
    setState(() => _loadingTopicsForChapter.add(chapterId));
    try {
      final topics = await GetIt.I<CurriculumApi>().topicsForChapter(chapterId);
      if (!mounted) return;
      setState(() {
        _topicsByChapter[chapterId] = topics;
        _loadingTopicsForChapter.remove(chapterId);
      });
    } catch (e) {
      if (!mounted) return;
      // Honest empty state, not a blocking error -- a chapter with no
      // Topic/Subtopic content yet (extraction not run) is a real, common
      // case, and this filter is optional; the chapter-level checkbox
      // above still works regardless.
      setState(() {
        _topicsByChapter[chapterId] = [];
        _loadingTopicsForChapter.remove(chapterId);
      });
    }
  }

  /// Any subtopic belonging to a chapter that's no longer selected must be
  /// dropped too -- otherwise a stale subtopicId from a deselected chapter
  /// would silently keep narrowing the search.
  void _pruneSubtopicsForDeselectedChapters() {
    final validIds = <String>{
      for (final chapterId in _selectedChapters)
        ...?_topicsByChapter[chapterId]?.expand((t) => t.subtopics).map((s) => s.id),
    };
    _selectedSubtopics.removeWhere((id) => !validIds.contains(id));
  }

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

  static List<String> subjectsForGrade(int grade) {
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
        'Computer Science',
      ];
    }
    return const [
      'Science',
      'Mathematics',
      'Social Science',
      'English',
      'Hindi',
      'Sanskrit',
      'Computer Science',
    ];
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
                    value: _selectedGrade,
                    decoration: const InputDecoration(labelText: 'Grade *'),
                    items: List.generate(12, (i) => i + 1).map((g) => DropdownMenuItem(value: g, child: Text('Grade $g'))).toList(),
                    onChanged: (v) {
                      if (v == null) return;
                      setState(() {
                        _selectedGrade = v;
                        final available = subjectsForGrade(_selectedGrade);
                        if (!available.contains(_selectedSubject)) {
                          _selectedSubject = available.first;
                        }
                        _selectedChapters.clear();
                        _selectedSubtopics.clear();
                        _loadChapters();
                      });
                    },
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: ValueKey('subject_dropdown_${_selectedGrade}_$_selectedSubject'),
                    value: _selectedSubject,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Subject *'),
                    items: subjectsForGrade(_selectedGrade)
                        .map((s) => DropdownMenuItem(value: s, child: Text(s, overflow: TextOverflow.ellipsis))).toList(),
                    onChanged: (v) => setState(() {
                      _selectedSubject = v!;
                      _selectedChapters.clear();
                      _selectedSubtopics.clear();
                      _loadChapters();
                    }),
                  ),
                ),
              ],
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
          Text('Exam Preset', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'class_test', label: Text('Class (25m)')),
                ButtonSegment(value: 'weekly_test', label: Text('Weekly (40m)')),
                ButtonSegment(value: 'monthly_test', label: Text('Monthly (50m)')),
                ButtonSegment(value: 'board', label: Text('Board (80m)')),
              ],
              selected: {_selectedExamPreset},
              onSelectionChanged: (s) => _onSelectExamPreset(s.first),
            ),
          ),
          const SizedBox(height: 16),
          Text('Student Tier (PARAKH Differentiation)', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'foundation', label: Text('Foundation')),
                ButtonSegment(value: 'standard', label: Text('Standard')),
                ButtonSegment(value: 'advanced', label: Text('Advanced / HOTS')),
              ],
              selected: {_selectedTier},
              onSelectionChanged: (s) => _onSelectTier(s.first),
            ),
          ),
          const SizedBox(height: 16),
          Text('Parallel Question Sets', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text('Generates invariant parallel sets with rotated MCQs and swapped OR choices.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 8),
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 1, label: Text('1 Set (A)')),
              ButtonSegment(value: 2, label: Text('2 Sets (A, B)')),
              ButtonSegment(value: 3, label: Text('3 Sets (A, B, C)')),
            ],
            selected: {_setCount},
            onSelectionChanged: (s) => setState(() => _setCount = s.first),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  key: ValueKey('totalMarks-$_customQuestionMix-${_blueprint.totalMarks}'),
                  initialValue: _blueprint.totalMarks.toString(),
                  enabled: !_customQuestionMix,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'Total Marks',
                    helperText: _customQuestionMix ? 'Derived from the question mix below' : null,
                  ),
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
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Custom question mix'),
            subtitle: const Text('Set exact counts of 1/2/3/4/5-mark questions instead of an auto-derived split'),
            value: _customQuestionMix,
            onChanged: (v) {
              setState(() => _customQuestionMix = v);
              if (v) _applyCustomMix();
            },
          ),
          if (_customQuestionMix) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                for (final marks in const [1, 2, 3, 4, 5])
                  SizedBox(
                    width: 110,
                    child: TextFormField(
                      initialValue: _markCounts[marks].toString(),
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(labelText: '$marks-mark Qs'),
                      onChanged: (v) {
                        _markCounts[marks] = int.tryParse(v) ?? 0;
                        _applyCustomMix();
                      },
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '${_blueprint.sections.fold<int>(0, (s, sec) => s + sec.questionCount)} questions · '
              '$_customMixTotalMarks marks total',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
          ],
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

  /// Shows real chapter names in the review summary rather than the raw
  /// chapterId slugs stored in _selectedChapters (readable for the teacher
  /// reviewing before generating; the request itself still sends real ids).
  String _selectedChapterNames() {
    final byId = {for (final c in _chapters) c.chapterId: c.chapterName};
    return _selectedChapters.map((id) => byId[id] ?? id).join(', ');
  }

  Step _buildStep3ChapterSelection() {
    return Step(
      title: const Text('Chapters'),
      subtitle: const Text('Select chapters to include (leave empty to draw from all chapters)'),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [_buildChapterListContent(), _buildSubtopicFilter()],
      ),
    );
  }

  Widget _buildChapterListContent() {
    return _chaptersLoading
          ? const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(child: CircularProgressIndicator()),
            )
          : _chaptersError != null
              ? Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Could not load chapters: $_chaptersError',
                          style: TextStyle(color: Theme.of(context).colorScheme.error)),
                      const SizedBox(height: 8),
                      OutlinedButton.icon(
                        onPressed: _loadChapters,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _chapters.isEmpty
                  ? Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: Text(
                        'No chapters found for $_selectedSubject Grade $_selectedGrade in the bundled '
                        'question bank yet. You can still continue -- leaving chapters empty draws '
                        'from every question available for this subject and grade.',
                        style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
                      ),
                    )
                  : Column(
                      children: _chapters.map((c) => CheckboxListTile(
                        title: Text(c.chapterName),
                        subtitle: Text('${c.questionCount} question${c.questionCount == 1 ? '' : 's'} available'),
                        value: _selectedChapters.contains(c.chapterId),
                        onChanged: (v) => setState(() {
                          if (v!) {
                            _selectedChapters.add(c.chapterId);
                          } else {
                            _selectedChapters.remove(c.chapterId);
                            _pruneSubtopicsForDeselectedChapters();
                          }
                        }),
                      )).toList(),
                    );
  }

  Widget _buildSubtopicFilter() {
    if (_selectedChapters.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: ExpansionTile(
        title: const Text('Filter by subtopic (optional)'),
        subtitle: Text(_selectedSubtopics.isEmpty
            ? 'Leave empty to draw from the whole chapter'
            : '${_selectedSubtopics.length} subtopic${_selectedSubtopics.length == 1 ? '' : 's'} selected'),
        onExpansionChanged: (expanded) {
          if (expanded) {
            for (final chapterId in _selectedChapters) {
              _loadTopicsForChapter(chapterId);
            }
          }
        },
        children: _selectedChapters.map((chapterId) {
          final chapterName = _chapters.firstWhere(
            (c) => c.chapterId == chapterId,
            orElse: () => ChapterEntry.fromJson({'chapterId': chapterId, 'chapterName': chapterId}),
          ).chapterName;
          if (_loadingTopicsForChapter.contains(chapterId)) {
            return const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          final topics = _topicsByChapter[chapterId];
          if (topics == null) return const SizedBox.shrink();
          if (topics.isEmpty) {
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text('$chapterName: no subtopic breakdown available yet',
                  style: Theme.of(context).textTheme.bodySmall),
            );
          }
          return Padding(
            padding: const EdgeInsets.only(left: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(8, 8, 8, 0),
                  child: Text(chapterName, style: Theme.of(context).textTheme.labelLarge),
                ),
                for (final topic in topics)
                  ...topic.subtopics.map((s) => CheckboxListTile(
                        dense: true,
                        contentPadding: const EdgeInsets.only(left: 24, right: 16),
                        title: Text(s.name),
                        subtitle: Text(topic.name, style: Theme.of(context).textTheme.bodySmall),
                        value: _selectedSubtopics.contains(s.id),
                        onChanged: (v) => setState(
                            () => v! ? _selectedSubtopics.add(s.id) : _selectedSubtopics.remove(s.id)),
                      )),
              ],
            ),
          );
        }).toList(),
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
                _buildSummaryRow('Chapters', _selectedChapters.isEmpty ? 'All chapters' : _selectedChapterNames()),
                if (_selectedSubtopics.isNotEmpty)
                  _buildSummaryRow('Subtopics', '${_selectedSubtopics.length} selected'),
                _buildSummaryRow('Format Preset', _selectedExamPreset.replaceAll('_', ' ').toUpperCase()),
                _buildSummaryRow('Student Tier', _selectedTier.toUpperCase()),
                _buildSummaryRow('Parallel Sets', '$_setCount Set${_setCount > 1 ? "s" : ""}'),
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
    const schoolId = AppConstants.currentSchoolId;

    try {
      bloc.add(AssessmentEvent.createAssessment(CreateAssessmentRequest(
        teacherId: teacherId,
        schoolId: schoolId,
        title: _titleController.text,
        subject: _selectedSubject,
        grade: _selectedGrade,
        chapterIds: _selectedChapters,
        blueprint: _blueprint.copyWith(
          tier: _selectedTier,
          examType: _selectedExamPreset,
        ),
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
          subtopicIds: _selectedSubtopics.isEmpty ? null : _selectedSubtopics.toList(),
          limit: 200,
        ),
      ));
      final optimized = await _nextResult(bloc);
      final optResult = optimized.mapOrNull(questionsSelected: (s) => s.result);
      if (optResult == null) {
        throw Exception(optimized.mapOrNull(error: (s) => s.message) ?? 'Failed to select questions');
      }
      // Real bug this closes: generating anyway with zero real questions
      // produced a paper with every section showing "(0 marks)" -- signed
      // off as a real generated paper with nothing in it. The corpus's
      // subject coverage is genuinely uneven (heavily Science/Math-weighted),
      // so a thin subject+grade+chapter combination legitimately returns no
      // matches -- refuse and say why, don't silently hand back a worthless
      // paper. Same fix already shipped on the backend for the same bug.
      if (optResult.selectedQuestions.isEmpty) {
        throw Exception(
            'No questions found for $_selectedSubject Grade $_selectedGrade with the selected chapters. '
            'Try widening the chapter selection or a different subject/grade -- '
            'this subject may have thin coverage in the bundled corpus.');
      }

      bloc.add(AssessmentEvent.generatePaper(
        assessmentId: assessment.id,
        blueprint: assessment.blueprint,
        questions: optResult.selectedQuestions,
        schoolId: schoolId,
        setCount: _setCount,
        tier: _selectedTier,
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
