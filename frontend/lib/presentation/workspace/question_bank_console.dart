import 'package:flutter/material.dart';

import '../../core/session/current_session.dart';
import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';

/// The question bank as the school sees it: coverage class by class, subject
/// by subject, chapter by chapter and topic by topic, each answer's trust tier
/// (published by CBSE/NCERT, or checked: grounded in the textbook or solved
/// twice), and -- for the principal and qbank_review admins -- the queue of
/// checked answers to approve or reject for this school.
class QuestionBankConsolePage extends StatefulWidget {
  final bool canReview;
  const QuestionBankConsolePage({super.key, this.canReview = false});

  @override
  State<QuestionBankConsolePage> createState() => _QuestionBankConsolePageState();
}

class _QuestionBankConsolePageState extends State<QuestionBankConsolePage> {
  @override
  Widget build(BuildContext context) {
    final review = widget.canReview || CurrentSession.role == 'principal';
    return DefaultTabController(
      length: review ? 2 : 1,
      child: Scaffold(
        appBar: AppBar(
          title: Text(tr('Question bank')),
          bottom: TabBar(tabs: [
            Tab(text: tr('Coverage')),
            if (review) Tab(text: tr('Review answers')),
          ]),
        ),
        body: TabBarView(children: [
          const _Coverage(),
          if (review) const _ReviewQueue(),
        ]),
      ),
    );
  }
}

class _Coverage extends StatefulWidget {
  const _Coverage();

  @override
  State<_Coverage> createState() => _CoverageState();
}

class _CoverageState extends State<_Coverage> {
  int? _grade;
  String? _subject;
  late Future<Map<String, dynamic>> _future = _fetch();

  Future<Map<String, dynamic>> _fetch() => Ops.map('/qbank/coverage-map', query: {
        if (_grade != null) 'grade': _grade,
        if (_subject != null) 'subject': _subject,
      });

  void _reload() => setState(() { _future = _fetch(); });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final d = snap.data!;
        final grades = (d['grades'] as List).cast<int>().where((g) => g >= 1 && g <= 10).toList();
        final subjects = (d['subjects'] as List).cast<Map>();
        return ListView(padding: const EdgeInsets.all(16), children: [
          Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
            DropdownButton<int?>(
              value: _grade,
              hint: Text(tr('All classes')),
              items: [
                DropdownMenuItem(value: null, child: Text(tr('All classes'))),
                for (final g in grades) DropdownMenuItem(value: g, child: Text('${tr('Class')} $g')),
              ],
              onChanged: (g) {
                _grade = g;
                _subject = null;
                _reload();
              },
            ),
            if (d['pendingReview'] != null && (d['pendingReview'] as int) > 0)
              Chip(label: Text('${d['pendingReview']} ${tr('answers to review')}')),
          ]),
          const SizedBox(height: 8),
          if (subjects.isEmpty)
            EmptyState(icon: Icons.menu_book_outlined, title: tr('No questions yet'),
                message: tr('This class has no questions in the bank yet.')),
          for (final s in subjects) _SubjectCard(s: Map<String, dynamic>.from(s), theme: theme),
        ]);
      },
    );
  }
}

class _SubjectCard extends StatelessWidget {
  final Map<String, dynamic> s;
  final ThemeData theme;
  const _SubjectCard({required this.s, required this.theme});

  @override
  Widget build(BuildContext context) {
    final chapters = (s['chapters'] as List).cast<Map>();
    final thin = (s['thinTopics'] as List).cast<String>();
    return AppCard(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${tr('Class')} ${s['grade']} · ${s['subject']}', style: theme.textTheme.titleMedium),
        const SizedBox(height: 4),
        Text('${s['questions']} ${tr('questions')} · ${s['published']} ${tr('published answers')} · '
            '${s['checked']} ${tr('checked answers')} · ${s['generated']} ${tr('written for topics')}',
            style: theme.textTheme.bodySmall),
        for (final c in chapters)
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: Text('${c['chapterName']}'),
            subtitle: Text('${c['questions']} · ${c['published']} ${tr('published')} · ${c['checked']} ${tr('checked')}'),
            children: [
              for (final t in (c['topics'] as List).cast<Map>())
                ListTile(
                  dense: true,
                  title: Text('${t['topic']}'),
                  trailing: Text('${t['questions']}',
                      style: TextStyle(color: (t['questions'] as int) < 3 ? theme.colorScheme.error : null)),
                ),
            ],
          ),
        if (thin.isNotEmpty) ...[
          const SizedBox(height: 6),
          Text('${tr('Thin topics')}: ${thin.take(8).join('; ')}${thin.length > 8 ? ' ...' : ''}',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error)),
        ],
      ]),
    );
  }
}

