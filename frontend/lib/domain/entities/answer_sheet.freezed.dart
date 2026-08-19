// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'answer_sheet.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

AnswerSheet _$AnswerSheetFromJson(Map<String, dynamic> json) {
  return _AnswerSheet.fromJson(json);
}

/// @nodoc
mixin _$AnswerSheet {
  String get id => throw _privateConstructorUsedError;
  String get assessmentId => throw _privateConstructorUsedError;
  String get studentId => throw _privateConstructorUsedError;
  String get studentName => throw _privateConstructorUsedError;
  String get rollNumber => throw _privateConstructorUsedError;
  List<ScannedPage> get pages => throw _privateConstructorUsedError;
  ScanMetadata get scanMetadata => throw _privateConstructorUsedError;
  List<QuestionResponse> get responses => throw _privateConstructorUsedError;
  AnswerSheetStatus get status => throw _privateConstructorUsedError;
  DateTime get submittedAt => throw _privateConstructorUsedError;
  DateTime get scannedAt => throw _privateConstructorUsedError;
  DateTime? get evaluatedAt => throw _privateConstructorUsedError;
  Map<String, dynamic> get metadata => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AnswerSheetCopyWith<AnswerSheet> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AnswerSheetCopyWith<$Res> {
  factory $AnswerSheetCopyWith(
          AnswerSheet value, $Res Function(AnswerSheet) then) =
      _$AnswerSheetCopyWithImpl<$Res, AnswerSheet>;
  @useResult
  $Res call(
      {String id,
      String assessmentId,
      String studentId,
      String studentName,
      String rollNumber,
      List<ScannedPage> pages,
      ScanMetadata scanMetadata,
      List<QuestionResponse> responses,
      AnswerSheetStatus status,
      DateTime submittedAt,
      DateTime scannedAt,
      DateTime? evaluatedAt,
      Map<String, dynamic> metadata});

  $ScanMetadataCopyWith<$Res> get scanMetadata;
}

/// @nodoc
class _$AnswerSheetCopyWithImpl<$Res, $Val extends AnswerSheet>
    implements $AnswerSheetCopyWith<$Res> {
  _$AnswerSheetCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? assessmentId = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? pages = null,
    Object? scanMetadata = null,
    Object? responses = null,
    Object? status = null,
    Object? submittedAt = null,
    Object? scannedAt = null,
    Object? evaluatedAt = freezed,
    Object? metadata = null,
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
      pages: null == pages
          ? _value.pages
          : pages // ignore: cast_nullable_to_non_nullable
              as List<ScannedPage>,
      scanMetadata: null == scanMetadata
          ? _value.scanMetadata
          : scanMetadata // ignore: cast_nullable_to_non_nullable
              as ScanMetadata,
      responses: null == responses
          ? _value.responses
          : responses // ignore: cast_nullable_to_non_nullable
              as List<QuestionResponse>,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as AnswerSheetStatus,
      submittedAt: null == submittedAt
          ? _value.submittedAt
          : submittedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      scannedAt: null == scannedAt
          ? _value.scannedAt
          : scannedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      evaluatedAt: freezed == evaluatedAt
          ? _value.evaluatedAt
          : evaluatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ScanMetadataCopyWith<$Res> get scanMetadata {
    return $ScanMetadataCopyWith<$Res>(_value.scanMetadata, (value) {
      return _then(_value.copyWith(scanMetadata: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AnswerSheetImplCopyWith<$Res>
    implements $AnswerSheetCopyWith<$Res> {
  factory _$$AnswerSheetImplCopyWith(
          _$AnswerSheetImpl value, $Res Function(_$AnswerSheetImpl) then) =
      __$$AnswerSheetImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String assessmentId,
      String studentId,
      String studentName,
      String rollNumber,
      List<ScannedPage> pages,
      ScanMetadata scanMetadata,
      List<QuestionResponse> responses,
      AnswerSheetStatus status,
      DateTime submittedAt,
      DateTime scannedAt,
      DateTime? evaluatedAt,
      Map<String, dynamic> metadata});

  @override
  $ScanMetadataCopyWith<$Res> get scanMetadata;
}

/// @nodoc
class __$$AnswerSheetImplCopyWithImpl<$Res>
    extends _$AnswerSheetCopyWithImpl<$Res, _$AnswerSheetImpl>
    implements _$$AnswerSheetImplCopyWith<$Res> {
  __$$AnswerSheetImplCopyWithImpl(
      _$AnswerSheetImpl _value, $Res Function(_$AnswerSheetImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? assessmentId = null,
    Object? studentId = null,
    Object? studentName = null,
    Object? rollNumber = null,
    Object? pages = null,
    Object? scanMetadata = null,
    Object? responses = null,
    Object? status = null,
    Object? submittedAt = null,
    Object? scannedAt = null,
    Object? evaluatedAt = freezed,
    Object? metadata = null,
  }) {
    return _then(_$AnswerSheetImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      assessmentId: null == assessmentId
          ? _value.assessmentId
          : assessmentId // ignore: cast_nullable_to_non_nullable
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
      pages: null == pages
          ? _value._pages
          : pages // ignore: cast_nullable_to_non_nullable
              as List<ScannedPage>,
      scanMetadata: null == scanMetadata
          ? _value.scanMetadata
          : scanMetadata // ignore: cast_nullable_to_non_nullable
              as ScanMetadata,
      responses: null == responses
          ? _value._responses
          : responses // ignore: cast_nullable_to_non_nullable
              as List<QuestionResponse>,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as AnswerSheetStatus,
      submittedAt: null == submittedAt
          ? _value.submittedAt
          : submittedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      scannedAt: null == scannedAt
          ? _value.scannedAt
          : scannedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      evaluatedAt: freezed == evaluatedAt
          ? _value.evaluatedAt
          : evaluatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      metadata: null == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AnswerSheetImpl implements _AnswerSheet {
  const _$AnswerSheetImpl(
      {required this.id,
      required this.assessmentId,
      required this.studentId,
      required this.studentName,
      required this.rollNumber,
      required final List<ScannedPage> pages,
      required this.scanMetadata,
      required final List<QuestionResponse> responses,
      required this.status,
      required this.submittedAt,
      required this.scannedAt,
      this.evaluatedAt,
      final Map<String, dynamic> metadata = const {}})
      : _pages = pages,
        _responses = responses,
        _metadata = metadata;

  factory _$AnswerSheetImpl.fromJson(Map<String, dynamic> json) =>
      _$$AnswerSheetImplFromJson(json);

  @override
  final String id;
  @override
  final String assessmentId;
  @override
  final String studentId;
  @override
  final String studentName;
  @override
  final String rollNumber;
  final List<ScannedPage> _pages;
  @override
  List<ScannedPage> get pages {
    if (_pages is EqualUnmodifiableListView) return _pages;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_pages);
  }

  @override
  final ScanMetadata scanMetadata;
  final List<QuestionResponse> _responses;
  @override
  List<QuestionResponse> get responses {
    if (_responses is EqualUnmodifiableListView) return _responses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_responses);
  }

  @override
  final AnswerSheetStatus status;
  @override
  final DateTime submittedAt;
  @override
  final DateTime scannedAt;
  @override
  final DateTime? evaluatedAt;
  final Map<String, dynamic> _metadata;
  @override
  @JsonKey()
  Map<String, dynamic> get metadata {
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_metadata);
  }

  @override
  String toString() {
    return 'AnswerSheet(id: $id, assessmentId: $assessmentId, studentId: $studentId, studentName: $studentName, rollNumber: $rollNumber, pages: $pages, scanMetadata: $scanMetadata, responses: $responses, status: $status, submittedAt: $submittedAt, scannedAt: $scannedAt, evaluatedAt: $evaluatedAt, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AnswerSheetImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.assessmentId, assessmentId) ||
                other.assessmentId == assessmentId) &&
            (identical(other.studentId, studentId) ||
                other.studentId == studentId) &&
            (identical(other.studentName, studentName) ||
                other.studentName == studentName) &&
            (identical(other.rollNumber, rollNumber) ||
                other.rollNumber == rollNumber) &&
            const DeepCollectionEquality().equals(other._pages, _pages) &&
            (identical(other.scanMetadata, scanMetadata) ||
                other.scanMetadata == scanMetadata) &&
            const DeepCollectionEquality()
                .equals(other._responses, _responses) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.submittedAt, submittedAt) ||
                other.submittedAt == submittedAt) &&
            (identical(other.scannedAt, scannedAt) ||
                other.scannedAt == scannedAt) &&
            (identical(other.evaluatedAt, evaluatedAt) ||
                other.evaluatedAt == evaluatedAt) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      assessmentId,
      studentId,
      studentName,
      rollNumber,
      const DeepCollectionEquality().hash(_pages),
      scanMetadata,
      const DeepCollectionEquality().hash(_responses),
      status,
      submittedAt,
      scannedAt,
      evaluatedAt,
      const DeepCollectionEquality().hash(_metadata));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AnswerSheetImplCopyWith<_$AnswerSheetImpl> get copyWith =>
      __$$AnswerSheetImplCopyWithImpl<_$AnswerSheetImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AnswerSheetImplToJson(
      this,
    );
  }
}

abstract class _AnswerSheet implements AnswerSheet {
  const factory _AnswerSheet(
      {required final String id,
      required final String assessmentId,
      required final String studentId,
      required final String studentName,
      required final String rollNumber,
      required final List<ScannedPage> pages,
      required final ScanMetadata scanMetadata,
      required final List<QuestionResponse> responses,
      required final AnswerSheetStatus status,
      required final DateTime submittedAt,
      required final DateTime scannedAt,
      final DateTime? evaluatedAt,
      final Map<String, dynamic> metadata}) = _$AnswerSheetImpl;

  factory _AnswerSheet.fromJson(Map<String, dynamic> json) =
      _$AnswerSheetImpl.fromJson;

  @override
  String get id;
  @override
  String get assessmentId;
  @override
  String get studentId;
  @override
  String get studentName;
  @override
  String get rollNumber;
  @override
  List<ScannedPage> get pages;
  @override
  ScanMetadata get scanMetadata;
  @override
  List<QuestionResponse> get responses;
  @override
  AnswerSheetStatus get status;
  @override
  DateTime get submittedAt;
  @override
  DateTime get scannedAt;
  @override
  DateTime? get evaluatedAt;
  @override
  Map<String, dynamic> get metadata;
  @override
  @JsonKey(ignore: true)
  _$$AnswerSheetImplCopyWith<_$AnswerSheetImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ScannedPage _$ScannedPageFromJson(Map<String, dynamic> json) {
  return _ScannedPage.fromJson(json);
}

/// @nodoc
mixin _$ScannedPage {
  int get pageNumber => throw _privateConstructorUsedError;
  String get imagePath => throw _privateConstructorUsedError;
  String get imageUrl => throw _privateConstructorUsedError;
  int get width => throw _privateConstructorUsedError;
  int get height => throw _privateConstructorUsedError;
  double get qualityScore => throw _privateConstructorUsedError;
  PageOrientation get orientation => throw _privateConstructorUsedError;
  List<QuestionSegment> get segments => throw _privateConstructorUsedError;
  Map<String, dynamic> get preprocessing => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ScannedPageCopyWith<ScannedPage> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ScannedPageCopyWith<$Res> {
  factory $ScannedPageCopyWith(
          ScannedPage value, $Res Function(ScannedPage) then) =
      _$ScannedPageCopyWithImpl<$Res, ScannedPage>;
  @useResult
  $Res call(
      {int pageNumber,
      String imagePath,
      String imageUrl,
      int width,
      int height,
      double qualityScore,
      PageOrientation orientation,
      List<QuestionSegment> segments,
      Map<String, dynamic> preprocessing});
}

/// @nodoc
class _$ScannedPageCopyWithImpl<$Res, $Val extends ScannedPage>
    implements $ScannedPageCopyWith<$Res> {
  _$ScannedPageCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pageNumber = null,
    Object? imagePath = null,
    Object? imageUrl = null,
    Object? width = null,
    Object? height = null,
    Object? qualityScore = null,
    Object? orientation = null,
    Object? segments = null,
    Object? preprocessing = null,
  }) {
    return _then(_value.copyWith(
      pageNumber: null == pageNumber
          ? _value.pageNumber
          : pageNumber // ignore: cast_nullable_to_non_nullable
              as int,
      imagePath: null == imagePath
          ? _value.imagePath
          : imagePath // ignore: cast_nullable_to_non_nullable
              as String,
      imageUrl: null == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String,
      width: null == width
          ? _value.width
          : width // ignore: cast_nullable_to_non_nullable
              as int,
      height: null == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as int,
      qualityScore: null == qualityScore
          ? _value.qualityScore
          : qualityScore // ignore: cast_nullable_to_non_nullable
              as double,
      orientation: null == orientation
          ? _value.orientation
          : orientation // ignore: cast_nullable_to_non_nullable
              as PageOrientation,
      segments: null == segments
          ? _value.segments
          : segments // ignore: cast_nullable_to_non_nullable
              as List<QuestionSegment>,
      preprocessing: null == preprocessing
          ? _value.preprocessing
          : preprocessing // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ScannedPageImplCopyWith<$Res>
    implements $ScannedPageCopyWith<$Res> {
  factory _$$ScannedPageImplCopyWith(
          _$ScannedPageImpl value, $Res Function(_$ScannedPageImpl) then) =
      __$$ScannedPageImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int pageNumber,
      String imagePath,
      String imageUrl,
      int width,
      int height,
      double qualityScore,
      PageOrientation orientation,
      List<QuestionSegment> segments,
      Map<String, dynamic> preprocessing});
}

/// @nodoc
class __$$ScannedPageImplCopyWithImpl<$Res>
    extends _$ScannedPageCopyWithImpl<$Res, _$ScannedPageImpl>
    implements _$$ScannedPageImplCopyWith<$Res> {
  __$$ScannedPageImplCopyWithImpl(
      _$ScannedPageImpl _value, $Res Function(_$ScannedPageImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pageNumber = null,
    Object? imagePath = null,
    Object? imageUrl = null,
    Object? width = null,
    Object? height = null,
    Object? qualityScore = null,
    Object? orientation = null,
    Object? segments = null,
    Object? preprocessing = null,
  }) {
    return _then(_$ScannedPageImpl(
      pageNumber: null == pageNumber
          ? _value.pageNumber
          : pageNumber // ignore: cast_nullable_to_non_nullable
              as int,
      imagePath: null == imagePath
          ? _value.imagePath
          : imagePath // ignore: cast_nullable_to_non_nullable
              as String,
      imageUrl: null == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String,
      width: null == width
          ? _value.width
          : width // ignore: cast_nullable_to_non_nullable
              as int,
      height: null == height
          ? _value.height
          : height // ignore: cast_nullable_to_non_nullable
              as int,
      qualityScore: null == qualityScore
          ? _value.qualityScore
          : qualityScore // ignore: cast_nullable_to_non_nullable
              as double,
      orientation: null == orientation
          ? _value.orientation
          : orientation // ignore: cast_nullable_to_non_nullable
              as PageOrientation,
      segments: null == segments
          ? _value._segments
          : segments // ignore: cast_nullable_to_non_nullable
              as List<QuestionSegment>,
      preprocessing: null == preprocessing
          ? _value._preprocessing
          : preprocessing // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ScannedPageImpl implements _ScannedPage {
  const _$ScannedPageImpl(
      {required this.pageNumber,
      required this.imagePath,
      required this.imageUrl,
      required this.width,
      required this.height,
      required this.qualityScore,
      required this.orientation,
      required final List<QuestionSegment> segments,
      final Map<String, dynamic> preprocessing = const {}})
      : _segments = segments,
        _preprocessing = preprocessing;

  factory _$ScannedPageImpl.fromJson(Map<String, dynamic> json) =>
      _$$ScannedPageImplFromJson(json);

  @override
  final int pageNumber;
  @override
  final String imagePath;
  @override
  final String imageUrl;
  @override
  final int width;
  @override
  final int height;
  @override
  final double qualityScore;
  @override
  final PageOrientation orientation;
  final List<QuestionSegment> _segments;
  @override
  List<QuestionSegment> get segments {
    if (_segments is EqualUnmodifiableListView) return _segments;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_segments);
  }

  final Map<String, dynamic> _preprocessing;
  @override
  @JsonKey()
  Map<String, dynamic> get preprocessing {
    if (_preprocessing is EqualUnmodifiableMapView) return _preprocessing;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_preprocessing);
  }

  @override
  String toString() {
    return 'ScannedPage(pageNumber: $pageNumber, imagePath: $imagePath, imageUrl: $imageUrl, width: $width, height: $height, qualityScore: $qualityScore, orientation: $orientation, segments: $segments, preprocessing: $preprocessing)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ScannedPageImpl &&
            (identical(other.pageNumber, pageNumber) ||
                other.pageNumber == pageNumber) &&
            (identical(other.imagePath, imagePath) ||
                other.imagePath == imagePath) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.width, width) || other.width == width) &&
            (identical(other.height, height) || other.height == height) &&
            (identical(other.qualityScore, qualityScore) ||
                other.qualityScore == qualityScore) &&
            (identical(other.orientation, orientation) ||
                other.orientation == orientation) &&
            const DeepCollectionEquality().equals(other._segments, _segments) &&
            const DeepCollectionEquality()
                .equals(other._preprocessing, _preprocessing));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      pageNumber,
      imagePath,
      imageUrl,
      width,
      height,
      qualityScore,
      orientation,
      const DeepCollectionEquality().hash(_segments),
      const DeepCollectionEquality().hash(_preprocessing));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ScannedPageImplCopyWith<_$ScannedPageImpl> get copyWith =>
      __$$ScannedPageImplCopyWithImpl<_$ScannedPageImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ScannedPageImplToJson(
      this,
    );
  }
}

