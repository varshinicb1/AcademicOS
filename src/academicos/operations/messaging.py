"""SMS and WhatsApp as notification channels (REQUIREMENTS INT-2, NTF-1 P1;
SA-6: a parent "receives notices by push/WhatsApp/SMS").

Until now a notification reached a person only in the app (inbox and push)
or by email. Many parents read neither; nearly all read WhatsApp and SMS.

- **Who.** A person gives their own Indian mobile number and says, per
  channel, whether they want SMS and whether they want WhatsApp -- nothing
  is sent without that consent, and it can be withdrawn at any time. The
  number is confirmed first: a one-time code goes to it, and nothing else
  does until the code comes back, so a mistyped digit cannot send a child's
  details to a stranger. Staff and parents only: a student is a minor, and
  the notices about them (homework due, an exam tomorrow, a holiday) go to
  the parents their account is actively linked to (DPDP Act 2023). A
  principal who teaches gets what a teacher gets; the principal's own
  alerts are free text, which no registered template can carry, so they
  stay in the app and email.
- **What.** Only kinds about someone's next action that matter off the app,
  and not a kind whose push the person has turned off. Quiet hours hold
  messages like push; someone on a daily digest gets only the kinds that
  cannot wait. The same notice to the same person within a day goes once.
- **How.** Both channels send registered templates, one per kind: DLT (for
  SMS) and Meta (for WhatsApp) refuse a template made only of variables, so
  the fixed words are in the template and only the notice's details are
  sent, as TEMPLATE_VARS lists them (DLT caps each at 30 characters).
  WhatsApp through the Cloud API (template `academicos_<kind>`, in English
  or Hindi); SMS through MSG91's v5 flow API (one DLT flow per kind, named
  by ACOS_SMS_FLOW_<KIND>). Until the owner has the accounts, the sender
  registration and the approved templates, a channel records "skipped: not
  configured" and nothing leaves the server.
- **Once.** A delivery is claimed (`sending`, committed) before its provider
  call, so two senders at once -- notify()'s thread and a request -- never
  send it twice; SMS and WhatsApp are billed per send. A failure is retried
  after a wait, three tries in all. A claim left behind by a process that
  died mid-call becomes a failure and is not sent again: it may have gone.

Nothing here imports notifications.py or FastAPI at module level: that
module mixes this one in, and the routes are in messaging_routes.py.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

MESSAGING_SCHEMA = """
-- INT-2: a person's own mobile number, and their consent per channel.
CREATE TABLE IF NOT EXISTS contact_numbers (
  user_id     TEXT PRIMARY KEY,
  phone       TEXT NOT NULL,
  sms_ok      INTEGER NOT NULL DEFAULT 0,
  whatsapp_ok INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL
);
-- The number is the person's: confirmed by a one-time code sent to it. Its
-- own table, not columns, so a restored older snapshot needs no migration.
-- A row whose phone is not the current number confirms nothing.
CREATE TABLE IF NOT EXISTS contact_verifications (
  user_id       TEXT PRIMARY KEY,
  phone         TEXT NOT NULL,
  verified_at   TEXT,
  code_hash     TEXT,
  code_expires  TEXT,
  code_attempts INTEGER NOT NULL DEFAULT 0,
  last_sent_at  TEXT,
  sent_on       TEXT,
  sends_on_day  INTEGER NOT NULL DEFAULT 0
);
-- One row per message: a notification, the person it goes to (its own
-- recipient, or a parent of the student it is about) and the channel.
-- (Supersedes message_deliveries, whose key could not hold a parent's copy;
-- that table is no longer written.)
CREATE TABLE IF NOT EXISTS message_outbox (
  id              TEXT PRIMARY KEY,
  notification_id TEXT NOT NULL,
  user_id         TEXT NOT NULL,
  about_id        TEXT,
  channel         TEXT NOT NULL,
  kind            TEXT NOT NULL,
  vars_json       TEXT NOT NULL,
  dedupe          TEXT NOT NULL,
  status          TEXT NOT NULL,
  attempts        INTEGER NOT NULL DEFAULT 0,
  next_at         TEXT,
  last_error      TEXT,
  provider_id     TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  UNIQUE (notification_id, user_id, channel)
);
CREATE INDEX IF NOT EXISTS idx_outbox_due ON message_outbox(status, next_at);
CREATE INDEX IF NOT EXISTS idx_outbox_user ON message_outbox(user_id, channel, dedupe);
"""

MESSAGE_CHANNELS = ("sms", "whatsapp")
# The kinds worth a message: each is about the person's next action and
# loses its point if it waits until they open the app.
MESSAGE_KINDS = frozenset({"substitution_proposed", "leave_decided", "homework_due", "exam_reminder",
                           "duty_reminder", "holiday_declared"})
# Of those, the ones sent to students: each also goes to the student's
# actively linked parents, who are who reads SMS and WhatsApp.
GUARDIAN_KINDS = frozenset({"homework_due", "exam_reminder", "holiday_declared"})
MESSAGE_ROLES = ("teacher", "principal", "parent")
# Each kind's registered template takes these variables, in this order. The
# first is whom the notice is about: the person's own first name, or on a
# parent's copy the child's (a parent of two needs to know which).
TEMPLATE_VARS: dict[str, tuple[str, ...]] = {
    "substitution_proposed": ("name", "date", "subject", "section", "period"),
    "leave_decided": ("name", "decision", "start", "end"),
    "homework_due": ("name", "title", "due"),
    "exam_reminder": ("name", "exam", "subject", "start", "end"),
    "duty_reminder": ("name", "exam", "count", "first"),
    "holiday_declared": ("name", "label", "dates"),
}
_MOBILE = re.compile(r"^[6-9][0-9]{9}$")     # [0-9]: \d also takes Devanagari and other digits
SMS_VAR_LIMIT = 30        # DLT: characters per template variable
WHATSAPP_VAR_LIMIT = 200
MAX_TRIES = 3             # as notifications.MAX_ATTEMPTS
RETRY_AFTER = (timedelta(minutes=2), timedelta(minutes=15))   # before the 2nd and the 3rd try
STUCK_AFTER = timedelta(minutes=15)
REPEAT_WINDOW = timedelta(hours=20)
CODE_TTL = timedelta(minutes=10)
CODE_TRIES = 5
CODE_COOLDOWN = timedelta(seconds=60)
CODES_PER_DAY = 5
_IST = timezone(timedelta(hours=5, minutes=30))


def normalize_mobile(raw: str) -> str:
    """An Indian mobile number as +91XXXXXXXXXX, from the ways people type
    it ("98765 43210", "+91-98765-43210", "098765 43210"). ValueError for
    anything else: this product serves Indian schools."""
    digits = re.sub(r"[\s\-().]", "", raw or "")
    if digits.startswith("+91"):
        digits = digits[3:]
    elif digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if not _MOBILE.match(digits):
        raise ValueError("give an Indian mobile number: 10 digits starting with 6, 7, 8 or 9")
    return "+91" + digits


def _iso(dt: datetime) -> str:
    """UTC, to the second: these compare as strings."""
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _clean(value: Any, channel: str) -> str:
    """A template variable as the provider accepts it. WhatsApp refuses a
    variable with a newline, a tab or more than four spaces in a row (error
    132018), and an empty one; DLT caps each at 30 characters."""
    text = " ".join(str(value if value is not None else "").split())
    text = text[:SMS_VAR_LIMIT if channel == "sms" else WHATSAPP_VAR_LIMIT].strip()
    return text or "-"


def template_vars(kind: str, params: dict[str, Any], name: Optional[str]) -> list[str]:
    """The kind's variables from a notification's params, raw (cleaned per
    channel when sent)."""
    return [(name or "") if v == "name" else ("" if params.get(v) is None else str(params[v]))
            for v in TEMPLATE_VARS[kind]]


# ---------------------------------------------------------------- senders

def _configured(channel: str) -> Optional[str]:
    """None when the channel's account is set up; otherwise what is missing."""
    if channel == "whatsapp":
        missing = [v for v in ("ACOS_WHATSAPP_TOKEN", "ACOS_WHATSAPP_PHONE_NUMBER_ID") if not os.environ.get(v)]
    else:
        missing = [v for v in ("ACOS_SMS_AUTHKEY",) if not os.environ.get(v)]
    return f"{channel} is not configured ({', '.join(missing)})" if missing else None


