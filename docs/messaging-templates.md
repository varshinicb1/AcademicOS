# SMS and WhatsApp templates (INT-2)

What the owner registers before SMS or WhatsApp can send anything, and
what the server sends into each template. The code is
`src/academicos/operations/messaging.py`; `TEMPLATE_VARS` there is the
source of truth for the variable order below.

Both channels send **registered templates only**. DLT (for SMS in India)
and Meta (for WhatsApp) both refuse a template made only of variables, so
the fixed words live in the template and only a notice's details are sent.
DLT also caps each variable at **30 characters**: the server cuts longer
values (a long homework title, for example) at 30.

Until a channel's account settings are set, it records "skipped: not
configured" and nothing leaves the server. A kind whose SMS template is not
registered is recorded "skipped: no SMS template registered for this
notice"; it is never sent as free text.

## Settings (Cloud Run)

| Setting | Secret? | What |
|---|---|---|
| `ACOS_WHATSAPP_TOKEN` | yes | A WhatsApp Business Platform (Cloud API) system-user token |
| `ACOS_WHATSAPP_PHONE_NUMBER_ID` | no | The sending number's id |
| `ACOS_WHATSAPP_TEMPLATE_PREFIX` | no | Default `academicos_`; the template for a kind is the prefix plus the kind |
| `ACOS_WHATSAPP_API_VERSION` | no | Default `v21.0` |
| `ACOS_SMS_AUTHKEY` | yes | The MSG91 auth key |
| `ACOS_SMS_FLOW_<KIND>` | no | The MSG91 flow id of the DLT template for that kind, for example `ACOS_SMS_FLOW_HOMEWORK_DUE` |
| `ACOS_SMS_FLOW_<KIND>_HI` | no | The same in Hindi, used for people who chose Hindi; English when unset |
| `ACOS_SMS_FLOW_CODE` | no | The flow for the one-time confirmation code |

One setting per template, not a JSON map, because `gcloud run deploy
--set-env-vars` splits on commas.

## The templates

The first variable is always whom the notice is about. On a person's own
message, it is their own first name. On a parent's copy of a student's
notice, it is the child's first name, so a parent of two knows which child.
In MSG91 flows, the variables are named as below (`##name##`, `##title##`).
In WhatsApp templates, they are `{{1}}`, `{{2}}` and so on, in this order.

| Kind (WhatsApp `academicos_<kind>`, SMS `ACOS_SMS_FLOW_<KIND>`) | Goes to | Variables, in order | Suggested English text |
|---|---|---|---|
| `substitution_proposed` | the teacher asked to cover | name, date, subject, section, period | `{{1}}, please cover {{3}} for {{4}}, period {{5}}, on {{2}}. Accept or decline in AcademicOS.` |
| `leave_decided` | the teacher who applied | name, decision, start, end | `{{1}}, your leave from {{3}} to {{4}} was {{2}}.` |
| `homework_due` | the student's linked parents | name, title, due | `{{1}}'s homework "{{2}}" is due {{3}} and is not submitted yet.` |
| `exam_reminder` | the student's linked parents | name, exam, subject, start, end | `{{1}} has {{2}}: {{3}} tomorrow, {{4}}-{{5}}.` |
| `duty_reminder` | the invigilating teacher | name, exam, count, first | `{{1}}, you invigilate {{3}} papers of {{2}} tomorrow; the first is {{4}}.` |
| `holiday_declared` | teachers, and students' linked parents | name, label, dates | `School is closed for {{2}} on {{3}} ({{1}}).` |
| `code` | the person confirming their number | code | WhatsApp: an **authentication** template with a copy-code button. SMS: `Your AcademicOS code is ##code##. It lasts 10 minutes.` |

The WhatsApp templates are the **utility** category, except `code`. The
one-time code template is the **authentication** category. Its code goes in
the body parameter and in the copy-code button's parameter. Register each in
English (`en`) and Hindi (`hi`); the language sent is the recipient's own
choice.

## What is not sent

- **Principal alerts** are free text (`principal_alert`: any title and
  body), and no registered template can carry free text. They stay in the
  app and email. A principal who teaches gets the teacher kinds above.
- **Anything to an unconfirmed number.** A new or changed number gets the
  one-time code and nothing else until the code comes back. The code is
  limited to one a minute and five a day per person, and five wrong tries
  end a code.
