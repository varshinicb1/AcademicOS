// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $AssessmentsTable extends Assessments
    with TableInfo<$AssessmentsTable, AssessmentRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AssessmentsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _schoolIdMeta =
      const VerificationMeta('schoolId');
  @override
  late final GeneratedColumn<String> schoolId = GeneratedColumn<String>(
      'school_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _teacherIdMeta =
      const VerificationMeta('teacherId');
  @override
  late final GeneratedColumn<String> teacherId = GeneratedColumn<String>(
      'teacher_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _subjectMeta =
      const VerificationMeta('subject');
  @override
  late final GeneratedColumn<String> subject = GeneratedColumn<String>(
      'subject', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _gradeMeta = const VerificationMeta('grade');
  @override
  late final GeneratedColumn<int> grade = GeneratedColumn<int>(
      'grade', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _chapterIdsMeta =
      const VerificationMeta('chapterIds');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> chapterIds =
      GeneratedColumn<String>('chapter_ids', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>($AssessmentsTable.$converterchapterIds);
  static const VerificationMeta _blueprintMeta =
      const VerificationMeta('blueprint');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      blueprint = GeneratedColumn<String>('blueprint', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $AssessmentsTable.$converterblueprint);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _updatedAtMeta =
      const VerificationMeta('updatedAt');
  @override
  late final GeneratedColumn<DateTime> updatedAt = GeneratedColumn<DateTime>(
      'updated_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _scheduledAtMeta =
      const VerificationMeta('scheduledAt');
  @override
  late final GeneratedColumn<DateTime> scheduledAt = GeneratedColumn<DateTime>(
      'scheduled_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _completedAtMeta =
      const VerificationMeta('completedAt');
  @override
  late final GeneratedColumn<DateTime> completedAt = GeneratedColumn<DateTime>(
      'completed_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _templateIdMeta =
      const VerificationMeta('templateId');
  @override
  late final GeneratedColumn<String> templateId = GeneratedColumn<String>(
      'template_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _metadataMeta =
      const VerificationMeta('metadata');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      metadata = GeneratedColumn<String>('metadata', aliasedName, false,
              type: DriftSqlType.string,
              requiredDuringInsert: false,
              defaultValue: const Constant('{}'))
          .withConverter<Map<String, dynamic>>(
              $AssessmentsTable.$convertermetadata);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        schoolId,
        teacherId,
        title,
        subject,
        grade,
        chapterIds,
        blueprint,
        status,
        createdAt,
        updatedAt,
        scheduledAt,
        completedAt,
        templateId,
        metadata
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'assessments';
  @override
  VerificationContext validateIntegrity(Insertable<AssessmentRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('school_id')) {
      context.handle(_schoolIdMeta,
          schoolId.isAcceptableOrUnknown(data['school_id']!, _schoolIdMeta));
    } else if (isInserting) {
      context.missing(_schoolIdMeta);
    }
    if (data.containsKey('teacher_id')) {
      context.handle(_teacherIdMeta,
          teacherId.isAcceptableOrUnknown(data['teacher_id']!, _teacherIdMeta));
    } else if (isInserting) {
      context.missing(_teacherIdMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('subject')) {
      context.handle(_subjectMeta,
          subject.isAcceptableOrUnknown(data['subject']!, _subjectMeta));
    } else if (isInserting) {
      context.missing(_subjectMeta);
    }
    if (data.containsKey('grade')) {
      context.handle(
          _gradeMeta, grade.isAcceptableOrUnknown(data['grade']!, _gradeMeta));
    } else if (isInserting) {
      context.missing(_gradeMeta);
    }
    context.handle(_chapterIdsMeta, const VerificationResult.success());
    context.handle(_blueprintMeta, const VerificationResult.success());
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(_updatedAtMeta,
          updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta));
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('scheduled_at')) {
      context.handle(
          _scheduledAtMeta,
          scheduledAt.isAcceptableOrUnknown(
              data['scheduled_at']!, _scheduledAtMeta));
    }
    if (data.containsKey('completed_at')) {
      context.handle(
          _completedAtMeta,
          completedAt.isAcceptableOrUnknown(
              data['completed_at']!, _completedAtMeta));
    }
    if (data.containsKey('template_id')) {
      context.handle(
          _templateIdMeta,
          templateId.isAcceptableOrUnknown(
              data['template_id']!, _templateIdMeta));
    }
    context.handle(_metadataMeta, const VerificationResult.success());
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  AssessmentRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AssessmentRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      schoolId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}school_id'])!,
      teacherId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}teacher_id'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      subject: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}subject'])!,
      grade: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}grade'])!,
      chapterIds: $AssessmentsTable.$converterchapterIds.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}chapter_ids'])!),
      blueprint: $AssessmentsTable.$converterblueprint.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}blueprint'])!),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      updatedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}updated_at'])!,
      scheduledAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}scheduled_at']),
      completedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}completed_at']),
      templateId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}template_id']),
      metadata: $AssessmentsTable.$convertermetadata.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}metadata'])!),
    );
  }

  @override
  $AssessmentsTable createAlias(String alias) {
    return $AssessmentsTable(attachedDatabase, alias);
  }

  static TypeConverter<List<String>, String> $converterchapterIds =
      const _StringListConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterblueprint =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertermetadata =
      const _JsonConverter();
}

