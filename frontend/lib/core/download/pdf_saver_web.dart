// Compiled only into the web build (the conditional import in pdf_saver.dart),
// with dart:html as secure_box_web.dart already uses it.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;
import 'dart:typed_data';

/// Web: a Blob of the bytes the app fetched WITH the session token, saved
/// through a temporary <a download>. A plain link to the API route cannot
/// work -- the browser would request it without the bearer token and get
/// 401 (the live release's answer-key bug, re-audit 2026-09-22).
Future<void> savePdf(Uint8List bytes, String filename) async {
  final type = filename.endsWith('.xlsx')
      ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      : filename.endsWith('.docx')
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf';
  final blob = html.Blob([bytes], type);
  final url = html.Url.createObjectUrlFromBlob(blob);
  final anchor = html.AnchorElement(href: url)
    ..download = filename
    ..style.display = 'none';
  html.document.body?.append(anchor);
  anchor.click();
  anchor.remove();
  // Revoked after the browser has taken the download, not immediately:
  // revoking in the same tick can cancel it in some browsers.
  Future<void>.delayed(const Duration(minutes: 1), () => html.Url.revokeObjectUrl(url));
}
