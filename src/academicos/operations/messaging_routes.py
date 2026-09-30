"""HTTP routes for SMS and WhatsApp consent (operations/messaging.py)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..assessment.auth_routes import get_current_user
from ..assessment.users import User
from ..curriculum.schemas import Camel
from .messaging import MESSAGE_KINDS, MESSAGE_ROLES, _configured

router = APIRouter(prefix="/api/v1")


class _Req(Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ContactRequest(_Req):
    """phone null, or neither channel ticked, removes the number."""
    phone: Optional[str] = Field(default=None, max_length=20)
    sms_ok: bool = False
    whatsapp_ok: bool = False


class VerifyRequest(_Req):
    code: str = Field(min_length=6, max_length=12)


class ContactResponse(Camel):
    phone: Optional[str] = None
    sms_ok: bool = False
    whatsapp_ok: bool = False
    # Confirmed by the code sent to it; nothing else is sent until it is.
    verified: bool = False
    # On a PUT: the channel a confirmation code just went on, or why none did.
    code_sent_via: Optional[str] = None
    code_error: Optional[str] = None
    # Whether the school's messaging is switched on at all (the owner's
    # provider accounts): the app says so rather than promising messages.
    sms_available: bool = False
    whatsapp_available: bool = False
    kinds: list[str] = []


def _store():
    from .routes import store
    return store()


def _response(user_id: str, contact: Optional[dict], *, sent_via: Optional[str] = None,
              code_error: Optional[str] = None) -> ContactResponse:
    return ContactResponse(
        phone=contact["phone"] if contact else None,
        sms_ok=bool(contact and contact["sms_ok"]), whatsapp_ok=bool(contact and contact["whatsapp_ok"]),
        verified=bool(contact) and _store().is_verified(user_id), code_sent_via=sent_via, code_error=code_error,
        sms_available=_configured("sms") is None, whatsapp_available=_configured("whatsapp") is None,
        kinds=sorted(MESSAGE_KINDS))


def _may_message(current: User) -> None:
    if current.role not in MESSAGE_ROLES:
        raise HTTPException(403, "messages about a student go to their parent's number; a student does not add one")


def _audit(action: str, current: User, details: dict) -> None:
    from ..assessment.audit_log import get_audit_log
    from ..curriculum import routes as cr
    get_audit_log(cr._cfg.data_root).append(action, actor=current.id,
                                            details={"schoolId": current.school_id, **details})


@router.get("/me/contact", response_model=ContactResponse)
def my_contact(current: User = Depends(get_current_user)) -> ContactResponse:
    """The caller's own number and consent. Nobody else can read it."""
    _may_message(current)
    return _response(current.id, _store().contact_for(current.id))


@router.put("/me/contact", response_model=ContactResponse)
def set_my_contact(req: ContactRequest, current: User = Depends(get_current_user)) -> ContactResponse:
    """Give, change or remove the caller's own number, and say per channel
    whether they want SMS and WhatsApp. A new or changed number is sent a
    one-time code (again on each PUT while unconfirmed, at most once a
    minute). The consent is audited (not the number: its last two digits,
    and whether it changed)."""
    _may_message(current)
    if req.phone is None and (req.sms_ok or req.whatsapp_ok):
        raise HTTPException(422, "give a number to receive SMS or WhatsApp")
    s = _store()
    try:
        before, after = s.set_contact(current.id, phone=req.phone, sms_ok=req.sms_ok, whatsapp_ok=req.whatsapp_ok)
    except ValueError as e:
        raise HTTPException(422, str(e))

    def shape(c):
        return None if c is None else {"phoneEnding": c["phone"][-2:], "sms": bool(c["sms_ok"]),
                                       "whatsapp": bool(c["whatsapp_ok"])}
    changed = (before or {}).get("phone") != (after or {}).get("phone")
    if shape(before) != shape(after) or changed:
        _audit("message_consent_set", current,
               {"before": shape(before), "after": shape(after), "numberChanged": changed})
    sent_via = code_error = None
    if after is not None and not s.is_verified(current.id):
        sent_via, code_error = s.send_contact_code(current.id)
    return _response(current.id, after, sent_via=sent_via, code_error=code_error)


@router.post("/me/contact/verify", response_model=ContactResponse)
def verify_my_contact(req: VerifyRequest, current: User = Depends(get_current_user)) -> ContactResponse:
    """Confirm the caller's number with the code sent to it. Five wrong
    tries end a code; a code lasts ten minutes."""
    _may_message(current)
    s = _store()
    was = s.is_verified(current.id)
    try:
        s.verify_contact_code(current.id, req.code)
    except ValueError as e:
        raise HTTPException(422, str(e))
    contact = s.contact_for(current.id)
    if not was:
        _audit("message_number_verified", current, {"phoneEnding": contact["phone"][-2:]})
    return _response(current.id, contact)
