import 'dart:typed_data';

import 'package:printing/printing.dart';

/// Desktop and mobile: `printing`'s native share/view sheet, the same path the
/// offline build's local exports already take (assessment_review_page.dart).
Future<void> savePdf(Uint8List bytes, String filename) =>
    Printing.sharePdf(bytes: bytes, filename: filename);
