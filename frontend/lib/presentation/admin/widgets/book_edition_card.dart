import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// The "Book editions" card on the principal's Roster tab: for each subject of
/// a grade, which book (edition) the school teaches this year, and a way to
/// add another.
///
/// PRD 12.7 (decided 2026-09-18): "Book edition: one per subject per year,
/// chosen by the school." Before this card the web admin had no book picker
/// and silently used books.first.id -- the row SQLite returned first. The
/// server holds the choice (GET/PUT /subjects/{id}/selected-book); this card
/// only shows and changes it. Choosing a new edition does not move lessons
/// already scheduled from the old one; the server's warning is shown as-is.
class BookEditionCard extends StatefulWidget {
  final List<GradeSummary> grades;
  final void Function(String message) onMessage;

  const BookEditionCard({super.key, required this.grades, required this.onMessage});

  @override
  State<BookEditionCard> createState() => _BookEditionCardState();
}

class _BookEditionCardState extends State<BookEditionCard> {
  String? _gradeId;
  List<SubjectSummary> _subjects = [];
  final Map<String, List<BookSummary>> _books = {};
  final Set<String> _saving = {};
  // Bumped on every reload of a subject's books; part of its dropdown's key.
  final Map<String, int> _reloads = {};
  bool _loading = false;
  String? _error;

  CurriculumApi get _api => GetIt.I<CurriculumApi>();

  Future<void> _onGradeChanged(String? gradeId) async {
    setState(() {
      _gradeId = gradeId;
      _subjects = [];
      _books.clear();
      _error = null;
    });
    if (gradeId == null) return;
    setState(() => _loading = true);
    try {
      final subjects = await _api.subjects(gradeId);
      final books = await Future.wait(subjects.map((s) => _api.books(s.id)));
      if (!mounted || _gradeId != gradeId) return;
      setState(() {
        _subjects = subjects;
        for (var i = 0; i < subjects.length; i++) {
          _books[subjects[i].id] = books[i];
        }
      });
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load books: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _reloadBooks(String subjectId) async {
    final books = await _api.books(subjectId);
    if (!mounted) return;
    setState(() {
      _books[subjectId] = books;
      _reloads[subjectId] = (_reloads[subjectId] ?? 0) + 1;
    });
  }

  /// Re-keys the subject's dropdown so it re-reads `initialValue` from the
  /// books already held, without asking the server for anything. After a
  /// refused choice the menu otherwise keeps showing the book the server did
  /// not accept.
  void _rekeyPicker(String subjectId) {
    if (!mounted) return;
    setState(() => _reloads[subjectId] = (_reloads[subjectId] ?? 0) + 1);
  }

  Future<void> _select(SubjectSummary subject, String? bookId) async {
    if (bookId == null) return;
    final current = _books[subject.id]?.where((b) => b.selected).firstOrNull;
    if (current?.id == bookId) return;
    setState(() => _saving.add(subject.id));
    try {
      final BookSelectionResult res;
      try {
        res = await _api.selectBook(subject.id, bookId);
      } catch (e) {
        var message = 'Could not choose the book: ${serverErrorMessage(e)}';
        // The write did not land. Put the server's own answer back in the
        // dropdown from the list already in hand -- the refresh below throws
        // for the same reason the PUT did, and used to escape this Future
        // (nothing awaits it), leaving the refused book on screen.
        _rekeyPicker(subject.id);
        try {
          await _reloadBooks(subject.id);
        } catch (e2) {
          // Usually the same reason as the refusal above, but not always (a
          // refused PUT and a dropped connection on the reload are different
          // things), so it is said rather than assumed -- in ONE message, the
          // way the saved path below also folds a failed refresh into its own.
          message = '$message (The book list could not be refreshed either: '
              '${serverErrorMessage(e2)})';
        }
        widget.onMessage(message);
        return;
      }
      var message = '"${res.book.title}" is now the ${subject.name} edition for this year.';
      if (res.warning != null) message = '$message ${res.warning}';
      // The choice is saved. A refresh that fails now leaves a stale list,
      // not a failed write: saying "Could not choose the book" here would be
      // a wrong answer about a change that actually happened.
      try {
        await _reloadBooks(subject.id);
      } catch (e) {
        message = '$message (The book list could not be refreshed: '
            '${serverErrorMessage(e)})';
      }
      widget.onMessage(message);
    } finally {
      if (mounted) setState(() => _saving.remove(subject.id));
    }
  }

  Future<void> _addBook(SubjectSummary subject) async {
    List<BoardSummary> boards;
    try {
      boards = await _api.boards();
    } catch (e) {
      widget.onMessage('Could not load boards: ${serverErrorMessage(e)}');
      return;
    }
    if (!mounted) return;
    if (boards.isEmpty) {
      widget.onMessage('No board exists yet -- seed the curriculum first.');
      return;
    }
    final existingBoard = _books[subject.id]?.firstOrNull?.boardId;
    final input = await showDialog<_NewBook>(
      context: context,
      builder: (_) => _AddBookDialog(
        subjectName: subject.name,
        boards: boards,
        initialBoardId: boards.any((b) => b.id == existingBoard) ? existingBoard! : boards.first.id,
      ),
    );
    if (input == null) return;
    setState(() => _saving.add(subject.id));
    try {
      final book =
          await _api.addBook(subject.id, title: input.title, publisher: input.publisher, boardId: input.boardId);
      widget.onMessage('Added "${book.title}". Choose it below to make it the ${subject.name} edition.');
      await _reloadBooks(subject.id);
    } catch (e) {
      widget.onMessage('Could not add the book: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _saving.remove(subject.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DropdownButtonFormField<String>(
            initialValue: _gradeId,
            // Not "Grade": "Assign a teacher" below has a class picker too,
            // and a screen reader heard two controls with one name (QA S-22).
            decoration: const InputDecoration(labelText: 'Books for class'),
            isExpanded: true,
            items: [
              for (final g in widget.grades) DropdownMenuItem(value: g.id, child: Text(g.label)),
            ],
            onChanged: _onGradeChanged,
          ),
          if (_loading) ...[
            const Gap(12),
            const LinearProgressIndicator(),
          ],
          if (_error != null) ...[
            const Gap(12),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],
          for (final subject in _subjects) ...[
            const Gap(16),
            _subjectRow(theme, subject),
          ],
        ],
      ),
    );
  }

