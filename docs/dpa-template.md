# Data Processing Agreement (Template)

**Status: a fillable template, not a signed document and not a certification.**
This agreement becomes binding only when the bracketed `[FILL IN]` fields are
completed, both parties sign, and a real legal review (ideally an Indian data
protection / education-sector lawyer) has confirmed it matches the school's and
AcademicOS's actual practices on the day it is signed. Nothing here is a claim
that AcademicOS is "DPDP-compliant" or "CERT-In registered"; the template
records commitments, and commitments are only as good as their implementation.

DPDP Act 2023 requires that a data processing agreement exist **before any real
student data moves**. Every data subject under this agreement is a minor, so the
child-data provisions of the DPDP Act 2023 apply throughout.

---

## DATA PROCESSING AGREEMENT

This Data Processing Agreement ("**DPA**") is made on **[DATE]** between:

**(a) The School — "Data Controller"**
Name: **[FILL IN — School legal name]**
Registered address: **[FILL IN]**
Contact person for data protection matters: **[FILL IN — name, title, email,
phone]**

and

**(b) AcademicOS — "Data Processor"**
Name: **[FILL IN — legal entity operating AcademicOS; if none registered yet,
state "operating as AcademicOS" and name the natural person]**
Registered address: **[FILL IN]**
Contact person for data protection matters: **[FILL IN — name, title, email,
phone]**

(each a "**Party**"; together the "**Parties**").

### Recitals

**WHEREAS** the School wishes to use AcademicOS to generate assessments, grade
student answer sheets, and produce mastery/analytics reporting for its own
students; and

**WHEREAS** AcademicOS will process personal data of the School's students on
the School's behalf in the course of providing those services; and

**WHEREAS** the School is the data controller and AcademicOS is the data
processor within the meaning of the Digital Personal Data Protection Act, 2023
("**DPDP Act**"), and the Parties intend to set out their respective
obligations in writing before any student data is transferred.

**NOW THEREFORE** the Parties agree as follows:

### 1. Appointment and scope

1.1 The School appoints AcademicOS as a data processor to process the Data
Categories in Section 4 solely for the Processing Purposes in Section 2, on the
School's documented instructions. AcademicOS processes data on the School's
instructions only and does not determine the purposes or means of processing.

1.2 AcademicOS shall process student data only on behalf of and under the
instructions of the School, and shall not use such data for any purpose other
than the Processing Purposes without the School's prior written consent.

### 2. Purpose limitation

2.1 The only permitted purposes ("**Processing Purposes**") are:

   (a) **Assessment generation** — creating question papers and answer schemes
       for the School's own students;
   (b) **OCR-based grading** — scanning and transcribing student answer sheets
       and evaluating them against the School's marking schemes;
   (c) **Mastery and analytics reporting** — deriving mastery/analytics data
       for the School's own students and reporting it to the School.

2.2 **No secondary use.** The School's student data, including scanned answer
sheet images and OCR-extracted text, shall **not** be used for any secondary
purpose — including, without limitation, training, fine-tuning, or otherwise
improving machine-learning models — without separate, specific, informed
consent obtained from the parent/guardian of the affected student(s) beyond
whatever consent covers the primary grading purpose. Under the DPDP Act 2023,
children's data is subject to heightened protections; AcademicOS will not
engage in behavioural tracking, profiling, or targeted advertising of students
in any case.

### 3. Instructions and responsibility for consent

3.1 The School is the data controller and is responsible for ensuring it has
lawful grounds to submit student data, including the **verifiable consent of the
parent or guardian** of each student (all data subjects being minors) obtained
in accordance with the DPDP Act 2023. AcademicOS shall process data on the
School's documented instructions and shall not be responsible for obtaining or
validating parental consent, but shall flag to the School any processing it
reasonably believes exceeds those instructions.

3.2 The School shall not submit data it knows to be false, and shall keep its
instructions to AcademicOS lawful.

### 4. Data categories processed

The following categories of personal data are processed under this DPA:

   (a) Student name;
   (b) Roll number;
   (c) Grade/class and subject;
   (d) Scanned answer sheet images (photographs or PDF scans of handwritten
       answer scripts);
   (e) OCR-extracted text from answer sheets;
   (f) Awarded marks / grading results;
   (g) Mastery/analytics derived data.

### 5. Sub-processors

5.1 AcademicOS uses the following sub-processors to deliver the services, and
discloses them now as required:

   | Sub-processor | Role | Data it receives |
   |---------------|------|------------------|
   | **Sarvam AI** | OCR vision API (`api.sarvam.ai`, doc-digitization) and LLM scoring (`sarvam-105b`) | Receives scanned answer sheet images and OCR-extracted answer text; may also process OCR text for grading |
   | **Supabase** | Hosting/storage backend (Postgres-backed stores, including the append-only audit log, when configured) | Receives stored student data and audit records |
   | **Render** | Backend hosting provider | Receives/hosts backend application data, including student data and logs, on its infrastructure |

5.2 AcademicOS shall not add or replace a sub-processor (or change the data a
sub-processor receives in a way that affects the categories in Section 4)
without giving the School **written notice** and, where required by law, giving
the School an opportunity to object.

### 6. Retention period and deletion rights

