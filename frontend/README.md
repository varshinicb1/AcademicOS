# academicos

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## Web build

Recommended command (matches the deployed GitHub Pages site):

```powershell
flutter build web --release
```

Why this and not `--wasm` — measured on Flutter 3.44.9 stable with this app
(release builds, `build/web` deployable payload, `build/web/.git` excluded):

| Option | Command | Total | canvaskit/ | assets/ | main code | main code gzip |
|---|---|---|---|---|---|---|
| Default (JS/CanvasKit) | `flutter build web --release` | 49.6 MB | 38.5 MB | 6.4 MB | `main.dart.js` 4.65 MB | 1.29 MB |
| Wasm (skwasm + JS fallback) | `flutter build web --release --wasm` | 53.2 MB | 38.5 MB | 6.4 MB | `main.dart.wasm` 3.63 MB + `main.dart.js` 4.65 MB fallback | 1.31 MB + 1.29 MB |

- Flutter 3.44.x removed the `--web-renderer` flag (and the HTML renderer);
  the only renderer options are the default dart2js/CanvasKit build and
  `--wasm` (skwasm, WebAssembly with automatic JS fallback). See
  `flutter build web --help`.
- The wasm build is **heavier**, not lighter: it ships `main.dart.wasm`,
  `main.dart.mjs`, *and* the full `main.dart.js` JS fallback, so the
  deployable total goes from 49.6 MB to 53.2 MB. Gzipped, `main.dart.wasm`
  (1.31 MB) is not smaller than `main.dart.js` (1.29 MB).
- The wasm build **crashes at startup for this app**: `secure_box.dart`
  picks its web implementation via `if (dart.library.html)`, which is
  `false` under dart2wasm (dart:html is JS-only), so the dart:io impl is
  compiled and `getApplicationSupportDirectory()` throws an uncaught
  `MissingPluginException` before `runApp()`. Verified in headless Chrome
  against a locally served build. The default JS build boots cleanly.
- Serving note: `python -m http.server` maps `.mjs` to `text/plain`, which
  browsers reject for module scripts. Serve `build/web` with a MIME-aware
  static server (or any real host, e.g. GitHub Pages).

`build/web` is gitignored and is itself the deployment git repo for
`academicos-frontend-src` — never push build output to this repository.
