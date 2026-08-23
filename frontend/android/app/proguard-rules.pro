# google_mlkit_text_recognition (on_device_ocr.dart) references
# script-specific recognizer classes (Chinese/Devanagari/Japanese/Korean)
# reflectively for optional script support; only the Latin-script model is
# actually bundled here (TextRecognitionScript.latin), so R8 can't resolve
# those classes at minify time without this -- a documented issue with the
# plugin, not a real missing dependency. Confirmed real: this exact set of
# missing-class errors is what `flutter build apk --release` reported.
-dontwarn com.google.mlkit.vision.text.chinese.**
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**
