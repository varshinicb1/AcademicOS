import 'package:flutter/material.dart';

import '../constants/app_constants.dart';

/// The palette the whole app draws from, taken from the design system
/// (design/tokens.json): slate neutrals, one indigo accent, and white cards
/// on a cool off-white canvas. The canvas is deliberately not #FFFFFF --
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

  static const light = _Palette(
    brightness: Brightness.light,
    canvas: Color(0xFFF8FAFC), // neutral 50
    card: Color(0xFFFFFFFF),
    inset: Color(0xFFF1F5F9), // neutral 100
    line: Color(0xFFE2E8F0), // neutral 200
    lineStrong: Color(0xFFCBD5E1), // neutral 300
    text: Color(0xFF0F172A), // neutral 900
    textSecondary: Color(0xFF475569), // neutral 600
    textMuted: Color(0xFF64748B), // neutral 500
    accent: Color(0xFF4F46E5), // brand 600
    accentHover: Color(0xFF4338CA), // brand 700
    onAccent: Color(0xFFFFFFFF),
    accentTint: Color(0xFFEEF2FF), // brand 50
    onAccentTint: Color(0xFF3730A3),
    danger: Color(0xFFB91C1C),
    dangerTint: Color(0xFFFEF2F2),
    onDangerTint: Color(0xFF7F1D1D),
  );

  static const dark = _Palette(
    brightness: Brightness.dark,
    canvas: Color(0xFF0B1120),
    card: Color(0xFF111827),
    inset: Color(0xFF1E293B),
    line: Color(0xFF1F2937),
    lineStrong: Color(0xFF334155),
    text: Color(0xFFF1F5F9),
    textSecondary: Color(0xFFCBD5E1),
    textMuted: Color(0xFF94A3B8),
    accent: Color(0xFF818CF8),
    accentHover: Color(0xFFA5B4FC),
    onAccent: Color(0xFF0F172A),
    accentTint: Color(0xFF1E1B4B),
    onAccentTint: Color(0xFFC7D2FE),
    danger: Color(0xFFF87171),
    dangerTint: Color(0xFF450A0A),
    onDangerTint: Color(0xFFFECACA),
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
        onError: brightness == Brightness.light ? Colors.white : const Color(0xFF0F172A),
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
        inversePrimary: brightness == Brightness.light ? const Color(0xFFA5B4FC) : const Color(0xFF4F46E5),
        surfaceTint: Colors.transparent,
      );
}

