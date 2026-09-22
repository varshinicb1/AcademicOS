import 'package:flutter/material.dart';

import '../../../data/datasources/api/paper_builder_api.dart';
import '../paper_builder_controller.dart';

/// Opens the section editor on [initial] -- a new template, one of the
/// teacher's own, a preset or shared one (saved as a copy), or a template
/// with a fix from the availability check already applied. [saveAsNew]
/// ("Save as new" on one of the teacher's own cards) saves a copy and
/// leaves the original as it was.
Future<void> showSectionEditor(BuildContext context, PaperBuilderController c, PaperTemplateView initial,
    {String? note, bool saveAsNew = false}) {
  return Navigator.of(context).push(MaterialPageRoute<void>(
    fullscreenDialog: true,
    builder: (_) => SectionEditor(c: c, initial: initial, note: note, saveAsNew: saveAsNew),
  ));
}

/// The kinds a section can ask for, in a teacher's words. Empty = any kind at
/// this mark value, which is what most sections want: the bank's type labels
/// are mostly derived from marks (see TemplateSection's docstring).
const sectionKinds = <String, List<String>>{
  'Any kind': [],
  'Objective (MCQ)': ['mcq', 'assertion_reason'],
  'Short answer': ['very_short_answer', 'short_answer'],
  'Long answer': ['long_answer', 'very_long_answer'],
  'Case / source based': ['case_study'],
};

String kindOf(List<String> types) {
  for (final e in sectionKinds.entries) {
    if (e.value.length == types.length && e.value.toSet().containsAll(types)) return e.key;
  }
  return types.isEmpty ? 'Any kind' : 'As in the template';
}

/// A simple section editor: add a section, set its count, marks and ORs with
/// steppers (no number typing on a phone keyboard), and see the running
/// total. The total must match before saving -- the mismatch is shown here,
/// with the one-tap fix, never discovered as a failed request.
class SectionEditor extends StatefulWidget {
  final PaperBuilderController c;
  final PaperTemplateView initial;
  final String? note;
  final bool saveAsNew;
  const SectionEditor({super.key, required this.c, required this.initial, this.note, this.saveAsNew = false});

  @override
  State<SectionEditor> createState() => _SectionEditorState();
}

class _SectionEditorState extends State<SectionEditor> {
  late PaperTemplateView t = widget.initial;
  late final _name = TextEditingController(text: widget.initial.name);
  late final _total = TextEditingController(text: '${widget.initial.totalMarks}');
  late final _duration = TextEditingController(text: '${widget.initial.durationMinutes}');
  late final List<TextEditingController> _titles = [
    for (final s in widget.initial.sections) TextEditingController(text: s.title),
  ];
  bool _saving = false;
  String? _error;

  bool get _own => !widget.saveAsNew && widget.initial.id.isNotEmpty && !widget.initial.isPreset &&
      widget.initial.ownerId == widget.c.memory.userId;

  @override
  void dispose() {
    for (final x in [_name, _total, _duration, ..._titles]) {
      x.dispose();
    }
    super.dispose();
  }

  int get _totalMarks => int.tryParse(_total.text.trim()) ?? 0;
  int get _durationMinutes => int.tryParse(_duration.text.trim()) ?? 0;

  PaperTemplateView get _draft => t.copyWith(
        name: _name.text.trim(),
        totalMarks: _totalMarks,
        durationMinutes: _durationMinutes,
        sections: [
          for (final (i, s) in t.sections.indexed)
            s.copyWith(title: _titles[i].text.trim().isEmpty ? 'Section ${String.fromCharCode(65 + i)}' : _titles[i].text.trim()),
        ],
      );

  /// Everything that stops a save, in the order a teacher would fix it.
  List<String> get _problems {
    final d = _draft;
    return [
      if (d.name.isEmpty) 'Give the template a name.',
      if (d.sections.isEmpty) 'Add at least one section.',
      if (_durationMinutes <= 0) 'Set the duration in minutes.',
      if (d.sections.isNotEmpty && d.sectionMarks != _totalMarks)
        'Sections add up to ${d.sectionMarks} marks but the total is $_totalMarks.',
    ];
  }

  void _setSection(int i, TemplateSectionView s) => setState(() {
        final list = [...t.sections];
        list[i] = s;
        t = t.copyWith(sections: list);
      });

  void _addSection() => setState(() {
        final i = t.sections.length;
        _titles.add(TextEditingController(text: 'Section ${String.fromCharCode(65 + i)}'));
        t = t.copyWith(sections: [
          ...t.sections,
          TemplateSectionView(title: 'Section ${String.fromCharCode(65 + i)}', questionCount: 5, marksEach: 2),
        ]);
      });

  void _removeSection(int i) => setState(() {
        _titles.removeAt(i).dispose();
        t = t.copyWith(sections: [...t.sections]..removeAt(i));
      });

