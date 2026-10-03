import 'package:flutter/material.dart';

/// The Guide's content: for each role, the few jobs a school's staff, students
/// and parents do most, each as a handful of numbered steps and the page that
/// does it (school feedback, 2026-10-01: "too many options to confuse; add an
/// interactive user guide").
///
/// Every step names the page, tab, field and button exactly as the screen
/// labels it, and [GuideJob.menu] is the menu entry the steps start from;
/// test/widget/guide_test.dart holds both to the real menu and router, so a
/// renamed page or route fails a test instead of leaving a guide that points
/// nowhere.
///
/// The words are for a school office, not for engineers: short sentences, the
/// screen's own names, no jargon.
typedef GuideJob = ({
  String id,
  IconData icon,
  String title,
  String summary,
  List<String> steps,
  String route,
  String menu,
});

/// The name a role is called by in the Guide's opening line.
String guideRoleName(String role) => switch (role) {
      'principal' => 'principal',
      'teacher' => 'teacher',
      'student' => 'student',
      'parent' => 'parent',
      'owner' => 'school group owner',
      _ => '',
    };

/// The roles the Guide has jobs for.
const guideRoles = ['principal', 'teacher', 'student', 'parent', 'owner'];

/// The jobs for [role], most common first; empty for a role with no guide.
List<GuideJob> guideJobsFor(String role) => switch (role) {
      'principal' => _principal,
      'teacher' => _teacher,
      'student' => _student,
      'parent' => _parent,
      'owner' => _owner,
      _ => const [],
    };

const _makePaper = (
  id: 'paper',
  icon: Icons.description_outlined,
  title: 'Make a question paper and answer key',
  summary: 'Five short steps, from the class to the download.',
  steps: [
    'In the menu, open Papers and press New paper.',
    'Choose the class and the subject, then press Next: choose a template.',
    'Choose a template. It sets the marks, the time and the sections. Press Use.',
    'Tick the chapters the paper covers, or keep the whole syllabus. Press Generate paper.',
    'Read the paper and swap any question you do not want. Press Done: download.',
    'Press Download paper + answer key. The paper is also kept under Papers.',
  ],
  route: '/assessment/build',
  menu: 'Papers',
);

