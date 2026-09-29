import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'strings.dart';

/// The home of a class 1-5 student (SA-7): four large, coloured pictures
/// with one word each, larger text, and nothing else to read. The work
/// behind them is the same pages every student uses; a grown-up can also
/// do homework with the child from the parent account (My children).
class YoungHome extends StatelessWidget {
  const YoungHome({super.key});

  static const _tiles = [
    (icon: Icons.wb_sunny_rounded, label: 'Today', color: Color(0xFFF59E0B), path: '/school/today'),
    (icon: Icons.backpack_rounded, label: 'Homework', color: Color(0xFF3B82F6), path: '/school/my-homework'),
    (icon: Icons.star_rounded, label: 'How I am doing', color: Color(0xFF10B981), path: '/school/my-learning'),
    (icon: Icons.mail_rounded, label: 'Messages', color: Color(0xFF8B5CF6), path: '/school/inbox'),
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(builder: (context, c) {
      final cols = c.maxWidth > 700 ? 4 : 2;
      return GridView.count(
        padding: const EdgeInsets.all(20),
        crossAxisCount: cols,
        mainAxisSpacing: 16,
        crossAxisSpacing: 16,
        // A little taller than wide, so a two-line word fits at 375 px.
        childAspectRatio: 0.9,
        children: [
          for (final t in _tiles)
            // Read out as its one word, and announced as a button.
            Semantics(
              button: true,
              child: Material(
                color: t.color.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(28),
                child: InkWell(
                  borderRadius: BorderRadius.circular(28),
                  onTap: () => context.push(t.path),
                  child: Padding(
                    padding: const EdgeInsets.all(8),
                    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(t.icon, size: 72, color: t.color),
                      const SizedBox(height: 12),
                      Flexible(
                        child: Text(tr(t.label), textAlign: TextAlign.center, maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                      ),
                    ]),
                  ),
                ),
              ),
            ),
        ],
      );
    });
  }
}
