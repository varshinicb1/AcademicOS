import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Browse the real question bank: every question ingested from CBSE board
/// papers, filterable the way a teacher actually searches — subject, then
/// marks, then keyword.
class QuestionBankPage extends StatefulWidget {
  const QuestionBankPage({super.key});

  @override
  State<QuestionBankPage> createState() => _QuestionBankPageState();
}

class _QuestionBankPageState extends State<QuestionBankPage> {
  final _search = TextEditingController();

  List<CatalogEntry> _catalog = [];
  CatalogEntry? _selected;
  List<BankQuestion> _questions = [];
  int? _marksFilter;

  bool _loadingCatalog = true;
  bool _loadingQuestions = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadCatalog();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _loadCatalog() async {
    setState(() {
      _loadingCatalog = true;
      _error = null;
    });
    try {
      final c = await GetIt.I<PillarApi>().catalog();
      setState(() {
        _catalog = c.entries;
        _loadingCatalog = false;
        _selected = c.entries.isNotEmpty ? c.entries.first : null;
      });
      if (_selected != null) _loadQuestions();
    } catch (e) {
      setState(() {
        _error = '$e';
        _loadingCatalog = false;
      });
    }
  }

  Future<void> _loadQuestions() async {
    final sel = _selected;
    if (sel == null) return;
    setState(() {
      _loadingQuestions = true;
      _error = null;
    });
    try {
      final qs = await GetIt.I<PillarApi>().searchQuestions(
        subject: sel.subject,
        grade: sel.grade,
        keyword: _search.text.trim().isEmpty ? null : _search.text.trim(),
        minMarks: _marksFilter,
        maxMarks: _marksFilter,
        limit: 400,
      );
      setState(() {
        _questions = qs;
        _loadingQuestions = false;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _loadingQuestions = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Question Bank'),
        actions: [
          if (!_loadingCatalog)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Text(
                  '${_catalog.fold<int>(0, (s, e) => s + e.questionCount)} questions',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            ),
        ],
      ),
      body: _loadingCatalog
          ? const LoadingIndicator(message: 'Loading question bank…')
          : _error != null && _catalog.isEmpty
              ? ErrorDisplay(message: _error!, onRetry: _loadCatalog)
              : Column(
                  children: [
                    _subjectStrip(theme),
                    _filterBar(theme),
                    const Divider(height: 1),
                    Expanded(child: _questionList(theme)),
                  ],
                ),
    );
  }

  Widget _subjectStrip(ThemeData theme) {
    // Height must fit title + class + two stat lines + card padding; measured
    // rather than guessed, because an under-sized box paints Flutter's yellow
    // overflow stripes across the header.
    return SizedBox(
      height: 132,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
        itemCount: _catalog.length,
        separatorBuilder: (_, __) => const Gap(10),
        itemBuilder: (context, i) {
          final e = _catalog[i];
          final selected = _selected?.subject == e.subject && _selected?.grade == e.grade;
          return InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () {
              setState(() {
                _selected = e;
                _marksFilter = null;
              });
              _loadQuestions();
            },
            child: Container(
              width: 190,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: selected
                    ? theme.colorScheme.primaryContainer
                    : theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: selected
                      ? theme.colorScheme.primary
                      : theme.colorScheme.outlineVariant,
                  width: selected ? 1.6 : 1,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(e.subject,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w700)),
                  Text('Class ${e.grade}', style: theme.textTheme.bodySmall),
                  const Gap(4),
                  Text('${e.questionCount} questions',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  Text('${e.chapters} chapters',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _filterBar(ThemeData theme) {
    final marks = _selected?.marksAvailable ?? const <int>[];
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _search,
              onSubmitted: (_) => _loadQuestions(),
              decoration: InputDecoration(
                isDense: true,
                hintText: 'Search questions…',
                prefixIcon: const Icon(Icons.search, size: 20),
                suffixIcon: _search.text.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.clear, size: 18),
                        onPressed: () {
                          _search.clear();
                          _loadQuestions();
                        },
                      ),
                border: const OutlineInputBorder(),
              ),
            ),
          ),
          const Gap(12),
          Wrap(
            spacing: 6,
            children: [
              ChoiceChip(
                label: const Text('All'),
                selected: _marksFilter == null,
                onSelected: (_) {
                  setState(() => _marksFilter = null);
                  _loadQuestions();
                },
              ),
              for (final m in marks)
                ChoiceChip(
                  label: Text('${m}m'),
                  selected: _marksFilter == m,
                  onSelected: (_) {
                    setState(() => _marksFilter = m);
                    _loadQuestions();
                  },
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _questionList(ThemeData theme) {
    if (_loadingQuestions) {
      return const LoadingIndicator(message: 'Loading questions…');
    }
    if (_error != null) {
      return ErrorDisplay(message: _error!, onRetry: _loadQuestions);
    }
    if (_questions.isEmpty) {
      return const EmptyState(
        icon: Icons.search_off,
        title: 'No matching questions',
        message: 'Try a different subject, mark value, or search term.',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _questions.length,
      itemBuilder: (context, i) {
        final q = _questions[i];
        return AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  ChipTag(label: '${q.marks}m'),
                  const Gap(6),
                  ChipTag(label: q.difficulty, color: _difficultyColor(q.difficulty)),
                  const Gap(6),
                  ChipTag(label: q.bloomLevel),
                  const Spacer(),
                  Text('#${i + 1}',
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
              const Gap(10),
              SelectableText(q.stem, style: theme.textTheme.bodyMedium),
              if (q.chapterNames.isNotEmpty) ...[
                const Gap(10),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: q.chapterNames
                      .map((c) => ChipTag(label: c, color: theme.colorScheme.tertiary))
                      .toList(),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Color _difficultyColor(String d) => switch (d) {
        'easy' => Colors.green,
        'hard' => Colors.red,
        _ => Colors.orange,
      };
}
