import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';

import '../../../data/datasources/api/pillar_api.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

/// Every question in the bank for one chapter, grouped by mark value —
/// how a teacher decides what a chapter can actually be assessed with.
class ChapterDetailPage extends StatefulWidget {
  final String chapterId;
  final String subject;
  final int grade;
  final String chapterName;

  const ChapterDetailPage({
    super.key,
    required this.chapterId,
    this.subject = 'Science',
    this.grade = 10,
    this.chapterName = '',
  });

  @override
  State<ChapterDetailPage> createState() => _ChapterDetailPageState();
}

class _ChapterDetailPageState extends State<ChapterDetailPage> {
  List<BankQuestion> _questions = [];
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
      final qs = await GetIt.I<PillarApi>().searchQuestions(
        subject: widget.subject,
        grade: widget.grade,
        chapterIds: [widget.chapterId],
        limit: 300,
      );
      setState(() {
        _questions = qs;
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
    final byMarks = <int, List<BankQuestion>>{};
    for (final q in _questions) {
      byMarks.putIfAbsent(q.marks, () => []).add(q);
    }
    final markKeys = byMarks.keys.toList()..sort();

    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: Text(widget.chapterName.isEmpty
            ? widget.chapterId.replaceAll('-', ' ')
            : widget.chapterName),
      ),
      body: _loading
          ? const LoadingIndicator(message: 'Loading chapter questions…')
          : _error != null
              ? ErrorDisplay(message: _error!, onRetry: _load)
              : _questions.isEmpty
                  ? const EmptyState(
                      icon: Icons.inbox_outlined,
                      title: 'No questions for this chapter',
                      message:
                          'Nothing has been ingested for it yet — this is a coverage gap.',
                    )
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        AppCard(
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('${_questions.length} questions available',
                                        style: theme.textTheme.titleMedium?.copyWith(
                                            fontWeight: FontWeight.w700)),
                                    const Gap(4),
                                    Text('${widget.subject} · Class ${widget.grade}',
                                        style: theme.textTheme.bodySmall),
                                  ],
                                ),
                              ),
                              Wrap(
                                spacing: 6,
                                children: markKeys
                                    .map((m) => ChipTag(
                                        label: '${byMarks[m]!.length} × ${m}m'))
                                    .toList(),
                              ),
                            ],
                          ),
                        ),
                        for (final m in markKeys) ...[
                          SectionHeader(
                            title: '$m mark${m == 1 ? "" : "s"}',
                            subtitle: '${byMarks[m]!.length} questions',
                          ),
                          ...byMarks[m]!.map((q) => AppCard(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(children: [
                                      ChipTag(label: q.difficulty),
                                      const Gap(6),
                                      ChipTag(label: q.bloomLevel),
                                    ]),
                                    const Gap(8),
                                    SelectableText(q.stem,
                                        style: theme.textTheme.bodyMedium),
                                  ],
                                ),
                              )),
                        ],
                      ],
                    ),
    );
  }
}
