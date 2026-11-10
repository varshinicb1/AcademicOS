/// Server values as people read them (QA S-23, 2026-10-01): the screens
/// showed "last used 2026-10-01T21:27:20.432778+00:00", "full_day",
/// "(classes 10)" and "1 papers".
library;

import '../workspace/strings.dart';

const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

String _two(int n) => n.toString().padLeft(2, '0');

/// "2026-10-01" (or a full timestamp) -> "1 Oct 2026"; anything that is not
/// a date comes back as it was.
String readableDate(String iso) {
  final d = DateTime.tryParse(iso);
  return d == null ? iso : '${d.day} ${_months[d.month - 1]} ${d.year}';
}

/// A server timestamp in this device's time: "today at 21:27",
/// "yesterday at 09:05", or "1 Oct 2026 at 21:27". Null is [never].
String readableDateTime(String? iso, {DateTime? now, String never = 'never'}) {
  if (iso == null || iso.isEmpty) return never;
  final parsed = DateTime.tryParse(iso);
  if (parsed == null) return iso;
  final d = parsed.toLocal();
  final today = now ?? DateTime.now();
  final days = DateTime(today.year, today.month, today.day).difference(DateTime(d.year, d.month, d.day)).inDays;
  final time = '${_two(d.hour)}:${_two(d.minute)}';
  if (days == 0) return 'today at $time';
  if (days == 1) return 'yesterday at $time';
  return '${d.day} ${_months[d.month - 1]} ${d.year} at $time';
}

/// The clock time of a server timestamp, in this device's time: "21:27".
String readableTime(String iso) {
  final d = DateTime.tryParse(iso)?.toLocal();
  return d == null ? iso : '${_two(d.hour)}:${_two(d.minute)}';
}

/// "1 paper", "2 papers"; [many] when the plural is not [one] + "s". The noun
/// goes through [tr]: Hindi counts read "3 पीरियड" (R-B5).
String plural(int n, String one, [String? many]) => '$n ${tr(n == 1 ? one : (many ?? '${one}s'))}';

/// "class 10", "classes 9 and 10", "classes 6, 7 and 8".
String classesLabel(List<Object?> grades) {
  final g = [for (final x in grades) '$x'];
  if (g.isEmpty) return 'every class';
  if (g.length == 1) return 'class ${g.single}';
  return 'classes ${g.sublist(0, g.length - 1).join(', ')} and ${g.last}';
}

/// "full_day" -> "Full day", "second_fourth" -> "Second fourth": the last
/// resort for an enum no screen has a word for yet.
String humanWord(String raw) {
  final t = raw.replaceAll('_', ' ').trim();
  return t.isEmpty ? t : t[0].toUpperCase() + t.substring(1);
}

/// A seeded book's title without the source note the seed puts after it:
/// "CBSE Class 10 Science — official curriculum (CBSE Curriculum 2025-26,
/// Science_Sec_2025-26.pdf, ...)" -> "CBSE Class 10 Science — official
/// curriculum". The stored title keeps the note (re-seeding finds the book by
/// it); a school's own book titles come back as they were.
String bookName(String title) {
  const mark = '— official curriculum (';
  final at = title.indexOf(mark);
  return at < 0 || !title.endsWith(')') ? title : title.substring(0, at + mark.length - 2);
}

/// A leave request's kind, as the leave form names it.
String leaveKind(String kind) => switch (kind) {
      'full_day' => 'Full day',
      'first_half' => '1st half',
      'second_half' => '2nd half',
      'periods' => 'Some periods',
      _ => humanWord(kind),
    };

/// A leave request's state.
String leaveStatus(String status) => switch (status) {
      'pending' => 'Waiting for approval',
      'approved' => 'Approved',
      'rejected' => 'Not approved',
      'cancelled' => 'Cancelled',
      _ => humanWord(status),
    };