abstract class _ScannedPage implements ScannedPage {
  const factory _ScannedPage(
      {required final int pageNumber,
      required final String imagePath,
      required final String imageUrl,
      required final int width,
      required final int height,
      required final double qualityScore,
      required final PageOrientation orientation,
      required final List<QuestionSegment> segments,
      final Map<String, dynamic> preprocessing}) = _$ScannedPageImpl;

  factory _ScannedPage.fromJson(Map<String, dynamic> json) =
      _$ScannedPageImpl.fromJson;

  @override
  int get pageNumber;
  @override
  String get imagePath;
  @override
  String get imageUrl;
  @override
  int get width;
  @override
  int get height;
  @override
  double get qualityScore;
  @override
  PageOrientation get orientation;
  @override
  List<QuestionSegment> get segments;
  @override
  Map<String, dynamic> get preprocessing;
  @override
  @JsonKey(ignore: true)
  _$$ScannedPageImplCopyWith<_$ScannedPageImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionSegment _$QuestionSegmentFromJson(Map<String, dynamic> json) {
  return _QuestionSegment.fromJson(json);
}

/// @nodoc
mixin _$QuestionSegment {
  String get id => throw _privateConstructorUsedError;
  String get questionId => throw _privateConstructorUsedError;
  int get questionNumber => throw _privateConstructorUsedError;
  SegmentType get type => throw _privateConstructorUsedError;
  List<Point> get boundingBox => throw _privateConstructorUsedError;
  String get imagePath => throw _privateConstructorUsedError;
  String get imageUrl => throw _privateConstructorUsedError;
  String get ocrText => throw _privateConstructorUsedError;
  String get ocrTextLatex => throw _privateConstructorUsedError;
  double get ocrConfidence => throw _privateConstructorUsedError;
  double get visionConfidence => throw _privateConstructorUsedError;
  SegmentationStatus get status => throw _privateConstructorUsedError;
  List<String> get studentAnswerImages => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionSegmentCopyWith<QuestionSegment> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionSegmentCopyWith<$Res> {
  factory $QuestionSegmentCopyWith(
          QuestionSegment value, $Res Function(QuestionSegment) then) =
      _$QuestionSegmentCopyWithImpl<$Res, QuestionSegment>;
  @useResult
  $Res call(
      {String id,
      String questionId,
      int questionNumber,
      SegmentType type,
      List<Point> boundingBox,
      String imagePath,
      String imageUrl,
      String ocrText,
      String ocrTextLatex,
      double ocrConfidence,
      double visionConfidence,
      SegmentationStatus status,
      List<String> studentAnswerImages});
}

/// @nodoc
class _$QuestionSegmentCopyWithImpl<$Res, $Val extends QuestionSegment>
    implements $QuestionSegmentCopyWith<$Res> {
  _$QuestionSegmentCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? questionId = null,
    Object? questionNumber = null,
    Object? type = null,
    Object? boundingBox = null,
    Object? imagePath = null,
    Object? imageUrl = null,
    Object? ocrText = null,
    Object? ocrTextLatex = null,
    Object? ocrConfidence = null,
    Object? visionConfidence = null,
    Object? status = null,
    Object? studentAnswerImages = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as SegmentType,
      boundingBox: null == boundingBox
          ? _value.boundingBox
          : boundingBox // ignore: cast_nullable_to_non_nullable
              as List<Point>,
      imagePath: null == imagePath
          ? _value.imagePath
          : imagePath // ignore: cast_nullable_to_non_nullable
              as String,
      imageUrl: null == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String,
      ocrText: null == ocrText
          ? _value.ocrText
          : ocrText // ignore: cast_nullable_to_non_nullable
              as String,
      ocrTextLatex: null == ocrTextLatex
          ? _value.ocrTextLatex
          : ocrTextLatex // ignore: cast_nullable_to_non_nullable
              as String,
      ocrConfidence: null == ocrConfidence
          ? _value.ocrConfidence
          : ocrConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      visionConfidence: null == visionConfidence
          ? _value.visionConfidence
          : visionConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as SegmentationStatus,
      studentAnswerImages: null == studentAnswerImages
          ? _value.studentAnswerImages
          : studentAnswerImages // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuestionSegmentImplCopyWith<$Res>
    implements $QuestionSegmentCopyWith<$Res> {
  factory _$$QuestionSegmentImplCopyWith(_$QuestionSegmentImpl value,
          $Res Function(_$QuestionSegmentImpl) then) =
      __$$QuestionSegmentImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String questionId,
      int questionNumber,
      SegmentType type,
      List<Point> boundingBox,
      String imagePath,
      String imageUrl,
      String ocrText,
      String ocrTextLatex,
      double ocrConfidence,
      double visionConfidence,
      SegmentationStatus status,
      List<String> studentAnswerImages});
}

/// @nodoc
class __$$QuestionSegmentImplCopyWithImpl<$Res>
    extends _$QuestionSegmentCopyWithImpl<$Res, _$QuestionSegmentImpl>
    implements _$$QuestionSegmentImplCopyWith<$Res> {
  __$$QuestionSegmentImplCopyWithImpl(
      _$QuestionSegmentImpl _value, $Res Function(_$QuestionSegmentImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? questionId = null,
    Object? questionNumber = null,
    Object? type = null,
    Object? boundingBox = null,
    Object? imagePath = null,
    Object? imageUrl = null,
    Object? ocrText = null,
    Object? ocrTextLatex = null,
    Object? ocrConfidence = null,
    Object? visionConfidence = null,
    Object? status = null,
    Object? studentAnswerImages = null,
  }) {
    return _then(_$QuestionSegmentImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as SegmentType,
      boundingBox: null == boundingBox
          ? _value._boundingBox
          : boundingBox // ignore: cast_nullable_to_non_nullable
              as List<Point>,
      imagePath: null == imagePath
          ? _value.imagePath
          : imagePath // ignore: cast_nullable_to_non_nullable
              as String,
      imageUrl: null == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String,
      ocrText: null == ocrText
          ? _value.ocrText
          : ocrText // ignore: cast_nullable_to_non_nullable
              as String,
      ocrTextLatex: null == ocrTextLatex
          ? _value.ocrTextLatex
          : ocrTextLatex // ignore: cast_nullable_to_non_nullable
              as String,
      ocrConfidence: null == ocrConfidence
          ? _value.ocrConfidence
          : ocrConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      visionConfidence: null == visionConfidence
          ? _value.visionConfidence
          : visionConfidence // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as SegmentationStatus,
      studentAnswerImages: null == studentAnswerImages
          ? _value._studentAnswerImages
          : studentAnswerImages // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionSegmentImpl implements _QuestionSegment {
  const _$QuestionSegmentImpl(
      {required this.id,
      required this.questionId,
      required this.questionNumber,
      required this.type,
      required final List<Point> boundingBox,
      required this.imagePath,
      required this.imageUrl,
      required this.ocrText,
      required this.ocrTextLatex,
      required this.ocrConfidence,
      required this.visionConfidence,
      required this.status,
      final List<String> studentAnswerImages = const []})
      : _boundingBox = boundingBox,
        _studentAnswerImages = studentAnswerImages;

  factory _$QuestionSegmentImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionSegmentImplFromJson(json);

  @override
  final String id;
  @override
  final String questionId;
  @override
  final int questionNumber;
  @override
  final SegmentType type;
  final List<Point> _boundingBox;
  @override
  List<Point> get boundingBox {
    if (_boundingBox is EqualUnmodifiableListView) return _boundingBox;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_boundingBox);
  }

  @override
  final String imagePath;
  @override
  final String imageUrl;
  @override
  final String ocrText;
  @override
  final String ocrTextLatex;
  @override
  final double ocrConfidence;
  @override
  final double visionConfidence;
  @override
  final SegmentationStatus status;
  final List<String> _studentAnswerImages;
  @override
  @JsonKey()
  List<String> get studentAnswerImages {
    if (_studentAnswerImages is EqualUnmodifiableListView)
      return _studentAnswerImages;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_studentAnswerImages);
  }

  @override
  String toString() {
    return 'QuestionSegment(id: $id, questionId: $questionId, questionNumber: $questionNumber, type: $type, boundingBox: $boundingBox, imagePath: $imagePath, imageUrl: $imageUrl, ocrText: $ocrText, ocrTextLatex: $ocrTextLatex, ocrConfidence: $ocrConfidence, visionConfidence: $visionConfidence, status: $status, studentAnswerImages: $studentAnswerImages)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionSegmentImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.questionNumber, questionNumber) ||
                other.questionNumber == questionNumber) &&
            (identical(other.type, type) || other.type == type) &&
            const DeepCollectionEquality()
                .equals(other._boundingBox, _boundingBox) &&
            (identical(other.imagePath, imagePath) ||
                other.imagePath == imagePath) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.ocrText, ocrText) || other.ocrText == ocrText) &&
            (identical(other.ocrTextLatex, ocrTextLatex) ||
                other.ocrTextLatex == ocrTextLatex) &&
            (identical(other.ocrConfidence, ocrConfidence) ||
                other.ocrConfidence == ocrConfidence) &&
            (identical(other.visionConfidence, visionConfidence) ||
                other.visionConfidence == visionConfidence) &&
            (identical(other.status, status) || other.status == status) &&
            const DeepCollectionEquality()
                .equals(other._studentAnswerImages, _studentAnswerImages));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      questionId,
      questionNumber,
      type,
      const DeepCollectionEquality().hash(_boundingBox),
      imagePath,
      imageUrl,
      ocrText,
      ocrTextLatex,
      ocrConfidence,
      visionConfidence,
      status,
      const DeepCollectionEquality().hash(_studentAnswerImages));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionSegmentImplCopyWith<_$QuestionSegmentImpl> get copyWith =>
      __$$QuestionSegmentImplCopyWithImpl<_$QuestionSegmentImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionSegmentImplToJson(
      this,
    );
  }
}

