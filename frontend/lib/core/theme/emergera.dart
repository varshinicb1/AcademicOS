import 'dart:math' as math;

import 'package:flutter/material.dart';

/// The Emergera brand's components, ported from its `components.css` and
/// `tokens.css` (v2.3): the aurora page background, glass cards with a lit
/// rim, the ember-glass primary button, the frosted glass button, pill chips,
/// rounded fields and the sunrise tab underline. `AppTheme` wires these into
/// every Material component, so screens get them without change.
///
/// Values carry the CSS token they come from. Two things CSS has that a
/// Flutter theme cannot carry are approximated: inset box-shadows (the
/// specular top edge) become the rim gradient's bright top, and a card's
/// two-layer background (glass base over the dark tint) becomes one colour,
/// the base's mid-point composited over the tint.
abstract final class Em {
  static const ember = Color(0xFFFF5A1F); // --em-ember
  static const emberDeep = Color(0xFFC2410C); // --em-ember-deep
  static const gold = Color(0xFFFFB020);
  static const flare = Color(0xFFFFC24A);

  /// --em-sunrise: 92deg, #FF5A1F -> #FF8A1F -> #FFC24A.
  static const sunrise = LinearGradient(
    colors: [Color(0xFFFF5A1F), Color(0xFFFF8A1F), Color(0xFFFFC24A)],
    stops: [0, .5, 1],
  );

  /// .em-btn--primary: radial-gradient(120% 140% at 50% 0%, ...). The brand's lit
  /// stops (#FF9A5C ... #D9430A) put a white label at 2.1-4.4:1, below the 4.5:1 AA
  /// asks of button text, so every stop here is the brand's ember-deep family
  /// (#C2410C is its own accent): white on them is 4.66-5.72:1.
  /// test/unit/theme_contrast_test.dart holds the stops to it.
  static const primaryFill = RadialGradient(
    center: Alignment(0, -1),
    radius: 1.4,
    colors: [Color(0xFFCF450D), Color(0xFFC9420C), Color(0xFFC2410C), Color(0xFFB93A0A)],
    stops: [0, .42, .70, 1],
  );

  /// --em-glow-ember, and the hover glow.
  static const glow = [
    BoxShadow(color: Color(0x61FF5A1F), offset: Offset(0, 8), blurRadius: 28),
    BoxShadow(color: Color(0x4DFF5A1F), offset: Offset(0, 2), blurRadius: 6),
  ];
  static const glowHover = [
    BoxShadow(color: Color(0x80FF5A1F), offset: Offset(0, 12), blurRadius: 36),
    BoxShadow(color: Color(0x59FF5A1F), offset: Offset(0, 2), blurRadius: 8),
  ];

  /// What a primary button casts on the light theme instead of [glow].
  static const softShadow = [BoxShadow(color: Color(0x33C2410C), offset: Offset(0, 2), blurRadius: 8)];

  static const radiusSm = 10.0; // --em-radius-sm
  static const radiusMd = 16.0; // --em-radius-md
  static const radiusLg = 24.0; // --em-radius-lg: cards
  static const radiusField = 14.0; // .em-input
  static const controlH = 48.0; // --em-control-h
}

/// The theme-dependent half of the brand: the dark and light blocks of
/// tokens.css.
@immutable
class EmSurfaces {
  const EmSurfaces({
    required this.glass,
    required this.rim,
    required this.fill1,
    required this.fill2,
    required this.rimLine,
    required this.fieldBg,
    required this.fieldBorder,
    required this.btnGlass,
    required this.btnGlassRim,
    required this.btnGlassShadow,
    required this.btnGloss,
    required this.chipOnBg,
    required this.chipOnFg,
    required this.chipEmberBg,
    required this.chipEmberFg,
    required this.chipEmberRim,
    required this.segOnBg,
    required this.navBg,
    required this.navLine,
    required this.dialogBg,
    required this.popoverBg,
    required this.tipBg,
    required this.tipFg,
    required this.link,
    required this.cardShadow,
    required this.auroraCore,
    required this.auroraBase,
    required this.auroraOpacity,
    required this.auroraBlend,
    required this.pageAuroraOpacity,
  });

