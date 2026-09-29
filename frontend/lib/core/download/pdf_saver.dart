import 'dart:typed_data';

import 'pdf_saver_io.dart' if (dart.library.html) 'pdf_saver_web.dart' as impl;

/// Hands a PDF (or an Excel workbook, by its `.xlsx` name) the app already
/// holds to the user: a browser download on the web, the platform share/view
/// sheet elsewhere. Registered in GetIt
/// (service_locator.dart) so a test can see what would have been saved.
abstract class PdfSaver {
  Future<void> save(Uint8List bytes, String filename);

  /// The implementation for the platform this build runs on.
  factory PdfSaver.platform() = _PlatformPdfSaver;
}

class _PlatformPdfSaver implements PdfSaver {
  @override
  Future<void> save(Uint8List bytes, String filename) => impl.savePdf(bytes, filename);
}
