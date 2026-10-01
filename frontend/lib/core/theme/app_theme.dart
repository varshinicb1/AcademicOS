import 'package:flutter/material.dart';

import '../constants/app_constants.dart';
import 'emergera.dart';

/// The palette the whole app draws from, taken from the design system
/// (design/tokens.json), which carries the Emergera brand (2026-10-01): dark
/// by default -- ink page, night cards, ember accent -- and a light theme of
/// white cards on an off-white canvas. The canvas is deliberately not #FFFFFF --
/// tokens.json's `surface` note explains why a data-dense screen needs a
/// resting surface between its white cards.
///
/// Until 2026-09-30 the theme was generated from navy, blue and orange
/// seeds that were in no token, so the app and the design system disagreed
/// on every screen, and Material 3 tinted each raised card and app bar with
/// the seed. The roles below are named explicitly instead, with no surface
/// tint.
class _Palette {
  const _Palette({
    required this.brightness,
    required this.canvas,
    required this.card,
    required this.inset,
    required this.line,
    required this.lineStrong,
    required this.text,
    required this.textSecondary,
    required this.textMuted,
    required this.accent,
    required this.accentHover,
    required this.onAccent,
    required this.accentTint,
    required this.onAccentTint,
    required this.danger,
    required this.dangerTint,
    required this.onDangerTint,
  });

  final Brightness brightness;
  final Color canvas, card, inset, line, lineStrong;
  final Color text, textSecondary, textMuted;
  final Color accent, accentHover, onAccent, accentTint, onAccentTint;
  final Color danger, dangerTint, onDangerTint;

  // Emergera brand (design/tokens.json, from the brand's tokens.css v2.3):
  // light is white cards on a #F6F6F8 page with graphite text; the accent is
  // ember-deep, the brand's "ember text on light" (4.9:1 under white text).
  static const light = _Palette(
    brightness: Brightness.light,
    canvas: Color(0xFFF6F6F8), // neutral 50, the brand's bg-alt
    card: Color(0xFFFFFFFF),
    inset: Color(0xFFF0F0F3), // neutral 100
    line: Color(0xFFE8E8EC), // neutral 200, black at 9% on white
    lineStrong: Color(0xFFD2D2D8), // neutral 300
    text: Color(0xFF1D1D1F), // graphite
    textSecondary: Color(0xFF6E6E78), // slate-deep, 5.0:1 on fog
    textMuted: Color(0xFF6E6E78),
    accent: Color(0xFFC2410C), // ember-deep
    accentHover: Color(0xFF9A3412),
    onAccent: Color(0xFFFFFFFF),
    accentTint: Color(0xFFFFF1EA), // ember at 8% on white
    onAccentTint: Color(0xFF9A3412),
    danger: Color(0xFFB91C1C),
    dangerTint: Color(0xFFFEF2F2),
    onDangerTint: Color(0xFF7F1D1D),
  );

  // Dark is the brand's default: ink page, night cards, fog text, ember buttons.
  static const dark = _Palette(
    brightness: Brightness.dark,
    canvas: Color(0xFF07080F), // ink
    card: Color(0xFF0E1120), // night
    inset: Color(0xFF0B0D18), // bg-alt
    line: Color(0xFF1A1E33), // dusk, hairlines on dark
    lineStrong: Color(0xFF2A2E45),
    text: Color(0xFFF5F5F7), // fog
    textSecondary: Color(0xFFA1A3B3), // slate, 8.1:1 on ink
    textMuted: Color(0xFFA1A3B3),
    accent: Color(0xFFFF5A1F), // ember, THE accent
    accentHover: Color(0xFFFF7A45), // ember lifted for small text on ink
    onAccent: Color(0xFFFFFFFF),
    accentTint: Color(0xFF2A1406), // the brand's banner ember on ink
    onAccentTint: Color(0xFFFFB08A), // chip ember text
    danger: Color(0xFFFF6B6B),
    dangerTint: Color(0xFF2A0F12),
    onDangerTint: Color(0xFFFFC9C9),
  );

