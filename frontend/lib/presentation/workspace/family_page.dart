import 'package:flutter/material.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'report_cards_page.dart';
import 'student_pages.dart';
import 'strings.dart';

const _weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/// A parent's view (SA-6): each linked child's week, homework status and
/// progress, and the parental consent that lets the school process their
/// work -- given or withdrawn here, from the parent's own account.
class FamilyPage extends StatefulWidget {
  const FamilyPage({super.key});

  @override
  State<FamilyPage> createState() => _FamilyPageState();
}

class _FamilyPageState extends State<FamilyPage> {
  late Future<List<Map<String, dynamic>>> _future = Ops.list('/my-children');

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return Scaffold(appBar: AppBar(title: Text(tr('My children'))), body: const LoadingIndicator());
        }
        if (snap.hasError) {
          return Scaffold(appBar: AppBar(title: Text(tr('My children'))),
              body: ErrorDisplay(message: snap.error.toString(),
                  onRetry: () => setState(() { _future = Ops.list('/my-children'); })));
        }
        final kids = snap.data!;
        if (kids.isEmpty) {
          return Scaffold(appBar: AppBar(title: Text(tr('My children'))),
              body: const EmptyState(icon: Icons.family_restroom, title: 'No child linked yet',
                  message: 'Ask the school to link your account to your child.'));
        }
        return DefaultTabController(
          length: kids.length,
          child: Scaffold(
            appBar: AppBar(
              title: Text(tr('My children')),
              bottom: kids.length > 1
                  ? TabBar(tabs: [for (final k in kids) Tab(text: k['name'] as String)])
                  : null,
            ),
            body: TabBarView(children: [
              for (final k in kids)
                _ChildView(child: k, onChanged: () => setState(() { _future = Ops.list('/my-children'); })),
            ]),
          ),
        );
      },
    );
  }
}

class _ChildView extends StatelessWidget {
  final Map<String, dynamic> child;
  final VoidCallback onChanged;
  const _ChildView({required this.child, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final id = child['studentId'] as String;
    return DefaultTabController(
      length: 4,
      child: Column(children: [
        ListTile(
          title: Text(child['name'] as String, style: Theme.of(context).textTheme.titleMedium),
          subtitle: Text(child['sectionName'] != null ? 'Class ${child['sectionName']}' : 'Not placed in a class yet'),
          trailing: _ConsentChip(studentId: id, status: child['consent'] as String, onChanged: onChanged),
        ),
        // EX-8: this term's report card.
        Align(alignment: Alignment.centerLeft, child: TextButton.icon(
          key: ValueKey('child-report-card-$id'),
          onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(
              builder: (_) => StudentReportCardPage(studentId: id, name: child['name'] as String))),
          icon: const Icon(Icons.grading_outlined),
          label: Text(tr('Report card')),
        )),
        const TabBar(tabs: [Tab(text: 'Week'), Tab(text: 'Today'), Tab(text: 'Homework'), Tab(text: 'Progress')]),
        Expanded(child: TabBarView(children: [
          _Week(studentId: id),
          _Today(studentId: id),
          _Homework(studentId: id, name: child['name'] as String,
              young: (child['grade'] as int?) != null && (child['grade'] as int) <= 5),
          LearningView(path: '/children/$id/learning'),
        ])),
      ]),
    );
  }
}

class _ConsentChip extends StatelessWidget {
  final String studentId;
  final String status;
  final VoidCallback onChanged;
  const _ConsentChip({required this.studentId, required this.status, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final granted = status == 'granted';
    return ActionChip(
      avatar: Icon(granted ? Icons.verified_user : Icons.gpp_maybe, size: 18,
          color: granted ? Colors.green : Theme.of(context).colorScheme.error),
      label: Text(granted ? 'Consent given' : 'Consent needed'),
      onPressed: () async {
        final ok = await showDialog<bool>(context: context, builder: (_) => AlertDialog(
          title: Text(granted ? 'Withdraw consent?' : 'Give consent'),
          content: Text(granted
              ? 'The school will not be able to mark or process your child\'s work in the app until you give consent again.'
              : 'You agree that the school may process your child\'s homework, tests and practice in this app to teach '
                'and assess them (Digital Personal Data Protection Act, 2023). You can withdraw at any time.'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: Text(tr('Cancel'))),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: Text(granted ? 'Withdraw' : 'I agree')),
          ],
        ));
        if (ok != true) return;
        try {
          if (granted) {
            await Ops.delete('/children/$studentId/consent');
          } else {
            await Ops.post('/children/$studentId/consent');
          }
          onChanged();
        } catch (e) {
          if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
        }
      },
    );
  }
}

