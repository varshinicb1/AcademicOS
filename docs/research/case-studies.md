# Competitive case studies: ~50 companies solving parts of this problem

Research synthesis, 2026-09-17. Sources cited inline. Where a claim is marketing
rather than verified, it is marked as such — most vendor pages are marketing.

Companion to [`ui-ux-principles.md`](ui-ux-principles.md). This document answers
three questions: what is table stakes, **where is every incumbent weak** (which
is our opening), and what should we deliberately *not* copy.

---

## 1. Global student information systems (SIS)

The district-scale incumbents. What they have in common is more useful than how
they differ.

| Company | Position | Notable |
|---|---|---|
**PowerSchool SIS** | The default large-district SIS | Deep grading/scheduling/state-reporting; interoperability via SIF, Ed-Fi, OneRoster. Reviewed 4.1/5 (1,343 reviews). "Requires significant implementation and training." |
**Infinite Campus** | All-in-one district platform | 1,500+ core tools; emphasises data integrity, auditability, FERPA. 3.9/5 |
**Skyward** | SIS + *school business suite* | The only one explicitly covering finance, HR, payroll, procurement, assets alongside student records. 2,000+ districts |
**Veracross** | Private/independent schools | "One-person, one-record" — a single database per person across admissions, academics, billing, advancement. Best-rated at 4.4/5 |
**Bromcom** | UK | Admissions-to-enrolment with auditable step tracking; parent *and* teacher portals |
**Arbor** | UK | Governance focus: role-based access **plus change history** on student record fields |
**FACTS** | Private/faith-based, tuition-led | Connected records, admissions, tuition, financial aid |
**Gradelink** | Small schools | Simplicity; explicitly not for multi-campus or advanced finance |
**openSIS** | International / multilingual | Configurable, multilingual, multi-school |
**iSAMS / Classter / Aeries / Alma / Blackbaud** | Regional / niche | Blackbaud leads on role-based access and audit logging for record accountability |

**What this category tells us**

1. **Pricing is deliberately opaque.** Every single one is "custom" or "contact us".
   One comparison notes "it is impossible to assess fairness without direct
   engagement." This is an industry norm, and it is also an opportunity: our flat,
   published pricing is a differentiator in India (§3) and would be abroad too.
2. **Table stakes are enrolment, attendance, gradebook, scheduling, report cards,
   transcripts, portals, RBAC, audit log.** Not one of those is our differentiation.
3. **The differentiators they actually compete on are governance-grade**: change
   history, item-level audit trails, role-based access granularity, integration
   surface (OneRoster/SIF/Ed-Fi), and repeatable reporting outputs.
4. **Nobody in this table is competing on teaching.** They are records systems.
   The curriculum, lesson and question-bank layer is either absent or bolted on.

---

## 2. Lesson planning and curriculum mapping

The nearest neighbours to our scheduling/coverage half.

| Company | Scale claimed | The pattern worth stealing |
|---|---|---|
**Planbook** | 1M+ teachers, 1B lessons, since 2010 | **Lesson banks**: schools store curriculum centrally, teachers *copy or link* into their own plan, and keep control of their own scheduling. Admins review plans in real time and comment. |
**Atlas (Rubicon)** | 6,000+ schools and districts | **Unit planner templates that evolve**, plus cross-grade / cross-subject analysis: reports for gaps, redundancies, scope-and-sequence, standards alignment. AI insights bolted on in 2026. 50+ integrations |
**Common Planner** (was Common Curriculum) | — | AI-assisted planning, standards coverage tracked automatically, collaborative planbook, one-click print of the week |

**Three transferable ideas**

- **Link, don't copy** (Planbook). A central curriculum that teachers *link* into
  their own plan keeps the school's version authoritative while letting the teacher
  personalise — and it means a curriculum update propagates. Our `canonical_id`
  bridge is the same idea; the lesson is that the *UI* must make linking feel safe
  and reversible.
- **Report on gaps, not just coverage** (Atlas). Our coverage report answers "did we
  teach it". The more valuable question is "where are the gaps and redundancies
  across grades" — which is a principal's actual concern and a natural extension.
- **Approval with comments** (Planbook). Principal review is a first-class workflow
  with threaded feedback, not a status flag.

---