def sms_flow(key: str, language: str) -> Optional[str]:
    """The MSG91 flow (a DLT-registered template) for a kind, or "code":
    ACOS_SMS_FLOW_<KEY>, and ACOS_SMS_FLOW_<KEY>_HI for its Hindi text."""
    base = f"ACOS_SMS_FLOW_{key.upper()}"
    return (language == "hi" and os.environ.get(base + "_HI")) or os.environ.get(base) or None


def whatsapp_template(key: str) -> str:
    return os.environ.get("ACOS_WHATSAPP_TEMPLATE_PREFIX", "academicos_") + key


def send_whatsapp(phone: str, template: str, language: str, variables: list[str], *,
                  code_button: Optional[str] = None) -> tuple[str, Optional[str], Optional[str]]:
    """(status, error, provider message id). A Cloud API template message:
    the approved `template` in English or Hindi, with the variables as its
    body parameters. An authentication template (the one-time code) also
    carries the code for its copy-code button."""
    missing = _configured("whatsapp")
    if missing:
        return "skipped", missing, None
    import requests
    version = os.environ.get("ACOS_WHATSAPP_API_VERSION", "v21.0")
    url = f"https://graph.facebook.com/{version}/{os.environ['ACOS_WHATSAPP_PHONE_NUMBER_ID']}/messages"
    components: list[dict] = [{"type": "body", "parameters": [{"type": "text", "text": _clean(v, "whatsapp")}
                                                              for v in variables]}]
    if code_button is not None:
        components.append({"type": "button", "sub_type": "url", "index": "0",
                           "parameters": [{"type": "text", "text": code_button}]})
    payload = {
        "messaging_product": "whatsapp",
        "to": phone.lstrip("+"),
        "type": "template",
        "template": {"name": template, "language": {"code": "hi" if language == "hi" else "en"},
                     "components": components},
    }
    try:
        r = requests.post(url, json=payload, timeout=10,
                          headers={"Authorization": f"Bearer {os.environ['ACOS_WHATSAPP_TOKEN']}"})
        if r.status_code >= 300:
            return "failed", f"{r.status_code} {r.text[:200]}", None
        ids = (r.json() or {}).get("messages") or [{}]
        return "sent", None, ids[0].get("id")
    except Exception as exc:  # noqa: BLE001 - recorded on the delivery and retried
        return "failed", str(exc)[:300], None


