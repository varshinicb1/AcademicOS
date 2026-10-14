import 'package:flutter/material.dart';

import '../../../core/constants/wording.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../paper_builder_controller.dart';
import 'class_subject_step.dart';
import 'section_editor.dart';

/// Step 3: the chapters, with the template's availability check running on
/// every change -- the gaps are on screen BEFORE Generate, each with the
/// changes that would close it, one tap each.
class ScopeStep extends StatelessWidget {
  final PaperBuilderController c;
  const ScopeStep({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = c.template!;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        ClassSubjectBanner(c: c),
        Row(children: [
          Icon(Icons.description_outlined, size: 20, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          // Wraps: cut at two lines, a phone read "Half-Yearly Examination ·
          // 80 marks · 1…" (QA P-35).
          Expanded(
            child: Text('${t.name} · ${marksText(t.totalMarks)} · ${t.durationMinutes} min',
                key: const ValueKey('scope-template'), style: theme.textTheme.titleSmall),
          ),
          TextButton(
            onPressed: () => c.goTo(BuilderStep.template),
            style: TextButton.styleFrom(minimumSize: const Size(64, 44)),
            child: const Text('Change'),
          ),
        ]),
        const SizedBox(height: 8),
        AvailabilityPanel(c: c),
        if (c.generateError != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text('Could not generate: ${c.generateError}', style: TextStyle(color: theme.colorScheme.error)),
          ),
        const SizedBox(height: 16),
        Text('Question sets', style: theme.textTheme.titleMedium),
        const SizedBox(height: 4),
        Text('Sets B and C print different questions of the same marks and kind, where the bank has them. '
            'A question a set has to repeat is listed with the paper.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const SizedBox(height: 6),
        SegmentedButton<int>(
          segments: const [
            ButtonSegment(value: 1, label: Text('1 set')),
            ButtonSegment(value: 2, label: Text('A, B')),
            ButtonSegment(value: 3, label: Text('A, B, C')),
          ],
          selected: {c.setCount},
          onSelectionChanged: (s) => c.setSets(s.first),
        ),
        // A Foundation or Advanced version where the bank judges the levels
        // these sections take (R-C4); the server ranks each chapter's
        // questions by the judged level and says if it changed nothing.
        if (c.tierChoice) ...[
          const SizedBox(height: 12),
          Text('Level', style: theme.textTheme.titleSmall),
          const SizedBox(height: 6),
          SegmentedButton<String>(
            key: const ValueKey('builder-tier'),
            segments: const [
              ButtonSegment(value: 'foundation', label: Text('Foundation')),
              ButtonSegment(value: 'standard', label: Text('Standard')),
              ButtonSegment(value: 'advanced', label: Text('Advanced')),
            ],
            selected: {c.tier},
            onSelectionChanged: (s) => c.setTier(s.first),
          ),
        ],
        // No Foundation/Advanced choice is offered; say why, beside the
        // versions the paper does have, rather than offer three that match.
        if (c.availability?.tiers case final tiers? when !tiers.available && tiers.sentence.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(tiers.sentence,
                key: const ValueKey('availability-tiers'),
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ),
        const SizedBox(height: 16),
        Text('Chapters', style: theme.textTheme.titleMedium),
        _Chapters(c: c),
      ],
    );
  }
}

class _Chapters extends StatelessWidget {
  final PaperBuilderController c;
  const _Chapters({required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (c.loadingChapters) {
      return const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()));
    }
    if (c.chaptersError != null) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Could not load chapters: ${c.chaptersError}', style: TextStyle(color: theme.colorScheme.error)),
        Text('You can still generate from the whole syllabus.', style: theme.textTheme.bodySmall),
        // Only where trying again can work: a 401 or a 403 answers the same
        // way every time (see PaperBuilderController's class doc).
        if (c.chaptersRetryable)
          OutlinedButton.icon(
              onPressed: c.loadChapters, icon: const Icon(Icons.refresh), label: const Text('Try again')),
      ]);
    }
    if (c.chapters.isEmpty) {
      return Text('No chapter list for Class ${c.grade} ${c.subject} yet; the paper draws on the whole syllabus.',
          style: TextStyle(color: theme.colorScheme.onSurfaceVariant));
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      CheckboxListTile(
        contentPadding: EdgeInsets.zero,
        title: const Text('Whole syllabus (all chapters)'),
        value: c.chapterIds.isEmpty,
        onChanged: (_) => c.useAllChapters(),
      ),
      for (final (unit, list) in c.chaptersByUnit) ...[
        Padding(
          padding: const EdgeInsets.only(top: 8, bottom: 2),
          child: Text(unit, style: theme.textTheme.labelLarge?.copyWith(color: theme.colorScheme.primary)),
        ),
        for (final ch in list)
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(ch.chapterName),
            subtitle: Text(ch.questionCount == 0
                ? 'No questions in the bank yet'
                : '${ch.questionCount} question${ch.questionCount == 1 ? '' : 's'} available'),
            value: c.chapterIds.contains(ch.chapterId),
            onChanged: (_) => c.toggleChapter(ch.chapterId),
          ),
      ],
    ]);
  }
}

