// The light theme (the brand's light tokens: white cards on #F6F6F8, graphite
// text, the same ember buttons) and the toggle that switches to it. The app
// had been dark-only in practice, so light mode had never been looked at: a
// selected chip there was graphite on a graphite pill. This pumps the screens
// a school sees first -- the sign-in page, the shell around a list, and a
// dialog with chips -- in the light theme, and holds every piece of text and
// every icon to a legible contrast against what is actually painted behind
// it.
import 'dart:async';
import 'dart:io';

import 'package:academicos/core/local_engine/local_store.dart';
import 'package:academicos/core/theme/app_theme.dart';
import 'package:academicos/core/theme/emergera.dart';
import 'package:academicos/core/theme/theme_controller.dart';
import 'package:academicos/presentation/auth/pages/login_page.dart';
import 'package:academicos/presentation/guide/guide_page.dart';
import 'package:academicos/presentation/shared/widgets/common_widgets.dart';
import 'package:academicos/presentation/shared/widgets/shell.dart';
import 'package:academicos/presentation/shared/widgets/theme_toggle.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../responsive/responsive_harness.dart';

double _contrast(Color a, Color b) {
  final la = a.computeLuminance(), lb = b.computeLuminance();
  final hi = la > lb ? la : lb, lo = la > lb ? lb : la;
  return (hi + 0.05) / (lo + 0.05);
}

/// The colours painted behind [e], nearest first, down to the first opaque
/// one (or [page], the aurora's base, when none is).
Color _behind(Element e, Color page) {
  final layers = <Color>[];
  var opaque = page;
  e.visitAncestorElements((a) {
    final w = a.widget;
    Color? c;
    if (w is Material && w.type != MaterialType.transparency) {
      c = w.color ?? (w.type == MaterialType.canvas ? Theme.of(a).canvasColor : Theme.of(a).cardColor);
    } else if (w is Ink && w.decoration is BoxDecoration) {
      c = (w.decoration as BoxDecoration).color;
    } else if (w is Ink && w.decoration is ShapeDecoration) {
      c = (w.decoration as ShapeDecoration).color;
    } else if (w is DecoratedBox && w.decoration is BoxDecoration) {
      c = (w.decoration as BoxDecoration).color;
    } else if (w is DecoratedBox && w.decoration is ShapeDecoration) {
      c = (w.decoration as ShapeDecoration).color;
    } else if (w is ColoredBox) {
      c = w.color;
    }
    if (c == null || c.a == 0) return true;
    if (c.a >= 1) {
      opaque = c;
      return false;
    }
    layers.add(c);
    return true;
  });
  var bg = opaque;
  for (final c in layers.reversed) {
    bg = Color.alphaBlend(c, bg);
  }
  return bg;
}

bool _inside<T extends Widget>(Element e) {
  var found = false;
  e.visitAncestorElements((a) {
    found = a.widget is T;
    return !found;
  });
  return found;
}

/// Text and icons on screen whose colour is too close to what is behind
/// them. Skipped: the ember-filled buttons (white on the ember gradient, a
/// gradient this walk cannot see) and disabled controls, which WCAG exempts.
List<String> _illegible(WidgetTester tester, Color page, {double min = 3.0}) {
  final problems = <String>[];
  for (final e in find.byType(RichText).evaluate()) {
    final rt = e.widget as RichText;
    final box = e.renderObject as RenderBox?;
    if (box == null || !box.hasSize || box.size.isEmpty) continue;
    final colour = rt.text.style?.color;
    final text = rt.text.toPlainText().trim();
    if (colour == null || text.isEmpty) continue;
    if (_inside<FilledButton>(e) || _inside<ElevatedButton>(e) || _inside<FloatingActionButton>(e)) continue;
    var disabled = false;
    e.visitAncestorElements((a) {
      final w = a.widget;
      if (w is ButtonStyleButton && !w.enabled) disabled = true;
      return !disabled;
    });
    if (disabled) continue;
    final bg = _behind(e, page);
    final ratio = _contrast(Color.alphaBlend(colour, bg), bg);
    final what = rt.text.style?.fontFamily == 'MaterialIcons' ? 'icon U+${text.runes.first.toRadixString(16)}' : '"$text"';
    if (ratio < min) problems.add('$what: ${ratio.toStringAsFixed(2)}:1, $colour on $bg');
  }
  return problems;
}

/// The light page behind every screen: EmBackdrop's base in the light theme.
final _lightPage = EmSurfaces.light.auroraBase;