class _ReviewQueue extends StatefulWidget {
  const _ReviewQueue();

  @override
  State<_ReviewQueue> createState() => _ReviewQueueState();
}

class _ReviewQueueState extends State<_ReviewQueue> {
  String _status = 'pending';
  int? _grade;
  late Future<Map<String, dynamic>> _future = _fetch();

  Future<Map<String, dynamic>> _fetch() => Ops.map('/qbank/review-queue', query: {
        'status': _status,
        'limit': 50,
        if (_grade != null) 'grade': _grade,
      });

  void _reload() => setState(() { _future = _fetch(); });

  Future<void> _decide(String id, String decision) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await Ops.post('/qbank/review/$id', body: {'decision': decision});
      _reload();
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: serverErrorMessage(snap.error!), onRetry: _reload);
        final d = snap.data!;
        final counts = Map<String, dynamic>.from(d['counts'] as Map);
        final items = (d['items'] as List).cast<Map>();
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text(tr('Answers no board published: each rests on the textbook sentences shown, or on two agreeing '
              'solutions. Approve to mark it verified for your school; reject to keep it out of your papers and '
              'homework.'), style: theme.textTheme.bodySmall),
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final s in const ['pending', 'approved', 'rejected'])
              ChoiceChip(
                label: Text('${tr(s[0].toUpperCase() + s.substring(1))} (${counts[s] ?? 0})'),
                selected: _status == s,
                onSelected: (_) {
                  _status = s;
                  _reload();
                },
              ),
            DropdownButton<int?>(
              value: _grade,
              hint: Text(tr('All classes')),
              items: [
                DropdownMenuItem(value: null, child: Text(tr('All classes'))),
                for (var g = 1; g <= 10; g++) DropdownMenuItem(value: g, child: Text('${tr('Class')} $g')),
              ],
              onChanged: (g) {
                _grade = g;
                _reload();
              },
            ),
          ]),
          if (items.isEmpty)
            Padding(padding: const EdgeInsets.only(top: 24), child: Text(tr('Nothing here.'))),
          for (final it in items)
            AppCard(
              margin: const EdgeInsets.only(top: 12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${tr('Class')} ${it['grade']} · ${it['subject']} · ${it['chapter']} · ${it['topic']}',
                    style: theme.textTheme.labelMedium),
                const SizedBox(height: 6),
                Text('${it['stem']}', style: theme.textTheme.bodyLarge),
                const SizedBox(height: 6),
                Text('${tr('Answer')}: ${it['modelAnswer']}', style: theme.textTheme.bodyMedium),
                for (final e in (it['evidence'] as List).cast<Map>())
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text('“${e['quote']}”${e['page'] != null ? ' (p. ${e['page']})' : ''}',
                        style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic)),
                  ),
                const SizedBox(height: 6),
                Text('${it['provenance'] == 'two_model_solved' ? tr('Solved twice, answers agree') : tr('From the textbook')}'
                    ' · ${it['source'] == 'ai_generated' ? tr('written for this topic') : tr('book exercise')}',
                    style: theme.textTheme.bodySmall),
                if (_status == 'pending' || it['decision'] != null)
                  Row(children: [
                    TextButton.icon(onPressed: () => _decide(it['id'] as String, 'approved'),
                        icon: const Icon(Icons.check), label: Text(tr('Approve'))),
                    TextButton.icon(onPressed: () => _decide(it['id'] as String, 'rejected'),
                        icon: const Icon(Icons.close), label: Text(tr('Reject'))),
                  ]),
              ]),
            ),
        ]);
      },
    );
  }
}
