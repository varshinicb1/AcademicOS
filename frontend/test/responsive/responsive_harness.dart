// Shared checks for the Task 801 responsive tests: the teacher's main flows
// at the widths the web app is really opened at -- a phone browser
// (375 x 812), a tablet (768 x 1024) and a laptop (1280 x 800) -- and at the
// phone again with Android Chrome's "Large" text setting (1.3x).
//
// Teachers are "primarily mobile" (PRD requirements matrix) and the first
// sellable product is the web app, so for most of them it is a phone browser.
// Each flow's test asserts two things at every size:
//   * nothing overflowed -- Flutter reports "A RenderFlex overflowed" as an
//     exception, which [expectNoOverflow] takes and fails on;
//   * the screen's primary action is on screen, hit-testable (not covered by
//     a sheet, bar or another widget) and, on the phone, at least 44 px in
//     both directions -- the smallest target a thumb reliably hits.
import 'package:flutter/foundation.dart' show debugDefaultTargetPlatformOverride;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show FontLoader, rootBundle;
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/core/constants/app_constants.dart';
import 'package:academicos/core/theme/app_theme.dart';

/// A screen a flow is checked at: its size and the browser text scale.
///
/// Android Chrome's accessibility text-size setting reaches Flutter web as
/// MediaQuery.textScaler, and a phone-first product meets it: every width fix
/// in Task 801 (the Expanded headings, the 420 px LayoutBuilder, the Wrap
/// "when the text is scaled up") was justified by larger text with nothing
/// measuring it (review of 2026-09-23).
typedef Screen = ({Size size, double textScale});

const phone = Size(375, 812);
const tablet = Size(768, 1024);
const laptop = Size(1280, 800);

/// Every size a flow is checked at, named for the test description.
/// The three screens by name, for a test that pins one rather than looping.
const phoneScreen = (size: phone, textScale: 1.0);
const tabletScreen = (size: tablet, textScale: 1.0);
const laptopScreen = (size: laptop, textScale: 1.0);

const screenSizes = <String, Screen>{
  'phone 375x812': (size: phone, textScale: 1.0),
  // Android Chrome's "Large" text setting, on the width most teachers open
  // the app at.
  //
  // This row was parked in a comment until 2026-09-23 because it failed 7
  // flows. It does not: that measurement was taken before Inter was a bundled
  // asset (057d3f1), when [useAppFonts] had no real font to load and every
  // string was laid out in flutter_test's fallback glyph -- a fixed-width box
  // wider than Inter at every size. Re-measured with useAppFonts disabled, the
  // same 7 flows fail again; with the face a teacher actually reads, all of
  // them fit at 1.3x unchanged.
  //
  // The row is not decorative: at 2.4x, 15 of these 18 flows fail on this
  // exact suite, so a layout that stops fitting when the text grows is caught
  // here. A row that cannot fit wraps or stacks -- nothing is made smaller to
  // pass, because the setting exists for someone who needs it larger.
  'phone 375x812 at 1.3x text': (size: phone, textScale: 1.3),
  'tablet 768x1024': (size: tablet, textScale: 1.0),
  'laptop 1280x800': (size: laptop, textScale: 1.0),
};

/// Smallest tap target on the phone layout (Apple's 44 pt guideline; Material
/// pads its own buttons to 48).
const minTapTarget = 44.0;

/// Sets the test surface to [screen]'s logical pixels and text scale, for
/// this test only.
void useScreen(WidgetTester tester, Screen screen) {
  tester.view.physicalSize = screen.size;
  tester.view.devicePixelRatio = 1;
  tester.platformDispatcher.textScaleFactorTestValue = screen.textScale;
  addTearDown(tester.view.reset);
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
}