## 3. The Indian market

### Pricing reality (2026)

| Vendor | Segment | Price |
|---|---|---|
Most Indian vendors | Schools up to 500 | ₹20,000–50,000/yr; per-student ₹100–500/yr |
**Entab CampusCare** | Large CBSE/ICSE, metro, with IT staff | ~₹35,000+/yr; community reports of ₹1.5–8 lakh/yr + ₹75k–2.5 lakh implementation. 23 years, 2,300+ schools |
**Fedena** | Multi-campus, open-core | ~₹40,000+/yr SaaS; open-source self-host free but needs Ruby/IT capability |
**Teachmint** | Mobile-first, LMS-led | Quote-based; est. ₹100–300/student/yr. Free tier. 90,000+ Indian schools claimed |
**EduGradUP** | Budget K-12, incl. state boards | **Flat ₹9,000–23,000/yr by size band, all 43 modules, no per-student metering** |
**Edutris** | Administration-first | Flat ₹2,999 / 7,999 / 14,999 per month by size |
**Schoolites** | Mainstream K-12 | ₹10/student/month flat, all modules |
**Fuzen** | Custom build | From ₹25,000 one-time; no per-student fees |
**Classplus** | Tutors / coaching | Free tier; branded app from ~₹15,999/yr |
**Saral** | Maharashtra government schools | Free |

### What the Indian market tells us

1. **Per-student pricing is the norm, and it punishes growth.** A school that
   succeeds pays more. Flat, published per-school pricing is the exception and is
   repeatedly positioned as the differentiator.
2. **English-first, CBSE-first, and state boards are an afterthought.** One survey
   states it plainly: "Most India vendors are English-first and CBSE-first, and
   treat state-board schools as an afterthought." Another notes Hindi read rates
   run far ahead of English email, and that offline-capable Android matters where
   connectivity is unreliable.
3. **The recurring complaints are consistent and are all things we can avoid**:
   dated interfaces (Entab); module-by-module cost creep (Fedena — base price
   reasonable, transport/hostel/reporting are paid add-ons); no customisation plus
   **repeated product pivots that removed features schools had built workflows
   around** (Teachmint); opaque sales-call-only pricing.
4. **The market is crowded at the bottom and thin in the middle.** There are "200+
   school ERP products marketed to Indian schools", and most are fee + attendance +
   communication. Almost none do curriculum, assessment *and* scheduling.

### The strategic read

Our differentiation is **not** the ERP. It is the curriculum and assessment
engine: real CBSE questions with official marking schemes, blueprint generation,
coverage and pace reporting. Every vendor above treats the academic layer as an
afterthought or excludes it. But we must be honest that the ERP layer is where
schools actually spend — so the product has to be credible on fees and attendance
even though that is not where the value is.

---

## 4. Timetable and scheduling engines

| Engine | Scale | The algorithm |
|---|---|---|
**Untis** | 50+ years | Optimisation = **initial placement then swapping**. Every violation of a school's constraints scores **penalty points** weighted by importance; the total is the timetable's quality score. A diagnosis tool shows conflicts after manual edits |
**aSc TimeTables** | 200,000 schools, 30 years | Dynamic + heuristic; evaluates "over 5 million possibilities"; six rule-checkers running continuously. Now has an AI panel that accepts plain-language changes |
**Edval** (Tes) | UK/global | Auto-staff, auto-room, auto-fix clashes; **option block generation** — maximising students who get all their subject choices; 70+ integrations |

**The transferable idea, and it is a big one:** these are constraint-satisfaction
solvers with **explicit, weighted, inspectable constraints** and a **quality score
you can explain**. That is precisely the design the teacher-adoption research
demands — a scheduler whose output the user can predict, inspect and adjust.

Our scheduler is currently *sequential* rather than constrained: walk the
curriculum order, assign the next working days. That is defensible and honest, but
it cannot answer "we need Science before 2nd period and not on Fridays" — and
Untis's penalty-point model is the proven shape for when we do.

---

## 5. Assessment and question banks

The closest neighbours to our strongest asset.