class _Week extends StatelessWidget {
  final String studentId;
  const _Week({required this.studentId});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: Ops.map('/children/$studentId/timetable'),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: snap.error.toString());
        final entries = (snap.data!['entries'] as List).cast<Map>();
        if (entries.isEmpty) {
          return const EmptyState(icon: Icons.calendar_view_week, title: 'No timetable yet',
              message: 'The school has not published a timetable for this class.');
        }
        final byDay = <int, List<Map>>{};
        for (final e in entries) {
          byDay.putIfAbsent(e['dayOfWeek'] as int, () => []).add(e);
        }
        final names = Map<String, dynamic>.from(snap.data!['subjectNames'] as Map? ?? {});
        return ListView(padding: const EdgeInsets.all(16), children: [
          for (final day in byDay.keys.toList()..sort()) ...[
            Text(_weekdays[day], style: Theme.of(context).textTheme.titleSmall),
            Wrap(spacing: 6, runSpacing: 6, children: [
              for (final e in byDay[day]!..sort((a, b) => (a['period'] as int).compareTo(b['period'] as int)))
                Chip(label: Text('P${e['period']} ${names[e['subjectId']] ?? ''}')),
            ]),
            const SizedBox(height: 10),
          ],
        ]);
      },
    );
  }
}

class _Today extends StatelessWidget {
  final String studentId;
  const _Today({required this.studentId});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: Ops.map('/children/$studentId/day', query: {'date': isoDate(DateTime.now())}),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: snap.error.toString());
        final rows = (snap.data!['rows'] as List).cast<Map>();
        final names = Map<String, dynamic>.from(snap.data!['subjectNames'] as Map? ?? {});
        if (rows.isEmpty) {
          return const EmptyState(icon: Icons.weekend_outlined, title: 'No classes today',
              message: 'A holiday, a weekly off, or no timetable yet.');
        }
        const kinds = {
          'regular': 'As usual', 'substitute': 'Substitute teacher', 'supervised': 'Supervised period',
          'combined': 'Combined with another class', 'lost': 'Cancelled', 'uncovered': 'No teacher yet',
          'makeup': 'Make-up period',
        };
        return ListView(padding: const EdgeInsets.all(16), children: [
          for (final r in rows)
            ListTile(
              leading: CircleAvatar(child: Text('${r['period']}')),
              title: Text(names[r['subjectId']]?.toString() ?? ''),
              trailing: ChipTag(label: kinds[r['kind']] ?? r['kind']),
              subtitle: r['note'] != null ? Text(r['note']) : null,
            ),
        ]);
      },
    );
  }
}

class _Homework extends StatelessWidget {
  final String studentId;
  final String name;
  /// Classes 1-5: the parent does the homework with the child (SA-7).
  final bool young;
  const _Homework({required this.studentId, required this.name, required this.young});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: Ops.list('/children/$studentId/homework'),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
        if (snap.hasError) return ErrorDisplay(message: snap.error.toString());
        final items = snap.data!;
        if (items.isEmpty) {
          return const EmptyState(icon: Icons.assignment_turned_in_outlined, title: 'No homework',
              message: 'Homework the teachers set will appear here.');
        }
        return ListView(padding: const EdgeInsets.all(16), children: [
          if (young)
            Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(
                'In classes 1-5 you do the homework with $name: open one to answer it together.',
                style: Theme.of(context).textTheme.bodyMedium)),
          for (final h in items)
            HomeworkStatusTile(item: h, onTap: () => Navigator.of(context).push(MaterialPageRoute<void>(
                builder: (_) => HomeworkDetailPage(homeworkId: h['id'] as String, childId: studentId,
                    childName: name, young: young)))),
        ]);
      },
    );
  }
}