/// Call once per test file, from `main()`.
///
/// Loads the shipped typeface into the test binding, so a flow is measured in
/// the face a teacher actually reads it in.
///
/// Without this a widget test lays every string out in flutter_test's fallback
/// glyph, which is a fixed-width box unrelated to Inter, and a width assertion
/// on a 375 px phone is then only an approximation of the real one. It used to
/// be unavoidable: AppTheme's styles came from google_fonts, which downloads
/// Inter over HTTP on first use and rethrows when it cannot -- always, in a
/// widget test -- so the typeface had to be swapped out for a bare TextStyle
/// naming the same absent family. Now that Inter is a bundled asset
/// (pubspec.yaml's `fonts:` block) there is a real font to load, and
/// [FontLoader] puts it in front of the same text the app draws.
///
/// All four weights are registered under the one family, matching how the
/// pubspec declares them, so a style's `fontWeight` picks a real face here
/// too rather than a synthesised one.
void useAppFonts() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final loader = FontLoader(AppConstants.fontFamily);
    for (final asset in _interAssets) {
      loader.addFont(rootBundle.load(asset));
    }
    await loader.load();
  });
}

/// The Inter faces pubspec.yaml bundles, in the same order it declares them.
const _interAssets = <String>[
  'assets/fonts/Inter-Regular.ttf',
  'assets/fonts/Inter-Medium.ttf',
  'assets/fonts/Inter-SemiBold.ttf',
  'assets/fonts/Inter-Bold.ttf',
];

/// [page] inside the MaterialApp main.dart builds, theme and all.
///
/// The shipped theme is not Flutter's default and the differences are exactly
/// the kind that decide whether a row fits 375 px: 24/14 padding on elevated
/// and outlined buttons, 16/10 on text buttons, every form field `filled`
/// with 16/14 content padding, chips with their own label style and a 20 px
/// radius, and w600 labels across the six-tab admin strip. A flow measured
/// against the default theme proves nothing about the app a teacher opens
/// (review of 2026-09-23), which is the one claim this suite exists to make.
Widget appForTest(Widget page) => MaterialApp(theme: AppTheme.lightTheme, home: page);

/// [useScreen] + [appForTest] + settle: how every flow test starts.
Future<void> pumpPage(WidgetTester tester, Widget page, Screen screen) async {
  useScreen(tester, screen);
  await tester.pumpWidget(appForTest(page));
  await tester.pumpAndSettle();
}

/// Runs [body] as a desktop browser runs the app.
///
/// flutter_test pins `defaultTargetPlatform` to android, and ThemeData gives
/// android `VisualDensity.standard`. A browser on windows, linux or macOS
/// reports its own platform, and ThemeData gives those
/// `VisualDensity.compact` (-8, -8) -- the SDK's own comment calls compact
/// "the default for desktop/web". ButtonStyleButton runs `minimumSize`
/// through that density, so a control asked for 48 px renders 40 there
/// unless it pins its own density. None of the tests above can reach that
/// path, and the browser evidence for this task was taken in exactly it: a
/// desktop Chrome window resized to 375 px (review of 2026-09-23).
Future<void> withDesktopDensity(Future<void> Function() body) async {
  debugDefaultTargetPlatformOverride = TargetPlatform.windows;
  try {
    await body();
  } finally {
    debugDefaultTargetPlatformOverride = null;
  }
}

/// The height a main action draws at when it carries no style of its own.
///
/// Pumped, not written down: it is [AppTheme.lightTheme] plus whatever visual
/// density the running platform gives it, which is the whole point -- an
/// assertion that "the desktop look is unchanged" has to be against the theme
/// as it is, not against a number that drifts away from it. Call it inside
/// [withDesktopDensity] to get the compact height a laptop browser draws, and
/// before pumping the page under test (it pumps a widget of its own).
Future<double> themeButtonHeight(WidgetTester tester, Screen size) async {
  await pumpPage(
      tester, Scaffold(body: Center(child: FilledButton(onPressed: () {}, child: const Text('Sign in')))), size);
  return tester.getRect(paintedTarget(tester, find.byType(FilledButton))).height;
}

/// Fails with the overflow (or any other exception) the last frames raised.
void expectNoOverflow(WidgetTester tester, {String where = ''}) {
  final error = tester.takeException();
  // A FlutterError's deep form names the widget that overflowed and where it
  // was created -- the line to fix.
  expect(error, isNull,
      reason: 'layout error$where: ${error is FlutterError ? error.toStringDeep() : error}');
}

