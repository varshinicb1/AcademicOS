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
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const phone = Size(375, 812);
const tablet = Size(768, 1024);
const laptop = Size(1280, 800);

/// Every size a flow is checked at, named for the test description.
const screenSizes = <String, Size>{
  'phone 375x812': phone,
  'tablet 768x1024': tablet,
  'laptop 1280x800': laptop,
};

/// Smallest tap target on the phone layout (Apple's 44 pt guideline; Material
/// pads its own buttons to 48).
const minTapTarget = 44.0;

/// Sets the test surface to [size] logical pixels for this test only.
void useScreen(WidgetTester tester, Size size) {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

/// Fails with the overflow (or any other exception) the last frames raised.
void expectNoOverflow(WidgetTester tester, {String where = ''}) {
  final error = tester.takeException();
  // A FlutterError's deep form names the widget that overflowed and where it
  // was created -- the line to fix.
  expect(error, isNull,
      reason: 'layout error$where: ${error is FlutterError ? error.toStringDeep() : error}');
}

/// The primary action [action] is inside the [size] screen, hit-testable at
/// its centre and, on a phone-width screen, at least [minTapTarget] square.
void expectActionReady(WidgetTester tester, Finder action, Size size, {String? label}) {
  final name = label ?? action.toString();
  expect(action, findsOneWidget, reason: '$name must be on the screen');
  final r = tester.getRect(action);
  expect(r.left >= 0 && r.top >= 0 && r.right <= size.width + 0.01 && r.bottom <= size.height + 0.01, isTrue,
      reason: '$name at $r must be inside the ${size.width.toInt()}x${size.height.toInt()} screen');
  expect(action.hitTestable(), findsOneWidget,
      reason: '$name at $r must receive a tap, not be covered by another widget');
  if (size.width < 600) {
    expect(r.height >= minTapTarget && r.width >= minTapTarget, isTrue,
        reason: '$name is ${r.width.toStringAsFixed(0)}x${r.height.toStringAsFixed(0)}; '
            'a phone tap target needs at least ${minTapTarget.toInt()} px each way');
  }
}

/// Scrolls [target] into view (the way a teacher scrolls a long form) and
/// then checks it as [expectActionReady] does.
Future<void> scrollToAndExpectReady(WidgetTester tester, Finder target, Size size, {String? label}) async {
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
