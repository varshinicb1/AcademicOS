import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Pillar 1 — the template maker.
///
/// A school's paper format is institutional identity. Defining it once here
/// means every generated paper conforms exactly: header, margins, and the
/// school's own section layout (how many sections, marks per question).
class TemplateMakerPage extends StatefulWidget {
  final String schoolId;
  const TemplateMakerPage({super.key, this.schoolId = 'school_1'});

  @override
  State<TemplateMakerPage> createState() => _TemplateMakerPageState();
}

class _SectionDraft {
  String label;
  String name;
  int marksPerQuestion;
  int questionCount;

  _SectionDraft(this.label, this.name, this.marksPerQuestion, this.questionCount);

  int get totalMarks => marksPerQuestion * questionCount;

  Map<String, dynamic> toJson() => {
        'id': 'section-${label.toLowerCase()}',
        'label': label,
        'name': name,
        'marksPerQuestion': marksPerQuestion,
        'questionCount': questionCount,
        'totalMarks': totalMarks,
        'allowedBloomLevels': <String>[],
        'allowedDifficulties': <String>[],
        'hasInternalChoice': false,
        'internalChoiceCount': 0,
      };
}

class _TemplateMakerPageState extends State<TemplateMakerPage> {
  final _name = TextEditingController(text: 'School Term Paper Format');
  final _margin = TextEditingController(text: '18');
  final _fontSize = TextEditingController(text: '11');

  List<_SectionDraft> _sections = [
    _SectionDraft('A', 'MCQ', 1, 20),
    _SectionDraft('B', 'Very Short Answer', 2, 5),
    _SectionDraft('C', 'Short Answer', 3, 7),
    _SectionDraft('D', 'Long Answer', 5, 3),
    _SectionDraft('E', 'Case Study', 4, 3),
  ];

  // Fields this screen doesn't expose editors for yet, but must round-trip
  // rather than silently reset to blank on every save (logo/branding, once
  // set some other way, was getting wiped by every edit here).
  String _templateId = 'new';
  String _tagline = '';
  String _brandColor = '#000000';
  String _headerHtml = '';
  String _footerHtml = '';
  String _logoUrl = '';
  Map<String, dynamic> _sectionFormatting = {};

