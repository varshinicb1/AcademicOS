import 'package:flutter/material.dart';

import '../../../data/datasources/api/api_error.dart';
import '../../../data/datasources/api/paper_builder_api.dart';
import '../paper_builder_controller.dart';
import 'class_subject_step.dart';
import 'section_editor.dart';

/// Step 2: the paper's pattern. The teacher's own templates first (what they
/// reuse every term), then the school's shared ones, then the CBSE patterns.
class TemplateStep extends StatelessWidget {
  final PaperBuilderController c;
  const TemplateStep({super.key, required this.c});

  @override
  Widget build(BuildContext context) {
    final lists = c.templates;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        ClassSubjectBanner(c: c),
        const SizedBox(height: 4),
        Align(
          alignment: Alignment.centerLeft,
          child: OutlinedButton.icon(
            onPressed: lists == null ? null : () => openNewTemplate(context, c),
            icon: const Icon(Icons.add),
            label: const Text('New template'),
            style: OutlinedButton.styleFrom(minimumSize: const Size(0, 44)),
          ),
        ),
        const SizedBox(height: 8),
        if (c.loadingTemplates)
          const Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator()))
        else ...[
          // Above the lists, not instead of them. A refresh that fails after
          // a save or a duplicate (_refreshTemplateLists) leaves `templates`
          // holding the list the teacher was reading a moment ago, and the
          // action they took worked: replacing that list with a banner takes
          // away the templates AND hides the copy they just made. The banner
          // only ever stands alone when there is no list yet.
          //
          // No "Try again" where trying again cannot work -- a 401 or a 403
          // is refused again every time (see the controller's class doc).
          if (c.templatesError != null)
            _Problem(
              text: 'Could not load templates: ${c.templatesError}',
              action: 'Try again',
              onAction: c.templatesRetryable ? c.loadTemplates : null,
            ),
          if (lists != null) ...[
            _Group(
              title: 'My templates',
              empty: 'None yet. Build one with "New template", or duplicate a CBSE pattern below and change it.',
              templates: lists.mine,
              c: c,
            ),
            _Group(
              title: 'Shared by my school',
              empty: 'No colleague has shared a template for this class and subject yet.',
              templates: lists.shared,
              c: c,
            ),
            _Group(
              title: 'CBSE patterns',
              empty: 'No CBSE pattern for Class ${c.grade} ${c.subject} yet. Build your own with "New template" '
                  '-- the total is checked as you go.',
              templates: lists.presets,
              c: c,
            ),
          ],
        ],
      ],
    );
  }
}

Future<void> openNewTemplate(BuildContext context, PaperBuilderController c) {
  final draft = PaperTemplateView(
    name: 'Class ${c.grade} ${c.subject} test',
    grade: c.grade!,
    subject: c.subject!,
    totalMarks: 20,
    durationMinutes: 45,
    sections: [
      TemplateSectionView(title: 'Section A - Objective', questionCount: 10, marksEach: 1),
      TemplateSectionView(title: 'Section B - Short answer', questionCount: 5, marksEach: 2),
    ],
  );
  return showSectionEditor(context, c, draft);
}

class _Group extends StatelessWidget {
  final String title;
  final String empty;
  final List<PaperTemplateView> templates;
  final PaperBuilderController c;

  const _Group({required this.title, required this.empty, required this.templates, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(title, style: theme.textTheme.titleMedium),
        const SizedBox(height: 6),
        if (templates.isEmpty)
          Text(empty, style: TextStyle(color: theme.colorScheme.onSurfaceVariant))
        else
          for (final t in templates) TemplateCard(t: t, c: c),
      ]),
    );
  }
}

class TemplateCard extends StatelessWidget {
  final PaperTemplateView t;
  final PaperBuilderController c;
  const TemplateCard({super.key, required this.t, required this.c});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final selected = c.template?.id == t.id;
    final mine = !t.isPreset && t.ownerId == c.memory.userId;
    final badge = switch (t.patternStatus) {
      'cbse_board' => 'CBSE board pattern',
      'suggested' => 'Suggested pattern',
      _ => mine ? 'Mine' : 'Shared',
    };
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: selected ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
          width: selected ? 2 : 1,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => c.selectTemplate(t),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 8, 4),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(child: Text(t.name, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600))),
              if (selected) Icon(Icons.check_circle, color: theme.colorScheme.primary, semanticLabel: 'Selected'),
            ]),
            const SizedBox(height: 4),
            Text('${t.totalMarks} marks · ${t.durationMinutes} min · ${t.questionCount} questions · $badge',
                style: theme.textTheme.bodySmall),
            const SizedBox(height: 2),
            Text(t.sectionSummary,
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            Wrap(spacing: 4, children: [
              TextButton(
                onPressed: () => c.useTemplate(t),
                style: TextButton.styleFrom(minimumSize: const Size(56, 44)),
                child: const Text('Use'),
              ),
              TextButton(
                onPressed: () => showSectionEditor(context, c, t),
                style: TextButton.styleFrom(minimumSize: const Size(56, 44)),
                child: Text(mine ? 'Edit' : 'Edit a copy'),
              ),
              // "Edit a copy" already saves a preset or a colleague's
              // template as new; on the teacher's own, Edit saves in place,
              // so a copy is its own action.
              if (mine)
                TextButton(
                  onPressed: () => showSectionEditor(context, c, t.copyWith(name: '${t.name} (new)'), saveAsNew: true),
                  style: TextButton.styleFrom(minimumSize: const Size(56, 44)),
                  child: const Text('Save as new'),
                ),
              TextButton(
                onPressed: () async {
                  try {
                    final copy = await c.duplicate(t);
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context)
                        .showSnackBar(SnackBar(content: Text('Saved "${copy.name}" to My templates.')));
                  } catch (e) {
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context)
                        .showSnackBar(SnackBar(content: Text('Could not duplicate: ${serverErrorMessage(e)}')));
                  }
                },
                style: TextButton.styleFrom(minimumSize: const Size(56, 44)),
                child: const Text('Duplicate'),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}

/// A failure on this step, with [action] only when repeating the request
/// could succeed ([onAction] null otherwise -- no button is drawn at all,
/// rather than one that is disabled and says nothing about why).
class _Problem extends StatelessWidget {
  final String text;
  final String action;
  final VoidCallback? onAction;
  const _Problem({required this.text, required this.action, required this.onAction});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final retry = onAction;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(text, style: TextStyle(color: theme.colorScheme.error)),
        if (retry != null) ...[
          const SizedBox(height: 8),
          OutlinedButton.icon(onPressed: retry, icon: const Icon(Icons.refresh), label: Text(action)),
        ],
      ]),
    );
  }
}