  Widget _subjectRow(ThemeData theme, SubjectSummary subject) {
    final books = _books[subject.id] ?? const <BookSummary>[];
    final selected = books.where((b) => b.selected).firstOrNull;
    final saving = _saving.contains(subject.id);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(subject.name, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            ),
            if (saving) const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
            TextButton.icon(
              onPressed: saving ? null : () => _addBook(subject),
              icon: const Icon(Icons.add),
              label: const Text('Add book'),
            ),
          ],
        ),
        const Gap(8),
        if (books.isEmpty)
          Text('No book yet. Add one, or seed the curriculum.',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant))
        else
          KeyedSubtree(
            key: ValueKey('book-edition-${subject.id}'),
            child: DropdownButtonFormField<String>(
              // Re-keyed on every reload so the field re-reads initialValue:
              // after a refused choice the menu would otherwise keep showing
              // the book the server did not accept.
              key: ValueKey('book-edition-${subject.id}-${_reloads[subject.id] ?? 0}'),
              initialValue: selected?.id,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: 'Edition',
                helperText: selected == null ? 'Several books and none chosen: choose one.' : null,
              ),
              items: [
                for (final b in books)
                  DropdownMenuItem(value: b.id, child: Text(b.label, overflow: TextOverflow.ellipsis)),
              ],
              onChanged: saving ? null : (id) => _select(subject, id),
            ),
          ),
      ],
    );
  }
}

class _NewBook {
  final String title;
  final String? publisher;
  final String boardId;
  const _NewBook(this.title, this.publisher, this.boardId);
}

class _AddBookDialog extends StatefulWidget {
  final String subjectName;
  final List<BoardSummary> boards;
  final String initialBoardId;

  const _AddBookDialog({required this.subjectName, required this.boards, required this.initialBoardId});

  @override
  State<_AddBookDialog> createState() => _AddBookDialogState();
}

class _AddBookDialogState extends State<_AddBookDialog> {
  final _title = TextEditingController();
  final _publisher = TextEditingController();
  late String _boardId = widget.initialBoardId;

  @override
  void dispose() {
    _title.dispose();
    _publisher.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Add a ${widget.subjectName} book'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _title,
            autofocus: true,
            decoration: const InputDecoration(labelText: 'Title'),
            onChanged: (_) => setState(() {}),
          ),
          const Gap(12),
          TextField(
            controller: _publisher,
            decoration: const InputDecoration(
                labelText: 'Publisher / edition', hintText: 'e.g. NCERT, 2026 reprint'),
          ),
          const Gap(12),
          DropdownButtonFormField<String>(
            initialValue: _boardId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Board'),
            items: [for (final b in widget.boards) DropdownMenuItem(value: b.id, child: Text(b.name))],
            onChanged: (id) => setState(() => _boardId = id ?? _boardId),
          ),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
        FilledButton(
          onPressed: _title.text.trim().isEmpty
              ? null
              : () {
                  final publisher = _publisher.text.trim();
                  Navigator.of(context)
                      .pop(_NewBook(_title.text.trim(), publisher.isEmpty ? null : publisher, _boardId));
                },
          child: const Text('Add'),
        ),
      ],
    );
  }
}
