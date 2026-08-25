import 'package:flutter/material.dart';

import '../../shared/widgets/shell.dart';

/// Real Privacy Policy / Terms content -- was a dead `() {}` button before
/// this. Written to be honestly accurate to this build's actual state
/// (see docs/compliance.md), not marketing boilerplate: this app is not yet
/// DPDP-registered, ISO 27001 certified, or SOC 2 audited, and this text
/// says so rather than implying otherwise. Update this alongside
/// docs/compliance.md, not independently of it.
class LegalPage extends StatelessWidget {
  final String doc; // 'privacy' or 'terms'
  const LegalPage({super.key, required this.doc});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isPrivacy = doc == 'privacy';
    return Scaffold(
      appBar: AppBar(
        leading: shellLeading(context),
        title: Text(isPrivacy ? 'Privacy Policy' : 'Terms of Service'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Last updated: 2026',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          if (isPrivacy) ..._privacySections(theme) else ..._termsSections(theme),
        ],
      ),
    );
  }

  List<Widget> _privacySections(ThemeData theme) => [
        _section(theme, 'What this app stores',
            'AcademicOS stores assessment content, generated papers, and student answers/marks '
            'that a teacher enters or scans on this device. In offline mode, all of this is '
            'stored locally on the device, encrypted at rest, in a database only this app can '
            'read. Nothing is uploaded anywhere unless you explicitly turn on sync to a school '
            'server, or add an optional third-party OCR API key in Settings.'),
        _section(theme, 'Student data and minors',
            'Every CBSE student using or being assessed through this app is a minor. Indiaʼs '
            'DPDP Act 2023 requires verifiable parental/guardian consent before a school '
            'deploys a tool like this with real student data, no behavioral profiling or '
            'targeted advertising aimed at a student, and no secondary use of student answers '
            '(e.g. to train a model) without separate, specific consent. This app does not '
            'perform behavioral profiling, advertising, or model training on student data.'),
        _section(theme, 'Honest compliance status',
            'This app is not yet DPDP-registered, not ISO/IEC 27001 certified, and not SOC 2 '
            'audited. Those require an accredited external body and real time to complete. '
            'What is actually built today: encryption at rest for locally stored data, an '
            'append-only audit log of every grading action, and a documented incident-response '
            'plan template. A signed data-processing agreement with your school is required '
            'before any real (non-demo) student data is used with this app in production.'),
        _section(theme, 'Your rights',
            'A school administrator can request deletion of all data associated with their '
            'school at any time. Demo/sample data shown in this app (anything tagged "(Demo)") '
            'is synthetic and can be cleared from Settings at any time and never represents a '
            'real student.'),
        _section(theme, 'Contact',
            'Questions about this policy or a data request: reach the developer through the '
            'app store listing once published, or via the school deploying this app.'),
      ];

  List<Widget> _termsSections(ThemeData theme) => [
        _section(theme, 'What this app is',
            'AcademicOS is an assessment-generation and grading assistance tool for CBSE Class '
            'X teachers: it generates question papers from a real CBSE question corpus, assists '
            'grading of scanned answer sheets with on-device OCR and AI-assisted scoring, and '
            'tracks student mastery over time.'),
        _section(theme, 'AI-assisted grading is assistance, not final authority',
            'Every AI-suggested mark is meant to be reviewed and approved by a real teacher '
            'before it counts as final. Low-confidence answers are flagged for manual review '
            'rather than auto-scored. The teacher using this app remains responsible for the '
            'final, official grade given to any student.'),
        _section(theme, 'No warranty of grading accuracy',
            'Automated scoring, including OCR transcription and AI-assisted marking, can be '
            'wrong. This app does not claim a specific accuracy number beyond what has been '
            'measured against real, teacher-graded reference data (see docs/compliance.md in '
            'the project repository for the actual measured figures). Always review flagged '
            'and low-confidence items before finalizing marks.'),
        _section(theme, 'Demo data',
            'Any record in this app tagged "(Demo)" is synthetic sample data generated on this '
            'device for evaluation purposes and does not represent a real student, teacher, or '
            'school. It can be cleared from Settings before onboarding a real school.'),
        _section(theme, 'Changes',
            'These terms may be updated as the app evolves from a demo build toward a '
            'production release. Material changes affecting student data handling will be '
            'reflected here and in the projectʼs compliance documentation.'),
      ];

  Widget _section(ThemeData theme, String title, String body) => Padding(
        padding: const EdgeInsets.only(bottom: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Text(body, style: theme.textTheme.bodyMedium?.copyWith(height: 1.4)),
          ],
        ),
      );
}
