import '../../core/local_engine/local_store.dart';

/// What the builder remembers between papers, per teacher: the last class,
/// subject and template. A teacher sets papers for the same one or two
/// classes all term; asking again every time is typing the same thing twice.
///
/// Keyed by the signed-in user's id, so two teachers sharing a school laptop
/// each get their own last choice. Stored in the app's existing Hive box
/// (LocalStore), which is IndexedDB on the web build.
class BuilderMemory {
  final String userId;
  BuilderMemory(this.userId);

  String get _key => 'paper_builder_last_$userId';

  Map<String, dynamic> _read() {
    final raw = LocalStore.instance.box.get(_key);
    return raw is Map ? Map<String, dynamic>.from(raw) : const {};
  }

  int? get grade => _read()['grade'] as int?;
  String? get subject => _read()['subject'] as String?;
  String? get templateId => _read()['templateId'] as String?;

  void remember({required int grade, required String subject, String? templateId}) {
    LocalStore.instance.box.put(_key, {
      'grade': grade,
      'subject': subject,
      if (templateId != null) 'templateId': templateId,
    });
  }
}
