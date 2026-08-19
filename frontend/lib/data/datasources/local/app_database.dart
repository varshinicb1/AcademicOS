import 'dart:convert';
import 'package:drift/drift.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

import 'connection/connection_io.dart'
    if (dart.library.js_interop) 'connection/connection_web.dart';

part 'app_database.g.dart';

@TableIndex(name: 'idx_assessments_teacher', columns: {#teacherId})
@TableIndex(name: 'idx_assessments_school', columns: {#schoolId})
@TableIndex(name: 'idx_assessments_status', columns: {#status})
@DataClassName('AssessmentRow')
class Assessments extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get schoolId => text()();
  TextColumn get teacherId => text()();
  TextColumn get title => text()();
  TextColumn get subject => text()();
  IntColumn get grade => integer()();
  TextColumn get chapterIds => text().map(const _StringListConverter())();
  TextColumn get blueprint => text().map(const _JsonConverter())();
  TextColumn get status => text()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  DateTimeColumn get scheduledAt => dateTime().nullable()();
  DateTimeColumn get completedAt => dateTime().nullable()();
  TextColumn get templateId => text().nullable()();
  TextColumn get metadata => text().map(const _JsonConverter()).withDefault(const Constant('{}'))();

  @override
  Set<Column> get primaryKey => {id};
}

@TableIndex(name: 'idx_questions_assessment', columns: {#assessmentId})
@DataClassName('QuestionRow')
class Questions extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get assessmentId => text().nullable()();
  TextColumn get questionBankId => text()();
  TextColumn get subject => text()();
  IntColumn get grade => integer()();
  TextColumn get chapterIds => text().map(const _StringListConverter())();
  TextColumn get competencyIds => text().map(const _StringListConverter())();
  TextColumn get bloomLevel => text()();
  TextColumn get difficulty => text()();
  TextColumn get type => text()();
  TextColumn get stem => text()();
  TextColumn get stemLatex => text().nullable()();
  TextColumn get parts => text().map(const _JsonConverter())();
  TextColumn get answerScheme => text().map(const _JsonConverter())();
  IntColumn get estimatedTimeMinutes => integer()();
  IntColumn get marks => integer()();
  TextColumn get language => text()();
  TextColumn get source => text()();
  RealColumn get qualityScore => real()();
  TextColumn get tags => text().map(const _StringListConverter())();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  TextColumn get metadata => text().map(const _JsonConverter()).withDefault(const Constant('{}'))();

  @override
  Set<Column> get primaryKey => {id};
}

@TableIndex(name: 'idx_answer_sheets_assessment', columns: {#assessmentId})
@TableIndex(name: 'idx_answer_sheets_student', columns: {#studentId})
@TableIndex(name: 'idx_answer_sheets_status', columns: {#status})
@DataClassName('AnswerSheetRow')
class AnswerSheets extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get assessmentId => text()();
  TextColumn get studentId => text()();
  TextColumn get studentName => text()();
  TextColumn get rollNumber => text()();
  TextColumn get pages => text().map(const _JsonConverter())();
  TextColumn get scanMetadata => text().map(const _JsonConverter())();
  TextColumn get responses => text().map(const _JsonConverter())();
  TextColumn get status => text()();
  DateTimeColumn get submittedAt => dateTime()();
  DateTimeColumn get scannedAt => dateTime()();
  DateTimeColumn get evaluatedAt => dateTime().nullable()();
  TextColumn get metadata => text().map(const _JsonConverter()).withDefault(const Constant('{}'))();

  @override
  Set<Column> get primaryKey => {id};
}

@TableIndex(name: 'idx_evaluations_answer_sheet', columns: {#answerSheetId})
@TableIndex(name: 'idx_evaluations_question', columns: {#questionId})
class Evaluations extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get answerSheetId => text()();
  TextColumn get questionId => text()();
  TextColumn get studentAnswer => text()();
  TextColumn get studentAnswerLatex => text().nullable()();
  TextColumn get studentAnswerImages => text().map(const _StringListConverter())();
  IntColumn get awardedMarks => integer()();
  IntColumn get maxMarks => integer()();
  RealColumn get percentage => real()();
  TextColumn get verdict => text()();
  TextColumn get markingPoints => text().map(const _JsonConverter())();
  TextColumn get rubricLevel => text().map(const _JsonConverter())();
  RealColumn get confidenceScore => real()();
  TextColumn get reasoning => text()();
  TextColumn get strengths => text().map(const _StringListConverter())();
  TextColumn get gaps => text().map(const _StringListConverter())();
  TextColumn get carelessErrors => text().map(const _StringListConverter())();
  IntColumn get estimatedTimeSpentSeconds => integer()();
  TextColumn get status => text()();
  DateTimeColumn get evaluatedAt => dateTime()();
  TextColumn get teacherComment => text().nullable()();
  IntColumn get teacherAdjustedMarks => integer().nullable()();
  TextColumn get metadata => text().map(const _JsonConverter()).withDefault(const Constant('{}'))();

  @override
  Set<Column> get primaryKey => {id};
}

@TableIndex(name: 'idx_mastery_student', columns: {#studentId})
class StudentMasteryTable extends Table {
  TextColumn get studentId => text()();
  TextColumn get schoolId => text()();
  TextColumn get grade => text()();
  TextColumn get concepts => text().map(const _JsonConverter())();
  TextColumn get chapters => text().map(const _JsonConverter())();
  TextColumn get subjects => text().map(const _JsonConverter())();
  TextColumn get summary => text().map(const _JsonConverter())();
  DateTimeColumn get lastUpdated => dateTime()();
  IntColumn get version => integer()();

  @override
  Set<Column> get primaryKey => {studentId};
}

@TableIndex(name: 'idx_practice_student', columns: {#studentId})
@TableIndex(name: 'idx_practice_status', columns: {#status})
@DataClassName('PracticeSessionRow')
class PracticeSessions extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get studentId => text()();
  TextColumn get conceptIds => text().map(const _StringListConverter())();
  TextColumn get type => text()();
  IntColumn get questionCount => integer()();
  IntColumn get durationMinutes => integer()();
  TextColumn get questions => text().map(const _JsonConverter())();
  TextColumn get status => text()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get startedAt => dateTime().nullable()();
  DateTimeColumn get completedAt => dateTime().nullable()();
  TextColumn get result => text().map(const _JsonConverter()).nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

@TableIndex(name: 'idx_reports_student', columns: {#studentId})
@TableIndex(name: 'idx_reports_assessment', columns: {#assessmentId})
class Reports extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get assessmentId => text()();
  TextColumn get assessmentTitle => text()();
  TextColumn get studentId => text()();
  TextColumn get studentName => text()();
  TextColumn get rollNumber => text()();
  IntColumn get grade => integer()();
  TextColumn get section => text()();
  TextColumn get report => text().map(const _JsonConverter())();
  DateTimeColumn get generatedAt => dateTime()();
  TextColumn get generatedBy => text()();

  @override
  Set<Column> get primaryKey => {id};
}

@TableIndex(name: 'idx_notifications_user', columns: {#userId})
@TableIndex(name: 'idx_notifications_read', columns: {#isRead})
@DataClassName('NotificationRow')
class Notifications extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get userId => text()();
  TextColumn get type => text()();
  TextColumn get title => text()();
  TextColumn get body => text()();
  TextColumn get data => text().map(const _JsonConverter())();
  DateTimeColumn get createdAt => dateTime()();
  BoolColumn get isRead => boolean()();
  DateTimeColumn get readAt => dateTime().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class SyncQueue extends Table {
  TextColumn get id => text().withLength(min: 1, max: 36)();
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  TextColumn get operation => text()();
  TextColumn get payload => text().map(const _JsonConverter())();
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get nextRetryAt => dateTime()();
  TextColumn get error => text().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class _StringListConverter extends TypeConverter<List<String>, String> {
  const _StringListConverter();

  @override
  List<String> fromSql(String fromDb) {
    return List<String>.from(const JsonDecoder().convert(fromDb) as List<dynamic>);
  }

  @override
  String toSql(List<String> value) {
    return const JsonEncoder.withIndent('').convert(value);
  }
}

class _JsonConverter extends TypeConverter<Map<String, dynamic>, String> {
  const _JsonConverter();

  @override
  Map<String, dynamic> fromSql(String fromDb) {
    return Map<String, dynamic>.from(const JsonDecoder().convert(fromDb) as Map<String, dynamic>);
  }

  @override
  String toSql(Map<String, dynamic> value) {
    return const JsonEncoder.withIndent('').convert(value);
  }
}

@DriftDatabase(tables: [
  Assessments,
  Questions,
  AnswerSheets,
  Evaluations,
  StudentMasteryTable,
  PracticeSessions,
  Reports,
  Notifications,
  SyncQueue,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase(String dbPath) : super(openConnection(dbPath));

  @override
  int get schemaVersion => 1;

  static Future<String> defaultPath() async {
    final appDir = await getApplicationDocumentsDirectory();
    return p.join(appDir.path, 'assessmentos.db');
  }
}