void _signIn(String role) => LocalStore.instance.authUser = {
      'id': 'user_$role', 'schoolId': 'school_a', 'name': 'Test $role', 'email': '$role@example.com', 'role': role,
    };

/// The shell around a list page, following the theme mode as main.dart does.
Widget _shellApp() {
  final router = GoRouter(initialLocation: '/school/exams', routes: [
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        GoRoute(
          path: '/school/exams',
          builder: (context, state) => Scaffold(
            appBar: destinationAppBar(context, title: const Text('Exams')),
            body: ListView(padding: const EdgeInsets.all(16), children: [
              const SectionHeader(title: 'Datesheet', subtitle: '2026-10-12 to 2026-10-20'),
              for (final (name, status) in [('Half-yearly', 'published'), ('Unit test 2', 'draft')])
                AppCard(
                  child: ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(name),
                    subtitle: const Text('classes 6, 7, 8 · 9 papers'),
                    trailing: ChipTag(label: status),
                  ),
                ),
            ]),
            floatingActionButton:
                FloatingActionButton.extended(onPressed: () {}, icon: const Icon(Icons.add), label: const Text('New exam')),
          ),
        ),
        GoRoute(path: '/school', builder: (context, state) => const Scaffold(body: Text('Overview'))),
      ],
    ),
  ]);
  return ValueListenableBuilder<ThemeMode>(
    valueListenable: ThemeController.mode,
    builder: (context, mode, _) => MaterialApp.router(
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: mode,
      routerConfig: router,
    ),
  );
}

/// The New exam dialog's shape: a name, the dates, and class chips, one
/// selected.
class _ExamDialog extends StatelessWidget {
  const _ExamDialog();

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: const Text('New exam'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const TextField(decoration: InputDecoration(labelText: 'Name, e.g. Half-yearly')),
          const ListTile(contentPadding: EdgeInsets.zero, title: Text('Choose dates'), trailing: Icon(Icons.date_range)),
          const Text('Classes'),
          Wrap(spacing: 6, children: [
            for (var g = 6; g <= 9; g++) FilterChip(label: Text('$g'), selected: g == 7, onSelected: (_) {}),
          ]),
        ]),
        actions: [
          TextButton(onPressed: () {}, child: const Text('Cancel')),
          FilledButton(onPressed: () {}, child: const Text('Create')),
        ],
      );
}

