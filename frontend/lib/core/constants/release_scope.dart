import '../../data/datasources/api/pillar_api.dart' show CatalogEntry;

/// The classes this release serves: 1-10 (requirements v3; 6-10 until
/// 2026-09-29, and 11-12 stay out, the user 2026-09-23: "skip 11 and 12 for
/// now"). A class is still only offered, browsed or counted where the bank
/// holds questions for it: [releaseEntries] here, and the builder's
/// `offeredGrades`.
///
/// One list for every screen: the builder, the principal's insights card and
/// the browse screens each kept their own, and the browse screens' was none
/// -- the live Question Bank and Syllabus pages listed class 12's 510
/// questions over 35 subjects (audit D22, 2026-09-27).
const releaseGrades = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

/// The catalog rows a screen of this release may show: its classes, and only
/// pairs with questions to show.
List<CatalogEntry> releaseEntries(Iterable<CatalogEntry> entries) => [
      for (final e in entries)
        if (releaseGrades.contains(e.grade) && e.questionCount > 0) e,
    ];