/// What the bank can put on this paper, section by section.
/// The paper's competency-based share against CBSE's 50%, in the server's
/// own words: the share, what would change it, and -- when below -- how it was
/// counted.
class _CompetencyLine extends StatelessWidget {
  final CompetencyCheckView check;

  /// How many sets the paper will print.
  final int sets;

  /// Whether some section cannot be filled.
  final bool short;
  const _CompetencyLine({required this.check, this.sets = 1, this.short = false});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (icon, color) = switch (check.status) {
      // No green tick beside "4 of 4 sections cannot be filled" (QA P-18).
      'meets' when short => (Icons.info_outline, theme.colorScheme.onSurfaceVariant),
      'meets' => (Icons.check_circle_outline, theme.colorScheme.primary),
      'below_bank' => (Icons.warning_amber_rounded, theme.colorScheme.error),
      _ => (Icons.info_outline, theme.colorScheme.onSurfaceVariant),
    };
    // The check runs on Set A's questions; the other sets draw their own,
    // and their share is known only once they are generated (QA P-13).
    final others = sets == 2
        ? 'Set B draws its own questions; its share'
        : 'Sets B and C draw their own questions; their share';
    return Padding(
      key: const ValueKey('availability-competency'),
      padding: const EdgeInsets.only(top: 8),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(width: 8),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(sets > 1 ? 'Set A: ${check.summary}' : check.summary, style: theme.textTheme.bodyMedium),
            if (sets > 1)
              Text('$others is shown with the paper once it is generated.',
                  key: const ValueKey('competency-other-sets'), style: theme.textTheme.bodySmall),
            if (check.detail.isNotEmpty) Text(check.detail, style: theme.textTheme.bodySmall),
            if (check.belowTarget && check.counted.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(check.counted,
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ),
          ]),
        ),
      ]),
    );
  }
}