  Future<void> _save({required bool asNew}) async {
    if (_problems.isNotEmpty) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.c.saveTemplate(_draft, asNew: asNew, ownerId: widget.c.memory.userId);
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) setState(() => _error = apiErrorMessage(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final d = _draft;
    final problems = _problems;
    final ok = problems.isEmpty;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
            tooltip: 'Close without saving', icon: const Icon(Icons.close), onPressed: () => Navigator.of(context).pop()),
        title: Text(widget.initial.id.isEmpty ? 'New template' : (_own ? 'Edit template' : 'Edit a copy')),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          if (widget.note != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(widget.note!, style: TextStyle(color: theme.colorScheme.primary)),
            ),
          TextField(
            controller: _name,
            decoration: const InputDecoration(labelText: 'Template name'),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: TextField(
                key: const ValueKey('editor-total'),
                controller: _total,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Total marks'),
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _duration,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Minutes'),
                onChanged: (_) => setState(() {}),
              ),
            ),
          ]),
          const SizedBox(height: 16),
          for (final (i, s) in t.sections.indexed) _sectionCard(context, i, s),
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              onPressed: _addSection,
              icon: const Icon(Icons.add),
              label: const Text('Add section'),
              style: OutlinedButton.styleFrom(minimumSize: const Size(0, 44)),
            ),
          ),
        ],
      ),
      bottomNavigationBar: Material(
        elevation: 8,
        color: theme.colorScheme.surface,
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 10),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Text(
                'Running total: ${d.sectionMarks} of $_totalMarks marks',
                key: const ValueKey('editor-running-total'),
                style: theme.textTheme.titleSmall?.copyWith(
                    color: d.sectionMarks == _totalMarks ? theme.colorScheme.primary : theme.colorScheme.error),
              ),
              for (final p in problems)
                Text(p, style: TextStyle(color: theme.colorScheme.error)),
              if (d.sections.isNotEmpty && d.sectionMarks != _totalMarks && d.sectionMarks > 0)
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed: () => setState(() => _total.text = '${d.sectionMarks}'),
                    style: TextButton.styleFrom(minimumSize: const Size(0, 44)),
                    child: Text('Set the total to ${d.sectionMarks}'),
                  ),
                ),
              if (_error != null) Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
              const SizedBox(height: 6),
              Row(children: [
                if (_own) ...[
                  Expanded(
                    child: OutlinedButton(
                      onPressed: ok && !_saving ? () => _save(asNew: true) : null,
                      style: OutlinedButton.styleFrom(minimumSize: const Size(0, 48)),
                      child: const Text('Save as new'),
                    ),
                  ),
                  const SizedBox(width: 12),
                ],
                Expanded(
                  child: FilledButton(
                    key: const ValueKey('editor-save'),
                    onPressed: ok && !_saving ? () => _save(asNew: !_own) : null,
                    style: FilledButton.styleFrom(minimumSize: const Size(0, 48)),
                    child: Text(_saving ? 'Saving…' : (_own ? 'Save' : (widget.saveAsNew ? 'Save as new' : 'Save & use'))),
                  ),
                ),
              ]),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _sectionCard(BuildContext context, int i, TemplateSectionView s) {
    final theme = Theme.of(context);
    final letter = String.fromCharCode(65 + i);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 4, 4, 8),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(
              child: TextField(
                controller: _titles[i],
                decoration: InputDecoration(labelText: 'Section $letter title'),
                onChanged: (_) => setState(() {}),
              ),
            ),
            IconButton(
              tooltip: 'Remove section $letter',
              icon: const Icon(Icons.delete_outline),
              onPressed: () => _removeSection(i),
            ),
          ]),
          const SizedBox(height: 4),
          Wrap(spacing: 12, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
            _Stepper(
              label: 'Questions',
              semantic: 'section $letter questions',
              value: s.questionCount,
              min: 1,
              onChanged: (v) => _setSection(i, s.copyWith(questionCount: v)),
            ),
            _Stepper(
              label: 'Marks each',
              semantic: 'section $letter marks each',
              value: s.marksEach,
              min: 1,
              max: 20,
              onChanged: (v) => _setSection(i, s.copyWith(marksEach: v)),
            ),
            _Stepper(
              label: 'OR choices',
              semantic: 'section $letter OR choices',
              value: s.choiceCount > s.questionCount ? s.questionCount : s.choiceCount,
              min: 0,
              max: s.questionCount,
              onChanged: (v) => _setSection(i, s.copyWith(choiceCount: v)),
            ),
          ]),
          Row(children: [
            Text('Kind: ', style: theme.textTheme.bodySmall),
            Flexible(
              child: DropdownButton<String>(
                value: kindOf(s.questionTypes),
                isExpanded: true,
                items: [
                  for (final k in {...sectionKinds.keys, kindOf(s.questionTypes)})
                    DropdownMenuItem(value: k, child: Text(k, overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (k) {
                  if (k == null || !sectionKinds.containsKey(k)) return;
                  _setSection(i, s.copyWith(questionTypes: sectionKinds[k]));
                },
              ),
            ),
          ]),
          Text(
            '= ${s.marks} marks${s.choiceCount > 0 ? ' · ${s.choiceCount} with an OR choice' : ''}',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
        ]),
      ),
    );
  }
}

class _Stepper extends StatelessWidget {
  final String label;
  final String semantic;
  final int value;
  final int min;
  final int max;
  final ValueChanged<int> onChanged;

  const _Stepper({
    required this.label,
    required this.semantic,
    required this.value,
    required this.onChanged,
    this.min = 0,
    this.max = 99,
  });

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Text(label, style: Theme.of(context).textTheme.bodySmall),
      IconButton(
        tooltip: 'Fewer $semantic',
        icon: const Icon(Icons.remove_circle_outline),
        onPressed: value > min ? () => onChanged(value - 1) : null,
      ),
      Text('$value', style: Theme.of(context).textTheme.titleSmall),
      IconButton(
        tooltip: 'More $semantic',
        icon: const Icon(Icons.add_circle_outline),
        onPressed: value < max ? () => onChanged(value + 1) : null,
      ),
    ]);
  }
}
