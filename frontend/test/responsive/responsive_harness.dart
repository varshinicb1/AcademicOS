// Shared checks for the Task 801 responsive tests: the teacher's main flows
// at the three widths the web app is really opened at -- a phone browser
// (375 x 812), a tablet (768 x 1024) and a laptop (1280 x 800).
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
import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';

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
  // Android Chrome's "Large" text setting -- (size: phone, textScale: 1.3) --
  // is plumbed through `useScreen` but not listed yet: it fails on 7 of these
  // flows today (the assessments list, the custom-paper builder, the answer-key
  // download, the Coverage & Pace dashboard and three more). Those are real
  // defects on a setting a phone-first product meets, and they are Task 803's
  // to fix; adding the row here without them would only paint the suite red.
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
/// AppTheme's styles come from google_fonts, which downloads Inter over HTTP
/// the first time each weight is asked for -- gstatic.com URLs, from a widget
/// test -- and rethrows when it cannot, which lands as an unhandled error in
/// the test's zone and fails whichever test happens to be running. Disabling
/// its runtime fetching does not help: it throws there too (its own
/// loadFontIfNecessary rethrows both ways), and this app bundles no font
/// assets for it to fall back on.
///
/// So the theme's typeface is swapped instead, for a plain TextStyle naming
/// the same family. Nothing these tests measure changes: a widget test has no
/// Inter to render with either way and falls back to the test font, and what
/// is measured here is padding, constraints and density.
///
/// The limitation that follows -- these tests lay text out in flutter_test's
/// fixed-width fallback glyph, not in Inter, so a measured overrun is an
/// approximation of the Inter one (review of 2026-09-23).
///
/// That review read the limitation as a product defect -- "the shipped app
/// draws in the browser's fallback face" -- on the evidence that
/// `document.fonts` is empty in the released build. It is not: the live site
/// (https://vidyuthlabs.web.app, 2026-09-23) fetches three TTFs from
/// fonts.gstatic.com under /s/a/, which is google_fonts doing its runtime
/// load. `document.fonts` stays empty because CanvasKit registers a typeface
/// with Skia rather than as a CSS FontFace, so the browser's font set is the
/// wrong place to look. Inter does reach the user; only these tests render
/// without it.
void useAppFonts() {
  setUpAll(() {
    GoogleFonts.config.allowRuntimeFetching = false;
    AppTheme.font = _plainInter;
  });
  tearDownAll(() => AppTheme.font = AppTheme.inter);
}

TextStyle _plainInter({Color? color, double? fontSize, FontWeight? fontWeight, double? letterSpacing}) =>
    TextStyle(
      fontFamily: AppConstants.fontFamily,
      color: color,
      fontSize: fontSize,
      fontWeight: fontWeight,
      letterSpacing: letterSpacing,
    );

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
