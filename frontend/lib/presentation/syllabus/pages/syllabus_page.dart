import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Syllabus coverage: every chapter of the selected subject and how much
/// assessment evidence exists for it. Chapters with no questions are shown
/// explicitly — a coverage gap the teacher needs to see, not one hidden.
class SyllabusPage extends StatefulWidget {
  const SyllabusPage({super.key});

  @override
  State<SyllabusPage> createState() => _SyllabusPageState();
}

class _SyllabusPageState extends State<SyllabusPage> {
  List<CatalogEntry> _catalog = [];
  CatalogEntry? _selected;
  List<ChapterEntry> _chapters = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = GetIt.I<PillarApi>();
      final cat = await api.catalog();
      if (cat.entries.isEmpty) {
        setState(() {
          _catalog = [];
          _loading = false;
        });
        return;
      }
      final selected = _selected ??
          cat.entries.firstWhere((e) => e.subject == 'Science',
              orElse: () => cat.entries.first);
      _catalog = cat.entries;
      _selected = selected;
    } catch (e) {
      setState(() {
        _error = '$e';
        _loading = false;
      });
      return;
    }
    await _loadChaptersFor(_selected!);
  }

  Future<void> _select(CatalogEntry e) async {
    setState(() {
      _selected = e;
      _loading = true;
    });
    await _loadChaptersFor(e);
  }

  Future<void> _loadChaptersFor(CatalogEntry selected) async {
    try {
      final chapters = await GetIt.I<PillarApi>().chapters(selected.subject, selected.grade);
      setState(() {
        _chapters = chapters;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = '$e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final covered = _chapters.where((c) => c.questionCount > 0).length;
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Syllabus Coverage'),
        actions: [IconButton(tooltip: 'Refresh', onPressed: _load, icon: const Icon(Icons.refresh))],
      ),
      body: _loading && _chapters.isEmpty
          ? const LoadingIndicator(message: 'Loading syllabus…')
          : _error != null && _chapters.isEmpty
              ? ErrorDisplay(message: _error!, onRetry: _load)
              : Column(
                  children: [
                    if (_catalog.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                        child: DropdownButtonFormField<String>(
                          initialValue: '${_selected?.subject}|${_selected?.grade}',
                          decoration: const InputDecoration(
                              labelText: 'Subject', isDense: true),
                          items: _catalog
                              .map((e) => DropdownMenuItem(
                                    value: '${e.subject}|${e.grade}',
                                    child: Text('${e.subject} — Class ${e.grade}'),
                                  ))
                              .toList(),
                          onChanged: (v) {
                            if (v == null) return;
                            _select(_catalog
                                .firstWhere((e) => '${e.subject}|${e.grade}' == v));
                          },
                        ),
                      ),
                    // Hidden (not shown as a misleading "0/0") when this subject has
                    // no chapter-level tagging at all -- the empty-state message
                    // below already explains the real per-subject question count.
                    if (_selected != null && _chapters.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: AppCard(
                          child: Row(
                            children: [
                              ProgressRing(
                                progress: covered / _chapters.length,
                                size: 56,
                                child: Text('$covered/${_chapters.length}',
                                    style: const TextStyle(
                                        fontSize: 11, fontWeight: FontWeight.w700)),
                              ),
                              const Gap(16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Chapters with question coverage',
                                        style: theme.textTheme.titleSmall
                                            ?.copyWith(fontWeight: FontWeight.w600)),
                                    const Gap(4),
                                    Text(
                                      '${_selected!.questionCount} questions from CBSE board papers',
                                      style: theme.textTheme.bodySmall,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    Expanded(
                      child: _loading
                          ? const LoadingIndicator()
                          : _chapters.isEmpty
                              // Real dead end found in front of a real school demo:
                              // chapter-level tagging in the bundled corpus only
                              // exists for Science today (a real, disclosed
                              // extraction gap -- see assessment_create_page.dart's
                              // matching fix). Every other subject used to render a
                              // blank list under a "0/0" ring with zero explanation,
                              // which reads as "the app is broken/empty", not as a
                              // real, honest limitation. Leads with the real number
                              // that IS available (whole-subject question count),
                              // not the absence.
                              ? Padding(
                                  padding: const EdgeInsets.all(24),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.menu_book_outlined,
                                          size: 40, color: theme.colorScheme.onSurfaceVariant),
                                      const Gap(12),
                                      Text(
                                        '${_selected?.questionCount ?? 0} real questions are ready to use for '
                                        '${_selected?.subject ?? "this subject"}',
                                        style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                                        textAlign: TextAlign.center,
                                      ),
                                      const Gap(6),
                                      Text(
                                        'A chapter-by-chapter breakdown isn\'t available for this subject yet -- '
                                        'New Assessment can still draw from the full question bank above.',
                                        style: theme.textTheme.bodySmall
                                            ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                                        textAlign: TextAlign.center,
                                      ),
                                    ],
                                  ),
                                )
                              : ListView.builder(
                                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                                  itemCount: _chapters.length,
                                  itemBuilder: (context, i) =>
                                      _chapterTile(context, theme, _chapters[i]),
                                ),
                    ),
                  ],
                ),
    );
  }

  Widget _chapterTile(BuildContext context, ThemeData theme, ChapterEntry c) {
    final empty = c.questionCount == 0;
    return AppCard(
      // Real dead end found on-device: this used to send every chapter tap
      // to the generic, unfiltered Question Bank regardless of which
      // chapter was tapped -- ChapterDetailPage (grouped by mark value,
      // real per-chapter question list) existed and was routed, but
      // nothing in the app ever navigated to it.
      onTap: empty || _selected == null
          ? null
          : () => context.push(
                '/syllabus/chapter/${c.chapterId}',
                extra: {
                  'subject': _selected!.subject,
                  'grade': _selected!.grade,
                  'chapterName': c.chapterName,
                },
              ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: empty
                  ? theme.colorScheme.surfaceContainerHighest
                  : theme.colorScheme.primaryContainer,
              shape: BoxShape.circle,
            ),
            child: Icon(
              empty ? Icons.remove : Icons.menu_book,
              size: 20,
              color: empty
                  ? theme.colorScheme.onSurfaceVariant
                  : theme.colorScheme.onPrimaryContainer,
            ),
          ),
          const Gap(14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(c.chapterName,
                    style: theme.textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.w600)),
                const Gap(3),
                Text(
                  empty
                      ? 'No questions ingested yet — coverage gap'
                      : '${c.questionCount} questions · marks ${c.marksAvailable.join(", ")}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: empty
                        ? theme.colorScheme.error
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          if (!empty) ChipTag(label: '${c.questionCount}'),
        ],
      ),
    );
  }
}
