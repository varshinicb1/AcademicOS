"""Sign in with a one-time code by email (ROLE-2) -- for students and
parents, who should not need a password to open their homework or their
child's progress, and for principals (Phase 1 pilot, 2026-10-04), whose
password otherwise only AcademicOS can reset.

A code is six digits, lives ten minutes, allows five tries, and is stored
only as a hash. Asking for a code answers the same whether or not the email
has an account, so the route cannot be used to find out who is enrolled;
only principal, student and parent accounts are sent one (teachers use their
password, which the principal can reset). Requests are rate-limited per
client and per email, and tries per email per day, so guessing a principal's
code is not a matter of patience. Nothing is sent until the school's email
is set up (SMTP or Composio), and the route says so.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field

from ..api.rate_limit import RateLimiter, get_client_ip
from ..assessment.schemas import Camel

router = APIRouter(prefix="/api/v1/auth/code")

CODES_SCHEMA = """
CREATE TABLE IF NOT EXISTS sign_in_codes (
    email TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""
LIFETIME = timedelta(minutes=10)
MAX_ATTEMPTS = 5
ROLES = ("principal", "student", "parent")

_request_limiter = RateLimiter(max_requests=5, window_seconds=600, name="code_request")
_verify_limiter = RateLimiter(max_requests=20, window_seconds=600, name="code_verify")
# At most 30 tries a day per email: a guesser's chance is 1 in about 33,000 a
# day, where the 10-minute limit alone allows 2,880 tries a day.
_daily_verify_limiter = RateLimiter(max_requests=30, window_seconds=86400, name="code_verify_daily")


def _hash(email: str, code: str) -> str:
    return hashlib.sha256(f"{email}:{code}".encode("utf-8")).hexdigest()


class CodesMixin:
    """Added to OperationsStore."""

    def issue_code(self, email: str) -> str:
        code = f"{secrets.randbelow(10**6):06d}"
        now = datetime.now(timezone.utc)
        with self._conn_lock:
            self.conn.execute(
                "INSERT INTO sign_in_codes (email, code_hash, expires_at, attempts, created_at) VALUES (?,?,?,0,?)"
                " ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash, expires_at=excluded.expires_at,"
                " attempts=0, created_at=excluded.created_at",
                (email, _hash(email, code), (now + LIFETIME).isoformat(), now.isoformat()))
            self._commit()
        return code

    def check_code(self, email: str, code: str) -> bool:
        """True once, for the right unexpired code; every try counts.

        Each outcome is one statement, so tries at the same moment (two tabs, two instances) cannot
        both pass: the right code is claimed by deleting it, and only one DELETE gets the row back;
        a wrong one adds to the count in place. Reading the row first and writing later let two
        submissions of the right code both sign in, and wrong ones each see a count under the limit
        (security review 2026-10, ASVS V2.7.3)."""
        now = datetime.now(timezone.utc)
        with self._conn_lock:
            claimed = self.conn.execute(
                "DELETE FROM sign_in_codes WHERE email=? AND code_hash=? RETURNING expires_at",
                (email, _hash(email, code))).fetchone()
            if claimed is not None:
                self._commit()
                return datetime.fromisoformat(claimed["expires_at"]) > now
            row = self.conn.execute(
                "UPDATE sign_in_codes SET attempts=attempts+1 WHERE email=? RETURNING attempts, expires_at",
                (email,)).fetchone()
            if row is not None and (row["attempts"] >= MAX_ATTEMPTS
                                    or datetime.fromisoformat(row["expires_at"]) <= now):
                self.conn.execute("DELETE FROM sign_in_codes WHERE email=?", (email,))
            self._commit()
        return False


class CodeRequest(Camel):
    email: str = Field(min_length=3, max_length=200)


class CodeVerify(Camel):
    email: str = Field(min_length=3, max_length=200)
    code: str = Field(min_length=6, max_length=6)


def _limit(limiter: RateLimiter, request: Request, email: str) -> None:
    limiter.check(f"ip:{get_client_ip(request)}")
    limiter.check(f"email:{email}")


def _store():
    from .routes import _cfg, store
    if _cfg is None:
        raise HTTPException(503, "sign-in by code is not initialised")
    return store()


@router.post("/request")
def request_code(req: CodeRequest, request: Request) -> dict:
    """Email a sign-in code to a principal, student or parent account. The
    answer is the same whether or not the email has one."""
    from ..assessment import auth_routes, mailer
    from .notifications import send_email
    s = _store()
    email = req.email.strip().lower()
    _limit(_request_limiter, request, email)
    if not any(b.get("configured") for b in mailer.available_backends().values()):
        raise HTTPException(503, "sign-in by code needs the school's email to be set up; use your password for now")
    user = auth_routes._require().get_by_email(email)
    if user is not None and user.role in ROLES:
        code = s.issue_code(email)
        send_email(email, f"{code} is your AcademicOS sign-in code",
                   f"Your sign-in code is {code}. It works once, for 10 minutes.\n\n"
                   "If you did not ask for it, ignore this email: nobody can sign in without the code.")
    return {"detail": "If this email has an account that can sign in with a code, the code is on its way. "
                      "It works for 10 minutes."}


@router.post("/verify")
def verify_code(req: CodeVerify, request: Request):
    """Sign in with the emailed code: the same answer as a password sign-in."""
    from ..assessment import auth_routes
    s = _store()
    email = req.email.strip().lower()
    _limit(_verify_limiter, request, email)
    _daily_verify_limiter.check(f"email:{email}")
    user = auth_routes._require().get_by_email(email)
    if user is None or user.role not in ROLES or not s.check_code(email, req.code.strip()):
        raise HTTPException(401, "that code is not right or has expired; ask for a new one")
    token = auth_routes._require().create_session(user.id)
    return auth_routes.AuthResponse(user=auth_routes._to_response(user), token=token)