def send_sms(phone: str, flow_id: Optional[str], variables: dict[str, str]) -> tuple[str, Optional[str], Optional[str]]:
    """(status, error, provider request id). MSG91's v5 flow API: the
    DLT-registered flow, whose ##name## variables are the keys given."""
    missing = _configured("sms")
    if missing:
        return "skipped", missing, None
    if not flow_id:
        return "skipped", "no SMS template registered for this notice", None
    import requests
    payload = {"template_id": flow_id, "short_url": "0",
               "recipients": [{"mobiles": phone.lstrip("+"),
                               **{k: _clean(v, "sms") for k, v in variables.items()}}]}
    try:
        r = requests.post("https://control.msg91.com/api/v5/flow", json=payload, timeout=10,
                          headers={"authkey": os.environ["ACOS_SMS_AUTHKEY"], "accept": "application/json"})
        data = r.json() if r.content else {}
        if r.status_code >= 300 or (isinstance(data, dict) and data.get("type") == "error"):
            return "failed", f"{r.status_code} {str(data)[:200]}", None
        return "sent", None, (data.get("message") if isinstance(data, dict) else None)
    except Exception as exc:  # noqa: BLE001
        return "failed", str(exc)[:300], None


def _code_hash(user_id: str, phone: str, code: str) -> str:
    return hashlib.sha256(f"{user_id}|{phone}|{code}".encode()).hexdigest()


# ---------------------------------------------------------------- the store

