import 'package:flutter/material.dart';

import '../../shared/widgets/shell.dart';

/// Real Privacy Policy / Terms content -- was a dead `() {}` button before
/// this. Written to be honestly accurate to this buildʼs actual state
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
            'Last updated: 4 October 2026',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          if (isPrivacy) ..._privacySections(theme) else ..._termsSections(theme),
        ],
      ),
    );
  }

  List<Widget> _privacySections(ThemeData theme) => [
        _section(theme, 'Who this is for',
            'AcademicOS is run for schools. Your school decides who gets an account and what is '
            'entered, and your school is responsible for that data. AcademicOS stores and '
            'processes it on the schoolʼs behalf, under an agreement the school signs with us.'),
        _section(theme, 'What is stored',
            'Accounts (name, email, role and a protected form of the password, never the password '
            'itself); classes, sections, timetables and lesson plans; homework, answers and marks; '
            'question papers; scanned answer sheets and the text read from them; each studentʼs '
            'progress and revision schedule; notifications and messages; the record of a parentʼs '
            'consent; and a log of grading and administrative actions.'),
        _section(theme, 'Where it is kept',
            'On Google Cloud in Mumbai, India (the database and file storage), which encrypts '
            'stored data by default. Signing in lasts 30 days on a device unless you sign out. '
            'To work on a poor connection, the web app also keeps saved copies of pages you have '
            'opened in your browser on that device. On a shared computer, sign out and use '
            'Settings > Clear Cache; those copies stay in the browser until cleared.'),
        _section(theme, 'Who else receives data',
            'Google Cloud and Firebase Hosting (hosting and storage). Sarvam AI, when the schoolʼs '
            'deployment has it switched on, receives scanned answer-sheet images, which can show '
            'anything written on the page such as a name or roll number, and each answerʼs text '
            'with its question for scoring; no student identifier is added. The doubt-answering '
            'assistant sends the question a person types, which may be a studentʼs own words, to '
            'an AI service (Groq unless changed). Email is sent only if the school has set up a '
            'mail service, and then carries recipient addresses and the paper, not student '
            'records. Your browser also loads program files from Google (gstatic.com) and, for '
            'the paper preview, from unpkg.com; they receive your IP address, not school data. '
            'The full list is in the agreement the school signs.'),
        _section(theme, 'Children and consent',
            'Every student here is a child. Indiaʼs DPDP Act 2023 requires a parentʼs or '
            'guardianʼs consent before a school uses a tool like this with a childʼs data. The '
            'school records that consent for each student in AcademicOS, and the server will not '
            'process a studentʼs scanned work, grading or practice without it. AcademicOS does '
            'not show advertising, does not sell data, and does not itself train models on '
            'student data. It does track each studentʼs progress, so that their teachers can '
            'see where help is needed.'),
        _section(theme, 'How long it is kept',
            'AcademicOS does not delete data automatically. It stays until the school asks for '
            'it to be deleted. How long a school keeps student data is the schoolʼs decision, '
            'recorded in its agreement with us; nothing here ends it on a schedule.'),
        _section(theme, 'Seeing and deleting data',
            'A student, parent or teacher who wants to see or delete their data asks the schoolʼs '
            'administrator. The principal can review everything held about a student or a parent '
            'and erase it from the admin tools, and can ask us to delete the whole schoolʼs data. '
            'Erasing a person removes their records from AcademicOS; it cannot recall what a '
            'school has already printed, downloaded or e-mailed.'),
        _section(theme, 'The phone app without a school server',
            'The phone app that works with no school server keeps everything on that phone, in a '
            'database only the app can read, encrypted with a key held privately by the app. '
            'Nothing leaves the phone unless the school turns on syncing to its server.'),
        _section(theme, 'Honest compliance status',
            'This service is not yet DPDP-registered, not ISO/IEC 27001 certified and not SOC 2 '
            'audited; those need an outside body and time. What exists today: parental consent '
            'recorded and enforced, an erasure tool, a log of grading and admin actions, and an '
            'incident-response plan. A signed data-processing agreement with the school is '
            'required before real student data is used.'),
        _section(theme, 'Contact',
            'For any question or request about data, ask your schoolʼs administrator, who can '
            'act on it directly or pass it to us.'),
      ];

  List<Widget> _termsSections(ThemeData theme) => [
        _section(theme, 'What this app is',
            'AcademicOS is a school tool for CBSE classes 1 to 10: teachers, principals, students '
            'and parents use it for timetables, lesson plans, homework and progress, and teachers '
            'use it to generate question papers from a real CBSE question bank and to get help '
            'grading scanned answer sheets, with OCR and AI-assisted scoring. It also tracks '
            'each studentʼs progress over time.'),
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
