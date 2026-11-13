import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Release signing (R-B1). The owner holds the keystore; it is never committed.
// android/key.properties (gitignored) names it:
//   storeFile=<path to the .jks, relative to android/app/>
//   storePassword=<...>
//   keyAlias=<...>
//   keyPassword=<...>
// Why a real key matters: Android 15/16 and most OEM security layers refuse to install a
// release-type APK signed with the well-known public debug certificate (a real user report:
// "not getting installed on android 16 phones"). Without key.properties a release build
// still succeeds, signed with the local debug key, for local testing only. docs/apps.md has
// the owner's steps.
val keystorePropertiesFile = file("../key.properties")
val keystoreProperties = Properties()
val hasReleaseKey = keystorePropertiesFile.exists()
if (hasReleaseKey) {
    FileInputStream(keystorePropertiesFile).use { keystoreProperties.load(it) }
    val missing = listOf("storeFile", "storePassword", "keyAlias", "keyPassword")
        .filter { keystoreProperties.getProperty(it).isNullOrBlank() }
    if (missing.isNotEmpty()) {
        throw GradleException(
            "android/key.properties is missing ${missing.joinToString()}. " +
                "See docs/apps.md, \"Release signing\"."
        )
    }
}

if (!hasReleaseKey && gradle.startParameter.taskNames.any { it.contains("Release") }) {
    logger.warn(
        "AcademicOS: android/key.properties not found, so this release build is signed with " +
            "the local DEBUG key. Fine for local testing; Google Play and Android 15+ devices " +
            "refuse it. See docs/apps.md, \"Release signing\"."
    )
}

// One app per flavor (R-B1). Each flavor must be built with the dart-define that makes the
// Dart code that product (lib/presentation/workspace/app_mode.dart, ACADEMICOS_OFFLINE);
// a mismatch would ship, say, the web console inside the "AcademicOS Teacher" package.
data class AppFlavor(val name: String, val idSuffix: String?, val label: String, val define: Pair<String, String>)
val appFlavors = listOf(
    AppFlavor("teacher", ".teacher", "AcademicOS Teacher", "ACADEMICOS_APP" to "teacher"),
    AppFlavor("student", ".student", "AcademicOS Student", "ACADEMICOS_APP" to "student"),
    // No suffix: the offline app keeps the id it has always shipped under, so an installed
    // copy upgrades in place.
    AppFlavor("offline", null, "AcademicOS Offline", "ACADEMICOS_OFFLINE" to "true"),
)

// `flutter build`/`flutter run` pass their dart-defines to Gradle as one property of
// comma-separated base64 entries. Android Studio's own Gradle sync passes none, and is
// left alone.
val dartDefines: Map<String, String>? = (findProperty("dart-defines") as String?)?.let { raw ->
    raw.split(",").filter { it.isNotBlank() }.associate { entry ->
        val text = String(java.util.Base64.getDecoder().decode(entry), Charsets.UTF_8)
        text.substringBefore("=") to text.substringAfter("=", "")
    }
}
if (dartDefines != null) {
    val requested = gradle.startParameter.taskNames.map { it.substringAfterLast(":") }
    val usage = appFlavors.joinToString("\n") {
        "  flutter build appbundle --flavor ${it.name} --dart-define=${it.define.first}=${it.define.second}"
    }
    val flavorless = Regex("^(assemble|bundle|install)(Debug|Profile|Release)$")
    if (requested.any { flavorless.matches(it) }) {
        throw GradleException(
            "This Android project builds three apps; name one with --flavor:\n$usage\n" +
                "(docs/apps.md, \"Building\")."
        )
    }
    for (f in appFlavors) {
        val cap = f.name.replaceFirstChar { it.uppercase() }
        if (requested.none { it.contains(cap) }) continue
        val (key, want) = f.define
        val conflicting = f.name != "offline" && dartDefines["ACADEMICOS_OFFLINE"] == "true"
        if (dartDefines[key] != want || conflicting) {
            throw GradleException(
                "--flavor ${f.name} must be built with --dart-define=$key=$want" +
                    (if (conflicting) " and without ACADEMICOS_OFFLINE=true" else "") +
                    ", or the ${f.label} package would hold a different app.\n$usage"
            )
        }
    }
}

android {
    namespace = "com.example.academicos"
    // Overridden past Flutter's bundled default (34): flutter_plugin_android_lifecycle
    // (pulled in transitively by file_picker) requires compiling against API 36+,
    // confirmed by a real `flutter build apk` failure at the old default.
    compileSdk = 37
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        // The per-flavor app_name below is a generated resource.
        resValues = true
    }

    defaultConfig {
        // The store identity is the owner's decision (com.example.* cannot be published on
        // Google Play); the flavors below add their suffix to whatever this is.
        applicationId = "com.example.academicos"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    flavorDimensions += "app"
    productFlavors {
        for (f in appFlavors) {
            create(f.name) {
                dimension = "app"
                f.idSuffix?.let { applicationIdSuffix = it }
                resValue("string", "app_name", f.label)
                // Launcher icon: every flavor uses the shared @mipmap/ic_launcher until the
                // owner supplies per-app icons. They go in app/src/<flavor>/res/mipmap-*/
                // and override the shared one with no change here.
            }
        }
    }

    signingConfigs {
        create("release") {
            if (hasReleaseKey) {
                keyAlias = keystoreProperties.getProperty("keyAlias")
                keyPassword = keystoreProperties.getProperty("keyPassword")
                storeFile = file(keystoreProperties.getProperty("storeFile"))
                storePassword = keystoreProperties.getProperty("storePassword")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = if (hasReleaseKey) {
                signingConfigs.getByName("release")
            } else {
                signingConfigs.getByName("debug")
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