/// The design tokens' status and accent colours as constants, for code that
/// has no BuildContext (enum colour getters, PDF-free widgets built as
/// `const`). They are the light theme's text-strength shades: legible on
/// white as text or an icon, and soft enough behind 10% alpha as a fill.
/// Prefer [StatusColors.of] where a context exists, which follows dark mode.
abstract final class AppColors {
  static const Color success = Color(0xFF047857);
  static const Color warning = Color(0xFFB45309);
  static const Color danger = Color(0xFFB91C1C);
  static const Color info = Color(0xFF1D4ED8);
  static const Color accent = Color(0xFF4F46E5);
  static const Color neutral = Color(0xFF475569);
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
    success: Color(0xFF047857), successBg: Color(0xFFECFDF5), successBorder: Color(0xFFA7F3D0),
    warning: Color(0xFFB45309), warningBg: Color(0xFFFFFBEB), warningBorder: Color(0xFFFDE68A),
    danger: Color(0xFFB91C1C), dangerBg: Color(0xFFFEF2F2), dangerBorder: Color(0xFFFECACA),
    info: Color(0xFF1D4ED8), infoBg: Color(0xFFEFF6FF), infoBorder: Color(0xFFBFDBFE),
  );

  static const dark = StatusColors(
    success: Color(0xFF6EE7B7), successBg: Color(0xFF022C22), successBorder: Color(0xFF065F46),
    warning: Color(0xFFFCD34D), warningBg: Color(0xFF2A1A03), warningBorder: Color(0xFF78350F),
    danger: Color(0xFFFCA5A5), dangerBg: Color(0xFF2A0A0A), dangerBorder: Color(0xFF7F1D1D),
    info: Color(0xFF93C5FD), infoBg: Color(0xFF0B1B3A), infoBorder: Color(0xFF1E3A8A),
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

  static const double _radius = 8; // tokens radius.lg: controls
  static const double _cardRadius = 12; // tokens radius.xl: cards and dialogs

  static ThemeData _build(_Palette p, StatusColors status) {
    final scheme = p.scheme;
    final control = RoundedRectangleBorder(borderRadius: BorderRadius.circular(_radius));
    OutlineInputBorder field(Color c, [double w = 1]) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(_radius),
          borderSide: BorderSide(color: c, width: w),
        );
    final buttonText = font(fontSize: 14, fontWeight: FontWeight.w500);
    // No vertical padding: the minimum height decides, and it follows the
    // platform's density (40 px on a phone, 32 px at a desktop's compact
    // density), as Material's own buttons do. A padded button grew on a
    // laptop wherever a page added a little padding of its own.
    const buttonPadding = EdgeInsets.symmetric(horizontal: 16);

    return ThemeData(
      useMaterial3: true,
      brightness: p.brightness,
      colorScheme: scheme,
      extensions: [status],
      fontFamily: AppConstants.fontFamily,
      textTheme: _textTheme(p),
      scaffoldBackgroundColor: p.canvas,
      canvasColor: p.canvas,
      dividerColor: p.line,
      splashFactory: InkSparkle.splashFactory,
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        backgroundColor: p.card,
        surfaceTintColor: Colors.transparent,
        foregroundColor: p.text,
        shape: Border(bottom: BorderSide(color: p.line)),
        titleTextStyle: font(fontSize: 18, fontWeight: FontWeight.w600, color: p.text),
        iconTheme: IconThemeData(color: p.textSecondary, size: 22),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: p.card,
        surfaceTintColor: Colors.transparent,
        margin: const EdgeInsets.all(0),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(_cardRadius),
          side: BorderSide(color: p.line),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: p.accent,
          foregroundColor: p.onAccent,
          minimumSize: const Size(64, 40),
          padding: buttonPadding,
          shape: control,
          textStyle: buttonText,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: p.accent,
          foregroundColor: p.onAccent,
          elevation: 0,
          minimumSize: const Size(64, 40),
          padding: buttonPadding,
          shape: control,
          textStyle: buttonText,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: p.text,
          backgroundColor: p.card,
          side: BorderSide(color: p.lineStrong),
          minimumSize: const Size(64, 40),
          padding: buttonPadding,
          shape: control,
          textStyle: buttonText,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: p.accent,
          minimumSize: const Size(48, 40),
          padding: const EdgeInsets.symmetric(horizontal: 12),
          shape: control,
          textStyle: buttonText,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(foregroundColor: p.textSecondary, shape: control),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: p.accent,
        foregroundColor: p.onAccent,
        elevation: 0,
        focusElevation: 0,
        hoverElevation: 0,
        highlightElevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_cardRadius)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: p.card,
        isDense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        border: field(p.lineStrong),
        enabledBorder: field(p.lineStrong),
        focusedBorder: field(p.accent, 1.5),
        errorBorder: field(p.danger),
        focusedErrorBorder: field(p.danger, 1.5),
        disabledBorder: field(p.line),
        labelStyle: font(color: p.textSecondary, fontSize: 14),
        floatingLabelStyle: font(color: p.accent, fontSize: 14, fontWeight: FontWeight.w500),
        hintStyle: font(color: p.textMuted, fontSize: 14),
        helperStyle: font(color: p.textMuted, fontSize: 12),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: p.inset,
        selectedColor: p.accentTint,
        disabledColor: p.inset,
        side: BorderSide(color: p.line),
        checkmarkColor: p.onAccentTint,
        labelStyle: font(color: p.textSecondary, fontSize: 13, fontWeight: FontWeight.w500),
        secondaryLabelStyle: font(color: p.onAccentTint, fontSize: 13, fontWeight: FontWeight.w500),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        shape: const StadiumBorder(),
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          side: WidgetStatePropertyAll(BorderSide(color: p.line)),
          shape: WidgetStatePropertyAll(control),
          backgroundColor: WidgetStateProperty.resolveWith(
              (s) => s.contains(WidgetState.selected) ? p.accentTint : p.card),
          foregroundColor: WidgetStateProperty.resolveWith(
              (s) => s.contains(WidgetState.selected) ? p.onAccentTint : p.textSecondary),
          textStyle: WidgetStatePropertyAll(font(fontSize: 13, fontWeight: FontWeight.w500)),
        ),
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: p.text,
        unselectedLabelColor: p.textMuted,
        indicatorColor: p.accent,
        indicatorSize: TabBarIndicatorSize.label,
        dividerColor: p.line,
        labelStyle: font(fontSize: 14, fontWeight: FontWeight.w600),
        unselectedLabelStyle: font(fontSize: 14, fontWeight: FontWeight.w500),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: p.card,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        height: 68,
        indicatorColor: p.accentTint,
        iconTheme: WidgetStateProperty.resolveWith((s) => IconThemeData(
            color: s.contains(WidgetState.selected) ? p.onAccentTint : p.textMuted, size: 22)),
        labelTextStyle: WidgetStateProperty.resolveWith((s) => font(
            fontSize: 12,
            fontWeight: s.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w500,
            color: s.contains(WidgetState.selected) ? p.onAccentTint : p.textMuted)),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: p.card,
        indicatorColor: p.accentTint,
        selectedIconTheme: IconThemeData(color: p.onAccentTint),
        unselectedIconTheme: IconThemeData(color: p.textMuted),
        selectedLabelTextStyle: font(fontSize: 12, fontWeight: FontWeight.w600, color: p.onAccentTint),
        unselectedLabelTextStyle: font(fontSize: 12, fontWeight: FontWeight.w500, color: p.textMuted),
      ),
      navigationDrawerTheme: NavigationDrawerThemeData(
        backgroundColor: p.card,
        surfaceTintColor: Colors.transparent,
        indicatorColor: p.accentTint,
      ),
      drawerTheme: DrawerThemeData(
        backgroundColor: p.card,
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(),
      ),
      dividerTheme: DividerThemeData(color: p.line, thickness: 1, space: 1),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: AppConstants.defaultPadding, vertical: 2),
        minVerticalPadding: 10,
        iconColor: p.textSecondary,
        selectedColor: p.onAccentTint,
        selectedTileColor: p.accentTint,
        shape: control,
        titleTextStyle: font(fontSize: 14, fontWeight: FontWeight.w500, color: p.text),
        subtitleTextStyle: font(fontSize: 13, color: p.textMuted),
        leadingAndTrailingTextStyle: font(fontSize: 13, color: p.textSecondary),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: p.card,
        surfaceTintColor: Colors.transparent,
        elevation: 8,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_cardRadius)),
        titleTextStyle: font(fontSize: 18, fontWeight: FontWeight.w600, color: p.text),
        contentTextStyle: font(fontSize: 14, color: p.textSecondary, height: 1.45),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: p.card,
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(top: Radius.circular(_cardRadius))),
      ),
      popupMenuTheme: PopupMenuThemeData(
        color: p.card,
        surfaceTintColor: Colors.transparent,
        elevation: 6,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(_radius), side: BorderSide(color: p.line)),
        textStyle: font(fontSize: 14, color: p.text),
      ),
      menuTheme: MenuThemeData(
        style: MenuStyle(
          backgroundColor: WidgetStatePropertyAll(p.card),
          surfaceTintColor: const WidgetStatePropertyAll(Colors.transparent),
          shape: WidgetStatePropertyAll(RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(_radius), side: BorderSide(color: p.line))),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: p.brightness == Brightness.light ? const Color(0xFF0F172A) : p.inset,
        contentTextStyle: font(fontSize: 14, color: const Color(0xFFF8FAFC)),
        actionTextColor: const Color(0xFFA5B4FC),
        shape: control,
      ),
      tooltipTheme: TooltipThemeData(
        decoration: BoxDecoration(
          color: p.brightness == Brightness.light ? const Color(0xFF0F172A) : p.inset,
          borderRadius: BorderRadius.circular(6),
        ),
        textStyle: font(fontSize: 12, color: const Color(0xFFF8FAFC)),
      ),
      dataTableTheme: DataTableThemeData(
        headingTextStyle: font(fontSize: 12, fontWeight: FontWeight.w600, color: p.textMuted),
        dataTextStyle: font(fontSize: 13, color: p.text),
        dividerThickness: 1,
        headingRowColor: WidgetStatePropertyAll(p.card),
        horizontalMargin: 16,
        columnSpacing: 24,
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: p.accent,
        linearTrackColor: p.inset,
        circularTrackColor: p.inset,
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? p.accent : Colors.transparent),
        side: BorderSide(color: p.lineStrong, width: 1.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
      ),
      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? p.accent : p.lineStrong),
      ),
      switchTheme: SwitchThemeData(
        trackColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? p.accent : p.inset),
        thumbColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? p.onAccent : p.card),
        trackOutlineColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? p.accent : p.lineStrong),
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

  /// The type scale of tokens.json `typography.size`: 14/20 body, 16 card
  /// titles, 20 subheads, 24 page titles. Letter spacing stays 0: Inter is
  /// drawn for it, and Material's tracked-out defaults read loose.
  static TextTheme _textTheme(_Palette p) {
    TextStyle s(double size, FontWeight w, double lineHeight, [Color? c]) =>
        font(fontSize: size, fontWeight: w, height: lineHeight / size, color: c ?? p.text, letterSpacing: 0);
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