6.1 Default retention: student data is retained for **[FILL IN — suggested
default: the academic year in which the data was collected plus one further
year; the School may negotiate a shorter or longer period]**, after which it is
deleted or anonymized unless a shorter period is required by law or a longer
period is required by legal/regulatory retention obligations.

6.2 **Deletion on request.** The School may request deletion of some or all
student data at any time; AcademicOS shall comply within **[FILL IN — suggested
default: 30 days]** of a written, verified request, except where retention is
required by law.

6.3 Deletion includes the scanned answer sheet images, OCR-extracted text, and
derived marks/mastery data. AcademicOS shall confirm deletion in writing, and
shall instruct sub-processors to delete where the data is held by them.

### 7. Security measures

AcademicOS shall implement and maintain appropriate technical and
organisational measures, including at least the following measures **that are
already built into the AcademicOS platform** as of the date of this DPA:

   (a) **Encryption at rest for local/offline student data** on the Android
       build: the offline student-data store (`SecureBox` /
       `HiveAesCipher`, `frontend/lib/core/local_engine/secure_box.dart`)
       encrypts all locally stored assessment, evaluation, and mastery records
       with AES using a 256-bit key held in the app's OS-sandboxed private data
       directory. (Note: the key is not hardware-Keystore-backed; this is
       documented in `docs/compliance.md`.)
   (b) **Append-only audit logging** of every grading write and every paper
       export: the server-side `AuditLog` class
       (`src/academicos/assessment/audit_log.py`) records
       timestamp/action/assessment_id/student_id/actor/details, persists to
       SQLite or Supabase, and is never modified or deleted through normal
       application code; the offline build mirrors this via
       `LocalStore.appendAuditLog`.
   (c) **Watermarked/traceable PDF paper exports**: every exported paper PDF
       carries a unique, audit-logged watermark ID stamped in the footer
       (`src/academicos/assessment/pdf.py`), so a leaked copy can be traced to
       the export that produced it.

AcademicOS shall keep the School informed of any material change to these
measures. Nothing in this Section relieves AcademicOS of compliance with the
DPDP Act 2023, the Information Technology (Reasonable Security Practices and
Procedures and Sensitive Personal Data or Information) Rules, 2011, or the
CERT-In 2022 Directions.

### 8. Breach notification

8.1 AcademicOS shall notify the School's named data-protection contact
**without undue delay** after becoming aware of a personal data breach
(including any data breach, data leak, unauthorized access, identity theft, or
phishing incident affecting the School's student data).

8.2 The notification shall include: the nature of the breach, the data
categories and (to the extent known) the number of affected data subjects,
steps taken to contain the breach, and the expected next steps.

8.3 AcademicOS shall follow the **incident-response runbook**
(`docs/incident-response-runbook.md`), under which reportable incidents are
notified to **CERT-In within 6 hours of awareness** (Section 70B, IT Act 2000)
and breach notifications are made to the **Data Protection Board** and affected
users/parents under the DPDP Act 2023. The School, as controller, is
responsible for the parent/guardian-facing notification, and AcademicOS shall
cooperate with the School to meet it without undue delay.

8.4 AcademicOS shall preserve evidence (including relevant `audit_log` rows)
to support the School's and its own notification and investigation obligations.

### 9. Data subject rights

9.1 All data subjects are minors. **Verifiable parental/guardian consent** for
each student is the School's responsibility to obtain and maintain before
submitting student data to AcademicOS, as required by the DPDP Act 2023.
AcademicOS shall assist the School, where reasonably possible, in responding to
requests from parents/guardians to access, correct, or delete their child's
data, and shall process such requests on the School's instructions.

9.2 Where a parent/guardian or the School requests correction or deletion,
AcademicOS shall implement the School's instruction within the applicable
timeframe in Section 6.2.

### 10. Term and termination

10.1 This DPA takes effect on the date first written above and remains in force
until the earlier of: (a) termination by either Party on **[FILL IN —
suggested default: 60 days']** written notice; (b) termination by the School
with immediate effect on written notice where AcademicOS materially breaches
its obligations under this DPA or applicable law; or (c) the end of the
services agreement between the Parties, if any.

10.2 On termination, AcademicOS shall, at the School's election, return or
delete all student data (subject to any legal retention obligation) in
accordance with Section 6, and confirm the same in writing.

### 11. Governing law and dispute resolution

11.1 This DPA is governed by the laws of **India**. Disputes shall be subject
to the exclusive jurisdiction of the courts of **[FILL IN — suggested default:
the School's location / [CITY]]**.

### 12. General

12.1 This DPA is without prejudice to any rights or obligations under the DPDP
Act 2023, the IT Act 2000 and the SPDI Rules 2011, and the CERT-In 2022
Directions, all of which prevail to the extent of any conflict.

12.2 **[FILL IN — any additional clauses the legal review requires.]**

### Signatures

For and on behalf of the **School** (Data Controller):

Signature: ______________________
Name: **[FILL IN]**
Title: **[FILL IN]**
Date: **[FILL IN]**

For and on behalf of **AcademicOS** (Data Processor):

Signature: ______________________
Name: **[FILL IN]**
Title: **[FILL IN]**
Date: **[FILL IN]**

---

*Before signing: complete every `[FILL IN]` bracket, obtain a legal review, and
confirm the security measures in Section 7 match the AcademicOS build actually
being used by the School. Signing this template does not by itself make
AcademicOS compliant; it documents commitments the platform must then actually
meet.*