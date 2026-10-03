# School handover: question paper generation and the school day

**For the school's principal and teachers.**

**Site:** <https://vidyuthlabs.web.app>.

**Release:** this guide describes the release that carries the QA fixes of 2026-10-02:
- PR #88: paper access, printed papers, generation, screens, accounts and daily use;
- the question-bank cleanup PR.

**How it was checked:**
- Two QA passes played a teacher, a principal, a student and a parent at desktop and phone width.
- Every fix was re-tested on screen.
- Both test suites pass (backend 4,557 tests, Flutter 659).

Until that release is deployed, the site runs the earlier one.

Use a laptop or desktop browser for making papers. Phones work for everything else.

## What you can generate today

Measured on the question bank of this release (5,268 questions). Each cell is what one press of
"Generate paper" gives:

- **Full:** every section is filled and the marks add up. Each set (A, B, C) has its own questions and
  its own answer key.
- **Short X/Y:** the bank fills X of the paper's Y marks.
  - The builder says which sections are short, and by how many marks, before you generate.
  - You can generate anyway and complete the paper with Pick or in the Word copy.
- **None:** no questions yet for this class and subject. The builder does not offer it.

| Class | Subject | Unit test (20 marks) | Periodic (40) | Half-yearly (80) | Annual (80) |
|---|---|---|---|---|---|
| 6, 7, 8 | Mathematics | Full | Full | Full | Full |
| 6, 7, 8 | Science | Full | Full | Full | Full |
| 9, 10 | Mathematics | Full | Full | Full | Full |
| 9 | Science | Full | Full | Short 60/80 | Short 60/80 |
| 10 | Science | Full | Full | Short 58/80 | Short 58/80 |
| 10 | Social Science | Short 12/20 | Short 16/40 | Short 18/80 | Short 18/80 |
| 6, 9, 10 | English | Short (1-12 marks) | Short | Short | Short |
| 6-9 | Social Science | None | None | None | None |
| 7, 8 | English | None | None | None | None |
| 6-10 | Hindi | None | None | None | None |
| 1-5 | All subjects | None | None | None | None |

**For a first trial, use Mathematics 6-10 and Science 6-8 (any paper), and Science 9-10 unit and periodic
tests.**

## First day: the principal

1. **Create the principal account.**
   - Open the site, choose **Create account**, and open **First principal of a new school**.
   - Enter the school's ID and the principal key (AcademicOS gives you both privately), then your name,
     email and a password.
   - The key creates a school's first principal only.
2. **Follow "Set up your school"** on the School page. It lists the five steps in order, links each one to
   where it is done, and ticks it when done:
   1. **School profile:**
      - the school's name, address, affiliation line and logo;
      - the name, the address/affiliation line and the logo print at the top of every paper, answer key,
        report card and term report;
      - use a PNG or JPEG logo of at most 1 MB.
   2. **Classes.** "Set up classes" creates the classes:
      - classes 6 to 10 get their CBSE subjects and chapters;
      - classes 1 to 5 are created without subjects; add their subjects under Classes.
   3. **Calendar and terms:** holidays, weekly offs, the 2nd/4th Saturday rule, and terms.
   4. **People:** **Invite people** for a teacher, a student or a parent.
      - The code is shown on screen, with a Copy button. Give each person their code.
      - They choose **Create account** and enter it. A code works once.
      - For many people at once, use **Import and export**.
   5. **Timetable.** **Generate** shows each period that would move, be added or be removed. **Publish**
      makes it live.

   Classes, calendar and timetable are needed for homework, lesson plans, attendance and cover. **They are
   not needed for making papers.**

## Making a paper: a teacher

1. **Papers → New paper.** The builder starts fresh each time.
2. **Class and subject.**
3. **Template.** Unit test, Periodic, Half-yearly or Annual, each with the CBSE section pattern, marks and
   time. You can also make your own template.
