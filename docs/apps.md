# The teacher app and the student app

One Flutter codebase (`frontend/`) builds four products:

| Product | Build flag | Talks to | First page |
|---|---|---|---|
| Web console | none (default) | the backend | Today (`/home`); parents and students land on School |
| Teacher app | `--dart-define=ACADEMICOS_APP=teacher` | the backend | My day |
| Student app (with parent mode) | `--dart-define=ACADEMICOS_APP=student` | the backend | Today (a parent: My children) |
| Offline Android app | `--dart-define=ACADEMICOS_OFFLINE=true` | nothing: a local engine and a bundled bank | Today |

The two phone apps use the same pages as the web console's **School** tab
(`frontend/lib/presentation/workspace/`), inside a phone shell with a bottom bar of
at most five tabs (`app_mode.dart`):

- **Teacher:** My day (periods, cover duties to accept, check-in), Homework (set from the
  lesson, mark per question, see photos of written work), Papers, Inbox, More (reviews,
  exam duties, and any admin tools the principal has granted).
- **Student:** Today, Homework (answer in the app or attach photos), Progress, Exams, Inbox.
- **Parent** (signs in to the student app): My children (week, today, homework, progress,
  consent) and Inbox.

## Building

Each Android app is a Gradle product flavor (`frontend/android/app/build.gradle.kts`, R-B1)
with its own application id and launcher name, so all three install side by side:

| Flavor | Application id | Launcher name | Must be built with |
|---|---|---|---|
| `teacher` | `com.example.academicos.teacher` | AcademicOS Teacher | `--dart-define=ACADEMICOS_APP=teacher` |
| `student` | `com.example.academicos.student` | AcademicOS Student | `--dart-define=ACADEMICOS_APP=student` |
| `offline` | `com.example.academicos` (unchanged, so installed copies upgrade) | AcademicOS Offline | `--dart-define=ACADEMICOS_OFFLINE=true` |

The flavor picks the package; the dart-define picks the Dart app inside it. Gradle refuses
a build whose define does not match its flavor, and an Android build with no `--flavor`,
with a message listing the right commands.

```bash
cd frontend
API="https://academicos-backend-2eskom55ta-el.a.run.app/api/v1"
# Play upload (app bundles)
flutter build appbundle --release --flavor teacher --dart-define=ACADEMICOS_APP=teacher --dart-define=ACADEMICOS_API="$API"
flutter build appbundle --release --flavor student --dart-define=ACADEMICOS_APP=student --dart-define=ACADEMICOS_API="$API"
flutter build appbundle --release --flavor offline --dart-define=ACADEMICOS_OFFLINE=true
# Sideload APKs (one per ABI keeps each small)
flutter build apk --release --split-per-abi --flavor teacher --dart-define=ACADEMICOS_APP=teacher --dart-define=ACADEMICOS_API="$API"
flutter build apk --release --split-per-abi --flavor student --dart-define=ACADEMICOS_APP=student --dart-define=ACADEMICOS_API="$API"
flutter build apk --release --split-per-abi --flavor offline --dart-define=ACADEMICOS_OFFLINE=true
# On a connected phone
flutter run --flavor teacher --dart-define=ACADEMICOS_APP=teacher --dart-define=ACADEMICOS_API="$API"
```

Outputs land in `build/app/outputs/bundle/<flavor>Release/` and
`build/app/outputs/flutter-apk/app-<abi>-<flavor>-release.apk`.

Launcher icons: all three use the shared `@mipmap/ic_launcher` today. The owner supplies
per-app icons (the logo is a locked asset); they go in
`frontend/android/app/src/<flavor>/res/mipmap-*/ic_launcher.png` and override the shared one
with no Gradle change.

The base id `com.example.academicos` cannot be published on Google Play. Choosing the real
id is the owner's decision; change `applicationId` in `build.gradle.kts` and every flavor
follows. Do it before the first Play upload, because a published id can never change.

### Release signing (owner)

The owner holds the upload keystore. It and its passwords are never committed:
`frontend/android/.gitignore` ignores `key.properties`, `*.jks` and `*.keystore`.

1. Create the keystore once, outside the repository, and back it up somewhere safe
   (losing it means asking Play support to reset the upload key):

   ```bash
   keytool -genkey -v -keystore ~/keys/academicos-upload.jks -keyalg RSA -keysize 2048 \
     -validity 10000 -alias upload
   ```

2. Create `frontend/android/key.properties` (placeholders shown; `storeFile` is relative to
   `frontend/android/app/` or absolute):

   ```properties
   storeFile=/home/<you>/keys/academicos-upload.jks
   storePassword=<store password>
   keyAlias=upload
   keyPassword=<key password>
   ```

3. Build the three app bundles above. With `key.properties` present they are signed with
   that key; a missing field fails the build by name. Without the file, release builds still
   succeed for local testing, signed with the local debug key, and Gradle warns that Google
   Play and Android 15+ phones refuse them.
4. In the Play Console, create one app per flavor (teacher, student, and offline if it is
   to be listed), opt in to Play App Signing, and upload each `.aab` to
   **Testing > Internal testing**, then add the testers' email list.

Push notifications on the phone need `ACOS_FCM_PROJECT` on the backend and the Firebase
config files in the Android project.

`ACADEMICOS_OFFLINE` and `ACADEMICOS_APP` are independent: the offline build ignores
`ACADEMICOS_APP`, and neither flag may reach the web build.