class AssessmentRow extends DataClass implements Insertable<AssessmentRow> {
  final String id;
  final String schoolId;
  final String teacherId;
  final String title;
  final String subject;
  final int grade;
  final List<String> chapterIds;
  final Map<String, dynamic> blueprint;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? scheduledAt;
  final DateTime? completedAt;
  final String? templateId;
  final Map<String, dynamic> metadata;
  const AssessmentRow(
      {required this.id,
      required this.schoolId,
      required this.teacherId,
      required this.title,
      required this.subject,
      required this.grade,
      required this.chapterIds,
      required this.blueprint,
      required this.status,
      required this.createdAt,
      required this.updatedAt,
      this.scheduledAt,
      this.completedAt,
      this.templateId,
      required this.metadata});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['school_id'] = Variable<String>(schoolId);
    map['teacher_id'] = Variable<String>(teacherId);
    map['title'] = Variable<String>(title);
    map['subject'] = Variable<String>(subject);
    map['grade'] = Variable<int>(grade);
    {
      map['chapter_ids'] = Variable<String>(
          $AssessmentsTable.$converterchapterIds.toSql(chapterIds));
    }
    {
      map['blueprint'] = Variable<String>(
          $AssessmentsTable.$converterblueprint.toSql(blueprint));
    }
    map['status'] = Variable<String>(status);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['updated_at'] = Variable<DateTime>(updatedAt);
    if (!nullToAbsent || scheduledAt != null) {
      map['scheduled_at'] = Variable<DateTime>(scheduledAt);
    }
    if (!nullToAbsent || completedAt != null) {
      map['completed_at'] = Variable<DateTime>(completedAt);
    }
    if (!nullToAbsent || templateId != null) {
      map['template_id'] = Variable<String>(templateId);
    }
    {
      map['metadata'] = Variable<String>(
          $AssessmentsTable.$convertermetadata.toSql(metadata));
    }
    return map;
  }

  AssessmentsCompanion toCompanion(bool nullToAbsent) {
    return AssessmentsCompanion(
      id: Value(id),
      schoolId: Value(schoolId),
      teacherId: Value(teacherId),
      title: Value(title),
      subject: Value(subject),
      grade: Value(grade),
      chapterIds: Value(chapterIds),
      blueprint: Value(blueprint),
      status: Value(status),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      scheduledAt: scheduledAt == null && nullToAbsent
          ? const Value.absent()
          : Value(scheduledAt),
      completedAt: completedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(completedAt),
      templateId: templateId == null && nullToAbsent
          ? const Value.absent()
          : Value(templateId),
      metadata: Value(metadata),
    );
  }

  factory AssessmentRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AssessmentRow(
      id: serializer.fromJson<String>(json['id']),
      schoolId: serializer.fromJson<String>(json['schoolId']),
      teacherId: serializer.fromJson<String>(json['teacherId']),
      title: serializer.fromJson<String>(json['title']),
      subject: serializer.fromJson<String>(json['subject']),
      grade: serializer.fromJson<int>(json['grade']),
      chapterIds: serializer.fromJson<List<String>>(json['chapterIds']),
      blueprint: serializer.fromJson<Map<String, dynamic>>(json['blueprint']),
      status: serializer.fromJson<String>(json['status']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
      scheduledAt: serializer.fromJson<DateTime?>(json['scheduledAt']),
      completedAt: serializer.fromJson<DateTime?>(json['completedAt']),
      templateId: serializer.fromJson<String?>(json['templateId']),
      metadata: serializer.fromJson<Map<String, dynamic>>(json['metadata']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'schoolId': serializer.toJson<String>(schoolId),
      'teacherId': serializer.toJson<String>(teacherId),
      'title': serializer.toJson<String>(title),
      'subject': serializer.toJson<String>(subject),
      'grade': serializer.toJson<int>(grade),
      'chapterIds': serializer.toJson<List<String>>(chapterIds),
      'blueprint': serializer.toJson<Map<String, dynamic>>(blueprint),
      'status': serializer.toJson<String>(status),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
      'scheduledAt': serializer.toJson<DateTime?>(scheduledAt),
      'completedAt': serializer.toJson<DateTime?>(completedAt),
      'templateId': serializer.toJson<String?>(templateId),
      'metadata': serializer.toJson<Map<String, dynamic>>(metadata),
    };
  }

  AssessmentRow copyWith(
          {String? id,
          String? schoolId,
          String? teacherId,
          String? title,
          String? subject,
          int? grade,
          List<String>? chapterIds,
          Map<String, dynamic>? blueprint,
          String? status,
          DateTime? createdAt,
          DateTime? updatedAt,
          Value<DateTime?> scheduledAt = const Value.absent(),
          Value<DateTime?> completedAt = const Value.absent(),
          Value<String?> templateId = const Value.absent(),
          Map<String, dynamic>? metadata}) =>
      AssessmentRow(
        id: id ?? this.id,
        schoolId: schoolId ?? this.schoolId,
        teacherId: teacherId ?? this.teacherId,
        title: title ?? this.title,
        subject: subject ?? this.subject,
        grade: grade ?? this.grade,
        chapterIds: chapterIds ?? this.chapterIds,
        blueprint: blueprint ?? this.blueprint,
        status: status ?? this.status,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
        scheduledAt: scheduledAt.present ? scheduledAt.value : this.scheduledAt,
        completedAt: completedAt.present ? completedAt.value : this.completedAt,
        templateId: templateId.present ? templateId.value : this.templateId,
        metadata: metadata ?? this.metadata,
      );
  AssessmentRow copyWithCompanion(AssessmentsCompanion data) {
    return AssessmentRow(
      id: data.id.present ? data.id.value : this.id,
      schoolId: data.schoolId.present ? data.schoolId.value : this.schoolId,
      teacherId: data.teacherId.present ? data.teacherId.value : this.teacherId,
      title: data.title.present ? data.title.value : this.title,
      subject: data.subject.present ? data.subject.value : this.subject,
      grade: data.grade.present ? data.grade.value : this.grade,
      chapterIds:
          data.chapterIds.present ? data.chapterIds.value : this.chapterIds,
      blueprint: data.blueprint.present ? data.blueprint.value : this.blueprint,
      status: data.status.present ? data.status.value : this.status,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      scheduledAt:
          data.scheduledAt.present ? data.scheduledAt.value : this.scheduledAt,
      completedAt:
          data.completedAt.present ? data.completedAt.value : this.completedAt,
      templateId:
          data.templateId.present ? data.templateId.value : this.templateId,
      metadata: data.metadata.present ? data.metadata.value : this.metadata,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AssessmentRow(')
          ..write('id: $id, ')
          ..write('schoolId: $schoolId, ')
          ..write('teacherId: $teacherId, ')
          ..write('title: $title, ')
          ..write('subject: $subject, ')
          ..write('grade: $grade, ')
          ..write('chapterIds: $chapterIds, ')
          ..write('blueprint: $blueprint, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('scheduledAt: $scheduledAt, ')
          ..write('completedAt: $completedAt, ')
          ..write('templateId: $templateId, ')
          ..write('metadata: $metadata')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      schoolId,
      teacherId,
      title,
      subject,
      grade,
      chapterIds,
      blueprint,
      status,
      createdAt,
      updatedAt,
      scheduledAt,
      completedAt,
      templateId,
      metadata);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AssessmentRow &&
          other.id == this.id &&
          other.schoolId == this.schoolId &&
          other.teacherId == this.teacherId &&
          other.title == this.title &&
          other.subject == this.subject &&
          other.grade == this.grade &&
          other.chapterIds == this.chapterIds &&
          other.blueprint == this.blueprint &&
          other.status == this.status &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.scheduledAt == this.scheduledAt &&
          other.completedAt == this.completedAt &&
          other.templateId == this.templateId &&
          other.metadata == this.metadata);
}

class AssessmentsCompanion extends UpdateCompanion<AssessmentRow> {
  final Value<String> id;
  final Value<String> schoolId;
  final Value<String> teacherId;
  final Value<String> title;
  final Value<String> subject;
  final Value<int> grade;
  final Value<List<String>> chapterIds;
  final Value<Map<String, dynamic>> blueprint;
  final Value<String> status;
  final Value<DateTime> createdAt;
  final Value<DateTime> updatedAt;
  final Value<DateTime?> scheduledAt;
  final Value<DateTime?> completedAt;
  final Value<String?> templateId;
  final Value<Map<String, dynamic>> metadata;
  final Value<int> rowid;
  const AssessmentsCompanion({
    this.id = const Value.absent(),
    this.schoolId = const Value.absent(),
    this.teacherId = const Value.absent(),
    this.title = const Value.absent(),
    this.subject = const Value.absent(),
    this.grade = const Value.absent(),
    this.chapterIds = const Value.absent(),
    this.blueprint = const Value.absent(),
    this.status = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.scheduledAt = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.templateId = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AssessmentsCompanion.insert({
    required String id,
    required String schoolId,
    required String teacherId,
    required String title,
    required String subject,
    required int grade,
    required List<String> chapterIds,
    required Map<String, dynamic> blueprint,
    required String status,
    required DateTime createdAt,
    required DateTime updatedAt,
    this.scheduledAt = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.templateId = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        schoolId = Value(schoolId),
        teacherId = Value(teacherId),
        title = Value(title),
        subject = Value(subject),
        grade = Value(grade),
        chapterIds = Value(chapterIds),
        blueprint = Value(blueprint),
        status = Value(status),
        createdAt = Value(createdAt),
        updatedAt = Value(updatedAt);
  static Insertable<AssessmentRow> custom({
    Expression<String>? id,
    Expression<String>? schoolId,
    Expression<String>? teacherId,
    Expression<String>? title,
    Expression<String>? subject,
    Expression<int>? grade,
    Expression<String>? chapterIds,
    Expression<String>? blueprint,
    Expression<String>? status,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? updatedAt,
    Expression<DateTime>? scheduledAt,
    Expression<DateTime>? completedAt,
    Expression<String>? templateId,
    Expression<String>? metadata,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (schoolId != null) 'school_id': schoolId,
      if (teacherId != null) 'teacher_id': teacherId,
      if (title != null) 'title': title,
      if (subject != null) 'subject': subject,
      if (grade != null) 'grade': grade,
      if (chapterIds != null) 'chapter_ids': chapterIds,
      if (blueprint != null) 'blueprint': blueprint,
      if (status != null) 'status': status,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (scheduledAt != null) 'scheduled_at': scheduledAt,
      if (completedAt != null) 'completed_at': completedAt,
      if (templateId != null) 'template_id': templateId,
      if (metadata != null) 'metadata': metadata,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AssessmentsCompanion copyWith(
      {Value<String>? id,
      Value<String>? schoolId,
      Value<String>? teacherId,
      Value<String>? title,
      Value<String>? subject,
      Value<int>? grade,
      Value<List<String>>? chapterIds,
      Value<Map<String, dynamic>>? blueprint,
      Value<String>? status,
      Value<DateTime>? createdAt,
      Value<DateTime>? updatedAt,
      Value<DateTime?>? scheduledAt,
      Value<DateTime?>? completedAt,
      Value<String?>? templateId,
      Value<Map<String, dynamic>>? metadata,
      Value<int>? rowid}) {
    return AssessmentsCompanion(
      id: id ?? this.id,
      schoolId: schoolId ?? this.schoolId,
      teacherId: teacherId ?? this.teacherId,
      title: title ?? this.title,
      subject: subject ?? this.subject,
      grade: grade ?? this.grade,
      chapterIds: chapterIds ?? this.chapterIds,
      blueprint: blueprint ?? this.blueprint,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      scheduledAt: scheduledAt ?? this.scheduledAt,
      completedAt: completedAt ?? this.completedAt,
      templateId: templateId ?? this.templateId,
      metadata: metadata ?? this.metadata,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (schoolId.present) {
      map['school_id'] = Variable<String>(schoolId.value);
    }
    if (teacherId.present) {
      map['teacher_id'] = Variable<String>(teacherId.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (subject.present) {
      map['subject'] = Variable<String>(subject.value);
    }
    if (grade.present) {
      map['grade'] = Variable<int>(grade.value);
    }
    if (chapterIds.present) {
      map['chapter_ids'] = Variable<String>(
          $AssessmentsTable.$converterchapterIds.toSql(chapterIds.value));
    }
    if (blueprint.present) {
      map['blueprint'] = Variable<String>(
          $AssessmentsTable.$converterblueprint.toSql(blueprint.value));
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<DateTime>(updatedAt.value);
    }
    if (scheduledAt.present) {
      map['scheduled_at'] = Variable<DateTime>(scheduledAt.value);
    }
    if (completedAt.present) {
      map['completed_at'] = Variable<DateTime>(completedAt.value);
    }
    if (templateId.present) {
      map['template_id'] = Variable<String>(templateId.value);
    }
    if (metadata.present) {
      map['metadata'] = Variable<String>(
          $AssessmentsTable.$convertermetadata.toSql(metadata.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AssessmentsCompanion(')
          ..write('id: $id, ')
          ..write('schoolId: $schoolId, ')
          ..write('teacherId: $teacherId, ')
          ..write('title: $title, ')
          ..write('subject: $subject, ')
          ..write('grade: $grade, ')
          ..write('chapterIds: $chapterIds, ')
          ..write('blueprint: $blueprint, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('scheduledAt: $scheduledAt, ')
          ..write('completedAt: $completedAt, ')
          ..write('templateId: $templateId, ')
          ..write('metadata: $metadata, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $QuestionsTable extends Questions
    with TableInfo<$QuestionsTable, QuestionRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $QuestionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _assessmentIdMeta =
      const VerificationMeta('assessmentId');
  @override
  late final GeneratedColumn<String> assessmentId = GeneratedColumn<String>(
      'assessment_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _questionBankIdMeta =
      const VerificationMeta('questionBankId');
  @override
  late final GeneratedColumn<String> questionBankId = GeneratedColumn<String>(
      'question_bank_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _subjectMeta =
      const VerificationMeta('subject');
  @override
  late final GeneratedColumn<String> subject = GeneratedColumn<String>(
      'subject', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _gradeMeta = const VerificationMeta('grade');
  @override
  late final GeneratedColumn<int> grade = GeneratedColumn<int>(
      'grade', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _chapterIdsMeta =
      const VerificationMeta('chapterIds');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> chapterIds =
      GeneratedColumn<String>('chapter_ids', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>($QuestionsTable.$converterchapterIds);
  static const VerificationMeta _competencyIdsMeta =
      const VerificationMeta('competencyIds');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String>
      competencyIds = GeneratedColumn<String>(
              'competency_ids', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>($QuestionsTable.$convertercompetencyIds);
  static const VerificationMeta _bloomLevelMeta =
      const VerificationMeta('bloomLevel');
  @override
  late final GeneratedColumn<String> bloomLevel = GeneratedColumn<String>(
      'bloom_level', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _difficultyMeta =
      const VerificationMeta('difficulty');
  @override
  late final GeneratedColumn<String> difficulty = GeneratedColumn<String>(
      'difficulty', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _typeMeta = const VerificationMeta('type');
  @override
  late final GeneratedColumn<String> type = GeneratedColumn<String>(
      'type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _stemMeta = const VerificationMeta('stem');
  @override
  late final GeneratedColumn<String> stem = GeneratedColumn<String>(
      'stem', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _stemLatexMeta =
      const VerificationMeta('stemLatex');
  @override
  late final GeneratedColumn<String> stemLatex = GeneratedColumn<String>(
      'stem_latex', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _partsMeta = const VerificationMeta('parts');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      parts = GeneratedColumn<String>('parts', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>($QuestionsTable.$converterparts);
  static const VerificationMeta _answerSchemeMeta =
      const VerificationMeta('answerScheme');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      answerScheme = GeneratedColumn<String>(
              'answer_scheme', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $QuestionsTable.$converteranswerScheme);
  static const VerificationMeta _estimatedTimeMinutesMeta =
      const VerificationMeta('estimatedTimeMinutes');
  @override
  late final GeneratedColumn<int> estimatedTimeMinutes = GeneratedColumn<int>(
      'estimated_time_minutes', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _marksMeta = const VerificationMeta('marks');
  @override
  late final GeneratedColumn<int> marks = GeneratedColumn<int>(
      'marks', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _languageMeta =
      const VerificationMeta('language');
  @override
  late final GeneratedColumn<String> language = GeneratedColumn<String>(
      'language', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sourceMeta = const VerificationMeta('source');
  @override
  late final GeneratedColumn<String> source = GeneratedColumn<String>(
      'source', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _qualityScoreMeta =
      const VerificationMeta('qualityScore');
  @override
  late final GeneratedColumn<double> qualityScore = GeneratedColumn<double>(
      'quality_score', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _tagsMeta = const VerificationMeta('tags');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> tags =
      GeneratedColumn<String>('tags', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>($QuestionsTable.$convertertags);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _updatedAtMeta =
      const VerificationMeta('updatedAt');
  @override
  late final GeneratedColumn<DateTime> updatedAt = GeneratedColumn<DateTime>(
      'updated_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _metadataMeta =
      const VerificationMeta('metadata');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      metadata = GeneratedColumn<String>('metadata', aliasedName, false,
              type: DriftSqlType.string,
              requiredDuringInsert: false,
              defaultValue: const Constant('{}'))
          .withConverter<Map<String, dynamic>>(
              $QuestionsTable.$convertermetadata);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        assessmentId,
        questionBankId,
        subject,
        grade,
        chapterIds,
        competencyIds,
        bloomLevel,
        difficulty,
        type,
        stem,
        stemLatex,
        parts,
        answerScheme,
        estimatedTimeMinutes,
        marks,
        language,
        source,
        qualityScore,
        tags,
        createdAt,
        updatedAt,
        metadata
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'questions';
  @override
  VerificationContext validateIntegrity(Insertable<QuestionRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('assessment_id')) {
      context.handle(
          _assessmentIdMeta,
          assessmentId.isAcceptableOrUnknown(
              data['assessment_id']!, _assessmentIdMeta));
    }
    if (data.containsKey('question_bank_id')) {
      context.handle(
          _questionBankIdMeta,
          questionBankId.isAcceptableOrUnknown(
              data['question_bank_id']!, _questionBankIdMeta));
    } else if (isInserting) {
      context.missing(_questionBankIdMeta);
    }
    if (data.containsKey('subject')) {
      context.handle(_subjectMeta,
          subject.isAcceptableOrUnknown(data['subject']!, _subjectMeta));
    } else if (isInserting) {
      context.missing(_subjectMeta);
    }
    if (data.containsKey('grade')) {
      context.handle(
          _gradeMeta, grade.isAcceptableOrUnknown(data['grade']!, _gradeMeta));
    } else if (isInserting) {
      context.missing(_gradeMeta);
    }
    context.handle(_chapterIdsMeta, const VerificationResult.success());
    context.handle(_competencyIdsMeta, const VerificationResult.success());
    if (data.containsKey('bloom_level')) {
      context.handle(
          _bloomLevelMeta,
          bloomLevel.isAcceptableOrUnknown(
              data['bloom_level']!, _bloomLevelMeta));
    } else if (isInserting) {
      context.missing(_bloomLevelMeta);
    }
    if (data.containsKey('difficulty')) {
      context.handle(
          _difficultyMeta,
          difficulty.isAcceptableOrUnknown(
              data['difficulty']!, _difficultyMeta));
    } else if (isInserting) {
      context.missing(_difficultyMeta);
    }
    if (data.containsKey('type')) {
      context.handle(
          _typeMeta, type.isAcceptableOrUnknown(data['type']!, _typeMeta));
    } else if (isInserting) {
      context.missing(_typeMeta);
    }
    if (data.containsKey('stem')) {
      context.handle(
          _stemMeta, stem.isAcceptableOrUnknown(data['stem']!, _stemMeta));
    } else if (isInserting) {
      context.missing(_stemMeta);
    }
    if (data.containsKey('stem_latex')) {
      context.handle(_stemLatexMeta,
          stemLatex.isAcceptableOrUnknown(data['stem_latex']!, _stemLatexMeta));
    }
    context.handle(_partsMeta, const VerificationResult.success());
    context.handle(_answerSchemeMeta, const VerificationResult.success());
    if (data.containsKey('estimated_time_minutes')) {
      context.handle(
          _estimatedTimeMinutesMeta,
          estimatedTimeMinutes.isAcceptableOrUnknown(
              data['estimated_time_minutes']!, _estimatedTimeMinutesMeta));
    } else if (isInserting) {
      context.missing(_estimatedTimeMinutesMeta);
    }
    if (data.containsKey('marks')) {
      context.handle(
          _marksMeta, marks.isAcceptableOrUnknown(data['marks']!, _marksMeta));
    } else if (isInserting) {
      context.missing(_marksMeta);
    }
    if (data.containsKey('language')) {
      context.handle(_languageMeta,
          language.isAcceptableOrUnknown(data['language']!, _languageMeta));
    } else if (isInserting) {
      context.missing(_languageMeta);
    }
    if (data.containsKey('source')) {
      context.handle(_sourceMeta,
          source.isAcceptableOrUnknown(data['source']!, _sourceMeta));
    } else if (isInserting) {
      context.missing(_sourceMeta);
    }
    if (data.containsKey('quality_score')) {
      context.handle(
          _qualityScoreMeta,
          qualityScore.isAcceptableOrUnknown(
              data['quality_score']!, _qualityScoreMeta));
    } else if (isInserting) {
      context.missing(_qualityScoreMeta);
    }
    context.handle(_tagsMeta, const VerificationResult.success());
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(_updatedAtMeta,
          updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta));
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    context.handle(_metadataMeta, const VerificationResult.success());
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  QuestionRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return QuestionRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      assessmentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}assessment_id']),
      questionBankId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}question_bank_id'])!,
      subject: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}subject'])!,
      grade: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}grade'])!,
      chapterIds: $QuestionsTable.$converterchapterIds.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}chapter_ids'])!),
      competencyIds: $QuestionsTable.$convertercompetencyIds.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}competency_ids'])!),
      bloomLevel: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}bloom_level'])!,
      difficulty: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}difficulty'])!,
      type: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}type'])!,
      stem: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}stem'])!,
      stemLatex: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}stem_latex']),
      parts: $QuestionsTable.$converterparts.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}parts'])!),
      answerScheme: $QuestionsTable.$converteranswerScheme.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}answer_scheme'])!),
      estimatedTimeMinutes: attachedDatabase.typeMapping.read(
          DriftSqlType.int, data['${effectivePrefix}estimated_time_minutes'])!,
      marks: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}marks'])!,
      language: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}language'])!,
      source: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}source'])!,
      qualityScore: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}quality_score'])!,
      tags: $QuestionsTable.$convertertags.fromSql(attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}tags'])!),
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      updatedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}updated_at'])!,
      metadata: $QuestionsTable.$convertermetadata.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}metadata'])!),
    );
  }

  @override
  $QuestionsTable createAlias(String alias) {
    return $QuestionsTable(attachedDatabase, alias);
  }

  static TypeConverter<List<String>, String> $converterchapterIds =
      const _StringListConverter();
  static TypeConverter<List<String>, String> $convertercompetencyIds =
      const _StringListConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterparts =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $converteranswerScheme =
      const _JsonConverter();
  static TypeConverter<List<String>, String> $convertertags =
      const _StringListConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertermetadata =
      const _JsonConverter();
}

class QuestionRow extends DataClass implements Insertable<QuestionRow> {
  final String id;
  final String? assessmentId;
  final String questionBankId;
  final String subject;
  final int grade;
  final List<String> chapterIds;
  final List<String> competencyIds;
  final String bloomLevel;
  final String difficulty;
  final String type;
  final String stem;
  final String? stemLatex;
  final Map<String, dynamic> parts;
  final Map<String, dynamic> answerScheme;
  final int estimatedTimeMinutes;
  final int marks;
  final String language;
  final String source;
  final double qualityScore;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime updatedAt;
  final Map<String, dynamic> metadata;
  const QuestionRow(
      {required this.id,
      this.assessmentId,
      required this.questionBankId,
      required this.subject,
      required this.grade,
      required this.chapterIds,
      required this.competencyIds,
      required this.bloomLevel,
      required this.difficulty,
      required this.type,
      required this.stem,
      this.stemLatex,
      required this.parts,
      required this.answerScheme,
      required this.estimatedTimeMinutes,
      required this.marks,
      required this.language,
      required this.source,
      required this.qualityScore,
      required this.tags,
      required this.createdAt,
      required this.updatedAt,
      required this.metadata});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    if (!nullToAbsent || assessmentId != null) {
      map['assessment_id'] = Variable<String>(assessmentId);
    }
    map['question_bank_id'] = Variable<String>(questionBankId);
    map['subject'] = Variable<String>(subject);
    map['grade'] = Variable<int>(grade);
    {
      map['chapter_ids'] = Variable<String>(
          $QuestionsTable.$converterchapterIds.toSql(chapterIds));
    }
    {
      map['competency_ids'] = Variable<String>(
          $QuestionsTable.$convertercompetencyIds.toSql(competencyIds));
    }
    map['bloom_level'] = Variable<String>(bloomLevel);
    map['difficulty'] = Variable<String>(difficulty);
    map['type'] = Variable<String>(type);
    map['stem'] = Variable<String>(stem);
    if (!nullToAbsent || stemLatex != null) {
      map['stem_latex'] = Variable<String>(stemLatex);
    }
    {
      map['parts'] =
          Variable<String>($QuestionsTable.$converterparts.toSql(parts));
    }
    {
      map['answer_scheme'] = Variable<String>(
          $QuestionsTable.$converteranswerScheme.toSql(answerScheme));
    }
    map['estimated_time_minutes'] = Variable<int>(estimatedTimeMinutes);
    map['marks'] = Variable<int>(marks);
    map['language'] = Variable<String>(language);
    map['source'] = Variable<String>(source);
    map['quality_score'] = Variable<double>(qualityScore);
    {
      map['tags'] =
          Variable<String>($QuestionsTable.$convertertags.toSql(tags));
    }
    map['created_at'] = Variable<DateTime>(createdAt);
    map['updated_at'] = Variable<DateTime>(updatedAt);
    {
      map['metadata'] =
          Variable<String>($QuestionsTable.$convertermetadata.toSql(metadata));
    }
    return map;
  }

  QuestionsCompanion toCompanion(bool nullToAbsent) {
    return QuestionsCompanion(
      id: Value(id),
      assessmentId: assessmentId == null && nullToAbsent
          ? const Value.absent()
          : Value(assessmentId),
      questionBankId: Value(questionBankId),
      subject: Value(subject),
      grade: Value(grade),
      chapterIds: Value(chapterIds),
      competencyIds: Value(competencyIds),
      bloomLevel: Value(bloomLevel),
      difficulty: Value(difficulty),
      type: Value(type),
      stem: Value(stem),
      stemLatex: stemLatex == null && nullToAbsent
          ? const Value.absent()
          : Value(stemLatex),
      parts: Value(parts),
      answerScheme: Value(answerScheme),
      estimatedTimeMinutes: Value(estimatedTimeMinutes),
      marks: Value(marks),
      language: Value(language),
      source: Value(source),
      qualityScore: Value(qualityScore),
      tags: Value(tags),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      metadata: Value(metadata),
    );
  }

  factory QuestionRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return QuestionRow(
      id: serializer.fromJson<String>(json['id']),
      assessmentId: serializer.fromJson<String?>(json['assessmentId']),
      questionBankId: serializer.fromJson<String>(json['questionBankId']),
      subject: serializer.fromJson<String>(json['subject']),
      grade: serializer.fromJson<int>(json['grade']),
      chapterIds: serializer.fromJson<List<String>>(json['chapterIds']),
      competencyIds: serializer.fromJson<List<String>>(json['competencyIds']),
      bloomLevel: serializer.fromJson<String>(json['bloomLevel']),
      difficulty: serializer.fromJson<String>(json['difficulty']),
      type: serializer.fromJson<String>(json['type']),
      stem: serializer.fromJson<String>(json['stem']),
      stemLatex: serializer.fromJson<String?>(json['stemLatex']),
      parts: serializer.fromJson<Map<String, dynamic>>(json['parts']),
      answerScheme:
          serializer.fromJson<Map<String, dynamic>>(json['answerScheme']),
      estimatedTimeMinutes:
          serializer.fromJson<int>(json['estimatedTimeMinutes']),
      marks: serializer.fromJson<int>(json['marks']),
      language: serializer.fromJson<String>(json['language']),
      source: serializer.fromJson<String>(json['source']),
      qualityScore: serializer.fromJson<double>(json['qualityScore']),
      tags: serializer.fromJson<List<String>>(json['tags']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
      metadata: serializer.fromJson<Map<String, dynamic>>(json['metadata']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'assessmentId': serializer.toJson<String?>(assessmentId),
      'questionBankId': serializer.toJson<String>(questionBankId),
      'subject': serializer.toJson<String>(subject),
      'grade': serializer.toJson<int>(grade),
      'chapterIds': serializer.toJson<List<String>>(chapterIds),
      'competencyIds': serializer.toJson<List<String>>(competencyIds),
      'bloomLevel': serializer.toJson<String>(bloomLevel),
      'difficulty': serializer.toJson<String>(difficulty),
      'type': serializer.toJson<String>(type),
      'stem': serializer.toJson<String>(stem),
      'stemLatex': serializer.toJson<String?>(stemLatex),
      'parts': serializer.toJson<Map<String, dynamic>>(parts),
      'answerScheme': serializer.toJson<Map<String, dynamic>>(answerScheme),
      'estimatedTimeMinutes': serializer.toJson<int>(estimatedTimeMinutes),
      'marks': serializer.toJson<int>(marks),
      'language': serializer.toJson<String>(language),
      'source': serializer.toJson<String>(source),
      'qualityScore': serializer.toJson<double>(qualityScore),
      'tags': serializer.toJson<List<String>>(tags),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
      'metadata': serializer.toJson<Map<String, dynamic>>(metadata),
    };
  }

  QuestionRow copyWith(
          {String? id,
          Value<String?> assessmentId = const Value.absent(),
          String? questionBankId,
          String? subject,
          int? grade,
          List<String>? chapterIds,
          List<String>? competencyIds,
          String? bloomLevel,
          String? difficulty,
          String? type,
          String? stem,
          Value<String?> stemLatex = const Value.absent(),
          Map<String, dynamic>? parts,
          Map<String, dynamic>? answerScheme,
          int? estimatedTimeMinutes,
          int? marks,
          String? language,
          String? source,
          double? qualityScore,
          List<String>? tags,
          DateTime? createdAt,
          DateTime? updatedAt,
          Map<String, dynamic>? metadata}) =>
      QuestionRow(
        id: id ?? this.id,
        assessmentId:
            assessmentId.present ? assessmentId.value : this.assessmentId,
        questionBankId: questionBankId ?? this.questionBankId,
        subject: subject ?? this.subject,
        grade: grade ?? this.grade,
        chapterIds: chapterIds ?? this.chapterIds,
        competencyIds: competencyIds ?? this.competencyIds,
        bloomLevel: bloomLevel ?? this.bloomLevel,
        difficulty: difficulty ?? this.difficulty,
        type: type ?? this.type,
        stem: stem ?? this.stem,
        stemLatex: stemLatex.present ? stemLatex.value : this.stemLatex,
        parts: parts ?? this.parts,
        answerScheme: answerScheme ?? this.answerScheme,
        estimatedTimeMinutes: estimatedTimeMinutes ?? this.estimatedTimeMinutes,
        marks: marks ?? this.marks,
        language: language ?? this.language,
        source: source ?? this.source,
        qualityScore: qualityScore ?? this.qualityScore,
        tags: tags ?? this.tags,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
        metadata: metadata ?? this.metadata,
      );
  QuestionRow copyWithCompanion(QuestionsCompanion data) {
    return QuestionRow(
      id: data.id.present ? data.id.value : this.id,
      assessmentId: data.assessmentId.present
          ? data.assessmentId.value
          : this.assessmentId,
      questionBankId: data.questionBankId.present
          ? data.questionBankId.value
          : this.questionBankId,
      subject: data.subject.present ? data.subject.value : this.subject,
      grade: data.grade.present ? data.grade.value : this.grade,
      chapterIds:
          data.chapterIds.present ? data.chapterIds.value : this.chapterIds,
      competencyIds: data.competencyIds.present
          ? data.competencyIds.value
          : this.competencyIds,
      bloomLevel:
          data.bloomLevel.present ? data.bloomLevel.value : this.bloomLevel,
      difficulty:
          data.difficulty.present ? data.difficulty.value : this.difficulty,
      type: data.type.present ? data.type.value : this.type,
      stem: data.stem.present ? data.stem.value : this.stem,
      stemLatex: data.stemLatex.present ? data.stemLatex.value : this.stemLatex,
      parts: data.parts.present ? data.parts.value : this.parts,
      answerScheme: data.answerScheme.present
          ? data.answerScheme.value
          : this.answerScheme,
      estimatedTimeMinutes: data.estimatedTimeMinutes.present
          ? data.estimatedTimeMinutes.value
          : this.estimatedTimeMinutes,
      marks: data.marks.present ? data.marks.value : this.marks,
      language: data.language.present ? data.language.value : this.language,
      source: data.source.present ? data.source.value : this.source,
      qualityScore: data.qualityScore.present
          ? data.qualityScore.value
          : this.qualityScore,
      tags: data.tags.present ? data.tags.value : this.tags,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      metadata: data.metadata.present ? data.metadata.value : this.metadata,
    );
  }

  @override
  String toString() {
    return (StringBuffer('QuestionRow(')
          ..write('id: $id, ')
          ..write('assessmentId: $assessmentId, ')
          ..write('questionBankId: $questionBankId, ')
          ..write('subject: $subject, ')
          ..write('grade: $grade, ')
          ..write('chapterIds: $chapterIds, ')
          ..write('competencyIds: $competencyIds, ')
          ..write('bloomLevel: $bloomLevel, ')
          ..write('difficulty: $difficulty, ')
          ..write('type: $type, ')
          ..write('stem: $stem, ')
          ..write('stemLatex: $stemLatex, ')
          ..write('parts: $parts, ')
          ..write('answerScheme: $answerScheme, ')
          ..write('estimatedTimeMinutes: $estimatedTimeMinutes, ')
          ..write('marks: $marks, ')
          ..write('language: $language, ')
          ..write('source: $source, ')
          ..write('qualityScore: $qualityScore, ')
          ..write('tags: $tags, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('metadata: $metadata')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
        id,
        assessmentId,
        questionBankId,
        subject,
        grade,
        chapterIds,
        competencyIds,
        bloomLevel,
        difficulty,
        type,
        stem,
        stemLatex,
        parts,
        answerScheme,
        estimatedTimeMinutes,
        marks,
        language,
        source,
        qualityScore,
        tags,
        createdAt,
        updatedAt,
        metadata
      ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is QuestionRow &&
          other.id == this.id &&
          other.assessmentId == this.assessmentId &&
          other.questionBankId == this.questionBankId &&
          other.subject == this.subject &&
          other.grade == this.grade &&
          other.chapterIds == this.chapterIds &&
          other.competencyIds == this.competencyIds &&
          other.bloomLevel == this.bloomLevel &&
          other.difficulty == this.difficulty &&
          other.type == this.type &&
          other.stem == this.stem &&
          other.stemLatex == this.stemLatex &&
          other.parts == this.parts &&
          other.answerScheme == this.answerScheme &&
          other.estimatedTimeMinutes == this.estimatedTimeMinutes &&
          other.marks == this.marks &&
          other.language == this.language &&
          other.source == this.source &&
          other.qualityScore == this.qualityScore &&
          other.tags == this.tags &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.metadata == this.metadata);
}

class QuestionsCompanion extends UpdateCompanion<QuestionRow> {
  final Value<String> id;
  final Value<String?> assessmentId;
  final Value<String> questionBankId;
  final Value<String> subject;
  final Value<int> grade;
  final Value<List<String>> chapterIds;
  final Value<List<String>> competencyIds;
  final Value<String> bloomLevel;
  final Value<String> difficulty;
  final Value<String> type;
  final Value<String> stem;
  final Value<String?> stemLatex;
  final Value<Map<String, dynamic>> parts;
  final Value<Map<String, dynamic>> answerScheme;
  final Value<int> estimatedTimeMinutes;
  final Value<int> marks;
  final Value<String> language;
  final Value<String> source;
  final Value<double> qualityScore;
  final Value<List<String>> tags;
  final Value<DateTime> createdAt;
  final Value<DateTime> updatedAt;
  final Value<Map<String, dynamic>> metadata;
  final Value<int> rowid;
  const QuestionsCompanion({
    this.id = const Value.absent(),
    this.assessmentId = const Value.absent(),
    this.questionBankId = const Value.absent(),
    this.subject = const Value.absent(),
    this.grade = const Value.absent(),
    this.chapterIds = const Value.absent(),
    this.competencyIds = const Value.absent(),
    this.bloomLevel = const Value.absent(),
    this.difficulty = const Value.absent(),
    this.type = const Value.absent(),
    this.stem = const Value.absent(),
    this.stemLatex = const Value.absent(),
    this.parts = const Value.absent(),
    this.answerScheme = const Value.absent(),
    this.estimatedTimeMinutes = const Value.absent(),
    this.marks = const Value.absent(),
    this.language = const Value.absent(),
    this.source = const Value.absent(),
    this.qualityScore = const Value.absent(),
    this.tags = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  QuestionsCompanion.insert({
    required String id,
    this.assessmentId = const Value.absent(),
    required String questionBankId,
    required String subject,
    required int grade,
    required List<String> chapterIds,
    required List<String> competencyIds,
    required String bloomLevel,
    required String difficulty,
    required String type,
    required String stem,
    this.stemLatex = const Value.absent(),
    required Map<String, dynamic> parts,
    required Map<String, dynamic> answerScheme,
    required int estimatedTimeMinutes,
    required int marks,
    required String language,
    required String source,
    required double qualityScore,
    required List<String> tags,
    required DateTime createdAt,
    required DateTime updatedAt,
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        questionBankId = Value(questionBankId),
        subject = Value(subject),
        grade = Value(grade),
        chapterIds = Value(chapterIds),
        competencyIds = Value(competencyIds),
        bloomLevel = Value(bloomLevel),
        difficulty = Value(difficulty),
        type = Value(type),
        stem = Value(stem),
        parts = Value(parts),
        answerScheme = Value(answerScheme),
        estimatedTimeMinutes = Value(estimatedTimeMinutes),
        marks = Value(marks),
        language = Value(language),
        source = Value(source),
        qualityScore = Value(qualityScore),
        tags = Value(tags),
        createdAt = Value(createdAt),
        updatedAt = Value(updatedAt);
  static Insertable<QuestionRow> custom({
    Expression<String>? id,
    Expression<String>? assessmentId,
    Expression<String>? questionBankId,
    Expression<String>? subject,
    Expression<int>? grade,
    Expression<String>? chapterIds,
    Expression<String>? competencyIds,
    Expression<String>? bloomLevel,
    Expression<String>? difficulty,
    Expression<String>? type,
    Expression<String>? stem,
    Expression<String>? stemLatex,
    Expression<String>? parts,
    Expression<String>? answerScheme,
    Expression<int>? estimatedTimeMinutes,
    Expression<int>? marks,
    Expression<String>? language,
    Expression<String>? source,
    Expression<double>? qualityScore,
    Expression<String>? tags,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? updatedAt,
    Expression<String>? metadata,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (assessmentId != null) 'assessment_id': assessmentId,
      if (questionBankId != null) 'question_bank_id': questionBankId,
      if (subject != null) 'subject': subject,
      if (grade != null) 'grade': grade,
      if (chapterIds != null) 'chapter_ids': chapterIds,
      if (competencyIds != null) 'competency_ids': competencyIds,
      if (bloomLevel != null) 'bloom_level': bloomLevel,
      if (difficulty != null) 'difficulty': difficulty,
      if (type != null) 'type': type,
      if (stem != null) 'stem': stem,
      if (stemLatex != null) 'stem_latex': stemLatex,
      if (parts != null) 'parts': parts,
      if (answerScheme != null) 'answer_scheme': answerScheme,
      if (estimatedTimeMinutes != null)
        'estimated_time_minutes': estimatedTimeMinutes,
      if (marks != null) 'marks': marks,
      if (language != null) 'language': language,
      if (source != null) 'source': source,
      if (qualityScore != null) 'quality_score': qualityScore,
      if (tags != null) 'tags': tags,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (metadata != null) 'metadata': metadata,
      if (rowid != null) 'rowid': rowid,
    });
  }

  QuestionsCompanion copyWith(
      {Value<String>? id,
      Value<String?>? assessmentId,
      Value<String>? questionBankId,
      Value<String>? subject,
      Value<int>? grade,
      Value<List<String>>? chapterIds,
      Value<List<String>>? competencyIds,
      Value<String>? bloomLevel,
      Value<String>? difficulty,
      Value<String>? type,
      Value<String>? stem,
      Value<String?>? stemLatex,
      Value<Map<String, dynamic>>? parts,
      Value<Map<String, dynamic>>? answerScheme,
      Value<int>? estimatedTimeMinutes,
      Value<int>? marks,
      Value<String>? language,
      Value<String>? source,
      Value<double>? qualityScore,
      Value<List<String>>? tags,
      Value<DateTime>? createdAt,
      Value<DateTime>? updatedAt,
      Value<Map<String, dynamic>>? metadata,
      Value<int>? rowid}) {
    return QuestionsCompanion(
      id: id ?? this.id,
      assessmentId: assessmentId ?? this.assessmentId,
      questionBankId: questionBankId ?? this.questionBankId,
      subject: subject ?? this.subject,
      grade: grade ?? this.grade,
      chapterIds: chapterIds ?? this.chapterIds,
      competencyIds: competencyIds ?? this.competencyIds,
      bloomLevel: bloomLevel ?? this.bloomLevel,
      difficulty: difficulty ?? this.difficulty,
      type: type ?? this.type,
      stem: stem ?? this.stem,
      stemLatex: stemLatex ?? this.stemLatex,
      parts: parts ?? this.parts,
      answerScheme: answerScheme ?? this.answerScheme,
      estimatedTimeMinutes: estimatedTimeMinutes ?? this.estimatedTimeMinutes,
      marks: marks ?? this.marks,
      language: language ?? this.language,
      source: source ?? this.source,
      qualityScore: qualityScore ?? this.qualityScore,
      tags: tags ?? this.tags,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      metadata: metadata ?? this.metadata,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (assessmentId.present) {
      map['assessment_id'] = Variable<String>(assessmentId.value);
    }
    if (questionBankId.present) {
      map['question_bank_id'] = Variable<String>(questionBankId.value);
    }
    if (subject.present) {
      map['subject'] = Variable<String>(subject.value);
    }
    if (grade.present) {
      map['grade'] = Variable<int>(grade.value);
    }
    if (chapterIds.present) {
      map['chapter_ids'] = Variable<String>(
          $QuestionsTable.$converterchapterIds.toSql(chapterIds.value));
    }
    if (competencyIds.present) {
      map['competency_ids'] = Variable<String>(
          $QuestionsTable.$convertercompetencyIds.toSql(competencyIds.value));
    }
    if (bloomLevel.present) {
      map['bloom_level'] = Variable<String>(bloomLevel.value);
    }
    if (difficulty.present) {
      map['difficulty'] = Variable<String>(difficulty.value);
    }
    if (type.present) {
      map['type'] = Variable<String>(type.value);
    }
    if (stem.present) {
      map['stem'] = Variable<String>(stem.value);
    }
    if (stemLatex.present) {
      map['stem_latex'] = Variable<String>(stemLatex.value);
    }
    if (parts.present) {
      map['parts'] =
          Variable<String>($QuestionsTable.$converterparts.toSql(parts.value));
    }
    if (answerScheme.present) {
      map['answer_scheme'] = Variable<String>(
          $QuestionsTable.$converteranswerScheme.toSql(answerScheme.value));
    }
    if (estimatedTimeMinutes.present) {
      map['estimated_time_minutes'] = Variable<int>(estimatedTimeMinutes.value);
    }
    if (marks.present) {
      map['marks'] = Variable<int>(marks.value);
    }
    if (language.present) {
      map['language'] = Variable<String>(language.value);
    }
    if (source.present) {
      map['source'] = Variable<String>(source.value);
    }
    if (qualityScore.present) {
      map['quality_score'] = Variable<double>(qualityScore.value);
    }
    if (tags.present) {
      map['tags'] =
          Variable<String>($QuestionsTable.$convertertags.toSql(tags.value));
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<DateTime>(updatedAt.value);
    }
    if (metadata.present) {
      map['metadata'] = Variable<String>(
          $QuestionsTable.$convertermetadata.toSql(metadata.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('QuestionsCompanion(')
          ..write('id: $id, ')
          ..write('assessmentId: $assessmentId, ')
          ..write('questionBankId: $questionBankId, ')
          ..write('subject: $subject, ')
          ..write('grade: $grade, ')
          ..write('chapterIds: $chapterIds, ')
          ..write('competencyIds: $competencyIds, ')
          ..write('bloomLevel: $bloomLevel, ')
          ..write('difficulty: $difficulty, ')
          ..write('type: $type, ')
          ..write('stem: $stem, ')
          ..write('stemLatex: $stemLatex, ')
          ..write('parts: $parts, ')
          ..write('answerScheme: $answerScheme, ')
          ..write('estimatedTimeMinutes: $estimatedTimeMinutes, ')
          ..write('marks: $marks, ')
          ..write('language: $language, ')
          ..write('source: $source, ')
          ..write('qualityScore: $qualityScore, ')
          ..write('tags: $tags, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('metadata: $metadata, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $AnswerSheetsTable extends AnswerSheets
    with TableInfo<$AnswerSheetsTable, AnswerSheetRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AnswerSheetsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _assessmentIdMeta =
      const VerificationMeta('assessmentId');
  @override
  late final GeneratedColumn<String> assessmentId = GeneratedColumn<String>(
      'assessment_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _studentIdMeta =
      const VerificationMeta('studentId');
  @override
  late final GeneratedColumn<String> studentId = GeneratedColumn<String>(
      'student_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _studentNameMeta =
      const VerificationMeta('studentName');
  @override
  late final GeneratedColumn<String> studentName = GeneratedColumn<String>(
      'student_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _rollNumberMeta =
      const VerificationMeta('rollNumber');
  @override
  late final GeneratedColumn<String> rollNumber = GeneratedColumn<String>(
      'roll_number', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _pagesMeta = const VerificationMeta('pages');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      pages = GeneratedColumn<String>('pages', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $AnswerSheetsTable.$converterpages);
  static const VerificationMeta _scanMetadataMeta =
      const VerificationMeta('scanMetadata');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      scanMetadata = GeneratedColumn<String>(
              'scan_metadata', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $AnswerSheetsTable.$converterscanMetadata);
  static const VerificationMeta _responsesMeta =
      const VerificationMeta('responses');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      responses = GeneratedColumn<String>('responses', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $AnswerSheetsTable.$converterresponses);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _submittedAtMeta =
      const VerificationMeta('submittedAt');
  @override
  late final GeneratedColumn<DateTime> submittedAt = GeneratedColumn<DateTime>(
      'submitted_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _scannedAtMeta =
      const VerificationMeta('scannedAt');
  @override
  late final GeneratedColumn<DateTime> scannedAt = GeneratedColumn<DateTime>(
      'scanned_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _evaluatedAtMeta =
      const VerificationMeta('evaluatedAt');
  @override
  late final GeneratedColumn<DateTime> evaluatedAt = GeneratedColumn<DateTime>(
      'evaluated_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _metadataMeta =
      const VerificationMeta('metadata');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      metadata = GeneratedColumn<String>('metadata', aliasedName, false,
              type: DriftSqlType.string,
              requiredDuringInsert: false,
              defaultValue: const Constant('{}'))
          .withConverter<Map<String, dynamic>>(
              $AnswerSheetsTable.$convertermetadata);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        assessmentId,
        studentId,
        studentName,
        rollNumber,
        pages,
        scanMetadata,
        responses,
        status,
        submittedAt,
        scannedAt,
        evaluatedAt,
        metadata
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'answer_sheets';
  @override
  VerificationContext validateIntegrity(Insertable<AnswerSheetRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('assessment_id')) {
      context.handle(
          _assessmentIdMeta,
          assessmentId.isAcceptableOrUnknown(
              data['assessment_id']!, _assessmentIdMeta));
    } else if (isInserting) {
      context.missing(_assessmentIdMeta);
    }
    if (data.containsKey('student_id')) {
      context.handle(_studentIdMeta,
          studentId.isAcceptableOrUnknown(data['student_id']!, _studentIdMeta));
    } else if (isInserting) {
      context.missing(_studentIdMeta);
    }
    if (data.containsKey('student_name')) {
      context.handle(
          _studentNameMeta,
          studentName.isAcceptableOrUnknown(
              data['student_name']!, _studentNameMeta));
    } else if (isInserting) {
      context.missing(_studentNameMeta);
    }
    if (data.containsKey('roll_number')) {
      context.handle(
          _rollNumberMeta,
          rollNumber.isAcceptableOrUnknown(
              data['roll_number']!, _rollNumberMeta));
    } else if (isInserting) {
      context.missing(_rollNumberMeta);
    }
    context.handle(_pagesMeta, const VerificationResult.success());
    context.handle(_scanMetadataMeta, const VerificationResult.success());
    context.handle(_responsesMeta, const VerificationResult.success());
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('submitted_at')) {
      context.handle(
          _submittedAtMeta,
          submittedAt.isAcceptableOrUnknown(
              data['submitted_at']!, _submittedAtMeta));
    } else if (isInserting) {
      context.missing(_submittedAtMeta);
    }
    if (data.containsKey('scanned_at')) {
      context.handle(_scannedAtMeta,
          scannedAt.isAcceptableOrUnknown(data['scanned_at']!, _scannedAtMeta));
    } else if (isInserting) {
      context.missing(_scannedAtMeta);
    }
    if (data.containsKey('evaluated_at')) {
      context.handle(
          _evaluatedAtMeta,
          evaluatedAt.isAcceptableOrUnknown(
              data['evaluated_at']!, _evaluatedAtMeta));
    }
    context.handle(_metadataMeta, const VerificationResult.success());
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  AnswerSheetRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AnswerSheetRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      assessmentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}assessment_id'])!,
      studentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_id'])!,
      studentName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_name'])!,
      rollNumber: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}roll_number'])!,
      pages: $AnswerSheetsTable.$converterpages.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}pages'])!),
      scanMetadata: $AnswerSheetsTable.$converterscanMetadata.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}scan_metadata'])!),
      responses: $AnswerSheetsTable.$converterresponses.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}responses'])!),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      submittedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}submitted_at'])!,
      scannedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}scanned_at'])!,
      evaluatedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}evaluated_at']),
      metadata: $AnswerSheetsTable.$convertermetadata.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}metadata'])!),
    );
  }

  @override
  $AnswerSheetsTable createAlias(String alias) {
    return $AnswerSheetsTable(attachedDatabase, alias);
  }

  static TypeConverter<Map<String, dynamic>, String> $converterpages =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterscanMetadata =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterresponses =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertermetadata =
      const _JsonConverter();
}

class AnswerSheetRow extends DataClass implements Insertable<AnswerSheetRow> {
  final String id;
  final String assessmentId;
  final String studentId;
  final String studentName;
  final String rollNumber;
  final Map<String, dynamic> pages;
  final Map<String, dynamic> scanMetadata;
  final Map<String, dynamic> responses;
  final String status;
  final DateTime submittedAt;
  final DateTime scannedAt;
  final DateTime? evaluatedAt;
  final Map<String, dynamic> metadata;
  const AnswerSheetRow(
      {required this.id,
      required this.assessmentId,
      required this.studentId,
      required this.studentName,
      required this.rollNumber,
      required this.pages,
      required this.scanMetadata,
      required this.responses,
      required this.status,
      required this.submittedAt,
      required this.scannedAt,
      this.evaluatedAt,
      required this.metadata});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['assessment_id'] = Variable<String>(assessmentId);
    map['student_id'] = Variable<String>(studentId);
    map['student_name'] = Variable<String>(studentName);
    map['roll_number'] = Variable<String>(rollNumber);
    {
      map['pages'] =
          Variable<String>($AnswerSheetsTable.$converterpages.toSql(pages));
    }
    {
      map['scan_metadata'] = Variable<String>(
          $AnswerSheetsTable.$converterscanMetadata.toSql(scanMetadata));
    }
    {
      map['responses'] = Variable<String>(
          $AnswerSheetsTable.$converterresponses.toSql(responses));
    }
    map['status'] = Variable<String>(status);
    map['submitted_at'] = Variable<DateTime>(submittedAt);
    map['scanned_at'] = Variable<DateTime>(scannedAt);
    if (!nullToAbsent || evaluatedAt != null) {
      map['evaluated_at'] = Variable<DateTime>(evaluatedAt);
    }
    {
      map['metadata'] = Variable<String>(
          $AnswerSheetsTable.$convertermetadata.toSql(metadata));
    }
    return map;
  }

  AnswerSheetsCompanion toCompanion(bool nullToAbsent) {
    return AnswerSheetsCompanion(
      id: Value(id),
      assessmentId: Value(assessmentId),
      studentId: Value(studentId),
      studentName: Value(studentName),
      rollNumber: Value(rollNumber),
      pages: Value(pages),
      scanMetadata: Value(scanMetadata),
      responses: Value(responses),
      status: Value(status),
      submittedAt: Value(submittedAt),
      scannedAt: Value(scannedAt),
      evaluatedAt: evaluatedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(evaluatedAt),
      metadata: Value(metadata),
    );
  }

  factory AnswerSheetRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AnswerSheetRow(
      id: serializer.fromJson<String>(json['id']),
      assessmentId: serializer.fromJson<String>(json['assessmentId']),
      studentId: serializer.fromJson<String>(json['studentId']),
      studentName: serializer.fromJson<String>(json['studentName']),
      rollNumber: serializer.fromJson<String>(json['rollNumber']),
      pages: serializer.fromJson<Map<String, dynamic>>(json['pages']),
      scanMetadata:
          serializer.fromJson<Map<String, dynamic>>(json['scanMetadata']),
      responses: serializer.fromJson<Map<String, dynamic>>(json['responses']),
      status: serializer.fromJson<String>(json['status']),
      submittedAt: serializer.fromJson<DateTime>(json['submittedAt']),
      scannedAt: serializer.fromJson<DateTime>(json['scannedAt']),
      evaluatedAt: serializer.fromJson<DateTime?>(json['evaluatedAt']),
      metadata: serializer.fromJson<Map<String, dynamic>>(json['metadata']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'assessmentId': serializer.toJson<String>(assessmentId),
      'studentId': serializer.toJson<String>(studentId),
      'studentName': serializer.toJson<String>(studentName),
      'rollNumber': serializer.toJson<String>(rollNumber),
      'pages': serializer.toJson<Map<String, dynamic>>(pages),
      'scanMetadata': serializer.toJson<Map<String, dynamic>>(scanMetadata),
      'responses': serializer.toJson<Map<String, dynamic>>(responses),
      'status': serializer.toJson<String>(status),
      'submittedAt': serializer.toJson<DateTime>(submittedAt),
      'scannedAt': serializer.toJson<DateTime>(scannedAt),
      'evaluatedAt': serializer.toJson<DateTime?>(evaluatedAt),
      'metadata': serializer.toJson<Map<String, dynamic>>(metadata),
    };
  }

  AnswerSheetRow copyWith(
          {String? id,
          String? assessmentId,
          String? studentId,
          String? studentName,
          String? rollNumber,
          Map<String, dynamic>? pages,
          Map<String, dynamic>? scanMetadata,
          Map<String, dynamic>? responses,
          String? status,
          DateTime? submittedAt,
          DateTime? scannedAt,
          Value<DateTime?> evaluatedAt = const Value.absent(),
          Map<String, dynamic>? metadata}) =>
      AnswerSheetRow(
        id: id ?? this.id,
        assessmentId: assessmentId ?? this.assessmentId,
        studentId: studentId ?? this.studentId,
        studentName: studentName ?? this.studentName,
        rollNumber: rollNumber ?? this.rollNumber,
        pages: pages ?? this.pages,
        scanMetadata: scanMetadata ?? this.scanMetadata,
        responses: responses ?? this.responses,
        status: status ?? this.status,
        submittedAt: submittedAt ?? this.submittedAt,
        scannedAt: scannedAt ?? this.scannedAt,
        evaluatedAt: evaluatedAt.present ? evaluatedAt.value : this.evaluatedAt,
        metadata: metadata ?? this.metadata,
      );
  AnswerSheetRow copyWithCompanion(AnswerSheetsCompanion data) {
    return AnswerSheetRow(
      id: data.id.present ? data.id.value : this.id,
      assessmentId: data.assessmentId.present
          ? data.assessmentId.value
          : this.assessmentId,
      studentId: data.studentId.present ? data.studentId.value : this.studentId,
      studentName:
          data.studentName.present ? data.studentName.value : this.studentName,
      rollNumber:
          data.rollNumber.present ? data.rollNumber.value : this.rollNumber,
      pages: data.pages.present ? data.pages.value : this.pages,
      scanMetadata: data.scanMetadata.present
          ? data.scanMetadata.value
          : this.scanMetadata,
      responses: data.responses.present ? data.responses.value : this.responses,
      status: data.status.present ? data.status.value : this.status,
      submittedAt:
          data.submittedAt.present ? data.submittedAt.value : this.submittedAt,
      scannedAt: data.scannedAt.present ? data.scannedAt.value : this.scannedAt,
      evaluatedAt:
          data.evaluatedAt.present ? data.evaluatedAt.value : this.evaluatedAt,
      metadata: data.metadata.present ? data.metadata.value : this.metadata,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AnswerSheetRow(')
          ..write('id: $id, ')
          ..write('assessmentId: $assessmentId, ')
          ..write('studentId: $studentId, ')
          ..write('studentName: $studentName, ')
          ..write('rollNumber: $rollNumber, ')
          ..write('pages: $pages, ')
          ..write('scanMetadata: $scanMetadata, ')
          ..write('responses: $responses, ')
          ..write('status: $status, ')
          ..write('submittedAt: $submittedAt, ')
          ..write('scannedAt: $scannedAt, ')
          ..write('evaluatedAt: $evaluatedAt, ')
          ..write('metadata: $metadata')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      assessmentId,
      studentId,
      studentName,
      rollNumber,
      pages,
      scanMetadata,
      responses,
      status,
      submittedAt,
      scannedAt,
      evaluatedAt,
      metadata);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AnswerSheetRow &&
          other.id == this.id &&
          other.assessmentId == this.assessmentId &&
          other.studentId == this.studentId &&
          other.studentName == this.studentName &&
          other.rollNumber == this.rollNumber &&
          other.pages == this.pages &&
          other.scanMetadata == this.scanMetadata &&
          other.responses == this.responses &&
          other.status == this.status &&
          other.submittedAt == this.submittedAt &&
          other.scannedAt == this.scannedAt &&
          other.evaluatedAt == this.evaluatedAt &&
          other.metadata == this.metadata);
}

class AnswerSheetsCompanion extends UpdateCompanion<AnswerSheetRow> {
  final Value<String> id;
  final Value<String> assessmentId;
  final Value<String> studentId;
  final Value<String> studentName;
  final Value<String> rollNumber;
  final Value<Map<String, dynamic>> pages;
  final Value<Map<String, dynamic>> scanMetadata;
  final Value<Map<String, dynamic>> responses;
  final Value<String> status;
  final Value<DateTime> submittedAt;
  final Value<DateTime> scannedAt;
  final Value<DateTime?> evaluatedAt;
  final Value<Map<String, dynamic>> metadata;
  final Value<int> rowid;
  const AnswerSheetsCompanion({
    this.id = const Value.absent(),
    this.assessmentId = const Value.absent(),
    this.studentId = const Value.absent(),
    this.studentName = const Value.absent(),
    this.rollNumber = const Value.absent(),
    this.pages = const Value.absent(),
    this.scanMetadata = const Value.absent(),
    this.responses = const Value.absent(),
    this.status = const Value.absent(),
    this.submittedAt = const Value.absent(),
    this.scannedAt = const Value.absent(),
    this.evaluatedAt = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AnswerSheetsCompanion.insert({
    required String id,
    required String assessmentId,
    required String studentId,
    required String studentName,
    required String rollNumber,
    required Map<String, dynamic> pages,
    required Map<String, dynamic> scanMetadata,
    required Map<String, dynamic> responses,
    required String status,
    required DateTime submittedAt,
    required DateTime scannedAt,
    this.evaluatedAt = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        assessmentId = Value(assessmentId),
        studentId = Value(studentId),
        studentName = Value(studentName),
        rollNumber = Value(rollNumber),
        pages = Value(pages),
        scanMetadata = Value(scanMetadata),
        responses = Value(responses),
        status = Value(status),
        submittedAt = Value(submittedAt),
        scannedAt = Value(scannedAt);
  static Insertable<AnswerSheetRow> custom({
    Expression<String>? id,
    Expression<String>? assessmentId,
    Expression<String>? studentId,
    Expression<String>? studentName,
    Expression<String>? rollNumber,
    Expression<String>? pages,
    Expression<String>? scanMetadata,
    Expression<String>? responses,
    Expression<String>? status,
    Expression<DateTime>? submittedAt,
    Expression<DateTime>? scannedAt,
    Expression<DateTime>? evaluatedAt,
    Expression<String>? metadata,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (assessmentId != null) 'assessment_id': assessmentId,
      if (studentId != null) 'student_id': studentId,
      if (studentName != null) 'student_name': studentName,
      if (rollNumber != null) 'roll_number': rollNumber,
      if (pages != null) 'pages': pages,
      if (scanMetadata != null) 'scan_metadata': scanMetadata,
      if (responses != null) 'responses': responses,
      if (status != null) 'status': status,
      if (submittedAt != null) 'submitted_at': submittedAt,
      if (scannedAt != null) 'scanned_at': scannedAt,
      if (evaluatedAt != null) 'evaluated_at': evaluatedAt,
      if (metadata != null) 'metadata': metadata,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AnswerSheetsCompanion copyWith(
      {Value<String>? id,
      Value<String>? assessmentId,
      Value<String>? studentId,
      Value<String>? studentName,
      Value<String>? rollNumber,
      Value<Map<String, dynamic>>? pages,
      Value<Map<String, dynamic>>? scanMetadata,
      Value<Map<String, dynamic>>? responses,
      Value<String>? status,
      Value<DateTime>? submittedAt,
      Value<DateTime>? scannedAt,
      Value<DateTime?>? evaluatedAt,
      Value<Map<String, dynamic>>? metadata,
      Value<int>? rowid}) {
    return AnswerSheetsCompanion(
      id: id ?? this.id,
      assessmentId: assessmentId ?? this.assessmentId,
      studentId: studentId ?? this.studentId,
      studentName: studentName ?? this.studentName,
      rollNumber: rollNumber ?? this.rollNumber,
      pages: pages ?? this.pages,
      scanMetadata: scanMetadata ?? this.scanMetadata,
      responses: responses ?? this.responses,
      status: status ?? this.status,
      submittedAt: submittedAt ?? this.submittedAt,
      scannedAt: scannedAt ?? this.scannedAt,
      evaluatedAt: evaluatedAt ?? this.evaluatedAt,
      metadata: metadata ?? this.metadata,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (assessmentId.present) {
      map['assessment_id'] = Variable<String>(assessmentId.value);
    }
    if (studentId.present) {
      map['student_id'] = Variable<String>(studentId.value);
    }
    if (studentName.present) {
      map['student_name'] = Variable<String>(studentName.value);
    }
    if (rollNumber.present) {
      map['roll_number'] = Variable<String>(rollNumber.value);
    }
    if (pages.present) {
      map['pages'] = Variable<String>(
          $AnswerSheetsTable.$converterpages.toSql(pages.value));
    }
    if (scanMetadata.present) {
      map['scan_metadata'] = Variable<String>(
          $AnswerSheetsTable.$converterscanMetadata.toSql(scanMetadata.value));
    }
    if (responses.present) {
      map['responses'] = Variable<String>(
          $AnswerSheetsTable.$converterresponses.toSql(responses.value));
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (submittedAt.present) {
      map['submitted_at'] = Variable<DateTime>(submittedAt.value);
    }
    if (scannedAt.present) {
      map['scanned_at'] = Variable<DateTime>(scannedAt.value);
    }
    if (evaluatedAt.present) {
      map['evaluated_at'] = Variable<DateTime>(evaluatedAt.value);
    }
    if (metadata.present) {
      map['metadata'] = Variable<String>(
          $AnswerSheetsTable.$convertermetadata.toSql(metadata.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AnswerSheetsCompanion(')
          ..write('id: $id, ')
          ..write('assessmentId: $assessmentId, ')
          ..write('studentId: $studentId, ')
          ..write('studentName: $studentName, ')
          ..write('rollNumber: $rollNumber, ')
          ..write('pages: $pages, ')
          ..write('scanMetadata: $scanMetadata, ')
          ..write('responses: $responses, ')
          ..write('status: $status, ')
          ..write('submittedAt: $submittedAt, ')
          ..write('scannedAt: $scannedAt, ')
          ..write('evaluatedAt: $evaluatedAt, ')
          ..write('metadata: $metadata, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $EvaluationsTable extends Evaluations
    with TableInfo<$EvaluationsTable, Evaluation> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $EvaluationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _answerSheetIdMeta =
      const VerificationMeta('answerSheetId');
  @override
  late final GeneratedColumn<String> answerSheetId = GeneratedColumn<String>(
      'answer_sheet_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _questionIdMeta =
      const VerificationMeta('questionId');
  @override
  late final GeneratedColumn<String> questionId = GeneratedColumn<String>(
      'question_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _studentAnswerMeta =
      const VerificationMeta('studentAnswer');
  @override
  late final GeneratedColumn<String> studentAnswer = GeneratedColumn<String>(
      'student_answer', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _studentAnswerLatexMeta =
      const VerificationMeta('studentAnswerLatex');
  @override
  late final GeneratedColumn<String> studentAnswerLatex =
      GeneratedColumn<String>('student_answer_latex', aliasedName, true,
          type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _studentAnswerImagesMeta =
      const VerificationMeta('studentAnswerImages');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String>
      studentAnswerImages = GeneratedColumn<String>(
              'student_answer_images', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>(
              $EvaluationsTable.$converterstudentAnswerImages);
  static const VerificationMeta _awardedMarksMeta =
      const VerificationMeta('awardedMarks');
  @override
  late final GeneratedColumn<int> awardedMarks = GeneratedColumn<int>(
      'awarded_marks', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _maxMarksMeta =
      const VerificationMeta('maxMarks');
  @override
  late final GeneratedColumn<int> maxMarks = GeneratedColumn<int>(
      'max_marks', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _percentageMeta =
      const VerificationMeta('percentage');
  @override
  late final GeneratedColumn<double> percentage = GeneratedColumn<double>(
      'percentage', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _verdictMeta =
      const VerificationMeta('verdict');
  @override
  late final GeneratedColumn<String> verdict = GeneratedColumn<String>(
      'verdict', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _markingPointsMeta =
      const VerificationMeta('markingPoints');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      markingPoints = GeneratedColumn<String>(
              'marking_points', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $EvaluationsTable.$convertermarkingPoints);
  static const VerificationMeta _rubricLevelMeta =
      const VerificationMeta('rubricLevel');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      rubricLevel = GeneratedColumn<String>('rubric_level', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $EvaluationsTable.$converterrubricLevel);
  static const VerificationMeta _confidenceScoreMeta =
      const VerificationMeta('confidenceScore');
  @override
  late final GeneratedColumn<double> confidenceScore = GeneratedColumn<double>(
      'confidence_score', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _reasoningMeta =
      const VerificationMeta('reasoning');
  @override
  late final GeneratedColumn<String> reasoning = GeneratedColumn<String>(
      'reasoning', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _strengthsMeta =
      const VerificationMeta('strengths');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> strengths =
      GeneratedColumn<String>('strengths', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>($EvaluationsTable.$converterstrengths);
  static const VerificationMeta _gapsMeta = const VerificationMeta('gaps');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> gaps =
      GeneratedColumn<String>('gaps', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>($EvaluationsTable.$convertergaps);
  static const VerificationMeta _carelessErrorsMeta =
      const VerificationMeta('carelessErrors');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String>
      carelessErrors = GeneratedColumn<String>(
              'careless_errors', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>(
              $EvaluationsTable.$convertercarelessErrors);
  static const VerificationMeta _estimatedTimeSpentSecondsMeta =
      const VerificationMeta('estimatedTimeSpentSeconds');
  @override
  late final GeneratedColumn<int> estimatedTimeSpentSeconds =
      GeneratedColumn<int>('estimated_time_spent_seconds', aliasedName, false,
          type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _evaluatedAtMeta =
      const VerificationMeta('evaluatedAt');
  @override
  late final GeneratedColumn<DateTime> evaluatedAt = GeneratedColumn<DateTime>(
      'evaluated_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _teacherCommentMeta =
      const VerificationMeta('teacherComment');
  @override
  late final GeneratedColumn<String> teacherComment = GeneratedColumn<String>(
      'teacher_comment', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _teacherAdjustedMarksMeta =
      const VerificationMeta('teacherAdjustedMarks');
  @override
  late final GeneratedColumn<int> teacherAdjustedMarks = GeneratedColumn<int>(
      'teacher_adjusted_marks', aliasedName, true,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _metadataMeta =
      const VerificationMeta('metadata');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      metadata = GeneratedColumn<String>('metadata', aliasedName, false,
              type: DriftSqlType.string,
              requiredDuringInsert: false,
              defaultValue: const Constant('{}'))
          .withConverter<Map<String, dynamic>>(
              $EvaluationsTable.$convertermetadata);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        answerSheetId,
        questionId,
        studentAnswer,
        studentAnswerLatex,
        studentAnswerImages,
        awardedMarks,
        maxMarks,
        percentage,
        verdict,
        markingPoints,
        rubricLevel,
        confidenceScore,
        reasoning,
        strengths,
        gaps,
        carelessErrors,
        estimatedTimeSpentSeconds,
        status,
        evaluatedAt,
        teacherComment,
        teacherAdjustedMarks,
        metadata
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'evaluations';
  @override
  VerificationContext validateIntegrity(Insertable<Evaluation> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('answer_sheet_id')) {
      context.handle(
          _answerSheetIdMeta,
          answerSheetId.isAcceptableOrUnknown(
              data['answer_sheet_id']!, _answerSheetIdMeta));
    } else if (isInserting) {
      context.missing(_answerSheetIdMeta);
    }
    if (data.containsKey('question_id')) {
      context.handle(
          _questionIdMeta,
          questionId.isAcceptableOrUnknown(
              data['question_id']!, _questionIdMeta));
    } else if (isInserting) {
      context.missing(_questionIdMeta);
    }
    if (data.containsKey('student_answer')) {
      context.handle(
          _studentAnswerMeta,
          studentAnswer.isAcceptableOrUnknown(
              data['student_answer']!, _studentAnswerMeta));
    } else if (isInserting) {
      context.missing(_studentAnswerMeta);
    }
    if (data.containsKey('student_answer_latex')) {
      context.handle(
          _studentAnswerLatexMeta,
          studentAnswerLatex.isAcceptableOrUnknown(
              data['student_answer_latex']!, _studentAnswerLatexMeta));
    }
    context.handle(
        _studentAnswerImagesMeta, const VerificationResult.success());
    if (data.containsKey('awarded_marks')) {
      context.handle(
          _awardedMarksMeta,
          awardedMarks.isAcceptableOrUnknown(
              data['awarded_marks']!, _awardedMarksMeta));
    } else if (isInserting) {
      context.missing(_awardedMarksMeta);
    }
    if (data.containsKey('max_marks')) {
      context.handle(_maxMarksMeta,
          maxMarks.isAcceptableOrUnknown(data['max_marks']!, _maxMarksMeta));
    } else if (isInserting) {
      context.missing(_maxMarksMeta);
    }
    if (data.containsKey('percentage')) {
      context.handle(
          _percentageMeta,
          percentage.isAcceptableOrUnknown(
              data['percentage']!, _percentageMeta));
    } else if (isInserting) {
      context.missing(_percentageMeta);
    }
    if (data.containsKey('verdict')) {
      context.handle(_verdictMeta,
          verdict.isAcceptableOrUnknown(data['verdict']!, _verdictMeta));
    } else if (isInserting) {
      context.missing(_verdictMeta);
    }
    context.handle(_markingPointsMeta, const VerificationResult.success());
    context.handle(_rubricLevelMeta, const VerificationResult.success());
    if (data.containsKey('confidence_score')) {
      context.handle(
          _confidenceScoreMeta,
          confidenceScore.isAcceptableOrUnknown(
              data['confidence_score']!, _confidenceScoreMeta));
    } else if (isInserting) {
      context.missing(_confidenceScoreMeta);
    }
    if (data.containsKey('reasoning')) {
      context.handle(_reasoningMeta,
          reasoning.isAcceptableOrUnknown(data['reasoning']!, _reasoningMeta));
    } else if (isInserting) {
      context.missing(_reasoningMeta);
    }
    context.handle(_strengthsMeta, const VerificationResult.success());
    context.handle(_gapsMeta, const VerificationResult.success());
    context.handle(_carelessErrorsMeta, const VerificationResult.success());
    if (data.containsKey('estimated_time_spent_seconds')) {
      context.handle(
          _estimatedTimeSpentSecondsMeta,
          estimatedTimeSpentSeconds.isAcceptableOrUnknown(
              data['estimated_time_spent_seconds']!,
              _estimatedTimeSpentSecondsMeta));
    } else if (isInserting) {
      context.missing(_estimatedTimeSpentSecondsMeta);
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('evaluated_at')) {
      context.handle(
          _evaluatedAtMeta,
          evaluatedAt.isAcceptableOrUnknown(
              data['evaluated_at']!, _evaluatedAtMeta));
    } else if (isInserting) {
      context.missing(_evaluatedAtMeta);
    }
    if (data.containsKey('teacher_comment')) {
      context.handle(
          _teacherCommentMeta,
          teacherComment.isAcceptableOrUnknown(
              data['teacher_comment']!, _teacherCommentMeta));
    }
    if (data.containsKey('teacher_adjusted_marks')) {
      context.handle(
          _teacherAdjustedMarksMeta,
          teacherAdjustedMarks.isAcceptableOrUnknown(
              data['teacher_adjusted_marks']!, _teacherAdjustedMarksMeta));
    }
    context.handle(_metadataMeta, const VerificationResult.success());
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Evaluation map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Evaluation(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      answerSheetId: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}answer_sheet_id'])!,
      questionId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}question_id'])!,
      studentAnswer: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_answer'])!,
      studentAnswerLatex: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}student_answer_latex']),
      studentAnswerImages: $EvaluationsTable.$converterstudentAnswerImages
          .fromSql(attachedDatabase.typeMapping.read(DriftSqlType.string,
              data['${effectivePrefix}student_answer_images'])!),
      awardedMarks: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}awarded_marks'])!,
      maxMarks: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}max_marks'])!,
      percentage: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}percentage'])!,
      verdict: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}verdict'])!,
      markingPoints: $EvaluationsTable.$convertermarkingPoints.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}marking_points'])!),
      rubricLevel: $EvaluationsTable.$converterrubricLevel.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}rubric_level'])!),
      confidenceScore: attachedDatabase.typeMapping.read(
          DriftSqlType.double, data['${effectivePrefix}confidence_score'])!,
      reasoning: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}reasoning'])!,
      strengths: $EvaluationsTable.$converterstrengths.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}strengths'])!),
      gaps: $EvaluationsTable.$convertergaps.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}gaps'])!),
      carelessErrors: $EvaluationsTable.$convertercarelessErrors.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}careless_errors'])!),
      estimatedTimeSpentSeconds: attachedDatabase.typeMapping.read(
          DriftSqlType.int,
          data['${effectivePrefix}estimated_time_spent_seconds'])!,
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      evaluatedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}evaluated_at'])!,
      teacherComment: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}teacher_comment']),
      teacherAdjustedMarks: attachedDatabase.typeMapping.read(
          DriftSqlType.int, data['${effectivePrefix}teacher_adjusted_marks']),
      metadata: $EvaluationsTable.$convertermetadata.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}metadata'])!),
    );
  }

  @override
  $EvaluationsTable createAlias(String alias) {
    return $EvaluationsTable(attachedDatabase, alias);
  }

  static TypeConverter<List<String>, String> $converterstudentAnswerImages =
      const _StringListConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertermarkingPoints =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterrubricLevel =
      const _JsonConverter();
  static TypeConverter<List<String>, String> $converterstrengths =
      const _StringListConverter();
  static TypeConverter<List<String>, String> $convertergaps =
      const _StringListConverter();
  static TypeConverter<List<String>, String> $convertercarelessErrors =
      const _StringListConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertermetadata =
      const _JsonConverter();
}

class Evaluation extends DataClass implements Insertable<Evaluation> {
  final String id;
  final String answerSheetId;
  final String questionId;
  final String studentAnswer;
  final String? studentAnswerLatex;
  final List<String> studentAnswerImages;
  final int awardedMarks;
  final int maxMarks;
  final double percentage;
  final String verdict;
  final Map<String, dynamic> markingPoints;
  final Map<String, dynamic> rubricLevel;
  final double confidenceScore;
  final String reasoning;
  final List<String> strengths;
  final List<String> gaps;
  final List<String> carelessErrors;
  final int estimatedTimeSpentSeconds;
  final String status;
  final DateTime evaluatedAt;
  final String? teacherComment;
  final int? teacherAdjustedMarks;
  final Map<String, dynamic> metadata;
  const Evaluation(
      {required this.id,
      required this.answerSheetId,
      required this.questionId,
      required this.studentAnswer,
      this.studentAnswerLatex,
      required this.studentAnswerImages,
      required this.awardedMarks,
      required this.maxMarks,
      required this.percentage,
      required this.verdict,
      required this.markingPoints,
      required this.rubricLevel,
      required this.confidenceScore,
      required this.reasoning,
      required this.strengths,
      required this.gaps,
      required this.carelessErrors,
      required this.estimatedTimeSpentSeconds,
      required this.status,
      required this.evaluatedAt,
      this.teacherComment,
      this.teacherAdjustedMarks,
      required this.metadata});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['answer_sheet_id'] = Variable<String>(answerSheetId);
    map['question_id'] = Variable<String>(questionId);
    map['student_answer'] = Variable<String>(studentAnswer);
    if (!nullToAbsent || studentAnswerLatex != null) {
      map['student_answer_latex'] = Variable<String>(studentAnswerLatex);
    }
    {
      map['student_answer_images'] = Variable<String>($EvaluationsTable
          .$converterstudentAnswerImages
          .toSql(studentAnswerImages));
    }
    map['awarded_marks'] = Variable<int>(awardedMarks);
    map['max_marks'] = Variable<int>(maxMarks);
    map['percentage'] = Variable<double>(percentage);
    map['verdict'] = Variable<String>(verdict);
    {
      map['marking_points'] = Variable<String>(
          $EvaluationsTable.$convertermarkingPoints.toSql(markingPoints));
    }
    {
      map['rubric_level'] = Variable<String>(
          $EvaluationsTable.$converterrubricLevel.toSql(rubricLevel));
    }
    map['confidence_score'] = Variable<double>(confidenceScore);
    map['reasoning'] = Variable<String>(reasoning);
    {
      map['strengths'] = Variable<String>(
          $EvaluationsTable.$converterstrengths.toSql(strengths));
    }
    {
      map['gaps'] =
          Variable<String>($EvaluationsTable.$convertergaps.toSql(gaps));
    }
    {
      map['careless_errors'] = Variable<String>(
          $EvaluationsTable.$convertercarelessErrors.toSql(carelessErrors));
    }
    map['estimated_time_spent_seconds'] =
        Variable<int>(estimatedTimeSpentSeconds);
    map['status'] = Variable<String>(status);
    map['evaluated_at'] = Variable<DateTime>(evaluatedAt);
    if (!nullToAbsent || teacherComment != null) {
      map['teacher_comment'] = Variable<String>(teacherComment);
    }
    if (!nullToAbsent || teacherAdjustedMarks != null) {
      map['teacher_adjusted_marks'] = Variable<int>(teacherAdjustedMarks);
    }
    {
      map['metadata'] = Variable<String>(
          $EvaluationsTable.$convertermetadata.toSql(metadata));
    }
    return map;
  }

  EvaluationsCompanion toCompanion(bool nullToAbsent) {
    return EvaluationsCompanion(
      id: Value(id),
      answerSheetId: Value(answerSheetId),
      questionId: Value(questionId),
      studentAnswer: Value(studentAnswer),
      studentAnswerLatex: studentAnswerLatex == null && nullToAbsent
          ? const Value.absent()
          : Value(studentAnswerLatex),
      studentAnswerImages: Value(studentAnswerImages),
      awardedMarks: Value(awardedMarks),
      maxMarks: Value(maxMarks),
      percentage: Value(percentage),
      verdict: Value(verdict),
      markingPoints: Value(markingPoints),
      rubricLevel: Value(rubricLevel),
      confidenceScore: Value(confidenceScore),
      reasoning: Value(reasoning),
      strengths: Value(strengths),
      gaps: Value(gaps),
      carelessErrors: Value(carelessErrors),
      estimatedTimeSpentSeconds: Value(estimatedTimeSpentSeconds),
      status: Value(status),
      evaluatedAt: Value(evaluatedAt),
      teacherComment: teacherComment == null && nullToAbsent
          ? const Value.absent()
          : Value(teacherComment),
      teacherAdjustedMarks: teacherAdjustedMarks == null && nullToAbsent
          ? const Value.absent()
          : Value(teacherAdjustedMarks),
      metadata: Value(metadata),
    );
  }

  factory Evaluation.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Evaluation(
      id: serializer.fromJson<String>(json['id']),
      answerSheetId: serializer.fromJson<String>(json['answerSheetId']),
      questionId: serializer.fromJson<String>(json['questionId']),
      studentAnswer: serializer.fromJson<String>(json['studentAnswer']),
      studentAnswerLatex:
          serializer.fromJson<String?>(json['studentAnswerLatex']),
      studentAnswerImages:
          serializer.fromJson<List<String>>(json['studentAnswerImages']),
      awardedMarks: serializer.fromJson<int>(json['awardedMarks']),
      maxMarks: serializer.fromJson<int>(json['maxMarks']),
      percentage: serializer.fromJson<double>(json['percentage']),
      verdict: serializer.fromJson<String>(json['verdict']),
      markingPoints:
          serializer.fromJson<Map<String, dynamic>>(json['markingPoints']),
      rubricLevel:
          serializer.fromJson<Map<String, dynamic>>(json['rubricLevel']),
      confidenceScore: serializer.fromJson<double>(json['confidenceScore']),
      reasoning: serializer.fromJson<String>(json['reasoning']),
      strengths: serializer.fromJson<List<String>>(json['strengths']),
      gaps: serializer.fromJson<List<String>>(json['gaps']),
      carelessErrors: serializer.fromJson<List<String>>(json['carelessErrors']),
      estimatedTimeSpentSeconds:
          serializer.fromJson<int>(json['estimatedTimeSpentSeconds']),
      status: serializer.fromJson<String>(json['status']),
      evaluatedAt: serializer.fromJson<DateTime>(json['evaluatedAt']),
      teacherComment: serializer.fromJson<String?>(json['teacherComment']),
      teacherAdjustedMarks:
          serializer.fromJson<int?>(json['teacherAdjustedMarks']),
      metadata: serializer.fromJson<Map<String, dynamic>>(json['metadata']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'answerSheetId': serializer.toJson<String>(answerSheetId),
      'questionId': serializer.toJson<String>(questionId),
      'studentAnswer': serializer.toJson<String>(studentAnswer),
      'studentAnswerLatex': serializer.toJson<String?>(studentAnswerLatex),
      'studentAnswerImages':
          serializer.toJson<List<String>>(studentAnswerImages),
      'awardedMarks': serializer.toJson<int>(awardedMarks),
      'maxMarks': serializer.toJson<int>(maxMarks),
      'percentage': serializer.toJson<double>(percentage),
      'verdict': serializer.toJson<String>(verdict),
      'markingPoints': serializer.toJson<Map<String, dynamic>>(markingPoints),
      'rubricLevel': serializer.toJson<Map<String, dynamic>>(rubricLevel),
      'confidenceScore': serializer.toJson<double>(confidenceScore),
      'reasoning': serializer.toJson<String>(reasoning),
      'strengths': serializer.toJson<List<String>>(strengths),
      'gaps': serializer.toJson<List<String>>(gaps),
      'carelessErrors': serializer.toJson<List<String>>(carelessErrors),
      'estimatedTimeSpentSeconds':
          serializer.toJson<int>(estimatedTimeSpentSeconds),
      'status': serializer.toJson<String>(status),
      'evaluatedAt': serializer.toJson<DateTime>(evaluatedAt),
      'teacherComment': serializer.toJson<String?>(teacherComment),
      'teacherAdjustedMarks': serializer.toJson<int?>(teacherAdjustedMarks),
      'metadata': serializer.toJson<Map<String, dynamic>>(metadata),
    };
  }

  Evaluation copyWith(
          {String? id,
          String? answerSheetId,
          String? questionId,
          String? studentAnswer,
          Value<String?> studentAnswerLatex = const Value.absent(),
          List<String>? studentAnswerImages,
          int? awardedMarks,
          int? maxMarks,
          double? percentage,
          String? verdict,
          Map<String, dynamic>? markingPoints,
          Map<String, dynamic>? rubricLevel,
          double? confidenceScore,
          String? reasoning,
          List<String>? strengths,
          List<String>? gaps,
          List<String>? carelessErrors,
          int? estimatedTimeSpentSeconds,
          String? status,
          DateTime? evaluatedAt,
          Value<String?> teacherComment = const Value.absent(),
          Value<int?> teacherAdjustedMarks = const Value.absent(),
          Map<String, dynamic>? metadata}) =>
      Evaluation(
        id: id ?? this.id,
        answerSheetId: answerSheetId ?? this.answerSheetId,
        questionId: questionId ?? this.questionId,
        studentAnswer: studentAnswer ?? this.studentAnswer,
        studentAnswerLatex: studentAnswerLatex.present
            ? studentAnswerLatex.value
            : this.studentAnswerLatex,
        studentAnswerImages: studentAnswerImages ?? this.studentAnswerImages,
        awardedMarks: awardedMarks ?? this.awardedMarks,
        maxMarks: maxMarks ?? this.maxMarks,
        percentage: percentage ?? this.percentage,
        verdict: verdict ?? this.verdict,
        markingPoints: markingPoints ?? this.markingPoints,
        rubricLevel: rubricLevel ?? this.rubricLevel,
        confidenceScore: confidenceScore ?? this.confidenceScore,
        reasoning: reasoning ?? this.reasoning,
        strengths: strengths ?? this.strengths,
        gaps: gaps ?? this.gaps,
        carelessErrors: carelessErrors ?? this.carelessErrors,
        estimatedTimeSpentSeconds:
            estimatedTimeSpentSeconds ?? this.estimatedTimeSpentSeconds,
        status: status ?? this.status,
        evaluatedAt: evaluatedAt ?? this.evaluatedAt,
        teacherComment:
            teacherComment.present ? teacherComment.value : this.teacherComment,
        teacherAdjustedMarks: teacherAdjustedMarks.present
            ? teacherAdjustedMarks.value
            : this.teacherAdjustedMarks,
        metadata: metadata ?? this.metadata,
      );
  Evaluation copyWithCompanion(EvaluationsCompanion data) {
    return Evaluation(
      id: data.id.present ? data.id.value : this.id,
      answerSheetId: data.answerSheetId.present
          ? data.answerSheetId.value
          : this.answerSheetId,
      questionId:
          data.questionId.present ? data.questionId.value : this.questionId,
      studentAnswer: data.studentAnswer.present
          ? data.studentAnswer.value
          : this.studentAnswer,
      studentAnswerLatex: data.studentAnswerLatex.present
          ? data.studentAnswerLatex.value
          : this.studentAnswerLatex,
      studentAnswerImages: data.studentAnswerImages.present
          ? data.studentAnswerImages.value
          : this.studentAnswerImages,
      awardedMarks: data.awardedMarks.present
          ? data.awardedMarks.value
          : this.awardedMarks,
      maxMarks: data.maxMarks.present ? data.maxMarks.value : this.maxMarks,
      percentage:
          data.percentage.present ? data.percentage.value : this.percentage,
      verdict: data.verdict.present ? data.verdict.value : this.verdict,
      markingPoints: data.markingPoints.present
          ? data.markingPoints.value
          : this.markingPoints,
      rubricLevel:
          data.rubricLevel.present ? data.rubricLevel.value : this.rubricLevel,
      confidenceScore: data.confidenceScore.present
          ? data.confidenceScore.value
          : this.confidenceScore,
      reasoning: data.reasoning.present ? data.reasoning.value : this.reasoning,
      strengths: data.strengths.present ? data.strengths.value : this.strengths,
      gaps: data.gaps.present ? data.gaps.value : this.gaps,
      carelessErrors: data.carelessErrors.present
          ? data.carelessErrors.value
          : this.carelessErrors,
      estimatedTimeSpentSeconds: data.estimatedTimeSpentSeconds.present
          ? data.estimatedTimeSpentSeconds.value
          : this.estimatedTimeSpentSeconds,
      status: data.status.present ? data.status.value : this.status,
      evaluatedAt:
          data.evaluatedAt.present ? data.evaluatedAt.value : this.evaluatedAt,
      teacherComment: data.teacherComment.present
          ? data.teacherComment.value
          : this.teacherComment,
      teacherAdjustedMarks: data.teacherAdjustedMarks.present
          ? data.teacherAdjustedMarks.value
          : this.teacherAdjustedMarks,
      metadata: data.metadata.present ? data.metadata.value : this.metadata,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Evaluation(')
          ..write('id: $id, ')
          ..write('answerSheetId: $answerSheetId, ')
          ..write('questionId: $questionId, ')
          ..write('studentAnswer: $studentAnswer, ')
          ..write('studentAnswerLatex: $studentAnswerLatex, ')
          ..write('studentAnswerImages: $studentAnswerImages, ')
          ..write('awardedMarks: $awardedMarks, ')
          ..write('maxMarks: $maxMarks, ')
          ..write('percentage: $percentage, ')
          ..write('verdict: $verdict, ')
          ..write('markingPoints: $markingPoints, ')
          ..write('rubricLevel: $rubricLevel, ')
          ..write('confidenceScore: $confidenceScore, ')
          ..write('reasoning: $reasoning, ')
          ..write('strengths: $strengths, ')
          ..write('gaps: $gaps, ')
          ..write('carelessErrors: $carelessErrors, ')
          ..write('estimatedTimeSpentSeconds: $estimatedTimeSpentSeconds, ')
          ..write('status: $status, ')
          ..write('evaluatedAt: $evaluatedAt, ')
          ..write('teacherComment: $teacherComment, ')
          ..write('teacherAdjustedMarks: $teacherAdjustedMarks, ')
          ..write('metadata: $metadata')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
        id,
        answerSheetId,
        questionId,
        studentAnswer,
        studentAnswerLatex,
        studentAnswerImages,
        awardedMarks,
        maxMarks,
        percentage,
        verdict,
        markingPoints,
        rubricLevel,
        confidenceScore,
        reasoning,
        strengths,
        gaps,
        carelessErrors,
        estimatedTimeSpentSeconds,
        status,
        evaluatedAt,
        teacherComment,
        teacherAdjustedMarks,
        metadata
      ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Evaluation &&
          other.id == this.id &&
          other.answerSheetId == this.answerSheetId &&
          other.questionId == this.questionId &&
          other.studentAnswer == this.studentAnswer &&
          other.studentAnswerLatex == this.studentAnswerLatex &&
          other.studentAnswerImages == this.studentAnswerImages &&
          other.awardedMarks == this.awardedMarks &&
          other.maxMarks == this.maxMarks &&
          other.percentage == this.percentage &&
          other.verdict == this.verdict &&
          other.markingPoints == this.markingPoints &&
          other.rubricLevel == this.rubricLevel &&
          other.confidenceScore == this.confidenceScore &&
          other.reasoning == this.reasoning &&
          other.strengths == this.strengths &&
          other.gaps == this.gaps &&
          other.carelessErrors == this.carelessErrors &&
          other.estimatedTimeSpentSeconds == this.estimatedTimeSpentSeconds &&
          other.status == this.status &&
          other.evaluatedAt == this.evaluatedAt &&
          other.teacherComment == this.teacherComment &&
          other.teacherAdjustedMarks == this.teacherAdjustedMarks &&
          other.metadata == this.metadata);
}

class EvaluationsCompanion extends UpdateCompanion<Evaluation> {
  final Value<String> id;
  final Value<String> answerSheetId;
  final Value<String> questionId;
  final Value<String> studentAnswer;
  final Value<String?> studentAnswerLatex;
  final Value<List<String>> studentAnswerImages;
  final Value<int> awardedMarks;
  final Value<int> maxMarks;
  final Value<double> percentage;
  final Value<String> verdict;
  final Value<Map<String, dynamic>> markingPoints;
  final Value<Map<String, dynamic>> rubricLevel;
  final Value<double> confidenceScore;
  final Value<String> reasoning;
  final Value<List<String>> strengths;
  final Value<List<String>> gaps;
  final Value<List<String>> carelessErrors;
  final Value<int> estimatedTimeSpentSeconds;
  final Value<String> status;
  final Value<DateTime> evaluatedAt;
  final Value<String?> teacherComment;
  final Value<int?> teacherAdjustedMarks;
  final Value<Map<String, dynamic>> metadata;
  final Value<int> rowid;
  const EvaluationsCompanion({
    this.id = const Value.absent(),
    this.answerSheetId = const Value.absent(),
    this.questionId = const Value.absent(),
    this.studentAnswer = const Value.absent(),
    this.studentAnswerLatex = const Value.absent(),
    this.studentAnswerImages = const Value.absent(),
    this.awardedMarks = const Value.absent(),
    this.maxMarks = const Value.absent(),
    this.percentage = const Value.absent(),
    this.verdict = const Value.absent(),
    this.markingPoints = const Value.absent(),
    this.rubricLevel = const Value.absent(),
    this.confidenceScore = const Value.absent(),
    this.reasoning = const Value.absent(),
    this.strengths = const Value.absent(),
    this.gaps = const Value.absent(),
    this.carelessErrors = const Value.absent(),
    this.estimatedTimeSpentSeconds = const Value.absent(),
    this.status = const Value.absent(),
    this.evaluatedAt = const Value.absent(),
    this.teacherComment = const Value.absent(),
    this.teacherAdjustedMarks = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  EvaluationsCompanion.insert({
    required String id,
    required String answerSheetId,
    required String questionId,
    required String studentAnswer,
    this.studentAnswerLatex = const Value.absent(),
    required List<String> studentAnswerImages,
    required int awardedMarks,
    required int maxMarks,
    required double percentage,
    required String verdict,
    required Map<String, dynamic> markingPoints,
    required Map<String, dynamic> rubricLevel,
    required double confidenceScore,
    required String reasoning,
    required List<String> strengths,
    required List<String> gaps,
    required List<String> carelessErrors,
    required int estimatedTimeSpentSeconds,
    required String status,
    required DateTime evaluatedAt,
    this.teacherComment = const Value.absent(),
    this.teacherAdjustedMarks = const Value.absent(),
    this.metadata = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        answerSheetId = Value(answerSheetId),
        questionId = Value(questionId),
        studentAnswer = Value(studentAnswer),
        studentAnswerImages = Value(studentAnswerImages),
        awardedMarks = Value(awardedMarks),
        maxMarks = Value(maxMarks),
        percentage = Value(percentage),
        verdict = Value(verdict),
        markingPoints = Value(markingPoints),
        rubricLevel = Value(rubricLevel),
        confidenceScore = Value(confidenceScore),
        reasoning = Value(reasoning),
        strengths = Value(strengths),
        gaps = Value(gaps),
        carelessErrors = Value(carelessErrors),
        estimatedTimeSpentSeconds = Value(estimatedTimeSpentSeconds),
        status = Value(status),
        evaluatedAt = Value(evaluatedAt);
  static Insertable<Evaluation> custom({
    Expression<String>? id,
    Expression<String>? answerSheetId,
    Expression<String>? questionId,
    Expression<String>? studentAnswer,
    Expression<String>? studentAnswerLatex,
    Expression<String>? studentAnswerImages,
    Expression<int>? awardedMarks,
    Expression<int>? maxMarks,
    Expression<double>? percentage,
    Expression<String>? verdict,
    Expression<String>? markingPoints,
    Expression<String>? rubricLevel,
    Expression<double>? confidenceScore,
    Expression<String>? reasoning,
    Expression<String>? strengths,
    Expression<String>? gaps,
    Expression<String>? carelessErrors,
    Expression<int>? estimatedTimeSpentSeconds,
    Expression<String>? status,
    Expression<DateTime>? evaluatedAt,
    Expression<String>? teacherComment,
    Expression<int>? teacherAdjustedMarks,
    Expression<String>? metadata,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (answerSheetId != null) 'answer_sheet_id': answerSheetId,
      if (questionId != null) 'question_id': questionId,
      if (studentAnswer != null) 'student_answer': studentAnswer,
      if (studentAnswerLatex != null)
        'student_answer_latex': studentAnswerLatex,
      if (studentAnswerImages != null)
        'student_answer_images': studentAnswerImages,
      if (awardedMarks != null) 'awarded_marks': awardedMarks,
      if (maxMarks != null) 'max_marks': maxMarks,
      if (percentage != null) 'percentage': percentage,
      if (verdict != null) 'verdict': verdict,
      if (markingPoints != null) 'marking_points': markingPoints,
      if (rubricLevel != null) 'rubric_level': rubricLevel,
      if (confidenceScore != null) 'confidence_score': confidenceScore,
      if (reasoning != null) 'reasoning': reasoning,
      if (strengths != null) 'strengths': strengths,
      if (gaps != null) 'gaps': gaps,
      if (carelessErrors != null) 'careless_errors': carelessErrors,
      if (estimatedTimeSpentSeconds != null)
        'estimated_time_spent_seconds': estimatedTimeSpentSeconds,
      if (status != null) 'status': status,
      if (evaluatedAt != null) 'evaluated_at': evaluatedAt,
      if (teacherComment != null) 'teacher_comment': teacherComment,
      if (teacherAdjustedMarks != null)
        'teacher_adjusted_marks': teacherAdjustedMarks,
      if (metadata != null) 'metadata': metadata,
      if (rowid != null) 'rowid': rowid,
    });
  }

  EvaluationsCompanion copyWith(
      {Value<String>? id,
      Value<String>? answerSheetId,
      Value<String>? questionId,
      Value<String>? studentAnswer,
      Value<String?>? studentAnswerLatex,
      Value<List<String>>? studentAnswerImages,
      Value<int>? awardedMarks,
      Value<int>? maxMarks,
      Value<double>? percentage,
      Value<String>? verdict,
      Value<Map<String, dynamic>>? markingPoints,
      Value<Map<String, dynamic>>? rubricLevel,
      Value<double>? confidenceScore,
      Value<String>? reasoning,
      Value<List<String>>? strengths,
      Value<List<String>>? gaps,
      Value<List<String>>? carelessErrors,
      Value<int>? estimatedTimeSpentSeconds,
      Value<String>? status,
      Value<DateTime>? evaluatedAt,
      Value<String?>? teacherComment,
      Value<int?>? teacherAdjustedMarks,
      Value<Map<String, dynamic>>? metadata,
      Value<int>? rowid}) {
    return EvaluationsCompanion(
      id: id ?? this.id,
      answerSheetId: answerSheetId ?? this.answerSheetId,
      questionId: questionId ?? this.questionId,
      studentAnswer: studentAnswer ?? this.studentAnswer,
      studentAnswerLatex: studentAnswerLatex ?? this.studentAnswerLatex,
      studentAnswerImages: studentAnswerImages ?? this.studentAnswerImages,
      awardedMarks: awardedMarks ?? this.awardedMarks,
      maxMarks: maxMarks ?? this.maxMarks,
      percentage: percentage ?? this.percentage,
      verdict: verdict ?? this.verdict,
      markingPoints: markingPoints ?? this.markingPoints,
      rubricLevel: rubricLevel ?? this.rubricLevel,
      confidenceScore: confidenceScore ?? this.confidenceScore,
      reasoning: reasoning ?? this.reasoning,
      strengths: strengths ?? this.strengths,
      gaps: gaps ?? this.gaps,
      carelessErrors: carelessErrors ?? this.carelessErrors,
      estimatedTimeSpentSeconds:
          estimatedTimeSpentSeconds ?? this.estimatedTimeSpentSeconds,
      status: status ?? this.status,
      evaluatedAt: evaluatedAt ?? this.evaluatedAt,
      teacherComment: teacherComment ?? this.teacherComment,
      teacherAdjustedMarks: teacherAdjustedMarks ?? this.teacherAdjustedMarks,
      metadata: metadata ?? this.metadata,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (answerSheetId.present) {
      map['answer_sheet_id'] = Variable<String>(answerSheetId.value);
    }
    if (questionId.present) {
      map['question_id'] = Variable<String>(questionId.value);
    }
    if (studentAnswer.present) {
      map['student_answer'] = Variable<String>(studentAnswer.value);
    }
    if (studentAnswerLatex.present) {
      map['student_answer_latex'] = Variable<String>(studentAnswerLatex.value);
    }
    if (studentAnswerImages.present) {
      map['student_answer_images'] = Variable<String>($EvaluationsTable
          .$converterstudentAnswerImages
          .toSql(studentAnswerImages.value));
    }
    if (awardedMarks.present) {
      map['awarded_marks'] = Variable<int>(awardedMarks.value);
    }
    if (maxMarks.present) {
      map['max_marks'] = Variable<int>(maxMarks.value);
    }
    if (percentage.present) {
      map['percentage'] = Variable<double>(percentage.value);
    }
    if (verdict.present) {
      map['verdict'] = Variable<String>(verdict.value);
    }
    if (markingPoints.present) {
      map['marking_points'] = Variable<String>(
          $EvaluationsTable.$convertermarkingPoints.toSql(markingPoints.value));
    }
    if (rubricLevel.present) {
      map['rubric_level'] = Variable<String>(
          $EvaluationsTable.$converterrubricLevel.toSql(rubricLevel.value));
    }
    if (confidenceScore.present) {
      map['confidence_score'] = Variable<double>(confidenceScore.value);
    }
    if (reasoning.present) {
      map['reasoning'] = Variable<String>(reasoning.value);
    }
    if (strengths.present) {
      map['strengths'] = Variable<String>(
          $EvaluationsTable.$converterstrengths.toSql(strengths.value));
    }
    if (gaps.present) {
      map['gaps'] =
          Variable<String>($EvaluationsTable.$convertergaps.toSql(gaps.value));
    }
    if (carelessErrors.present) {
      map['careless_errors'] = Variable<String>($EvaluationsTable
          .$convertercarelessErrors
          .toSql(carelessErrors.value));
    }
    if (estimatedTimeSpentSeconds.present) {
      map['estimated_time_spent_seconds'] =
          Variable<int>(estimatedTimeSpentSeconds.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (evaluatedAt.present) {
      map['evaluated_at'] = Variable<DateTime>(evaluatedAt.value);
    }
    if (teacherComment.present) {
      map['teacher_comment'] = Variable<String>(teacherComment.value);
    }
    if (teacherAdjustedMarks.present) {
      map['teacher_adjusted_marks'] = Variable<int>(teacherAdjustedMarks.value);
    }
    if (metadata.present) {
      map['metadata'] = Variable<String>(
          $EvaluationsTable.$convertermetadata.toSql(metadata.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('EvaluationsCompanion(')
          ..write('id: $id, ')
          ..write('answerSheetId: $answerSheetId, ')
          ..write('questionId: $questionId, ')
          ..write('studentAnswer: $studentAnswer, ')
          ..write('studentAnswerLatex: $studentAnswerLatex, ')
          ..write('studentAnswerImages: $studentAnswerImages, ')
          ..write('awardedMarks: $awardedMarks, ')
          ..write('maxMarks: $maxMarks, ')
          ..write('percentage: $percentage, ')
          ..write('verdict: $verdict, ')
          ..write('markingPoints: $markingPoints, ')
          ..write('rubricLevel: $rubricLevel, ')
          ..write('confidenceScore: $confidenceScore, ')
          ..write('reasoning: $reasoning, ')
          ..write('strengths: $strengths, ')
          ..write('gaps: $gaps, ')
          ..write('carelessErrors: $carelessErrors, ')
          ..write('estimatedTimeSpentSeconds: $estimatedTimeSpentSeconds, ')
          ..write('status: $status, ')
          ..write('evaluatedAt: $evaluatedAt, ')
          ..write('teacherComment: $teacherComment, ')
          ..write('teacherAdjustedMarks: $teacherAdjustedMarks, ')
          ..write('metadata: $metadata, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $StudentMasteryTableTable extends StudentMasteryTable
    with TableInfo<$StudentMasteryTableTable, StudentMasteryTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $StudentMasteryTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _studentIdMeta =
      const VerificationMeta('studentId');
  @override
  late final GeneratedColumn<String> studentId = GeneratedColumn<String>(
      'student_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _schoolIdMeta =
      const VerificationMeta('schoolId');
  @override
  late final GeneratedColumn<String> schoolId = GeneratedColumn<String>(
      'school_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _gradeMeta = const VerificationMeta('grade');
  @override
  late final GeneratedColumn<String> grade = GeneratedColumn<String>(
      'grade', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _conceptsMeta =
      const VerificationMeta('concepts');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      concepts = GeneratedColumn<String>('concepts', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $StudentMasteryTableTable.$converterconcepts);
  static const VerificationMeta _chaptersMeta =
      const VerificationMeta('chapters');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      chapters = GeneratedColumn<String>('chapters', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $StudentMasteryTableTable.$converterchapters);
  static const VerificationMeta _subjectsMeta =
      const VerificationMeta('subjects');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      subjects = GeneratedColumn<String>('subjects', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $StudentMasteryTableTable.$convertersubjects);
  static const VerificationMeta _summaryMeta =
      const VerificationMeta('summary');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      summary = GeneratedColumn<String>('summary', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $StudentMasteryTableTable.$convertersummary);
  static const VerificationMeta _lastUpdatedMeta =
      const VerificationMeta('lastUpdated');
  @override
  late final GeneratedColumn<DateTime> lastUpdated = GeneratedColumn<DateTime>(
      'last_updated', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _versionMeta =
      const VerificationMeta('version');
  @override
  late final GeneratedColumn<int> version = GeneratedColumn<int>(
      'version', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        studentId,
        schoolId,
        grade,
        concepts,
        chapters,
        subjects,
        summary,
        lastUpdated,
        version
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'student_mastery_table';
  @override
  VerificationContext validateIntegrity(
      Insertable<StudentMasteryTableData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('student_id')) {
      context.handle(_studentIdMeta,
          studentId.isAcceptableOrUnknown(data['student_id']!, _studentIdMeta));
    } else if (isInserting) {
      context.missing(_studentIdMeta);
    }
    if (data.containsKey('school_id')) {
      context.handle(_schoolIdMeta,
          schoolId.isAcceptableOrUnknown(data['school_id']!, _schoolIdMeta));
    } else if (isInserting) {
      context.missing(_schoolIdMeta);
    }
    if (data.containsKey('grade')) {
      context.handle(
          _gradeMeta, grade.isAcceptableOrUnknown(data['grade']!, _gradeMeta));
    } else if (isInserting) {
      context.missing(_gradeMeta);
    }
    context.handle(_conceptsMeta, const VerificationResult.success());
    context.handle(_chaptersMeta, const VerificationResult.success());
    context.handle(_subjectsMeta, const VerificationResult.success());
    context.handle(_summaryMeta, const VerificationResult.success());
    if (data.containsKey('last_updated')) {
      context.handle(
          _lastUpdatedMeta,
          lastUpdated.isAcceptableOrUnknown(
              data['last_updated']!, _lastUpdatedMeta));
    } else if (isInserting) {
      context.missing(_lastUpdatedMeta);
    }
    if (data.containsKey('version')) {
      context.handle(_versionMeta,
          version.isAcceptableOrUnknown(data['version']!, _versionMeta));
    } else if (isInserting) {
      context.missing(_versionMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {studentId};
  @override
  StudentMasteryTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return StudentMasteryTableData(
      studentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_id'])!,
      schoolId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}school_id'])!,
      grade: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}grade'])!,
      concepts: $StudentMasteryTableTable.$converterconcepts.fromSql(
          attachedDatabase.typeMapping
              .read(DriftSqlType.string, data['${effectivePrefix}concepts'])!),
      chapters: $StudentMasteryTableTable.$converterchapters.fromSql(
          attachedDatabase.typeMapping
              .read(DriftSqlType.string, data['${effectivePrefix}chapters'])!),
      subjects: $StudentMasteryTableTable.$convertersubjects.fromSql(
          attachedDatabase.typeMapping
              .read(DriftSqlType.string, data['${effectivePrefix}subjects'])!),
      summary: $StudentMasteryTableTable.$convertersummary.fromSql(
          attachedDatabase.typeMapping
              .read(DriftSqlType.string, data['${effectivePrefix}summary'])!),
      lastUpdated: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}last_updated'])!,
      version: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}version'])!,
    );
  }

  @override
  $StudentMasteryTableTable createAlias(String alias) {
    return $StudentMasteryTableTable(attachedDatabase, alias);
  }

  static TypeConverter<Map<String, dynamic>, String> $converterconcepts =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterchapters =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertersubjects =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $convertersummary =
      const _JsonConverter();
}

class StudentMasteryTableData extends DataClass
    implements Insertable<StudentMasteryTableData> {
  final String studentId;
  final String schoolId;
  final String grade;
  final Map<String, dynamic> concepts;
  final Map<String, dynamic> chapters;
  final Map<String, dynamic> subjects;
  final Map<String, dynamic> summary;
  final DateTime lastUpdated;
  final int version;
  const StudentMasteryTableData(
      {required this.studentId,
      required this.schoolId,
      required this.grade,
      required this.concepts,
      required this.chapters,
      required this.subjects,
      required this.summary,
      required this.lastUpdated,
      required this.version});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['student_id'] = Variable<String>(studentId);
    map['school_id'] = Variable<String>(schoolId);
    map['grade'] = Variable<String>(grade);
    {
      map['concepts'] = Variable<String>(
          $StudentMasteryTableTable.$converterconcepts.toSql(concepts));
    }
    {
      map['chapters'] = Variable<String>(
          $StudentMasteryTableTable.$converterchapters.toSql(chapters));
    }
    {
      map['subjects'] = Variable<String>(
          $StudentMasteryTableTable.$convertersubjects.toSql(subjects));
    }
    {
      map['summary'] = Variable<String>(
          $StudentMasteryTableTable.$convertersummary.toSql(summary));
    }
    map['last_updated'] = Variable<DateTime>(lastUpdated);
    map['version'] = Variable<int>(version);
    return map;
  }

  StudentMasteryTableCompanion toCompanion(bool nullToAbsent) {
    return StudentMasteryTableCompanion(
      studentId: Value(studentId),
      schoolId: Value(schoolId),
      grade: Value(grade),
      concepts: Value(concepts),
      chapters: Value(chapters),
      subjects: Value(subjects),
      summary: Value(summary),
      lastUpdated: Value(lastUpdated),
      version: Value(version),
    );
  }

  factory StudentMasteryTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return StudentMasteryTableData(
      studentId: serializer.fromJson<String>(json['studentId']),
      schoolId: serializer.fromJson<String>(json['schoolId']),
      grade: serializer.fromJson<String>(json['grade']),
      concepts: serializer.fromJson<Map<String, dynamic>>(json['concepts']),
      chapters: serializer.fromJson<Map<String, dynamic>>(json['chapters']),
      subjects: serializer.fromJson<Map<String, dynamic>>(json['subjects']),
      summary: serializer.fromJson<Map<String, dynamic>>(json['summary']),
      lastUpdated: serializer.fromJson<DateTime>(json['lastUpdated']),
      version: serializer.fromJson<int>(json['version']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'studentId': serializer.toJson<String>(studentId),
      'schoolId': serializer.toJson<String>(schoolId),
      'grade': serializer.toJson<String>(grade),
      'concepts': serializer.toJson<Map<String, dynamic>>(concepts),
      'chapters': serializer.toJson<Map<String, dynamic>>(chapters),
      'subjects': serializer.toJson<Map<String, dynamic>>(subjects),
      'summary': serializer.toJson<Map<String, dynamic>>(summary),
      'lastUpdated': serializer.toJson<DateTime>(lastUpdated),
      'version': serializer.toJson<int>(version),
    };
  }

  StudentMasteryTableData copyWith(
          {String? studentId,
          String? schoolId,
          String? grade,
          Map<String, dynamic>? concepts,
          Map<String, dynamic>? chapters,
          Map<String, dynamic>? subjects,
          Map<String, dynamic>? summary,
          DateTime? lastUpdated,
          int? version}) =>
      StudentMasteryTableData(
        studentId: studentId ?? this.studentId,
        schoolId: schoolId ?? this.schoolId,
        grade: grade ?? this.grade,
        concepts: concepts ?? this.concepts,
        chapters: chapters ?? this.chapters,
        subjects: subjects ?? this.subjects,
        summary: summary ?? this.summary,
        lastUpdated: lastUpdated ?? this.lastUpdated,
        version: version ?? this.version,
      );
  StudentMasteryTableData copyWithCompanion(StudentMasteryTableCompanion data) {
    return StudentMasteryTableData(
      studentId: data.studentId.present ? data.studentId.value : this.studentId,
      schoolId: data.schoolId.present ? data.schoolId.value : this.schoolId,
      grade: data.grade.present ? data.grade.value : this.grade,
      concepts: data.concepts.present ? data.concepts.value : this.concepts,
      chapters: data.chapters.present ? data.chapters.value : this.chapters,
      subjects: data.subjects.present ? data.subjects.value : this.subjects,
      summary: data.summary.present ? data.summary.value : this.summary,
      lastUpdated:
          data.lastUpdated.present ? data.lastUpdated.value : this.lastUpdated,
      version: data.version.present ? data.version.value : this.version,
    );
  }

  @override
  String toString() {
    return (StringBuffer('StudentMasteryTableData(')
          ..write('studentId: $studentId, ')
          ..write('schoolId: $schoolId, ')
          ..write('grade: $grade, ')
          ..write('concepts: $concepts, ')
          ..write('chapters: $chapters, ')
          ..write('subjects: $subjects, ')
          ..write('summary: $summary, ')
          ..write('lastUpdated: $lastUpdated, ')
          ..write('version: $version')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(studentId, schoolId, grade, concepts,
      chapters, subjects, summary, lastUpdated, version);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is StudentMasteryTableData &&
          other.studentId == this.studentId &&
          other.schoolId == this.schoolId &&
          other.grade == this.grade &&
          other.concepts == this.concepts &&
          other.chapters == this.chapters &&
          other.subjects == this.subjects &&
          other.summary == this.summary &&
          other.lastUpdated == this.lastUpdated &&
          other.version == this.version);
}

class StudentMasteryTableCompanion
    extends UpdateCompanion<StudentMasteryTableData> {
  final Value<String> studentId;
  final Value<String> schoolId;
  final Value<String> grade;
  final Value<Map<String, dynamic>> concepts;
  final Value<Map<String, dynamic>> chapters;
  final Value<Map<String, dynamic>> subjects;
  final Value<Map<String, dynamic>> summary;
  final Value<DateTime> lastUpdated;
  final Value<int> version;
  final Value<int> rowid;
  const StudentMasteryTableCompanion({
    this.studentId = const Value.absent(),
    this.schoolId = const Value.absent(),
    this.grade = const Value.absent(),
    this.concepts = const Value.absent(),
    this.chapters = const Value.absent(),
    this.subjects = const Value.absent(),
    this.summary = const Value.absent(),
    this.lastUpdated = const Value.absent(),
    this.version = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  StudentMasteryTableCompanion.insert({
    required String studentId,
    required String schoolId,
    required String grade,
    required Map<String, dynamic> concepts,
    required Map<String, dynamic> chapters,
    required Map<String, dynamic> subjects,
    required Map<String, dynamic> summary,
    required DateTime lastUpdated,
    required int version,
    this.rowid = const Value.absent(),
  })  : studentId = Value(studentId),
        schoolId = Value(schoolId),
        grade = Value(grade),
        concepts = Value(concepts),
        chapters = Value(chapters),
        subjects = Value(subjects),
        summary = Value(summary),
        lastUpdated = Value(lastUpdated),
        version = Value(version);
  static Insertable<StudentMasteryTableData> custom({
    Expression<String>? studentId,
    Expression<String>? schoolId,
    Expression<String>? grade,
    Expression<String>? concepts,
    Expression<String>? chapters,
    Expression<String>? subjects,
    Expression<String>? summary,
    Expression<DateTime>? lastUpdated,
    Expression<int>? version,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (studentId != null) 'student_id': studentId,
      if (schoolId != null) 'school_id': schoolId,
      if (grade != null) 'grade': grade,
      if (concepts != null) 'concepts': concepts,
      if (chapters != null) 'chapters': chapters,
      if (subjects != null) 'subjects': subjects,
      if (summary != null) 'summary': summary,
      if (lastUpdated != null) 'last_updated': lastUpdated,
      if (version != null) 'version': version,
      if (rowid != null) 'rowid': rowid,
    });
  }

  StudentMasteryTableCompanion copyWith(
      {Value<String>? studentId,
      Value<String>? schoolId,
      Value<String>? grade,
      Value<Map<String, dynamic>>? concepts,
      Value<Map<String, dynamic>>? chapters,
      Value<Map<String, dynamic>>? subjects,
      Value<Map<String, dynamic>>? summary,
      Value<DateTime>? lastUpdated,
      Value<int>? version,
      Value<int>? rowid}) {
    return StudentMasteryTableCompanion(
      studentId: studentId ?? this.studentId,
      schoolId: schoolId ?? this.schoolId,
      grade: grade ?? this.grade,
      concepts: concepts ?? this.concepts,
      chapters: chapters ?? this.chapters,
      subjects: subjects ?? this.subjects,
      summary: summary ?? this.summary,
      lastUpdated: lastUpdated ?? this.lastUpdated,
      version: version ?? this.version,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (studentId.present) {
      map['student_id'] = Variable<String>(studentId.value);
    }
    if (schoolId.present) {
      map['school_id'] = Variable<String>(schoolId.value);
    }
    if (grade.present) {
      map['grade'] = Variable<String>(grade.value);
    }
    if (concepts.present) {
      map['concepts'] = Variable<String>(
          $StudentMasteryTableTable.$converterconcepts.toSql(concepts.value));
    }
    if (chapters.present) {
      map['chapters'] = Variable<String>(
          $StudentMasteryTableTable.$converterchapters.toSql(chapters.value));
    }
    if (subjects.present) {
      map['subjects'] = Variable<String>(
          $StudentMasteryTableTable.$convertersubjects.toSql(subjects.value));
    }
    if (summary.present) {
      map['summary'] = Variable<String>(
          $StudentMasteryTableTable.$convertersummary.toSql(summary.value));
    }
    if (lastUpdated.present) {
      map['last_updated'] = Variable<DateTime>(lastUpdated.value);
    }
    if (version.present) {
      map['version'] = Variable<int>(version.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('StudentMasteryTableCompanion(')
          ..write('studentId: $studentId, ')
          ..write('schoolId: $schoolId, ')
          ..write('grade: $grade, ')
          ..write('concepts: $concepts, ')
          ..write('chapters: $chapters, ')
          ..write('subjects: $subjects, ')
          ..write('summary: $summary, ')
          ..write('lastUpdated: $lastUpdated, ')
          ..write('version: $version, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $PracticeSessionsTable extends PracticeSessions
    with TableInfo<$PracticeSessionsTable, PracticeSessionRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PracticeSessionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _studentIdMeta =
      const VerificationMeta('studentId');
  @override
  late final GeneratedColumn<String> studentId = GeneratedColumn<String>(
      'student_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _conceptIdsMeta =
      const VerificationMeta('conceptIds');
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> conceptIds =
      GeneratedColumn<String>('concept_ids', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<List<String>>(
              $PracticeSessionsTable.$converterconceptIds);
  static const VerificationMeta _typeMeta = const VerificationMeta('type');
  @override
  late final GeneratedColumn<String> type = GeneratedColumn<String>(
      'type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _questionCountMeta =
      const VerificationMeta('questionCount');
  @override
  late final GeneratedColumn<int> questionCount = GeneratedColumn<int>(
      'question_count', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _durationMinutesMeta =
      const VerificationMeta('durationMinutes');
  @override
  late final GeneratedColumn<int> durationMinutes = GeneratedColumn<int>(
      'duration_minutes', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _questionsMeta =
      const VerificationMeta('questions');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      questions = GeneratedColumn<String>('questions', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $PracticeSessionsTable.$converterquestions);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _startedAtMeta =
      const VerificationMeta('startedAt');
  @override
  late final GeneratedColumn<DateTime> startedAt = GeneratedColumn<DateTime>(
      'started_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _completedAtMeta =
      const VerificationMeta('completedAt');
  @override
  late final GeneratedColumn<DateTime> completedAt = GeneratedColumn<DateTime>(
      'completed_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _resultMeta = const VerificationMeta('result');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>?, String>
      result = GeneratedColumn<String>('result', aliasedName, true,
              type: DriftSqlType.string, requiredDuringInsert: false)
          .withConverter<Map<String, dynamic>?>(
              $PracticeSessionsTable.$converterresultn);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        studentId,
        conceptIds,
        type,
        questionCount,
        durationMinutes,
        questions,
        status,
        createdAt,
        startedAt,
        completedAt,
        result
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'practice_sessions';
  @override
  VerificationContext validateIntegrity(Insertable<PracticeSessionRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('student_id')) {
      context.handle(_studentIdMeta,
          studentId.isAcceptableOrUnknown(data['student_id']!, _studentIdMeta));
    } else if (isInserting) {
      context.missing(_studentIdMeta);
    }
    context.handle(_conceptIdsMeta, const VerificationResult.success());
    if (data.containsKey('type')) {
      context.handle(
          _typeMeta, type.isAcceptableOrUnknown(data['type']!, _typeMeta));
    } else if (isInserting) {
      context.missing(_typeMeta);
    }
    if (data.containsKey('question_count')) {
      context.handle(
          _questionCountMeta,
          questionCount.isAcceptableOrUnknown(
              data['question_count']!, _questionCountMeta));
    } else if (isInserting) {
      context.missing(_questionCountMeta);
    }
    if (data.containsKey('duration_minutes')) {
      context.handle(
          _durationMinutesMeta,
          durationMinutes.isAcceptableOrUnknown(
              data['duration_minutes']!, _durationMinutesMeta));
    } else if (isInserting) {
      context.missing(_durationMinutesMeta);
    }
    context.handle(_questionsMeta, const VerificationResult.success());
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('started_at')) {
      context.handle(_startedAtMeta,
          startedAt.isAcceptableOrUnknown(data['started_at']!, _startedAtMeta));
    }
    if (data.containsKey('completed_at')) {
      context.handle(
          _completedAtMeta,
          completedAt.isAcceptableOrUnknown(
              data['completed_at']!, _completedAtMeta));
    }
    context.handle(_resultMeta, const VerificationResult.success());
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  PracticeSessionRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PracticeSessionRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      studentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_id'])!,
      conceptIds: $PracticeSessionsTable.$converterconceptIds.fromSql(
          attachedDatabase.typeMapping.read(
              DriftSqlType.string, data['${effectivePrefix}concept_ids'])!),
      type: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}type'])!,
      questionCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}question_count'])!,
      durationMinutes: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}duration_minutes'])!,
      questions: $PracticeSessionsTable.$converterquestions.fromSql(
          attachedDatabase.typeMapping
              .read(DriftSqlType.string, data['${effectivePrefix}questions'])!),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      startedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}started_at']),
      completedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}completed_at']),
      result: $PracticeSessionsTable.$converterresultn.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}result'])),
    );
  }

  @override
  $PracticeSessionsTable createAlias(String alias) {
    return $PracticeSessionsTable(attachedDatabase, alias);
  }

  static TypeConverter<List<String>, String> $converterconceptIds =
      const _StringListConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterquestions =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>, String> $converterresult =
      const _JsonConverter();
  static TypeConverter<Map<String, dynamic>?, String?> $converterresultn =
      NullAwareTypeConverter.wrap($converterresult);
}

class PracticeSessionRow extends DataClass
    implements Insertable<PracticeSessionRow> {
  final String id;
  final String studentId;
  final List<String> conceptIds;
  final String type;
  final int questionCount;
  final int durationMinutes;
  final Map<String, dynamic> questions;
  final String status;
  final DateTime createdAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final Map<String, dynamic>? result;
  const PracticeSessionRow(
      {required this.id,
      required this.studentId,
      required this.conceptIds,
      required this.type,
      required this.questionCount,
      required this.durationMinutes,
      required this.questions,
      required this.status,
      required this.createdAt,
      this.startedAt,
      this.completedAt,
      this.result});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['student_id'] = Variable<String>(studentId);
    {
      map['concept_ids'] = Variable<String>(
          $PracticeSessionsTable.$converterconceptIds.toSql(conceptIds));
    }
    map['type'] = Variable<String>(type);
    map['question_count'] = Variable<int>(questionCount);
    map['duration_minutes'] = Variable<int>(durationMinutes);
    {
      map['questions'] = Variable<String>(
          $PracticeSessionsTable.$converterquestions.toSql(questions));
    }
    map['status'] = Variable<String>(status);
    map['created_at'] = Variable<DateTime>(createdAt);
    if (!nullToAbsent || startedAt != null) {
      map['started_at'] = Variable<DateTime>(startedAt);
    }
    if (!nullToAbsent || completedAt != null) {
      map['completed_at'] = Variable<DateTime>(completedAt);
    }
    if (!nullToAbsent || result != null) {
      map['result'] = Variable<String>(
          $PracticeSessionsTable.$converterresultn.toSql(result));
    }
    return map;
  }

  PracticeSessionsCompanion toCompanion(bool nullToAbsent) {
    return PracticeSessionsCompanion(
      id: Value(id),
      studentId: Value(studentId),
      conceptIds: Value(conceptIds),
      type: Value(type),
      questionCount: Value(questionCount),
      durationMinutes: Value(durationMinutes),
      questions: Value(questions),
      status: Value(status),
      createdAt: Value(createdAt),
      startedAt: startedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(startedAt),
      completedAt: completedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(completedAt),
      result:
          result == null && nullToAbsent ? const Value.absent() : Value(result),
    );
  }

  factory PracticeSessionRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PracticeSessionRow(
      id: serializer.fromJson<String>(json['id']),
      studentId: serializer.fromJson<String>(json['studentId']),
      conceptIds: serializer.fromJson<List<String>>(json['conceptIds']),
      type: serializer.fromJson<String>(json['type']),
      questionCount: serializer.fromJson<int>(json['questionCount']),
      durationMinutes: serializer.fromJson<int>(json['durationMinutes']),
      questions: serializer.fromJson<Map<String, dynamic>>(json['questions']),
      status: serializer.fromJson<String>(json['status']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      startedAt: serializer.fromJson<DateTime?>(json['startedAt']),
      completedAt: serializer.fromJson<DateTime?>(json['completedAt']),
      result: serializer.fromJson<Map<String, dynamic>?>(json['result']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'studentId': serializer.toJson<String>(studentId),
      'conceptIds': serializer.toJson<List<String>>(conceptIds),
      'type': serializer.toJson<String>(type),
      'questionCount': serializer.toJson<int>(questionCount),
      'durationMinutes': serializer.toJson<int>(durationMinutes),
      'questions': serializer.toJson<Map<String, dynamic>>(questions),
      'status': serializer.toJson<String>(status),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'startedAt': serializer.toJson<DateTime?>(startedAt),
      'completedAt': serializer.toJson<DateTime?>(completedAt),
      'result': serializer.toJson<Map<String, dynamic>?>(result),
    };
  }

  PracticeSessionRow copyWith(
          {String? id,
          String? studentId,
          List<String>? conceptIds,
          String? type,
          int? questionCount,
          int? durationMinutes,
          Map<String, dynamic>? questions,
          String? status,
          DateTime? createdAt,
          Value<DateTime?> startedAt = const Value.absent(),
          Value<DateTime?> completedAt = const Value.absent(),
          Value<Map<String, dynamic>?> result = const Value.absent()}) =>
      PracticeSessionRow(
        id: id ?? this.id,
        studentId: studentId ?? this.studentId,
        conceptIds: conceptIds ?? this.conceptIds,
        type: type ?? this.type,
        questionCount: questionCount ?? this.questionCount,
        durationMinutes: durationMinutes ?? this.durationMinutes,
        questions: questions ?? this.questions,
        status: status ?? this.status,
        createdAt: createdAt ?? this.createdAt,
        startedAt: startedAt.present ? startedAt.value : this.startedAt,
        completedAt: completedAt.present ? completedAt.value : this.completedAt,
        result: result.present ? result.value : this.result,
      );
  PracticeSessionRow copyWithCompanion(PracticeSessionsCompanion data) {
    return PracticeSessionRow(
      id: data.id.present ? data.id.value : this.id,
      studentId: data.studentId.present ? data.studentId.value : this.studentId,
      conceptIds:
          data.conceptIds.present ? data.conceptIds.value : this.conceptIds,
      type: data.type.present ? data.type.value : this.type,
      questionCount: data.questionCount.present
          ? data.questionCount.value
          : this.questionCount,
      durationMinutes: data.durationMinutes.present
          ? data.durationMinutes.value
          : this.durationMinutes,
      questions: data.questions.present ? data.questions.value : this.questions,
      status: data.status.present ? data.status.value : this.status,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      startedAt: data.startedAt.present ? data.startedAt.value : this.startedAt,
      completedAt:
          data.completedAt.present ? data.completedAt.value : this.completedAt,
      result: data.result.present ? data.result.value : this.result,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PracticeSessionRow(')
          ..write('id: $id, ')
          ..write('studentId: $studentId, ')
          ..write('conceptIds: $conceptIds, ')
          ..write('type: $type, ')
          ..write('questionCount: $questionCount, ')
          ..write('durationMinutes: $durationMinutes, ')
          ..write('questions: $questions, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('startedAt: $startedAt, ')
          ..write('completedAt: $completedAt, ')
          ..write('result: $result')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      studentId,
      conceptIds,
      type,
      questionCount,
      durationMinutes,
      questions,
      status,
      createdAt,
      startedAt,
      completedAt,
      result);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PracticeSessionRow &&
          other.id == this.id &&
          other.studentId == this.studentId &&
          other.conceptIds == this.conceptIds &&
          other.type == this.type &&
          other.questionCount == this.questionCount &&
          other.durationMinutes == this.durationMinutes &&
          other.questions == this.questions &&
          other.status == this.status &&
          other.createdAt == this.createdAt &&
          other.startedAt == this.startedAt &&
          other.completedAt == this.completedAt &&
          other.result == this.result);
}

class PracticeSessionsCompanion extends UpdateCompanion<PracticeSessionRow> {
  final Value<String> id;
  final Value<String> studentId;
  final Value<List<String>> conceptIds;
  final Value<String> type;
  final Value<int> questionCount;
  final Value<int> durationMinutes;
  final Value<Map<String, dynamic>> questions;
  final Value<String> status;
  final Value<DateTime> createdAt;
  final Value<DateTime?> startedAt;
  final Value<DateTime?> completedAt;
  final Value<Map<String, dynamic>?> result;
  final Value<int> rowid;
  const PracticeSessionsCompanion({
    this.id = const Value.absent(),
    this.studentId = const Value.absent(),
    this.conceptIds = const Value.absent(),
    this.type = const Value.absent(),
    this.questionCount = const Value.absent(),
    this.durationMinutes = const Value.absent(),
    this.questions = const Value.absent(),
    this.status = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.startedAt = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.result = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  PracticeSessionsCompanion.insert({
    required String id,
    required String studentId,
    required List<String> conceptIds,
    required String type,
    required int questionCount,
    required int durationMinutes,
    required Map<String, dynamic> questions,
    required String status,
    required DateTime createdAt,
    this.startedAt = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.result = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        studentId = Value(studentId),
        conceptIds = Value(conceptIds),
        type = Value(type),
        questionCount = Value(questionCount),
        durationMinutes = Value(durationMinutes),
        questions = Value(questions),
        status = Value(status),
        createdAt = Value(createdAt);
  static Insertable<PracticeSessionRow> custom({
    Expression<String>? id,
    Expression<String>? studentId,
    Expression<String>? conceptIds,
    Expression<String>? type,
    Expression<int>? questionCount,
    Expression<int>? durationMinutes,
    Expression<String>? questions,
    Expression<String>? status,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? startedAt,
    Expression<DateTime>? completedAt,
    Expression<String>? result,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (studentId != null) 'student_id': studentId,
      if (conceptIds != null) 'concept_ids': conceptIds,
      if (type != null) 'type': type,
      if (questionCount != null) 'question_count': questionCount,
      if (durationMinutes != null) 'duration_minutes': durationMinutes,
      if (questions != null) 'questions': questions,
      if (status != null) 'status': status,
      if (createdAt != null) 'created_at': createdAt,
      if (startedAt != null) 'started_at': startedAt,
      if (completedAt != null) 'completed_at': completedAt,
      if (result != null) 'result': result,
      if (rowid != null) 'rowid': rowid,
    });
  }

  PracticeSessionsCompanion copyWith(
      {Value<String>? id,
      Value<String>? studentId,
      Value<List<String>>? conceptIds,
      Value<String>? type,
      Value<int>? questionCount,
      Value<int>? durationMinutes,
      Value<Map<String, dynamic>>? questions,
      Value<String>? status,
      Value<DateTime>? createdAt,
      Value<DateTime?>? startedAt,
      Value<DateTime?>? completedAt,
      Value<Map<String, dynamic>?>? result,
      Value<int>? rowid}) {
    return PracticeSessionsCompanion(
      id: id ?? this.id,
      studentId: studentId ?? this.studentId,
      conceptIds: conceptIds ?? this.conceptIds,
      type: type ?? this.type,
      questionCount: questionCount ?? this.questionCount,
      durationMinutes: durationMinutes ?? this.durationMinutes,
      questions: questions ?? this.questions,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      startedAt: startedAt ?? this.startedAt,
      completedAt: completedAt ?? this.completedAt,
      result: result ?? this.result,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (studentId.present) {
      map['student_id'] = Variable<String>(studentId.value);
    }
    if (conceptIds.present) {
      map['concept_ids'] = Variable<String>(
          $PracticeSessionsTable.$converterconceptIds.toSql(conceptIds.value));
    }
    if (type.present) {
      map['type'] = Variable<String>(type.value);
    }
    if (questionCount.present) {
      map['question_count'] = Variable<int>(questionCount.value);
    }
    if (durationMinutes.present) {
      map['duration_minutes'] = Variable<int>(durationMinutes.value);
    }
    if (questions.present) {
      map['questions'] = Variable<String>(
          $PracticeSessionsTable.$converterquestions.toSql(questions.value));
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (startedAt.present) {
      map['started_at'] = Variable<DateTime>(startedAt.value);
    }
    if (completedAt.present) {
      map['completed_at'] = Variable<DateTime>(completedAt.value);
    }
    if (result.present) {
      map['result'] = Variable<String>(
          $PracticeSessionsTable.$converterresultn.toSql(result.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PracticeSessionsCompanion(')
          ..write('id: $id, ')
          ..write('studentId: $studentId, ')
          ..write('conceptIds: $conceptIds, ')
          ..write('type: $type, ')
          ..write('questionCount: $questionCount, ')
          ..write('durationMinutes: $durationMinutes, ')
          ..write('questions: $questions, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('startedAt: $startedAt, ')
          ..write('completedAt: $completedAt, ')
          ..write('result: $result, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ReportsTable extends Reports with TableInfo<$ReportsTable, Report> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ReportsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _assessmentIdMeta =
      const VerificationMeta('assessmentId');
  @override
  late final GeneratedColumn<String> assessmentId = GeneratedColumn<String>(
      'assessment_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _assessmentTitleMeta =
      const VerificationMeta('assessmentTitle');
  @override
  late final GeneratedColumn<String> assessmentTitle = GeneratedColumn<String>(
      'assessment_title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _studentIdMeta =
      const VerificationMeta('studentId');
  @override
  late final GeneratedColumn<String> studentId = GeneratedColumn<String>(
      'student_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _studentNameMeta =
      const VerificationMeta('studentName');
  @override
  late final GeneratedColumn<String> studentName = GeneratedColumn<String>(
      'student_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _rollNumberMeta =
      const VerificationMeta('rollNumber');
  @override
  late final GeneratedColumn<String> rollNumber = GeneratedColumn<String>(
      'roll_number', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _gradeMeta = const VerificationMeta('grade');
  @override
  late final GeneratedColumn<int> grade = GeneratedColumn<int>(
      'grade', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _sectionMeta =
      const VerificationMeta('section');
  @override
  late final GeneratedColumn<String> section = GeneratedColumn<String>(
      'section', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _reportMeta = const VerificationMeta('report');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      report = GeneratedColumn<String>('report', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>($ReportsTable.$converterreport);
  static const VerificationMeta _generatedAtMeta =
      const VerificationMeta('generatedAt');
  @override
  late final GeneratedColumn<DateTime> generatedAt = GeneratedColumn<DateTime>(
      'generated_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _generatedByMeta =
      const VerificationMeta('generatedBy');
  @override
  late final GeneratedColumn<String> generatedBy = GeneratedColumn<String>(
      'generated_by', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        assessmentId,
        assessmentTitle,
        studentId,
        studentName,
        rollNumber,
        grade,
        section,
        report,
        generatedAt,
        generatedBy
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'reports';
  @override
  VerificationContext validateIntegrity(Insertable<Report> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('assessment_id')) {
      context.handle(
          _assessmentIdMeta,
          assessmentId.isAcceptableOrUnknown(
              data['assessment_id']!, _assessmentIdMeta));
    } else if (isInserting) {
      context.missing(_assessmentIdMeta);
    }
    if (data.containsKey('assessment_title')) {
      context.handle(
          _assessmentTitleMeta,
          assessmentTitle.isAcceptableOrUnknown(
              data['assessment_title']!, _assessmentTitleMeta));
    } else if (isInserting) {
      context.missing(_assessmentTitleMeta);
    }
    if (data.containsKey('student_id')) {
      context.handle(_studentIdMeta,
          studentId.isAcceptableOrUnknown(data['student_id']!, _studentIdMeta));
    } else if (isInserting) {
      context.missing(_studentIdMeta);
    }
    if (data.containsKey('student_name')) {
      context.handle(
          _studentNameMeta,
          studentName.isAcceptableOrUnknown(
              data['student_name']!, _studentNameMeta));
    } else if (isInserting) {
      context.missing(_studentNameMeta);
    }
    if (data.containsKey('roll_number')) {
      context.handle(
          _rollNumberMeta,
          rollNumber.isAcceptableOrUnknown(
              data['roll_number']!, _rollNumberMeta));
    } else if (isInserting) {
      context.missing(_rollNumberMeta);
    }
    if (data.containsKey('grade')) {
      context.handle(
          _gradeMeta, grade.isAcceptableOrUnknown(data['grade']!, _gradeMeta));
    } else if (isInserting) {
      context.missing(_gradeMeta);
    }
    if (data.containsKey('section')) {
      context.handle(_sectionMeta,
          section.isAcceptableOrUnknown(data['section']!, _sectionMeta));
    } else if (isInserting) {
      context.missing(_sectionMeta);
    }
    context.handle(_reportMeta, const VerificationResult.success());
    if (data.containsKey('generated_at')) {
      context.handle(
          _generatedAtMeta,
          generatedAt.isAcceptableOrUnknown(
              data['generated_at']!, _generatedAtMeta));
    } else if (isInserting) {
      context.missing(_generatedAtMeta);
    }
    if (data.containsKey('generated_by')) {
      context.handle(
          _generatedByMeta,
          generatedBy.isAcceptableOrUnknown(
              data['generated_by']!, _generatedByMeta));
    } else if (isInserting) {
      context.missing(_generatedByMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Report map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Report(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      assessmentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}assessment_id'])!,
      assessmentTitle: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}assessment_title'])!,
      studentId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_id'])!,
      studentName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}student_name'])!,
      rollNumber: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}roll_number'])!,
      grade: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}grade'])!,
      section: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}section'])!,
      report: $ReportsTable.$converterreport.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}report'])!),
      generatedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}generated_at'])!,
      generatedBy: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}generated_by'])!,
    );
  }

  @override
  $ReportsTable createAlias(String alias) {
    return $ReportsTable(attachedDatabase, alias);
  }

  static TypeConverter<Map<String, dynamic>, String> $converterreport =
      const _JsonConverter();
}

class Report extends DataClass implements Insertable<Report> {
  final String id;
  final String assessmentId;
  final String assessmentTitle;
  final String studentId;
  final String studentName;
  final String rollNumber;
  final int grade;
  final String section;
  final Map<String, dynamic> report;
  final DateTime generatedAt;
  final String generatedBy;
  const Report(
      {required this.id,
      required this.assessmentId,
      required this.assessmentTitle,
      required this.studentId,
      required this.studentName,
      required this.rollNumber,
      required this.grade,
      required this.section,
      required this.report,
      required this.generatedAt,
      required this.generatedBy});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['assessment_id'] = Variable<String>(assessmentId);
    map['assessment_title'] = Variable<String>(assessmentTitle);
    map['student_id'] = Variable<String>(studentId);
    map['student_name'] = Variable<String>(studentName);
    map['roll_number'] = Variable<String>(rollNumber);
    map['grade'] = Variable<int>(grade);
    map['section'] = Variable<String>(section);
    {
      map['report'] =
          Variable<String>($ReportsTable.$converterreport.toSql(report));
    }
    map['generated_at'] = Variable<DateTime>(generatedAt);
    map['generated_by'] = Variable<String>(generatedBy);
    return map;
  }

  ReportsCompanion toCompanion(bool nullToAbsent) {
    return ReportsCompanion(
      id: Value(id),
      assessmentId: Value(assessmentId),
      assessmentTitle: Value(assessmentTitle),
      studentId: Value(studentId),
      studentName: Value(studentName),
      rollNumber: Value(rollNumber),
      grade: Value(grade),
      section: Value(section),
      report: Value(report),
      generatedAt: Value(generatedAt),
      generatedBy: Value(generatedBy),
    );
  }

  factory Report.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Report(
      id: serializer.fromJson<String>(json['id']),
      assessmentId: serializer.fromJson<String>(json['assessmentId']),
      assessmentTitle: serializer.fromJson<String>(json['assessmentTitle']),
      studentId: serializer.fromJson<String>(json['studentId']),
      studentName: serializer.fromJson<String>(json['studentName']),
      rollNumber: serializer.fromJson<String>(json['rollNumber']),
      grade: serializer.fromJson<int>(json['grade']),
      section: serializer.fromJson<String>(json['section']),
      report: serializer.fromJson<Map<String, dynamic>>(json['report']),
      generatedAt: serializer.fromJson<DateTime>(json['generatedAt']),
      generatedBy: serializer.fromJson<String>(json['generatedBy']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'assessmentId': serializer.toJson<String>(assessmentId),
      'assessmentTitle': serializer.toJson<String>(assessmentTitle),
      'studentId': serializer.toJson<String>(studentId),
      'studentName': serializer.toJson<String>(studentName),
      'rollNumber': serializer.toJson<String>(rollNumber),
      'grade': serializer.toJson<int>(grade),
      'section': serializer.toJson<String>(section),
      'report': serializer.toJson<Map<String, dynamic>>(report),
      'generatedAt': serializer.toJson<DateTime>(generatedAt),
      'generatedBy': serializer.toJson<String>(generatedBy),
    };
  }

  Report copyWith(
          {String? id,
          String? assessmentId,
          String? assessmentTitle,
          String? studentId,
          String? studentName,
          String? rollNumber,
          int? grade,
          String? section,
          Map<String, dynamic>? report,
          DateTime? generatedAt,
          String? generatedBy}) =>
      Report(
        id: id ?? this.id,
        assessmentId: assessmentId ?? this.assessmentId,
        assessmentTitle: assessmentTitle ?? this.assessmentTitle,
        studentId: studentId ?? this.studentId,
        studentName: studentName ?? this.studentName,
        rollNumber: rollNumber ?? this.rollNumber,
        grade: grade ?? this.grade,
        section: section ?? this.section,
        report: report ?? this.report,
        generatedAt: generatedAt ?? this.generatedAt,
        generatedBy: generatedBy ?? this.generatedBy,
      );
  Report copyWithCompanion(ReportsCompanion data) {
    return Report(
      id: data.id.present ? data.id.value : this.id,
      assessmentId: data.assessmentId.present
          ? data.assessmentId.value
          : this.assessmentId,
      assessmentTitle: data.assessmentTitle.present
          ? data.assessmentTitle.value
          : this.assessmentTitle,
      studentId: data.studentId.present ? data.studentId.value : this.studentId,
      studentName:
          data.studentName.present ? data.studentName.value : this.studentName,
      rollNumber:
          data.rollNumber.present ? data.rollNumber.value : this.rollNumber,
      grade: data.grade.present ? data.grade.value : this.grade,
      section: data.section.present ? data.section.value : this.section,
      report: data.report.present ? data.report.value : this.report,
      generatedAt:
          data.generatedAt.present ? data.generatedAt.value : this.generatedAt,
      generatedBy:
          data.generatedBy.present ? data.generatedBy.value : this.generatedBy,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Report(')
          ..write('id: $id, ')
          ..write('assessmentId: $assessmentId, ')
          ..write('assessmentTitle: $assessmentTitle, ')
          ..write('studentId: $studentId, ')
          ..write('studentName: $studentName, ')
          ..write('rollNumber: $rollNumber, ')
          ..write('grade: $grade, ')
          ..write('section: $section, ')
          ..write('report: $report, ')
          ..write('generatedAt: $generatedAt, ')
          ..write('generatedBy: $generatedBy')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      assessmentId,
      assessmentTitle,
      studentId,
      studentName,
      rollNumber,
      grade,
      section,
      report,
      generatedAt,
      generatedBy);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Report &&
          other.id == this.id &&
          other.assessmentId == this.assessmentId &&
          other.assessmentTitle == this.assessmentTitle &&
          other.studentId == this.studentId &&
          other.studentName == this.studentName &&
          other.rollNumber == this.rollNumber &&
          other.grade == this.grade &&
          other.section == this.section &&
          other.report == this.report &&
          other.generatedAt == this.generatedAt &&
          other.generatedBy == this.generatedBy);
}

class ReportsCompanion extends UpdateCompanion<Report> {
  final Value<String> id;
  final Value<String> assessmentId;
  final Value<String> assessmentTitle;
  final Value<String> studentId;
  final Value<String> studentName;
  final Value<String> rollNumber;
  final Value<int> grade;
  final Value<String> section;
  final Value<Map<String, dynamic>> report;
  final Value<DateTime> generatedAt;
  final Value<String> generatedBy;
  final Value<int> rowid;
  const ReportsCompanion({
    this.id = const Value.absent(),
    this.assessmentId = const Value.absent(),
    this.assessmentTitle = const Value.absent(),
    this.studentId = const Value.absent(),
    this.studentName = const Value.absent(),
    this.rollNumber = const Value.absent(),
    this.grade = const Value.absent(),
    this.section = const Value.absent(),
    this.report = const Value.absent(),
    this.generatedAt = const Value.absent(),
    this.generatedBy = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ReportsCompanion.insert({
    required String id,
    required String assessmentId,
    required String assessmentTitle,
    required String studentId,
    required String studentName,
    required String rollNumber,
    required int grade,
    required String section,
    required Map<String, dynamic> report,
    required DateTime generatedAt,
    required String generatedBy,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        assessmentId = Value(assessmentId),
        assessmentTitle = Value(assessmentTitle),
        studentId = Value(studentId),
        studentName = Value(studentName),
        rollNumber = Value(rollNumber),
        grade = Value(grade),
        section = Value(section),
        report = Value(report),
        generatedAt = Value(generatedAt),
        generatedBy = Value(generatedBy);
  static Insertable<Report> custom({
    Expression<String>? id,
    Expression<String>? assessmentId,
    Expression<String>? assessmentTitle,
    Expression<String>? studentId,
    Expression<String>? studentName,
    Expression<String>? rollNumber,
    Expression<int>? grade,
    Expression<String>? section,
    Expression<String>? report,
    Expression<DateTime>? generatedAt,
    Expression<String>? generatedBy,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (assessmentId != null) 'assessment_id': assessmentId,
      if (assessmentTitle != null) 'assessment_title': assessmentTitle,
      if (studentId != null) 'student_id': studentId,
      if (studentName != null) 'student_name': studentName,
      if (rollNumber != null) 'roll_number': rollNumber,
      if (grade != null) 'grade': grade,
      if (section != null) 'section': section,
      if (report != null) 'report': report,
      if (generatedAt != null) 'generated_at': generatedAt,
      if (generatedBy != null) 'generated_by': generatedBy,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ReportsCompanion copyWith(
      {Value<String>? id,
      Value<String>? assessmentId,
      Value<String>? assessmentTitle,
      Value<String>? studentId,
      Value<String>? studentName,
      Value<String>? rollNumber,
      Value<int>? grade,
      Value<String>? section,
      Value<Map<String, dynamic>>? report,
      Value<DateTime>? generatedAt,
      Value<String>? generatedBy,
      Value<int>? rowid}) {
    return ReportsCompanion(
      id: id ?? this.id,
      assessmentId: assessmentId ?? this.assessmentId,
      assessmentTitle: assessmentTitle ?? this.assessmentTitle,
      studentId: studentId ?? this.studentId,
      studentName: studentName ?? this.studentName,
      rollNumber: rollNumber ?? this.rollNumber,
      grade: grade ?? this.grade,
      section: section ?? this.section,
      report: report ?? this.report,
      generatedAt: generatedAt ?? this.generatedAt,
      generatedBy: generatedBy ?? this.generatedBy,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (assessmentId.present) {
      map['assessment_id'] = Variable<String>(assessmentId.value);
    }
    if (assessmentTitle.present) {
      map['assessment_title'] = Variable<String>(assessmentTitle.value);
    }
    if (studentId.present) {
      map['student_id'] = Variable<String>(studentId.value);
    }
    if (studentName.present) {
      map['student_name'] = Variable<String>(studentName.value);
    }
    if (rollNumber.present) {
      map['roll_number'] = Variable<String>(rollNumber.value);
    }
    if (grade.present) {
      map['grade'] = Variable<int>(grade.value);
    }
    if (section.present) {
      map['section'] = Variable<String>(section.value);
    }
    if (report.present) {
      map['report'] =
          Variable<String>($ReportsTable.$converterreport.toSql(report.value));
    }
    if (generatedAt.present) {
      map['generated_at'] = Variable<DateTime>(generatedAt.value);
    }
    if (generatedBy.present) {
      map['generated_by'] = Variable<String>(generatedBy.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ReportsCompanion(')
          ..write('id: $id, ')
          ..write('assessmentId: $assessmentId, ')
          ..write('assessmentTitle: $assessmentTitle, ')
          ..write('studentId: $studentId, ')
          ..write('studentName: $studentName, ')
          ..write('rollNumber: $rollNumber, ')
          ..write('grade: $grade, ')
          ..write('section: $section, ')
          ..write('report: $report, ')
          ..write('generatedAt: $generatedAt, ')
          ..write('generatedBy: $generatedBy, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $NotificationsTable extends Notifications
    with TableInfo<$NotificationsTable, NotificationRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $NotificationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _userIdMeta = const VerificationMeta('userId');
  @override
  late final GeneratedColumn<String> userId = GeneratedColumn<String>(
      'user_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _typeMeta = const VerificationMeta('type');
  @override
  late final GeneratedColumn<String> type = GeneratedColumn<String>(
      'type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _bodyMeta = const VerificationMeta('body');
  @override
  late final GeneratedColumn<String> body = GeneratedColumn<String>(
      'body', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _dataMeta = const VerificationMeta('data');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      data = GeneratedColumn<String>('data', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $NotificationsTable.$converterdata);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _isReadMeta = const VerificationMeta('isRead');
  @override
  late final GeneratedColumn<bool> isRead = GeneratedColumn<bool>(
      'is_read', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_read" IN (0, 1))'));
  static const VerificationMeta _readAtMeta = const VerificationMeta('readAt');
  @override
  late final GeneratedColumn<DateTime> readAt = GeneratedColumn<DateTime>(
      'read_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, userId, type, title, body, data, createdAt, isRead, readAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'notifications';
  @override
  VerificationContext validateIntegrity(Insertable<NotificationRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('user_id')) {
      context.handle(_userIdMeta,
          userId.isAcceptableOrUnknown(data['user_id']!, _userIdMeta));
    } else if (isInserting) {
      context.missing(_userIdMeta);
    }
    if (data.containsKey('type')) {
      context.handle(
          _typeMeta, type.isAcceptableOrUnknown(data['type']!, _typeMeta));
    } else if (isInserting) {
      context.missing(_typeMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('body')) {
      context.handle(
          _bodyMeta, body.isAcceptableOrUnknown(data['body']!, _bodyMeta));
    } else if (isInserting) {
      context.missing(_bodyMeta);
    }
    context.handle(_dataMeta, const VerificationResult.success());
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('is_read')) {
      context.handle(_isReadMeta,
          isRead.isAcceptableOrUnknown(data['is_read']!, _isReadMeta));
    } else if (isInserting) {
      context.missing(_isReadMeta);
    }
    if (data.containsKey('read_at')) {
      context.handle(_readAtMeta,
          readAt.isAcceptableOrUnknown(data['read_at']!, _readAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  NotificationRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return NotificationRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      userId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}user_id'])!,
      type: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}type'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      body: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}body'])!,
      data: $NotificationsTable.$converterdata.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}data'])!),
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      isRead: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_read'])!,
      readAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}read_at']),
    );
  }

  @override
  $NotificationsTable createAlias(String alias) {
    return $NotificationsTable(attachedDatabase, alias);
  }

  static TypeConverter<Map<String, dynamic>, String> $converterdata =
      const _JsonConverter();
}

class NotificationRow extends DataClass implements Insertable<NotificationRow> {
  final String id;
  final String userId;
  final String type;
  final String title;
  final String body;
  final Map<String, dynamic> data;
  final DateTime createdAt;
  final bool isRead;
  final DateTime? readAt;
  const NotificationRow(
      {required this.id,
      required this.userId,
      required this.type,
      required this.title,
      required this.body,
      required this.data,
      required this.createdAt,
      required this.isRead,
      this.readAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['user_id'] = Variable<String>(userId);
    map['type'] = Variable<String>(type);
    map['title'] = Variable<String>(title);
    map['body'] = Variable<String>(body);
    {
      map['data'] =
          Variable<String>($NotificationsTable.$converterdata.toSql(data));
    }
    map['created_at'] = Variable<DateTime>(createdAt);
    map['is_read'] = Variable<bool>(isRead);
    if (!nullToAbsent || readAt != null) {
      map['read_at'] = Variable<DateTime>(readAt);
    }
    return map;
  }

  NotificationsCompanion toCompanion(bool nullToAbsent) {
    return NotificationsCompanion(
      id: Value(id),
      userId: Value(userId),
      type: Value(type),
      title: Value(title),
      body: Value(body),
      data: Value(data),
      createdAt: Value(createdAt),
      isRead: Value(isRead),
      readAt:
          readAt == null && nullToAbsent ? const Value.absent() : Value(readAt),
    );
  }

  factory NotificationRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return NotificationRow(
      id: serializer.fromJson<String>(json['id']),
      userId: serializer.fromJson<String>(json['userId']),
      type: serializer.fromJson<String>(json['type']),
      title: serializer.fromJson<String>(json['title']),
      body: serializer.fromJson<String>(json['body']),
      data: serializer.fromJson<Map<String, dynamic>>(json['data']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      isRead: serializer.fromJson<bool>(json['isRead']),
      readAt: serializer.fromJson<DateTime?>(json['readAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'userId': serializer.toJson<String>(userId),
      'type': serializer.toJson<String>(type),
      'title': serializer.toJson<String>(title),
      'body': serializer.toJson<String>(body),
      'data': serializer.toJson<Map<String, dynamic>>(data),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'isRead': serializer.toJson<bool>(isRead),
      'readAt': serializer.toJson<DateTime?>(readAt),
    };
  }

  NotificationRow copyWith(
          {String? id,
          String? userId,
          String? type,
          String? title,
          String? body,
          Map<String, dynamic>? data,
          DateTime? createdAt,
          bool? isRead,
          Value<DateTime?> readAt = const Value.absent()}) =>
      NotificationRow(
        id: id ?? this.id,
        userId: userId ?? this.userId,
        type: type ?? this.type,
        title: title ?? this.title,
        body: body ?? this.body,
        data: data ?? this.data,
        createdAt: createdAt ?? this.createdAt,
        isRead: isRead ?? this.isRead,
        readAt: readAt.present ? readAt.value : this.readAt,
      );
  NotificationRow copyWithCompanion(NotificationsCompanion data) {
    return NotificationRow(
      id: data.id.present ? data.id.value : this.id,
      userId: data.userId.present ? data.userId.value : this.userId,
      type: data.type.present ? data.type.value : this.type,
      title: data.title.present ? data.title.value : this.title,
      body: data.body.present ? data.body.value : this.body,
      data: data.data.present ? data.data.value : this.data,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      isRead: data.isRead.present ? data.isRead.value : this.isRead,
      readAt: data.readAt.present ? data.readAt.value : this.readAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('NotificationRow(')
          ..write('id: $id, ')
          ..write('userId: $userId, ')
          ..write('type: $type, ')
          ..write('title: $title, ')
          ..write('body: $body, ')
          ..write('data: $data, ')
          ..write('createdAt: $createdAt, ')
          ..write('isRead: $isRead, ')
          ..write('readAt: $readAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, userId, type, title, body, data, createdAt, isRead, readAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is NotificationRow &&
          other.id == this.id &&
          other.userId == this.userId &&
          other.type == this.type &&
          other.title == this.title &&
          other.body == this.body &&
          other.data == this.data &&
          other.createdAt == this.createdAt &&
          other.isRead == this.isRead &&
          other.readAt == this.readAt);
}

class NotificationsCompanion extends UpdateCompanion<NotificationRow> {
  final Value<String> id;
  final Value<String> userId;
  final Value<String> type;
  final Value<String> title;
  final Value<String> body;
  final Value<Map<String, dynamic>> data;
  final Value<DateTime> createdAt;
  final Value<bool> isRead;
  final Value<DateTime?> readAt;
  final Value<int> rowid;
  const NotificationsCompanion({
    this.id = const Value.absent(),
    this.userId = const Value.absent(),
    this.type = const Value.absent(),
    this.title = const Value.absent(),
    this.body = const Value.absent(),
    this.data = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.isRead = const Value.absent(),
    this.readAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  NotificationsCompanion.insert({
    required String id,
    required String userId,
    required String type,
    required String title,
    required String body,
    required Map<String, dynamic> data,
    required DateTime createdAt,
    required bool isRead,
    this.readAt = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        userId = Value(userId),
        type = Value(type),
        title = Value(title),
        body = Value(body),
        data = Value(data),
        createdAt = Value(createdAt),
        isRead = Value(isRead);
  static Insertable<NotificationRow> custom({
    Expression<String>? id,
    Expression<String>? userId,
    Expression<String>? type,
    Expression<String>? title,
    Expression<String>? body,
    Expression<String>? data,
    Expression<DateTime>? createdAt,
    Expression<bool>? isRead,
    Expression<DateTime>? readAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (userId != null) 'user_id': userId,
      if (type != null) 'type': type,
      if (title != null) 'title': title,
      if (body != null) 'body': body,
      if (data != null) 'data': data,
      if (createdAt != null) 'created_at': createdAt,
      if (isRead != null) 'is_read': isRead,
      if (readAt != null) 'read_at': readAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  NotificationsCompanion copyWith(
      {Value<String>? id,
      Value<String>? userId,
      Value<String>? type,
      Value<String>? title,
      Value<String>? body,
      Value<Map<String, dynamic>>? data,
      Value<DateTime>? createdAt,
      Value<bool>? isRead,
      Value<DateTime?>? readAt,
      Value<int>? rowid}) {
    return NotificationsCompanion(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      type: type ?? this.type,
      title: title ?? this.title,
      body: body ?? this.body,
      data: data ?? this.data,
      createdAt: createdAt ?? this.createdAt,
      isRead: isRead ?? this.isRead,
      readAt: readAt ?? this.readAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (userId.present) {
      map['user_id'] = Variable<String>(userId.value);
    }
    if (type.present) {
      map['type'] = Variable<String>(type.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (body.present) {
      map['body'] = Variable<String>(body.value);
    }
    if (data.present) {
      map['data'] = Variable<String>(
          $NotificationsTable.$converterdata.toSql(data.value));
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (isRead.present) {
      map['is_read'] = Variable<bool>(isRead.value);
    }
    if (readAt.present) {
      map['read_at'] = Variable<DateTime>(readAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('NotificationsCompanion(')
          ..write('id: $id, ')
          ..write('userId: $userId, ')
          ..write('type: $type, ')
          ..write('title: $title, ')
          ..write('body: $body, ')
          ..write('data: $data, ')
          ..write('createdAt: $createdAt, ')
          ..write('isRead: $isRead, ')
          ..write('readAt: $readAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncQueueTable extends SyncQueue
    with TableInfo<$SyncQueueTable, SyncQueueData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncQueueTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      additionalChecks:
          GeneratedColumn.checkTextLength(minTextLength: 1, maxTextLength: 36),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _entityTypeMeta =
      const VerificationMeta('entityType');
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
      'entity_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _entityIdMeta =
      const VerificationMeta('entityId');
  @override
  late final GeneratedColumn<String> entityId = GeneratedColumn<String>(
      'entity_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _operationMeta =
      const VerificationMeta('operation');
  @override
  late final GeneratedColumn<String> operation = GeneratedColumn<String>(
      'operation', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _payloadMeta =
      const VerificationMeta('payload');
  @override
  late final GeneratedColumnWithTypeConverter<Map<String, dynamic>, String>
      payload = GeneratedColumn<String>('payload', aliasedName, false,
              type: DriftSqlType.string, requiredDuringInsert: true)
          .withConverter<Map<String, dynamic>>(
              $SyncQueueTable.$converterpayload);
  static const VerificationMeta _retryCountMeta =
      const VerificationMeta('retryCount');
  @override
  late final GeneratedColumn<int> retryCount = GeneratedColumn<int>(
      'retry_count', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _nextRetryAtMeta =
      const VerificationMeta('nextRetryAt');
  @override
  late final GeneratedColumn<DateTime> nextRetryAt = GeneratedColumn<DateTime>(
      'next_retry_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _errorMeta = const VerificationMeta('error');
  @override
  late final GeneratedColumn<String> error = GeneratedColumn<String>(
      'error', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        entityType,
        entityId,
        operation,
        payload,
        retryCount,
        createdAt,
        nextRetryAt,
        error
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_queue';
  @override
  VerificationContext validateIntegrity(Insertable<SyncQueueData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('entity_type')) {
      context.handle(
          _entityTypeMeta,
          entityType.isAcceptableOrUnknown(
              data['entity_type']!, _entityTypeMeta));
    } else if (isInserting) {
      context.missing(_entityTypeMeta);
    }
    if (data.containsKey('entity_id')) {
      context.handle(_entityIdMeta,
          entityId.isAcceptableOrUnknown(data['entity_id']!, _entityIdMeta));
    } else if (isInserting) {
      context.missing(_entityIdMeta);
    }
    if (data.containsKey('operation')) {
      context.handle(_operationMeta,
          operation.isAcceptableOrUnknown(data['operation']!, _operationMeta));
    } else if (isInserting) {
      context.missing(_operationMeta);
    }
    context.handle(_payloadMeta, const VerificationResult.success());
    if (data.containsKey('retry_count')) {
      context.handle(
          _retryCountMeta,
          retryCount.isAcceptableOrUnknown(
              data['retry_count']!, _retryCountMeta));
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('next_retry_at')) {
      context.handle(
          _nextRetryAtMeta,
          nextRetryAt.isAcceptableOrUnknown(
              data['next_retry_at']!, _nextRetryAtMeta));
    } else if (isInserting) {
      context.missing(_nextRetryAtMeta);
    }
    if (data.containsKey('error')) {
      context.handle(
          _errorMeta, error.isAcceptableOrUnknown(data['error']!, _errorMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SyncQueueData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncQueueData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      entityType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}entity_type'])!,
      entityId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}entity_id'])!,
      operation: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}operation'])!,
      payload: $SyncQueueTable.$converterpayload.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload'])!),
      retryCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}retry_count'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      nextRetryAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}next_retry_at'])!,
      error: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}error']),
    );
  }

  @override
  $SyncQueueTable createAlias(String alias) {
    return $SyncQueueTable(attachedDatabase, alias);
  }

  static TypeConverter<Map<String, dynamic>, String> $converterpayload =
      const _JsonConverter();
}

class SyncQueueData extends DataClass implements Insertable<SyncQueueData> {
  final String id;
  final String entityType;
  final String entityId;
  final String operation;
  final Map<String, dynamic> payload;
  final int retryCount;
  final DateTime createdAt;
  final DateTime nextRetryAt;
  final String? error;
  const SyncQueueData(
      {required this.id,
      required this.entityType,
      required this.entityId,
      required this.operation,
      required this.payload,
      required this.retryCount,
      required this.createdAt,
      required this.nextRetryAt,
      this.error});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['entity_type'] = Variable<String>(entityType);
    map['entity_id'] = Variable<String>(entityId);
    map['operation'] = Variable<String>(operation);
    {
      map['payload'] =
          Variable<String>($SyncQueueTable.$converterpayload.toSql(payload));
    }
    map['retry_count'] = Variable<int>(retryCount);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['next_retry_at'] = Variable<DateTime>(nextRetryAt);
    if (!nullToAbsent || error != null) {
      map['error'] = Variable<String>(error);
    }
    return map;
  }

  SyncQueueCompanion toCompanion(bool nullToAbsent) {
    return SyncQueueCompanion(
      id: Value(id),
      entityType: Value(entityType),
      entityId: Value(entityId),
      operation: Value(operation),
      payload: Value(payload),
      retryCount: Value(retryCount),
      createdAt: Value(createdAt),
      nextRetryAt: Value(nextRetryAt),
      error:
          error == null && nullToAbsent ? const Value.absent() : Value(error),
    );
  }

  factory SyncQueueData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncQueueData(
      id: serializer.fromJson<String>(json['id']),
      entityType: serializer.fromJson<String>(json['entityType']),
      entityId: serializer.fromJson<String>(json['entityId']),
      operation: serializer.fromJson<String>(json['operation']),
      payload: serializer.fromJson<Map<String, dynamic>>(json['payload']),
      retryCount: serializer.fromJson<int>(json['retryCount']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      nextRetryAt: serializer.fromJson<DateTime>(json['nextRetryAt']),
      error: serializer.fromJson<String?>(json['error']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'entityType': serializer.toJson<String>(entityType),
      'entityId': serializer.toJson<String>(entityId),
      'operation': serializer.toJson<String>(operation),
      'payload': serializer.toJson<Map<String, dynamic>>(payload),
      'retryCount': serializer.toJson<int>(retryCount),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'nextRetryAt': serializer.toJson<DateTime>(nextRetryAt),
      'error': serializer.toJson<String?>(error),
    };
  }

  SyncQueueData copyWith(
          {String? id,
          String? entityType,
          String? entityId,
          String? operation,
          Map<String, dynamic>? payload,
          int? retryCount,
          DateTime? createdAt,
          DateTime? nextRetryAt,
          Value<String?> error = const Value.absent()}) =>
      SyncQueueData(
        id: id ?? this.id,
        entityType: entityType ?? this.entityType,
        entityId: entityId ?? this.entityId,
        operation: operation ?? this.operation,
        payload: payload ?? this.payload,
        retryCount: retryCount ?? this.retryCount,
        createdAt: createdAt ?? this.createdAt,
        nextRetryAt: nextRetryAt ?? this.nextRetryAt,
        error: error.present ? error.value : this.error,
      );
  SyncQueueData copyWithCompanion(SyncQueueCompanion data) {
    return SyncQueueData(
      id: data.id.present ? data.id.value : this.id,
      entityType:
          data.entityType.present ? data.entityType.value : this.entityType,
      entityId: data.entityId.present ? data.entityId.value : this.entityId,
      operation: data.operation.present ? data.operation.value : this.operation,
      payload: data.payload.present ? data.payload.value : this.payload,
      retryCount:
          data.retryCount.present ? data.retryCount.value : this.retryCount,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      nextRetryAt:
          data.nextRetryAt.present ? data.nextRetryAt.value : this.nextRetryAt,
      error: data.error.present ? data.error.value : this.error,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncQueueData(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('operation: $operation, ')
          ..write('payload: $payload, ')
          ..write('retryCount: $retryCount, ')
          ..write('createdAt: $createdAt, ')
          ..write('nextRetryAt: $nextRetryAt, ')
          ..write('error: $error')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, entityType, entityId, operation, payload,
      retryCount, createdAt, nextRetryAt, error);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncQueueData &&
          other.id == this.id &&
          other.entityType == this.entityType &&
          other.entityId == this.entityId &&
          other.operation == this.operation &&
          other.payload == this.payload &&
          other.retryCount == this.retryCount &&
          other.createdAt == this.createdAt &&
          other.nextRetryAt == this.nextRetryAt &&
          other.error == this.error);
}

class SyncQueueCompanion extends UpdateCompanion<SyncQueueData> {
  final Value<String> id;
  final Value<String> entityType;
  final Value<String> entityId;
  final Value<String> operation;
  final Value<Map<String, dynamic>> payload;
  final Value<int> retryCount;
  final Value<DateTime> createdAt;
  final Value<DateTime> nextRetryAt;
  final Value<String?> error;
  final Value<int> rowid;
  const SyncQueueCompanion({
    this.id = const Value.absent(),
    this.entityType = const Value.absent(),
    this.entityId = const Value.absent(),
    this.operation = const Value.absent(),
    this.payload = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.nextRetryAt = const Value.absent(),
    this.error = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncQueueCompanion.insert({
    required String id,
    required String entityType,
    required String entityId,
    required String operation,
    required Map<String, dynamic> payload,
    this.retryCount = const Value.absent(),
    required DateTime createdAt,
    required DateTime nextRetryAt,
    this.error = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        entityType = Value(entityType),
        entityId = Value(entityId),
        operation = Value(operation),
        payload = Value(payload),
        createdAt = Value(createdAt),
        nextRetryAt = Value(nextRetryAt);
  static Insertable<SyncQueueData> custom({
    Expression<String>? id,
    Expression<String>? entityType,
    Expression<String>? entityId,
    Expression<String>? operation,
    Expression<String>? payload,
    Expression<int>? retryCount,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? nextRetryAt,
    Expression<String>? error,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (entityType != null) 'entity_type': entityType,
      if (entityId != null) 'entity_id': entityId,
      if (operation != null) 'operation': operation,
      if (payload != null) 'payload': payload,
      if (retryCount != null) 'retry_count': retryCount,
      if (createdAt != null) 'created_at': createdAt,
      if (nextRetryAt != null) 'next_retry_at': nextRetryAt,
      if (error != null) 'error': error,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncQueueCompanion copyWith(
      {Value<String>? id,
      Value<String>? entityType,
      Value<String>? entityId,
      Value<String>? operation,
      Value<Map<String, dynamic>>? payload,
      Value<int>? retryCount,
      Value<DateTime>? createdAt,
      Value<DateTime>? nextRetryAt,
      Value<String?>? error,
      Value<int>? rowid}) {
    return SyncQueueCompanion(
      id: id ?? this.id,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      operation: operation ?? this.operation,
      payload: payload ?? this.payload,
      retryCount: retryCount ?? this.retryCount,
      createdAt: createdAt ?? this.createdAt,
      nextRetryAt: nextRetryAt ?? this.nextRetryAt,
      error: error ?? this.error,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (entityId.present) {
      map['entity_id'] = Variable<String>(entityId.value);
    }
    if (operation.present) {
      map['operation'] = Variable<String>(operation.value);
    }
    if (payload.present) {
      map['payload'] = Variable<String>(
          $SyncQueueTable.$converterpayload.toSql(payload.value));
    }
    if (retryCount.present) {
      map['retry_count'] = Variable<int>(retryCount.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (nextRetryAt.present) {
      map['next_retry_at'] = Variable<DateTime>(nextRetryAt.value);
    }
    if (error.present) {
      map['error'] = Variable<String>(error.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncQueueCompanion(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('operation: $operation, ')
          ..write('payload: $payload, ')
          ..write('retryCount: $retryCount, ')
          ..write('createdAt: $createdAt, ')
          ..write('nextRetryAt: $nextRetryAt, ')
          ..write('error: $error, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $AssessmentsTable assessments = $AssessmentsTable(this);
  late final $QuestionsTable questions = $QuestionsTable(this);
  late final $AnswerSheetsTable answerSheets = $AnswerSheetsTable(this);
  late final $EvaluationsTable evaluations = $EvaluationsTable(this);
  late final $StudentMasteryTableTable studentMasteryTable =
      $StudentMasteryTableTable(this);
  late final $PracticeSessionsTable practiceSessions =
      $PracticeSessionsTable(this);
  late final $ReportsTable reports = $ReportsTable(this);
  late final $NotificationsTable notifications = $NotificationsTable(this);
  late final $SyncQueueTable syncQueue = $SyncQueueTable(this);
  late final Index idxAssessmentsTeacher = Index('idx_assessments_teacher',
      'CREATE INDEX idx_assessments_teacher ON assessments (teacher_id)');
  late final Index idxAssessmentsSchool = Index('idx_assessments_school',
      'CREATE INDEX idx_assessments_school ON assessments (school_id)');
  late final Index idxAssessmentsStatus = Index('idx_assessments_status',
      'CREATE INDEX idx_assessments_status ON assessments (status)');
  late final Index idxQuestionsAssessment = Index('idx_questions_assessment',
      'CREATE INDEX idx_questions_assessment ON questions (assessment_id)');
  late final Index idxAnswerSheetsAssessment = Index(
      'idx_answer_sheets_assessment',
      'CREATE INDEX idx_answer_sheets_assessment ON answer_sheets (assessment_id)');
  late final Index idxAnswerSheetsStudent = Index('idx_answer_sheets_student',
      'CREATE INDEX idx_answer_sheets_student ON answer_sheets (student_id)');
  late final Index idxAnswerSheetsStatus = Index('idx_answer_sheets_status',
      'CREATE INDEX idx_answer_sheets_status ON answer_sheets (status)');
  late final Index idxEvaluationsAnswerSheet = Index(
      'idx_evaluations_answer_sheet',
      'CREATE INDEX idx_evaluations_answer_sheet ON evaluations (answer_sheet_id)');
  late final Index idxEvaluationsQuestion = Index('idx_evaluations_question',
      'CREATE INDEX idx_evaluations_question ON evaluations (question_id)');
  late final Index idxMasteryStudent = Index('idx_mastery_student',
      'CREATE INDEX idx_mastery_student ON student_mastery_table (student_id)');
  late final Index idxPracticeStudent = Index('idx_practice_student',
      'CREATE INDEX idx_practice_student ON practice_sessions (student_id)');
  late final Index idxPracticeStatus = Index('idx_practice_status',
      'CREATE INDEX idx_practice_status ON practice_sessions (status)');
  late final Index idxReportsStudent = Index('idx_reports_student',
      'CREATE INDEX idx_reports_student ON reports (student_id)');
  late final Index idxReportsAssessment = Index('idx_reports_assessment',
      'CREATE INDEX idx_reports_assessment ON reports (assessment_id)');
  late final Index idxNotificationsUser = Index('idx_notifications_user',
      'CREATE INDEX idx_notifications_user ON notifications (user_id)');
  late final Index idxNotificationsRead = Index('idx_notifications_read',
      'CREATE INDEX idx_notifications_read ON notifications (is_read)');
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
        assessments,
        questions,
        answerSheets,
        evaluations,
        studentMasteryTable,
        practiceSessions,
        reports,
        notifications,
        syncQueue,
        idxAssessmentsTeacher,
        idxAssessmentsSchool,
        idxAssessmentsStatus,
        idxQuestionsAssessment,
        idxAnswerSheetsAssessment,
        idxAnswerSheetsStudent,
        idxAnswerSheetsStatus,
        idxEvaluationsAnswerSheet,
        idxEvaluationsQuestion,
        idxMasteryStudent,
        idxPracticeStudent,
        idxPracticeStatus,
        idxReportsStudent,
        idxReportsAssessment,
        idxNotificationsUser,
        idxNotificationsRead
      ];
}

typedef $$AssessmentsTableCreateCompanionBuilder = AssessmentsCompanion
    Function({
  required String id,
  required String schoolId,
  required String teacherId,
  required String title,
  required String subject,
  required int grade,
  required List<String> chapterIds,
  required Map<String, dynamic> blueprint,
  required String status,
  required DateTime createdAt,
  required DateTime updatedAt,
  Value<DateTime?> scheduledAt,
  Value<DateTime?> completedAt,
  Value<String?> templateId,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});
typedef $$AssessmentsTableUpdateCompanionBuilder = AssessmentsCompanion
    Function({
  Value<String> id,
  Value<String> schoolId,
  Value<String> teacherId,
  Value<String> title,
  Value<String> subject,
  Value<int> grade,
  Value<List<String>> chapterIds,
  Value<Map<String, dynamic>> blueprint,
  Value<String> status,
  Value<DateTime> createdAt,
  Value<DateTime> updatedAt,
  Value<DateTime?> scheduledAt,
  Value<DateTime?> completedAt,
  Value<String?> templateId,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});

class $$AssessmentsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $AssessmentsTable,
    AssessmentRow,
    $$AssessmentsTableFilterComposer,
    $$AssessmentsTableOrderingComposer,
    $$AssessmentsTableCreateCompanionBuilder,
    $$AssessmentsTableUpdateCompanionBuilder> {
  $$AssessmentsTableTableManager(_$AppDatabase db, $AssessmentsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$AssessmentsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$AssessmentsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> schoolId = const Value.absent(),
            Value<String> teacherId = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String> subject = const Value.absent(),
            Value<int> grade = const Value.absent(),
            Value<List<String>> chapterIds = const Value.absent(),
            Value<Map<String, dynamic>> blueprint = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<DateTime> updatedAt = const Value.absent(),
            Value<DateTime?> scheduledAt = const Value.absent(),
            Value<DateTime?> completedAt = const Value.absent(),
            Value<String?> templateId = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AssessmentsCompanion(
            id: id,
            schoolId: schoolId,
            teacherId: teacherId,
            title: title,
            subject: subject,
            grade: grade,
            chapterIds: chapterIds,
            blueprint: blueprint,
            status: status,
            createdAt: createdAt,
            updatedAt: updatedAt,
            scheduledAt: scheduledAt,
            completedAt: completedAt,
            templateId: templateId,
            metadata: metadata,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String schoolId,
            required String teacherId,
            required String title,
            required String subject,
            required int grade,
            required List<String> chapterIds,
            required Map<String, dynamic> blueprint,
            required String status,
            required DateTime createdAt,
            required DateTime updatedAt,
            Value<DateTime?> scheduledAt = const Value.absent(),
            Value<DateTime?> completedAt = const Value.absent(),
            Value<String?> templateId = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AssessmentsCompanion.insert(
            id: id,
            schoolId: schoolId,
            teacherId: teacherId,
            title: title,
            subject: subject,
            grade: grade,
            chapterIds: chapterIds,
            blueprint: blueprint,
            status: status,
            createdAt: createdAt,
            updatedAt: updatedAt,
            scheduledAt: scheduledAt,
            completedAt: completedAt,
            templateId: templateId,
            metadata: metadata,
            rowid: rowid,
          ),
        ));
}

class $$AssessmentsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $AssessmentsTable> {
  $$AssessmentsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get schoolId => $state.composableBuilder(
      column: $state.table.schoolId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get teacherId => $state.composableBuilder(
      column: $state.table.teacherId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get title => $state.composableBuilder(
      column: $state.table.title,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get subject => $state.composableBuilder(
      column: $state.table.subject,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get chapterIds => $state.composableBuilder(
          column: $state.table.chapterIds,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get blueprint => $state.composableBuilder(
          column: $state.table.blueprint,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get updatedAt => $state.composableBuilder(
      column: $state.table.updatedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get scheduledAt => $state.composableBuilder(
      column: $state.table.scheduledAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get completedAt => $state.composableBuilder(
      column: $state.table.completedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get templateId => $state.composableBuilder(
      column: $state.table.templateId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get metadata => $state.composableBuilder(
          column: $state.table.metadata,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));
}

class $$AssessmentsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $AssessmentsTable> {
  $$AssessmentsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get schoolId => $state.composableBuilder(
      column: $state.table.schoolId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get teacherId => $state.composableBuilder(
      column: $state.table.teacherId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get title => $state.composableBuilder(
      column: $state.table.title,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get subject => $state.composableBuilder(
      column: $state.table.subject,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get chapterIds => $state.composableBuilder(
      column: $state.table.chapterIds,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get blueprint => $state.composableBuilder(
      column: $state.table.blueprint,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get updatedAt => $state.composableBuilder(
      column: $state.table.updatedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get scheduledAt => $state.composableBuilder(
      column: $state.table.scheduledAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get completedAt => $state.composableBuilder(
      column: $state.table.completedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get templateId => $state.composableBuilder(
      column: $state.table.templateId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get metadata => $state.composableBuilder(
      column: $state.table.metadata,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$QuestionsTableCreateCompanionBuilder = QuestionsCompanion Function({
  required String id,
  Value<String?> assessmentId,
  required String questionBankId,
  required String subject,
  required int grade,
  required List<String> chapterIds,
  required List<String> competencyIds,
  required String bloomLevel,
  required String difficulty,
  required String type,
  required String stem,
  Value<String?> stemLatex,
  required Map<String, dynamic> parts,
  required Map<String, dynamic> answerScheme,
  required int estimatedTimeMinutes,
  required int marks,
  required String language,
  required String source,
  required double qualityScore,
  required List<String> tags,
  required DateTime createdAt,
  required DateTime updatedAt,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});
typedef $$QuestionsTableUpdateCompanionBuilder = QuestionsCompanion Function({
  Value<String> id,
  Value<String?> assessmentId,
  Value<String> questionBankId,
  Value<String> subject,
  Value<int> grade,
  Value<List<String>> chapterIds,
  Value<List<String>> competencyIds,
  Value<String> bloomLevel,
  Value<String> difficulty,
  Value<String> type,
  Value<String> stem,
  Value<String?> stemLatex,
  Value<Map<String, dynamic>> parts,
  Value<Map<String, dynamic>> answerScheme,
  Value<int> estimatedTimeMinutes,
  Value<int> marks,
  Value<String> language,
  Value<String> source,
  Value<double> qualityScore,
  Value<List<String>> tags,
  Value<DateTime> createdAt,
  Value<DateTime> updatedAt,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});

class $$QuestionsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $QuestionsTable,
    QuestionRow,
    $$QuestionsTableFilterComposer,
    $$QuestionsTableOrderingComposer,
    $$QuestionsTableCreateCompanionBuilder,
    $$QuestionsTableUpdateCompanionBuilder> {
  $$QuestionsTableTableManager(_$AppDatabase db, $QuestionsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$QuestionsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$QuestionsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String?> assessmentId = const Value.absent(),
            Value<String> questionBankId = const Value.absent(),
            Value<String> subject = const Value.absent(),
            Value<int> grade = const Value.absent(),
            Value<List<String>> chapterIds = const Value.absent(),
            Value<List<String>> competencyIds = const Value.absent(),
            Value<String> bloomLevel = const Value.absent(),
            Value<String> difficulty = const Value.absent(),
            Value<String> type = const Value.absent(),
            Value<String> stem = const Value.absent(),
            Value<String?> stemLatex = const Value.absent(),
            Value<Map<String, dynamic>> parts = const Value.absent(),
            Value<Map<String, dynamic>> answerScheme = const Value.absent(),
            Value<int> estimatedTimeMinutes = const Value.absent(),
            Value<int> marks = const Value.absent(),
            Value<String> language = const Value.absent(),
            Value<String> source = const Value.absent(),
            Value<double> qualityScore = const Value.absent(),
            Value<List<String>> tags = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<DateTime> updatedAt = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              QuestionsCompanion(
            id: id,
            assessmentId: assessmentId,
            questionBankId: questionBankId,
            subject: subject,
            grade: grade,
            chapterIds: chapterIds,
            competencyIds: competencyIds,
            bloomLevel: bloomLevel,
            difficulty: difficulty,
            type: type,
            stem: stem,
            stemLatex: stemLatex,
            parts: parts,
            answerScheme: answerScheme,
            estimatedTimeMinutes: estimatedTimeMinutes,
            marks: marks,
            language: language,
            source: source,
            qualityScore: qualityScore,
            tags: tags,
            createdAt: createdAt,
            updatedAt: updatedAt,
            metadata: metadata,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            Value<String?> assessmentId = const Value.absent(),
            required String questionBankId,
            required String subject,
            required int grade,
            required List<String> chapterIds,
            required List<String> competencyIds,
            required String bloomLevel,
            required String difficulty,
            required String type,
            required String stem,
            Value<String?> stemLatex = const Value.absent(),
            required Map<String, dynamic> parts,
            required Map<String, dynamic> answerScheme,
            required int estimatedTimeMinutes,
            required int marks,
            required String language,
            required String source,
            required double qualityScore,
            required List<String> tags,
            required DateTime createdAt,
            required DateTime updatedAt,
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              QuestionsCompanion.insert(
            id: id,
            assessmentId: assessmentId,
            questionBankId: questionBankId,
            subject: subject,
            grade: grade,
            chapterIds: chapterIds,
            competencyIds: competencyIds,
            bloomLevel: bloomLevel,
            difficulty: difficulty,
            type: type,
            stem: stem,
            stemLatex: stemLatex,
            parts: parts,
            answerScheme: answerScheme,
            estimatedTimeMinutes: estimatedTimeMinutes,
            marks: marks,
            language: language,
            source: source,
            qualityScore: qualityScore,
            tags: tags,
            createdAt: createdAt,
            updatedAt: updatedAt,
            metadata: metadata,
            rowid: rowid,
          ),
        ));
}

class $$QuestionsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $QuestionsTable> {
  $$QuestionsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get assessmentId => $state.composableBuilder(
      column: $state.table.assessmentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get questionBankId => $state.composableBuilder(
      column: $state.table.questionBankId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get subject => $state.composableBuilder(
      column: $state.table.subject,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get chapterIds => $state.composableBuilder(
          column: $state.table.chapterIds,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get competencyIds => $state.composableBuilder(
          column: $state.table.competencyIds,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<String> get bloomLevel => $state.composableBuilder(
      column: $state.table.bloomLevel,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get difficulty => $state.composableBuilder(
      column: $state.table.difficulty,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get type => $state.composableBuilder(
      column: $state.table.type,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get stem => $state.composableBuilder(
      column: $state.table.stem,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get stemLatex => $state.composableBuilder(
      column: $state.table.stemLatex,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get parts => $state.composableBuilder(
          column: $state.table.parts,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get answerScheme => $state.composableBuilder(
          column: $state.table.answerScheme,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<int> get estimatedTimeMinutes => $state.composableBuilder(
      column: $state.table.estimatedTimeMinutes,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get marks => $state.composableBuilder(
      column: $state.table.marks,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get language => $state.composableBuilder(
      column: $state.table.language,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get source => $state.composableBuilder(
      column: $state.table.source,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<double> get qualityScore => $state.composableBuilder(
      column: $state.table.qualityScore,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String> get tags =>
      $state.composableBuilder(
          column: $state.table.tags,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get updatedAt => $state.composableBuilder(
      column: $state.table.updatedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get metadata => $state.composableBuilder(
          column: $state.table.metadata,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));
}

class $$QuestionsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $QuestionsTable> {
  $$QuestionsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get assessmentId => $state.composableBuilder(
      column: $state.table.assessmentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get questionBankId => $state.composableBuilder(
      column: $state.table.questionBankId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get subject => $state.composableBuilder(
      column: $state.table.subject,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get chapterIds => $state.composableBuilder(
      column: $state.table.chapterIds,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get competencyIds => $state.composableBuilder(
      column: $state.table.competencyIds,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get bloomLevel => $state.composableBuilder(
      column: $state.table.bloomLevel,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get difficulty => $state.composableBuilder(
      column: $state.table.difficulty,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get type => $state.composableBuilder(
      column: $state.table.type,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get stem => $state.composableBuilder(
      column: $state.table.stem,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get stemLatex => $state.composableBuilder(
      column: $state.table.stemLatex,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get parts => $state.composableBuilder(
      column: $state.table.parts,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get answerScheme => $state.composableBuilder(
      column: $state.table.answerScheme,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get estimatedTimeMinutes => $state.composableBuilder(
      column: $state.table.estimatedTimeMinutes,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get marks => $state.composableBuilder(
      column: $state.table.marks,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get language => $state.composableBuilder(
      column: $state.table.language,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get source => $state.composableBuilder(
      column: $state.table.source,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<double> get qualityScore => $state.composableBuilder(
      column: $state.table.qualityScore,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get tags => $state.composableBuilder(
      column: $state.table.tags,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get updatedAt => $state.composableBuilder(
      column: $state.table.updatedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get metadata => $state.composableBuilder(
      column: $state.table.metadata,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$AnswerSheetsTableCreateCompanionBuilder = AnswerSheetsCompanion
    Function({
  required String id,
  required String assessmentId,
  required String studentId,
  required String studentName,
  required String rollNumber,
  required Map<String, dynamic> pages,
  required Map<String, dynamic> scanMetadata,
  required Map<String, dynamic> responses,
  required String status,
  required DateTime submittedAt,
  required DateTime scannedAt,
  Value<DateTime?> evaluatedAt,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});
typedef $$AnswerSheetsTableUpdateCompanionBuilder = AnswerSheetsCompanion
    Function({
  Value<String> id,
  Value<String> assessmentId,
  Value<String> studentId,
  Value<String> studentName,
  Value<String> rollNumber,
  Value<Map<String, dynamic>> pages,
  Value<Map<String, dynamic>> scanMetadata,
  Value<Map<String, dynamic>> responses,
  Value<String> status,
  Value<DateTime> submittedAt,
  Value<DateTime> scannedAt,
  Value<DateTime?> evaluatedAt,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});

class $$AnswerSheetsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $AnswerSheetsTable,
    AnswerSheetRow,
    $$AnswerSheetsTableFilterComposer,
    $$AnswerSheetsTableOrderingComposer,
    $$AnswerSheetsTableCreateCompanionBuilder,
    $$AnswerSheetsTableUpdateCompanionBuilder> {
  $$AnswerSheetsTableTableManager(_$AppDatabase db, $AnswerSheetsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$AnswerSheetsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$AnswerSheetsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> assessmentId = const Value.absent(),
            Value<String> studentId = const Value.absent(),
            Value<String> studentName = const Value.absent(),
            Value<String> rollNumber = const Value.absent(),
            Value<Map<String, dynamic>> pages = const Value.absent(),
            Value<Map<String, dynamic>> scanMetadata = const Value.absent(),
            Value<Map<String, dynamic>> responses = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<DateTime> submittedAt = const Value.absent(),
            Value<DateTime> scannedAt = const Value.absent(),
            Value<DateTime?> evaluatedAt = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AnswerSheetsCompanion(
            id: id,
            assessmentId: assessmentId,
            studentId: studentId,
            studentName: studentName,
            rollNumber: rollNumber,
            pages: pages,
            scanMetadata: scanMetadata,
            responses: responses,
            status: status,
            submittedAt: submittedAt,
            scannedAt: scannedAt,
            evaluatedAt: evaluatedAt,
            metadata: metadata,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String assessmentId,
            required String studentId,
            required String studentName,
            required String rollNumber,
            required Map<String, dynamic> pages,
            required Map<String, dynamic> scanMetadata,
            required Map<String, dynamic> responses,
            required String status,
            required DateTime submittedAt,
            required DateTime scannedAt,
            Value<DateTime?> evaluatedAt = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AnswerSheetsCompanion.insert(
            id: id,
            assessmentId: assessmentId,
            studentId: studentId,
            studentName: studentName,
            rollNumber: rollNumber,
            pages: pages,
            scanMetadata: scanMetadata,
            responses: responses,
            status: status,
            submittedAt: submittedAt,
            scannedAt: scannedAt,
            evaluatedAt: evaluatedAt,
            metadata: metadata,
            rowid: rowid,
          ),
        ));
}

class $$AnswerSheetsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $AnswerSheetsTable> {
  $$AnswerSheetsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get assessmentId => $state.composableBuilder(
      column: $state.table.assessmentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentName => $state.composableBuilder(
      column: $state.table.studentName,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get rollNumber => $state.composableBuilder(
      column: $state.table.rollNumber,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get pages => $state.composableBuilder(
          column: $state.table.pages,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get scanMetadata => $state.composableBuilder(
          column: $state.table.scanMetadata,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get responses => $state.composableBuilder(
          column: $state.table.responses,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get submittedAt => $state.composableBuilder(
      column: $state.table.submittedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get scannedAt => $state.composableBuilder(
      column: $state.table.scannedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get evaluatedAt => $state.composableBuilder(
      column: $state.table.evaluatedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get metadata => $state.composableBuilder(
          column: $state.table.metadata,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));
}

class $$AnswerSheetsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $AnswerSheetsTable> {
  $$AnswerSheetsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get assessmentId => $state.composableBuilder(
      column: $state.table.assessmentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentName => $state.composableBuilder(
      column: $state.table.studentName,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get rollNumber => $state.composableBuilder(
      column: $state.table.rollNumber,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get pages => $state.composableBuilder(
      column: $state.table.pages,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get scanMetadata => $state.composableBuilder(
      column: $state.table.scanMetadata,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get responses => $state.composableBuilder(
      column: $state.table.responses,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get submittedAt => $state.composableBuilder(
      column: $state.table.submittedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get scannedAt => $state.composableBuilder(
      column: $state.table.scannedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get evaluatedAt => $state.composableBuilder(
      column: $state.table.evaluatedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get metadata => $state.composableBuilder(
      column: $state.table.metadata,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$EvaluationsTableCreateCompanionBuilder = EvaluationsCompanion
    Function({
  required String id,
  required String answerSheetId,
  required String questionId,
  required String studentAnswer,
  Value<String?> studentAnswerLatex,
  required List<String> studentAnswerImages,
  required int awardedMarks,
  required int maxMarks,
  required double percentage,
  required String verdict,
  required Map<String, dynamic> markingPoints,
  required Map<String, dynamic> rubricLevel,
  required double confidenceScore,
  required String reasoning,
  required List<String> strengths,
  required List<String> gaps,
  required List<String> carelessErrors,
  required int estimatedTimeSpentSeconds,
  required String status,
  required DateTime evaluatedAt,
  Value<String?> teacherComment,
  Value<int?> teacherAdjustedMarks,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});
typedef $$EvaluationsTableUpdateCompanionBuilder = EvaluationsCompanion
    Function({
  Value<String> id,
  Value<String> answerSheetId,
  Value<String> questionId,
  Value<String> studentAnswer,
  Value<String?> studentAnswerLatex,
  Value<List<String>> studentAnswerImages,
  Value<int> awardedMarks,
  Value<int> maxMarks,
  Value<double> percentage,
  Value<String> verdict,
  Value<Map<String, dynamic>> markingPoints,
  Value<Map<String, dynamic>> rubricLevel,
  Value<double> confidenceScore,
  Value<String> reasoning,
  Value<List<String>> strengths,
  Value<List<String>> gaps,
  Value<List<String>> carelessErrors,
  Value<int> estimatedTimeSpentSeconds,
  Value<String> status,
  Value<DateTime> evaluatedAt,
  Value<String?> teacherComment,
  Value<int?> teacherAdjustedMarks,
  Value<Map<String, dynamic>> metadata,
  Value<int> rowid,
});

class $$EvaluationsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $EvaluationsTable,
    Evaluation,
    $$EvaluationsTableFilterComposer,
    $$EvaluationsTableOrderingComposer,
    $$EvaluationsTableCreateCompanionBuilder,
    $$EvaluationsTableUpdateCompanionBuilder> {
  $$EvaluationsTableTableManager(_$AppDatabase db, $EvaluationsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$EvaluationsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$EvaluationsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> answerSheetId = const Value.absent(),
            Value<String> questionId = const Value.absent(),
            Value<String> studentAnswer = const Value.absent(),
            Value<String?> studentAnswerLatex = const Value.absent(),
            Value<List<String>> studentAnswerImages = const Value.absent(),
            Value<int> awardedMarks = const Value.absent(),
            Value<int> maxMarks = const Value.absent(),
            Value<double> percentage = const Value.absent(),
            Value<String> verdict = const Value.absent(),
            Value<Map<String, dynamic>> markingPoints = const Value.absent(),
            Value<Map<String, dynamic>> rubricLevel = const Value.absent(),
            Value<double> confidenceScore = const Value.absent(),
            Value<String> reasoning = const Value.absent(),
            Value<List<String>> strengths = const Value.absent(),
            Value<List<String>> gaps = const Value.absent(),
            Value<List<String>> carelessErrors = const Value.absent(),
            Value<int> estimatedTimeSpentSeconds = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<DateTime> evaluatedAt = const Value.absent(),
            Value<String?> teacherComment = const Value.absent(),
            Value<int?> teacherAdjustedMarks = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              EvaluationsCompanion(
            id: id,
            answerSheetId: answerSheetId,
            questionId: questionId,
            studentAnswer: studentAnswer,
            studentAnswerLatex: studentAnswerLatex,
            studentAnswerImages: studentAnswerImages,
            awardedMarks: awardedMarks,
            maxMarks: maxMarks,
            percentage: percentage,
            verdict: verdict,
            markingPoints: markingPoints,
            rubricLevel: rubricLevel,
            confidenceScore: confidenceScore,
            reasoning: reasoning,
            strengths: strengths,
            gaps: gaps,
            carelessErrors: carelessErrors,
            estimatedTimeSpentSeconds: estimatedTimeSpentSeconds,
            status: status,
            evaluatedAt: evaluatedAt,
            teacherComment: teacherComment,
            teacherAdjustedMarks: teacherAdjustedMarks,
            metadata: metadata,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String answerSheetId,
            required String questionId,
            required String studentAnswer,
            Value<String?> studentAnswerLatex = const Value.absent(),
            required List<String> studentAnswerImages,
            required int awardedMarks,
            required int maxMarks,
            required double percentage,
            required String verdict,
            required Map<String, dynamic> markingPoints,
            required Map<String, dynamic> rubricLevel,
            required double confidenceScore,
            required String reasoning,
            required List<String> strengths,
            required List<String> gaps,
            required List<String> carelessErrors,
            required int estimatedTimeSpentSeconds,
            required String status,
            required DateTime evaluatedAt,
            Value<String?> teacherComment = const Value.absent(),
            Value<int?> teacherAdjustedMarks = const Value.absent(),
            Value<Map<String, dynamic>> metadata = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              EvaluationsCompanion.insert(
            id: id,
            answerSheetId: answerSheetId,
            questionId: questionId,
            studentAnswer: studentAnswer,
            studentAnswerLatex: studentAnswerLatex,
            studentAnswerImages: studentAnswerImages,
            awardedMarks: awardedMarks,
            maxMarks: maxMarks,
            percentage: percentage,
            verdict: verdict,
            markingPoints: markingPoints,
            rubricLevel: rubricLevel,
            confidenceScore: confidenceScore,
            reasoning: reasoning,
            strengths: strengths,
            gaps: gaps,
            carelessErrors: carelessErrors,
            estimatedTimeSpentSeconds: estimatedTimeSpentSeconds,
            status: status,
            evaluatedAt: evaluatedAt,
            teacherComment: teacherComment,
            teacherAdjustedMarks: teacherAdjustedMarks,
            metadata: metadata,
            rowid: rowid,
          ),
        ));
}

class $$EvaluationsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $EvaluationsTable> {
  $$EvaluationsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get answerSheetId => $state.composableBuilder(
      column: $state.table.answerSheetId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get questionId => $state.composableBuilder(
      column: $state.table.questionId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentAnswer => $state.composableBuilder(
      column: $state.table.studentAnswer,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentAnswerLatex => $state.composableBuilder(
      column: $state.table.studentAnswerLatex,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get studentAnswerImages => $state.composableBuilder(
          column: $state.table.studentAnswerImages,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<int> get awardedMarks => $state.composableBuilder(
      column: $state.table.awardedMarks,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get maxMarks => $state.composableBuilder(
      column: $state.table.maxMarks,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<double> get percentage => $state.composableBuilder(
      column: $state.table.percentage,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get verdict => $state.composableBuilder(
      column: $state.table.verdict,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get markingPoints => $state.composableBuilder(
          column: $state.table.markingPoints,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get rubricLevel => $state.composableBuilder(
          column: $state.table.rubricLevel,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<double> get confidenceScore => $state.composableBuilder(
      column: $state.table.confidenceScore,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get reasoning => $state.composableBuilder(
      column: $state.table.reasoning,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get strengths => $state.composableBuilder(
          column: $state.table.strengths,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String> get gaps =>
      $state.composableBuilder(
          column: $state.table.gaps,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get carelessErrors => $state.composableBuilder(
          column: $state.table.carelessErrors,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<int> get estimatedTimeSpentSeconds => $state.composableBuilder(
      column: $state.table.estimatedTimeSpentSeconds,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get evaluatedAt => $state.composableBuilder(
      column: $state.table.evaluatedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get teacherComment => $state.composableBuilder(
      column: $state.table.teacherComment,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get teacherAdjustedMarks => $state.composableBuilder(
      column: $state.table.teacherAdjustedMarks,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get metadata => $state.composableBuilder(
          column: $state.table.metadata,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));
}

class $$EvaluationsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $EvaluationsTable> {
  $$EvaluationsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get answerSheetId => $state.composableBuilder(
      column: $state.table.answerSheetId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get questionId => $state.composableBuilder(
      column: $state.table.questionId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentAnswer => $state.composableBuilder(
      column: $state.table.studentAnswer,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentAnswerLatex => $state.composableBuilder(
      column: $state.table.studentAnswerLatex,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentAnswerImages => $state.composableBuilder(
      column: $state.table.studentAnswerImages,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get awardedMarks => $state.composableBuilder(
      column: $state.table.awardedMarks,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get maxMarks => $state.composableBuilder(
      column: $state.table.maxMarks,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<double> get percentage => $state.composableBuilder(
      column: $state.table.percentage,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get verdict => $state.composableBuilder(
      column: $state.table.verdict,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get markingPoints => $state.composableBuilder(
      column: $state.table.markingPoints,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get rubricLevel => $state.composableBuilder(
      column: $state.table.rubricLevel,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<double> get confidenceScore => $state.composableBuilder(
      column: $state.table.confidenceScore,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get reasoning => $state.composableBuilder(
      column: $state.table.reasoning,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get strengths => $state.composableBuilder(
      column: $state.table.strengths,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get gaps => $state.composableBuilder(
      column: $state.table.gaps,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get carelessErrors => $state.composableBuilder(
      column: $state.table.carelessErrors,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get estimatedTimeSpentSeconds =>
      $state.composableBuilder(
          column: $state.table.estimatedTimeSpentSeconds,
          builder: (column, joinBuilders) =>
              ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get evaluatedAt => $state.composableBuilder(
      column: $state.table.evaluatedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get teacherComment => $state.composableBuilder(
      column: $state.table.teacherComment,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get teacherAdjustedMarks => $state.composableBuilder(
      column: $state.table.teacherAdjustedMarks,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get metadata => $state.composableBuilder(
      column: $state.table.metadata,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$StudentMasteryTableTableCreateCompanionBuilder
    = StudentMasteryTableCompanion Function({
  required String studentId,
  required String schoolId,
  required String grade,
  required Map<String, dynamic> concepts,
  required Map<String, dynamic> chapters,
  required Map<String, dynamic> subjects,
  required Map<String, dynamic> summary,
  required DateTime lastUpdated,
  required int version,
  Value<int> rowid,
});
typedef $$StudentMasteryTableTableUpdateCompanionBuilder
    = StudentMasteryTableCompanion Function({
  Value<String> studentId,
  Value<String> schoolId,
  Value<String> grade,
  Value<Map<String, dynamic>> concepts,
  Value<Map<String, dynamic>> chapters,
  Value<Map<String, dynamic>> subjects,
  Value<Map<String, dynamic>> summary,
  Value<DateTime> lastUpdated,
  Value<int> version,
  Value<int> rowid,
});

class $$StudentMasteryTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $StudentMasteryTableTable,
    StudentMasteryTableData,
    $$StudentMasteryTableTableFilterComposer,
    $$StudentMasteryTableTableOrderingComposer,
    $$StudentMasteryTableTableCreateCompanionBuilder,
    $$StudentMasteryTableTableUpdateCompanionBuilder> {
  $$StudentMasteryTableTableTableManager(
      _$AppDatabase db, $StudentMasteryTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer: $$StudentMasteryTableTableFilterComposer(
              ComposerState(db, table)),
          orderingComposer: $$StudentMasteryTableTableOrderingComposer(
              ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> studentId = const Value.absent(),
            Value<String> schoolId = const Value.absent(),
            Value<String> grade = const Value.absent(),
            Value<Map<String, dynamic>> concepts = const Value.absent(),
            Value<Map<String, dynamic>> chapters = const Value.absent(),
            Value<Map<String, dynamic>> subjects = const Value.absent(),
            Value<Map<String, dynamic>> summary = const Value.absent(),
            Value<DateTime> lastUpdated = const Value.absent(),
            Value<int> version = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              StudentMasteryTableCompanion(
            studentId: studentId,
            schoolId: schoolId,
            grade: grade,
            concepts: concepts,
            chapters: chapters,
            subjects: subjects,
            summary: summary,
            lastUpdated: lastUpdated,
            version: version,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String studentId,
            required String schoolId,
            required String grade,
            required Map<String, dynamic> concepts,
            required Map<String, dynamic> chapters,
            required Map<String, dynamic> subjects,
            required Map<String, dynamic> summary,
            required DateTime lastUpdated,
            required int version,
            Value<int> rowid = const Value.absent(),
          }) =>
              StudentMasteryTableCompanion.insert(
            studentId: studentId,
            schoolId: schoolId,
            grade: grade,
            concepts: concepts,
            chapters: chapters,
            subjects: subjects,
            summary: summary,
            lastUpdated: lastUpdated,
            version: version,
            rowid: rowid,
          ),
        ));
}

class $$StudentMasteryTableTableFilterComposer
    extends FilterComposer<_$AppDatabase, $StudentMasteryTableTable> {
  $$StudentMasteryTableTableFilterComposer(super.$state);
  ColumnFilters<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get schoolId => $state.composableBuilder(
      column: $state.table.schoolId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get concepts => $state.composableBuilder(
          column: $state.table.concepts,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get chapters => $state.composableBuilder(
          column: $state.table.chapters,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get subjects => $state.composableBuilder(
          column: $state.table.subjects,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get summary => $state.composableBuilder(
          column: $state.table.summary,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get lastUpdated => $state.composableBuilder(
      column: $state.table.lastUpdated,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get version => $state.composableBuilder(
      column: $state.table.version,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));
}

class $$StudentMasteryTableTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $StudentMasteryTableTable> {
  $$StudentMasteryTableTableOrderingComposer(super.$state);
  ColumnOrderings<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get schoolId => $state.composableBuilder(
      column: $state.table.schoolId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get concepts => $state.composableBuilder(
      column: $state.table.concepts,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get chapters => $state.composableBuilder(
      column: $state.table.chapters,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get subjects => $state.composableBuilder(
      column: $state.table.subjects,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get summary => $state.composableBuilder(
      column: $state.table.summary,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get lastUpdated => $state.composableBuilder(
      column: $state.table.lastUpdated,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get version => $state.composableBuilder(
      column: $state.table.version,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$PracticeSessionsTableCreateCompanionBuilder
    = PracticeSessionsCompanion Function({
  required String id,
  required String studentId,
  required List<String> conceptIds,
  required String type,
  required int questionCount,
  required int durationMinutes,
  required Map<String, dynamic> questions,
  required String status,
  required DateTime createdAt,
  Value<DateTime?> startedAt,
  Value<DateTime?> completedAt,
  Value<Map<String, dynamic>?> result,
  Value<int> rowid,
});
typedef $$PracticeSessionsTableUpdateCompanionBuilder
    = PracticeSessionsCompanion Function({
  Value<String> id,
  Value<String> studentId,
  Value<List<String>> conceptIds,
  Value<String> type,
  Value<int> questionCount,
  Value<int> durationMinutes,
  Value<Map<String, dynamic>> questions,
  Value<String> status,
  Value<DateTime> createdAt,
  Value<DateTime?> startedAt,
  Value<DateTime?> completedAt,
  Value<Map<String, dynamic>?> result,
  Value<int> rowid,
});

class $$PracticeSessionsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $PracticeSessionsTable,
    PracticeSessionRow,
    $$PracticeSessionsTableFilterComposer,
    $$PracticeSessionsTableOrderingComposer,
    $$PracticeSessionsTableCreateCompanionBuilder,
    $$PracticeSessionsTableUpdateCompanionBuilder> {
  $$PracticeSessionsTableTableManager(
      _$AppDatabase db, $PracticeSessionsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$PracticeSessionsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$PracticeSessionsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> studentId = const Value.absent(),
            Value<List<String>> conceptIds = const Value.absent(),
            Value<String> type = const Value.absent(),
            Value<int> questionCount = const Value.absent(),
            Value<int> durationMinutes = const Value.absent(),
            Value<Map<String, dynamic>> questions = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<DateTime?> startedAt = const Value.absent(),
            Value<DateTime?> completedAt = const Value.absent(),
            Value<Map<String, dynamic>?> result = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              PracticeSessionsCompanion(
            id: id,
            studentId: studentId,
            conceptIds: conceptIds,
            type: type,
            questionCount: questionCount,
            durationMinutes: durationMinutes,
            questions: questions,
            status: status,
            createdAt: createdAt,
            startedAt: startedAt,
            completedAt: completedAt,
            result: result,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String studentId,
            required List<String> conceptIds,
            required String type,
            required int questionCount,
            required int durationMinutes,
            required Map<String, dynamic> questions,
            required String status,
            required DateTime createdAt,
            Value<DateTime?> startedAt = const Value.absent(),
            Value<DateTime?> completedAt = const Value.absent(),
            Value<Map<String, dynamic>?> result = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              PracticeSessionsCompanion.insert(
            id: id,
            studentId: studentId,
            conceptIds: conceptIds,
            type: type,
            questionCount: questionCount,
            durationMinutes: durationMinutes,
            questions: questions,
            status: status,
            createdAt: createdAt,
            startedAt: startedAt,
            completedAt: completedAt,
            result: result,
            rowid: rowid,
          ),
        ));
}

class $$PracticeSessionsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $PracticeSessionsTable> {
  $$PracticeSessionsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
      get conceptIds => $state.composableBuilder(
          column: $state.table.conceptIds,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<String> get type => $state.composableBuilder(
      column: $state.table.type,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get questionCount => $state.composableBuilder(
      column: $state.table.questionCount,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get durationMinutes => $state.composableBuilder(
      column: $state.table.durationMinutes,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get questions => $state.composableBuilder(
          column: $state.table.questions,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get startedAt => $state.composableBuilder(
      column: $state.table.startedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get completedAt => $state.composableBuilder(
      column: $state.table.completedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>?, Map<String, dynamic>,
          String>
      get result => $state.composableBuilder(
          column: $state.table.result,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));
}

class $$PracticeSessionsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $PracticeSessionsTable> {
  $$PracticeSessionsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get conceptIds => $state.composableBuilder(
      column: $state.table.conceptIds,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get type => $state.composableBuilder(
      column: $state.table.type,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get questionCount => $state.composableBuilder(
      column: $state.table.questionCount,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get durationMinutes => $state.composableBuilder(
      column: $state.table.durationMinutes,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get questions => $state.composableBuilder(
      column: $state.table.questions,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get status => $state.composableBuilder(
      column: $state.table.status,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get startedAt => $state.composableBuilder(
      column: $state.table.startedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get completedAt => $state.composableBuilder(
      column: $state.table.completedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get result => $state.composableBuilder(
      column: $state.table.result,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$ReportsTableCreateCompanionBuilder = ReportsCompanion Function({
  required String id,
  required String assessmentId,
  required String assessmentTitle,
  required String studentId,
  required String studentName,
  required String rollNumber,
  required int grade,
  required String section,
  required Map<String, dynamic> report,
  required DateTime generatedAt,
  required String generatedBy,
  Value<int> rowid,
});
typedef $$ReportsTableUpdateCompanionBuilder = ReportsCompanion Function({
  Value<String> id,
  Value<String> assessmentId,
  Value<String> assessmentTitle,
  Value<String> studentId,
  Value<String> studentName,
  Value<String> rollNumber,
  Value<int> grade,
  Value<String> section,
  Value<Map<String, dynamic>> report,
  Value<DateTime> generatedAt,
  Value<String> generatedBy,
  Value<int> rowid,
});

class $$ReportsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $ReportsTable,
    Report,
    $$ReportsTableFilterComposer,
    $$ReportsTableOrderingComposer,
    $$ReportsTableCreateCompanionBuilder,
    $$ReportsTableUpdateCompanionBuilder> {
  $$ReportsTableTableManager(_$AppDatabase db, $ReportsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$ReportsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$ReportsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> assessmentId = const Value.absent(),
            Value<String> assessmentTitle = const Value.absent(),
            Value<String> studentId = const Value.absent(),
            Value<String> studentName = const Value.absent(),
            Value<String> rollNumber = const Value.absent(),
            Value<int> grade = const Value.absent(),
            Value<String> section = const Value.absent(),
            Value<Map<String, dynamic>> report = const Value.absent(),
            Value<DateTime> generatedAt = const Value.absent(),
            Value<String> generatedBy = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              ReportsCompanion(
            id: id,
            assessmentId: assessmentId,
            assessmentTitle: assessmentTitle,
            studentId: studentId,
            studentName: studentName,
            rollNumber: rollNumber,
            grade: grade,
            section: section,
            report: report,
            generatedAt: generatedAt,
            generatedBy: generatedBy,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String assessmentId,
            required String assessmentTitle,
            required String studentId,
            required String studentName,
            required String rollNumber,
            required int grade,
            required String section,
            required Map<String, dynamic> report,
            required DateTime generatedAt,
            required String generatedBy,
            Value<int> rowid = const Value.absent(),
          }) =>
              ReportsCompanion.insert(
            id: id,
            assessmentId: assessmentId,
            assessmentTitle: assessmentTitle,
            studentId: studentId,
            studentName: studentName,
            rollNumber: rollNumber,
            grade: grade,
            section: section,
            report: report,
            generatedAt: generatedAt,
            generatedBy: generatedBy,
            rowid: rowid,
          ),
        ));
}

class $$ReportsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $ReportsTable> {
  $$ReportsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get assessmentId => $state.composableBuilder(
      column: $state.table.assessmentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get assessmentTitle => $state.composableBuilder(
      column: $state.table.assessmentTitle,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get studentName => $state.composableBuilder(
      column: $state.table.studentName,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get rollNumber => $state.composableBuilder(
      column: $state.table.rollNumber,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<int> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get section => $state.composableBuilder(
      column: $state.table.section,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get report => $state.composableBuilder(
          column: $state.table.report,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get generatedAt => $state.composableBuilder(
      column: $state.table.generatedAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get generatedBy => $state.composableBuilder(
      column: $state.table.generatedBy,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));
}

class $$ReportsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $ReportsTable> {
  $$ReportsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get assessmentId => $state.composableBuilder(
      column: $state.table.assessmentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get assessmentTitle => $state.composableBuilder(
      column: $state.table.assessmentTitle,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentId => $state.composableBuilder(
      column: $state.table.studentId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get studentName => $state.composableBuilder(
      column: $state.table.studentName,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get rollNumber => $state.composableBuilder(
      column: $state.table.rollNumber,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get grade => $state.composableBuilder(
      column: $state.table.grade,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get section => $state.composableBuilder(
      column: $state.table.section,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get report => $state.composableBuilder(
      column: $state.table.report,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get generatedAt => $state.composableBuilder(
      column: $state.table.generatedAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get generatedBy => $state.composableBuilder(
      column: $state.table.generatedBy,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$NotificationsTableCreateCompanionBuilder = NotificationsCompanion
    Function({
  required String id,
  required String userId,
  required String type,
  required String title,
  required String body,
  required Map<String, dynamic> data,
  required DateTime createdAt,
  required bool isRead,
  Value<DateTime?> readAt,
  Value<int> rowid,
});
typedef $$NotificationsTableUpdateCompanionBuilder = NotificationsCompanion
    Function({
  Value<String> id,
  Value<String> userId,
  Value<String> type,
  Value<String> title,
  Value<String> body,
  Value<Map<String, dynamic>> data,
  Value<DateTime> createdAt,
  Value<bool> isRead,
  Value<DateTime?> readAt,
  Value<int> rowid,
});

class $$NotificationsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $NotificationsTable,
    NotificationRow,
    $$NotificationsTableFilterComposer,
    $$NotificationsTableOrderingComposer,
    $$NotificationsTableCreateCompanionBuilder,
    $$NotificationsTableUpdateCompanionBuilder> {
  $$NotificationsTableTableManager(_$AppDatabase db, $NotificationsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$NotificationsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$NotificationsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> userId = const Value.absent(),
            Value<String> type = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String> body = const Value.absent(),
            Value<Map<String, dynamic>> data = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<bool> isRead = const Value.absent(),
            Value<DateTime?> readAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              NotificationsCompanion(
            id: id,
            userId: userId,
            type: type,
            title: title,
            body: body,
            data: data,
            createdAt: createdAt,
            isRead: isRead,
            readAt: readAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String userId,
            required String type,
            required String title,
            required String body,
            required Map<String, dynamic> data,
            required DateTime createdAt,
            required bool isRead,
            Value<DateTime?> readAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              NotificationsCompanion.insert(
            id: id,
            userId: userId,
            type: type,
            title: title,
            body: body,
            data: data,
            createdAt: createdAt,
            isRead: isRead,
            readAt: readAt,
            rowid: rowid,
          ),
        ));
}

class $$NotificationsTableFilterComposer
    extends FilterComposer<_$AppDatabase, $NotificationsTable> {
  $$NotificationsTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get userId => $state.composableBuilder(
      column: $state.table.userId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get type => $state.composableBuilder(
      column: $state.table.type,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get title => $state.composableBuilder(
      column: $state.table.title,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get body => $state.composableBuilder(
      column: $state.table.body,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get data => $state.composableBuilder(
          column: $state.table.data,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<bool> get isRead => $state.composableBuilder(
      column: $state.table.isRead,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get readAt => $state.composableBuilder(
      column: $state.table.readAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));
}

class $$NotificationsTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $NotificationsTable> {
  $$NotificationsTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get userId => $state.composableBuilder(
      column: $state.table.userId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get type => $state.composableBuilder(
      column: $state.table.type,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get title => $state.composableBuilder(
      column: $state.table.title,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get body => $state.composableBuilder(
      column: $state.table.body,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get data => $state.composableBuilder(
      column: $state.table.data,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<bool> get isRead => $state.composableBuilder(
      column: $state.table.isRead,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get readAt => $state.composableBuilder(
      column: $state.table.readAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

typedef $$SyncQueueTableCreateCompanionBuilder = SyncQueueCompanion Function({
  required String id,
  required String entityType,
  required String entityId,
  required String operation,
  required Map<String, dynamic> payload,
  Value<int> retryCount,
  required DateTime createdAt,
  required DateTime nextRetryAt,
  Value<String?> error,
  Value<int> rowid,
});
typedef $$SyncQueueTableUpdateCompanionBuilder = SyncQueueCompanion Function({
  Value<String> id,
  Value<String> entityType,
  Value<String> entityId,
  Value<String> operation,
  Value<Map<String, dynamic>> payload,
  Value<int> retryCount,
  Value<DateTime> createdAt,
  Value<DateTime> nextRetryAt,
  Value<String?> error,
  Value<int> rowid,
});

class $$SyncQueueTableTableManager extends RootTableManager<
    _$AppDatabase,
    $SyncQueueTable,
    SyncQueueData,
    $$SyncQueueTableFilterComposer,
    $$SyncQueueTableOrderingComposer,
    $$SyncQueueTableCreateCompanionBuilder,
    $$SyncQueueTableUpdateCompanionBuilder> {
  $$SyncQueueTableTableManager(_$AppDatabase db, $SyncQueueTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$SyncQueueTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$SyncQueueTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> entityType = const Value.absent(),
            Value<String> entityId = const Value.absent(),
            Value<String> operation = const Value.absent(),
            Value<Map<String, dynamic>> payload = const Value.absent(),
            Value<int> retryCount = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<DateTime> nextRetryAt = const Value.absent(),
            Value<String?> error = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              SyncQueueCompanion(
            id: id,
            entityType: entityType,
            entityId: entityId,
            operation: operation,
            payload: payload,
            retryCount: retryCount,
            createdAt: createdAt,
            nextRetryAt: nextRetryAt,
            error: error,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String entityType,
            required String entityId,
            required String operation,
            required Map<String, dynamic> payload,
            Value<int> retryCount = const Value.absent(),
            required DateTime createdAt,
            required DateTime nextRetryAt,
            Value<String?> error = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              SyncQueueCompanion.insert(
            id: id,
            entityType: entityType,
            entityId: entityId,
            operation: operation,
            payload: payload,
            retryCount: retryCount,
            createdAt: createdAt,
            nextRetryAt: nextRetryAt,
            error: error,
            rowid: rowid,
          ),
        ));
}

class $$SyncQueueTableFilterComposer
    extends FilterComposer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableFilterComposer(super.$state);
  ColumnFilters<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get entityType => $state.composableBuilder(
      column: $state.table.entityType,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get entityId => $state.composableBuilder(
      column: $state.table.entityId,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get operation => $state.composableBuilder(
      column: $state.table.operation,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnWithTypeConverterFilters<Map<String, dynamic>, Map<String, dynamic>,
          String>
      get payload => $state.composableBuilder(
          column: $state.table.payload,
          builder: (column, joinBuilders) => ColumnWithTypeConverterFilters(
              column,
              joinBuilders: joinBuilders));

  ColumnFilters<int> get retryCount => $state.composableBuilder(
      column: $state.table.retryCount,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get nextRetryAt => $state.composableBuilder(
      column: $state.table.nextRetryAt,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get error => $state.composableBuilder(
      column: $state.table.error,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));
}

class $$SyncQueueTableOrderingComposer
    extends OrderingComposer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableOrderingComposer(super.$state);
  ColumnOrderings<String> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get entityType => $state.composableBuilder(
      column: $state.table.entityType,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get entityId => $state.composableBuilder(
      column: $state.table.entityId,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get operation => $state.composableBuilder(
      column: $state.table.operation,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get payload => $state.composableBuilder(
      column: $state.table.payload,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<int> get retryCount => $state.composableBuilder(
      column: $state.table.retryCount,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get createdAt => $state.composableBuilder(
      column: $state.table.createdAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get nextRetryAt => $state.composableBuilder(
      column: $state.table.nextRetryAt,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get error => $state.composableBuilder(
      column: $state.table.error,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$AssessmentsTableTableManager get assessments =>
      $$AssessmentsTableTableManager(_db, _db.assessments);
  $$QuestionsTableTableManager get questions =>
      $$QuestionsTableTableManager(_db, _db.questions);
  $$AnswerSheetsTableTableManager get answerSheets =>
      $$AnswerSheetsTableTableManager(_db, _db.answerSheets);
  $$EvaluationsTableTableManager get evaluations =>
      $$EvaluationsTableTableManager(_db, _db.evaluations);
  $$StudentMasteryTableTableTableManager get studentMasteryTable =>
      $$StudentMasteryTableTableTableManager(_db, _db.studentMasteryTable);
  $$PracticeSessionsTableTableManager get practiceSessions =>
      $$PracticeSessionsTableTableManager(_db, _db.practiceSessions);
  $$ReportsTableTableManager get reports =>
      $$ReportsTableTableManager(_db, _db.reports);
  $$NotificationsTableTableManager get notifications =>
      $$NotificationsTableTableManager(_db, _db.notifications);
  $$SyncQueueTableTableManager get syncQueue =>
      $$SyncQueueTableTableManager(_db, _db.syncQueue);
}