/// The box of [action] that is actually painted -- what a teacher aims at.
///
/// Measuring a Material button's own finder measures nothing useful. Every
/// ButtonStyleButton, FloatingActionButton and RawMaterialButton returns
/// `_InputPadding > ConstrainedBox > Material > InkWell`
/// (button_style_button.dart, button.dart), and `_InputPadding` expands to
/// `kMinInteractiveDimension` (48) whenever `tapTargetSize` is `padded` --
/// which ThemeData picks for android and iOS, and flutter_test pins the
/// platform to android. So `tester.getRect(button)` is 48 px square by
/// construction and the rule below could never fail, however small the
/// control is drawn: a plain TextButton (M3 minimum 64x40) passed it before
/// anyone widened it (review of 2026-09-23). The `Material` inside the
/// button's own `ConstrainedBox` is the box that gets drawn and that the ink
/// splashes in, so that is the one that is size-checked.
///
/// A SegmentedButton pads itself from the inside instead (its render object
/// adds `tapTargetVerticalPadding`), so its own box is padded too; what a
/// thumb lands on is one segment, a TextButton, and that is measured.
/// Anything that is not a Material button -- a Tab, a ListTile, a TextField,
/// an InkWell, the Tooltip that sits *inside* an IconButton's Material -- is
/// already its own painted box and is measured as it is.
Finder paintedTarget(WidgetTester tester, Finder action) {
  var target = action;
  if (tester.widget(target) is SegmentedButton) {
    final segment = find.descendant(
        of: target, matching: find.byWidgetPredicate((w) => w is ButtonStyleButton));
    expect(segment, findsWidgets, reason: 'a SegmentedButton always builds its segments as TextButtons');
    target = segment.first;
  }
  final widget = tester.widget(target);
  if (widget is ButtonStyleButton || widget is FloatingActionButton || widget is RawMaterialButton) {
    final painted = find.descendant(of: target, matching: find.byType(Material));
    expect(painted, findsWidgets, reason: 'a Material button always paints into a Material');
    return painted.first;
  }
  return target;
}

/// The primary action [action] is inside the [size] screen, hit-testable at
/// its centre and, on a phone-width screen, at least [minTapTarget] square.
void expectActionReady(WidgetTester tester, Finder action, Screen screen, {String? label}) {
  final size = screen.size;
  final name = label ?? action.toString();
  expect(action, findsOneWidget, reason: '$name must be on the screen');
  final r = tester.getRect(action);
  expect(r.left >= 0 && r.top >= 0 && r.right <= size.width + 0.01 && r.bottom <= size.height + 0.01, isTrue,
      reason: '$name at $r must be inside the ${size.width.toInt()}x${size.height.toInt()} screen');
  expect(action.hitTestable(), findsOneWidget,
      reason: '$name at $r must receive a tap, not be covered by another widget');
  if (size.width < 600) {
    final painted = tester.getRect(paintedTarget(tester, action));
    expect(painted.height >= minTapTarget && painted.width >= minTapTarget, isTrue,
        reason: '$name is drawn ${painted.width.toStringAsFixed(0)}x${painted.height.toStringAsFixed(0)}; '
            'a phone tap target needs at least ${minTapTarget.toInt()} px each way');
  }
}

/// Scrolls [target] into view (the way a teacher scrolls a long form) and
/// then checks it as [expectActionReady] does.
Future<void> scrollToAndExpectReady(WidgetTester tester, Finder target, Screen size, {String? label}) async {
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  expectActionReady(tester, target, size, label: label);
}

/// Drags [scrollable] until [target] is built at all. A long list builds its
/// children lazily, so a finder for something far down matches nothing until
/// the list has been scrolled near it -- and `.first` on a finder that
/// matches nothing throws rather than waiting.
Future<void> scrollUntilPresent(WidgetTester tester, Finder target, Finder scrollable,
    {double delta = 300, int maxDrags = 80}) async {
  for (var i = 0; i < maxDrags && target.evaluate().isEmpty; i++) {
    await tester.drag(scrollable, Offset(0, -delta));
    await tester.pump();
  }
  expect(target, findsWidgets, reason: 'nothing matched $target after scrolling the list');
}
