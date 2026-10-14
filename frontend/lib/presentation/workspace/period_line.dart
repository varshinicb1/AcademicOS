// The words for one period of a day (`GET /curriculum/my-day` rows) that the
// teacher's My day and the student's Today both show: its clock time, its
// room, and the next period's countdown. Both pages showed neither time nor
// room (v3 audit N-4-2).
import 'strings.dart';

/// "08:00–08:45", or '' when the school has no bell schedule.
String periodTime(Map r) {
  final start = r['startTime'] as String?;
  final end = r['endTime'] as String?;
  if (start == null) return '';
  return end == null ? start : '$start–$end';
}

/// The time, then the room when one is booked: "08:00–08:45 · Physics Lab".
String periodWhenWhere(Map r) =>
    [periodTime(r), if (r['roomName'] != null) r['roomName'] as String].where((s) => s.isNotEmpty).join(' · ');

/// Minutes from `now` to "HH:MM" on the same day (negative once it passed).
int? minutesUntil(String? hhmm, DateTime now) {
  if (hhmm == null || !hhmm.contains(':')) return null;
  final parts = hhmm.split(':');
  final h = int.tryParse(parts[0]);
  final m = int.tryParse(parts[1]);
  if (h == null || m == null) return null;
  return h * 60 + m - (now.hour * 60 + now.minute);
}

/// "Next: period 2 at 09:00 (in 25 min)" for the first period still to
/// start today, or null when none is left or the day has no times. Lost and
/// away periods are not "next" for anyone.
String? nextPeriodLine(List<Map> rows, DateTime now, {String Function(Map r)? what}) {
  Map? next;
  int? inMinutes;
  for (final r in rows) {
    if (r['kind'] == 'lost' || r['kind'] == 'away') continue;
    final m = minutesUntil(r['startTime'] as String?, now);
    if (m == null || m < 0) continue;
    if (inMinutes == null || m < inMinutes) {
      next = r;
      inMinutes = m;
    }
  }
  if (next == null || inMinutes == null) return null;
  final label = what?.call(next);
  // Whole sentences with their values (trf), not words joined around them:
  // "in 25 min" reads "25 मिनट में" in Hindi.
  final when = inMinutes == 0
      ? tr('now')
      : inMinutes < 60
          ? trf('in {m} min', {'m': inMinutes})
          : trf('in {h} h {m} min', {'h': inMinutes ~/ 60, 'm': inMinutes % 60});
  final head = trf('Next: period {n} at {time}', {'n': next['period'], 'time': next['startTime']});
  return '$head${label == null || label.isEmpty ? '' : ' · $label'} ($when)';
}