const List<GuideJob> _principal = [
  (
    id: 'setup',
    icon: Icons.school_outlined,
    title: 'Set up the school',
    summary: 'Classes, the calendar, terms, books and the name on papers.',
    steps: [
      'In the menu, open Setup, then Invite people. This opens the School Admin Console.',
      'A new school sees Set up your school year. Type the school name, the year (for example 2026-27), '
          'the first and last day, and the sections per class. Press Set up classes.',
      'Open the Calendar & Setup tab. Choose the weekly off day and the Saturday rule, then press Initialize Calendar.',
      'On the same tab, under Terms, add your terms. Most CBSE schools use two.',
      'Open the Roster tab. Under Book editions, choose one book for each subject.',
      'Last, open School profile under Setup. Check the name and add the logo printed on every paper.',
    ],
    route: '/admin',
    menu: 'Invite people',
  ),
  (
    id: 'invite',
    icon: Icons.person_add_alt_1_outlined,
    title: 'Invite teachers and students',
    summary: 'Each person joins with a code you create.',
    steps: [
      'In the menu, open Setup, then Invite people.',
      'Under Invite people, choose Teacher or Student.',
      'If you like, type their email so only they can use the code, and choose when it expires.',
      'Press Create invite, then Copy code or Copy invite link.',
      'Send it to the person by message or email. They open the link, or press Create account on the '
          'sign-in page and type the code.',
      'Many people at once? Open Import and export under Setup. Fill in the Excel template, choose the file, '
          'press Check, then Apply.',
    ],
    route: '/admin',
    menu: 'Invite people',
  ),
  (
    id: 'timetable',
    icon: Icons.table_chart_outlined,
    title: 'Give classes their teachers and make the timetable',
    summary: 'Who teaches what, then a week with no clashes.',
    steps: [
      'In the menu, open Timetable.',
      'On the Allocations tab, choose a section. For each subject choose the teacher and the periods a week, '
          'then press Save. Do this for every section.',
      'On the Bell tab, give the bell a name, tick the school days, and type the periods in Slots, one a line '
          '(for example 08:00-08:45). Press Save the bell.',
      'If a subject needs a lab, add it on the Rooms tab. If a teacher is not free at some times, '
          'mark them on the Availability tab.',
      'On the Generate tab, press Preview and check the week. Then press Publish: every teacher is told.',
      'Each section\'s class teacher is chosen on the School Admin Console: on the Roster tab, under Sections, '
          'press the pencil beside the section and choose the Class teacher.',
    ],
    route: '/school/timetable',
    menu: 'Timetable',
  ),
  (
    id: 'lessons',
    icon: Icons.menu_book_outlined,
    title: 'Plan lessons',
    summary: 'Give every lesson a date from the book and the timetable.',
    steps: [
      'First check each subject has its book (Roster tab, Book editions) and its periods a week '
          '(Timetable, Allocations tab).',
      'In the menu, open Lesson plans.',
      'Choose a section and a subject. The page shows how many chapters are ready to plan.',
      'Press Make the plan. Every lesson gets a date on that section\'s timetable.',
      'To plan the whole school at once, press Plan every section.',
      'Teachers then see each day\'s lessons on My day and mark them taught.',
    ],
    route: '/school/lesson-plans',
    menu: 'Lesson plans',
  ),
  _makePaper,
  (
    id: 'exams',
    icon: Icons.event_note_outlined,
    title: 'Publish an exam datesheet',
    summary: 'The dates, the papers and the invigilators, then tell everyone.',
    steps: [
      'In the menu, open Exams and press New exam.',
      'Type the name (for example Half-yearly), choose the dates, tick the classes and press Create.',
      'Open the exam. Under Datesheet, press Paper, choose the class, the subject and the date, and press Add. '
          'Do this for each paper.',
      'Under Invigilation, press Fill automatically to give every room a teacher.',
      'Press Publish at the top. Students and invigilators are told at once.',
    ],
    route: '/school/exams',
    menu: 'Exams',
  ),
  (
    id: 'cover',
    icon: Icons.how_to_reg_outlined,
    title: 'Mark a teacher absent and arrange cover',
    summary: 'Every period of an absent teacher gets a cover.',
    steps: [
      'In the menu, open Attendance and cover. It shows today; press the date at the top for another day.',
      'Under Staff attendance, set the teacher to Absent (or absent for half the day), then press Save.',
      'Their periods appear under Cover. Press Assign beside each one.',
      'Press the name of a teacher who is free. Teaches it means they teach that subject. You can also press '
          'Supervised, Combine classes or Lose the period.',
      'Leave requests wait under Leave waiting for you. Press Approve or Reject.',
      'A lost period is listed under Periods owed, in More, so it can be made up later.',
    ],
    route: '/school/cover',
    menu: 'Attendance and cover',
  ),
  (
    id: 'term-report',
    icon: Icons.assessment_outlined,
    title: 'Read the term report',
    summary: 'How every class is doing against the plan.',
    steps: [
      'In the menu, open Term report.',
      'It shows this term for the whole school. To look closer, choose a class, section or subject at the top.',
      'The numbers show lessons taught against the plan, classes behind, papers set, homework handed in and cover.',
      'Behind the plan lists the classes that need attention first.',
      'To share it, press the Excel or the PDF button at the top right to download it.',
    ],
    route: '/school/term-report',
    menu: 'Term report',
  ),
];

const List<GuideJob> _teacher = [
  (
    id: 'today',
    icon: Icons.wb_sunny_outlined,
    title: 'See today\'s classes',
    summary: 'Your periods for today, and any changes.',
    steps: [
      'In the menu, open My day.',
      'Under Today you see each period: the class, the subject, the time and the room. A changed period is marked.',
      'Press I\'m here at the top to mark yourself present.',
      'If you are asked to cover a class, it shows under Cover asked of you. Press Accept or Decline.',
      'For the whole week, open My week.',
    ],
    route: '/school/my-day',
    menu: 'My day',
  ),
  (
    id: 'mark-taught',
    icon: Icons.task_alt_outlined,
    title: 'Mark a lesson taught',
    summary: 'Keep the lesson plan true to what happened in class.',
    steps: [
      'In the menu, open My day.',
      'Find the lesson under Today\'s lessons.',
      'Press Taught when you have finished it.',
      'Press Partly if some is left, or Not taught if you could not teach it. Write a short note and press Save.',
      'A lesson that was not finished is planned again at your next free period.',
    ],
    route: '/school/my-day',
    menu: 'My day',
  ),
  (
    id: 'homework',
    icon: Icons.assignment_turned_in_outlined,
    title: 'Set homework',
    summary: 'Pick the questions and tell the students.',
    steps: [
      'In the menu, open Homework and press Set homework.',
      'Choose the subject and tick the sections.',
      'Type a title and choose the due date. Suggest from the lesson fills it from your lesson.',
      'Tick the chapters, or tick the exact questions you want.',
      'Press Set and notify students.',
      'Answers come back here. Open a homework to mark the answers, or press Remind for those who have not '
          'handed it in.',
    ],
    route: '/school/homework',
    menu: 'Homework',
  ),
  _makePaper,
  (
    id: 'marks',
    icon: Icons.grid_on_outlined,
    title: 'Enter marks',
    summary: 'Each student\'s marks for a paper, question by question.',
    steps: [
      'In the menu, open Papers and open the paper.',
      'Press the three dots at the top right and choose Enter marks.',
      'Choose the section.',
      'Type each student\'s marks for each question. Tick Absent for anyone who missed it.',
      'Press Save. The Analysis tab shows the class average and what to teach again.',
    ],
    route: '/assessment',
    menu: 'Papers',
  ),
  (
    id: 'leave',
    icon: Icons.event_busy_outlined,
    title: 'Apply for leave',
    summary: 'Ask the principal, and leave a note for whoever covers.',
    steps: [
      'In the menu, open My day.',
      'Under My leave, press Apply for leave.',
      'Choose Today, Tomorrow or Other days, then Full day, 1st half, 2nd half or Periods.',
      'Add a reason and a note for whoever covers, if you like. You can attach a document.',
      'Press Apply. The principal is asked, and the answer shows under My leave.',
    ],
    route: '/school/my-day',
    menu: 'My day',
  ),
];