class MessagingMixin:
    """Mixed into NotificationsMixin (operations store). ValueError is the
    route's 422."""

    # The person's name, for a template's first variable; set by the
    # operations routes, like email_for.
    name_for: Optional[Callable[[str], Optional[str]]] = None

    def contact_for(self, user_id: str) -> Optional[dict[str, Any]]:
        return self._fetchone("SELECT * FROM contact_numbers WHERE user_id=?", (user_id,))

    def is_verified(self, user_id: str) -> bool:
        r = self._fetchone("SELECT v.verified_at FROM contact_verifications v JOIN contact_numbers c "
                           "ON c.user_id = v.user_id AND c.phone = v.phone WHERE v.user_id=?", (user_id,))
        return bool(r and r["verified_at"])

    def _skip_waiting(self, user_id: str, why: str, channel: Optional[str] = None) -> None:
        self._exec("UPDATE message_outbox SET status='skipped', last_error=?, updated_at=? WHERE user_id=? "
                   "AND status IN ('pending','deferred','failed')" + (" AND channel=?" if channel else ""),
                   (why, _iso(datetime.now(timezone.utc)), user_id) + ((channel,) if channel else ()))

    def set_contact(self, user_id: str, *, phone: Optional[str], sms_ok: bool,
                    whatsapp_ok: bool) -> tuple[Optional[dict], Optional[dict]]:
        """Set a person's number and consent, or remove it. Returns (before,
        after). With no channel ticked the number is not kept -- nothing
        would use it -- and removing it withdraws both. A changed number is
        unconfirmed until its code comes back."""
        before = self.contact_for(user_id)
        if phone is None or not (sms_ok or whatsapp_ok):
            with self._conn_lock:
                self._exec("DELETE FROM contact_numbers WHERE user_id=?", (user_id,))
                # The number goes; the day's code count stays, so removing and
                # re-adding a number does not reset the limit.
                self._exec("UPDATE contact_verifications SET phone='', verified_at=NULL, code_hash=NULL, "
                           "code_expires=NULL WHERE user_id=?", (user_id,))
                # Anything still waiting to go to that number goes nowhere now.
                self._skip_waiting(user_id, "consent withdrawn")
            self._commit()
            return before, None
        number = normalize_mobile(phone)
        with self._conn_lock:
            self._exec("INSERT INTO contact_numbers (user_id, phone, sms_ok, whatsapp_ok, updated_at) "
                       "VALUES (?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET phone=excluded.phone, "
                       "sms_ok=excluded.sms_ok, whatsapp_ok=excluded.whatsapp_ok, updated_at=excluded.updated_at",
                       (user_id, number, int(sms_ok), int(whatsapp_ok), _iso(datetime.now(timezone.utc))))
            for ch, ok in (("sms", sms_ok), ("whatsapp", whatsapp_ok)):
                if not ok:
                    self._skip_waiting(user_id, "consent withdrawn", ch)
        self._commit()
        return before, self.contact_for(user_id)

    # ---------------- confirming the number ----------------

    def send_contact_code(self, user_id: str, now: Optional[datetime] = None) -> tuple[Optional[str], Optional[str]]:
        """Send a one-time code to the person's unconfirmed number, on a
        channel they ticked (WhatsApp first). Returns (the channel it went
        on, None) or (None, why not, in words for the person). At most one
        code a minute and five a day, so the route cannot be used to flood a
        number or run up the school's bill."""
        now = now or datetime.now(timezone.utc)
        contact = self.contact_for(user_id)
        if contact is None:
            return None, "add your number first"
        if self.is_verified(user_id):
            return None, None
        # Counted per person, not per number: changing the number does not
        # reset the limits.
        v = self._fetchone("SELECT * FROM contact_verifications WHERE user_id=?", (user_id,))
        if v and v["last_sent_at"] and now - datetime.fromisoformat(v["last_sent_at"]) < CODE_COOLDOWN:
            return None, "a code was sent less than a minute ago: use it, or ask again in a minute"
        today = now.astimezone(_IST).date().isoformat()
        sends = v["sends_on_day"] if v and v["sent_on"] == today else 0
        if sends >= CODES_PER_DAY:
            return None, "five codes have been sent today: try again tomorrow"
        channel = next((ch for ch in ("whatsapp", "sms") if contact[f"{ch}_ok"] and _configured(ch) is None
                        and (ch == "whatsapp" or sms_flow("code", "en"))), None)
        if channel is None:
            return None, ("the school has not switched on the channel you ticked yet: your number is kept, "
                          "and a code comes to it once it does")
        code = f"{secrets.randbelow(10 ** 6):06d}"
        with self._conn_lock:
            self._exec("INSERT INTO contact_verifications (user_id, phone, code_hash, code_expires, code_attempts, "
                       "last_sent_at, sent_on, sends_on_day) VALUES (?,?,?,?,0,?,?,?) ON CONFLICT(user_id) DO UPDATE "
                       "SET phone=excluded.phone, verified_at=NULL, code_hash=excluded.code_hash, "
                       "code_expires=excluded.code_expires, code_attempts=0, last_sent_at=excluded.last_sent_at, "
                       "sent_on=excluded.sent_on, sends_on_day=excluded.sends_on_day",
                       (user_id, contact["phone"], _code_hash(user_id, contact["phone"], code), _iso(now + CODE_TTL),
                        _iso(now), today, sends + 1))
        self._commit()
        language = self.settings_for(user_id)["language"]
        if channel == "whatsapp":
            status, err, _ = send_whatsapp(contact["phone"], whatsapp_template("code"), language, [code],
                                           code_button=code)
        else:
            status, err, _ = send_sms(contact["phone"], sms_flow("code", language), {"code": code})
        if status != "sent":
            logger.warning("confirmation code for %s not sent on %s: %s", user_id, channel, err)
            return None, "the code could not be sent just now: try again in a minute"
        return channel, None

    def verify_contact_code(self, user_id: str, code: str, now: Optional[datetime] = None) -> None:
        """Confirm the number with the code sent to it. ValueError, in words
        for the person, when it is not right."""
        now = now or datetime.now(timezone.utc)
        contact = self.contact_for(user_id)
        if contact is None:
            raise ValueError("add your number first")
        if self.is_verified(user_id):
            return
        v = self._fetchone("SELECT * FROM contact_verifications WHERE user_id=?", (user_id,))
        if v is None or v["phone"] != contact["phone"] or not v["code_hash"]:
            raise ValueError("ask for a code first")
        if v["code_attempts"] >= CODE_TRIES:
            raise ValueError("too many wrong codes: ask for a new one")
        if now > datetime.fromisoformat(v["code_expires"]):
            raise ValueError("that code has expired: ask for a new one")
        if not hmac.compare_digest(_code_hash(user_id, contact["phone"], "".join(code.split())), v["code_hash"]):
            self._exec("UPDATE contact_verifications SET code_attempts=code_attempts+1 WHERE user_id=?", (user_id,))
            self._commit()
            left = CODE_TRIES - v["code_attempts"] - 1
            raise ValueError("that code is not right: " + (f"{left} tries left" if left else "ask for a new one"))
        self._exec("UPDATE contact_verifications SET verified_at=?, code_hash=NULL, code_expires=NULL "
                   "WHERE user_id=?", (_iso(now), user_id))
        self._commit()

    # ---------------- queueing ----------------

    def _first_name(self, user_id: str) -> str:
        try:
            full = self.name_for(user_id) if self.name_for else None
        except Exception:  # noqa: BLE001 - a name is a courtesy; the notice still goes
            full = None
        return (full or "").split(" ")[0]

    def _queue_messages(self, notification_id: str, school_id: str, user_id: str, kind: str,
                        params: dict[str, Any], *, now: datetime) -> None:
        """Called by notify() inside its lock: a message per channel for the
        notification's recipient and, for a student's kinds, for each parent
        actively linked to them in this school -- each by their own consent,
        confirmed number, push choice, digest and quiet hours. Executes
        only; notify() commits."""
        if kind not in MESSAGE_KINDS:
            return
        targets = [(user_id, user_id)]
        if kind in GUARDIAN_KINDS:
            targets += [(g.parent_id, user_id) for g in self.guardians_of(user_id) if g.school_id == school_id]
        names: dict[str, str] = {}    # the name is a users-store call: once per notice, not per parent
        for to, about in targets:
            self._queue_for(notification_id, to, about, kind, params, now, names)

    def _queue_for(self, notification_id: str, to: str, about: str, kind: str, params: dict[str, Any],
                   now: datetime, names: dict[str, str]) -> None:
        from .notifications import DIGEST_EXEMPT, IST, in_quiet_hours
        contact = self.contact_for(to)
        if contact is None or not self.is_verified(to) or not self.channel_enabled(to, kind, "push"):
            return
        s = self.settings_for(to)
        if s.get("digest_at") and kind not in DIGEST_EXEMPT:
            return
        quiet = in_quiet_hours(now.astimezone(IST), s["quiet_start"], s["quiet_end"])
        if about not in names:
            names[about] = self._first_name(about)
        variables = template_vars(kind, params, names[about])
        dedupe = hashlib.sha256(json.dumps([kind, variables]).encode()).hexdigest()[:24]
        from ..curriculum.store import new_id
        for ch in MESSAGE_CHANNELS:
            if not contact[f"{ch}_ok"]:
                continue
            # The same notice to the same person within a day goes once (a
            # holiday is notified once per lesson plan it moves).
            if self._fetchone("SELECT 1 FROM message_outbox WHERE user_id=? AND channel=? AND dedupe=? "
                              "AND created_at>=?", (to, ch, dedupe, _iso(now - REPEAT_WINDOW))):
                continue
            self._exec("INSERT OR IGNORE INTO message_outbox (id, notification_id, user_id, about_id, channel, kind, "
                       "vars_json, dedupe, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (new_id("msg"), notification_id, to, None if about == to else about, ch, kind,
                        json.dumps(variables, ensure_ascii=False), dedupe, "deferred" if quiet else "pending",
                        _iso(now), _iso(now)))

    # ---------------- sending ----------------

    def _release_stuck(self, now: datetime) -> None:
        """A claim older than STUCK_AFTER was left by a process that died
        mid-call: a failure, and not sent again, since it may have gone."""
        with self._conn_lock:
            self._exec("UPDATE message_outbox SET status='failed', attempts=?, next_at=NULL, updated_at=?, "
                       "last_error='interrupted while sending; not sent again, as it may have gone' "
                       "WHERE status='sending' AND updated_at<?", (MAX_TRIES, _iso(now), _iso(now - STUCK_AFTER)))

    def _claim(self, row: dict, now: datetime) -> bool:
        """Take a due row for this sender, committed before the provider is
        called. False when another sender took it first."""
        with self._conn_lock:
            won = self.conn.execute("UPDATE message_outbox SET status='sending', updated_at=? WHERE id=? "
                                    "AND status=? AND attempts=?",
                                    (_iso(now), row["id"], row["status"], row["attempts"])).rowcount == 1
            self._commit()
        return won

    def _send_one(self, row: dict, language: str) -> tuple[str, Optional[str], Optional[str]]:
        contact = self.contact_for(row["user_id"])
        if contact is None or not contact[f"{row['channel']}_ok"]:
            return "skipped", "consent withdrawn", None
        if not self.is_verified(row["user_id"]):
            return "skipped", "number not confirmed", None
        variables = json.loads(row["vars_json"])
        if row["channel"] == "whatsapp":
            return send_whatsapp(contact["phone"], whatsapp_template(row["kind"]), language, variables)
        return send_sms(contact["phone"], sms_flow(row["kind"], language),
                        dict(zip(TEMPLATE_VARS[row["kind"]], variables)))

    def _deliver_messages(self, now: datetime) -> int:
        """Send due messages (pending, deferred past quiet hours, failed and
        past their wait). Each is claimed first and committed after its
        send. Returns how many went."""
        from .notifications import IST, in_quiet_hours
        self._release_stuck(now)
        rows = self._fetchall("SELECT * FROM message_outbox WHERE status IN ('pending','deferred','failed') "
                              "AND attempts<? AND (next_at IS NULL OR next_at<=?) ORDER BY created_at",
                              (MAX_TRIES, _iso(now)))
        sent = 0
        for r in rows:
            s = self.settings_for(r["user_id"])
            if in_quiet_hours(now.astimezone(IST), s["quiet_start"], s["quiet_end"]) or not self._claim(r, now):
                continue
            status, err, pid = self._send_one(r, s["language"])
            attempts = r["attempts"] + (status == "failed")
            retry = status == "failed" and attempts < MAX_TRIES
            with self._conn_lock:
                self._exec("UPDATE message_outbox SET status=?, attempts=?, last_error=?, provider_id=?, next_at=?, "
                           "updated_at=? WHERE id=?",
                           (status, attempts, err, pid, _iso(now + RETRY_AFTER[attempts - 1]) if retry else None,
                            _iso(now), r["id"]))
                self._commit()
            sent += status == "sent"
        return sent

    def message_status(self, notification_id: str, user_id: Optional[str] = None) -> dict[str, str]:
        """{channel: status} for one person's copy of a notification: its own
        recipient's, or with user_id a parent's."""
        if user_id is None:
            n = self._fetchone("SELECT user_id FROM notifications WHERE id=?", (notification_id,))
            user_id = n["user_id"] if n else ""
        return {r["channel"]: r["status"] for r in self._fetchall(
            "SELECT channel, status FROM message_outbox WHERE notification_id=? AND user_id=?",
            (notification_id, user_id))}
