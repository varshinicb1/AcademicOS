class AppConstants {
  static const String appName = 'AcademicOS';
  static const String appTagline = 'CBSE Academic Brain';
  
  // API
  static const String defaultBaseUrl = 'http://localhost:8000/api/v1';
  static const Duration apiTimeout = Duration(seconds: 30);
  static const int maxRetries = 3;
  
  // Storage
  static const String dbName = 'academicos.db';
  static const int dbVersion = 1;
  static const String hiveBoxName = 'academicos_cache';
  
  // Sync
  static const Duration syncInterval = Duration(minutes: 15);
  static const int maxOfflineDays = 30;

  // No "current school" constant lives here any more: a screen gets the
  // school and user from CurrentSession (core/session/current_session.dart),
  // i.e. whoever signed in. A fixed id here made the live web app show every
  // real school the demo school's (empty) data (re-audit, 2026-09-22).
  
  // UI
  static const double defaultPadding = 16.0;
  static const double smallPadding = 8.0;
  static const double largePadding = 24.0;
  static const double cardElevation = 2.0;
  static const double borderRadius = 12.0;
  static const Duration animationDuration = Duration(milliseconds: 200);

  /// Below this logical width the app is laid out for a touch screen held in
  /// a hand: the shell collapses its side navigation into a drawer
  /// (presentation/shared/widgets/shell.dart) and a main action pins itself
  /// to a 48 px tap target (presentation/shared/widgets/common_widgets.dart).
  /// One number for both so a screen cannot be "mobile" for its navigation
  /// and "desktop" for its buttons at the same width.
  static const double mobileBreakpoint = 800.0;

  /// The text scale the app renders at, whatever the browser asks for.
  ///
  /// Android Chrome's accessibility text setting and a desktop browser's page
  /// zoom both arrive as `MediaQuery.textScaler`; main.dart's `builder`
  /// clamps it to this range before any screen is laid out, so a browser at
  /// 200% reaches a screen as 1.3 and nothing above that is reachable in the
  /// shipped app. Named here because test/responsive applies the same clamp
  /// ([appForTest]) -- a suite driven past [maxTextScale] would be measuring
  /// a state no teacher can get to.
  static const double minTextScale = 0.85;
  static const double maxTextScale = 1.3;
  
  // CBSE
  static const int minGrade = 1;
  static const int maxGrade = 12;
  static const List<String> subjects = [
    'Mathematics',
    'Science',
    'Social Science',
    'English',
    'Hindi',
    'Sanskrit',
    'Computer Science',
    'Physical Education',
    'Accountancy',
    'Business Studies',
    'Economics',
    'Physics',
    'Chemistry',
    'Biology',
    'History',
    'Geography',
    'Political Science',
  ];
  
  static const List<String> bloomLevels = [
    'Remember',
    'Understand',
    'Apply',
    'Analyze',
    'Evaluate',
    'Create',
  ];
  
  static const List<String> competencyDomains = [
    'Knowledge',
    'Understanding',
    'Application',
    'Skill',
    'Attitude',
  ];
  
  // Colors (semantic)
  static const int primaryColorValue = 0xFF1E3A5F;      // Deep navy
  static const int secondaryColorValue = 0xFF2E86C1;    // Bright blue
  static const int accentColorValue = 0xFFE67E22;       // Orange
  static const int successColorValue = 0xFF27AE60;      // Green
  static const int warningColorValue = 0xFFF39C12;      // Amber
  static const int errorColorValue = 0xFFE74C3C;        // Red
  static const int surfaceColorValue = 0xFFFFFFFF;      // White
  static const int backgroundColorValue = 0xFFF8FAFC;   // Light gray
  
  // Typography
  static const String fontFamily = 'Inter';
  static const String monoFontFamily = 'JetBrainsMono';
  
  // Feature flags
  static const bool enableOfflineMode = true;
  static const bool enableAnalytics = true;
  static const bool enableTeacherTools = true;
  static const bool enableParentView = false; // Future
}