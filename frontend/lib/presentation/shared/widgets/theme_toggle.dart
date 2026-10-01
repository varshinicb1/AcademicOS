import 'package:flutter/material.dart';

import '../../../core/theme/theme_controller.dart';

/// The light/dark switch: the brand template's theme toggle. It shows what a
/// tap switches to -- a sun in the dark theme, a moon in the light one -- and
/// the choice is kept on the device ([ThemeController]).
///
/// It reads the theme on screen rather than the stored mode, so with the
/// system setting it still switches to the other of the two.
class ThemeToggleButton extends StatelessWidget {
  const ThemeToggleButton({super.key});

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return IconButton(
      key: const ValueKey('theme-toggle'),
      tooltip: dark ? 'Light theme' : 'Dark theme',
      icon: Icon(dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined),
      onPressed: () => ThemeController.set(dark ? ThemeMode.light : ThemeMode.dark),
    );
  }
}