| Platform | Positioning | What it does that we should study |
|---|---|---|
**Questionmark** | Governance-grade item bank | **Versioned item lifecycle** with review states (draft → published); **item-level audit trail**; blueprint alignment; psychometric reporting |
**ExamSoft** | High-stakes exam operations | Versioned items, moderation before *and* after deployment; secure delivery tightly coupled to packaging |
**Learnosity** | API-first | **QTI export**, adaptive testing (item selection rules), API for item retrieval and assessment rendering into a custom UI |
**TAO** | Open / API | Programmatic item management for automation |
**Mettl, Cirrus** | Item governance | Versioned history + approval gates for repeatable assembly |
**Gradescope** | Rubric grading | **Grade by question across all submissions** — a fundamentally different and faster grading UI than grade-by-student |
**Respondus, ClassMarker** | Conversion / classroom | Randomized form generation from a bank; QTI/SCORM export |
**ZipGrade** | Teacher OSS | Answer-sheet scanning with instant results — the same job as our mobile scan, done cheaply |

**Four things this category does that we do not:**

1. **Version every item, with review states.** A published form must be
   reconstructable from the item revisions that produced it. Our question bank has
   no `version` field — flagged in [`../question-bank-api.md`](../question-bank-api.md) §3.
2. **Item-level audit trail.** Which item, which revision, in which administration.
   We have a general audit log; we do not have per-item provenance exposed.
3. **Grade by question, not by student** (Gradescope). A teacher marking 40 scripts
   is dramatically faster grading question 1 across all 40 than working student by
   student. Our evaluation flow is per-script. **This is the single most
   transferable UI idea in this entire document.**
4. **QTI export.** It is the interoperability format the whole sector speaks. If the
   question bank is to be an asset (§ [`../question-bank-api.md`](../question-bank-api.md)),
   QTI is a distribution channel we would be foolish to ignore.

---

## 6. The Indian edtech financial case studies — read this one