const List<GuideJob> _student = [
  (
    id: 'today',
    icon: Icons.today_outlined,
    title: 'See today',
    summary: 'Your periods, homework due and the next exam.',
    steps: [
      'In the menu, open Today.',
      'You see each period and its subject. A period that changed is marked Changed.',
      'Homework that is due and your next exam are shown at the top.',
      'Press the arrow at the top to see tomorrow.',
    ],
    route: '/school/today',
    menu: 'Today',
  ),
  (
    id: 'homework',
    icon: Icons.assignment_outlined,
    title: 'Do your homework',
    summary: 'Answer, hand it in, then see your marks.',
    steps: [
      'In the menu, open Homework.',
      'Press a homework to open it.',
      'Answer each question.',
      'Press Submit. You can send it again until it is closed.',
      'When your teacher has marked it, your marks and their note show here.',
    ],
    route: '/school/my-homework',
    menu: 'Homework',
  ),
  (
    id: 'exams',
    icon: Icons.event_note_outlined,
    title: 'See your exams and prepare',
    summary: 'The datesheet, and practice for each paper.',
    steps: [
      'In the menu, open Exams. Each exam shows its datesheet.',
      'Press Prepare beside a paper that is still to come.',
      'Answer the practice questions and press Check my answers.',
      'See the right answers, then press Practise again for more.',
    ],
    route: '/school/my-exams',
    menu: 'Exams',
  ),
  (
    id: 'progress',
    icon: Icons.trending_up_outlined,
    title: 'See your progress',
    summary: 'What you know well, and what to revise next.',
    steps: [
      'In the menu, open Progress.',
      'Revise next lists the topics to work on first. Press Practise to try questions on one.',
      'Week by week shows how your marked work went each week.',
      'Below, each subject lists its chapters and how well you know each one.',
    ],
    route: '/school/my-learning',
    menu: 'Progress',
  ),
];

const List<GuideJob> _parent = [
  (
    id: 'week',
    icon: Icons.calendar_view_week_outlined,
    title: 'See your child\'s week',
    summary: 'The timetable, and today\'s changes.',
    steps: [
      'In the menu, open My children.',
      'If you have more than one child, press the child\'s name at the top.',
      'The Week tab shows the timetable. The Today tab shows today\'s periods and any changes.',
    ],
    route: '/school/family',
    menu: 'My children',
  ),
  (
    id: 'homework',
    icon: Icons.assignment_outlined,
    title: 'Check homework',
    summary: 'What is due, what was handed in, and the marks.',
    steps: [
      'In the menu, open My children and choose the child.',
      'Open the Homework tab. Each homework shows whether it was handed in and marked.',
      'Press a homework to see the questions, the answers and the marks.',
      'For a child in classes 1 to 5, you can answer it together and hand it in here.',
    ],
    route: '/school/family',
    menu: 'My children',
  ),
  (
    id: 'report-card',
    icon: Icons.grading_outlined,
    title: 'See the report card',
    summary: 'This term\'s marks for each subject.',
    steps: [
      'In the menu, open My children and choose the child.',
      'Press Report card, under the child\'s name.',
      'You see this term\'s marks for each subject, with the grade.',
      'Press the PDF button at the top to download a copy.',
    ],
    route: '/school/family',
    menu: 'My children',
  ),
];

const List<GuideJob> _owner = [
  (
    id: 'schools',
    icon: Icons.domain_outlined,
    title: 'Open one of your schools',
    summary: 'Work in one school as its principal.',
    steps: [
      'All schools shows each of your schools side by side.',
      'Press the school switcher at the top of the menu and choose a school.',
      'You now work as that school\'s principal, and this Guide shows the principal\'s jobs.',
      'To go back, choose All schools in the switcher.',
    ],
    route: '/owner',
    menu: 'All schools',
  ),
];