  final Color glass;
  final Gradient rim;
  final Color fill1, fill2, rimLine;
  final Color fieldBg, fieldBorder;
  final Gradient btnGlass;
  final Color btnGlassRim;
  final List<BoxShadow> btnGlassShadow;
  final double btnGloss;
  final Color chipOnBg, chipOnFg, chipEmberBg, chipEmberFg, chipEmberRim, segOnBg;
  final Color navBg, navLine, dialogBg, popoverBg, tipBg, tipFg, link;
  final List<BoxShadow> cardShadow;
  final Color auroraCore, auroraBase;
  final double auroraOpacity;
  final BlendMode auroraBlend;
  final double pageAuroraOpacity;

  static EmSurfaces of(Brightness b) => b == Brightness.dark ? dark : light;

  static final dark = EmSurfaces(
    // --em-glass-base mid-point (white 5.75%) over --em-glass-tint rgba(10,12,24,.45).
    glass: Color.alphaBlend(const Color(0x0FFFFFFF), const Color(0x730A0C18)),
    // --em-glass-rim: lit at the top, fading down.
    rim: const LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [Color(0x57FFFFFF), Color(0x0FFFFFFF), Color(0x08FFFFFF)],
      stops: [0, .4, 1],
    ),
    fill1: const Color(0x0FFFFFFF),
    fill2: const Color(0x1AFFFFFF),
    rimLine: const Color(0x24FFFFFF),
    fieldBg: const Color(0x0DFFFFFF),
    fieldBorder: const Color(0x2EFFFFFF),
    btnGlass: const LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [Color(0x2EFFFFFF), Color(0x0DFFFFFF)],
    ),
    btnGlassRim: const Color(0x24FFFFFF),
    btnGlassShadow: const [],
    btnGloss: .35,
    chipOnBg: const Color(0xFFF5F5F7),
    chipOnFg: const Color(0xFF1D1D1F),
    chipEmberBg: const Color(0x24FF5A1F),
    chipEmberFg: const Color(0xFFFFB08A),
    chipEmberRim: const Color(0x59FF5A1F),
    segOnBg: const Color(0x29FFFFFF),
    navBg: const Color(0x9E07080F),
    navLine: const Color(0x12FFFFFF),
    // Opaque, not the brand's 92% glass: the paper behind a dialog or the
    // bank picker read through its fields (QA P-34).
    dialogBg: const Color(0xFF101220),
    popoverBg: const Color(0xFF15182A), // --em-solid-popover
    tipBg: const Color(0xFFF5F5F7),
    tipFg: const Color(0xFF1D1D1F),
    link: const Color(0xFF8AB4FF), // --em-sky
    cardShadow: const [
      BoxShadow(color: Color(0x38000000), offset: Offset(0, 2), blurRadius: 4),
      BoxShadow(color: Color(0x47000000), offset: Offset(0, 8), blurRadius: 24),
    ],
    auroraCore: const Color(0xFF120E1C),
    auroraBase: const Color(0xFF07080F),
    auroraOpacity: .85,
    auroraBlend: BlendMode.screen,
    pageAuroraOpacity: .42,
  );

  static final light = EmSurfaces(
    // --em-glass-base mid-point (white 83%) over --em-glass-tint rgba(255,255,255,.62).
    glass: Color.alphaBlend(const Color(0xD4FFFFFF), const Color(0x9EFFFFFF)),
    rim: const LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [Color(0x0F000000), Color(0x17000000)],
    ),
    fill1: const Color(0x09000000),
    fill2: const Color(0x0F000000),
    rimLine: const Color(0x1A000000),
    fieldBg: const Color(0xFFFFFFFF),
    fieldBorder: const Color(0x2E000000),
    btnGlass: const LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [Color(0xFFFFFFFF), Color(0xFFF3F3F6)],
    ),
    btnGlassRim: const Color(0x1F000000),
    btnGlassShadow: const [
      BoxShadow(color: Color(0x0F101220), offset: Offset(0, 1), blurRadius: 2),
      BoxShadow(color: Color(0x0F101220), offset: Offset(0, 4), blurRadius: 14),
    ],
    btnGloss: 0,
    chipOnBg: const Color(0xFF1D1D1F),
    chipOnFg: const Color(0xFFFFFFFF),
    chipEmberBg: const Color(0x17FF5A1F),
    chipEmberFg: const Color(0xFFC2410C),
    chipEmberRim: const Color(0x40FF5A1F),
    segOnBg: const Color(0xFFFFFFFF),
    navBg: const Color(0xCCFFFFFF),
    navLine: const Color(0x14000000),
    // Opaque for the same reason as the dark surfaces' (QA P-34).
    dialogBg: const Color(0xFFFFFFFF),
    popoverBg: const Color(0xFFFFFFFF),
    tipBg: const Color(0xFF1D1D1F),
    tipFg: const Color(0xFFFFFFFF),
    link: const Color(0xFF0055CC),
    cardShadow: const [
      BoxShadow(color: Color(0x0D101220), offset: Offset(0, 1), blurRadius: 2),
      BoxShadow(color: Color(0x12101220), offset: Offset(0, 6), blurRadius: 20),
    ],
    auroraCore: const Color(0xFFFFF0E3),
    auroraBase: const Color(0xFFFFFFFF),
    auroraOpacity: .20,
    auroraBlend: BlendMode.multiply,
    pageAuroraOpacity: .6,
  );
}

