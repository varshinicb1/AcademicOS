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

# ML Kit's real, actually-used vision/text classes are loaded reflectively
# at runtime -- -dontwarn above only silences a BUILD-time warning about the
# unused optional-script classes, it does nothing to stop R8's release-mode
# optimizer from renaming/stripping the classes ML Kit genuinely needs,
# which reflection can't see through. Missing this is a real, documented,
# common cause of an ML Kit call crashing only in a minified release build
# (works in debug, breaks in release) -- exactly the difference between the
# debug build an earlier investigation compiled cleanly and the release
# build this app actually ships. These are Google's own published keep
# rules for this library.
-keep class com.google.mlkit.vision.text.** { *; }
-keep class com.google.android.gms.internal.mlkit_vision_text_common.** { *; }
-keep class com.google_mlkit_text_recognition.** { *; }
-keep class com.google_mlkit_commons.** { *; }