abstract class _QuestionSegment implements QuestionSegment {
  const factory _QuestionSegment(
      {required final String id,
      required final String questionId,
      required final int questionNumber,
      required final SegmentType type,
      required final List<Point> boundingBox,
      required final String imagePath,
      required final String imageUrl,
      required final String ocrText,
      required final String ocrTextLatex,
      required final double ocrConfidence,
      required final double visionConfidence,
      required final SegmentationStatus status,
      final List<String> studentAnswerImages}) = _$QuestionSegmentImpl;

  factory _QuestionSegment.fromJson(Map<String, dynamic> json) =
      _$QuestionSegmentImpl.fromJson;

  @override
  String get id;
  @override
  String get questionId;
  @override
  int get questionNumber;
  @override
  SegmentType get type;
  @override
  List<Point> get boundingBox;
  @override
  String get imagePath;
  @override
  String get imageUrl;
  @override
  String get ocrText;
  @override
  String get ocrTextLatex;
  @override
  double get ocrConfidence;
  @override
  double get visionConfidence;
  @override
  SegmentationStatus get status;
  @override
  List<String> get studentAnswerImages;
  @override
  @JsonKey(ignore: true)
  _$$QuestionSegmentImplCopyWith<_$QuestionSegmentImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ScanMetadata _$ScanMetadataFromJson(Map<String, dynamic> json) {
  return _ScanMetadata.fromJson(json);
}

/// @nodoc
mixin _$ScanMetadata {
  String get deviceId => throw _privateConstructorUsedError;
  String get appVersion => throw _privateConstructorUsedError;
  int get totalPages => throw _privateConstructorUsedError;
  double get avgQualityScore => throw _privateConstructorUsedError;
  int get scanDurationMs => throw _privateConstructorUsedError;
  LightingCondition get lighting => throw _privateConstructorUsedError;
  List<String> get warnings => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ScanMetadataCopyWith<ScanMetadata> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ScanMetadataCopyWith<$Res> {
  factory $ScanMetadataCopyWith(
          ScanMetadata value, $Res Function(ScanMetadata) then) =
      _$ScanMetadataCopyWithImpl<$Res, ScanMetadata>;
  @useResult
  $Res call(
      {String deviceId,
      String appVersion,
      int totalPages,
      double avgQualityScore,
      int scanDurationMs,
      LightingCondition lighting,
      List<String> warnings});
}

/// @nodoc
class _$ScanMetadataCopyWithImpl<$Res, $Val extends ScanMetadata>
    implements $ScanMetadataCopyWith<$Res> {
  _$ScanMetadataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? deviceId = null,
    Object? appVersion = null,
    Object? totalPages = null,
    Object? avgQualityScore = null,
    Object? scanDurationMs = null,
    Object? lighting = null,
    Object? warnings = null,
  }) {
    return _then(_value.copyWith(
      deviceId: null == deviceId
          ? _value.deviceId
          : deviceId // ignore: cast_nullable_to_non_nullable
              as String,
      appVersion: null == appVersion
          ? _value.appVersion
          : appVersion // ignore: cast_nullable_to_non_nullable
              as String,
      totalPages: null == totalPages
          ? _value.totalPages
          : totalPages // ignore: cast_nullable_to_non_nullable
              as int,
      avgQualityScore: null == avgQualityScore
          ? _value.avgQualityScore
          : avgQualityScore // ignore: cast_nullable_to_non_nullable
              as double,
      scanDurationMs: null == scanDurationMs
          ? _value.scanDurationMs
          : scanDurationMs // ignore: cast_nullable_to_non_nullable
              as int,
      lighting: null == lighting
          ? _value.lighting
          : lighting // ignore: cast_nullable_to_non_nullable
              as LightingCondition,
      warnings: null == warnings
          ? _value.warnings
          : warnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ScanMetadataImplCopyWith<$Res>
    implements $ScanMetadataCopyWith<$Res> {
  factory _$$ScanMetadataImplCopyWith(
          _$ScanMetadataImpl value, $Res Function(_$ScanMetadataImpl) then) =
      __$$ScanMetadataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String deviceId,
      String appVersion,
      int totalPages,
      double avgQualityScore,
      int scanDurationMs,
      LightingCondition lighting,
      List<String> warnings});
}

/// @nodoc
class __$$ScanMetadataImplCopyWithImpl<$Res>
    extends _$ScanMetadataCopyWithImpl<$Res, _$ScanMetadataImpl>
    implements _$$ScanMetadataImplCopyWith<$Res> {
  __$$ScanMetadataImplCopyWithImpl(
      _$ScanMetadataImpl _value, $Res Function(_$ScanMetadataImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? deviceId = null,
    Object? appVersion = null,
    Object? totalPages = null,
    Object? avgQualityScore = null,
    Object? scanDurationMs = null,
    Object? lighting = null,
    Object? warnings = null,
  }) {
    return _then(_$ScanMetadataImpl(
      deviceId: null == deviceId
          ? _value.deviceId
          : deviceId // ignore: cast_nullable_to_non_nullable
              as String,
      appVersion: null == appVersion
          ? _value.appVersion
          : appVersion // ignore: cast_nullable_to_non_nullable
              as String,
      totalPages: null == totalPages
          ? _value.totalPages
          : totalPages // ignore: cast_nullable_to_non_nullable
              as int,
      avgQualityScore: null == avgQualityScore
          ? _value.avgQualityScore
          : avgQualityScore // ignore: cast_nullable_to_non_nullable
              as double,
      scanDurationMs: null == scanDurationMs
          ? _value.scanDurationMs
          : scanDurationMs // ignore: cast_nullable_to_non_nullable
              as int,
      lighting: null == lighting
          ? _value.lighting
          : lighting // ignore: cast_nullable_to_non_nullable
              as LightingCondition,
      warnings: null == warnings
          ? _value._warnings
          : warnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ScanMetadataImpl implements _ScanMetadata {
  const _$ScanMetadataImpl(
      {required this.deviceId,
      required this.appVersion,
      required this.totalPages,
      required this.avgQualityScore,
      required this.scanDurationMs,
      required this.lighting,
      final List<String> warnings = const []})
      : _warnings = warnings;

  factory _$ScanMetadataImpl.fromJson(Map<String, dynamic> json) =>
      _$$ScanMetadataImplFromJson(json);

  @override
  final String deviceId;
  @override
  final String appVersion;
  @override
  final int totalPages;
  @override
  final double avgQualityScore;
  @override
  final int scanDurationMs;
  @override
  final LightingCondition lighting;
  final List<String> _warnings;
  @override
  @JsonKey()
  List<String> get warnings {
    if (_warnings is EqualUnmodifiableListView) return _warnings;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_warnings);
  }

  @override
  String toString() {
    return 'ScanMetadata(deviceId: $deviceId, appVersion: $appVersion, totalPages: $totalPages, avgQualityScore: $avgQualityScore, scanDurationMs: $scanDurationMs, lighting: $lighting, warnings: $warnings)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ScanMetadataImpl &&
            (identical(other.deviceId, deviceId) ||
                other.deviceId == deviceId) &&
            (identical(other.appVersion, appVersion) ||
                other.appVersion == appVersion) &&
            (identical(other.totalPages, totalPages) ||
                other.totalPages == totalPages) &&
            (identical(other.avgQualityScore, avgQualityScore) ||
                other.avgQualityScore == avgQualityScore) &&
            (identical(other.scanDurationMs, scanDurationMs) ||
                other.scanDurationMs == scanDurationMs) &&
            (identical(other.lighting, lighting) ||
                other.lighting == lighting) &&
            const DeepCollectionEquality().equals(other._warnings, _warnings));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      deviceId,
      appVersion,
      totalPages,
      avgQualityScore,
      scanDurationMs,
      lighting,
      const DeepCollectionEquality().hash(_warnings));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ScanMetadataImplCopyWith<_$ScanMetadataImpl> get copyWith =>
      __$$ScanMetadataImplCopyWithImpl<_$ScanMetadataImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ScanMetadataImplToJson(
      this,
    );
  }
}

abstract class _ScanMetadata implements ScanMetadata {
  const factory _ScanMetadata(
      {required final String deviceId,
      required final String appVersion,
      required final int totalPages,
      required final double avgQualityScore,
      required final int scanDurationMs,
      required final LightingCondition lighting,
      final List<String> warnings}) = _$ScanMetadataImpl;

  factory _ScanMetadata.fromJson(Map<String, dynamic> json) =
      _$ScanMetadataImpl.fromJson;

  @override
  String get deviceId;
  @override
  String get appVersion;
  @override
  int get totalPages;
  @override
  double get avgQualityScore;
  @override
  int get scanDurationMs;
  @override
  LightingCondition get lighting;
  @override
  List<String> get warnings;
  @override
  @JsonKey(ignore: true)
  _$$ScanMetadataImplCopyWith<_$ScanMetadataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuestionResponse _$QuestionResponseFromJson(Map<String, dynamic> json) {
  return _QuestionResponse.fromJson(json);
}

/// @nodoc
mixin _$QuestionResponse {
  String get questionId => throw _privateConstructorUsedError;
  int get questionNumber => throw _privateConstructorUsedError;
  String get studentAnswer => throw _privateConstructorUsedError;
  String get studentAnswerLatex => throw _privateConstructorUsedError;
  List<String> get studentAnswerImages => throw _privateConstructorUsedError;
  EvaluationResult? get evaluation => throw _privateConstructorUsedError;
  EvaluationStatus get evaluationStatus => throw _privateConstructorUsedError;
  DateTime? get evaluatedAt => throw _privateConstructorUsedError;
  String? get teacherComment => throw _privateConstructorUsedError;
  int? get teacherAdjustedMarks => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuestionResponseCopyWith<QuestionResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuestionResponseCopyWith<$Res> {
  factory $QuestionResponseCopyWith(
          QuestionResponse value, $Res Function(QuestionResponse) then) =
      _$QuestionResponseCopyWithImpl<$Res, QuestionResponse>;
  @useResult
  $Res call(
      {String questionId,
      int questionNumber,
      String studentAnswer,
      String studentAnswerLatex,
      List<String> studentAnswerImages,
      EvaluationResult? evaluation,
      EvaluationStatus evaluationStatus,
      DateTime? evaluatedAt,
      String? teacherComment,
      int? teacherAdjustedMarks});

  $EvaluationResultCopyWith<$Res>? get evaluation;
}

/// @nodoc
class _$QuestionResponseCopyWithImpl<$Res, $Val extends QuestionResponse>
    implements $QuestionResponseCopyWith<$Res> {
  _$QuestionResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? questionNumber = null,
    Object? studentAnswer = null,
    Object? studentAnswerLatex = null,
    Object? studentAnswerImages = null,
    Object? evaluation = freezed,
    Object? evaluationStatus = null,
    Object? evaluatedAt = freezed,
    Object? teacherComment = freezed,
    Object? teacherAdjustedMarks = freezed,
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
      studentAnswer: null == studentAnswer
          ? _value.studentAnswer
          : studentAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerLatex: null == studentAnswerLatex
          ? _value.studentAnswerLatex
          : studentAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerImages: null == studentAnswerImages
          ? _value.studentAnswerImages
          : studentAnswerImages // ignore: cast_nullable_to_non_nullable
              as List<String>,
      evaluation: freezed == evaluation
          ? _value.evaluation
          : evaluation // ignore: cast_nullable_to_non_nullable
              as EvaluationResult?,
      evaluationStatus: null == evaluationStatus
          ? _value.evaluationStatus
          : evaluationStatus // ignore: cast_nullable_to_non_nullable
              as EvaluationStatus,
      evaluatedAt: freezed == evaluatedAt
          ? _value.evaluatedAt
          : evaluatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      teacherComment: freezed == teacherComment
          ? _value.teacherComment
          : teacherComment // ignore: cast_nullable_to_non_nullable
              as String?,
      teacherAdjustedMarks: freezed == teacherAdjustedMarks
          ? _value.teacherAdjustedMarks
          : teacherAdjustedMarks // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $EvaluationResultCopyWith<$Res>? get evaluation {
    if (_value.evaluation == null) {
      return null;
    }

    return $EvaluationResultCopyWith<$Res>(_value.evaluation!, (value) {
      return _then(_value.copyWith(evaluation: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$QuestionResponseImplCopyWith<$Res>
    implements $QuestionResponseCopyWith<$Res> {
  factory _$$QuestionResponseImplCopyWith(_$QuestionResponseImpl value,
          $Res Function(_$QuestionResponseImpl) then) =
      __$$QuestionResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String questionId,
      int questionNumber,
      String studentAnswer,
      String studentAnswerLatex,
      List<String> studentAnswerImages,
      EvaluationResult? evaluation,
      EvaluationStatus evaluationStatus,
      DateTime? evaluatedAt,
      String? teacherComment,
      int? teacherAdjustedMarks});

  @override
  $EvaluationResultCopyWith<$Res>? get evaluation;
}

/// @nodoc
class __$$QuestionResponseImplCopyWithImpl<$Res>
    extends _$QuestionResponseCopyWithImpl<$Res, _$QuestionResponseImpl>
    implements _$$QuestionResponseImplCopyWith<$Res> {
  __$$QuestionResponseImplCopyWithImpl(_$QuestionResponseImpl _value,
      $Res Function(_$QuestionResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? questionNumber = null,
    Object? studentAnswer = null,
    Object? studentAnswerLatex = null,
    Object? studentAnswerImages = null,
    Object? evaluation = freezed,
    Object? evaluationStatus = null,
    Object? evaluatedAt = freezed,
    Object? teacherComment = freezed,
    Object? teacherAdjustedMarks = freezed,
  }) {
    return _then(_$QuestionResponseImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      questionNumber: null == questionNumber
          ? _value.questionNumber
          : questionNumber // ignore: cast_nullable_to_non_nullable
              as int,
      studentAnswer: null == studentAnswer
          ? _value.studentAnswer
          : studentAnswer // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerLatex: null == studentAnswerLatex
          ? _value.studentAnswerLatex
          : studentAnswerLatex // ignore: cast_nullable_to_non_nullable
              as String,
      studentAnswerImages: null == studentAnswerImages
          ? _value._studentAnswerImages
          : studentAnswerImages // ignore: cast_nullable_to_non_nullable
              as List<String>,
      evaluation: freezed == evaluation
          ? _value.evaluation
          : evaluation // ignore: cast_nullable_to_non_nullable
              as EvaluationResult?,
      evaluationStatus: null == evaluationStatus
          ? _value.evaluationStatus
          : evaluationStatus // ignore: cast_nullable_to_non_nullable
              as EvaluationStatus,
      evaluatedAt: freezed == evaluatedAt
          ? _value.evaluatedAt
          : evaluatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      teacherComment: freezed == teacherComment
          ? _value.teacherComment
          : teacherComment // ignore: cast_nullable_to_non_nullable
              as String?,
      teacherAdjustedMarks: freezed == teacherAdjustedMarks
          ? _value.teacherAdjustedMarks
          : teacherAdjustedMarks // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuestionResponseImpl implements _QuestionResponse {
  const _$QuestionResponseImpl(
      {required this.questionId,
      required this.questionNumber,
      required this.studentAnswer,
      required this.studentAnswerLatex,
      required final List<String> studentAnswerImages,
      this.evaluation,
      required this.evaluationStatus,
      this.evaluatedAt,
      this.teacherComment,
      this.teacherAdjustedMarks})
      : _studentAnswerImages = studentAnswerImages;

  factory _$QuestionResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuestionResponseImplFromJson(json);

  @override
  final String questionId;
  @override
  final int questionNumber;
  @override
  final String studentAnswer;
  @override
  final String studentAnswerLatex;
  final List<String> _studentAnswerImages;
  @override
  List<String> get studentAnswerImages {
    if (_studentAnswerImages is EqualUnmodifiableListView)
      return _studentAnswerImages;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_studentAnswerImages);
  }

  @override
  final EvaluationResult? evaluation;
  @override
  final EvaluationStatus evaluationStatus;
  @override
  final DateTime? evaluatedAt;
  @override
  final String? teacherComment;
  @override
  final int? teacherAdjustedMarks;

  @override
  String toString() {
    return 'QuestionResponse(questionId: $questionId, questionNumber: $questionNumber, studentAnswer: $studentAnswer, studentAnswerLatex: $studentAnswerLatex, studentAnswerImages: $studentAnswerImages, evaluation: $evaluation, evaluationStatus: $evaluationStatus, evaluatedAt: $evaluatedAt, teacherComment: $teacherComment, teacherAdjustedMarks: $teacherAdjustedMarks)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuestionResponseImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.questionNumber, questionNumber) ||
                other.questionNumber == questionNumber) &&
            (identical(other.studentAnswer, studentAnswer) ||
                other.studentAnswer == studentAnswer) &&
            (identical(other.studentAnswerLatex, studentAnswerLatex) ||
                other.studentAnswerLatex == studentAnswerLatex) &&
            const DeepCollectionEquality()
                .equals(other._studentAnswerImages, _studentAnswerImages) &&
            (identical(other.evaluation, evaluation) ||
                other.evaluation == evaluation) &&
            (identical(other.evaluationStatus, evaluationStatus) ||
                other.evaluationStatus == evaluationStatus) &&
            (identical(other.evaluatedAt, evaluatedAt) ||
                other.evaluatedAt == evaluatedAt) &&
            (identical(other.teacherComment, teacherComment) ||
                other.teacherComment == teacherComment) &&
            (identical(other.teacherAdjustedMarks, teacherAdjustedMarks) ||
                other.teacherAdjustedMarks == teacherAdjustedMarks));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      questionId,
      questionNumber,
      studentAnswer,
      studentAnswerLatex,
      const DeepCollectionEquality().hash(_studentAnswerImages),
      evaluation,
      evaluationStatus,
      evaluatedAt,
      teacherComment,
      teacherAdjustedMarks);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuestionResponseImplCopyWith<_$QuestionResponseImpl> get copyWith =>
      __$$QuestionResponseImplCopyWithImpl<_$QuestionResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuestionResponseImplToJson(
      this,
    );
  }
}

abstract class _QuestionResponse implements QuestionResponse {
  const factory _QuestionResponse(
      {required final String questionId,
      required final int questionNumber,
      required final String studentAnswer,
      required final String studentAnswerLatex,
      required final List<String> studentAnswerImages,
      final EvaluationResult? evaluation,
      required final EvaluationStatus evaluationStatus,
      final DateTime? evaluatedAt,
      final String? teacherComment,
      final int? teacherAdjustedMarks}) = _$QuestionResponseImpl;

  factory _QuestionResponse.fromJson(Map<String, dynamic> json) =
      _$QuestionResponseImpl.fromJson;

  @override
  String get questionId;
  @override
  int get questionNumber;
  @override
  String get studentAnswer;
  @override
  String get studentAnswerLatex;
  @override
  List<String> get studentAnswerImages;
  @override
  EvaluationResult? get evaluation;
  @override
  EvaluationStatus get evaluationStatus;
  @override
  DateTime? get evaluatedAt;
  @override
  String? get teacherComment;
  @override
  int? get teacherAdjustedMarks;
  @override
  @JsonKey(ignore: true)
  _$$QuestionResponseImplCopyWith<_$QuestionResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

EvaluationResult _$EvaluationResultFromJson(Map<String, dynamic> json) {
  return _EvaluationResult.fromJson(json);
}

/// @nodoc
mixin _$EvaluationResult {
  String get id => throw _privateConstructorUsedError;
  int get awardedMarks => throw _privateConstructorUsedError;
  int get maxMarks => throw _privateConstructorUsedError;
  double get percentage => throw _privateConstructorUsedError;
  EvaluationVerdict get verdict => throw _privateConstructorUsedError;
  List<MarkingPointResult> get markingPoints =>
      throw _privateConstructorUsedError;
  RubricLevelResult get rubricLevel => throw _privateConstructorUsedError;
  double get confidenceScore => throw _privateConstructorUsedError;
  String get reasoning => throw _privateConstructorUsedError;
  List<String> get strengths => throw _privateConstructorUsedError;
  List<String> get gaps => throw _privateConstructorUsedError;
  List<String> get carelessErrors => throw _privateConstructorUsedError;
  int get estimatedTimeSpentSeconds => throw _privateConstructorUsedError;
  Map<String, dynamic> get metadata => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $EvaluationResultCopyWith<EvaluationResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $EvaluationResultCopyWith<$Res> {
  factory $EvaluationResultCopyWith(
          EvaluationResult value, $Res Function(EvaluationResult) then) =
      _$EvaluationResultCopyWithImpl<$Res, EvaluationResult>;
  @useResult
  $Res call(
      {String id,
      int awardedMarks,
      int maxMarks,
      double percentage,
      EvaluationVerdict verdict,
      List<MarkingPointResult> markingPoints,
      RubricLevelResult rubricLevel,
      double confidenceScore,
      String reasoning,
      List<String> strengths,
      List<String> gaps,
      List<String> carelessErrors,
      int estimatedTimeSpentSeconds,
      Map<String, dynamic> metadata});

  $RubricLevelResultCopyWith<$Res> get rubricLevel;
}

/// @nodoc
class _$EvaluationResultCopyWithImpl<$Res, $Val extends EvaluationResult>
    implements $EvaluationResultCopyWith<$Res> {
  _$EvaluationResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? awardedMarks = null,
    Object? maxMarks = null,
    Object? percentage = null,
    Object? verdict = null,
    Object? markingPoints = null,
    Object? rubricLevel = null,
    Object? confidenceScore = null,
    Object? reasoning = null,
    Object? strengths = null,
    Object? gaps = null,
    Object? carelessErrors = null,
    Object? estimatedTimeSpentSeconds = null,
    Object? metadata = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      awardedMarks: null == awardedMarks
          ? _value.awardedMarks
          : awardedMarks // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      verdict: null == verdict
          ? _value.verdict
          : verdict // ignore: cast_nullable_to_non_nullable
              as EvaluationVerdict,
      markingPoints: null == markingPoints
          ? _value.markingPoints
          : markingPoints // ignore: cast_nullable_to_non_nullable
              as List<MarkingPointResult>,
      rubricLevel: null == rubricLevel
          ? _value.rubricLevel
          : rubricLevel // ignore: cast_nullable_to_non_nullable
              as RubricLevelResult,
      confidenceScore: null == confidenceScore
          ? _value.confidenceScore
          : confidenceScore // ignore: cast_nullable_to_non_nullable
              as double,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      strengths: null == strengths
          ? _value.strengths
          : strengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      gaps: null == gaps
          ? _value.gaps
          : gaps // ignore: cast_nullable_to_non_nullable
              as List<String>,
      carelessErrors: null == carelessErrors
          ? _value.carelessErrors
          : carelessErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      estimatedTimeSpentSeconds: null == estimatedTimeSpentSeconds
          ? _value.estimatedTimeSpentSeconds
          : estimatedTimeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      metadata: null == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $RubricLevelResultCopyWith<$Res> get rubricLevel {
    return $RubricLevelResultCopyWith<$Res>(_value.rubricLevel, (value) {
      return _then(_value.copyWith(rubricLevel: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$EvaluationResultImplCopyWith<$Res>
    implements $EvaluationResultCopyWith<$Res> {
  factory _$$EvaluationResultImplCopyWith(_$EvaluationResultImpl value,
          $Res Function(_$EvaluationResultImpl) then) =
      __$$EvaluationResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      int awardedMarks,
      int maxMarks,
      double percentage,
      EvaluationVerdict verdict,
      List<MarkingPointResult> markingPoints,
      RubricLevelResult rubricLevel,
      double confidenceScore,
      String reasoning,
      List<String> strengths,
      List<String> gaps,
      List<String> carelessErrors,
      int estimatedTimeSpentSeconds,
      Map<String, dynamic> metadata});

  @override
  $RubricLevelResultCopyWith<$Res> get rubricLevel;
}

/// @nodoc
class __$$EvaluationResultImplCopyWithImpl<$Res>
    extends _$EvaluationResultCopyWithImpl<$Res, _$EvaluationResultImpl>
    implements _$$EvaluationResultImplCopyWith<$Res> {
  __$$EvaluationResultImplCopyWithImpl(_$EvaluationResultImpl _value,
      $Res Function(_$EvaluationResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? awardedMarks = null,
    Object? maxMarks = null,
    Object? percentage = null,
    Object? verdict = null,
    Object? markingPoints = null,
    Object? rubricLevel = null,
    Object? confidenceScore = null,
    Object? reasoning = null,
    Object? strengths = null,
    Object? gaps = null,
    Object? carelessErrors = null,
    Object? estimatedTimeSpentSeconds = null,
    Object? metadata = null,
  }) {
    return _then(_$EvaluationResultImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      awardedMarks: null == awardedMarks
          ? _value.awardedMarks
          : awardedMarks // ignore: cast_nullable_to_non_nullable
              as int,
      maxMarks: null == maxMarks
          ? _value.maxMarks
          : maxMarks // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as double,
      verdict: null == verdict
          ? _value.verdict
          : verdict // ignore: cast_nullable_to_non_nullable
              as EvaluationVerdict,
      markingPoints: null == markingPoints
          ? _value._markingPoints
          : markingPoints // ignore: cast_nullable_to_non_nullable
              as List<MarkingPointResult>,
      rubricLevel: null == rubricLevel
          ? _value.rubricLevel
          : rubricLevel // ignore: cast_nullable_to_non_nullable
              as RubricLevelResult,
      confidenceScore: null == confidenceScore
          ? _value.confidenceScore
          : confidenceScore // ignore: cast_nullable_to_non_nullable
              as double,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      strengths: null == strengths
          ? _value._strengths
          : strengths // ignore: cast_nullable_to_non_nullable
              as List<String>,
      gaps: null == gaps
          ? _value._gaps
          : gaps // ignore: cast_nullable_to_non_nullable
              as List<String>,
      carelessErrors: null == carelessErrors
          ? _value._carelessErrors
          : carelessErrors // ignore: cast_nullable_to_non_nullable
              as List<String>,
      estimatedTimeSpentSeconds: null == estimatedTimeSpentSeconds
          ? _value.estimatedTimeSpentSeconds
          : estimatedTimeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      metadata: null == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$EvaluationResultImpl implements _EvaluationResult {
  const _$EvaluationResultImpl(
      {required this.id,
      required this.awardedMarks,
      required this.maxMarks,
      required this.percentage,
      required this.verdict,
      required final List<MarkingPointResult> markingPoints,
      required this.rubricLevel,
      required this.confidenceScore,
      required this.reasoning,
      required final List<String> strengths,
      required final List<String> gaps,
      required final List<String> carelessErrors,
      required this.estimatedTimeSpentSeconds,
      final Map<String, dynamic> metadata = const {}})
      : _markingPoints = markingPoints,
        _strengths = strengths,
        _gaps = gaps,
        _carelessErrors = carelessErrors,
        _metadata = metadata;

  factory _$EvaluationResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$EvaluationResultImplFromJson(json);

  @override
  final String id;
  @override
  final int awardedMarks;
  @override
  final int maxMarks;
  @override
  final double percentage;
  @override
  final EvaluationVerdict verdict;
  final List<MarkingPointResult> _markingPoints;
  @override
  List<MarkingPointResult> get markingPoints {
    if (_markingPoints is EqualUnmodifiableListView) return _markingPoints;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_markingPoints);
  }

  @override
  final RubricLevelResult rubricLevel;
  @override
  final double confidenceScore;
  @override
  final String reasoning;
  final List<String> _strengths;
  @override
  List<String> get strengths {
    if (_strengths is EqualUnmodifiableListView) return _strengths;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_strengths);
  }

  final List<String> _gaps;
  @override
  List<String> get gaps {
    if (_gaps is EqualUnmodifiableListView) return _gaps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_gaps);
  }

  final List<String> _carelessErrors;
  @override
  List<String> get carelessErrors {
    if (_carelessErrors is EqualUnmodifiableListView) return _carelessErrors;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_carelessErrors);
  }

  @override
  final int estimatedTimeSpentSeconds;
  final Map<String, dynamic> _metadata;
  @override
  @JsonKey()
  Map<String, dynamic> get metadata {
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_metadata);
  }

  @override
  String toString() {
    return 'EvaluationResult(id: $id, awardedMarks: $awardedMarks, maxMarks: $maxMarks, percentage: $percentage, verdict: $verdict, markingPoints: $markingPoints, rubricLevel: $rubricLevel, confidenceScore: $confidenceScore, reasoning: $reasoning, strengths: $strengths, gaps: $gaps, carelessErrors: $carelessErrors, estimatedTimeSpentSeconds: $estimatedTimeSpentSeconds, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$EvaluationResultImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.awardedMarks, awardedMarks) ||
                other.awardedMarks == awardedMarks) &&
            (identical(other.maxMarks, maxMarks) ||
                other.maxMarks == maxMarks) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.verdict, verdict) || other.verdict == verdict) &&
            const DeepCollectionEquality()
                .equals(other._markingPoints, _markingPoints) &&
            (identical(other.rubricLevel, rubricLevel) ||
                other.rubricLevel == rubricLevel) &&
            (identical(other.confidenceScore, confidenceScore) ||
                other.confidenceScore == confidenceScore) &&
            (identical(other.reasoning, reasoning) ||
                other.reasoning == reasoning) &&
            const DeepCollectionEquality()
                .equals(other._strengths, _strengths) &&
            const DeepCollectionEquality().equals(other._gaps, _gaps) &&
            const DeepCollectionEquality()
                .equals(other._carelessErrors, _carelessErrors) &&
            (identical(other.estimatedTimeSpentSeconds,
                    estimatedTimeSpentSeconds) ||
                other.estimatedTimeSpentSeconds == estimatedTimeSpentSeconds) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      awardedMarks,
      maxMarks,
      percentage,
      verdict,
      const DeepCollectionEquality().hash(_markingPoints),
      rubricLevel,
      confidenceScore,
      reasoning,
      const DeepCollectionEquality().hash(_strengths),
      const DeepCollectionEquality().hash(_gaps),
      const DeepCollectionEquality().hash(_carelessErrors),
      estimatedTimeSpentSeconds,
      const DeepCollectionEquality().hash(_metadata));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$EvaluationResultImplCopyWith<_$EvaluationResultImpl> get copyWith =>
      __$$EvaluationResultImplCopyWithImpl<_$EvaluationResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$EvaluationResultImplToJson(
      this,
    );
  }
}

abstract class _EvaluationResult implements EvaluationResult {
  const factory _EvaluationResult(
      {required final String id,
      required final int awardedMarks,
      required final int maxMarks,
      required final double percentage,
      required final EvaluationVerdict verdict,
      required final List<MarkingPointResult> markingPoints,
      required final RubricLevelResult rubricLevel,
      required final double confidenceScore,
      required final String reasoning,
      required final List<String> strengths,
      required final List<String> gaps,
      required final List<String> carelessErrors,
      required final int estimatedTimeSpentSeconds,
      final Map<String, dynamic> metadata}) = _$EvaluationResultImpl;

  factory _EvaluationResult.fromJson(Map<String, dynamic> json) =
      _$EvaluationResultImpl.fromJson;

  @override
  String get id;
  @override
  int get awardedMarks;
  @override
  int get maxMarks;
  @override
  double get percentage;
  @override
  EvaluationVerdict get verdict;
  @override
  List<MarkingPointResult> get markingPoints;
  @override
  RubricLevelResult get rubricLevel;
  @override
  double get confidenceScore;
  @override
  String get reasoning;
  @override
  List<String> get strengths;
  @override
  List<String> get gaps;
  @override
  List<String> get carelessErrors;
  @override
  int get estimatedTimeSpentSeconds;
  @override
  Map<String, dynamic> get metadata;
  @override
  @JsonKey(ignore: true)
  _$$EvaluationResultImplCopyWith<_$EvaluationResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MarkingPointResult _$MarkingPointResultFromJson(Map<String, dynamic> json) {
  return _MarkingPointResult.fromJson(json);
}

/// @nodoc
mixin _$MarkingPointResult {
  String get markingPointId => throw _privateConstructorUsedError;
  bool get awarded => throw _privateConstructorUsedError;
  String get reason => throw _privateConstructorUsedError;
  double get similarityScore => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $MarkingPointResultCopyWith<MarkingPointResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MarkingPointResultCopyWith<$Res> {
  factory $MarkingPointResultCopyWith(
          MarkingPointResult value, $Res Function(MarkingPointResult) then) =
      _$MarkingPointResultCopyWithImpl<$Res, MarkingPointResult>;
  @useResult
  $Res call(
      {String markingPointId,
      bool awarded,
      String reason,
      double similarityScore});
}

/// @nodoc
class _$MarkingPointResultCopyWithImpl<$Res, $Val extends MarkingPointResult>
    implements $MarkingPointResultCopyWith<$Res> {
  _$MarkingPointResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? markingPointId = null,
    Object? awarded = null,
    Object? reason = null,
    Object? similarityScore = null,
  }) {
    return _then(_value.copyWith(
      markingPointId: null == markingPointId
          ? _value.markingPointId
          : markingPointId // ignore: cast_nullable_to_non_nullable
              as String,
      awarded: null == awarded
          ? _value.awarded
          : awarded // ignore: cast_nullable_to_non_nullable
              as bool,
      reason: null == reason
          ? _value.reason
          : reason // ignore: cast_nullable_to_non_nullable
              as String,
      similarityScore: null == similarityScore
          ? _value.similarityScore
          : similarityScore // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MarkingPointResultImplCopyWith<$Res>
    implements $MarkingPointResultCopyWith<$Res> {
  factory _$$MarkingPointResultImplCopyWith(_$MarkingPointResultImpl value,
          $Res Function(_$MarkingPointResultImpl) then) =
      __$$MarkingPointResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String markingPointId,
      bool awarded,
      String reason,
      double similarityScore});
}

/// @nodoc
class __$$MarkingPointResultImplCopyWithImpl<$Res>
    extends _$MarkingPointResultCopyWithImpl<$Res, _$MarkingPointResultImpl>
    implements _$$MarkingPointResultImplCopyWith<$Res> {
  __$$MarkingPointResultImplCopyWithImpl(_$MarkingPointResultImpl _value,
      $Res Function(_$MarkingPointResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? markingPointId = null,
    Object? awarded = null,
    Object? reason = null,
    Object? similarityScore = null,
  }) {
    return _then(_$MarkingPointResultImpl(
      markingPointId: null == markingPointId
          ? _value.markingPointId
          : markingPointId // ignore: cast_nullable_to_non_nullable
              as String,
      awarded: null == awarded
          ? _value.awarded
          : awarded // ignore: cast_nullable_to_non_nullable
              as bool,
      reason: null == reason
          ? _value.reason
          : reason // ignore: cast_nullable_to_non_nullable
              as String,
      similarityScore: null == similarityScore
          ? _value.similarityScore
          : similarityScore // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MarkingPointResultImpl implements _MarkingPointResult {
  const _$MarkingPointResultImpl(
      {required this.markingPointId,
      required this.awarded,
      required this.reason,
      required this.similarityScore});

  factory _$MarkingPointResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$MarkingPointResultImplFromJson(json);

  @override
  final String markingPointId;
  @override
  final bool awarded;
  @override
  final String reason;
  @override
  final double similarityScore;

  @override
  String toString() {
    return 'MarkingPointResult(markingPointId: $markingPointId, awarded: $awarded, reason: $reason, similarityScore: $similarityScore)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MarkingPointResultImpl &&
            (identical(other.markingPointId, markingPointId) ||
                other.markingPointId == markingPointId) &&
            (identical(other.awarded, awarded) || other.awarded == awarded) &&
            (identical(other.reason, reason) || other.reason == reason) &&
            (identical(other.similarityScore, similarityScore) ||
                other.similarityScore == similarityScore));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, markingPointId, awarded, reason, similarityScore);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$MarkingPointResultImplCopyWith<_$MarkingPointResultImpl> get copyWith =>
      __$$MarkingPointResultImplCopyWithImpl<_$MarkingPointResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MarkingPointResultImplToJson(
      this,
    );
  }
}

abstract class _MarkingPointResult implements MarkingPointResult {
  const factory _MarkingPointResult(
      {required final String markingPointId,
      required final bool awarded,
      required final String reason,
      required final double similarityScore}) = _$MarkingPointResultImpl;

  factory _MarkingPointResult.fromJson(Map<String, dynamic> json) =
      _$MarkingPointResultImpl.fromJson;

  @override
  String get markingPointId;
  @override
  bool get awarded;
  @override
  String get reason;
  @override
  double get similarityScore;
  @override
  @JsonKey(ignore: true)
  _$$MarkingPointResultImplCopyWith<_$MarkingPointResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RubricLevelResult _$RubricLevelResultFromJson(Map<String, dynamic> json) {
  return _RubricLevelResult.fromJson(json);
}

/// @nodoc
mixin _$RubricLevelResult {
  int get level => throw _privateConstructorUsedError;
  String get label => throw _privateConstructorUsedError;
  String get justification => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $RubricLevelResultCopyWith<RubricLevelResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RubricLevelResultCopyWith<$Res> {
  factory $RubricLevelResultCopyWith(
          RubricLevelResult value, $Res Function(RubricLevelResult) then) =
      _$RubricLevelResultCopyWithImpl<$Res, RubricLevelResult>;
  @useResult
  $Res call({int level, String label, String justification});
}

/// @nodoc
class _$RubricLevelResultCopyWithImpl<$Res, $Val extends RubricLevelResult>
    implements $RubricLevelResultCopyWith<$Res> {
  _$RubricLevelResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? label = null,
    Object? justification = null,
  }) {
    return _then(_value.copyWith(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as int,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      justification: null == justification
          ? _value.justification
          : justification // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RubricLevelResultImplCopyWith<$Res>
    implements $RubricLevelResultCopyWith<$Res> {
  factory _$$RubricLevelResultImplCopyWith(_$RubricLevelResultImpl value,
          $Res Function(_$RubricLevelResultImpl) then) =
      __$$RubricLevelResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int level, String label, String justification});
}

/// @nodoc
class __$$RubricLevelResultImplCopyWithImpl<$Res>
    extends _$RubricLevelResultCopyWithImpl<$Res, _$RubricLevelResultImpl>
    implements _$$RubricLevelResultImplCopyWith<$Res> {
  __$$RubricLevelResultImplCopyWithImpl(_$RubricLevelResultImpl _value,
      $Res Function(_$RubricLevelResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? label = null,
    Object? justification = null,
  }) {
    return _then(_$RubricLevelResultImpl(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as int,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      justification: null == justification
          ? _value.justification
          : justification // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RubricLevelResultImpl implements _RubricLevelResult {
  const _$RubricLevelResultImpl(
      {required this.level, required this.label, required this.justification});

  factory _$RubricLevelResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$RubricLevelResultImplFromJson(json);

  @override
  final int level;
  @override
  final String label;
  @override
  final String justification;

  @override
  String toString() {
    return 'RubricLevelResult(level: $level, label: $label, justification: $justification)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RubricLevelResultImpl &&
            (identical(other.level, level) || other.level == level) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.justification, justification) ||
                other.justification == justification));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, level, label, justification);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$RubricLevelResultImplCopyWith<_$RubricLevelResultImpl> get copyWith =>
      __$$RubricLevelResultImplCopyWithImpl<_$RubricLevelResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RubricLevelResultImplToJson(
      this,
    );
  }
}

abstract class _RubricLevelResult implements RubricLevelResult {
  const factory _RubricLevelResult(
      {required final int level,
      required final String label,
      required final String justification}) = _$RubricLevelResultImpl;

  factory _RubricLevelResult.fromJson(Map<String, dynamic> json) =
      _$RubricLevelResultImpl.fromJson;

  @override
  int get level;
  @override
  String get label;
  @override
  String get justification;
  @override
  @JsonKey(ignore: true)
  _$$RubricLevelResultImplCopyWith<_$RubricLevelResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