/// A rounded rectangle whose 1 px edge is a vertical gradient: the brand's
/// `.em-card::before` lit rim, brighter at the top like light catching glass.
class EmRimBorder extends RoundedRectangleBorder {
  const EmRimBorder({super.borderRadius, required this.rim});

  final Gradient rim;

  @override
  void paint(Canvas canvas, Rect rect, {TextDirection? textDirection}) {
    final rrect = borderRadius.resolve(textDirection).toRRect(rect).deflate(.5);
    canvas.drawRRect(
      rrect,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..shader = rim.createShader(rect),
    );
  }

  @override
  EmRimBorder copyWith({BorderSide? side, BorderRadiusGeometry? borderRadius}) =>
      EmRimBorder(borderRadius: borderRadius ?? this.borderRadius, rim: rim);

  @override
  ShapeBorder scale(double t) => EmRimBorder(borderRadius: borderRadius * t, rim: rim);

  @override
  bool operator ==(Object other) =>
      other is EmRimBorder && other.borderRadius == borderRadius && other.rim == rim;

  @override
  int get hashCode => Object.hash(borderRadius, rim);
}

/// `.em-btn--primary`: ember glass lit from within -- the radial ember fill,
/// a dark-orange rim, the ember glow, and the curved specular gloss across
/// the top half (`.em-btn::before`). For [ButtonStyle.backgroundBuilder].
Widget emPrimaryBackground(BuildContext context, Set<WidgetState> states, Widget? child) {
  final disabled = states.contains(WidgetState.disabled);
  final hot = states.contains(WidgetState.hovered) || states.contains(WidgetState.focused);
  // The ember glow is the brand's night look. On the light default it is a loud halo
  // around every button, so light gets a soft shadow and a fainter gloss.
  final light = Theme.of(context).brightness == Brightness.light;
  return Opacity(
    opacity: disabled ? .45 : 1,
    child: DecoratedBox(
      decoration: ShapeDecoration(
        shape: const StadiumBorder(side: BorderSide(color: Color(0x8CD2460A))),
        gradient: Em.primaryFill,
        shadows: disabled ? const [] : light ? Em.softShadow : (hot ? Em.glowHover : Em.glow),
      ),
      child: Stack(alignment: Alignment.center, children: [
        _Gloss(opacity: (hot ? .75 : .5) * (light ? .5 : 1)),
        if (child != null) child,
      ]),
    ),
  );
}

