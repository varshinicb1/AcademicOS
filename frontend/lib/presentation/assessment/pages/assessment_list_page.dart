import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../domain/entities/entities.dart';
import '../../blocs/assessment_bloc.dart';
import '../../shared/widgets/common_widgets.dart';
import '../../shared/widgets/shell.dart';

const _teacherId = 'teacher_1';

class AssessmentListPage extends StatefulWidget {
  const AssessmentListPage({super.key});

  @override
  State<AssessmentListPage> createState() => _AssessmentListPageState();
}

class _AssessmentListPageState extends State<AssessmentListPage> {
  @override
  void initState() {
    super.initState();
    context.read<AssessmentBloc>().add(const AssessmentEvent.loadAssessments(_teacherId));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: const Text('Assessments'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/assessment/create'),
          ),
        ],
      ),
      body: BlocBuilder<AssessmentBloc, AssessmentState>(
        builder: (context, state) {
          return state.maybeWhen(
            loading: () => const Center(child: CircularProgressIndicator()),
            assessmentsLoaded: (assessments) => _buildList(context, assessments),
            error: (message) => ErrorDisplay(
              message: message,
              onRetry: () => context
                  .read<AssessmentBloc>()
                  .add(const AssessmentEvent.loadAssessments(_teacherId)),
            ),
            // Any other state (e.g. left over from the create flow) isn't a
            // list result — re-fetch rather than rendering a misleading empty list.
            orElse: () {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (mounted) {
                  context
                      .read<AssessmentBloc>()
                      .add(const AssessmentEvent.loadAssessments(_teacherId));
                }
              });
              return const Center(child: CircularProgressIndicator());
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/assessment/create'),
        icon: const Icon(Icons.assignment_add),
        label: const Text('New Assessment'),
      ),
    );
  }

  Widget _buildList(BuildContext context, List<Assessment> assessments) {
    if (assessments.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'No assessments yet.\nTap "New Assessment" to build one with the AI Assessment Designer.',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: assessments.length,
      itemBuilder: (context, index) {
        final a = assessments[index];
        return AppCard(
          onTap: () => context.push('/assessment/${a.id}', extra: {'assessment': a}),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(a.title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Text('${a.subject} · Grade ${a.grade} · ${a.blueprint.totalMarks} marks',
                        style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
              ChipTag(label: a.status.name),
            ],
          ),
        );
      },
    );
  }
}
