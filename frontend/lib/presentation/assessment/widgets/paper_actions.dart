import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';

import '../../../core/local_engine/local_api_client.dart' show LocalApiClient, editableAssessmentStatuses;
import '../../../core/session/current_session.dart';
import '../../../data/datasources/api/api_client.dart';
import '../../../data/datasources/api/api_error.dart';
import '../../../domain/entities/entities.dart';
import '../../workspace/ops_api.dart';
import '../../workspace/strings.dart';

/// What the signed-in person may do with one saved paper, by the server's
/// rules (QA P-09, P-22). Whatever is hidden here the server refuses anyway;
/// a button that can only answer 403 is not offered.
///
///  * change it -- swap, pick or remove a question, rename it: its author,
///    the principal, or a teacher holding the exams grant;
///  * delete it, or ask a colleague to review it: its author or the principal;
///  * approve and lock it: the principal or the exams admin.
///
/// On the offline build every paper on the device is its user's own.
class PaperPermissions {
  final bool author;
  final bool principal;
  final bool examsAdmin;

  const PaperPermissions({this.author = false, this.principal = false, this.examsAdmin = false});

  factory PaperPermissions.of(Assessment a, {Set<String> grants = const {}}) {
    final role = CurrentSession.role;
    return PaperPermissions(
      author: onDevice || (a.teacherId.isNotEmpty && a.teacherId == CurrentSession.userId),
      principal: role == 'principal',
      examsAdmin: role == 'teacher' && grants.contains('exams'),
    );
  }

  /// The on-device engine is the ApiClient (the offline Android build).
  static bool get onDevice {
    final sl = GetIt.instance;
    if (sl.isRegistered<ApiClient>()) return sl<ApiClient>() is LocalApiClient;
    return const bool.fromEnvironment('ACADEMICOS_OFFLINE', defaultValue: false);
  }

  bool get mayChange => author || principal || examsAdmin;
  bool get mayDelete => author || principal;
  bool get mayAskForReview => author || principal;
  bool get mayApprove => principal || examsAdmin;
}

/// Whether [a]'s questions and title can still change: until it is approved.
bool paperIsEditable(Assessment a) => editableAssessmentStatuses.contains(a.status);

/// The paper's marks as printed: the server's `paperMarks` (the total after
/// any question was removed) when it sent one, else the blueprint's.
int paperMarksOf(Assessment a) {
  final printed = a.metadata['paperMarks'];
  return printed is num ? printed.toInt() : a.blueprint.totalMarks;
}

/// "Meera Iyer · 1 Oct 2026": who made the paper and when, from the list's
/// `metadata.authorName` (empty when the server sent none).
String paperByline(Assessment a) {
  final author = '${a.metadata['authorName'] ?? ''}'.trim();
  final date = shortDate(a.createdAt.toLocal());
  return author.isEmpty ? date : '$author · $date';
}

const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/// "1 Oct 2026".
String shortDate(DateTime d) => '${d.day} ${_months[d.month - 1]} ${d.year}';

/// Asks for a new title and saves it (PUT /assessments/{id} with the whole
/// assessment). Returns the renamed assessment, or null when the teacher
/// cancelled or the server refused -- the refusal (409 once the paper is
/// locked) is shown in a snackbar in the server's words.
///
/// The PUT carries the assessment as the server holds it now, read just
/// before: the copy a screen holds can predate a swap or a removal, whose
/// question list and edit log the PUT would otherwise put back. The list's
/// display-only fields (`authorName`, `paperMarks`) are not stored.
Future<Assessment?> renamePaper(BuildContext context, Assessment a) async {
  final title = await showDialog<String>(context: context, builder: (_) => _RenameDialog(current: a.title));
  if (title == null || title == a.title || !context.mounted) return null;
  try {
    final api = GetIt.I<ApiClient>();
    final current = await api.getAssessment(a.id);
    final metadata = Map<String, dynamic>.from(current.metadata)
      ..remove('authorName')
      ..remove('paperMarks');
    final renamed = await api.updateAssessment(
        a.id, current.copyWith(title: title, metadata: metadata, updatedAt: DateTime.now()));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Renamed to "$title"')));
    }
    return renamed;
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not rename it: ${serverErrorMessage(e)}')));
    }
    return null;
  }
}