4. **Chapters.** Choose the chapters, or keep **Whole syllabus**. Before you generate, the builder shows:
   - each section's fill;
   - the competency-based share against CBSE's 50%;
   - any section that would be short, and the fixes that close the gap.
5. **Generate paper.** It is saved to your Papers at once.
   - Questions are spread over the chapters.
   - Competency-based questions come first, aiming for CBSE's 50%.
   - **Your next paper for the same class and subject uses questions your recent papers did not**, where the
     bank has them. Where it must repeat one, it says which section.
   - With sets A, B and C, each set has its own questions of the same pattern.
6. **Check every question before printing.** On each question, in each set:
   - **Swap** puts in the next best question;
   - **Pick** lets you choose one from the bank;
   - **Remove** takes it off (marks and instructions update);
   - **Swap OR** changes an internal choice.
7. **Download.** One press per file:
   - the paper and its answer key as PDFs;
   - a Word (.docx) copy to edit.

   Files are named for the class, title and set. Every download carries a traceable copy number in its
   footer.
8. **Later, from Papers → the paper → ⋮:**
   - **Rename**, **Delete** (with a confirmation), **Send for review** and **Enter marks**;
   - Swap, Pick and Remove until the paper is approved.

### Who sees what

- **A teacher's Papers list** holds the papers they wrote, review, or teach the subject of in that class.
  The principal sees them all.
- **Changing a paper** is for its author, the principal, or a teacher the principal made an exams admin.
- **Downloading a paper or its answer key before the exam** is for those people and the colleague asked to
  review it. Other colleagues can read the questions on screen, without the answers. Once the exam has been
  held, any teacher of the school can download it.

### Review and approval (optional)

- **Ask a colleague to review** names a reviewer, who is notified. While a paper is under review it cannot
  be changed or deleted.
- **The reviewer:** **Paper reviews** → approve it for the principal, or **Ask for changes** with a
  comment. Asking for changes sends the paper back to its author.
- **The principal:** **Paper reviews → Waiting** holds the papers a colleague approved. **Approve & lock**
  locks the paper. A locked paper can be downloaded, but not edited or deleted.

## Accounts and passwords

- **Forgot password?** on the sign-in page says how to get back in:
  - staff ask the principal;
  - students and parents ask their class teacher or the principal.
- **The principal resets a password** from **Staff and access** (or the student and parent lists) →
  ⋮ → **Reset password**.
  - This shows a one-time password to read out or copy, and signs that account out everywhere.
  - The principal's own account is reset by AcademicOS, not in the app.
- **Anyone can change their own password** with **Change password** (Settings).
- Sign-in locks for 15 minutes after 10 wrong passwords on one account. Other accounts are not affected.

## Read before printing: known limits

- **Read every question and answer before printing.**
  - The question-bank cleanup withdrew the answer keys found cut short or missing their numbers, removed
    editing notes and repeated option lists, and fixed the chapter tags QA found wrong.
  - Some copying errors from the source PDFs remain, for example "(−4k)2" for (−4k)². Use Swap on any
    question that reads wrong.
- **Short papers.** Science 9-10 half-yearly and annual fill about three quarters of the marks. Choose more
  chapters, or generate anyway and complete the short sections with Pick or in the Word copy.
- **Not yet available:**
  - classes 1-5;
  - Hindi;
  - Social Science 6-9;
  - most English.
- **Competency share.** A paper says when it is below CBSE's 50% competency-based questions. The bank has
  few such questions in some subjects, so a second or third paper for the same class may fall below 50%
  unless it repeats them. The builder says so before you generate.
- **Difficulty** is the source's own label, not yet checked by a teacher panel.
- **A page refresh in the middle of the builder** loses the choices made so far. Your saved papers are not
  affected.

## If something goes wrong

Send AcademicOS:
- what you were doing;
- the paper's title;
- the time;
- a screenshot.

If the screen shows a **reference** (for example "tell the school's administrator this reference:
d7cf27357a0e"), include it; it finds the exact error in the server's log.
