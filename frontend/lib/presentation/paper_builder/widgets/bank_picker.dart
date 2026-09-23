import 'package:flutter/material.dart';

import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../paper_builder_controller.dart';

/// Opens the bank picker for one slot and returns the chosen question id,
/// or null if the teacher closed it.
Future<String?> showBankPicker(BuildContext context, PaperBuilderController c,
    {required String slot, required int marks}) {
  return showModalBottomSheet<String>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (_) => FractionallySizedBox(
      heightFactor: 0.9,
      child: BankPicker(c: c, slot: slot, marks: marks),
    ),
  );
}

/// The question bank, filtered to what fits one slot: same marks, the
/// paper's chapters by default. Each question shows whether it has a
/// verified answer key; one without cannot be picked (PRD rule Q1: no answer
/// key, no question), and one already on the paper is marked as such.
class BankPicker extends StatefulWidget {
  final PaperBuilderController c;
  final String slot;
  final int marks;
  const BankPicker({super.key, required this.c, required this.slot, required this.marks});

  @override
  State<BankPicker> createState() => _BankPickerState();
}

class _BankPickerState extends State<BankPicker> {
  final _search = TextEditingController();
  late String? _chapter = widget.c.chapterIds.length == 1 ? widget.c.chapterIds.first : null;
  List<BankItem>? _items;
  String? _error;
  bool _errorRetryable = false;
  bool _loading = false;
  int _ticket = 0;

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
        marks: widget.marks,
        chapterIds: _chapter != null ? [_chapter!] : c.chapterIds.toList(),
        keyword: _search.text,
      );
      if (!mounted || ticket != _ticket) return;
      setState(() => _items = items);
    } catch (e) {
      if (!mounted || ticket != _ticket) return;
      setState(() {
        _error = serverErrorMessage(e);
        // The same rule the rest of the builder follows: no "Try again" on a
        // 401/403/404, which answers the same way every time.
        _errorRetryable = isRetryable(e);
      });
    } finally {
      if (mounted && ticket == _ticket) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final onPaper = widget.c.onPaper;
    final items = _items ?? const <BankItem>[];
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('Pick question ${widget.slot.replaceAll('_OR', ' (OR)')} · ${widget.marks} marks',
                style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
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
            if (widget.c.chapters.isNotEmpty)
              DropdownButton<String?>(
                value: _chapter,
                isExpanded: true,
                items: [
                  DropdownMenuItem<String?>(
                    value: null,
                    child: Text(widget.c.chapterIds.isEmpty ? 'All chapters' : "This paper's chapters"),
                  ),
                  for (final ch in widget.c.chapters)
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
          ]),
        ),
        if (_loading) const LinearProgressIndicator(),
        Expanded(
          child: _error != null
              ? _message(context, 'Could not search the bank: $_error', retry: _errorRetryable)
              : _items == null
                  ? const SizedBox.shrink()
                  : items.isEmpty
                      ? _message(context,
                          'No ${widget.marks}-mark questions match. Clear the search or choose another chapter.')
                      : ListView.separated(
                          itemCount: items.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, i) => _tile(context, items[i], onPaper.contains(items[i].id)),
                        ),
        ),
      ]),
    );
  }

  Widget _tile(BuildContext context, BankItem q, bool alreadyOn) {
    final theme = Theme.of(context);
    final usable = q.hasAnswerKey && !alreadyOn;
    final status = alreadyOn
        ? 'Already on this paper'
        : q.hasAnswerKey
            ? 'Has answer key'
            : "No answer key -- can't be used";
    return ListTile(
      enabled: usable,
      minVerticalPadding: 10,
      title: Text(q.stem, maxLines: 4, overflow: TextOverflow.ellipsis),
      subtitle: Text('${q.marks} marks · $status',
          style: TextStyle(color: q.hasAnswerKey ? null : theme.colorScheme.error)),
      trailing: usable ? const Icon(Icons.add_circle_outline, semanticLabel: 'Use this question') : null,
      onTap: usable ? () => Navigator.of(context).pop(q.id) : null,
    );
  }

  Widget _message(BuildContext context, String text, {bool retry = false}) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(children: [
          Text(text, textAlign: TextAlign.center),
          if (retry) TextButton.icon(onPressed: _load, icon: const Icon(Icons.refresh), label: const Text('Try again')),
        ]),
      );
}