  bool _loading = true;
  bool _saving = false;
  String? _message;
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _name.dispose();
    _margin.dispose();
    _fontSize.dispose();
    super.dispose();
  }

  int get _total => _sections.fold(0, (s, e) => s + e.totalMarks);

  Future<void> _load() async {
    try {
      final api = GetIt.I<PillarApi>();
      final templates = await api.schoolTemplates(widget.schoolId);
      if (templates.isEmpty) return;
      final t = templates.firstWhere((e) => e['isDefault'] == true, orElse: () => templates.first);
      _templateId = (t['id'] as String?) ?? 'new';
      _name.text = (t['name'] as String?) ?? _name.text;
      _tagline = (t['tagline'] as String?) ?? '';
      _brandColor = (t['brandColor'] as String?) ?? '#000000';
      _headerHtml = (t['headerHtml'] as String?) ?? '';
      _footerHtml = (t['footerHtml'] as String?) ?? '';
      _logoUrl = (t['logoUrl'] as String?) ?? '';
      _margin.text = '${(t['marginTop'] as num?) ?? 18}';
      _fontSize.text = '${(t['fontSize'] as num?) ?? 11}';
      _sectionFormatting = Map<String, dynamic>.from(t['sectionFormatting'] as Map? ?? {});

      if (_templateId != 'new' && _templateId != 'default') {
        final sections = await api.templateSections(widget.schoolId, _templateId);
        if (sections.isNotEmpty) {
          _sections = sections
              .map((s) => _SectionDraft(
                    s['label'] as String? ?? '?',
                    s['name'] as String? ?? 'Section',
                    (s['marksPerQuestion'] as num?)?.toInt() ?? 1,
                    (s['questionCount'] as num?)?.toInt() ?? 1,
                  ))
              .toList();
        }
      }
    } catch (e) {
      // No saved template yet (or fetch failed): keep the demo defaults as a
      // starting point rather than blocking the page.
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _message = null;
    });
    try {
      final saved = await GetIt.I<PillarApi>().saveTemplate(
        widget.schoolId,
        {
          'id': _templateId,
          'schoolId': widget.schoolId,
          'name': _name.text.trim().isEmpty ? 'School Template' : _name.text.trim(),
          'tagline': _tagline,
          'brandColor': _brandColor,
          'headerHtml': _headerHtml,
          'footerHtml': _footerHtml,
          'logoUrl': _logoUrl,
          'marginTop': double.tryParse(_margin.text) ?? 18,
          'marginBottom': double.tryParse(_margin.text) ?? 18,
          'marginLeft': double.tryParse(_margin.text) ?? 18,
          'marginRight': double.tryParse(_margin.text) ?? 18,
          'fontFamily': 'Helvetica',
          'fontSize': int.tryParse(_fontSize.text) ?? 11,
          'lineHeight': 1.4,
          'sectionFormatting': _sectionFormatting,
          'isDefault': true,
        },
        _sections.map((s) => s.toJson()).toList(),
      );
      setState(() {
        _error = false;
        _templateId = (saved['id'] as String?) ?? _templateId;
        _message = 'Saved "${saved['name']}" as the default format for this school.';
      });
    } catch (e) {
      setState(() {
        _error = true;
        _message = '$e';
      });
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _addSection() {
    const labels = 'ABCDEFGH';
    final next = labels[_sections.length.clamp(0, labels.length - 1)];
    setState(() => _sections.add(_SectionDraft(next, 'New Section', 2, 4)));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(leading: shellLeading(context), title: const Text('Paper Template')),
      body: _loading
          ? const LoadingIndicator(message: 'Loading school template…')
          : _buildForm(theme),
    );
  }

  Widget _buildForm(ThemeData theme) {
    return ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('School format',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700)),
                const Gap(4),
                Text('Every generated paper will follow this layout exactly.',
                    style: theme.textTheme.bodySmall),
                const Gap(14),
                TextField(
                  controller: _name,
                  decoration: const InputDecoration(
                      labelText: 'Template name', border: OutlineInputBorder()),
                ),
                const Gap(12),
                Row(children: [
                  Expanded(
                    child: TextField(
                      controller: _margin,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                          labelText: 'Margin (mm)', border: OutlineInputBorder()),
                    ),
                  ),
                  const Gap(12),
                  Expanded(
                    child: TextField(
                      controller: _fontSize,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                          labelText: 'Font size (pt)', border: OutlineInputBorder()),
                    ),
                  ),
                ]),
              ],
            ),
          ),
          Row(
            children: [
              Text('Sections',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const Spacer(),
              ChipTag(
                label: 'Total $_total marks',
                color: theme.colorScheme.primary,
              ),
            ],
          ),
          const Gap(8),
          ..._sections.asMap().entries.map((e) => _sectionCard(theme, e.key, e.value)),
          const Gap(4),
          OutlinedButton.icon(
            onPressed: _addSection,
            icon: const Icon(Icons.add),
            label: const Text('Add section'),
          ),
          const Gap(16),
          if (_message != null)
            AppCard(
              color: (_error ? theme.colorScheme.error : Colors.green)
                  .withValues(alpha: 0.12),
              child: Row(children: [
                Icon(_error ? Icons.error_outline : Icons.check_circle,
                    color: _error ? theme.colorScheme.error : Colors.green),
                const Gap(10),
                Expanded(child: Text(_message!)),
              ]),
            ),
          FilledButton.icon(
            onPressed: _saving ? null : _save,
            icon: _saving
                ? const SizedBox(
                    width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.save),
            label: Text(_saving ? 'Saving…' : 'Save as school default'),
            style: FilledButton.styleFrom(minimumSize: const Size(double.infinity, 48)),
          ),
        ],
      );
  }

  Widget _sectionCard(ThemeData theme, int index, _SectionDraft s) {
    // Section name gets its own full-width row: squeezed between the avatar,
    // marks chip and delete button (the original single-row layout) it had
    // under 240px on a phone screen, clipping longer names like "Very Short
    // Answer" mid-word with no ellipsis. A full card width comfortably fits
    // every CBSE section name in the default template.
    return AppCard(
      child: Column(
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 15,
                backgroundColor: theme.colorScheme.primaryContainer,
                child: Text(s.label,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
              ),
              const Gap(10),
              Expanded(
                child: TextFormField(
                  initialValue: s.name,
                  decoration: const InputDecoration(
                      labelText: 'Section name', isDense: true),
                  onChanged: (v) => setState(() => s.name = v),
                ),
              ),
            ],
          ),
          const Gap(8),
          Row(children: [
            ChipTag(label: '${s.totalMarks}m'),
            const Spacer(),
            IconButton(
              tooltip: 'Remove section',
              icon: const Icon(Icons.delete_outline, size: 20),
              onPressed: _sections.length > 1
                  ? () => setState(() => _sections.removeAt(index))
                  : null,
            ),
          ]),
          const Gap(6),
          Row(children: [
            Expanded(
              child: _stepper(theme, 'Marks', s.marksPerQuestion, 1, 10,
                  (v) => setState(() => s.marksPerQuestion = v)),
            ),
            const Gap(12),
            Expanded(
              child: _stepper(theme, 'Qs', s.questionCount, 1, 40,
                  (v) => setState(() => s.questionCount = v)),
            ),
          ]),
        ],
      ),
    );
  }

  Widget _stepper(ThemeData theme, String label, int value, int min, int max,
      ValueChanged<int> onChanged) {
    return Row(
      children: [
        Expanded(
          child: Text(label, style: theme.textTheme.bodySmall,
              maxLines: 1, overflow: TextOverflow.ellipsis),
        ),
        IconButton(
          visualDensity: VisualDensity.compact,
          icon: const Icon(Icons.remove_circle_outline, size: 19),
          onPressed: value > min ? () => onChanged(value - 1) : null,
        ),
        Text('$value', style: const TextStyle(fontWeight: FontWeight.w600)),
        IconButton(
          visualDensity: VisualDensity.compact,
          icon: const Icon(Icons.add_circle_outline, size: 19),
          onPressed: value < max ? () => onChanged(value + 1) : null,
        ),
      ],
    );
  }
}
