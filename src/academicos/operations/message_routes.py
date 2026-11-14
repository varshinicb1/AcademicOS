"""HTTP routes for teacher-parent messaging (MSG-1; operations/messages.py).

- A parent writes about one linked child to a member of staff who teaches
  that child's section, is its class teacher, or is the principal.
- A teacher (or the principal) writes to a linked parent of a student they
  teach (the principal: any student of the school).
- Only the two people in a conversation read or write it. Each new message
  tells the other person (`message_received`), and the conversation stays in
  the school's record: it is erased only with the student or the parent.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..assessment.auth_routes import get_current_user
from ..assessment.users import User
from ..curriculum import routes as cr
from ..curriculum.schemas import Camel
from .routes import notify_safely, store

router = APIRouter(prefix="/api/v1")

PREVIEW = 120


class _Req(Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class StartConversationRequest(_Req):
    student_id: str
    # The other person: a member of staff when a parent writes, a parent
    # when staff write.
    with_id: str
    body: str = Field(min_length=1, max_length=2000)


class SendMessageRequest(_Req):
    body: str = Field(min_length=1, max_length=2000)


class MessageResponse(Camel):
    id: str
    sender_id: str
    sender_name: str
    mine: bool
    body: str
    created_at: str


class ConversationResponse(Camel):
    id: str
    student_id: str
    student_name: str
    with_id: str
    with_name: str
    with_role: str
    last_at: str
    last_message: Optional[str] = None
    unread: int = 0


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]


class ParentContact(Camel):
    """A parent a member of staff may write to, and the child it is about."""
    student_id: str
    student_name: str
    class_name: str           # "10-B"
    parent_id: str
    parent_name: str
    relation: str             # mother, father, guardian, grandparent, other


class Contact(Camel):
    user_id: str
    name: str
    role: str                 # "class teacher", "Science teacher", "principal"


# ---------------- who may write to whom ----------------

def _section_of(student_id: str):
    cs = cr._require()
    e = cs.enrollment_for_student(student_id)
    return cs.get_section(e.section_id) if e and e.section_id else None


def teachers_of(student_id: str, school_id: str) -> list[Contact]:
    """The staff a parent may write to about this child: the class teacher,
    the section's subject teachers, and the school's principals."""
    cs, users = cr._require(), cr._require_users()
    out: dict[str, Contact] = {}
    section = _section_of(student_id)
    if section is not None:
        if section.class_teacher_id:
            u = users.get(section.class_teacher_id)
            if u and u.school_id == school_id:
                out[u.id] = Contact(user_id=u.id, name=u.name, role="class teacher")
        for a in cs.allocations_for_year(section.academic_year_id):
            if a.section_id != section.id or not a.teacher_id or a.teacher_id in out:
                continue
            u = users.get(a.teacher_id)
            subj = cs.get_subject(a.subject_id)
            if u and u.school_id == school_id:
                out[u.id] = Contact(user_id=u.id, name=u.name, role=f"{subj.name if subj else 'subject'} teacher")
    for u in users.users_for_school(school_id, role="principal"):
        out.setdefault(u.id, Contact(user_id=u.id, name=u.name, role="principal"))
    return list(out.values())


def _staff_may_reach(staff: User, student_id: str) -> bool:
    if staff.role == "principal":
        return True
    return any(c.user_id == staff.id for c in teachers_of(student_id, staff.school_id))


def _conversation(conversation_id: str, current: User) -> dict:
    conv = store().get_conversation(conversation_id)
    if conv is None or conv["school_id"] != current.school_id or current.id not in (conv["parent_id"], conv["staff_id"]):
        raise HTTPException(404, "no conversation of yours with that id")
    return conv


def _name(user_id: str) -> str:
    u = cr._require_users().get(user_id)
    return u.name if u else ""


def _summary(conv: dict, current: User) -> ConversationResponse:
    s = store()
    other = conv["staff_id"] if current.id == conv["parent_id"] else conv["parent_id"]
    u = cr._require_users().get(other)
    last = s.last_message(conv["id"])
    return ConversationResponse(
        id=conv["id"], student_id=conv["student_id"], student_name=_name(conv["student_id"]), with_id=other,
        with_name=u.name if u else "", with_role=u.role if u else "", last_at=conv["last_at"],
        last_message=(last["body"][:PREVIEW] if last else None), unread=s.conversation_unread(conv, current.id))


def _detail(conv: dict, current: User) -> ConversationDetail:
    msgs = [MessageResponse(id=m["id"], sender_id=m["sender_id"], sender_name=_name(m["sender_id"]),
                            mine=m["sender_id"] == current.id, body=m["body"], created_at=m["created_at"])
            for m in store().messages_of(conv["id"])]
    return ConversationDetail(**_summary(conv, current).model_dump(), messages=msgs)


def _send(conv: dict, current: User, body: str) -> None:
    msg = store().add_message(conv["id"], sender_id=current.id, body=body.strip())
    other = conv["staff_id"] if current.id == conv["parent_id"] else conv["parent_id"]
    notify_safely(school_id=conv["school_id"], user_ids=[other], kind="message_received",
                  params={"sender": current.name, "student": _name(conv["student_id"]), "preview": body.strip()[:PREVIEW]},
                  link=f"/school/messages/{conv['id']}",
                  # keyed on the student, so erasing the student finds it (forget.py)
                  dedupe_key=f"msg:{msg['id']}:{conv['student_id']}")


def _audit(action: str, current: User, conv: dict) -> None:
    from ..assessment.audit_log import get_audit_log
    get_audit_log(cr._cfg.data_root).append(action, actor=current.id, details={
        "schoolId": conv["school_id"], "conversationId": conv["id"], "studentId": conv["student_id"]})


# ---------------- routes ----------------

@router.get("/children/{student_id}/contacts", response_model=list[Contact])
def child_contacts(student_id: str, current: User = Depends(get_current_user)) -> list[Contact]:
    """Whom a parent may write to about this child."""
    from .guardian_routes import _my_child
    child = _my_child(student_id, current)
    return teachers_of(child.id, child.school_id)


@router.get("/message-contacts", response_model=list[ParentContact])
def message_contacts(current: User = Depends(get_current_user)) -> list[ParentContact]:
    """The parents a teacher may write to: the linked parents of students in
    the sections they are class teacher of or teach (the principal: every
    section). Sorted by class, then student."""
    if current.role not in ("teacher", "principal"):
        raise HTTPException(403, "this is the staff's list of parents; a parent writes from My children")
    cs, users, s = cr._require(), cr._require_users(), store()
    sections = []
    for y in cs.academic_years_for_school(current.school_id):
        mine = None
        if current.role == "teacher":
            mine = {a.section_id for a in cs.allocations_for_year(y.id) if a.teacher_id == current.id}
        for sec in cs.sections_for_year(y.id):
            if mine is None or sec.class_teacher_id == current.id or sec.id in mine:
                sections.append(sec)
    out: list[ParentContact] = []
    seen: set[tuple[str, str]] = set()
    for sec in sections:
        g = cs.get_grade(sec.grade_id)
        label = f"{g.number}-{sec.name}" if g else sec.name
        for e in cs.enrollments_for_section(sec.id):
            current_section = _section_of(e.student_id)
            if current_section is None or current_section.id != sec.id:
                continue          # last year's class: not theirs to write about now
            child = users.get(e.student_id)
            if child is None or child.school_id != current.school_id:
                continue
            for link in s.guardians_of(child.id):
                parent = users.get(link.parent_id)
                if parent is None or link.school_id != current.school_id or (child.id, parent.id) in seen:
                    continue
                seen.add((child.id, parent.id))
                out.append(ParentContact(student_id=child.id, student_name=child.name, class_name=label,
                                         parent_id=parent.id, parent_name=parent.name, relation=link.relation))
    return sorted(out, key=lambda c: (c.class_name, c.student_name.lower(), c.parent_name.lower()))


@router.get("/conversations", response_model=list[ConversationResponse])
def my_conversations(current: User = Depends(get_current_user)) -> list[ConversationResponse]:
    if current.role not in ("parent", "teacher", "principal"):
        raise HTTPException(403, "messages are between parents and the school's staff")
    s = store()
    return [_summary(c, current) for c in s.conversations_for(current.id, school_id=current.school_id)]


@router.post("/conversations", response_model=ConversationDetail)
def start_conversation(req: StartConversationRequest, current: User = Depends(get_current_user)) -> ConversationDetail:
    """Write the first message (or one more, if the conversation exists)."""
    users = cr._require_users()
    if current.role == "parent":
        from .guardian_routes import _my_child
        child = _my_child(req.student_id, current)
        if not any(c.user_id == req.with_id for c in teachers_of(child.id, current.school_id)):
            raise HTTPException(403, "you can write to your child's class teacher, subject teachers or the principal")
        parent_id, staff_id = current.id, req.with_id
    elif current.role in ("teacher", "principal"):
        from ..assessment.authz import require_school_owns_student
        require_school_owns_student(users, req.student_id, current)
        if not _staff_may_reach(current, req.student_id):
            raise HTTPException(403, "you can write to the parents of students you teach")
        if not store().is_guardian(req.with_id, req.student_id):
            raise HTTPException(404, "no linked parent of that student with that id")
        parent_id, staff_id = req.with_id, current.id
    else:
        raise HTTPException(403, "messages are between parents and the school's staff")
    conv = store().open_conversation(school_id=current.school_id, student_id=req.student_id, parent_id=parent_id,
                                     staff_id=staff_id)
    _send(conv, current, req.body)
    _audit("message_sent", current, conv)
    return _detail(store().get_conversation(conv["id"]), current)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def read_conversation(conversation_id: str, current: User = Depends(get_current_user)) -> ConversationDetail:
    """The whole conversation; reading it marks it read for the caller."""
    conv = _conversation(conversation_id, current)
    store().mark_conversation_read(conv, current.id)
    return _detail(store().get_conversation(conversation_id), current)


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationDetail)
def reply(conversation_id: str, req: SendMessageRequest, current: User = Depends(get_current_user)) -> ConversationDetail:
    conv = _conversation(conversation_id, current)
    # A parent whose link to the child has ended, or staff no longer
    # teaching them, can read the past but not write more.
    if current.id == conv["parent_id"] and not store().is_guardian(current.id, conv["student_id"]):
        raise HTTPException(403, "your link to this child has ended; ask the school to restore it")
    if current.id == conv["staff_id"] and not _staff_may_reach(current, conv["student_id"]):
        raise HTTPException(403, "you no longer teach this student; the class teacher can reply")
    _send(conv, current, req.body)
    _audit("message_sent", current, conv)
    store().mark_conversation_read(conv, current.id)
    return _detail(store().get_conversation(conversation_id), current)
