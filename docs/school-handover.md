# School handover: question paper generation

**For the school's principal and teachers, from 2026-10-01.**

**Live at <https://vidyuthlabs.web.app>.** Release `9f5c41d`, checked end to end on 2026-10-01 with a fresh
test school: 279 of 282 workflow checks, 19 of 19 live checks, and both test suites. Use a laptop or desktop
browser for making papers; phones work for everything else.

## What you can generate today

Measured on the live question bank (5,319 questions). Each cell is what one click of "Generate paper" gives:

- **Full:** every section is filled, the marks add up, and there are three different sets (A, B, C), each with
  its answer key.
- **Short X/Y:** the bank fills X of the paper's Y marks. The builder says which sections are short. You can
  generate anyway and add or change questions.
- **None:** no questions yet for this class and subject.

| Class | Subject | Unit test (20 marks, 40 min) | Periodic (40, 90 min) | Half-yearly (80, 3 h) | Annual (80, 3 h) |
|---|---|---|---|---|---|
| 6, 7, 8 | Mathematics | Full | Full | Full | Full |
| 6, 7, 8 | Science | Full | Full | Full | Full |
| 9, 10 | Mathematics | Full | Full | Full | Full |
| 9 | Science | Full | Full | Short 60/80 | Short 60/80 |
| 10 | Science | Full | Full | Short 58/80 | Short 58/80 |
| 10 | Social Science | Short 12/20 | Short 16/40 | Short 18/80 | Short 18/80 |
| 6, 9, 10 | English | Short (1-13 marks) | Short | Short | Short |
| 6-9 | Social Science | None | None | None | None |
| 7, 8 | English | None | None | None | None |
| 6-10 | Hindi | None | None | None | None |
| 1-5 | All subjects | None | None | None | None |

**For a first trial, use Mathematics 6-10 and Science 6-8 (any paper), and Science 9-10 unit and
periodic tests.**

## First day: the principal

1. **Create the principal account.** Open the site, choose **Create account**, and open **First principal of a
   new school**. Enter:
   - the school's ID and the principal key, both of which AcademicOS gives you privately;
   - the principal's name, email and a password.

   The key creates a school's first principal only.
2. **School profile.** **Setup → School profile**: the school's name, address, affiliation line and logo.
   Every paper and answer key prints these. Use a PNG or JPEG logo of at most 1 MB.
3. **Invite teachers.** **Setup → Invite people**: choose *Teacher*, optionally enter the email, then **Create
   invite**. Give each teacher their code. They choose **Create account** and enter it. A code works once.
   For many teachers at once, use **Setup → Import and export**.
4. *(Optional)* **Classes and timetable.** These are only needed for homework, lesson plans and cover, **not
   for making papers.**

## Making a paper: a teacher

1. **Papers → New paper** (or **New paper** on Today).
2. **Class and subject.**
3. **Template.** Unit test, Periodic, Half-yearly or Annual. Each has the CBSE section pattern, marks and time.
4. **Scope.** Choose the chapters the paper covers.
   - The builder shows, section by section, how many questions the bank has.
   - It shows the competency-based share against CBSE's 50%.
   - It lists any section that would be short.
5. **Generate paper.** It makes three sets (A, B, C) that share no questions where the bank allows.
6. **Check every question before printing.**
   - **Swap** replaces a question with the next best one.
   - **Remove** takes it off; marks and instructions update.
   - **Swap OR** changes an internal choice.
7. **Finish → Download.** The paper and its answer key, for each set, as PDFs.
   - From the saved paper (**Papers →** the paper) you can also download a **Word (.docx)** copy to edit.
   - Every download carries a traceable copy number in its footer.
8. *(Optional)* **Review and approval.**
   - On the saved paper, **Ask a colleague to review** names a reviewer, who is notified. While under review,
     the paper cannot be changed.
   - The principal's approval (**Paper reviews → Approve and lock**) locks it. A locked paper can be
     downloaded but not edited or deleted.

## Read before printing: known limits

- **A few bank questions carry copying errors from their source PDFs.** About 45 of 5,319, mostly class 10
  Mathematics competency items. Typical errors:
  - a degree sign read as a zero ("(A + B) ≤ 900" for 90°, "tan 300" for tan 30°);
  - a stray leading mark ("1 The distance…");
  - "x2" for x²;
  - a fraction run together ("11323 250").

  **Read every question and use Swap on any that is wrong.** These are being corrected in the bank.
- **Short papers.** Science 9-10 half-yearly and annual fill about three quarters of the marks. Choose more
  chapters, or generate anyway and complete the short sections by hand in the Word copy.
- **Not yet available:** classes 1-5, Hindi, Social Science 6-9 and most English. The builder does not offer a
  class and subject with no questions.
- **Competency share.** The paper says when a set is below CBSE's 50% competency-based questions. Set A is
  usually closest.
- **Difficulty** is the source's own label, not yet checked by a teacher panel.

## If something goes wrong

Send AcademicOS:
- what you were doing;
- the paper's title;
- the time;
- a screenshot.

If the screen shows a **reference** (for example "tell the school's administrator this reference:
d7cf27357a0e"), include it; it finds the exact error in the server's log.

Sign-in locks for 15 minutes after 10 wrong passwords on one account. Other accounts are not affected.