The most consequential lessons here are financial, not product. Sources:
[TechCrunch](https://techcrunch.com/2026/09/01/indias-unacademy-sells-to-rival-upgrad-for-206m-about-94-less-than-its-peak-valuation/),
[Economic Times](https://economictimes.indiatimes.com/),
[CompoundingAI](https://compoundingai.in/market-news/pwl-q4-fy26-earnings-call).

| Company | Peak | Now |
|---|---|---|
**BYJU'S** | $22 B (2022) | **Insolvency 2024.** Founder sentenced to six months for contempt in Singapore. Aakash — bought for ~$1 B — written off entirely |
**Unacademy** | $3.4 B (2021) | **Sold to upGrad for $206 M, September 2026 — ~94% below peak.** ~$880 M raised across 13 rounds. Standalone revenue halved ₹716 Cr → ₹347 Cr |
**Vedantu** | $1 B (2021) | Survivor by restraint: revenue roughly flat at ₹234 Cr FY25, still lossmaking (~₹157 Cr FY24), IPO planned |
**PhysicsWallah** | — | **Profitable and listed.** FY26 revenue ₹3,900 Cr (+35%), EBITDA ₹300 Cr (3× YoY), PAT positive. IPO Nov 2025 at ~₹31,526 Cr |

### Why PW won and the others did not

The Economic Times analysis of BYJU'S is the sharpest thing written on this:

> "Byju's expanded for a future that never arrived […] the company stopped behaving
> like a fast-growing business and started behaving like an empire in the making."

And on PhysicWallah, the contrast:

> "PhysicsWallah […] grew inside the actual exam-coaching demand cycle, NEET and JEE
> season after season, without assuming that demand would ever be anything more than
> seasonal and recurring. **That's the difference between a story and a balance sheet.**"

Four transferable lessons, all of which apply to a school-software business:

1. **Never assume a demand spike is permanent.** BYJU'S and Unacademy both built
   cost structures for a pandemic that ended. AcademicOS's demand is *seasonal and
   recurring* — admission season, term starts, exam season — and should be planned
   as such, not as a growth curve.
2. **Debt changes the psychology.** BYJU'S's $1.2 B term loan converted equity-style
   tolerance for losses into litigation. Prefer revenue.
3. **Acquisition-driven growth is how you lose the asset you bought.** BYJU'S lost
   Aakash by failing the terms of its own acquisition. Build, do not buy, until
   there is a discipline to integrate.
4. **Governance failure is preceded by auditor resignation.** Deloitte resigned
   before the collapse became public. The auditability we are building (per-item
   audit trails, versioned records, provenance) is not compliance theatre — it is
   the thing that survives a crisis.

And one more, from PW's own numbers: **retention under 2%, <1% NPA on student
loans, and a shift to "100% asset-light K-12"** with no further M&A capital. The
company that is profitable is the one that stopped trying to own everything.

---

## 7. Where every incumbent is weak — our opening

| Gap | Who fails at it | Why we can win |
|---|---|---|
**The academic/curriculum layer** | Every SIS. PowerSchool, Infinite Campus and Skyward are records systems; curriculum is a module, not the core | Real CBSE/NCERT curriculum with 46 chapters decomposed to 404 subtopics, admin-approved |
**Authentic questions *with official marking schemes*** | Nobody in India combines both at this granularity. Question banks abroad sell governance, not content | Our marking schemes are the scarce half — see `question-bank-api.md` §1 |
**Coverage and pace reporting tied to a real dated schedule** | Atlas does curriculum mapping; Planbook does plans; not the operational "planned vs actually taught, this week, this class" | We have it, tested |
**Offline for low-connectivity schools** | Most Indian vendors are cloud-only; only a few claim offline Android | AcademicOS Mobile is fully offline — a genuine, hard-to-copy advantage |
**Flat published pricing** | Almost everyone meters per student or hides behind a quote | Duplicable by competitors, but a real wedge right now |
**Grade-by-question marking** | Only Gradescope, and it is not India-focused | A UI idea we can adopt cheaply |
**Predictable, inspectable generation** | Generative tools are black boxes; the ITS study (see `ui-ux-principles.md` §5) shows teachers abandon them | Our review/approve flow, if we keep it prominent |

---

## 8. What NOT to copy

- **Per-student pricing.** It punishes the schools that grow, and it makes the
  invoice unpredictable — the opposite of what a ₹9,000-flat competitor advertises
  as its advantage.
- **Quote-only pricing.** Every global SIS does it. It makes comparison impossible
  and creates pressure to buy quickly. Two Indian challengers are winning
  explicitly on published flat rates.
- **Per-module gating.** Fedena's most repeated criticism is that base price is
  reasonable and transport/hostel/reporting are add-ons. Module creep is how you
  lose trust after the sale.
- **Product pivots that remove features.** Teachmint "has pivoted its product
  strategy several times. Features present in an earlier version have been changed
  or removed, affecting schools that built workflows around them."
- **District-scale complexity for a 300-student school.** Infinite Campus has 1,500
  tools and a learning curve. Gradelink competes on the opposite: simplicity.
- **Enterprise "one platform for everything".** The category's most successful
  financial performer is the one that went asset-light and stopped buying.
- **Administrator-only sales.** The 5% problem: "you can sell to chief academic
  officers […] but you're not always accountable for the use of the products."
  Teachers renew, even when administrators buy.

---

## 9. Synthesis: what to do about it

**Table stakes we must match** (or the product is not credible): attendance, fees,
report cards, parent communication, RBAC, audit log, data export. We should be
honest that we are weaker here than Entab or PowerSchool, and that this is
therefore *sales* work, not differentiation.

**Where to invest, in order**

1. **Grade-by-question marking** — the cheapest high-impact UI idea in this
   document, and it makes the evaluation feature genuinely better than the
   incumbents'.
2. **Item versioning + item-level audit trail** — required before the question bank
   can be sold as an asset, and it is the differentiator the whole assessment sector
   competes on.
3. **Constraint-based scheduling with an explicit, inspectable quality score** —
   the Untis model. This is a large piece of work and should follow, not precede,
   the two above.
4. **Gap analysis, not just coverage** — Atlas's "gaps and redundancies across
   grades" is what a principal actually wants from the report we already have.
5. **QTI export** — the sector's interoperability format; a distribution channel for
   the question bank.
6. **Flat published pricing and Hindi-first** — both are proven wedges in this
   market, and both are policy decisions rather than engineering.

**And the strategic constraint that overrides all of it:** the demand is seasonal
and recurring. Build for a school year that repeats, not for a curve that only goes
up. That is the whole difference between the company that got sold for $206 M and
the one that is profitable.
