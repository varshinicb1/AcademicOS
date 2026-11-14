# Notifications policy

**v1.0 · 2026-09-17** · Referenced from [`design-system.md`](design-system.md) §12.

The research finding behind this file: most school software's notification
strategy destroys trust, and an engagement-driven push is how that happens. A
teacher who receives four notifications a week that are not about their next
action learns to ignore all of them — including the one that mattered.

---

## The policy

| Notification | Sent? | Trigger | Why |
|---|---|---|---|
**Morning digest** | ✅ one per school day | The teacher's own timetable, ~45 min before their first period | Answers "what am I teaching today" — a question they already ask themselves every morning. It is a service, not a prompt. |
Lesson marked by someone else | ✅ | A principal overrides a lesson completion the teacher recorded | It corrects the teacher's own record; they must not be surprised by it. |
Paper approved / returned | ✅ | A principal approves or returns the teacher's paper | Blocks the teacher's next step. |
Lesson rescheduled onto me | ✅ | A principal reschedules onto the teacher's calendar | Changes what they teach today. |
Register not taken | ✅ | 11:00 on a school day, a class with students and no register: its class teacher; the principal gets one line naming every such class | The register is the class teacher's next action; parents' absence notices depend on it |
Overdue summary | ✅ one per week | **Principal only**, Monday morning | A management cadence, not a nudge. |
New feature available | ❌ | — | Product marketing inside an operations tool. |
"Continue where you left off" | ❌ | — | Engagement-driven. |
Streak reminder | ❌ | — | See `design-system.md` §12: there are no streaks. |
Anything containing an emoji | ❌ | — | Banned product-wide. |

---

## Rules

1. **A notification is about the recipient's next action, or it is not sent.**
   If the honest purpose is "make them open the app", do not send it.
2. **One digest beats many alerts.** Batch anything not time-critical into the
   morning digest.
3. **Quiet hours are absolute.** Nothing outside 07:00–19:00 IST, and nothing on
   Sundays or declared holidays — the school calendar already knows these dates,
   so read them from it rather than hardcoding.
4. **Never notify about a metric.** "Your coverage is 62%" is a report; it belongs
   on a screen, not on a lock screen.
5. **Every notification is individually mutable**, defaulting on only for the
   digest. A user who cannot turn one off will turn all of them off.
6. **No per-teacher comparison, ever.** Nothing that ranks teachers by usage,
   speed or compliance. See `design-system.md` §12.

---

## Why this is a hard rule and not a preference

The adoption research is unambiguous that **time pressure, not motivation**, is
why teachers abandon school software — and that a tool which costs attention
without returning an answer is the first thing dropped. Notifications are the
most expensive attention this product can spend. Spending it on engagement
metrics spends the trust that the curriculum and assessment features need.

Sources and reasoning: [`research/ui-ux-principles.md`](research/ui-ux-principles.md) §4 and §5.
