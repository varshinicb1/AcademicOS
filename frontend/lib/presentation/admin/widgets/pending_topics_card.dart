import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/curriculum_api.dart';
import '../../shared/widgets/common_widgets.dart';

/// "Proposed topics" on the principal's console: every chapter of a subject,
/// what the seed proposed for it from the committed decomposition template, and
/// one button that accepts a whole chapter's proposal.
///
/// Why this screen exists. Measured on a fresh school 2026-09-22: seeding gave
/// 5 subjects, 23 units and 58 chapters, and `GET /chapters/{id}/topics`
/// answered `[]` for every one of them -- so the subtopic filter,
/// micro-scheduling and coverage worked for no school but school_1. Seeding now
/// proposes real topics from a real source, but deliberately as PENDING
/// proposals: they came from another school's approved work or from a
/// textbook's headings, and approving them is this principal's decision, not
/// something the seed may do on their behalf.
///
/// "Approve all for this chapter" is what makes that decision affordable. A
/// Class 10 seed proposes topics for 46 chapters; at one proposal at a time
/// (the per-proposal review surface, which stays for LLM drafts) a school would
/// not finish setup. The card shows exactly what will be created, and where it
/// came from, before the principal accepts it.
class PendingTopicsCard extends StatefulWidget {
  final List<GradeSummary> grades;
  final void Function(String message) onMessage;

  const PendingTopicsCard({super.key, required this.grades, required this.onMessage});

  @override
  State<PendingTopicsCard> createState() => _PendingTopicsCardState();
}

class _PendingTopicsCardState extends State<PendingTopicsCard> {
  String? _gradeId;
  String? _subjectId;
  List<SubjectSummary> _subjects = [];
  List<ChapterSummary> _chapters = [];
  final Map<String, List<ChapterTopicProposals>> _pending = {};
  final Set<String> _approving = {};
  bool _loading = false;
  String? _error;

  CurriculumApi get _api => GetIt.I<CurriculumApi>();

  Future<void> _onGradeChanged(String? gradeId) async {
    setState(() {
      _gradeId = gradeId;
      _subjectId = null;
      _subjects = [];
      _chapters = [];
      _pending.clear();
      _error = null;
    });
    if (gradeId == null) return;
    setState(() => _loading = true);
    try {
      final subjects = await _api.subjects(gradeId);
      if (!mounted || _gradeId != gradeId) return;
      setState(() => _subjects = subjects);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load subjects: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _onSubjectChanged(String? subjectId) async {
    setState(() {
      _subjectId = subjectId;
      _chapters = [];
      _pending.clear();
      _error = null;
    });
    if (subjectId == null) return;
    setState(() => _loading = true);
    try {
      // The subject's chosen edition, not books.first: a subject can hold
      // several editions and only one is this year's (PRD 12.7).
      final book = await _api.selectedBook(subjectId);
      if (book == null) {
        if (mounted) {
          setState(() => _error =
              'This subject has no chosen edition yet -- choose one on the Roster tab first.');
        }
        return;
      }
      final chapters = await _api.chapters(book.id);
      chapters.sort((a, b) => a.seq.compareTo(b.seq));
      final proposals = await Future.wait(chapters.map((c) => _api.proposedTopics(c.id)));
      if (!mounted || _subjectId != subjectId) return;
      setState(() {
        _chapters = chapters;
        for (var i = 0; i < chapters.length; i++) {
          _pending[chapters[i].id] = proposals[i];
        }
      });
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load proposals: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _approveChapter(ChapterSummary chapter) async {
    setState(() => _approving.add(chapter.id));
    try {
      final result = await _api.approveAllTopics(chapter.id);
      widget.onMessage('${chapter.name}: ${result.summary}');
      // Re-read rather than clearing locally: approved proposals disappear
      // from this list because they are real topics now, and that is the
      // server's answer to check, not an assumption.
      final left = await _api.proposedTopics(chapter.id);
      if (mounted) setState(() => _pending[chapter.id] = left);
    } catch (e) {
      widget.onMessage('Could not approve ${chapter.name}: ${serverErrorMessage(e)}');
    } finally {
      if (mounted) setState(() => _approving.remove(chapter.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final waiting = _chapters.where((c) => (_pending[c.id] ?? const []).isNotEmpty).toList();
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Proposed topics',
              style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
          const Gap(4),
          Text(
            'Seeding proposes a chapter breakdown from a real source. Nothing below is part '
            'of your curriculum until you approve it.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
          const Gap(12),
          DropdownButtonFormField<String>(
            initialValue: _gradeId,
            decoration: const InputDecoration(labelText: 'Grade', border: OutlineInputBorder()),
            isExpanded: true,
            items: [
              for (final g in widget.grades) DropdownMenuItem(value: g.id, child: Text(g.label)),
            ],
            onChanged: _onGradeChanged,
          ),
          if (_subjects.isNotEmpty) ...[
            const Gap(12),
            DropdownButtonFormField<String>(
              initialValue: _subjectId,
              decoration: const InputDecoration(labelText: 'Subject', border: OutlineInputBorder()),
              isExpanded: true,
              items: [
                for (final s in _subjects) DropdownMenuItem(value: s.id, child: Text(s.name)),
              ],
              onChanged: _onSubjectChanged,
            ),
          ],
          if (_loading) ...[
            const Gap(12),
            const LinearProgressIndicator(),
          ],
          if (_error != null) ...[
            const Gap(12),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],
          if (!_loading && _subjectId != null && _error == null) ...[
            const Gap(12),
            Text(
              waiting.isEmpty
                  ? 'No chapter of this subject is waiting for approval. Chapters with no '
                      'proposal at all need the LLM extraction route, or topics added by hand.'
                  : '${waiting.length} of ${_chapters.length} chapters have proposals waiting.',
              style: theme.textTheme.bodySmall,
            ),
            for (final chapter in waiting) ...[
              const Gap(12),
              _chapterTile(theme, chapter, _pending[chapter.id]!),
            ],
          ],
        ],
      ),
    );
  }

  Widget _chapterTile(ThemeData theme, ChapterSummary chapter,
      List<ChapterTopicProposals> proposals) {
    final topics = [for (final p in proposals) ...p.topics];
    final subtopics = topics.fold<int>(0, (n, t) => n + t.subtopics.length);
    final approving = _approving.contains(chapter.id);
    return Card(
      margin: EdgeInsets.zero,
      child: ExpansionTile(
        title: Text(chapter.name),
        subtitle: Text(
          '${topics.length} topics, $subtopics subtopics proposed from '
          '${proposals.map((p) => p.sourceLabel).toSet().join(', ')}',
          style: theme.textTheme.bodySmall,
        ),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final t in topics) ...[
            Text(t.name, style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
            if (t.description != null)
              Text(t.description!,
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            for (final s in t.subtopics)
              Padding(
                padding: const EdgeInsets.only(left: 16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: Text('• ${s.name}', style: theme.textTheme.bodySmall)),
                    // The source's own reference, kept next to the name it
                    // justifies -- this is what the principal checks against
                    // the book before accepting the chapter.
                    if (s.description != null)
                      Text(s.description!,
                          style: theme.textTheme.bodySmall
                              ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  ],
                ),
              ),
            const Gap(8),
          ],
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.icon(
              onPressed: approving ? null : () => _approveChapter(chapter),
              icon: approving
                  ? const SizedBox(
                      width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.check),
              label: const Text('Approve all for this chapter'),
            ),
          ),
        ],
      ),
    );
  }
}