  ColorScheme get scheme => ColorScheme(
        brightness: brightness,
        primary: accent,
        onPrimary: onAccent,
        primaryContainer: accentTint,
        onPrimaryContainer: onAccentTint,
        secondary: textSecondary,
        onSecondary: card,
        secondaryContainer: inset,
        onSecondaryContainer: text,
        tertiary: accentHover,
        onTertiary: onAccent,
        tertiaryContainer: accentTint,
        onTertiaryContainer: onAccentTint,
        error: danger,
        onError: brightness == Brightness.light ? Colors.white : const Color(0xFF07080F),
        errorContainer: dangerTint,
        onErrorContainer: onDangerTint,
        surface: card,
        onSurface: text,
        onSurfaceVariant: textSecondary,
        surfaceContainerLowest: card,
        surfaceContainerLow: canvas,
        surfaceContainer: inset,
        surfaceContainerHigh: inset,
        surfaceContainerHighest: line,
        outline: lineStrong,
        outlineVariant: line,
        shadow: Colors.black,
        scrim: Colors.black,
        inverseSurface: text,
        onInverseSurface: canvas,
        inversePrimary: brightness == Brightness.light ? const Color(0xFFFF7A45) : const Color(0xFFC2410C),
        surfaceTint: Colors.transparent,
      );
}

/// The design tokens' status and accent colours as constants, for code that
/// has no BuildContext (enum colour getters, PDF-free widgets built as
/// `const`). They are the light theme's text-strength shades: legible on
/// white as text or an icon, and soft enough behind 10% alpha as a fill.
/// Prefer [StatusColors.of] where a context exists, which follows dark mode.
abstract final class AppColors {
  static const Color success = Color(0xFF0B7A5A); // mint-deep
  static const Color warning = Color(0xFFB45309);
  static const Color danger = Color(0xFFB91C1C);
  static const Color info = Color(0xFF1D4ED8);
  static const Color accent = Color(0xFFC2410C); // ember-deep
  static const Color neutral = Color(0xFF6E6E78);
}

/// Status colours for chips, banners and progress (tokens.json
/// `semantic`): the text colour, a soft fill and its border. Read with
/// `Theme.of(context).extension<StatusColors>()!` or [StatusColors.of].
@immutable
class StatusColors extends ThemeExtension<StatusColors> {
  const StatusColors({
    required this.success,
    required this.successBg,
    required this.successBorder,
    required this.warning,
    required this.warningBg,
    required this.warningBorder,
    required this.danger,
    required this.dangerBg,
    required this.dangerBorder,
    required this.info,
    required this.infoBg,
    required this.infoBorder,
  });

  final Color success, successBg, successBorder;
  final Color warning, warningBg, warningBorder;
  final Color danger, dangerBg, dangerBorder;
  final Color info, infoBg, infoBorder;

  static const light = StatusColors(
    success: Color(0xFF0B7A5A), successBg: Color(0xFFE8F7F1), successBorder: Color(0xFFA9E5CF),
    warning: Color(0xFFB45309), warningBg: Color(0xFFFFFBEB), warningBorder: Color(0xFFFDE68A),
    danger: Color(0xFFB91C1C), dangerBg: Color(0xFFFEF2F2), dangerBorder: Color(0xFFFECACA),
    info: Color(0xFF1D4ED8), infoBg: Color(0xFFEFF6FF), infoBorder: Color(0xFFBFDBFE),
  );

  // The brand's text-safe status colours on ink, with their 12% fills.
  static const dark = StatusColors(
    success: Color(0xFF30D5A0), successBg: Color(0xFF0A1F1C), successBorder: Color(0xFF0B7A5A),
    warning: Color(0xFFFFC24A), warningBg: Color(0xFF211B0E), warningBorder: Color(0xFF7A5A12),
    danger: Color(0xFFFF6B6B), dangerBg: Color(0xFF24100F), dangerBorder: Color(0xFF7F1D1D),
    info: Color(0xFF8AB4FF), infoBg: Color(0xFF141B2D), infoBorder: Color(0xFF2B4A85),
  );

  static StatusColors of(BuildContext context) =>
      Theme.of(context).extension<StatusColors>() ?? light;

