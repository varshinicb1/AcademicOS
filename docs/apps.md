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

```bash
cd frontend
flutter build apk --release --dart-define=ACADEMICOS_APP=teacher --dart-define=ACADEMICOS_API="https://academicos-backend-2eskom55ta-el.a.run.app/api/v1"
flutter build apk --release --dart-define=ACADEMICOS_APP=student --dart-define=ACADEMICOS_API="https://academicos-backend-2eskom55ta-el.a.run.app/api/v1"
```

Both builds share one Android application id today, so a device holds one at a time.
Installing both side by side needs Gradle product flavors with an `applicationIdSuffix`
(`.teacher`, `.student`); that, store listings and signing are the owner's next step.
Push notifications on the phone need `ACOS_FCM_PROJECT` on the backend and the Firebase
config files in the Android project.

`ACADEMICOS_OFFLINE` and `ACADEMICOS_APP` are independent: the offline build ignores
`ACADEMICOS_APP`, and neither flag may reach the web build.
