// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'report.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

StudentReport _$StudentReportFromJson(Map<String, dynamic> json) {
  return _StudentReport.fromJson(json);
}

/// @nodoc
mixin _$StudentReport {
  String get id => throw _privateConstructorUsedError;
  String get assessmentId => throw _privateConstructorUsedError;
  String get assessmentTitle => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  String get studentName => throw _privateConstructorUsedError;
  String get rollNumber => throw _privateConstructorUsedError;
  int get grade => throw _privateConstructorUsedError;
  String get section => throw _privateConstructorUsedError;
  ReportHeader get header => throw _privateConstructorUsedError;
  PerformanceOverview get overview => throw _privateConstructorUsedError;
  List<SectionReport> get sectionReports => throw _privateConstructorUsedError;
  List<ConceptReport> get conceptReports => throw _privateConstructorUsedError;
  BloomReport get bloomReport => throw _privateConstructorUsedError;
  CompetencyReport get competencyReport => throw _privateConstructorUsedError;
  List<String> get strengths => throw _privateConstructorUsedError;
  List<String> get weaknesses => throw _privateConstructorUsedError;
  List<String> get carelessErrors => throw _privateConstructorUsedError;
  List<ActionableRecommendation> get recommendations =>
      throw _privateConstructorUsedError;
  TeacherRemarks get teacherRemarks => throw _privateConstructorUsedError;
  ParentSummary get parentSummary => throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;
  String get generatedBy => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $StudentReportCopyWith<StudentReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StudentReportCopyWith<$Res> {
  factory $StudentReportCopyWith(
          StudentReport value, $Res Function(StudentReport) then) =
      _$StudentReportCopyWithImpl<$Res, StudentReport>;
  @useResult
  $Res call(
      {String id,
      String assessmentId,
      String assessmentTitle,
      String studentId,
      String studentName,
      String rollNumber,
      int grade,
      String section,
      ReportHeader header,
      PerformanceOverview overview,
      List<SectionReport> sectionReports,
      List<ConceptReport> conceptReports,
      BloomReport bloomReport,
      CompetencyReport competencyReport,
      List<String> strengths,
      List<String> weaknesses,
      List<String> carelessErrors,
      List<ActionableRecommendation> recommendations,
      TeacherRemarks teacherRemarks,
      ParentSummary parentSummary,
      DateTime generatedAt,
      String generatedBy});

  $ReportHeaderCopyWith<$Res> get header;
  $PerformanceOverviewCopyWith<$Res> get overview;
  $BloomReportCopyWith<$Res> get bloomReport;
  $CompetencyReportCopyWith<$Res> get competencyReport;
  $TeacherRemarksCopyWith<$Res> get teacherRemarks;
  $ParentSummaryCopyWith<$Res> get parentSummary;
}

/// @nodoc
class _$StudentReportCopyWithImpl<$Res, $Val extends StudentReport>
    implements $StudentReportCopyWith<$Res> {
  _$StudentReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? assessmentId = null,
    Object? assessmentTitle = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? grade = null,
    Object? section = null,
    Object? header = null,
    Object? overview = null,
    Object? sectionReports = null,
    Object? conceptReports = null,
    Object? bloomReport = null,
    Object? competencyReport = null,
    Object? strengths = null,
    Object? weaknesses = null,
    Object? carelessErrors = null,
    Object? recommendations = null,
    Object? teacherRemarks = null,
    Object? parentSummary = null,
    Object? generatedAt = null,
    Object? generatedBy = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      rollNumber: null == rollNumber
          ? _value.rollNumber
          : rollNumber // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      section: null == section
          ? _value.section
          : section // ignore: cast_nullable_to_non_nullable
              as String,
      header: null == header
          ? _value.header
          : header // ignore: cast_nullable_to_non_nullable
              as ReportHeader,
      overview: null == overview
          ? _value.overview
          : overview // ignore: cast_nullable_to_non_nullable
              as PerformanceOverview,
      sectionReports: null == sectionReports
          ? _value.sectionReports
          : sectionReports // ignore: cast_nullable_to_non_nullable
              as List<SectionReport>,
      conceptReports: null == conceptReports
          ? _value.conceptReports
          : conceptReports // ignore: cast_nullable_to_non_nullable
              as List<ConceptReport>,
      bloomReport: null == bloomReport
          ? _value.bloomReport
          : bloomReport // ignore: cast_nullable_to_non_nullable
              as BloomReport,
      competencyReport: null == competencyReport
          ? _value.competencyReport
          : competencyReport // ignore: cast_nullable_to_non_nullable
              as CompetencyReport,
      strengths: null == strengths
          ? _value.strengths
          : strengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      weaknesses: null == weaknesses
          ? _value.weaknesses
          : weaknesses // ignore: cast_nullable_to_non_nullable
              as List<String>,
      carelessErrors: null == carelessErrors
          ? _value.carelessErrors
          : carelessErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      recommendations: null == recommendations
          ? _value.recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      teacherRemarks: null == teacherRemarks
          ? _value.teacherRemarks
          : teacherRemarks // ignore: cast_nullable_to_non_nullable
              as TeacherRemarks,
      parentSummary: null == parentSummary
          ? _value.parentSummary
          : parentSummary // ignore: cast_nullable_to_non_nullable
              as ParentSummary,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      generatedBy: null == generatedBy
          ? _value.generatedBy
          : generatedBy // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ReportHeaderCopyWith<$Res> get header {
    return $ReportHeaderCopyWith<$Res>(_value.header, (value) {
      return _then(_value.copyWith(header: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $PerformanceOverviewCopyWith<$Res> get overview {
    return $PerformanceOverviewCopyWith<$Res>(_value.overview, (value) {
      return _then(_value.copyWith(overview: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $BloomReportCopyWith<$Res> get bloomReport {
    return $BloomReportCopyWith<$Res>(_value.bloomReport, (value) {
      return _then(_value.copyWith(bloomReport: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $CompetencyReportCopyWith<$Res> get competencyReport {
    return $CompetencyReportCopyWith<$Res>(_value.competencyReport, (value) {
      return _then(_value.copyWith(competencyReport: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $TeacherRemarksCopyWith<$Res> get teacherRemarks {
    return $TeacherRemarksCopyWith<$Res>(_value.teacherRemarks, (value) {
      return _then(_value.copyWith(teacherRemarks: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ParentSummaryCopyWith<$Res> get parentSummary {
    return $ParentSummaryCopyWith<$Res>(_value.parentSummary, (value) {
      return _then(_value.copyWith(parentSummary: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$StudentReportImplCopyWith<$Res>
    implements $StudentReportCopyWith<$Res> {
  factory _$$StudentReportImplCopyWith(
          _$StudentReportImpl value, $Res Function(_$StudentReportImpl) then) =
      __$$StudentReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String assessmentId,
      String assessmentTitle,
      String studentId,
      String studentName,
      String rollNumber,
      int grade,
      String section,
      ReportHeader header,
      PerformanceOverview overview,
      List<SectionReport> sectionReports,
      List<ConceptReport> conceptReports,
      BloomReport bloomReport,
      CompetencyReport competencyReport,
      List<String> strengths,
      List<String> weaknesses,
      List<String> carelessErrors,
      List<ActionableRecommendation> recommendations,
      TeacherRemarks teacherRemarks,
      ParentSummary parentSummary,
      DateTime generatedAt,
      String generatedBy});

  @override
  $ReportHeaderCopyWith<$Res> get header;
  @override
  $PerformanceOverviewCopyWith<$Res> get overview;
  @override
  $BloomReportCopyWith<$Res> get bloomReport;
  @override
  $CompetencyReportCopyWith<$Res> get competencyReport;
  @override
  $TeacherRemarksCopyWith<$Res> get teacherRemarks;
  @override
  $ParentSummaryCopyWith<$Res> get parentSummary;
}

/// @nodoc
class __$$StudentReportImplCopyWithImpl<$Res>
    extends _$StudentReportCopyWithImpl<$Res, _$StudentReportImpl>
    implements _$$StudentReportImplCopyWith<$Res> {
  __$$StudentReportImplCopyWithImpl(
      _$StudentReportImpl _value, $Res Function(_$StudentReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? assessmentId = null,
    Object? assessmentTitle = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? grade = null,
    Object? section = null,
    Object? header = null,
    Object? overview = null,
    Object? sectionReports = null,
    Object? conceptReports = null,
    Object? bloomReport = null,
    Object? competencyReport = null,
    Object? strengths = null,
    Object? weaknesses = null,
    Object? carelessErrors = null,
    Object? recommendations = null,
    Object? teacherRemarks = null,
    Object? parentSummary = null,
    Object? generatedAt = null,
    Object? generatedBy = null,
  }) {
    return _then(_$StudentReportImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      rollNumber: null == rollNumber
          ? _value.rollNumber
          : rollNumber // ignore: cast_nullable_to_non_nullable
              as String,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as int,
      section: null == section
          ? _value.section
          : section // ignore: cast_nullable_to_non_nullable
              as String,
      header: null == header
          ? _value.header
          : header // ignore: cast_nullable_to_non_nullable
              as ReportHeader,
      overview: null == overview
          ? _value.overview
          : overview // ignore: cast_nullable_to_non_nullable
              as PerformanceOverview,
      sectionReports: null == sectionReports
          ? _value._sectionReports
          : sectionReports // ignore: cast_nullable_to_non_nullable
              as List<SectionReport>,
      conceptReports: null == conceptReports
          ? _value._conceptReports
          : conceptReports // ignore: cast_nullable_to_non_nullable
              as List<ConceptReport>,
      bloomReport: null == bloomReport
          ? _value.bloomReport
          : bloomReport // ignore: cast_nullable_to_non_nullable
              as BloomReport,
      competencyReport: null == competencyReport
          ? _value.competencyReport
          : competencyReport // ignore: cast_nullable_to_non_nullable
              as CompetencyReport,
      strengths: null == strengths
          ? _value._strengths
          : strengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      weaknesses: null == weaknesses
          ? _value._weaknesses
          : weaknesses // ignore: cast_nullable_to_non_nullable
              as List<String>,
      carelessErrors: null == carelessErrors
          ? _value._carelessErrors
          : carelessErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      recommendations: null == recommendations
          ? _value._recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      teacherRemarks: null == teacherRemarks
          ? _value.teacherRemarks
          : teacherRemarks // ignore: cast_nullable_to_non_nullable
              as TeacherRemarks,
      parentSummary: null == parentSummary
          ? _value.parentSummary
          : parentSummary // ignore: cast_nullable_to_non_nullable
              as ParentSummary,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      generatedBy: null == generatedBy
          ? _value.generatedBy
          : generatedBy // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StudentReportImpl implements _StudentReport {
  const _$StudentReportImpl(
      {required this.id,
      required this.assessmentId,
      required this.assessmentTitle,
      required this.studentId,
      required this.studentName,
      required this.rollNumber,
      required this.grade,
      required this.section,
      required this.header,
      required this.overview,
      required final List<SectionReport> sectionReports,
      required final List<ConceptReport> conceptReports,
      required this.bloomReport,
      required this.competencyReport,
      required final List<String> strengths,
      required final List<String> weaknesses,
      required final List<String> carelessErrors,
      required final List<ActionableRecommendation> recommendations,
      required this.teacherRemarks,
      required this.parentSummary,
      required this.generatedAt,
      required this.generatedBy})
      : _sectionReports = sectionReports,
        _conceptReports = conceptReports,
        _strengths = strengths,
        _weaknesses = weaknesses,
        _carelessErrors = carelessErrors,
        _recommendations = recommendations;

  factory _$StudentReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$StudentReportImplFromJson(json);

  @override
  final String id;
  @override
  final String assessmentId;
  @override
  final String assessmentTitle;
  @override
  final String studentId;
  @override
  final String studentName;
  @override
  final String rollNumber;
  @override
  final int grade;
  @override
  final String section;
  @override
  final ReportHeader header;
  @override
  final PerformanceOverview overview;
  final List<SectionReport> _sectionReports;
  @override
  List<SectionReport> get sectionReports {
    if (_sectionReports is EqualUnmodifiableListView) return _sectionReports;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_sectionReports);
  }

  final List<ConceptReport> _conceptReports;
  @override
  List<ConceptReport> get conceptReports {
    if (_conceptReports is EqualUnmodifiableListView) return _conceptReports;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_conceptReports);
  }

  @override
  final BloomReport bloomReport;
  @override
  final CompetencyReport competencyReport;
  final List<String> _strengths;
  @override
  List<String> get strengths {
    if (_strengths is EqualUnmodifiableListView) return _strengths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_strengths);
  }

  final List<String> _weaknesses;
  @override
  List<String> get weaknesses {
    if (_weaknesses is EqualUnmodifiableListView) return _weaknesses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_weaknesses);
  }

  final List<String> _carelessErrors;
  @override
  List<String> get carelessErrors {
    if (_carelessErrors is EqualUnmodifiableListView) return _carelessErrors;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_carelessErrors);
  }

  final List<ActionableRecommendation> _recommendations;
  @override
  List<ActionableRecommendation> get recommendations {
    if (_recommendations is EqualUnmodifiableListView) return _recommendations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendations);
  }

  @override
  final TeacherRemarks teacherRemarks;
  @override
  final ParentSummary parentSummary;
  @override
  final DateTime generatedAt;
  @override
  final String generatedBy;

  @override
  String toString() {
    return 'StudentReport(id: $id, assessmentId: $assessmentId, assessmentTitle: $assessmentTitle, studentId: $studentId, studentName: $studentName, rollNumber: $rollNumber, grade: $grade, section: $section, header: $header, overview: $overview, sectionReports: $sectionReports, conceptReports: $conceptReports, bloomReport: $bloomReport, competencyReport: $competencyReport, strengths: $strengths, weaknesses: $weaknesses, carelessErrors: $carelessErrors, recommendations: $recommendations, teacherRemarks: $teacherRemarks, parentSummary: $parentSummary, generatedAt: $generatedAt, generatedBy: $generatedBy)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StudentReportImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.assessmentTitle, assessmentTitle) ||
                other.assessmentTitle == assessmentTitle) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.studentName, studentName) ||
                other.studentName == studentName) &&
            (identical(other.rollNumber, rollNumber) ||
                other.rollNumber == rollNumber) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.section, section) || other.section == section) &&
            (identical(other.header, header) || other.header == header) &&
            (identical(other.overview, overview) ||
                other.overview == overview) &&
            const DeepCollectionEquality()
                .equals(other._sectionReports, _sectionReports) &&
            const DeepCollectionEquality()
                .equals(other._conceptReports, _conceptReports) &&
            (identical(other.bloomReport, bloomReport) ||
                other.bloomReport == bloomReport) &&
            (identical(other.competencyReport, competencyReport) ||
                other.competencyReport == competencyReport) &&
            const DeepCollectionEquality()
                .equals(other._strengths, _strengths) &&
            const DeepCollectionEquality()
                .equals(other._weaknesses, _weaknesses) &&
            const DeepCollectionEquality()
                .equals(other._carelessErrors, _carelessErrors) &&
            const DeepCollectionEquality()
                .equals(other._recommendations, _recommendations) &&
            (identical(other.teacherRemarks, teacherRemarks) ||
                other.teacherRemarks == teacherRemarks) &&
            (identical(other.parentSummary, parentSummary) ||
                other.parentSummary == parentSummary) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt) &&
            (identical(other.generatedBy, generatedBy) ||
                other.generatedBy == generatedBy));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        id,
        assessmentId,
        assessmentTitle,
        studentId,
        studentName,
        rollNumber,
        grade,
        section,
        header,
        overview,
        const DeepCollectionEquality().hash(_sectionReports),
        const DeepCollectionEquality().hash(_conceptReports),
        bloomReport,
        competencyReport,
        const DeepCollectionEquality().hash(_strengths),
        const DeepCollectionEquality().hash(_weaknesses),
        const DeepCollectionEquality().hash(_carelessErrors),
        const DeepCollectionEquality().hash(_recommendations),
        teacherRemarks,
        parentSummary,
        generatedAt,
        generatedBy
      ]);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$StudentReportImplCopyWith<_$StudentReportImpl> get copyWith =>
      __$$StudentReportImplCopyWithImpl<_$StudentReportImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StudentReportImplToJson(
      this,
    );
  }
}

abstract class _StudentReport implements StudentReport {
  const factory _StudentReport(
      {required final String id,
      required final String assessmentId,
      required final String assessmentTitle,
      required final String studentId,
      required final String studentName,
      required final String rollNumber,
      required final int grade,
      required final String section,
      required final ReportHeader header,
      required final PerformanceOverview overview,
      required final List<SectionReport> sectionReports,
      required final List<ConceptReport> conceptReports,
      required final BloomReport bloomReport,
      required final CompetencyReport competencyReport,
      required final List<String> strengths,
      required final List<String> weaknesses,
      required final List<String> carelessErrors,
      required final List<ActionableRecommendation> recommendations,
      required final TeacherRemarks teacherRemarks,
      required final ParentSummary parentSummary,
      required final DateTime generatedAt,
      required final String generatedBy}) = _$StudentReportImpl;

  factory _StudentReport.fromJson(Map<String, dynamic> json) =
      _$StudentReportImpl.fromJson;

  @override
  String get id;
  @override
  String get assessmentId;
  @override
  String get assessmentTitle;
  @override
  String get studentId;
  @override
  String get studentName;
  @override
  String get rollNumber;
  @override
  int get grade;
  @override
  String get section;
  @override
  ReportHeader get header;
  @override
  PerformanceOverview get overview;
  @override
  List<SectionReport> get sectionReports;
  @override
  List<ConceptReport> get conceptReports;
  @override
  BloomReport get bloomReport;
  @override
  CompetencyReport get competencyReport;
  @override
  List<String> get strengths;
  @override
  List<String> get weaknesses;
  @override
  List<String> get carelessErrors;
  @override
  List<ActionableRecommendation> get recommendations;
  @override
  TeacherRemarks get teacherRemarks;
  @override
  ParentSummary get parentSummary;
  @override
  DateTime get generatedAt;
  @override
  String get generatedBy;
  @override
  @JsonKey(ignore: true)
  _$$StudentReportImplCopyWith<_$StudentReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ReportHeader _$ReportHeaderFromJson(Map<String, dynamic> json) {
  return _ReportHeader.fromJson(json);
}

/// @nodoc
mixin _$ReportHeader {
  String get schoolName => throw _privateConstructorUsedError;
  String get schoolLogoUrl => throw _privateConstructorUsedError;
  String get academicYear => throw _privateConstructorUsedError;
  String get term => throw _privateConstructorUsedError;
  DateTime get assessmentDate => throw _privateConstructorUsedError;
  DateTime get reportDate => throw _privateConstructorUsedError;
  String get principalName => throw _privateConstructorUsedError;
  String get teacherName => throw _privateConstructorUsedError;
  String get className => throw _privateConstructorUsedError;
  String get section => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ReportHeaderCopyWith<ReportHeader> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ReportHeaderCopyWith<$Res> {
  factory $ReportHeaderCopyWith(
          ReportHeader value, $Res Function(ReportHeader) then) =
      _$ReportHeaderCopyWithImpl<$Res, ReportHeader>;
  @useResult
  $Res call(
      {String schoolName,
      String schoolLogoUrl,
      String academicYear,
      String term,
      DateTime assessmentDate,
      DateTime reportDate,
      String principalName,
      String teacherName,
      String className,
      String section});
}

/// @nodoc
class _$ReportHeaderCopyWithImpl<$Res, $Val extends ReportHeader>
    implements $ReportHeaderCopyWith<$Res> {
  _$ReportHeaderCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? schoolName = null,
    Object? schoolLogoUrl = null,
    Object? academicYear = null,
    Object? term = null,
    Object? assessmentDate = null,
    Object? reportDate = null,
    Object? principalName = null,
    Object? teacherName = null,
    Object? className = null,
    Object? section = null,
  }) {
    return _then(_value.copyWith(
      schoolName: null == schoolName
          ? _value.schoolName
          : schoolName // ignore: cast_nullable_to_non_nullable
              as String,
      schoolLogoUrl: null == schoolLogoUrl
          ? _value.schoolLogoUrl
          : schoolLogoUrl // ignore: cast_nullable_to_non_nullable
              as String,
      academicYear: null == academicYear
          ? _value.academicYear
          : academicYear // ignore: cast_nullable_to_non_nullable
              as String,
      term: null == term
          ? _value.term
          : term // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentDate: null == assessmentDate
          ? _value.assessmentDate
          : assessmentDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      reportDate: null == reportDate
          ? _value.reportDate
          : reportDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      principalName: null == principalName
          ? _value.principalName
          : principalName // ignore: cast_nullable_to_non_nullable
              as String,
      teacherName: null == teacherName
          ? _value.teacherName
          : teacherName // ignore: cast_nullable_to_non_nullable
              as String,
      className: null == className
          ? _value.className
          : className // ignore: cast_nullable_to_non_nullable
              as String,
      section: null == section
          ? _value.section
          : section // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ReportHeaderImplCopyWith<$Res>
    implements $ReportHeaderCopyWith<$Res> {
  factory _$$ReportHeaderImplCopyWith(
          _$ReportHeaderImpl value, $Res Function(_$ReportHeaderImpl) then) =
      __$$ReportHeaderImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String schoolName,
      String schoolLogoUrl,
      String academicYear,
      String term,
      DateTime assessmentDate,
      DateTime reportDate,
      String principalName,
      String teacherName,
      String className,
      String section});
}

/// @nodoc
class __$$ReportHeaderImplCopyWithImpl<$Res>
    extends _$ReportHeaderCopyWithImpl<$Res, _$ReportHeaderImpl>
    implements _$$ReportHeaderImplCopyWith<$Res> {
  __$$ReportHeaderImplCopyWithImpl(
      _$ReportHeaderImpl _value, $Res Function(_$ReportHeaderImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? schoolName = null,
    Object? schoolLogoUrl = null,
    Object? academicYear = null,
    Object? term = null,
    Object? assessmentDate = null,
    Object? reportDate = null,
    Object? principalName = null,
    Object? teacherName = null,
    Object? className = null,
    Object? section = null,
  }) {
    return _then(_$ReportHeaderImpl(
      schoolName: null == schoolName
          ? _value.schoolName
          : schoolName // ignore: cast_nullable_to_non_nullable
              as String,
      schoolLogoUrl: null == schoolLogoUrl
          ? _value.schoolLogoUrl
          : schoolLogoUrl // ignore: cast_nullable_to_non_nullable
              as String,
      academicYear: null == academicYear
          ? _value.academicYear
          : academicYear // ignore: cast_nullable_to_non_nullable
              as String,
      term: null == term
          ? _value.term
          : term // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentDate: null == assessmentDate
          ? _value.assessmentDate
          : assessmentDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      reportDate: null == reportDate
          ? _value.reportDate
          : reportDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      principalName: null == principalName
          ? _value.principalName
          : principalName // ignore: cast_nullable_to_non_nullable
              as String,
      teacherName: null == teacherName
          ? _value.teacherName
          : teacherName // ignore: cast_nullable_to_non_nullable
              as String,
      className: null == className
          ? _value.className
          : className // ignore: cast_nullable_to_non_nullable
              as String,
      section: null == section
          ? _value.section
          : section // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ReportHeaderImpl implements _ReportHeader {
  const _$ReportHeaderImpl(
      {required this.schoolName,
      required this.schoolLogoUrl,
      required this.academicYear,
      required this.term,
      required this.assessmentDate,
      required this.reportDate,
      required this.principalName,
      required this.teacherName,
      required this.className,
      required this.section});

  factory _$ReportHeaderImpl.fromJson(Map<String, dynamic> json) =>
      _$$ReportHeaderImplFromJson(json);

  @override
  final String schoolName;
  @override
  final String schoolLogoUrl;
  @override
  final String academicYear;
  @override
  final String term;
  @override
  final DateTime assessmentDate;
  @override
  final DateTime reportDate;
  @override
  final String principalName;
  @override
  final String teacherName;
  @override
  final String className;
  @override
  final String section;

  @override
  String toString() {
    return 'ReportHeader(schoolName: $schoolName, schoolLogoUrl: $schoolLogoUrl, academicYear: $academicYear, term: $term, assessmentDate: $assessmentDate, reportDate: $reportDate, principalName: $principalName, teacherName: $teacherName, className: $className, section: $section)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ReportHeaderImpl &&
            (identical(other.schoolName, schoolName) ||
                other.schoolName == schoolName) &&
            (identical(other.schoolLogoUrl, schoolLogoUrl) ||
                other.schoolLogoUrl == schoolLogoUrl) &&
            (identical(other.academicYear, academicYear) ||
                other.academicYear == academicYear) &&
            (identical(other.term, term) || other.term == term) &&
            (identical(other.assessmentDate, assessmentDate) ||
                other.assessmentDate == assessmentDate) &&
            (identical(other.reportDate, reportDate) ||
                other.reportDate == reportDate) &&
            (identical(other.principalName, principalName) ||
                other.principalName == principalName) &&
            (identical(other.teacherName, teacherName) ||
                other.teacherName == teacherName) &&
            (identical(other.className, className) ||
                other.className == className) &&
            (identical(other.section, section) || other.section == section));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      schoolName,
      schoolLogoUrl,
      academicYear,
      term,
      assessmentDate,
      reportDate,
      principalName,
      teacherName,
      className,
      section);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ReportHeaderImplCopyWith<_$ReportHeaderImpl> get copyWith =>
      __$$ReportHeaderImplCopyWithImpl<_$ReportHeaderImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ReportHeaderImplToJson(
      this,
    );
  }
}

abstract class _ReportHeader implements ReportHeader {
  const factory _ReportHeader(
      {required final String schoolName,
      required final String schoolLogoUrl,
      required final String academicYear,
      required final String term,
      required final DateTime assessmentDate,
      required final DateTime reportDate,
      required final String principalName,
      required final String teacherName,
      required final String className,
      required final String section}) = _$ReportHeaderImpl;

  factory _ReportHeader.fromJson(Map<String, dynamic> json) =
      _$ReportHeaderImpl.fromJson;

  @override
  String get schoolName;
  @override
  String get schoolLogoUrl;
  @override
  String get academicYear;
  @override
  String get term;
  @override
  DateTime get assessmentDate;
  @override
  DateTime get reportDate;
  @override
  String get principalName;
  @override
  String get teacherName;
  @override
  String get className;
  @override
  String get section;
  @override
  @JsonKey(ignore: true)
  _$$ReportHeaderImplCopyWith<_$ReportHeaderImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PerformanceOverview _$PerformanceOverviewFromJson(Map<String, dynamic> json) {
  return _PerformanceOverview.fromJson(json);
}

/// @nodoc
mixin _$PerformanceOverview {
  int get totalScore => throw _privateConstructorUsedError;
  int get maxScore => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  String get grade => throw _privateConstructorUsedError;
  int get classRank => throw _privateConstructorUsedError;
  int get totalStudents => throw _privateConstructorUsedError;
  double get percentile => throw _privateConstructorUsedError;
  String get performanceLevel => throw _privateConstructorUsedError;
  Map<String, SectionScore> get sectionScores =>
      throw _privateConstructorUsedError;
  double get classAverage => throw _privateConstructorUsedError;
  double get classMedian => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PerformanceOverviewCopyWith<PerformanceOverview> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PerformanceOverviewCopyWith<$Res> {
  factory $PerformanceOverviewCopyWith(
          PerformanceOverview value, $Res Function(PerformanceOverview) then) =
      _$PerformanceOverviewCopyWithImpl<$Res, PerformanceOverview>;
  @useResult
  $Res call(
      {int totalScore,
      int maxScore,
      double percentage,
      String grade,
      int classRank,
      int totalStudents,
      double percentile,
      String performanceLevel,
      Map<String, SectionScore> sectionScores,
      double classAverage,
      double classMedian});
}

/// @nodoc
class _$PerformanceOverviewCopyWithImpl<$Res, $Val extends PerformanceOverview>
    implements $PerformanceOverviewCopyWith<$Res> {
  _$PerformanceOverviewCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalScore = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? grade = null,
    Object? classRank = null,
    Object? totalStudents = null,
    Object? percentile = null,
    Object? performanceLevel = null,
    Object? sectionScores = null,
    Object? classAverage = null,
    Object? classMedian = null,
  }) {
    return _then(_value.copyWith(
      totalScore: null == totalScore
          ? _value.totalScore
          : totalScore // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      classRank: null == classRank
          ? _value.classRank
          : classRank // ignore: cast_nullable_to_non_nullable
              as int,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      percentile: null == percentile
          ? _value.percentile
          : percentile // ignore: cast_nullable_to_non_nullable
              as double,
      performanceLevel: null == performanceLevel
          ? _value.performanceLevel
          : performanceLevel // ignore: cast_nullable_to_non_nullable
              as String,
      sectionScores: null == sectionScores
          ? _value.sectionScores
          : sectionScores // ignore: cast_nullable_to_non_nullable
              as Map<String, SectionScore>,
      classAverage: null == classAverage
          ? _value.classAverage
          : classAverage // ignore: cast_nullable_to_non_nullable
              as double,
      classMedian: null == classMedian
          ? _value.classMedian
          : classMedian // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PerformanceOverviewImplCopyWith<$Res>
    implements $PerformanceOverviewCopyWith<$Res> {
  factory _$$PerformanceOverviewImplCopyWith(_$PerformanceOverviewImpl value,
          $Res Function(_$PerformanceOverviewImpl) then) =
      __$$PerformanceOverviewImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int totalScore,
      int maxScore,
      double percentage,
      String grade,
      int classRank,
      int totalStudents,
      double percentile,
      String performanceLevel,
      Map<String, SectionScore> sectionScores,
      double classAverage,
      double classMedian});
}

/// @nodoc
class __$$PerformanceOverviewImplCopyWithImpl<$Res>
    extends _$PerformanceOverviewCopyWithImpl<$Res, _$PerformanceOverviewImpl>
    implements _$$PerformanceOverviewImplCopyWith<$Res> {
  __$$PerformanceOverviewImplCopyWithImpl(_$PerformanceOverviewImpl _value,
      $Res Function(_$PerformanceOverviewImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalScore = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? grade = null,
    Object? classRank = null,
    Object? totalStudents = null,
    Object? percentile = null,
    Object? performanceLevel = null,
    Object? sectionScores = null,
    Object? classAverage = null,
    Object? classMedian = null,
  }) {
    return _then(_$PerformanceOverviewImpl(
      totalScore: null == totalScore
          ? _value.totalScore
          : totalScore // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      classRank: null == classRank
          ? _value.classRank
          : classRank // ignore: cast_nullable_to_non_nullable
              as int,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      percentile: null == percentile
          ? _value.percentile
          : percentile // ignore: cast_nullable_to_non_nullable
              as double,
      performanceLevel: null == performanceLevel
          ? _value.performanceLevel
          : performanceLevel // ignore: cast_nullable_to_non_nullable
              as String,
      sectionScores: null == sectionScores
          ? _value._sectionScores
          : sectionScores // ignore: cast_nullable_to_non_nullable
              as Map<String, SectionScore>,
      classAverage: null == classAverage
          ? _value.classAverage
          : classAverage // ignore: cast_nullable_to_non_nullable
              as double,
      classMedian: null == classMedian
          ? _value.classMedian
          : classMedian // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PerformanceOverviewImpl implements _PerformanceOverview {
  const _$PerformanceOverviewImpl(
      {required this.totalScore,
      required this.maxScore,
      required this.percentage,
      required this.grade,
      required this.classRank,
      required this.totalStudents,
      required this.percentile,
      required this.performanceLevel,
      required final Map<String, SectionScore> sectionScores,
      required this.classAverage,
      required this.classMedian})
      : _sectionScores = sectionScores;

  factory _$PerformanceOverviewImpl.fromJson(Map<String, dynamic> json) =>
      _$$PerformanceOverviewImplFromJson(json);

  @override
  final int totalScore;
  @override
  final int maxScore;
  @override
  final double percentage;
  @override
  final String grade;
  @override
  final int classRank;
  @override
  final int totalStudents;
  @override
  final double percentile;
  @override
  final String performanceLevel;
  final Map<String, SectionScore> _sectionScores;
  @override
  Map<String, SectionScore> get sectionScores {
    if (_sectionScores is EqualUnmodifiableMapView) return _sectionScores;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_sectionScores);
  }

  @override
  final double classAverage;
  @override
  final double classMedian;

  @override
  String toString() {
    return 'PerformanceOverview(totalScore: $totalScore, maxScore: $maxScore, percentage: $percentage, grade: $grade, classRank: $classRank, totalStudents: $totalStudents, percentile: $percentile, performanceLevel: $performanceLevel, sectionScores: $sectionScores, classAverage: $classAverage, classMedian: $classMedian)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PerformanceOverviewImpl &&
            (identical(other.totalScore, totalScore) ||
                other.totalScore == totalScore) &&
            (identical(other.maxScore, maxScore) ||
                other.maxScore == maxScore) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.classRank, classRank) ||
                other.classRank == classRank) &&
            (identical(other.totalStudents, totalStudents) ||
                other.totalStudents == totalStudents) &&
            (identical(other.percentile, percentile) ||
                other.percentile == percentile) &&
            (identical(other.performanceLevel, performanceLevel) ||
                other.performanceLevel == performanceLevel) &&
            const DeepCollectionEquality()
                .equals(other._sectionScores, _sectionScores) &&
            (identical(other.classAverage, classAverage) ||
                other.classAverage == classAverage) &&
            (identical(other.classMedian, classMedian) ||
                other.classMedian == classMedian));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalScore,
      maxScore,
      percentage,
      grade,
      classRank,
      totalStudents,
      percentile,
      performanceLevel,
      const DeepCollectionEquality().hash(_sectionScores),
      classAverage,
      classMedian);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PerformanceOverviewImplCopyWith<_$PerformanceOverviewImpl> get copyWith =>
      __$$PerformanceOverviewImplCopyWithImpl<_$PerformanceOverviewImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PerformanceOverviewImplToJson(
      this,
    );
  }
}

abstract class _PerformanceOverview implements PerformanceOverview {
  const factory _PerformanceOverview(
      {required final int totalScore,
      required final int maxScore,
      required final double percentage,
      required final String grade,
      required final int classRank,
      required final int totalStudents,
      required final double percentile,
      required final String performanceLevel,
      required final Map<String, SectionScore> sectionScores,
      required final double classAverage,
      required final double classMedian}) = _$PerformanceOverviewImpl;

  factory _PerformanceOverview.fromJson(Map<String, dynamic> json) =
      _$PerformanceOverviewImpl.fromJson;

  @override
  int get totalScore;
  @override
  int get maxScore;
  @override
  double get percentage;
  @override
  String get grade;
  @override
  int get classRank;
  @override
  int get totalStudents;
  @override
  double get percentile;
  @override
  String get performanceLevel;
  @override
  Map<String, SectionScore> get sectionScores;
  @override
  double get classAverage;
  @override
  double get classMedian;
  @override
  @JsonKey(ignore: true)
  _$$PerformanceOverviewImplCopyWith<_$PerformanceOverviewImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SectionReport _$SectionReportFromJson(Map<String, dynamic> json) {
  return _SectionReport.fromJson(json);
}

/// @nodoc
mixin _$SectionReport {
  String get sectionId => throw _privateConstructorUsedError;
  String get sectionLabel => throw _privateConstructorUsedError;
  String get sectionName => throw _privateConstructorUsedError;
  int get score => throw _privateConstructorUsedError;
  int get maxScore => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  int get questionsAttempted => throw _privateConstructorUsedError;
  int get questionsCorrect => throw _privateConstructorUsedError;
  int get questionsPartial => throw _privateConstructorUsedError;
  List<QuestionReport> get questions => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SectionReportCopyWith<SectionReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SectionReportCopyWith<$Res> {
  factory $SectionReportCopyWith(
          SectionReport value, $Res Function(SectionReport) then) =
      _$SectionReportCopyWithImpl<$Res, SectionReport>;
  @useResult
  $Res call(
      {String sectionId,
      String sectionLabel,
      String sectionName,
      int score,
      int maxScore,
      double percentage,
      int questionsAttempted,
      int questionsCorrect,
      int questionsPartial,
      List<QuestionReport> questions});
}

/// @nodoc
class _$SectionReportCopyWithImpl<$Res, $Val extends SectionReport>
    implements $SectionReportCopyWith<$Res> {
  _$SectionReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sectionId = null,
    Object? sectionLabel = null,
    Object? sectionName = null,
    Object? score = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? questionsAttempted = null,
    Object? questionsCorrect = null,
    Object? questionsPartial = null,
    Object? questions = null,
  }) {
    return _then(_value.copyWith(
      sectionId: null == sectionId
          ? _value.sectionId
          : sectionId // ignore: cast_nullable_to_non_nullable
              as String,
      sectionLabel: null == sectionLabel
          ? _value.sectionLabel
          : sectionLabel // ignore: cast_nullable_to_non_nullable
              as String,
      sectionName: null == sectionName
          ? _value.sectionName
          : sectionName // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      questionsCorrect: null == questionsCorrect
          ? _value.questionsCorrect
          : questionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      questionsPartial: null == questionsPartial
          ? _value.questionsPartial
          : questionsPartial // ignore: cast_nullable_to_non_nullable
              as int,
      questions: null == questions
          ? _value.questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<QuestionReport>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SectionReportImplCopyWith<$Res>
    implements $SectionReportCopyWith<$Res> {
  factory _$$SectionReportImplCopyWith(
          _$SectionReportImpl value, $Res Function(_$SectionReportImpl) then) =
      __$$SectionReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String sectionId,
      String sectionLabel,
      String sectionName,
      int score,
      int maxScore,
      double percentage,
      int questionsAttempted,
      int questionsCorrect,
      int questionsPartial,
      List<QuestionReport> questions});
}

/// @nodoc
class __$$SectionReportImplCopyWithImpl<$Res>
    extends _$SectionReportCopyWithImpl<$Res, _$SectionReportImpl>
    implements _$$SectionReportImplCopyWith<$Res> {
  __$$SectionReportImplCopyWithImpl(
      _$SectionReportImpl _value, $Res Function(_$SectionReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sectionId = null,
    Object? sectionLabel = null,
    Object? sectionName = null,
    Object? score = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? questionsAttempted = null,
    Object? questionsCorrect = null,
    Object? questionsPartial = null,
    Object? questions = null,
  }) {
    return _then(_$SectionReportImpl(
      sectionId: null == sectionId
          ? _value.sectionId
          : sectionId // ignore: cast_nullable_to_non_nullable
              as String,
      sectionLabel: null == sectionLabel
          ? _value.sectionLabel
          : sectionLabel // ignore: cast_nullable_to_non_nullable
              as String,
      sectionName: null == sectionName
          ? _value.sectionName
          : sectionName // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      questionsCorrect: null == questionsCorrect
          ? _value.questionsCorrect
          : questionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      questionsPartial: null == questionsPartial
          ? _value.questionsPartial
          : questionsPartial // ignore: cast_nullable_to_non_nullable
              as int,
      questions: null == questions
          ? _value._questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<QuestionReport>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SectionReportImpl implements _SectionReport {
  const _$SectionReportImpl(
      {required this.sectionId,
      required this.sectionLabel,
      required this.sectionName,
      required this.score,
      required this.maxScore,
      required this.percentage,
      required this.questionsAttempted,
      required this.questionsCorrect,
      required this.questionsPartial,
      required final List<QuestionReport> questions})
      : _questions = questions;

  factory _$SectionReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$SectionReportImplFromJson(json);

  @override
  final String sectionId;
  @override
  final String sectionLabel;
  @override
  final String sectionName;
  @override
  final int score;
  @override
  final int maxScore;
  @override
  final double percentage;
  @override
  final int questionsAttempted;
  @override
  final int questionsCorrect;
  @override
  final int questionsPartial;
  final List<QuestionReport> _questions;
  @override
  List<QuestionReport> get questions {
    if (_questions is EqualUnmodifiableListView) return _questions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questions);
  }

  @override
  String toString() {
    return 'SectionReport(sectionId: $sectionId, sectionLabel: $sectionLabel, sectionName: $sectionName, score: $score, maxScore: $maxScore, percentage: $percentage, questionsAttempted: $questionsAttempted, questionsCorrect: $questionsCorrect, questionsPartial: $questionsPartial, questions: $questions)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SectionReportImpl &&
            (identical(other.sectionId, sectionId) ||
                other.sectionId == sectionId) &&
            (identical(other.sectionLabel, sectionLabel) ||
                other.sectionLabel == sectionLabel) &&
            (identical(other.sectionName, sectionName) ||
                other.sectionName == sectionName) &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.maxScore, maxScore) ||
                other.maxScore == maxScore) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.questionsAttempted, questionsAttempted) ||
                other.questionsAttempted == questionsAttempted) &&
            (identical(other.questionsCorrect, questionsCorrect) ||
                other.questionsCorrect == questionsCorrect) &&
            (identical(other.questionsPartial, questionsPartial) ||
                other.questionsPartial == questionsPartial) &&
            const DeepCollectionEquality()
                .equals(other._questions, _questions));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      sectionId,
      sectionLabel,
      sectionName,
      score,
      maxScore,
      percentage,
      questionsAttempted,
      questionsCorrect,
      questionsPartial,
      const DeepCollectionEquality().hash(_questions));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SectionReportImplCopyWith<_$SectionReportImpl> get copyWith =>
      __$$SectionReportImplCopyWithImpl<_$SectionReportImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SectionReportImplToJson(
      this,
    );
  }
}

abstract class _SectionReport implements SectionReport {
  const factory _SectionReport(
      {required final String sectionId,
      required final String sectionLabel,
      required final String sectionName,
      required final int score,
      required final int maxScore,
      required final double percentage,
      required final int questionsAttempted,
      required final int questionsCorrect,
      required final int questionsPartial,
      required final List<QuestionReport> questions}) = _$SectionReportImpl;

  factory _SectionReport.fromJson(Map<String, dynamic> json) =
      _$SectionReportImpl.fromJson;

  @override
  String get sectionId;
  @override
  String get sectionLabel;
  @override
  String get sectionName;
  @override
  int get score;
  @override
  int get maxScore;
  @override
  double get percentage;
  @override
  int get questionsAttempted;
  @override
  int get questionsCorrect;
  @override
  int get questionsPartial;
  @override
  List<QuestionReport> get questions;
  @override
  @JsonKey(ignore: true)
  _$$SectionReportImplCopyWith<_$SectionReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionReport _$QuestionReportFromJson(Map<String, dynamic> json) {
  return _QuestionReport.fromJson(json);
}

/// @nodoc
mixin _$QuestionReport {
  String get questionId => throw _privateConstructorUsedError;
  int get questionNumber => throw _privateConstructorUsedError;
  String get questionText => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  int get awardedMarks => throw _privateConstructorUsedError;
  String get studentAnswer => throw _privateConstructorUsedError;
  String get modelAnswer => throw _privateConstructorUsedError;
  String get verdict => throw _privateConstructorUsedError;
  String get feedback => throw _privateConstructorUsedError;
  String get conceptTag => throw _privateConstructorUsedError;
  String get bloomLevel => throw _privateConstructorUsedError;
  String get difficulty => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionReportCopyWith<QuestionReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionReportCopyWith<$Res> {
  factory $QuestionReportCopyWith(
          QuestionReport value, $Res Function(QuestionReport) then) =
      _$QuestionReportCopyWithImpl<$Res, QuestionReport>;
  @useResult
  $Res call(
      {String questionId,
      int questionNumber,
      String questionText,
      int maxMarks,
      int awardedMarks,
      String studentAnswer,
      String modelAnswer,
      String verdict,
      String feedback,
      String conceptTag,
      String bloomLevel,
      String difficulty});
}

/// @nodoc
class _$QuestionReportCopyWithImpl<$Res, $Val extends QuestionReport>
    implements $QuestionReportCopyWith<$Res> {
  _$QuestionReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? questionNumber = null,
    Object? questionText = null,
    Object? maxMarks = null,
    Object? awardedMarks = null,
    Object? studentAnswer = null,
    Object? modelAnswer = null,
    Object? verdict = null,
    Object? feedback = null,
    Object? conceptTag = null,
    Object? bloomLevel = null,
    Object? difficulty = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      questionText: null == questionText
          ? _value.questionText
          : questionText // ignore: cast_nullable_to_non_nullable
              as String,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      awardedMarks: null == awardedMarks
          ? _value.awardedMarks
          : awardedMarks // ignore: cast_nullable_to_non_nullable
              as int,
      studentAnswer: null == studentAnswer
          ? _value.studentAnswer
          : studentAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      modelAnswer: null == modelAnswer
          ? _value.modelAnswer
          : modelAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      verdict: null == verdict
          ? _value.verdict
          : verdict // ignore: cast_nullable_to_non_nullable
              as String,
      feedback: null == feedback
          ? _value.feedback
          : feedback // ignore: cast_nullable_to_non_nullable
              as String,
      conceptTag: null == conceptTag
          ? _value.conceptTag
          : conceptTag // ignore: cast_nullable_to_non_nullable
              as String,
      bloomLevel: null == bloomLevel
          ? _value.bloomLevel
          : bloomLevel // ignore: cast_nullable_to_non_nullable
              as String,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuestionReportImplCopyWith<$Res>
    implements $QuestionReportCopyWith<$Res> {
  factory _$$QuestionReportImplCopyWith(_$QuestionReportImpl value,
          $Res Function(_$QuestionReportImpl) then) =
      __$$QuestionReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      int questionNumber,
      String questionText,
      int maxMarks,
      int awardedMarks,
      String studentAnswer,
      String modelAnswer,
      String verdict,
      String feedback,
      String conceptTag,
      String bloomLevel,
      String difficulty});
}

/// @nodoc
class __$$QuestionReportImplCopyWithImpl<$Res>
    extends _$QuestionReportCopyWithImpl<$Res, _$QuestionReportImpl>
    implements _$$QuestionReportImplCopyWith<$Res> {
  __$$QuestionReportImplCopyWithImpl(
      _$QuestionReportImpl _value, $Res Function(_$QuestionReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? questionNumber = null,
    Object? questionText = null,
    Object? maxMarks = null,
    Object? awardedMarks = null,
    Object? studentAnswer = null,
    Object? modelAnswer = null,
    Object? verdict = null,
    Object? feedback = null,
    Object? conceptTag = null,
    Object? bloomLevel = null,
    Object? difficulty = null,
  }) {
    return _then(_$QuestionReportImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      questionText: null == questionText
          ? _value.questionText
          : questionText // ignore: cast_nullable_to_non_nullable
              as String,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      awardedMarks: null == awardedMarks
          ? _value.awardedMarks
          : awardedMarks // ignore: cast_nullable_to_non_nullable
              as int,
      studentAnswer: null == studentAnswer
          ? _value.studentAnswer
          : studentAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      modelAnswer: null == modelAnswer
          ? _value.modelAnswer
          : modelAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      verdict: null == verdict
          ? _value.verdict
          : verdict // ignore: cast_nullable_to_non_nullable
              as String,
      feedback: null == feedback
          ? _value.feedback
          : feedback // ignore: cast_nullable_to_non_nullable
              as String,
      conceptTag: null == conceptTag
          ? _value.conceptTag
          : conceptTag // ignore: cast_nullable_to_non_nullable
              as String,
      bloomLevel: null == bloomLevel
          ? _value.bloomLevel
          : bloomLevel // ignore: cast_nullable_to_non_nullable
              as String,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionReportImpl implements _QuestionReport {
  const _$QuestionReportImpl(
      {required this.questionId,
      required this.questionNumber,
      required this.questionText,
      required this.maxMarks,
      required this.awardedMarks,
      required this.studentAnswer,
      required this.modelAnswer,
      required this.verdict,
      required this.feedback,
      required this.conceptTag,
      required this.bloomLevel,
      required this.difficulty});

  factory _$QuestionReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionReportImplFromJson(json);

  @override
  final String questionId;
  @override
  final int questionNumber;
  @override
  final String questionText;
  @override
  final int maxMarks;
  @override
  final int awardedMarks;
  @override
  final String studentAnswer;
  @override
  final String modelAnswer;
  @override
  final String verdict;
  @override
  final String feedback;
  @override
  final String conceptTag;
  @override
  final String bloomLevel;
  @override
  final String difficulty;

  @override
  String toString() {
    return 'QuestionReport(questionId: $questionId, questionNumber: $questionNumber, questionText: $questionText, maxMarks: $maxMarks, awardedMarks: $awardedMarks, studentAnswer: $studentAnswer, modelAnswer: $modelAnswer, verdict: $verdict, feedback: $feedback, conceptTag: $conceptTag, bloomLevel: $bloomLevel, difficulty: $difficulty)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionReportImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.questionNumber, questionNumber) ||
                other.questionNumber == questionNumber) &&
            (identical(other.questionText, questionText) ||
                other.questionText == questionText) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.awardedMarks, awardedMarks) ||
                other.awardedMarks == awardedMarks) &&
            (identical(other.studentAnswer, studentAnswer) ||
                other.studentAnswer == studentAnswer) &&
            (identical(other.modelAnswer, modelAnswer) ||
                other.modelAnswer == modelAnswer) &&
            (identical(other.verdict, verdict) || other.verdict == verdict) &&
            (identical(other.feedback, feedback) ||
                other.feedback == feedback) &&
            (identical(other.conceptTag, conceptTag) ||
                other.conceptTag == conceptTag) &&
            (identical(other.bloomLevel, bloomLevel) ||
                other.bloomLevel == bloomLevel) &&
            (identical(other.difficulty, difficulty) ||
                other.difficulty == difficulty));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      questionNumber,
      questionText,
      maxMarks,
      awardedMarks,
      studentAnswer,
      modelAnswer,
      verdict,
      feedback,
      conceptTag,
      bloomLevel,
      difficulty);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionReportImplCopyWith<_$QuestionReportImpl> get copyWith =>
      __$$QuestionReportImplCopyWithImpl<_$QuestionReportImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionReportImplToJson(
      this,
    );
  }
}

abstract class _QuestionReport implements QuestionReport {
  const factory _QuestionReport(
      {required final String questionId,
      required final int questionNumber,
      required final String questionText,
      required final int maxMarks,
      required final int awardedMarks,
      required final String studentAnswer,
      required final String modelAnswer,
      required final String verdict,
      required final String feedback,
      required final String conceptTag,
      required final String bloomLevel,
      required final String difficulty}) = _$QuestionReportImpl;

  factory _QuestionReport.fromJson(Map<String, dynamic> json) =
      _$QuestionReportImpl.fromJson;

  @override
  String get questionId;
  @override
  int get questionNumber;
  @override
  String get questionText;
  @override
  int get maxMarks;
  @override
  int get awardedMarks;
  @override
  String get studentAnswer;
  @override
  String get modelAnswer;
  @override
  String get verdict;
  @override
  String get feedback;
  @override
  String get conceptTag;
  @override
  String get bloomLevel;
  @override
  String get difficulty;
  @override
  @JsonKey(ignore: true)
  _$$QuestionReportImplCopyWith<_$QuestionReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ConceptReport _$ConceptReportFromJson(Map<String, dynamic> json) {
  return _ConceptReport.fromJson(json);
}

/// @nodoc
mixin _$ConceptReport {
  String get conceptId => throw _privateConstructorUsedError;
  String get conceptName => throw _privateConstructorUsedError;
  String get chapterName => throw _privateConstructorUsedError;
  double get masteryScore => throw _privateConstructorUsedError;
  MasteryStatus get status => throw _privateConstructorUsedError;
  int get questionsAttempted => throw _privateConstructorUsedError;
  int get questionsCorrect => throw _privateConstructorUsedError;
  String get statusLabel => throw _privateConstructorUsedError;
  String get recommendation => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ConceptReportCopyWith<ConceptReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ConceptReportCopyWith<$Res> {
  factory $ConceptReportCopyWith(
          ConceptReport value, $Res Function(ConceptReport) then) =
      _$ConceptReportCopyWithImpl<$Res, ConceptReport>;
  @useResult
  $Res call(
      {String conceptId,
      String conceptName,
      String chapterName,
      double masteryScore,
      MasteryStatus status,
      int questionsAttempted,
      int questionsCorrect,
      String statusLabel,
      String recommendation});
}

/// @nodoc
class _$ConceptReportCopyWithImpl<$Res, $Val extends ConceptReport>
    implements $ConceptReportCopyWith<$Res> {
  _$ConceptReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? conceptId = null,
    Object? conceptName = null,
    Object? chapterName = null,
    Object? masteryScore = null,
    Object? status = null,
    Object? questionsAttempted = null,
    Object? questionsCorrect = null,
    Object? statusLabel = null,
    Object? recommendation = null,
  }) {
    return _then(_value.copyWith(
      conceptId: null == conceptId
          ? _value.conceptId
          : conceptId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptName: null == conceptName
          ? _value.conceptName
          : conceptName // ignore: cast_nullable_to_non_nullable
              as String,
      chapterName: null == chapterName
          ? _value.chapterName
          : chapterName // ignore: cast_nullable_to_non_nullable
              as String,
      masteryScore: null == masteryScore
          ? _value.masteryScore
          : masteryScore // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as MasteryStatus,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      questionsCorrect: null == questionsCorrect
          ? _value.questionsCorrect
          : questionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      statusLabel: null == statusLabel
          ? _value.statusLabel
          : statusLabel // ignore: cast_nullable_to_non_nullable
              as String,
      recommendation: null == recommendation
          ? _value.recommendation
          : recommendation // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ConceptReportImplCopyWith<$Res>
    implements $ConceptReportCopyWith<$Res> {
  factory _$$ConceptReportImplCopyWith(
          _$ConceptReportImpl value, $Res Function(_$ConceptReportImpl) then) =
      __$$ConceptReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String conceptId,
      String conceptName,
      String chapterName,
      double masteryScore,
      MasteryStatus status,
      int questionsAttempted,
      int questionsCorrect,
      String statusLabel,
      String recommendation});
}

/// @nodoc
class __$$ConceptReportImplCopyWithImpl<$Res>
    extends _$ConceptReportCopyWithImpl<$Res, _$ConceptReportImpl>
    implements _$$ConceptReportImplCopyWith<$Res> {
  __$$ConceptReportImplCopyWithImpl(
      _$ConceptReportImpl _value, $Res Function(_$ConceptReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? conceptId = null,
    Object? conceptName = null,
    Object? chapterName = null,
    Object? masteryScore = null,
    Object? status = null,
    Object? questionsAttempted = null,
    Object? questionsCorrect = null,
    Object? statusLabel = null,
    Object? recommendation = null,
  }) {
    return _then(_$ConceptReportImpl(
      conceptId: null == conceptId
          ? _value.conceptId
          : conceptId // ignore: cast_nullable_to_non_nullable
              as String,
      conceptName: null == conceptName
          ? _value.conceptName
          : conceptName // ignore: cast_nullable_to_non_nullable
              as String,
      chapterName: null == chapterName
          ? _value.chapterName
          : chapterName // ignore: cast_nullable_to_non_nullable
              as String,
      masteryScore: null == masteryScore
          ? _value.masteryScore
          : masteryScore // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as MasteryStatus,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      questionsCorrect: null == questionsCorrect
          ? _value.questionsCorrect
          : questionsCorrect // ignore: cast_nullable_to_non_nullable
              as int,
      statusLabel: null == statusLabel
          ? _value.statusLabel
          : statusLabel // ignore: cast_nullable_to_non_nullable
              as String,
      recommendation: null == recommendation
          ? _value.recommendation
          : recommendation // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ConceptReportImpl implements _ConceptReport {
  const _$ConceptReportImpl(
      {required this.conceptId,
      required this.conceptName,
      required this.chapterName,
      required this.masteryScore,
      required this.status,
      required this.questionsAttempted,
      required this.questionsCorrect,
      required this.statusLabel,
      required this.recommendation});

  factory _$ConceptReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConceptReportImplFromJson(json);

  @override
  final String conceptId;
  @override
  final String conceptName;
  @override
  final String chapterName;
  @override
  final double masteryScore;
  @override
  final MasteryStatus status;
  @override
  final int questionsAttempted;
  @override
  final int questionsCorrect;
  @override
  final String statusLabel;
  @override
  final String recommendation;

  @override
  String toString() {
    return 'ConceptReport(conceptId: $conceptId, conceptName: $conceptName, chapterName: $chapterName, masteryScore: $masteryScore, status: $status, questionsAttempted: $questionsAttempted, questionsCorrect: $questionsCorrect, statusLabel: $statusLabel, recommendation: $recommendation)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConceptReportImpl &&
            (identical(other.conceptId, conceptId) ||
                other.conceptId == conceptId) &&
            (identical(other.conceptName, conceptName) ||
                other.conceptName == conceptName) &&
            (identical(other.chapterName, chapterName) ||
                other.chapterName == chapterName) &&
            (identical(other.masteryScore, masteryScore) ||
                other.masteryScore == masteryScore) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.questionsAttempted, questionsAttempted) ||
                other.questionsAttempted == questionsAttempted) &&
            (identical(other.questionsCorrect, questionsCorrect) ||
                other.questionsCorrect == questionsCorrect) &&
            (identical(other.statusLabel, statusLabel) ||
                other.statusLabel == statusLabel) &&
            (identical(other.recommendation, recommendation) ||
                other.recommendation == recommendation));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      conceptId,
      conceptName,
      chapterName,
      masteryScore,
      status,
      questionsAttempted,
      questionsCorrect,
      statusLabel,
      recommendation);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ConceptReportImplCopyWith<_$ConceptReportImpl> get copyWith =>
      __$$ConceptReportImplCopyWithImpl<_$ConceptReportImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ConceptReportImplToJson(
      this,
    );
  }
}

abstract class _ConceptReport implements ConceptReport {
  const factory _ConceptReport(
      {required final String conceptId,
      required final String conceptName,
      required final String chapterName,
      required final double masteryScore,
      required final MasteryStatus status,
      required final int questionsAttempted,
      required final int questionsCorrect,
      required final String statusLabel,
      required final String recommendation}) = _$ConceptReportImpl;

  factory _ConceptReport.fromJson(Map<String, dynamic> json) =
      _$ConceptReportImpl.fromJson;

  @override
  String get conceptId;
  @override
  String get conceptName;
  @override
  String get chapterName;
  @override
  double get masteryScore;
  @override
  MasteryStatus get status;
  @override
  int get questionsAttempted;
  @override
  int get questionsCorrect;
  @override
  String get statusLabel;
  @override
  String get recommendation;
  @override
  @JsonKey(ignore: true)
  _$$ConceptReportImplCopyWith<_$ConceptReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BloomReport _$BloomReportFromJson(Map<String, dynamic> json) {
  return _BloomReport.fromJson(json);
}

/// @nodoc
mixin _$BloomReport {
  Map<String, BloomLevelReport> get byLevel =>
      throw _privateConstructorUsedError;
  String get strongestLevel => throw _privateConstructorUsedError;
  String get weakestLevel => throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BloomReportCopyWith<BloomReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BloomReportCopyWith<$Res> {
  factory $BloomReportCopyWith(
          BloomReport value, $Res Function(BloomReport) then) =
      _$BloomReportCopyWithImpl<$Res, BloomReport>;
  @useResult
  $Res call(
      {Map<String, BloomLevelReport> byLevel,
      String strongestLevel,
      String weakestLevel,
      List<String> insights});
}

/// @nodoc
class _$BloomReportCopyWithImpl<$Res, $Val extends BloomReport>
    implements $BloomReportCopyWith<$Res> {
  _$BloomReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byLevel = null,
    Object? strongestLevel = null,
    Object? weakestLevel = null,
    Object? insights = null,
  }) {
    return _then(_value.copyWith(
      byLevel: null == byLevel
          ? _value.byLevel
          : byLevel // ignore: cast_nullable_to_non_nullable
              as Map<String, BloomLevelReport>,
      strongestLevel: null == strongestLevel
          ? _value.strongestLevel
          : strongestLevel // ignore: cast_nullable_to_non_nullable
              as String,
      weakestLevel: null == weakestLevel
          ? _value.weakestLevel
          : weakestLevel // ignore: cast_nullable_to_non_nullable
              as String,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BloomReportImplCopyWith<$Res>
    implements $BloomReportCopyWith<$Res> {
  factory _$$BloomReportImplCopyWith(
          _$BloomReportImpl value, $Res Function(_$BloomReportImpl) then) =
      __$$BloomReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {Map<String, BloomLevelReport> byLevel,
      String strongestLevel,
      String weakestLevel,
      List<String> insights});
}

/// @nodoc
class __$$BloomReportImplCopyWithImpl<$Res>
    extends _$BloomReportCopyWithImpl<$Res, _$BloomReportImpl>
    implements _$$BloomReportImplCopyWith<$Res> {
  __$$BloomReportImplCopyWithImpl(
      _$BloomReportImpl _value, $Res Function(_$BloomReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byLevel = null,
    Object? strongestLevel = null,
    Object? weakestLevel = null,
    Object? insights = null,
  }) {
    return _then(_$BloomReportImpl(
      byLevel: null == byLevel
          ? _value._byLevel
          : byLevel // ignore: cast_nullable_to_non_nullable
              as Map<String, BloomLevelReport>,
      strongestLevel: null == strongestLevel
          ? _value.strongestLevel
          : strongestLevel // ignore: cast_nullable_to_non_nullable
              as String,
      weakestLevel: null == weakestLevel
          ? _value.weakestLevel
          : weakestLevel // ignore: cast_nullable_to_non_nullable
              as String,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BloomReportImpl implements _BloomReport {
  const _$BloomReportImpl(
      {required final Map<String, BloomLevelReport> byLevel,
      required this.strongestLevel,
      required this.weakestLevel,
      required final List<String> insights})
      : _byLevel = byLevel,
        _insights = insights;

  factory _$BloomReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$BloomReportImplFromJson(json);

  final Map<String, BloomLevelReport> _byLevel;
  @override
  Map<String, BloomLevelReport> get byLevel {
    if (_byLevel is EqualUnmodifiableMapView) return _byLevel;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_byLevel);
  }

  @override
  final String strongestLevel;
  @override
  final String weakestLevel;
  final List<String> _insights;
  @override
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  @override
  String toString() {
    return 'BloomReport(byLevel: $byLevel, strongestLevel: $strongestLevel, weakestLevel: $weakestLevel, insights: $insights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BloomReportImpl &&
            const DeepCollectionEquality().equals(other._byLevel, _byLevel) &&
            (identical(other.strongestLevel, strongestLevel) ||
                other.strongestLevel == strongestLevel) &&
            (identical(other.weakestLevel, weakestLevel) ||
                other.weakestLevel == weakestLevel) &&
            const DeepCollectionEquality().equals(other._insights, _insights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_byLevel),
      strongestLevel,
      weakestLevel,
      const DeepCollectionEquality().hash(_insights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BloomReportImplCopyWith<_$BloomReportImpl> get copyWith =>
      __$$BloomReportImplCopyWithImpl<_$BloomReportImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BloomReportImplToJson(
      this,
    );
  }
}

abstract class _BloomReport implements BloomReport {
  const factory _BloomReport(
      {required final Map<String, BloomLevelReport> byLevel,
      required final String strongestLevel,
      required final String weakestLevel,
      required final List<String> insights}) = _$BloomReportImpl;

  factory _BloomReport.fromJson(Map<String, dynamic> json) =
      _$BloomReportImpl.fromJson;

  @override
  Map<String, BloomLevelReport> get byLevel;
  @override
  String get strongestLevel;
  @override
  String get weakestLevel;
  @override
  List<String> get insights;
  @override
  @JsonKey(ignore: true)
  _$$BloomReportImplCopyWith<_$BloomReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BloomLevelReport _$BloomLevelReportFromJson(Map<String, dynamic> json) {
  return _BloomLevelReport.fromJson(json);
}

/// @nodoc
mixin _$BloomLevelReport {
  String get level => throw _privateConstructorUsedError;
  int get questionsAttempted => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  int get scoredMarks => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $BloomLevelReportCopyWith<BloomLevelReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BloomLevelReportCopyWith<$Res> {
  factory $BloomLevelReportCopyWith(
          BloomLevelReport value, $Res Function(BloomLevelReport) then) =
      _$BloomLevelReportCopyWithImpl<$Res, BloomLevelReport>;
  @useResult
  $Res call(
      {String level,
      int questionsAttempted,
      int maxMarks,
      int scoredMarks,
      double percentage,
      String status});
}

/// @nodoc
class _$BloomLevelReportCopyWithImpl<$Res, $Val extends BloomLevelReport>
    implements $BloomLevelReportCopyWith<$Res> {
  _$BloomLevelReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? questionsAttempted = null,
    Object? maxMarks = null,
    Object? scoredMarks = null,
    Object? percentage = null,
    Object? status = null,
  }) {
    return _then(_value.copyWith(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      scoredMarks: null == scoredMarks
          ? _value.scoredMarks
          : scoredMarks // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BloomLevelReportImplCopyWith<$Res>
    implements $BloomLevelReportCopyWith<$Res> {
  factory _$$BloomLevelReportImplCopyWith(_$BloomLevelReportImpl value,
          $Res Function(_$BloomLevelReportImpl) then) =
      __$$BloomLevelReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String level,
      int questionsAttempted,
      int maxMarks,
      int scoredMarks,
      double percentage,
      String status});
}

/// @nodoc
class __$$BloomLevelReportImplCopyWithImpl<$Res>
    extends _$BloomLevelReportCopyWithImpl<$Res, _$BloomLevelReportImpl>
    implements _$$BloomLevelReportImplCopyWith<$Res> {
  __$$BloomLevelReportImplCopyWithImpl(_$BloomLevelReportImpl _value,
      $Res Function(_$BloomLevelReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? questionsAttempted = null,
    Object? maxMarks = null,
    Object? scoredMarks = null,
    Object? percentage = null,
    Object? status = null,
  }) {
    return _then(_$BloomLevelReportImpl(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      scoredMarks: null == scoredMarks
          ? _value.scoredMarks
          : scoredMarks // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BloomLevelReportImpl implements _BloomLevelReport {
  const _$BloomLevelReportImpl(
      {required this.level,
      required this.questionsAttempted,
      required this.maxMarks,
      required this.scoredMarks,
      required this.percentage,
      required this.status});

  factory _$BloomLevelReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$BloomLevelReportImplFromJson(json);

  @override
  final String level;
  @override
  final int questionsAttempted;
  @override
  final int maxMarks;
  @override
  final int scoredMarks;
  @override
  final double percentage;
  @override
  final String status;

  @override
  String toString() {
    return 'BloomLevelReport(level: $level, questionsAttempted: $questionsAttempted, maxMarks: $maxMarks, scoredMarks: $scoredMarks, percentage: $percentage, status: $status)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BloomLevelReportImpl &&
            (identical(other.level, level) || other.level == level) &&
            (identical(other.questionsAttempted, questionsAttempted) ||
                other.questionsAttempted == questionsAttempted) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.scoredMarks, scoredMarks) ||
                other.scoredMarks == scoredMarks) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.status, status) || other.status == status));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, level, questionsAttempted,
      maxMarks, scoredMarks, percentage, status);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$BloomLevelReportImplCopyWith<_$BloomLevelReportImpl> get copyWith =>
      __$$BloomLevelReportImplCopyWithImpl<_$BloomLevelReportImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BloomLevelReportImplToJson(
      this,
    );
  }
}

abstract class _BloomLevelReport implements BloomLevelReport {
  const factory _BloomLevelReport(
      {required final String level,
      required final int questionsAttempted,
      required final int maxMarks,
      required final int scoredMarks,
      required final double percentage,
      required final String status}) = _$BloomLevelReportImpl;

  factory _BloomLevelReport.fromJson(Map<String, dynamic> json) =
      _$BloomLevelReportImpl.fromJson;

  @override
  String get level;
  @override
  int get questionsAttempted;
  @override
  int get maxMarks;
  @override
  int get scoredMarks;
  @override
  double get percentage;
  @override
  String get status;
  @override
  @JsonKey(ignore: true)
  _$$BloomLevelReportImplCopyWith<_$BloomLevelReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CompetencyReport _$CompetencyReportFromJson(Map<String, dynamic> json) {
  return _CompetencyReport.fromJson(json);
}

/// @nodoc
mixin _$CompetencyReport {
  Map<String, CompetencyReportItem> get byCompetency =>
      throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CompetencyReportCopyWith<CompetencyReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CompetencyReportCopyWith<$Res> {
  factory $CompetencyReportCopyWith(
          CompetencyReport value, $Res Function(CompetencyReport) then) =
      _$CompetencyReportCopyWithImpl<$Res, CompetencyReport>;
  @useResult
  $Res call(
      {Map<String, CompetencyReportItem> byCompetency, List<String> insights});
}

/// @nodoc
class _$CompetencyReportCopyWithImpl<$Res, $Val extends CompetencyReport>
    implements $CompetencyReportCopyWith<$Res> {
  _$CompetencyReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byCompetency = null,
    Object? insights = null,
  }) {
    return _then(_value.copyWith(
      byCompetency: null == byCompetency
          ? _value.byCompetency
          : byCompetency // ignore: cast_nullable_to_non_nullable
              as Map<String, CompetencyReportItem>,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CompetencyReportImplCopyWith<$Res>
    implements $CompetencyReportCopyWith<$Res> {
  factory _$$CompetencyReportImplCopyWith(_$CompetencyReportImpl value,
          $Res Function(_$CompetencyReportImpl) then) =
      __$$CompetencyReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {Map<String, CompetencyReportItem> byCompetency, List<String> insights});
}

/// @nodoc
class __$$CompetencyReportImplCopyWithImpl<$Res>
    extends _$CompetencyReportCopyWithImpl<$Res, _$CompetencyReportImpl>
    implements _$$CompetencyReportImplCopyWith<$Res> {
  __$$CompetencyReportImplCopyWithImpl(_$CompetencyReportImpl _value,
      $Res Function(_$CompetencyReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? byCompetency = null,
    Object? insights = null,
  }) {
    return _then(_$CompetencyReportImpl(
      byCompetency: null == byCompetency
          ? _value._byCompetency
          : byCompetency // ignore: cast_nullable_to_non_nullable
              as Map<String, CompetencyReportItem>,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CompetencyReportImpl implements _CompetencyReport {
  const _$CompetencyReportImpl(
      {required final Map<String, CompetencyReportItem> byCompetency,
      required final List<String> insights})
      : _byCompetency = byCompetency,
        _insights = insights;

  factory _$CompetencyReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$CompetencyReportImplFromJson(json);

  final Map<String, CompetencyReportItem> _byCompetency;
  @override
  Map<String, CompetencyReportItem> get byCompetency {
    if (_byCompetency is EqualUnmodifiableMapView) return _byCompetency;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_byCompetency);
  }

  final List<String> _insights;
  @override
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  @override
  String toString() {
    return 'CompetencyReport(byCompetency: $byCompetency, insights: $insights)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CompetencyReportImpl &&
            const DeepCollectionEquality()
                .equals(other._byCompetency, _byCompetency) &&
            const DeepCollectionEquality().equals(other._insights, _insights));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_byCompetency),
      const DeepCollectionEquality().hash(_insights));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CompetencyReportImplCopyWith<_$CompetencyReportImpl> get copyWith =>
      __$$CompetencyReportImplCopyWithImpl<_$CompetencyReportImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CompetencyReportImplToJson(
      this,
    );
  }
}

abstract class _CompetencyReport implements CompetencyReport {
  const factory _CompetencyReport(
      {required final Map<String, CompetencyReportItem> byCompetency,
      required final List<String> insights}) = _$CompetencyReportImpl;

  factory _CompetencyReport.fromJson(Map<String, dynamic> json) =
      _$CompetencyReportImpl.fromJson;

  @override
  Map<String, CompetencyReportItem> get byCompetency;
  @override
  List<String> get insights;
  @override
  @JsonKey(ignore: true)
  _$$CompetencyReportImplCopyWith<_$CompetencyReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CompetencyReportItem _$CompetencyReportItemFromJson(Map<String, dynamic> json) {
  return _CompetencyReportItem.fromJson(json);
}

/// @nodoc
mixin _$CompetencyReportItem {
  String get competencyId => throw _privateConstructorUsedError;
  String get competencyName => throw _privateConstructorUsedError;
  int get questionsAttempted => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  int get scoredMarks => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $CompetencyReportItemCopyWith<CompetencyReportItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CompetencyReportItemCopyWith<$Res> {
  factory $CompetencyReportItemCopyWith(CompetencyReportItem value,
          $Res Function(CompetencyReportItem) then) =
      _$CompetencyReportItemCopyWithImpl<$Res, CompetencyReportItem>;
  @useResult
  $Res call(
      {String competencyId,
      String competencyName,
      int questionsAttempted,
      int maxMarks,
      int scoredMarks,
      double percentage,
      String status});
}

/// @nodoc
class _$CompetencyReportItemCopyWithImpl<$Res,
        $Val extends CompetencyReportItem>
    implements $CompetencyReportItemCopyWith<$Res> {
  _$CompetencyReportItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? competencyId = null,
    Object? competencyName = null,
    Object? questionsAttempted = null,
    Object? maxMarks = null,
    Object? scoredMarks = null,
    Object? percentage = null,
    Object? status = null,
  }) {
    return _then(_value.copyWith(
      competencyId: null == competencyId
          ? _value.competencyId
          : competencyId // ignore: cast_nullable_to_non_nullable
              as String,
      competencyName: null == competencyName
          ? _value.competencyName
          : competencyName // ignore: cast_nullable_to_non_nullable
              as String,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      scoredMarks: null == scoredMarks
          ? _value.scoredMarks
          : scoredMarks // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CompetencyReportItemImplCopyWith<$Res>
    implements $CompetencyReportItemCopyWith<$Res> {
  factory _$$CompetencyReportItemImplCopyWith(_$CompetencyReportItemImpl value,
          $Res Function(_$CompetencyReportItemImpl) then) =
      __$$CompetencyReportItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String competencyId,
      String competencyName,
      int questionsAttempted,
      int maxMarks,
      int scoredMarks,
      double percentage,
      String status});
}

/// @nodoc
class __$$CompetencyReportItemImplCopyWithImpl<$Res>
    extends _$CompetencyReportItemCopyWithImpl<$Res, _$CompetencyReportItemImpl>
    implements _$$CompetencyReportItemImplCopyWith<$Res> {
  __$$CompetencyReportItemImplCopyWithImpl(_$CompetencyReportItemImpl _value,
      $Res Function(_$CompetencyReportItemImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? competencyId = null,
    Object? competencyName = null,
    Object? questionsAttempted = null,
    Object? maxMarks = null,
    Object? scoredMarks = null,
    Object? percentage = null,
    Object? status = null,
  }) {
    return _then(_$CompetencyReportItemImpl(
      competencyId: null == competencyId
          ? _value.competencyId
          : competencyId // ignore: cast_nullable_to_non_nullable
              as String,
      competencyName: null == competencyName
          ? _value.competencyName
          : competencyName // ignore: cast_nullable_to_non_nullable
              as String,
      questionsAttempted: null == questionsAttempted
          ? _value.questionsAttempted
          : questionsAttempted // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      scoredMarks: null == scoredMarks
          ? _value.scoredMarks
          : scoredMarks // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CompetencyReportItemImpl implements _CompetencyReportItem {
  const _$CompetencyReportItemImpl(
      {required this.competencyId,
      required this.competencyName,
      required this.questionsAttempted,
      required this.maxMarks,
      required this.scoredMarks,
      required this.percentage,
      required this.status});

  factory _$CompetencyReportItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$CompetencyReportItemImplFromJson(json);

  @override
  final String competencyId;
  @override
  final String competencyName;
  @override
  final int questionsAttempted;
  @override
  final int maxMarks;
  @override
  final int scoredMarks;
  @override
  final double percentage;
  @override
  final String status;

  @override
  String toString() {
    return 'CompetencyReportItem(competencyId: $competencyId, competencyName: $competencyName, questionsAttempted: $questionsAttempted, maxMarks: $maxMarks, scoredMarks: $scoredMarks, percentage: $percentage, status: $status)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CompetencyReportItemImpl &&
            (identical(other.competencyId, competencyId) ||
                other.competencyId == competencyId) &&
            (identical(other.competencyName, competencyName) ||
                other.competencyName == competencyName) &&
            (identical(other.questionsAttempted, questionsAttempted) ||
                other.questionsAttempted == questionsAttempted) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.scoredMarks, scoredMarks) ||
                other.scoredMarks == scoredMarks) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.status, status) || other.status == status));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, competencyId, competencyName,
      questionsAttempted, maxMarks, scoredMarks, percentage, status);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$CompetencyReportItemImplCopyWith<_$CompetencyReportItemImpl>
      get copyWith =>
          __$$CompetencyReportItemImplCopyWithImpl<_$CompetencyReportItemImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CompetencyReportItemImplToJson(
      this,
    );
  }
}

abstract class _CompetencyReportItem implements CompetencyReportItem {
  const factory _CompetencyReportItem(
      {required final String competencyId,
      required final String competencyName,
      required final int questionsAttempted,
      required final int maxMarks,
      required final int scoredMarks,
      required final double percentage,
      required final String status}) = _$CompetencyReportItemImpl;

  factory _CompetencyReportItem.fromJson(Map<String, dynamic> json) =
      _$CompetencyReportItemImpl.fromJson;

  @override
  String get competencyId;
  @override
  String get competencyName;
  @override
  int get questionsAttempted;
  @override
  int get maxMarks;
  @override
  int get scoredMarks;
  @override
  double get percentage;
  @override
  String get status;
  @override
  @JsonKey(ignore: true)
  _$$CompetencyReportItemImplCopyWith<_$CompetencyReportItemImpl>
      get copyWith => throw _privateConstructorUsedError;
}

TeacherRemarks _$TeacherRemarksFromJson(Map<String, dynamic> json) {
  return _TeacherRemarks.fromJson(json);
}

/// @nodoc
mixin _$TeacherRemarks {
  String get overallComment => throw _privateConstructorUsedError;
  List<String> get specificComments => throw _privateConstructorUsedError;
  String get encouragement => throw _privateConstructorUsedError;
  String get nextSteps => throw _privateConstructorUsedError;
  DateTime get writtenAt => throw _privateConstructorUsedError;
  String get writtenBy => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $TeacherRemarksCopyWith<TeacherRemarks> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TeacherRemarksCopyWith<$Res> {
  factory $TeacherRemarksCopyWith(
          TeacherRemarks value, $Res Function(TeacherRemarks) then) =
      _$TeacherRemarksCopyWithImpl<$Res, TeacherRemarks>;
  @useResult
  $Res call(
      {String overallComment,
      List<String> specificComments,
      String encouragement,
      String nextSteps,
      DateTime writtenAt,
      String writtenBy});
}

/// @nodoc
class _$TeacherRemarksCopyWithImpl<$Res, $Val extends TeacherRemarks>
    implements $TeacherRemarksCopyWith<$Res> {
  _$TeacherRemarksCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? overallComment = null,
    Object? specificComments = null,
    Object? encouragement = null,
    Object? nextSteps = null,
    Object? writtenAt = null,
    Object? writtenBy = null,
  }) {
    return _then(_value.copyWith(
      overallComment: null == overallComment
          ? _value.overallComment
          : overallComment // ignore: cast_nullable_to_non_nullable
              as String,
      specificComments: null == specificComments
          ? _value.specificComments
          : specificComments // ignore: cast_nullable_to_non_nullable
              as List<String>,
      encouragement: null == encouragement
          ? _value.encouragement
          : encouragement // ignore: cast_nullable_to_non_nullable
              as String,
      nextSteps: null == nextSteps
          ? _value.nextSteps
          : nextSteps // ignore: cast_nullable_to_non_nullable
              as String,
      writtenAt: null == writtenAt
          ? _value.writtenAt
          : writtenAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      writtenBy: null == writtenBy
          ? _value.writtenBy
          : writtenBy // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TeacherRemarksImplCopyWith<$Res>
    implements $TeacherRemarksCopyWith<$Res> {
  factory _$$TeacherRemarksImplCopyWith(_$TeacherRemarksImpl value,
          $Res Function(_$TeacherRemarksImpl) then) =
      __$$TeacherRemarksImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String overallComment,
      List<String> specificComments,
      String encouragement,
      String nextSteps,
      DateTime writtenAt,
      String writtenBy});
}

/// @nodoc
class __$$TeacherRemarksImplCopyWithImpl<$Res>
    extends _$TeacherRemarksCopyWithImpl<$Res, _$TeacherRemarksImpl>
    implements _$$TeacherRemarksImplCopyWith<$Res> {
  __$$TeacherRemarksImplCopyWithImpl(
      _$TeacherRemarksImpl _value, $Res Function(_$TeacherRemarksImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? overallComment = null,
    Object? specificComments = null,
    Object? encouragement = null,
    Object? nextSteps = null,
    Object? writtenAt = null,
    Object? writtenBy = null,
  }) {
    return _then(_$TeacherRemarksImpl(
      overallComment: null == overallComment
          ? _value.overallComment
          : overallComment // ignore: cast_nullable_to_non_nullable
              as String,
      specificComments: null == specificComments
          ? _value._specificComments
          : specificComments // ignore: cast_nullable_to_non_nullable
              as List<String>,
      encouragement: null == encouragement
          ? _value.encouragement
          : encouragement // ignore: cast_nullable_to_non_nullable
              as String,
      nextSteps: null == nextSteps
          ? _value.nextSteps
          : nextSteps // ignore: cast_nullable_to_non_nullable
              as String,
      writtenAt: null == writtenAt
          ? _value.writtenAt
          : writtenAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      writtenBy: null == writtenBy
          ? _value.writtenBy
          : writtenBy // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TeacherRemarksImpl implements _TeacherRemarks {
  const _$TeacherRemarksImpl(
      {required this.overallComment,
      required final List<String> specificComments,
      required this.encouragement,
      required this.nextSteps,
      required this.writtenAt,
      required this.writtenBy})
      : _specificComments = specificComments;

  factory _$TeacherRemarksImpl.fromJson(Map<String, dynamic> json) =>
      _$$TeacherRemarksImplFromJson(json);

  @override
  final String overallComment;
  final List<String> _specificComments;
  @override
  List<String> get specificComments {
    if (_specificComments is EqualUnmodifiableListView)
      return _specificComments;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_specificComments);
  }

  @override
  final String encouragement;
  @override
  final String nextSteps;
  @override
  final DateTime writtenAt;
  @override
  final String writtenBy;

  @override
  String toString() {
    return 'TeacherRemarks(overallComment: $overallComment, specificComments: $specificComments, encouragement: $encouragement, nextSteps: $nextSteps, writtenAt: $writtenAt, writtenBy: $writtenBy)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TeacherRemarksImpl &&
            (identical(other.overallComment, overallComment) ||
                other.overallComment == overallComment) &&
            const DeepCollectionEquality()
                .equals(other._specificComments, _specificComments) &&
            (identical(other.encouragement, encouragement) ||
                other.encouragement == encouragement) &&
            (identical(other.nextSteps, nextSteps) ||
                other.nextSteps == nextSteps) &&
            (identical(other.writtenAt, writtenAt) ||
                other.writtenAt == writtenAt) &&
            (identical(other.writtenBy, writtenBy) ||
                other.writtenBy == writtenBy));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      overallComment,
      const DeepCollectionEquality().hash(_specificComments),
      encouragement,
      nextSteps,
      writtenAt,
      writtenBy);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$TeacherRemarksImplCopyWith<_$TeacherRemarksImpl> get copyWith =>
      __$$TeacherRemarksImplCopyWithImpl<_$TeacherRemarksImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TeacherRemarksImplToJson(
      this,
    );
  }
}

abstract class _TeacherRemarks implements TeacherRemarks {
  const factory _TeacherRemarks(
      {required final String overallComment,
      required final List<String> specificComments,
      required final String encouragement,
      required final String nextSteps,
      required final DateTime writtenAt,
      required final String writtenBy}) = _$TeacherRemarksImpl;

  factory _TeacherRemarks.fromJson(Map<String, dynamic> json) =
      _$TeacherRemarksImpl.fromJson;

  @override
  String get overallComment;
  @override
  List<String> get specificComments;
  @override
  String get encouragement;
  @override
  String get nextSteps;
  @override
  DateTime get writtenAt;
  @override
  String get writtenBy;
  @override
  @JsonKey(ignore: true)
  _$$TeacherRemarksImplCopyWith<_$TeacherRemarksImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ParentSummary _$ParentSummaryFromJson(Map<String, dynamic> json) {
  return _ParentSummary.fromJson(json);
}

/// @nodoc
mixin _$ParentSummary {
  String get simpleSummary => throw _privateConstructorUsedError;
  List<String> get keyStrengths => throw _privateConstructorUsedError;
  List<String> get keyAreasForImprovement => throw _privateConstructorUsedError;
  String get homeSupportSuggestion => throw _privateConstructorUsedError;
  String get teacherMessage => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ParentSummaryCopyWith<ParentSummary> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParentSummaryCopyWith<$Res> {
  factory $ParentSummaryCopyWith(
          ParentSummary value, $Res Function(ParentSummary) then) =
      _$ParentSummaryCopyWithImpl<$Res, ParentSummary>;
  @useResult
  $Res call(
      {String simpleSummary,
      List<String> keyStrengths,
      List<String> keyAreasForImprovement,
      String homeSupportSuggestion,
      String teacherMessage});
}

/// @nodoc
class _$ParentSummaryCopyWithImpl<$Res, $Val extends ParentSummary>
    implements $ParentSummaryCopyWith<$Res> {
  _$ParentSummaryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? simpleSummary = null,
    Object? keyStrengths = null,
    Object? keyAreasForImprovement = null,
    Object? homeSupportSuggestion = null,
    Object? teacherMessage = null,
  }) {
    return _then(_value.copyWith(
      simpleSummary: null == simpleSummary
          ? _value.simpleSummary
          : simpleSummary // ignore: cast_nullable_to_non_nullable
              as String,
      keyStrengths: null == keyStrengths
          ? _value.keyStrengths
          : keyStrengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      keyAreasForImprovement: null == keyAreasForImprovement
          ? _value.keyAreasForImprovement
          : keyAreasForImprovement // ignore: cast_nullable_to_non_nullable
              as List<String>,
      homeSupportSuggestion: null == homeSupportSuggestion
          ? _value.homeSupportSuggestion
          : homeSupportSuggestion // ignore: cast_nullable_to_non_nullable
              as String,
      teacherMessage: null == teacherMessage
          ? _value.teacherMessage
          : teacherMessage // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ParentSummaryImplCopyWith<$Res>
    implements $ParentSummaryCopyWith<$Res> {
  factory _$$ParentSummaryImplCopyWith(
          _$ParentSummaryImpl value, $Res Function(_$ParentSummaryImpl) then) =
      __$$ParentSummaryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String simpleSummary,
      List<String> keyStrengths,
      List<String> keyAreasForImprovement,
      String homeSupportSuggestion,
      String teacherMessage});
}

/// @nodoc
class __$$ParentSummaryImplCopyWithImpl<$Res>
    extends _$ParentSummaryCopyWithImpl<$Res, _$ParentSummaryImpl>
    implements _$$ParentSummaryImplCopyWith<$Res> {
  __$$ParentSummaryImplCopyWithImpl(
      _$ParentSummaryImpl _value, $Res Function(_$ParentSummaryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? simpleSummary = null,
    Object? keyStrengths = null,
    Object? keyAreasForImprovement = null,
    Object? homeSupportSuggestion = null,
    Object? teacherMessage = null,
  }) {
    return _then(_$ParentSummaryImpl(
      simpleSummary: null == simpleSummary
          ? _value.simpleSummary
          : simpleSummary // ignore: cast_nullable_to_non_nullable
              as String,
      keyStrengths: null == keyStrengths
          ? _value._keyStrengths
          : keyStrengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      keyAreasForImprovement: null == keyAreasForImprovement
          ? _value._keyAreasForImprovement
          : keyAreasForImprovement // ignore: cast_nullable_to_non_nullable
              as List<String>,
      homeSupportSuggestion: null == homeSupportSuggestion
          ? _value.homeSupportSuggestion
          : homeSupportSuggestion // ignore: cast_nullable_to_non_nullable
              as String,
      teacherMessage: null == teacherMessage
          ? _value.teacherMessage
          : teacherMessage // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ParentSummaryImpl implements _ParentSummary {
  const _$ParentSummaryImpl(
      {required this.simpleSummary,
      required final List<String> keyStrengths,
      required final List<String> keyAreasForImprovement,
      required this.homeSupportSuggestion,
      required this.teacherMessage})
      : _keyStrengths = keyStrengths,
        _keyAreasForImprovement = keyAreasForImprovement;

  factory _$ParentSummaryImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParentSummaryImplFromJson(json);

  @override
  final String simpleSummary;
  final List<String> _keyStrengths;
  @override
  List<String> get keyStrengths {
    if (_keyStrengths is EqualUnmodifiableListView) return _keyStrengths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keyStrengths);
  }

  final List<String> _keyAreasForImprovement;
  @override
  List<String> get keyAreasForImprovement {
    if (_keyAreasForImprovement is EqualUnmodifiableListView)
      return _keyAreasForImprovement;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keyAreasForImprovement);
  }

  @override
  final String homeSupportSuggestion;
  @override
  final String teacherMessage;

  @override
  String toString() {
    return 'ParentSummary(simpleSummary: $simpleSummary, keyStrengths: $keyStrengths, keyAreasForImprovement: $keyAreasForImprovement, homeSupportSuggestion: $homeSupportSuggestion, teacherMessage: $teacherMessage)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParentSummaryImpl &&
            (identical(other.simpleSummary, simpleSummary) ||
                other.simpleSummary == simpleSummary) &&
            const DeepCollectionEquality()
                .equals(other._keyStrengths, _keyStrengths) &&
            const DeepCollectionEquality().equals(
                other._keyAreasForImprovement, _keyAreasForImprovement) &&
            (identical(other.homeSupportSuggestion, homeSupportSuggestion) ||
                other.homeSupportSuggestion == homeSupportSuggestion) &&
            (identical(other.teacherMessage, teacherMessage) ||
                other.teacherMessage == teacherMessage));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      simpleSummary,
      const DeepCollectionEquality().hash(_keyStrengths),
      const DeepCollectionEquality().hash(_keyAreasForImprovement),
      homeSupportSuggestion,
      teacherMessage);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ParentSummaryImplCopyWith<_$ParentSummaryImpl> get copyWith =>
      __$$ParentSummaryImplCopyWithImpl<_$ParentSummaryImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ParentSummaryImplToJson(
      this,
    );
  }
}

abstract class _ParentSummary implements ParentSummary {
  const factory _ParentSummary(
      {required final String simpleSummary,
      required final List<String> keyStrengths,
      required final List<String> keyAreasForImprovement,
      required final String homeSupportSuggestion,
      required final String teacherMessage}) = _$ParentSummaryImpl;

  factory _ParentSummary.fromJson(Map<String, dynamic> json) =
      _$ParentSummaryImpl.fromJson;

  @override
  String get simpleSummary;
  @override
  List<String> get keyStrengths;
  @override
  List<String> get keyAreasForImprovement;
  @override
  String get homeSupportSuggestion;
  @override
  String get teacherMessage;
  @override
  @JsonKey(ignore: true)
  _$$ParentSummaryImplCopyWith<_$ParentSummaryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ParentReport _$ParentReportFromJson(Map<String, dynamic> json) {
  return _ParentReport.fromJson(json);
}

/// @nodoc
mixin _$ParentReport {
  String get id => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  String get studentName => throw _privateConstructorUsedError;
  String get assessmentId => throw _privateConstructorUsedError;
  String get assessmentTitle => throw _privateConstructorUsedError;
  String get className => throw _privateConstructorUsedError;
  ReportHeader get header => throw _privateConstructorUsedError;
  ParentPerformanceSummary get summary => throw _privateConstructorUsedError;
  List<String> get keyStrengths => throw _privateConstructorUsedError;
  List<String> get areasForImprovement => throw _privateConstructorUsedError;
  List<String> get atHomeSuggestions => throw _privateConstructorUsedError;
  String get teacherMessage => throw _privateConstructorUsedError;
  List<ActionableRecommendation> get nextSteps =>
      throw _privateConstructorUsedError;
  DateTime get generatedAt => throw _privateConstructorUsedError;
  String get generatedBy => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ParentReportCopyWith<ParentReport> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParentReportCopyWith<$Res> {
  factory $ParentReportCopyWith(
          ParentReport value, $Res Function(ParentReport) then) =
      _$ParentReportCopyWithImpl<$Res, ParentReport>;
  @useResult
  $Res call(
      {String id,
      String studentId,
      String studentName,
      String assessmentId,
      String assessmentTitle,
      String className,
      ReportHeader header,
      ParentPerformanceSummary summary,
      List<String> keyStrengths,
      List<String> areasForImprovement,
      List<String> atHomeSuggestions,
      String teacherMessage,
      List<ActionableRecommendation> nextSteps,
      DateTime generatedAt,
      String generatedBy});

  $ReportHeaderCopyWith<$Res> get header;
  $ParentPerformanceSummaryCopyWith<$Res> get summary;
}

/// @nodoc
class _$ParentReportCopyWithImpl<$Res, $Val extends ParentReport>
    implements $ParentReportCopyWith<$Res> {
  _$ParentReportCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? assessmentId = null,
    Object? assessmentTitle = null,
    Object? className = null,
    Object? header = null,
    Object? summary = null,
    Object? keyStrengths = null,
    Object? areasForImprovement = null,
    Object? atHomeSuggestions = null,
    Object? teacherMessage = null,
    Object? nextSteps = null,
    Object? generatedAt = null,
    Object? generatedBy = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      className: null == className
          ? _value.className
          : className // ignore: cast_nullable_to_non_nullable
              as String,
      header: null == header
          ? _value.header
          : header // ignore: cast_nullable_to_non_nullable
              as ReportHeader,
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as ParentPerformanceSummary,
      keyStrengths: null == keyStrengths
          ? _value.keyStrengths
          : keyStrengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      areasForImprovement: null == areasForImprovement
          ? _value.areasForImprovement
          : areasForImprovement // ignore: cast_nullable_to_non_nullable
              as List<String>,
      atHomeSuggestions: null == atHomeSuggestions
          ? _value.atHomeSuggestions
          : atHomeSuggestions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      teacherMessage: null == teacherMessage
          ? _value.teacherMessage
          : teacherMessage // ignore: cast_nullable_to_non_nullable
              as String,
      nextSteps: null == nextSteps
          ? _value.nextSteps
          : nextSteps // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      generatedBy: null == generatedBy
          ? _value.generatedBy
          : generatedBy // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ReportHeaderCopyWith<$Res> get header {
    return $ReportHeaderCopyWith<$Res>(_value.header, (value) {
      return _then(_value.copyWith(header: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ParentPerformanceSummaryCopyWith<$Res> get summary {
    return $ParentPerformanceSummaryCopyWith<$Res>(_value.summary, (value) {
      return _then(_value.copyWith(summary: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ParentReportImplCopyWith<$Res>
    implements $ParentReportCopyWith<$Res> {
  factory _$$ParentReportImplCopyWith(
          _$ParentReportImpl value, $Res Function(_$ParentReportImpl) then) =
      __$$ParentReportImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String studentId,
      String studentName,
      String assessmentId,
      String assessmentTitle,
      String className,
      ReportHeader header,
      ParentPerformanceSummary summary,
      List<String> keyStrengths,
      List<String> areasForImprovement,
      List<String> atHomeSuggestions,
      String teacherMessage,
      List<ActionableRecommendation> nextSteps,
      DateTime generatedAt,
      String generatedBy});

  @override
  $ReportHeaderCopyWith<$Res> get header;
  @override
  $ParentPerformanceSummaryCopyWith<$Res> get summary;
}

/// @nodoc
class __$$ParentReportImplCopyWithImpl<$Res>
    extends _$ParentReportCopyWithImpl<$Res, _$ParentReportImpl>
    implements _$$ParentReportImplCopyWith<$Res> {
  __$$ParentReportImplCopyWithImpl(
      _$ParentReportImpl _value, $Res Function(_$ParentReportImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? assessmentId = null,
    Object? assessmentTitle = null,
    Object? className = null,
    Object? header = null,
    Object? summary = null,
    Object? keyStrengths = null,
    Object? areasForImprovement = null,
    Object? atHomeSuggestions = null,
    Object? teacherMessage = null,
    Object? nextSteps = null,
    Object? generatedAt = null,
    Object? generatedBy = null,
  }) {
    return _then(_$ParentReportImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      studentId: null == studentId
          ? _value.studentId
          : studentId // ignore: cast_nullable_to_non_nullable
              as String,
      studentName: null == studentName
          ? _value.studentName
          : studentName // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentTitle: null == assessmentTitle
          ? _value.assessmentTitle
          : assessmentTitle // ignore: cast_nullable_to_non_nullable
              as String,
      className: null == className
          ? _value.className
          : className // ignore: cast_nullable_to_non_nullable
              as String,
      header: null == header
          ? _value.header
          : header // ignore: cast_nullable_to_non_nullable
              as ReportHeader,
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as ParentPerformanceSummary,
      keyStrengths: null == keyStrengths
          ? _value._keyStrengths
          : keyStrengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      areasForImprovement: null == areasForImprovement
          ? _value._areasForImprovement
          : areasForImprovement // ignore: cast_nullable_to_non_nullable
              as List<String>,
      atHomeSuggestions: null == atHomeSuggestions
          ? _value._atHomeSuggestions
          : atHomeSuggestions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      teacherMessage: null == teacherMessage
          ? _value.teacherMessage
          : teacherMessage // ignore: cast_nullable_to_non_nullable
              as String,
      nextSteps: null == nextSteps
          ? _value._nextSteps
          : nextSteps // ignore: cast_nullable_to_non_nullable
              as List<ActionableRecommendation>,
      generatedAt: null == generatedAt
          ? _value.generatedAt
          : generatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      generatedBy: null == generatedBy
          ? _value.generatedBy
          : generatedBy // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ParentReportImpl implements _ParentReport {
  const _$ParentReportImpl(
      {required this.id,
      required this.studentId,
      required this.studentName,
      required this.assessmentId,
      required this.assessmentTitle,
      required this.className,
      required this.header,
      required this.summary,
      required final List<String> keyStrengths,
      required final List<String> areasForImprovement,
      required final List<String> atHomeSuggestions,
      required this.teacherMessage,
      required final List<ActionableRecommendation> nextSteps,
      required this.generatedAt,
      required this.generatedBy})
      : _keyStrengths = keyStrengths,
        _areasForImprovement = areasForImprovement,
        _atHomeSuggestions = atHomeSuggestions,
        _nextSteps = nextSteps;

  factory _$ParentReportImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParentReportImplFromJson(json);

  @override
  final String id;
  @override
  final String studentId;
  @override
  final String studentName;
  @override
  final String assessmentId;
  @override
  final String assessmentTitle;
  @override
  final String className;
  @override
  final ReportHeader header;
  @override
  final ParentPerformanceSummary summary;
  final List<String> _keyStrengths;
  @override
  List<String> get keyStrengths {
    if (_keyStrengths is EqualUnmodifiableListView) return _keyStrengths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keyStrengths);
  }

  final List<String> _areasForImprovement;
  @override
  List<String> get areasForImprovement {
    if (_areasForImprovement is EqualUnmodifiableListView)
      return _areasForImprovement;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_areasForImprovement);
  }

  final List<String> _atHomeSuggestions;
  @override
  List<String> get atHomeSuggestions {
    if (_atHomeSuggestions is EqualUnmodifiableListView)
      return _atHomeSuggestions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_atHomeSuggestions);
  }

  @override
  final String teacherMessage;
  final List<ActionableRecommendation> _nextSteps;
  @override
  List<ActionableRecommendation> get nextSteps {
    if (_nextSteps is EqualUnmodifiableListView) return _nextSteps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_nextSteps);
  }

  @override
  final DateTime generatedAt;
  @override
  final String generatedBy;

  @override
  String toString() {
    return 'ParentReport(id: $id, studentId: $studentId, studentName: $studentName, assessmentId: $assessmentId, assessmentTitle: $assessmentTitle, className: $className, header: $header, summary: $summary, keyStrengths: $keyStrengths, areasForImprovement: $areasForImprovement, atHomeSuggestions: $atHomeSuggestions, teacherMessage: $teacherMessage, nextSteps: $nextSteps, generatedAt: $generatedAt, generatedBy: $generatedBy)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParentReportImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.studentName, studentName) ||
                other.studentName == studentName) &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.assessmentTitle, assessmentTitle) ||
                other.assessmentTitle == assessmentTitle) &&
            (identical(other.className, className) ||
                other.className == className) &&
            (identical(other.header, header) || other.header == header) &&
            (identical(other.summary, summary) || other.summary == summary) &&
            const DeepCollectionEquality()
                .equals(other._keyStrengths, _keyStrengths) &&
            const DeepCollectionEquality()
                .equals(other._areasForImprovement, _areasForImprovement) &&
            const DeepCollectionEquality()
                .equals(other._atHomeSuggestions, _atHomeSuggestions) &&
            (identical(other.teacherMessage, teacherMessage) ||
                other.teacherMessage == teacherMessage) &&
            const DeepCollectionEquality()
                .equals(other._nextSteps, _nextSteps) &&
            (identical(other.generatedAt, generatedAt) ||
                other.generatedAt == generatedAt) &&
            (identical(other.generatedBy, generatedBy) ||
                other.generatedBy == generatedBy));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      studentId,
      studentName,
      assessmentId,
      assessmentTitle,
      className,
      header,
      summary,
      const DeepCollectionEquality().hash(_keyStrengths),
      const DeepCollectionEquality().hash(_areasForImprovement),
      const DeepCollectionEquality().hash(_atHomeSuggestions),
      teacherMessage,
      const DeepCollectionEquality().hash(_nextSteps),
      generatedAt,
      generatedBy);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ParentReportImplCopyWith<_$ParentReportImpl> get copyWith =>
      __$$ParentReportImplCopyWithImpl<_$ParentReportImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ParentReportImplToJson(
      this,
    );
  }
}

abstract class _ParentReport implements ParentReport {
  const factory _ParentReport(
      {required final String id,
      required final String studentId,
      required final String studentName,
      required final String assessmentId,
      required final String assessmentTitle,
      required final String className,
      required final ReportHeader header,
      required final ParentPerformanceSummary summary,
      required final List<String> keyStrengths,
      required final List<String> areasForImprovement,
      required final List<String> atHomeSuggestions,
      required final String teacherMessage,
      required final List<ActionableRecommendation> nextSteps,
      required final DateTime generatedAt,
      required final String generatedBy}) = _$ParentReportImpl;

  factory _ParentReport.fromJson(Map<String, dynamic> json) =
      _$ParentReportImpl.fromJson;

  @override
  String get id;
  @override
  String get studentId;
  @override
  String get studentName;
  @override
  String get assessmentId;
  @override
  String get assessmentTitle;
  @override
  String get className;
  @override
  ReportHeader get header;
  @override
  ParentPerformanceSummary get summary;
  @override
  List<String> get keyStrengths;
  @override
  List<String> get areasForImprovement;
  @override
  List<String> get atHomeSuggestions;
  @override
  String get teacherMessage;
  @override
  List<ActionableRecommendation> get nextSteps;
  @override
  DateTime get generatedAt;
  @override
  String get generatedBy;
  @override
  @JsonKey(ignore: true)
  _$$ParentReportImplCopyWith<_$ParentReportImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ParentPerformanceSummary _$ParentPerformanceSummaryFromJson(
    Map<String, dynamic> json) {
  return _ParentPerformanceSummary.fromJson(json);
}

/// @nodoc
mixin _$ParentPerformanceSummary {
  int get totalScore => throw _privateConstructorUsedError;
  int get maxScore => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  String get grade => throw _privateConstructorUsedError;
  int get classRank => throw _privateConstructorUsedError;
  int get totalStudents => throw _privateConstructorUsedError;
  String get simpleSummary => throw _privateConstructorUsedError;
  String get performanceLevel => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ParentPerformanceSummaryCopyWith<ParentPerformanceSummary> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParentPerformanceSummaryCopyWith<$Res> {
  factory $ParentPerformanceSummaryCopyWith(ParentPerformanceSummary value,
          $Res Function(ParentPerformanceSummary) then) =
      _$ParentPerformanceSummaryCopyWithImpl<$Res, ParentPerformanceSummary>;
  @useResult
  $Res call(
      {int totalScore,
      int maxScore,
      double percentage,
      String grade,
      int classRank,
      int totalStudents,
      String simpleSummary,
      String performanceLevel});
}

/// @nodoc
class _$ParentPerformanceSummaryCopyWithImpl<$Res,
        $Val extends ParentPerformanceSummary>
    implements $ParentPerformanceSummaryCopyWith<$Res> {
  _$ParentPerformanceSummaryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalScore = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? grade = null,
    Object? classRank = null,
    Object? totalStudents = null,
    Object? simpleSummary = null,
    Object? performanceLevel = null,
  }) {
    return _then(_value.copyWith(
      totalScore: null == totalScore
          ? _value.totalScore
          : totalScore // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      classRank: null == classRank
          ? _value.classRank
          : classRank // ignore: cast_nullable_to_non_nullable
              as int,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      simpleSummary: null == simpleSummary
          ? _value.simpleSummary
          : simpleSummary // ignore: cast_nullable_to_non_nullable
              as String,
      performanceLevel: null == performanceLevel
          ? _value.performanceLevel
          : performanceLevel // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ParentPerformanceSummaryImplCopyWith<$Res>
    implements $ParentPerformanceSummaryCopyWith<$Res> {
  factory _$$ParentPerformanceSummaryImplCopyWith(
          _$ParentPerformanceSummaryImpl value,
          $Res Function(_$ParentPerformanceSummaryImpl) then) =
      __$$ParentPerformanceSummaryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int totalScore,
      int maxScore,
      double percentage,
      String grade,
      int classRank,
      int totalStudents,
      String simpleSummary,
      String performanceLevel});
}

/// @nodoc
class __$$ParentPerformanceSummaryImplCopyWithImpl<$Res>
    extends _$ParentPerformanceSummaryCopyWithImpl<$Res,
        _$ParentPerformanceSummaryImpl>
    implements _$$ParentPerformanceSummaryImplCopyWith<$Res> {
  __$$ParentPerformanceSummaryImplCopyWithImpl(
      _$ParentPerformanceSummaryImpl _value,
      $Res Function(_$ParentPerformanceSummaryImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalScore = null,
    Object? maxScore = null,
    Object? percentage = null,
    Object? grade = null,
    Object? classRank = null,
    Object? totalStudents = null,
    Object? simpleSummary = null,
    Object? performanceLevel = null,
  }) {
    return _then(_$ParentPerformanceSummaryImpl(
      totalScore: null == totalScore
          ? _value.totalScore
          : totalScore // ignore: cast_nullable_to_non_nullable
              as int,
      maxScore: null == maxScore
          ? _value.maxScore
          : maxScore // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      grade: null == grade
          ? _value.grade
          : grade // ignore: cast_nullable_to_non_nullable
              as String,
      classRank: null == classRank
          ? _value.classRank
          : classRank // ignore: cast_nullable_to_non_nullable
              as int,
      totalStudents: null == totalStudents
          ? _value.totalStudents
          : totalStudents // ignore: cast_nullable_to_non_nullable
              as int,
      simpleSummary: null == simpleSummary
          ? _value.simpleSummary
          : simpleSummary // ignore: cast_nullable_to_non_nullable
              as String,
      performanceLevel: null == performanceLevel
          ? _value.performanceLevel
          : performanceLevel // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ParentPerformanceSummaryImpl implements _ParentPerformanceSummary {
  const _$ParentPerformanceSummaryImpl(
      {required this.totalScore,
      required this.maxScore,
      required this.percentage,
      required this.grade,
      required this.classRank,
      required this.totalStudents,
      required this.simpleSummary,
      required this.performanceLevel});

  factory _$ParentPerformanceSummaryImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParentPerformanceSummaryImplFromJson(json);

  @override
  final int totalScore;
  @override
  final int maxScore;
  @override
  final double percentage;
  @override
  final String grade;
  @override
  final int classRank;
  @override
  final int totalStudents;
  @override
  final String simpleSummary;
  @override
  final String performanceLevel;

  @override
  String toString() {
    return 'ParentPerformanceSummary(totalScore: $totalScore, maxScore: $maxScore, percentage: $percentage, grade: $grade, classRank: $classRank, totalStudents: $totalStudents, simpleSummary: $simpleSummary, performanceLevel: $performanceLevel)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParentPerformanceSummaryImpl &&
            (identical(other.totalScore, totalScore) ||
                other.totalScore == totalScore) &&
            (identical(other.maxScore, maxScore) ||
                other.maxScore == maxScore) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.grade, grade) || other.grade == grade) &&
            (identical(other.classRank, classRank) ||
                other.classRank == classRank) &&
            (identical(other.totalStudents, totalStudents) ||
                other.totalStudents == totalStudents) &&
            (identical(other.simpleSummary, simpleSummary) ||
                other.simpleSummary == simpleSummary) &&
            (identical(other.performanceLevel, performanceLevel) ||
                other.performanceLevel == performanceLevel));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, totalScore, maxScore, percentage,
      grade, classRank, totalStudents, simpleSummary, performanceLevel);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ParentPerformanceSummaryImplCopyWith<_$ParentPerformanceSummaryImpl>
      get copyWith => __$$ParentPerformanceSummaryImplCopyWithImpl<
          _$ParentPerformanceSummaryImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ParentPerformanceSummaryImplToJson(
      this,
    );
  }
}

abstract class _ParentPerformanceSummary implements ParentPerformanceSummary {
  const factory _ParentPerformanceSummary(
      {required final int totalScore,
      required final int maxScore,
      required final double percentage,
      required final String grade,
      required final int classRank,
      required final int totalStudents,
      required final String simpleSummary,
      required final String performanceLevel}) = _$ParentPerformanceSummaryImpl;

  factory _ParentPerformanceSummary.fromJson(Map<String, dynamic> json) =
      _$ParentPerformanceSummaryImpl.fromJson;

  @override
  int get totalScore;
  @override
  int get maxScore;
  @override
  double get percentage;
  @override
  String get grade;
  @override
  int get classRank;
  @override
  int get totalStudents;
  @override
  String get simpleSummary;
  @override
  String get performanceLevel;
  @override
  @JsonKey(ignore: true)
  _$$ParentPerformanceSummaryImplCopyWith<_$ParentPerformanceSummaryImpl>
      get copyWith => throw _privateConstructorUsedError;
}