void main() {
  late Directory tmp;
  useAppFonts();

  setUpAll(() async {
    tmp = Directory.systemTemp.createTempSync('light_theme_test_');
    Hive.init(tmp.path);
    await Hive.openBox('academicos_cache');
  });

  setUp(() => ThemeController.set(ThemeMode.dark));

  tearDown(() => LocalStore.instance.clearAuth());

  tearDownAll(() async {
    try {
      await Hive.close().timeout(const Duration(seconds: 10));
    } on TimeoutException {
      // ignore: avoid_print
      print('light_theme_test: Hive.close() did not return within 10s -- proceeding.');
    }
    try {
      tmp.deleteSync(recursive: true);
    } on FileSystemException {
      // Windows may still hold the box file; a leaked temp dir is harmless.
    }
  });

  testWidgets('the toggle shows what it switches to, flips the mode and keeps it', (tester) async {
    await tester.pumpWidget(ValueListenableBuilder<ThemeMode>(
      valueListenable: ThemeController.mode,
      builder: (context, mode, _) => MaterialApp(
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: mode,
        home: const Scaffold(body: Center(child: ThemeToggleButton())),
      ),
    ));
    await tester.pumpAndSettle();
    final toggle = find.byKey(const ValueKey('theme-toggle'));
    expect(find.byTooltip('Light theme'), findsOneWidget, reason: 'in the dark theme it offers light');
    expect(find.byIcon(Icons.light_mode_outlined), findsOneWidget, reason: 'a sun');

    await tester.tap(toggle);
    await tester.pumpAndSettle();
    expect(ThemeController.mode.value, ThemeMode.light);
    expect(Theme.of(tester.element(toggle)).brightness, Brightness.light);
    expect(find.byTooltip('Dark theme'), findsOneWidget);
    expect(find.byIcon(Icons.dark_mode_outlined), findsOneWidget, reason: 'a moon');
    expect(LocalStore.instance.themeModeName, 'light', reason: 'kept on the device');

    await tester.tap(toggle);
    await tester.pumpAndSettle();
    expect(ThemeController.mode.value, ThemeMode.dark);
    expect(LocalStore.instance.themeModeName, 'dark');
  });

  testWidgets('the sign-in page has the toggle at the top right, and reads in the light theme', (tester) async {
    for (final screen in [phoneScreen, laptopScreen]) {
      await tester.pumpWidget(const SizedBox()); // a fresh page, in Sign in mode
      await pumpPage(tester, const LoginPage(), screen);
      expectNoOverflow(tester);
      final toggle = find.byKey(const ValueKey('theme-toggle'));
      expect(toggle, findsOneWidget);
      final r = tester.getRect(toggle);
      expect(r.right, greaterThan(screen.size.width - 60), reason: 'at the right edge');
      expect(r.top, lessThan(60), reason: 'at the top');
      expect(tester.getSize(toggle).height, greaterThanOrEqualTo(minTapTarget));
      expect(_illegible(tester, _lightPage), isEmpty, reason: 'sign-in page, light theme, ${screen.size}');

      await tester.tap(find.text('Create account'));
      await tester.pumpAndSettle();
      expect(_illegible(tester, _lightPage), isEmpty, reason: 'register form, light theme, ${screen.size}');
    }
  });

  testWidgets('the shell has the toggle beside the Guide, and a list reads in the light theme', (tester) async {
    useScreen(tester, laptopScreen);
    _signIn('principal');
    await tester.pumpWidget(_shellApp());
    await tester.pumpAndSettle();
    final toggle = find.byKey(const ValueKey('theme-toggle'));
    final guide = find.byKey(const ValueKey('guide-button'));
    expect(toggle, findsOneWidget, reason: 'a signed-in page has the toggle in its app bar');
    expect(guide, findsOneWidget);
    expect((tester.getCenter(toggle).dy - tester.getCenter(guide).dy).abs(), lessThan(1), reason: 'side by side');
    expect(tester.getCenter(toggle).dx, lessThan(tester.getCenter(guide).dx), reason: 'the Guide is last');

    await tester.tap(toggle);
    await tester.pumpAndSettle();
    expect(Theme.of(tester.element(toggle)).brightness, Brightness.light);
    expectNoOverflow(tester);
    expect(_illegible(tester, _lightPage), isEmpty, reason: 'the shell and a list, light theme');

    // The same page on a phone, with the drawer open.
    useScreen(tester, phoneScreen);
    await tester.pumpAndSettle();
    expect(_illegible(tester, _lightPage), isEmpty, reason: 'a list on a phone, light theme');
    await tester.tap(find.byTooltip('Menu'));
    await tester.pumpAndSettle();
    expect(_illegible(tester, _lightPage), isEmpty, reason: 'the drawer, light theme');
  });

  testWidgets('the Guide reads in the light theme, a job open', (tester) async {
    useScreen(tester, phoneScreen);
    await tester.pumpWidget(MaterialApp(theme: AppTheme.lightTheme, home: const GuidePage(role: 'principal')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Publish an exam datesheet'));
    await tester.pumpAndSettle();
    expectNoOverflow(tester);
    expect(_illegible(tester, _lightPage), isEmpty, reason: 'the Guide, light theme');
  });

  for (final (name, theme, page) in [
    ('light', AppTheme.lightTheme, EmSurfaces.light.auroraBase),
    ('dark', AppTheme.darkTheme, EmSurfaces.dark.auroraBase),
  ]) {
    testWidgets('$name theme: a dialog with a selected class chip reads, label and all', (tester) async {
      useScreen(tester, phoneScreen);
      await tester.pumpWidget(MaterialApp(
        theme: theme,
        home: Builder(builder: (context) => Scaffold(
              body: Center(child: TextButton(
                onPressed: () => showDialog<void>(context: context, builder: (_) => const _ExamDialog()),
                child: const Text('Open'),
              )),
            )),
      ));
      await tester.tap(find.text('Open'));
      await tester.pumpAndSettle();
      expectNoOverflow(tester);
      final problems = _illegible(tester, page)
          .where((p) => !p.startsWith('"Open"')) // the page under the dialog's barrier
          .toList();
      expect(problems, isEmpty, reason: 'New exam dialog, $name theme');
      // The selected chip itself, label against its own pill (at least 4.5:1).
      final chip = find.widgetWithText(FilterChip, '7');
      final label = tester
          .widget<RichText>(find.descendant(of: chip, matching: find.byType(RichText)))
          .text
          .style!
          .color!;
      final pill = (tester.widget<Ink>(find.descendant(of: chip, matching: find.byType(Ink))).decoration!
              as ShapeDecoration)
          .color!;
      expect(_contrast(label, pill), greaterThanOrEqualTo(4.5));
    });
  }
}