/// `.em-btn--glass`: a clear frosted bubble with a lit rim.
Widget emGlassBackground(BuildContext context, Set<WidgetState> states, Widget? child) {
  final s = EmSurfaces.of(Theme.of(context).brightness);
  final disabled = states.contains(WidgetState.disabled);
  final hot = states.contains(WidgetState.hovered) || states.contains(WidgetState.focused);
  return Opacity(
    opacity: disabled ? .45 : 1,
    child: DecoratedBox(
      decoration: ShapeDecoration(
        shape: StadiumBorder(side: BorderSide(color: hot ? s.rimLine.withValues(alpha: .34) : s.btnGlassRim)),
        gradient: s.btnGlass,
        shadows: s.btnGlassShadow,
      ),
      child: Stack(alignment: Alignment.center, children: [
        if (s.btnGloss > 0) _Gloss(opacity: hot ? s.btnGloss + .2 : s.btnGloss),
        if (child != null) child,
      ]),
    ),
  );
}

/// The curved highlight across a button's top half: inset 6% each side,
/// 52% tall, white 60% fading to nothing.
class _Gloss extends StatelessWidget {
  const _Gloss({required this.opacity});
  final double opacity;

  @override
  Widget build(BuildContext context) => Positioned.fill(
        child: IgnorePointer(
          child: Align(
            alignment: Alignment.topCenter,
            child: FractionallySizedBox(
              widthFactor: .88,
              heightFactor: .52,
              child: Padding(
                padding: const EdgeInsets.only(top: 1),
                child: Opacity(
                  opacity: opacity,
                  child: const DecoratedBox(
                    decoration: ShapeDecoration(
                      shape: StadiumBorder(),
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [Color(0x99FFFFFF), Color(0x00FFFFFF)],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );
}

/// `.em-tabs [aria-selected="true"]::after`: a 2 px sunrise bar, inset
/// 10 px, with an ember glow.
class EmTabIndicator extends Decoration {
  const EmTabIndicator();

  @override
  BoxPainter createBoxPainter([VoidCallback? onChanged]) => _EmTabPainter();
}

class _EmTabPainter extends BoxPainter {
  @override
  void paint(Canvas canvas, Offset offset, ImageConfiguration cfg) {
    final size = cfg.size;
    if (size == null || size.width <= 20) return;
    final bar = Rect.fromLTWH(offset.dx + 10, offset.dy + size.height - 2, size.width - 20, 2);
    final rrect = RRect.fromRectAndRadius(bar, const Radius.circular(2));
    canvas.drawRRect(
      rrect,
      Paint()
        ..color = const Color(0x99FF5A1F)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 5),
    );
    canvas.drawRRect(rrect, Paint()..shader = Em.sunrise.createShader(bar));
  }
}

/// The page background: the brand's fixed aurora (`.em-aurora--fixed
/// .em-aurora--no-horizon`) -- a warm core over ink and four soft glows,
/// ember, amber, violet and rose, drifting over 28 s. Light theme is the
/// dawn wash the brand defines (20% glows, multiplied over white). Still
/// when the platform asks for reduced motion.
class EmBackdrop extends StatefulWidget {
  const EmBackdrop({super.key, required this.child});
  final Widget child;

  @override
  State<EmBackdrop> createState() => _EmBackdropState();
}

class _EmBackdropState extends State<EmBackdrop> with SingleTickerProviderStateMixin {
  late final AnimationController _drift =
      AnimationController(vsync: this, duration: const Duration(seconds: 28));

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final still = MediaQuery.maybeDisableAnimationsOf(context) ?? false;
    if (still) {
      _drift.stop();
    } else if (!_drift.isAnimating) {
      _drift.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _drift.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = EmSurfaces.of(Theme.of(context).brightness);
    return Stack(fit: StackFit.expand, children: [
      RepaintBoundary(child: CustomPaint(painter: _AuroraPainter(_drift, s))),
      widget.child,
    ]);
  }
}

class _AuroraPainter extends CustomPainter {
  _AuroraPainter(this.t, this.s) : super(repaint: t);
  final Animation<double> t;
  final EmSurfaces s;

  // .em-aurora i:nth-child(1..4): size in vmax, left as a share of the width
  // (or from the right), top above the horizon in vmax, colour, and the
  // blob's own speed and phase.
  static const _blobs = [
    (w: 62.0, h: 34.0, x: .19, right: false, up: 18.0, c: Color(0xF2FF5A1F), speed: 1.0, phase: 0.0),
    (w: 46.0, h: 26.0, x: .40, right: false, up: 20.0, c: Color(0xBFFFA41B), speed: 1.25, phase: .21),
    (w: 50.0, h: 30.0, x: -.12, right: false, up: 26.0, c: Color(0x8C6C4DFF), speed: .83, phase: .43),
    (w: 52.0, h: 30.0, x: -.14, right: true, up: 30.0, c: Color(0x73FF3D6E), speed: .91, phase: .11),
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    // .page-aurora (site.css): the whole layer at 42% (60% light) over the
    // page colour, its horizon below the window (--aurora-y: 115%), so the
    // glow rises from the bottom edge; phones and touch screens (<= 820 px)
    // get the plain page, as the brand turns the costly layer off there.
    canvas.drawRect(rect, Paint()..color = s.auroraBase);
    if (size.width <= 820) return;
    final horizon = size.height * 1.15;
    canvas.saveLayer(rect, Paint()..color = Color.fromRGBO(0, 0, 0, s.pageAuroraOpacity));
    canvas.drawRect(
      rect,
      Paint()
        ..shader = RadialGradient(
          center: const Alignment(0, 1.3),
          radius: 1.2,
          colors: [s.auroraCore, s.auroraBase],
          stops: const [0, .6],
        ).createShader(rect),
    );
    final vmax = math.max(size.width, size.height) / 100;
    for (var i = 0; i < _blobs.length; i++) {
      final b = _blobs[i];
      final w = b.w * vmax, h = b.h * vmax;
      final left = b.right ? size.width - w - b.x * size.width : b.x * size.width;
      final top = horizon - b.up * vmax;
      // em-drift: (-6%, 2%) scale 1 -> (4%, -3%) 1.08 -> (8%, 1%) .96, eased.
      final p = Curves.easeInOutCubic.transform(((t.value * b.speed + b.phase) % 1.0));
      final (dx, dy, sc) = p < .5
          ? _lerp3((-.06, .02, 1.0), (.04, -.03, 1.08), p * 2)
          : _lerp3((.04, -.03, 1.08), (.08, .01, .96), (p - .5) * 2);
      final cx = left + w / 2 + dx * w, cy = top + h / 2 + dy * h;
      canvas.save();
      canvas.translate(cx, cy);
      canvas.scale(sc, sc * h / w);
      final r = w / 2;
      final circle = Rect.fromCircle(center: Offset.zero, radius: r);
      canvas.drawCircle(
        Offset.zero,
        r,
        Paint()
          ..blendMode = s.auroraBlend
          ..shader = RadialGradient(colors: [
            b.c.withValues(alpha: b.c.a * s.auroraOpacity),
            b.c.withValues(alpha: 0),
          ]).createShader(circle),
      );
      canvas.restore();
    }
    canvas.restore();
  }

  static (double, double, double) _lerp3((double, double, double) a, (double, double, double) b, double t) =>
      (a.$1 + (b.$1 - a.$1) * t, a.$2 + (b.$2 - a.$2) * t, a.$3 + (b.$3 - a.$3) * t);

  @override
  bool shouldRepaint(_AuroraPainter old) => old.s != s;
}
