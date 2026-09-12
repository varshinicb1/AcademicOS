import 'package:flutter/material.dart';

/// Shown once, right after a demo-seeded offline build finishes populating
/// its sample department (see DemoSeeder), so a teacher who has never used
/// AcademicOS before sees a guided explanation of the real data already
/// sitting in front of them -- 5 teachers' worth of evaluated assessments
/// and one fully scanned-and-corrected answer sheet -- instead of just
/// landing on Home and having to guess what everything means. Real user
/// request: this build is going to 5 real teachers at a real school, and
/// nothing in it should require Claude (or anyone) standing over their
/// shoulder explaining it.
///
/// Deliberately five short slides, not a feature tour of the whole app --
/// each one points at something that's ALREADY on Home/Scan History right
/// now, so a teacher can back out of the tour mid-way and still find
/// everything it mentioned for themselves.
class AppTourPage extends StatefulWidget {
  const AppTourPage({super.key});

  @override
  State<AppTourPage> createState() => _AppTourPageState();
}

class _TourSlide {
  final IconData icon;
  final String title;
  final String body;
  const _TourSlide({required this.icon, required this.title, required this.body});
}

const _slides = [
  _TourSlide(
    icon: Icons.waving_hand_rounded,
    title: 'This app already has a real example loaded',
    body: 'Before you scan a single real answer sheet, look around -- this build comes '
        'pre-loaded with 5 teachers\' worth of genuinely graded Class X assessments and one '
        'fully scanned, corrected answer sheet, all run through the exact same AI grading '
        'engine your real classes will use. Nothing here is a mockup or a screenshot.',
  ),
  _TourSlide(
    icon: Icons.dashboard_customize_outlined,
    title: '"Today" is your starting point',
    body: 'New Assessment builds a fresh CBSE-aligned paper from the question bank. '
        'Scan & Grade photographs a student\'s answer sheet and AI-grades it on your phone, '
        'no internet needed. These two buttons are what you\'ll use for almost everything.',
  ),
  _TourSlide(
    icon: Icons.fact_check_outlined,
    title: 'Recent assessments -- 5 subjects, already graded',
    body: 'Tap any "(Demo)" assessment to see real per-question marks, teacher overrides, and '
        'mastery data for a full class of 10 students -- a strong performer down to a '
        'struggling one, exactly the spread a real class has.',
  ),
  _TourSlide(
    icon: Icons.document_scanner_outlined,
    title: 'Scan history -- see a real correction, photo and all',
    body: 'Open Ananya Iyer\'s finalized scan and choose "Raw scanned booklet" to see the '
        'actual photographed answer sheet, or "Corrected sheet" for the question-by-question '
        'marks. This is exactly what a real student\'s scan looks like once you finish grading it.',
  ),
  _TourSlide(
    icon: Icons.cleaning_services_outlined,
    title: 'Before your first real class',
    body: 'Once you\'re comfortable, open Settings and tap "Clear Demo Data" -- it removes '
        'every "(Demo)" record in one tap so your real students never mix with this sample. '
        'You can always revisit this tour from Settings later.',
  ),
];

class _AppTourPageState extends State<AppTourPage> {
  final _controller = PageController();
  int _index = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _finish() => Navigator.of(context).maybePop();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final last = _index == _slides.length - 1;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.only(right: 8, top: 4),
                child: TextButton(onPressed: _finish, child: const Text('Skip')),
              ),
            ),
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _slides.length,
                onPageChanged: (i) => setState(() => _index = i),
                itemBuilder: (context, i) {
                  final slide = _slides[i];
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 96,
                          height: 96,
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primaryContainer,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(slide.icon, size: 44, color: theme.colorScheme.onPrimaryContainer),
                        ),
                        const SizedBox(height: 32),
                        Text(
                          slide.title,
                          textAlign: TextAlign.center,
                          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          slide.body,
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _slides.length,
                (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: i == _index ? 22 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: i == _index ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: last
                      ? _finish
                      : () => _controller.nextPage(
                          duration: const Duration(milliseconds: 250), curve: Curves.easeOut),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Text(last ? 'Start exploring' : 'Next'),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
