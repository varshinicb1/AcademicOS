# Integration candidates

Third-party APIs worth evaluating for the v3 requirements (`docs/REQUIREMENTS.md`), from a review of
the community list [public-apis/public-apis](https://github.com/public-apis/public-apis) on 2026-09-27.
That list holds 1,953 APIs in 52 categories and has no Education category. It is community-maintained and
goes stale: in its Authentication & Authorization section alone, 2 of 7 entries were dead and 2 had been
acquired or renamed. **Recheck any entry before building on it**, and get a data-processing agreement for
any provider that receives student or parent personal data (`docs/compliance.md`, DPDP Act 2023).

"Checked" below means the site was fetched on 2026-09-27; nothing here has been integrated or load-tested.

## 1. Authentication & Authorization (requirements ROLE-1, ROLE-2, NFR-2)

What AcademicOS has today (`src/academicos/assessment/users.py`, `auth_routes.py`, `api/route_policy.py`):
- email and password, hashed with PBKDF2-SHA256 at 200,000 rounds;
- opaque server-side sessions (not JWTs), so revoking one is deleting a row;
- invite-only registration with expiring codes;
- a role rule on every route (`principal`, `teacher`, `student`).

v3 adds four things:
- **OTP sign-in** for students and parents;
- **Google sign-in**;
- **parent accounts** linked to children;
- **delegated admin**: permission sets and scopes that a principal grants to chosen teachers.

| Entry (public-apis) | What it is | Status 2026-09-27 | Fit |
|---|---|---|---|
| [Auth0](https://auth0.com) | Full identity platform | Live | Capable; priced per monthly active user, which is costly at thousands of students; data processed abroad |
| [GetOTP / otp.dev](https://otp.dev/en/docs/) | OTP verification flows with channel retry | Live | Candidate for phone OTP |
| [MojoAuth](https://mojoauth.com) | Passwordless: passkeys, magic links, email/SMS/**WhatsApp** OTP, social login | Live | Best fit in the list for parents and young students (WhatsApp OTP) |
| [Stytch](https://stytch.com/) | Authentication and user infrastructure | Live; **joined Twilio** | Capable; same cost and data-location questions as Auth0 |
| [Warrant](https://warrant.dev/) | Fine-grained authorization | **Deprecated; now WorkOS FGA** | Suits delegated admin, but more machinery than the roles need now |
| [Micro User Service (m3o)](https://m3o.com/user) | User management | **Dead (404)** | none |
| [SAWO Labs](https://sawolabs.com) | Passwordless login | **Dead (parked domain)** | none |

**Recommendation.**
- **Keep the in-house core:** sessions, invites and the route policy.
- **Build delegated admin in-house.** Extend roles with permission sets and grade/section/subject
  scopes (ROLE-1). It is a data-model change, not a vendor.
- **Add phone OTP and Google sign-in through one provider.** The strongest candidate is **not in the
  list**: **Firebase Authentication**, because the web app already runs on the `vidyuthlabs` Firebase
  project. From the list, MojoAuth.
- **Settle two things before choosing a provider:**
  - India's TRAI DLT rules require registered sender IDs and templates for SMS OTP. Check whether the
    provider handles that registration.
  - Any provider receiving students' phone numbers needs a DPA.

## 2. Other candidates, by requirement

| Requirement | Candidate | Notes |
|---|---|---|
| SCH-1 holidays in the academic calendar | [Calendarific](https://calendarific.com/), [caldays](https://caldays.com/api) | Worldwide holiday data; India's state and regional coverage is **not verified**. [Nager.Date](https://date.nager.at) has **no India data** (checked: India is not in its country list). A school's own list, imported by CSV, must stay the source of truth. |
| INT-2 calendar sync | [Google Calendar API](https://developers.google.com/google-apps/calendar/) | Publish timetables and exam dates to teachers' and students' calendars (OAuth) |
| INT-5 government and board integrations | [API Setu](https://www.apisetu.gov.in/), [data.gov.in](https://data.gov.in/) | API Setu's site lists CBSE and DigiLocker services (results, verification); for later |
| ROLE-2 bulk import checks | [Indian Pincode](https://indianpincode.com/), phone validation (Numverify, Veriphone), disposable-email detection (Disify, Kickbox) | Validate school and user data on import |
| NFR-2 password hygiene | [HaveIBeenPwned](https://haveibeenpwned.com/API/v3) | Refuse passwords already exposed in breaches |
| SA-3/SA-4 student learning | [Free Dictionary API](https://dictionaryapi.dev/) (keyless), [Wiktionary](https://en.wiktionary.org/w/api.php) | English vocabulary and pronunciation |
| QB-12, NFR-6 Hindi | [LibreTranslate](https://libretranslate.com/docs) (keyless, self-hostable) | Draft translations only; anything served still goes through the review queue (QB-5). Sarvam, already behind `llm/`, is the Indic-first option |
| TA-4/SA-2 homework photo uploads | [Google Safe Browsing](https://developers.google.com/safe-browsing/), the Anti-Malware category | Scan submitted files and links |
| TA-4 maths auto-checking | [Newton](https://newton.vercel.app) | Symbolic maths checks for typed answers |
| EX-5 document export | the Documents & Productivity category (for example CloudConvert) | AcademicOS already renders PDFs; consider only for DOCX export |

## 3. Needed but not in the list (from general knowledge; not checked in this pass)

- **Push:** Firebase Cloud Messaging (NTF-1). The `vidyuthlabs` Firebase project already exists.
- **SMS in India:** a DLT-compliant gateway such as MSG91 or Twilio (NTF-1, INT-2).
- **WhatsApp:** the WhatsApp Business Platform, through Meta or a BSP such as Gupshup (INT-2, parent
  notices).
- **Error tracking:** Sentry or Google Cloud Error Reporting (NFR-7).
- **Timetable solver:** Google OR-Tools CP-SAT (SCH-3). This is a library, not an API.
