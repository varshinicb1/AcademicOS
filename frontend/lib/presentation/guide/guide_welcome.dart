import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../core/session/current_session.dart';
import '../shared/device_memory.dart';
import '../shared/widgets/shell.dart';
import '../workspace/app_mode.dart';
import 'guide_content.dart';
import 'guide_page.dart';

/// What each person chose on the welcome, kept on this device per user:
/// 'guide' (Show me around) or 'later' (Not now, or dismissed).
abstract final class GuideWelcomeMemory {
  static String _key(String userId) => 'guide_welcome:$userId';

  static String? choiceOf(String userId) => DeviceMemory.read(_key(userId)) as String?;

  static void remember(String userId, String choice) => DeviceMemory.write(_key(userId), choice);
}

/// The signed-in user's id, or '' with no local store (a test that mounts a
/// page alone).
String _signedInUser() => Hive.isBoxOpen('academicos_cache') ? CurrentSession.userId : '';

/// Users already welcomed in this run: the shell can be rebuilt (an owner
/// switching schools) while the dialog is still open.
final Set<String> _askedThisRun = {};

/// Forget who was welcomed in this run (tests).
@visibleForTesting
void resetGuideWelcomeRun() => _askedThisRun.clear();

/// Shows the first-time welcome over the app's pages: the first time a
/// person signs in on this device, a short dialog offers Show me around
/// (the Guide) or Not now. Either answer, or dismissing it, is remembered
/// for that person, so it is not shown to them again here; the Guide stays
/// in the menu and behind the question mark on the pages.
///
/// Wraps the shell in the router (app_router.dart), so it sees every page
/// but never the sign-in screen.
class GuideWelcome extends StatefulWidget {
  const GuideWelcome({super.key, required this.child, this.userId, this.role});

  final Widget child;

  /// Who is signed in; the session's user and role when null (tests pass them).
  final String? userId;
  final String? role;

  @override
  State<GuideWelcome> createState() => _GuideWelcomeState();
}

class _GuideWelcomeState extends State<GuideWelcome> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeWelcome());
  }

  Future<void> _maybeWelcome() async {
    if (!mounted) return;
    final user = widget.userId ?? _signedInUser();
    final role = widget.role ?? signedInRole();
    if (user.isEmpty || !guideAvailableFor(role)) return;
    if (GuideWelcomeMemory.choiceOf(user) != null || _askedThisRun.contains(user)) return;
    _askedThisRun.add(user);
    final router = GoRouter.of(context);
    final showMe = await showDialog<bool>(context: context, builder: (_) => WelcomeDialog(role: role));
    GuideWelcomeMemory.remember(user, showMe == true ? 'guide' : 'later');
    if (showMe == true) router.go(guidePath);
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

/// The welcome itself: what the Guide is, where it stays, and the two choices.
class WelcomeDialog extends StatelessWidget {
  const WelcomeDialog({super.key, required this.role});

  final String role;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      key: const ValueKey('guide-welcome'),
      icon: const Icon(Icons.waving_hand_outlined),
      title: const Text('Welcome to AcademicOS'),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420),
        child: Text(
          'A short guide shows, step by step, the jobs a ${guideRoleName(role)} does most, '
          'with a button that takes you to each page.\n\n'
          // The phone apps have tabs, not the menu.
          '${appMode == AppMode.console ? 'You can open it any time: Guide in the menu, or the question mark '
              'at the top of a page.' : 'You can open it any time from the question mark at the top of a page.'}',
        ),
      ),
      actions: [
        TextButton(
          key: const ValueKey('guide-welcome-later'),
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Not now'),
        ),
        FilledButton(
          key: const ValueKey('guide-welcome-go'),
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('Show me around'),
        ),
      ],
    );
  }
}
