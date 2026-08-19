import 'package:equatable/equatable.dart';

abstract class Failure extends Equatable {
  final String message;
  final String? code;
  final dynamic originalError;

  const Failure(this.message, {this.code, this.originalError});

  @override
  List<Object?> get props => [message, code, originalError];
}

class ServerFailure extends Failure {
  const ServerFailure(super.message, {super.code, super.originalError});
}

class CacheFailure extends Failure {
  const CacheFailure(super.message, {super.code, super.originalError});
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message, {super.code, super.originalError});
}

class AuthFailure extends Failure {
  const AuthFailure(super.message, {super.code, super.originalError});
}

class PermissionFailure extends Failure {
  const PermissionFailure(super.message, {super.code, super.originalError});
}

class NotFoundFailure extends Failure {
  const NotFoundFailure(super.message, {super.code, super.originalError});
}

class ValidationFailure extends Failure {
  final Map<String, String> fieldErrors;

  const ValidationFailure(super.message, {this.fieldErrors = const {}, super.code, super.originalError});

  @override
  List<Object?> get props => [message, code, originalError, fieldErrors];
}

class ParsingFailure extends Failure {
  const ParsingFailure(super.message, {super.code, super.originalError});
}

class OfflineFailure extends Failure {
  const OfflineFailure(super.message, {super.code, super.originalError});
}

class SyncFailure extends Failure {
  const SyncFailure(super.message, {super.code, super.originalError});
}

class OcrFailure extends Failure {
  const OcrFailure(super.message, {super.code, super.originalError});
}

class VisionFailure extends Failure {
  const VisionFailure(super.message, {super.code, super.originalError});
}

class EvaluationFailure extends Failure {
  const EvaluationFailure(super.message, {super.code, super.originalError});
}

class GenerationFailure extends Failure {
  const GenerationFailure(super.message, {super.code, super.originalError});
}

class TemplateFailure extends Failure {
  const TemplateFailure(super.message, {super.code, super.originalError});
}

class ScanningFailure extends Failure {
  const ScanningFailure(super.message, {super.code, super.originalError});
}