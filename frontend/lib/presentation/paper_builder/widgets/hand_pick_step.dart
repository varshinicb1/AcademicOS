import 'package:flutter/material.dart';

import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../paper_builder_controller.dart';
import 'class_subject_step.dart';

/// Step 3, hand-picked: the class's question bank, filtered by chapter, marks
/// and words, and the questions picked so far. The paper prints exactly
/// those questions (POST /papers/generate-from-ids), grouped into sections by
/// marks -- nothing added, nothing dropped (audit D57).
class HandPickStep extends StatefulWidget {
  final PaperBuilderController c;
  const HandPickStep({super.key, required this.c});

  @override
  State<HandPickStep> createState() => _HandPickStepState();
}

class _HandPickStepState extends State<HandPickStep> {
  final _search = TextEditingController();
  String? _chapter;
  int? _marks;
  List<BankItem>? _items;
  String? _error;
  bool _errorRetryable = false;
  bool _loading = false;
  int _ticket = 0;

  static const _marksChoices = [1, 2, 3, 4, 5];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final ticket = ++_ticket;
    setState(() {
      _loading = true;
      _error = null;
      _errorRetryable = false;
    });
    try {
      final c = widget.c;
      final items = await c.api.searchBank(
        subject: c.subject!,
        grade: c.grade!,
        marks: _marks,
        chapterIds: _chapter != null ? [_chapter!] : const [],
        keyword: _search.text,
      );
      if (!mounted || ticket != _ticket) return;
      setState(() => _items = items);
    } catch (e) {
      if (!mounted || ticket != _ticket) return;
      setState(() {
        _error = serverErrorMessage(e);
        _errorRetryable = isRetryable(e);
      });
    } finally {
      if (mounted && ticket == _ticket) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    final theme = Theme.of(context);
    final items = _items ?? const <BankItem>[];
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        ClassSubjectBanner(c: c),
        Row(children: [
          Icon(Icons.checklist, size: 20, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text('Pick the questions yourself', style: theme.textTheme.titleSmall)),
          TextButton(
            onPressed: () => c.goTo(BuilderStep.template),
            style: TextButton.styleFrom(minimumSize: const Size(64, 44)),
            child: const Text('Change'),
          ),
        ]),
        Text('The paper prints exactly the questions you pick, grouped into sections by marks.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const SizedBox(height: 12),
        _Picked(c: c),
        if (c.generateError != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text('Could not generate: ${c.generateError}',
                key: const ValueKey('hand-pick-error'), style: TextStyle(color: theme.colorScheme.error)),
          ),
        const SizedBox(height: 16),
        Text('The question bank', style: theme.textTheme.titleMedium),
        const SizedBox(height: 4),
        TextField(
          controller: _search,
          textInputAction: TextInputAction.search,
          decoration: InputDecoration(
            labelText: 'Search the question text',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: IconButton(tooltip: 'Search', icon: const Icon(Icons.arrow_forward), onPressed: _load),
          ),
          onSubmitted: (_) => _load(),
        ),
        if (c.chapters.isNotEmpty)
          DropdownButton<String?>(
            value: _chapter,
            isExpanded: true,
            items: [
              const DropdownMenuItem<String?>(value: null, child: Text('All chapters')),
              for (final ch in c.chapters)
                DropdownMenuItem<String?>(
                  value: ch.chapterId,
                  child: Text(ch.chapterName, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (v) {
              setState(() => _chapter = v);
              _load();
            },
          ),
        Wrap(spacing: 6, children: [
          ChoiceChip(
            label: const Text('Any marks'),
            selected: _marks == null,
            onSelected: (_) {
              setState(() => _marks = null);
              _load();
            },
          ),
          for (final m in _marksChoices)
            ChoiceChip(
              label: Text('$m mark${m == 1 ? '' : 's'}'),
              selected: _marks == m,
              onSelected: (_) {
                setState(() => _marks = m);
                _load();
              },
            ),
        ]),
        if (_loading) const Padding(padding: EdgeInsets.only(top: 8), child: LinearProgressIndicator()),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Could not search the bank: $_error', style: TextStyle(color: theme.colorScheme.error)),
              if (_errorRetryable)
                TextButton.icon(onPressed: _load, icon: const Icon(Icons.refresh), label: const Text('Try again')),
            ]),
          )
        else if (_items != null && items.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Text('No question matches. Clear the search, or choose another chapter or marks.'),
          )
        else
          for (final q in items) _BankTile(c: c, q: q),
      ],
    );
  }
}

/// The questions picked so far, with their total: what the paper will print.
class _Picked extends StatelessWidget {
  final PaperBuilderController c;
  const _Picked({required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(
          c.picked.isEmpty
              ? 'No question picked yet. Add them from the bank below.'
              : 'Your paper: ${c.picked.length} question${c.picked.length == 1 ? '' : 's'}, '
                  '${c.pickedMarks} mark${c.pickedMarks == 1 ? '' : 's'}',
          key: const ValueKey('hand-pick-total'),
          style: theme.textTheme.titleSmall,
        ),
        for (final (i, q) in c.picked.indexed)
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Padding(padding: const EdgeInsets.only(top: 12), child: Text('${i + 1}.')),
            const SizedBox(width: 6),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(q.stem, maxLines: 2, overflow: TextOverflow.ellipsis),
              ),
            ),
            Padding(padding: const EdgeInsets.only(top: 12), child: Text('[${q.marks}]')),
            IconButton(
              tooltip: 'Take off the paper',
              icon: const Icon(Icons.remove_circle_outline),
              onPressed: () => c.removePick(q.id),
            ),
          ]),
      ]),
    );
  }
}

class _BankTile extends StatelessWidget {
  final PaperBuilderController c;
  final BankItem q;
  const _BankTile({required this.c, required this.q});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final picked = c.isPicked(q.id);
    final status = picked
        ? 'On your paper'
        : q.hasAnswerKey
            ? 'Has answer key'
            : "No answer key -- can't be used";
    return ListTile(
      key: ValueKey('bank-${q.id}'),
      contentPadding: EdgeInsets.zero,
      minVerticalPadding: 10,
      enabled: q.hasAnswerKey,
      title: Text(q.stem, maxLines: 4, overflow: TextOverflow.ellipsis),
      subtitle: Text('${q.marks} mark${q.marks == 1 ? '' : 's'} · $status',
          style: TextStyle(color: q.hasAnswerKey ? null : theme.colorScheme.error)),
      trailing: !q.hasAnswerKey
          ? null
          : picked
              ? IconButton(
                  tooltip: 'Take off the paper',
                  icon: Icon(Icons.check_circle, color: theme.colorScheme.primary),
                  onPressed: () => c.removePick(q.id),
                )
              : IconButton(
                  tooltip: 'Add to the paper',
                  icon: const Icon(Icons.add_circle_outline),
                  onPressed: () => c.addPick(q),
                ),
      onTap: !q.hasAnswerKey ? null : () => picked ? c.removePick(q.id) : c.addPick(q),
    );
  }
}