/// Asks first, then deletes the paper (DELETE /assessments/{id}). True once
/// it is gone; a refusal (409 once it is approved or under review) is shown
/// in the server's words and leaves it where it was.
Future<bool> deletePaper(BuildContext context, Assessment a) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text('Delete "${a.title}"?'),
      content: const Text('The paper, its sets and its answer key are deleted for everyone. '
          'This cannot be undone.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
        FilledButton(
          key: const ValueKey('confirm-delete-paper'),
          style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
          onPressed: () => Navigator.pop(ctx, true),
          child: const Text('Delete'),
        ),
      ],
    ),
  );
  if (ok != true || !context.mounted) return false;
  try {
    await GetIt.I<ApiClient>().deleteAssessment(a.id);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Deleted "${a.title}"')));
    }
    return true;
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not delete it: ${serverErrorMessage(e)}')));
    }
    return false;
  }
}

class _RenameDialog extends StatefulWidget {
  final String current;
  const _RenameDialog({required this.current});

  @override
  State<_RenameDialog> createState() => _RenameDialogState();
}

class _RenameDialogState extends State<_RenameDialog> {
  late final _title = TextEditingController(text: widget.current);

  @override
  void dispose() {
    _title.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final text = _title.text.trim();
    void save() => Navigator.pop(context, text);
    return AlertDialog(
      title: const Text('Rename paper'),
      content: SizedBox(
        width: 420,
        child: TextField(
          key: const ValueKey('rename-paper-title'),
          controller: _title,
          autofocus: true,
          maxLength: 120,
          decoration: const InputDecoration(labelText: 'Title', hintText: 'Class 10 Maths Half-Yearly 2026'),
          onChanged: (_) => setState(() {}),
          onSubmitted: (_) {
            if (text.isNotEmpty) save();
          },
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(tr('Cancel'))),
        FilledButton(onPressed: text.isEmpty ? null : save, child: const Text('Save')),
      ],
    );
  }
}

/// Asks a colleague to review a paper (EX-6), from the paper's own page.
/// Returns true once the request is sent; the paper is then "In review".
/// The author is never offered as their own reviewer -- the server refuses
/// that (QA P-22).
Future<bool> requestReview(BuildContext context, String assessmentId, {String? authorId}) async {
  final List<Map<String, dynamic>> staff;
  try {
    staff = (await Ops.list('/staff')).where((s) => s['id'] != authorId).toList();
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Could not list your colleagues: ${serverErrorMessage(e)}')));
    }
    return false;
  }
  if (!context.mounted) return false;
  String? reviewer;
  final note = TextEditingController();
  final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, set) => AlertDialog(
    title: const Text('Send for review'),
    content: SizedBox(width: 420, child: Column(mainAxisSize: MainAxisSize.min, children: [
      DropdownButtonFormField<String>(
        key: const ValueKey('review-reviewer'),
        initialValue: reviewer,
        decoration: const InputDecoration(labelText: 'Reviewer (HOD or a colleague)'),
        items: [for (final s in staff) DropdownMenuItem(value: s['id'] as String, child: Text(s['name'] as String))],
        onChanged: (v) => set(() => reviewer = v),
      ),
      TextField(controller: note, decoration: const InputDecoration(labelText: 'Note (optional)')),
    ])),
    actions: [
      TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(tr('Cancel'))),
      FilledButton(onPressed: reviewer == null ? null : () => Navigator.pop(ctx, true), child: const Text('Send')),
    ],
  )));
  if (ok != true || !context.mounted) return false;
  try {
    await Ops.post('/assessments/$assessmentId/review-request',
        body: {'reviewerId': reviewer, if (note.text.trim().isNotEmpty) 'note': note.text.trim()});
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Sent for review; the reviewer has been told')));
    }
    return true;
  } catch (e) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    return false;
  }
}
