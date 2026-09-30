# Sourcing questions with trustworthy answer keys (2026-09-30)

Why is it hard to fill a question bank whose every question carries a correct answer key, for CBSE grades 1-10?
**Part A** is what our own pipeline measured on the material processed so far. **Part B** is external research: what
exists, who owns it, what others do, and what the literature says. Part A is measured by the builders in
`src/academicos/corpus/` (#54). Part B was researched and cited source by source, and it is not legal advice.

## Part A: what our own pipeline measured

The bulk runs (`bank-pipeline/`, outside the repo) transcribe CBSE papers with their official marking schemes, and
NCERT chapters with their exercises plus questions written for each topic. The builders then accept or refuse each
question.

**Papers (board, sample, competency): 1,869 transcribed questions → 1,367 servable (73%).**

| Refused because | Count | Share |
|---|---|---|
| it needs a figure the student would not see | 234 | 12.5% |
| the transcribed answer could not be confirmed in the scheme's own text, nor by a second solve | 203 | 10.9% |
| an MCQ's options are incomplete | 50 | 2.7% |
| the answer sits in the wrong place in the scheme (a neighbour's answer) | 15 | 0.8% |

**Textbook chapters: 2,954 candidate questions → 1,910 servable (65%).**

| Where the questions came from | Count | What happened |
|---|---|---|
| The book's own exercises | 1,446 | **49%** are open-ended ("discuss", "do this activity") and can have no key; **25%** need a picture; NCERT prints its own answer for only **7%** (99) |
| Written for a chapter's topics | 1,508 | nearly all keyable by design (1,304 grounded in a quoted sentence of the chapter), but they are ours, not the board's: source `ai_generated`, "checked" tier |

**What we learned from it:**

- **Two models disagree often.**
  - On worked answers, two independent models disagreed on **127 of 568 (22%)**. A single model's answer is not a
    key.
  - Our rule: keep an answer only if a second solve agrees, and refuse it otherwise.
- **Official keys are hard to machine-read.**
  - Maths marking schemes set their working as images.
  - Many board papers are scans with no text layer.
  - The Hindi papers yield no text at all.
  - Verification therefore needs a vision model plus an independent second solve.
- **The work is throttled by quota, not code.**
  - About 40% of bulk attempts failed on empty or quota-limited replies, and there were 127 quota pauses in one night.
  - Median job time is about 230 s per chapter or paper.
  - All paid model plans in use (agy, opencode-go) ran out for hours at a time.
- **Coverage gaps by class.**
  - Classes 1-5 have no board papers, no Exemplar and no keyed official bank.
  - Their only material is the NCERT books, whose exercises are mostly open-ended or pictorial.
  - Keyed questions for these classes must be written, then checked.
- **Official keys contain errors too.**
  - The served bank's audits found wrong or misaligned keys in the competency items (4/60 in one sample) and
    Exemplar misalignments (D37).
  - "Official" is a tier, not a guarantee.
- **Official keys are rarely step-marked.**
  - 97.5% of served multi-mark keys are one all-or-nothing point (audit 2026-09-30, QB-9).
  - Partial credit needs value points that the sources often do not print.

## Part B: external research

*Prepared 30 Sep 2026 for AcademicOS (CBSE, grades 1-10). Method: web research plus direct inspection of official PDFs, which were read in memory and not stored. Figures marked **(inspected)** come from our own reading of the cited file. This is not legal advice.*

### Bottom line

- Keyed official material is plentiful only for Class 10. Classes 6-9 have small keyed banks; classes 1-5 almost none [S10][S11][S21][S23].
- The largest risk is extraction, not solving: CBSE PDFs silently lose minus signs and θ, and 10 of 19 PDFs in one 2025 release are pure scans **(inspected)** [S4][S5].
- Frontier LLMs solve text-only school maths almost perfectly but still fail on rewordings, diagrams and Hindi. Disagreement between independent solvers is an effective triage signal [S41][S42][S37][S44].
- Indian government works are copyrighted for 60 years; a court upheld CBSE's ownership of its papers against a commercial reprinter; NCERT refuses permission to private publishers [S25][S27][S34].
- Khan Academy, IXL and AQA all have a human review or re-solve every item; AI drafts or selects, it does not set final keys [S53][S54][S55][S58].

### 1. Official sources and their answer keys

| Source | Classes | Key? | Format reality |
|---|---|---|---|
| CBSE board papers and marking schemes (MS) | X and XII only. Main and supplementary exams 2022-2026, plus the 2026 second board exam for X [S1][S2] | Yes, one MS per set | One ZIP per subject; 2025 Maths Standard MS = 19 PDFs (18 sets plus a visually-impaired version). Each MS is headed "Strictly Confidential", gives suggested value points and tells examiners to credit correct alternatives. Question stems are images; solutions extract as text with fractions flattened **(inspected)** [S3]. |
| CBSE Sample Question Papers (SQP) with MS | X and XII, one paper per subject per year | Yes | Born-digital text. Most subjects also have a Hindi (_hi) version, but no Hindi MS is listed for Maths in 2025-26 **(inspected)** [S7]. We could not verify exact release dates. |
| Competency Focused Practice Questions (CBSE with Educational Initiatives) | X (five subjects) and XII | Yes, per chapter | Science X: 87 of 145 pages have under 50 extractable characters (items are images); extracted text has broken ligatures **(inspected)** [S9]. |
| CBSE/British Council item banks | Classes 6-10, Maths, Science and English | Yes, with mark guidance | Text PDFs, but small: 394 maths and 262 science items across classes 6-10 **(inspected)** [S10][S11]. The companion assessment specification is organised by pre-2023 textbook chapters [S11b]. |
| CBSE Class X Question Bank on DIKSHA | X | Step-by-step solutions curated by teachers | Over 2,000 questions [S12]. DIKSHA resources are licensed CC BY-NC-SA, and NCERT textbooks there are CC BY-NC-ND [S13]. |
| Practice papers by Educational Initiatives on DIKSHA | 3-9 | Not stated | [S10] |
| NCERT Exemplar | 6-12, Maths and Science only, with Hindi editions for most [S14] | Short answers only, no full working | Answer pages stamped "not to be republished"; Class X chapter dated 2018, predating NCF-SE 2023 books; exponents flatten on extraction (q² → "q2") **(inspected)** [S15][S16]. |
| NCERT textbooks | 1-10 | Mixed | Old Class X maths has an answers file [S17]. New Ganita Prakash (6-8) chapter PDFs append solution pages; sampled chapters of Ganita Manjari (9), Curiosity (7-8), Class 9 science and Maths Mela (3, 5) have none **(inspected)** [S18][S19]. |
| PARAKH Rashtriya Sarvekshan 2024 | 3, 6, 9 [S22] | No key in the Grade 3 sample PDF | 30 sample items, heavily pictorial **(inspected)** [S21] |
| SAFAL | 3, 5, 8 | None | Frameworks only. The maths handbook contains no keyed items **(inspected)** [S23]. |

**Gaps by class and subject:**
- **Classes 1-5:** no board papers, no Exemplar and no CBSE keyed item bank.
- **Classes 6-9:** keyed material is limited to about 650 British Council items, Exemplar answers and the Ganita Prakash solutions.
- **Hindi medium is the weakest:** the 2025 Hindi Course A papers yielded no Devanagari text at all **(inspected)** [S6].

Official keys also err. In 2022 CBSE re-scored 28,130 Class 10 Odia candidates after an expert committee corrected the answer key [S24].

### 2. Rights

- **Government works are protected, not public domain.** Works made under the direction of government or a public undertaking belong to that body and are protected for 60 years from publication (ss. 2(k), 17(d)/(dd), 28, 28A) [S25].
- **CBSE papers:**
  - A 1993 order dismissed a CBSE licensee's suit because CBSE's ownership was not proved [S28].
  - In 1996 the Delhi High Court held that question papers are original literary works owned by CBSE under s.17(dd). It rejected the commercial publishers' fair-dealing defence and granted an injunction [S27].
  - Marking schemes carry a warning against publishing them [S3]. We found no reuse licence on CBSE's websites.
- **NCERT:**
  - Its books state that all rights are reserved [S20].
  - It grants copyright permission only to State/UT boards, never to private publishers [S34].
  - An April 2024 press release warns of action against commercial use of textbook content, in whole or in part [S33].
  - A Lok Sabha reply reports 51 FIRs over counterfeit NCERT books in 2023-25 [S35].
- **Exceptions:**
  - s.52(1)(i) allows reproduction by a teacher or pupil during instruction, and as exam questions or answers [S26].
  - In the DU photocopy case, the Delhi High Court Division Bench held that copying by a third-party copy shop for instruction is covered [S29]. The publishers then withdrew the suit, and the Supreme Court declined to intervene [S30].
  - A 2024 Andhra Pradesh High Court ruling that maths and science textbooks are unprotected is widely criticised as weakly reasoned [S31].
- **Implication for AcademicOS:** a school reproducing a question in its own exam sits near s.52(1)(i); a vendor selling a bank of CBSE/NCERT items looks more like the 1996 commercial publisher. Guidebook publishers such as Educart do sell past papers with marking-scheme solutions [S60]; we found no public evidence of whether they hold licences. DIKSHA's non-commercial licences exclude paid use [S13].

### 3. Technical difficulties

**Extraction (inspected):**
- In the 2025 Class X Science release, 10 of 19 PDFs had zero extractable text, while sets 1 to 3 were bilingual text [S4].
- In Maths Standard set 30/1/1, extraction silently dropped minus signs and θ ("2x − 3y + a = 0" came out as "2x  3y + a = 0") [S5]. Silent corruption is worse than failure: an LLM will confidently solve the wrong question.
- Devanagari OCR on real printed scans: best system 86.3 chrF++, GPT-5.5 58.5; some OCR models emitted up to 71× the reference length [S36].

**Figures:** on vision-only CBSE/JEE maths items the best evaluated model scored 38.15%, lower in Hindi [S37]; models often answer from the text without reading the diagram [S39]; on Indian primary-exam visual items they are weak at folding, reflection and rotation, which the authors warn can cause wrong marking [S38].

**Alignment:** marking schemes are per set code, with image stems and OR-alternatives such as 29(A)/29(B) [S3]. The three sets within a region share ~67% of 8-word shingles vs ~15% across regions **(inspected)** [S4], so keys must be joined on (year, set code, question number) and near-duplicates collapsed, e.g. with MinHash [S52].

**LLM-generated keys:**
- Latest models score near-perfectly on Finnish upper-secondary maths exams [S44], yet one irrelevant added clause cut accuracy by up to 65% [S41], and in 2023 GPT-4 solved under 40% of JEE Advanced problems [S40].
- Human keys have defects too: frontier models run over GSM8K's 1,319 test items flagged 219; review removed 110 as ill-posed and relabelled 10 [S42]. 6.49% of MMLU questions contain errors [S43].
- Self-correction without external feedback does not help and can hurt [S47]. External checks do: self-consistency (majority vote over samples) +17.9 points on GSM8K [S45]; delegating arithmetic to Python (PAL) +15 points [S46].
- LLM marking against a mark scheme matched GCSE examiners at least as closely as examiners matched each other [S48].

**Difficulty and Bloom labels:** Bloom agreement varies widely: kappa 0.15-0.24 for a teacher panel vs 0.41-0.47 for experts; 0.53 on 585 biology items [S49]. A single expert's absolute difficulty rating correlates only ~0.15-0.5 with measured difficulty; ranking against anchor items reaches a median of 0.79, and five raters making three comparisons each roughly equal difficulty measured on 100 examinees [S50]. IRT calibration needs ~100 responses per item (Rasch) or 500 (three-parameter model) [S51].

### 4. How others source questions

- **Khan Academy:** a 20-person content team maintains over 100,000 questions. Humans write the first item of each type, an LLM drafts similar items, and every output is reviewed [S53].
- **IXL:** subject specialists (about half former teachers, half subject experts with advanced degrees) run several review rounds plus a sensitivity review [S54].
- **AQA:** a lead writer drafts, a reviser checks, an approval meeting signs off questions, a scrutineer sits the paper and a second scrutineer sits it again after typesetting; chief examiner and chair sign off [S55].
- **Embibe:** 30 faculty built a ~62,000-concept tree and hand-tagged hundreds of thousands of questions (difficulty, time, Bloom); OCR ingestion; IRT on attempt data; claims its auto-tagger picks the right concept 82% of the time vs 18% for crowd-sourced faculty (unverified vendor claim) [S56][S57].
- **Extramarks:** its AI selects only from an expert-vetted bank, and the teacher edits the draft paper [S58].
- **Examin8 (myCBSEguide):** over 7 lakh questions for classes 3-12, with solutions. It does not disclose who writes them or how they are checked [S59].
- **Not found:** we found no public description of review workflows or costs for BYJU'S, Vedantu, Toppr or Arihant, and no primary source for per-item review cost.

### 5. Recommendations for a small team

1. **Source priority:** (a) SQPs with marking schemes and the CBSE/British Council banks (text, keyed); (b) board marking schemes, Class 10 only, via page-image OCR; (c) Competency Focused Practice Questions (keyed, mostly images); (d) Ganita Prakash solutions and Exemplar answers as verification references, not served content; (e) classes 1-5 and other gaps: original parameterised items whose keys are computed by code.
2. **Gate extraction before solving:** show the page image beside extracted text, flag lost operators and symbols, attach figures, reject figure-dependent items without the figure.
3. **Accept keys in tiers:** official key plus one agreeing independent solve → accept; no official key → accept only if two model families and a code check agree; any disagreement, figure, Hindi or pictorial grade 1-5 item → human. Subjective items: store and label value points; the teacher judges.
4. **Measure residual error:** human-audit a random sample per stratum each release, as GSM8K-Platinum did.
5. **Humans:** one reviewer per subject stage acting as an AQA-style scrutineer who sits each new paper; an in-app "report key error" button.
6. **Difficulty/Bloom:** comparative judgements against anchors now; Rasch calibration once items have ~100 responses.
7. **Rights:** log provenance and licence per item; seek written permission from CBSE and NCERT or a legal opinion; meanwhile prefer original items and reference official ones to source; exclude DIKSHA non-commercial content from paid tiers.

### Sources

- [S1] CBSE previous years' question papers: https://www.cbse.gov.in/cbsenew/question-paper.html
- [S2] CBSE marking schemes index: https://www.cbse.gov.in/cbsenew/marking-scheme.html
- [S3] CBSE Class X 2025 Maths marking schemes (ZIP): https://www.cbse.gov.in/cbsenew/Marking-Scheme/2025/X/Math.zip
- [S4] CBSE Class X 2025 Science question papers (ZIP): https://www.cbse.gov.in/cbsenew/question-paper/2025/X/086_Science.zip
- [S5] CBSE Class X 2025 Maths Standard question papers (ZIP): https://www.cbse.gov.in/cbsenew/question-paper/2025/X/041_Mathematics_Standard.zip
- [S6] CBSE Class X 2025 Hindi Course A question papers (ZIP): https://www.cbse.gov.in/cbsenew/question-paper/2025/X/002_Hindi_Course_A.zip
- [S7] CBSE Class X SQP and MS 2025-26: https://cbseacademic.nic.in/sqp_classx_2025-26.html
- [S9] CFPQ Science Grade 10: https://cbseacademic.nic.in/web_material/Manuals/CFPQ_Science10.pdf
- [S10] CBSE CBE assessment resources: https://cbseacademic.nic.in/cbe/assessment.html
- [S11] Item Bank, Maths Class 6: https://cbseacademic.nic.in/cbe/documents/Item-Bank---Maths-Class-6.pdf (counts from all Maths/Science 6-10 item banks linked in [S10])
- [S11b] Assessment specification, Maths Class 6: https://cbseacademic.nic.in/cbe/documents/SAS_Maths-Class-6.pdf
- [S12] CBSE Question Bank for Practice, Class X (DIKSHA): https://cbseacademic.nic.in/revision10.html
- [S13] CIET-NCERT DIKSHA page (licences): https://ciet.ncert.gov.in/initiative/diksha?lang=en
- [S14] NCERT Exemplar problems index: https://ncert.nic.in/exemplar-problems.php
- [S15] NCERT Exemplar Class X Maths answers: https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep2an.pdf
- [S16] NCERT Exemplar Class X Maths ch.1: https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep201.pdf
- [S17] NCERT Class X Mathematics answers: https://ncert.nic.in/textbook/pdf/jemh1an.pdf
- [S18] Ganita Prakash chapter PDFs with solutions: https://ncert.nic.in/textbook/pdf/fegp110.pdf ; https://ncert.nic.in/textbook/pdf/gegp105.pdf ; https://ncert.nic.in/textbook/pdf/hegp105.pdf
- [S19] NCERT textbook listing and sampled chapters: https://ncert.nic.in/textbook.php ; https://ncert.nic.in/textbook/pdf/iemh103.pdf ; https://ncert.nic.in/textbook/pdf/hecu103.pdf ; https://ncert.nic.in/textbook/pdf/cemm103.pdf
- [S20] Ganita Prakash prelims (rights notice): https://ncert.nic.in/textbook/pdf/fegp1ps.pdf
- [S21] PARAKH Rashtriya Sarvekshan 2024 Grade 3 sample items: https://parakh.ncert.gov.in/themes/parakh/prs-files/Grade3.pdf
- [S22] Careers360, PARAKH 2024 grades 3, 6, 9: https://news.careers360.com/parakh-rashtriya-sarvekshan-2024-today-for-classes-3-6-and-9-in-over-87600-schools
- [S23] SAFAL: https://cbseacademic.nic.in/safal/index.html ; https://cbseacademic.nic.in/safal/assets/pdf/safal_mathshandbook.pdf
- [S24] Careers360, Odia answer-key correction: https://news.careers360.com/cbse-class-10-term-1-result-2021-22-revised-for-28130-students-post-errors-in-odia-answer-key-dharmendra-pradhan-cbse-gov-in/amp
- [S25] Copyright Act 1957 (full text): https://indiankanoon.org/doc/1136195/
- [S26] Copyright Act s.52: https://indiankanoon.org/doc/1013176/
- [S27] Rupendra Kashyap v Jiwan Publishing House (Del HC, 1 Jul 1996): https://indiankanoon.org/doc/134584/
- [S28] Rupendra Kashyap v Jiwan Publishing House (Del HC, 16 Dec 1993): https://indiankanoon.org/doc/235392/
- [S29] Univ. of Oxford v Rameshwari Photocopy (Del HC DB, 9 Dec 2016): https://indiankanoon.org/doc/114459608/
- [S30] Rameshwari case aftermath: https://en.wikipedia.org/wiki/University_of_Oxford_v._Rameshwari_Photocopy_Service
- [S31] SpicyIP on Addala Sitamahalakshmi (AP HC 2024): https://spicyip.com/2024/04/is-every-educational-use-a-fair-use-looking-at-the-ap-hcs-curious-decision-on-textbooks-and-copyright.html
- [S33] NCERT press release, 7 Apr 2024: https://www.ncert.nic.in/pdf/announcement/notices/Press_Release_Copyright_Infringement-NCERT.pdf
- [S34] NCERT notice on copyright permission: https://ncert.nic.in/pdf/publication/informationtocustomers/advtforgenuinebook.pdf
- [S35] Careers360, 51 FIRs (Lok Sabha reply): https://news.careers360.com/ncert-books-textbooks-fake-copied-51-fir-5-lakh-seized-most-2025-grows-890-pc-education-ministry-haryana-uttar-pradesh-delhi
- [S36] Can OCR-VLMs Read Devanagari?: https://arxiv.org/abs/2606.29213
- [S37] GanitBench: https://arxiv.org/abs/2508.03737
- [S38] Visual Reasoning Benchmark (primary exams): https://arxiv.org/abs/2602.12196
- [S39] MathVerse: https://arxiv.org/abs/2403.14624
- [S40] JEEBench: https://arxiv.org/abs/2305.15074
- [S41] GSM-Symbolic: https://arxiv.org/abs/2410.05229
- [S42] GSM8K-Platinum: https://huggingface.co/datasets/madrylab/gsm8k-platinum ; https://arxiv.org/abs/2502.03461
- [S43] Are We Done with MMLU?: https://arxiv.org/abs/2406.04127
- [S44] LLMs in upper-secondary mathematics (Finland): https://arxiv.org/abs/2504.12347
- [S45] Self-consistency: https://arxiv.org/abs/2203.11171
- [S46] PAL: https://arxiv.org/abs/2211.10435
- [S47] LLMs cannot self-correct reasoning yet: https://arxiv.org/abs/2310.01798
- [S48] LLM marking on double-marked GCSE: https://arxiv.org/abs/2606.24973
- [S49] Coleman (2017), reliability of educational taxonomies: https://www.cambridgeassessment.org.uk/Images/426171-on-the-reliability-of-applying-educational-taxonomies.pdf
- [S50] Attali et al. (2014), ETS RR-14-39: https://files.eric.ed.gov/fulltext/EJ1109277.pdf
- [S51] ASC, CAT and IRT calibration sample sizes: https://assess.com/computerized-adaptive-testing/
- [S52] Deduplicating training data: https://arxiv.org/abs/2107.06499
- [S53] Khan Academy, AI in content development: https://support.khanacademy.org/hc/en-us/articles/20349258135181-How-does-Khan-Academy-use-AI-in-our-content-development-process
- [S54] IXL Design Principles: https://www.ixl.com/research/IXL_Design_Principles.pdf
- [S55] AQA Inside Exams, question papers: https://store.aqa.org.uk/content/inside-exams/AQA-INSIDE-EXAMS-S2-E1-QP.PDF
- [S56] Embibe, learning outcomes AI stack: https://www.embibe.com/in-en/artificial-intelligence-ai-in-education/building-the-learning-outcomes-ai-stack/
- [S57] Inc42 on Embibe data science lab: https://inc42.com/resources/embibes-data-science-lab/
- [S58] Extramarks on AI question paper creation: https://www.extramarks.com/ai-in-education/how-ai-transforms-question-paper-creation/
- [S59] myCBSEguide / Examin8 test generator: https://mycbseguide.com/test-generator/
- [S60] Educart CBSE Class 10 question bank: https://www.educart.co/cbse/cbse-question-bank-class-10
