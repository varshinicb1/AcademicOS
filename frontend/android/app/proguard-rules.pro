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

# Real, device-confirmed crash (not a hypothesis): a real Android device
# running this exact release build threw
# "Unable to get provider com.google.mlkit.common.internal.MlKitInitProvider:
# ... Unsatisfied dependency ... class com.google.mlkit.common.sdkinternal.d"
# on cold start, BEFORE Flutter/Dart ever runs -- MlKitInitProvider is a
# ContentProvider Android auto-instantiates during process bind, so this
# crashed the whole app unconditionally regardless of anything in main.dart.
# Root cause: com.google.mlkit.common.** (Google's actual MLKit common SDK,
# dotted package) was never covered by the rules above -- those only kept
# com.google_mlkit_commons.** (the Flutter *plugin's* own underscored
# package, a different thing entirely) and the vision.text-specific classes.
-keep class com.google.mlkit.common.** { *; }