class AvailabilityPanel extends StatelessWidget {
  final PaperBuilderController c;
  const AvailabilityPanel({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final a = c.availability;
    if (c.availabilityError != null) {
      return _box(context, theme.colorScheme.errorContainer, [
        Text('Could not check the bank: ${c.availabilityError}'),
        // A template a colleague has just deleted (404) will not come back
        // on a second check; "Change" above goes to a template that exists.
        // Only a failure that could pass next time offers to check again.
        if (c.availabilityRetryable)
          TextButton.icon(
              onPressed: c.checkAvailability, icon: const Icon(Icons.refresh), label: const Text('Check again')),
      ]);
    }
    if (a == null) {
      return _box(context, theme.colorScheme.surfaceContainerHighest, [
        const Row(children: [
          SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
          SizedBox(width: 12),
          Expanded(child: Text('Checking what the question bank holds for this paper…')),
        ]),
      ]);
    }
    final short = a.short;
    final scope = c.chapterIds.isEmpty ? 'the whole syllabus' : '${c.chapterIds.length} chapter${c.chapterIds.length == 1 ? '' : 's'}';
    final notes = [...a.scopeNotes, for (final s in a.sections) ...s.notes];
    return _box(
      context,
      short.isEmpty ? theme.colorScheme.primaryContainer : theme.colorScheme.errorContainer,
      [
        Row(children: [
          Icon(short.isEmpty ? Icons.check_circle : Icons.warning_amber_rounded,
              color: short.isEmpty ? theme.colorScheme.primary : theme.colorScheme.error),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              a.nothingFits
                  ? 'The bank has nothing for this paper in $scope yet.'
                  : short.isEmpty
                      ? 'Ready: every section can be filled from $scope.'
                      : '${short.length} of ${a.sections.length} sections cannot be filled from $scope.',
              key: const ValueKey('availability-summary'),
              style: theme.textTheme.titleSmall,
            ),
          ),
          if (c.checking) const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
        ]),
        if (c.fillFromOutsideScope)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text('Gaps are filled from outside the chosen chapters; the paper lists those questions.',
                style: theme.textTheme.bodySmall),
          ),
        // How short, in marks: the sections alone never said the paper would
        // print 58 of its 80 (QA P-18).
        if (short.isNotEmpty && !a.nothingFits)
          if (c.marksReach case final reach?)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'The paper would print ${reach.reached} of ${marksText(reach.total)}'
                '${reach.reached < reach.total ? ' — ${reach.total - reach.reached} short' : ''}.',
                key: const ValueKey('availability-marks'),
                style: theme.textTheme.bodyMedium,
              ),
            ),
        // On the panel, never in the collapsed notes: CBSE's 50% is decided
        // here, while the chapters can still change (Task 125). Not beside a
        // paper with nothing to print.
        if (a.competency != null && !a.nothingFits)
          _CompetencyLine(check: a.competency!, sets: c.setCount, short: short.isNotEmpty),
        for (final s in short) _ShortSection(c: c, s: s),
        if (a.nothingFits)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              'Nothing can be generated until the bank has questions here. Choose other chapters, another '
              'template, or another class -- or check back when more questions are added.',
              style: theme.textTheme.bodySmall,
            ),
          ),
        if (notes.isNotEmpty)
          Theme(
            data: theme.copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: Text('${notes.length} note${notes.length == 1 ? '' : 's'} on this paper',
                  style: theme.textTheme.bodyMedium),
              children: [
                for (final n in notes)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Padding(padding: const EdgeInsets.only(bottom: 6), child: Text('• $n')),
                  ),
              ],
            ),
          ),
      ],
    );
  }

  // A Material, not a coloured Container: the notes' ExpansionTile paints
  // its ink on the nearest Material, which a DecoratedBox would hide.
  Widget _box(BuildContext context, Color color, List<Widget> children) => Material(
        color: color,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: SizedBox(
            width: double.infinity,
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: children),
          ),
        ),
      );
}

class _ShortSection extends StatelessWidget {
  final PaperBuilderController c;
  final SectionAvailabilityView s;
  const _ShortSection({required this.c, required this.s});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // What fits, not "bank has": the bank can hold more questions of the
        // marks than fit the section, and the server's reason below counts
        // those (QA P-18).
        Text(
          '${s.title} needs ${s.needed} × ${s.marksEach}-mark, ${s.filled} '
          '${s.filled == 1 ? 'fits' : 'fit'} '
          '${c.chapterIds.isEmpty ? 'from the whole syllabus' : 'from these chapters'}.',
          style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
        ),
        if (s.reason.isNotEmpty) Text(s.reason, style: theme.textTheme.bodySmall),
        // Only what can close the gap: fewer OR choices never fills a
        // compulsory question -- the bank fills those first -- so "Print
        // this section without OR choices" is not offered here.
        for (final f in s.fixes.where((f) => f.kind != 'reduce_choices'))
          InkWell(
            onTap: () => _apply(context, f),
            child: ConstrainedBox(
              constraints: const BoxConstraints(minHeight: 44),
              child: Row(children: [
                Icon(f.changesScope ? Icons.library_add_outlined : Icons.tune, size: 20, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(f.label, style: TextStyle(color: theme.colorScheme.primary)),
                ),
              ]),
            ),
          ),
      ]),
    );
  }

  Future<void> _apply(BuildContext context, SectionFixView f) async {
    final before = c.template!;
    final draft = await c.applyFix(s, f);
    if (draft == null || !context.mounted) return;
    final totalNote = draft.totalMarks == before.totalMarks
        ? ''
        : ' The total is now ${draft.totalMarks} marks (was ${before.totalMarks}).';
    await showSectionEditor(context, c, draft,
        note: 'Changed ${s.title}: ${f.label}$totalNote Save to use it for this paper.');
  }
}