  @override
  StatusColors copyWith() => this;

  @override
  StatusColors lerp(ThemeExtension<StatusColors>? other, double t) =>
      other is StatusColors && t >= 0.5 ? other : this;
}

class AppTheme {
  /// The typeface every style below is built from: Inter, the one family the
  /// design system names for anything user-facing (design/tokens.json,
  /// `typography.family.ui`).
  ///
  /// It is a bundled asset -- `assets/fonts/Inter-*.ttf`, declared with their
  /// weights in pubspec.yaml -- not a runtime download. google_fonts used to
  /// fetch it from fonts.gstatic.com on first paint, which worked on the web
  /// but meant the first frame was never the design system's, the offline
  /// desktop build had no way to get the typeface at all, and every weight
  /// arrived as its own one-face family so `copyWith(fontWeight: ...)`
  /// resolved to a synthesised face. See pubspec.yaml for the full note.
  ///
  /// Naming only the family (not a per-weight family) is what lets Flutter
  /// pick the real 400/500/600/700 face for whatever weight is asked for,
  /// here or in any `copyWith` downstream.
  static TextStyle font({
    Color? color,
    double? fontSize,
    FontWeight? fontWeight,
    double? letterSpacing,
    double? height,
  }) =>
      TextStyle(
        fontFamily: AppConstants.fontFamily,
        color: color,
        fontSize: fontSize,
        fontWeight: fontWeight,
        letterSpacing: letterSpacing,
        height: height,
      );

  static ThemeData get lightTheme => _build(_Palette.light, StatusColors.light);
  static ThemeData get darkTheme => _build(_Palette.dark, StatusColors.dark);

  static const double _radius = 12; // list rows and menus
  static const double _cardRadius = Em.radiusLg; // --em-radius-lg: cards and dialogs

  static ThemeData _build(_Palette p, StatusColors status) {
    final s = EmSurfaces.of(p.brightness);
    // Every surface a page paints is glass over the aurora, not only Cards.
    final scheme = p.scheme.copyWith(surface: s.glass, surfaceContainerLowest: s.glass);
    final control = RoundedRectangleBorder(borderRadius: BorderRadius.circular(_radius));
    final glassShape = EmRimBorder(borderRadius: BorderRadius.circular(_cardRadius), rim: s.rim);
    OutlineInputBorder field(Color c, [double w = 1]) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(Em.radiusField),
          borderSide: BorderSide(color: c, width: w),
        );
    // .em-btn: 17 px semibold, tracking -0.012em, a pill as tall as
    // --em-control-h (48 px), padded 0.46 of its height. Material's density
    // still trims it on a desktop's compact density, as before.
    final buttonText = font(fontSize: 17, fontWeight: FontWeight.w600, letterSpacing: -0.2);
    const buttonPadding = EdgeInsets.symmetric(horizontal: 22);
    const pill = StadiumBorder();
    const noOverlay = WidgetStatePropertyAll<Color>(Colors.transparent);
    final primary = ButtonStyle(
      backgroundBuilder: emPrimaryBackground,
      backgroundColor: const WidgetStatePropertyAll(Colors.transparent),
      foregroundColor: const WidgetStatePropertyAll(Colors.white),
      overlayColor: noOverlay,
      elevation: const WidgetStatePropertyAll(0),
      shadowColor: noOverlay,
      minimumSize: const WidgetStatePropertyAll(Size(Em.controlH, Em.controlH)),
      padding: const WidgetStatePropertyAll(buttonPadding),
      shape: const WidgetStatePropertyAll(pill),
      textStyle: WidgetStatePropertyAll(buttonText.copyWith(
          shadows: const [Shadow(color: Color(0x59781E00), offset: Offset(0, 1), blurRadius: 1)])),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: p.brightness,
      colorScheme: scheme,
      extensions: [status],
      fontFamily: AppConstants.fontFamily,
      textTheme: _textTheme(p),
      // Transparent: EmBackdrop (main.dart) paints the brand's aurora behind
      // every page, and the glass cards sit on it.
      scaffoldBackgroundColor: Colors.transparent,
      canvasColor: p.canvas,
      dividerColor: p.line,
      splashFactory: InkSparkle.splashFactory,
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        backgroundColor: s.navBg, // --em-nav-bg
        surfaceTintColor: Colors.transparent,
        foregroundColor: p.text,
        shape: Border(bottom: BorderSide(color: s.navLine)),
        titleTextStyle: font(fontSize: 18, fontWeight: FontWeight.w600, color: p.text, letterSpacing: -0.3),
        iconTheme: IconThemeData(color: p.textSecondary, size: 22),
      ),
      // .em-card: glass over the aurora, the lit rim, --em-radius-lg.
      cardTheme: CardThemeData(
        elevation: 2,
        shadowColor: p.brightness == Brightness.dark ? Colors.black : const Color(0x33101220),
        color: s.glass,
        surfaceTintColor: Colors.transparent,
        margin: const EdgeInsets.all(0),
        shape: glassShape,
      ),
      filledButtonTheme: FilledButtonThemeData(style: primary),
      elevatedButtonTheme: ElevatedButtonThemeData(style: primary),
      // .em-btn--glass
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: ButtonStyle(
          backgroundBuilder: emGlassBackground,
          backgroundColor: const WidgetStatePropertyAll(Colors.transparent),
          foregroundColor: WidgetStatePropertyAll(p.text),
          overlayColor: noOverlay,
          side: const WidgetStatePropertyAll(BorderSide.none),
          minimumSize: const WidgetStatePropertyAll(Size(Em.controlH, Em.controlH)),
          padding: const WidgetStatePropertyAll(buttonPadding),
          shape: const WidgetStatePropertyAll(pill),
          textStyle: WidgetStatePropertyAll(buttonText),
        ),
      ),
      // .em-link / .em-btn--ghost: link colour, a pill of --em-fill-2 on hover.
      textButtonTheme: TextButtonThemeData(
        style: ButtonStyle(
          foregroundColor: WidgetStatePropertyAll(s.link),
          overlayColor: WidgetStateProperty.resolveWith(
              (st) => st.contains(WidgetState.hovered) || st.contains(WidgetState.pressed) ? s.fill2 : null),
          minimumSize: const WidgetStatePropertyAll(Size(48, 40)),
          padding: const WidgetStatePropertyAll(EdgeInsets.symmetric(horizontal: 14)),
          shape: const WidgetStatePropertyAll(pill),
          textStyle: WidgetStatePropertyAll(font(fontSize: 15, fontWeight: FontWeight.w500)),
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(foregroundColor: p.textSecondary, hoverColor: s.fill2, shape: const CircleBorder()),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: Em.ember,
        foregroundColor: Colors.white,
        elevation: 6,
        focusElevation: 6,
        hoverElevation: 10,
        highlightElevation: 4,
        shape: pill,
        extendedTextStyle: buttonText,
      ),
      // .em-input: 14 px corners, --em-field-bg, the field rim, an ember focus edge.
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: s.fieldBg,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: field(s.fieldBorder),
        enabledBorder: field(s.fieldBorder),
        focusedBorder: field(Em.ember, 1.5),
        errorBorder: field(p.danger),
        focusedErrorBorder: field(p.danger, 1.5),
        disabledBorder: field(s.rimLine),
        labelStyle: font(color: p.textSecondary, fontSize: 15),
        floatingLabelStyle: font(color: p.text, fontSize: 15, fontWeight: FontWeight.w600),
        hintStyle: font(color: p.textMuted, fontSize: 15),
        helperStyle: font(color: p.textMuted, fontSize: 13),
      ),
      // .em-chip: a pill of --em-fill-1 with the rim; pressed is --em-chip-on.
      chipTheme: ChipThemeData(
        backgroundColor: s.fill1,
        selectedColor: s.chipOnBg,
        disabledColor: s.fill1,
        side: BorderSide(color: s.rimLine),
        checkmarkColor: s.chipOnFg,
        labelStyle: font(color: p.text, fontSize: 14, fontWeight: FontWeight.w500, letterSpacing: -0.07),
        secondaryLabelStyle: font(color: s.chipOnFg, fontSize: 14, fontWeight: FontWeight.w500),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
        shape: const StadiumBorder(),
      ),
      // .em-segmented
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          side: WidgetStatePropertyAll(BorderSide(color: s.rimLine)),
          shape: WidgetStatePropertyAll(RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
          backgroundColor: WidgetStateProperty.resolveWith(
              (st) => st.contains(WidgetState.selected) ? s.segOnBg : s.fill1),
          foregroundColor: WidgetStateProperty.resolveWith(
              (st) => st.contains(WidgetState.selected) ? p.text : p.textMuted),
          textStyle: WidgetStatePropertyAll(font(fontSize: 14, fontWeight: FontWeight.w500)),
        ),
      ),
      // .em-tabs: the selected tab's sunrise underline with its glow.
      tabBarTheme: TabBarThemeData(
        labelColor: p.text,
        unselectedLabelColor: p.textMuted,
        indicator: const EmTabIndicator(),
        indicatorSize: TabBarIndicatorSize.tab,
        dividerColor: s.navLine,
        overlayColor: WidgetStatePropertyAll(s.fill1),
        labelStyle: font(fontSize: 15, fontWeight: FontWeight.w600),
        unselectedLabelStyle: font(fontSize: 15, fontWeight: FontWeight.w500),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: s.navBg,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        height: 68,
        indicatorColor: p.accentTint,
        iconTheme: WidgetStateProperty.resolveWith((st) => IconThemeData(
            color: st.contains(WidgetState.selected) ? p.onAccentTint : p.textMuted, size: 22)),
        labelTextStyle: WidgetStateProperty.resolveWith((st) => font(
            fontSize: 12,
            fontWeight: st.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w500,
            color: st.contains(WidgetState.selected) ? p.onAccentTint : p.textMuted)),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: s.navBg,
        indicatorColor: p.accentTint,
        selectedIconTheme: IconThemeData(color: p.onAccentTint),
        unselectedIconTheme: IconThemeData(color: p.textMuted),
        selectedLabelTextStyle: font(fontSize: 12, fontWeight: FontWeight.w600, color: p.onAccentTint),
        unselectedLabelTextStyle: font(fontSize: 12, fontWeight: FontWeight.w500, color: p.textMuted),
      ),
      navigationDrawerTheme: NavigationDrawerThemeData(
        backgroundColor: s.popoverBg,
        surfaceTintColor: Colors.transparent,
        indicatorColor: p.accentTint,
      ),
      drawerTheme: DrawerThemeData(
        backgroundColor: s.popoverBg,
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(),
      ),
      dividerTheme: DividerThemeData(color: s.navLine, thickness: 1, space: 1),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: AppConstants.defaultPadding, vertical: 2),
        minVerticalPadding: 10,
        iconColor: p.textSecondary,
        selectedColor: p.onAccentTint,
        selectedTileColor: p.accentTint,
        shape: control,
        titleTextStyle: font(fontSize: 15, fontWeight: FontWeight.w500, color: p.text, letterSpacing: -0.16),
        subtitleTextStyle: font(fontSize: 13, color: p.textMuted),
        leadingAndTrailingTextStyle: font(fontSize: 13, color: p.textSecondary),
      ),
      // --em-dialog-bg with the lit rim.
      dialogTheme: DialogThemeData(
        backgroundColor: s.dialogBg,
        surfaceTintColor: Colors.transparent,
        elevation: 12,
        shape: glassShape,
        titleTextStyle: font(fontSize: 21, fontWeight: FontWeight.w600, color: p.text, letterSpacing: -0.4),
        contentTextStyle: font(fontSize: 15, color: p.textSecondary, height: 1.5),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: s.dialogBg,
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(top: Radius.circular(_cardRadius))),
      ),
      popupMenuTheme: PopupMenuThemeData(
        color: s.popoverBg,
        surfaceTintColor: Colors.transparent,
        elevation: 8,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(Em.radiusField), side: BorderSide(color: s.rimLine)),
        textStyle: font(fontSize: 15, color: p.text),
      ),
      menuTheme: MenuThemeData(
        style: MenuStyle(
          backgroundColor: WidgetStatePropertyAll(s.popoverBg),
          surfaceTintColor: const WidgetStatePropertyAll(Colors.transparent),
          shape: WidgetStatePropertyAll(RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(Em.radiusField), side: BorderSide(color: s.rimLine))),
        ),
      ),
      // --em-tip-bg / --em-tip-fg: the brand's inverted toast.
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: s.tipBg,
        contentTextStyle: font(fontSize: 15, color: s.tipFg),
        actionTextColor: Em.emberDeep,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Em.radiusField)),
      ),
      tooltipTheme: TooltipThemeData(
        decoration: BoxDecoration(color: s.tipBg, borderRadius: BorderRadius.circular(8)),
        textStyle: font(fontSize: 12, color: s.tipFg),
      ),
      dataTableTheme: DataTableThemeData(
        headingTextStyle: font(fontSize: 12, fontWeight: FontWeight.w600, color: p.textMuted),
        dataTextStyle: font(fontSize: 13, color: p.text),
        dividerThickness: 1,
        headingRowColor: const WidgetStatePropertyAll(Colors.transparent),
        horizontalMargin: 16,
        columnSpacing: 24,
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: Em.ember,
        linearTrackColor: s.fill2,
        circularTrackColor: s.fill2,
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith(
            (st) => st.contains(WidgetState.selected) ? Em.ember : Colors.transparent),
        side: BorderSide(color: s.fieldBorder, width: 1.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(5)),
      ),
      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith(
            (st) => st.contains(WidgetState.selected) ? Em.ember : s.fieldBorder),
      ),
      switchTheme: SwitchThemeData(
        trackColor: WidgetStateProperty.resolveWith(
            (st) => st.contains(WidgetState.selected) ? Em.ember : s.fill2),
        thumbColor: WidgetStateProperty.resolveWith(
            (st) => st.contains(WidgetState.selected) ? Colors.white : p.textSecondary),
        trackOutlineColor: WidgetStateProperty.resolveWith(
            (st) => st.contains(WidgetState.selected) ? Em.ember : s.rimLine),
      ),
      expansionTileTheme: ExpansionTileThemeData(
        shape: const Border(),
        collapsedShape: const Border(),
        iconColor: p.textSecondary,
        collapsedIconColor: p.textMuted,
      ),
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.iOS: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.windows: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.macOS: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.linux: FadeForwardsPageTransitionsBuilder(),
        },
      ),
    );
  }

  /// The type scale of tokens.json `typography.size`, with the Emergera
  /// tracking: -0.035em for display sizes, -0.022em for titles, -0.011em for
  /// body text (tokens.css --em-track-*).
  static TextTheme _textTheme(_Palette p) {
    TextStyle s(double size, FontWeight w, double lineHeight, [Color? c]) => font(
        fontSize: size,
        fontWeight: w,
        height: lineHeight / size,
        color: c ?? p.text,
        letterSpacing: size * (size >= 32 ? -0.035 : size >= 20 ? -0.022 : -0.011));
    return TextTheme(
      displayLarge: s(48, FontWeight.w600, 56),
      displayMedium: s(40, FontWeight.w600, 48),
      displaySmall: s(32, FontWeight.w600, 40),
      headlineLarge: s(28, FontWeight.w600, 36),
      headlineMedium: s(24, FontWeight.w600, 32),
      headlineSmall: s(22, FontWeight.w600, 30),
      titleLarge: s(20, FontWeight.w600, 28),
      titleMedium: s(16, FontWeight.w600, 24),
      titleSmall: s(14, FontWeight.w600, 20),
      bodyLarge: s(16, FontWeight.w400, 24),
      bodyMedium: s(14, FontWeight.w400, 20),
      bodySmall: s(12, FontWeight.w400, 16, p.textMuted),
      labelLarge: s(14, FontWeight.w500, 20),
      labelMedium: s(12, FontWeight.w500, 16, p.textSecondary),
      labelSmall: s(11, FontWeight.w500, 16, p.textMuted),
    );
  }
}
