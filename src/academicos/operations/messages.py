"""Teacher-parent messaging (MSG-1): one conversation per (student, parent,
staff member), with its messages, kept in the school's record.

A conversation is opened with an upsert on its unique key, so two first
messages at once (or two server instances) open one conversation
(AGENTS.md 5.5). Each side's read time is kept on the conversation; a
message after it is unread.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

MESSAGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
  id               TEXT PRIMARY KEY,
  school_id        TEXT NOT NULL,
  student_id       TEXT NOT NULL,
  parent_id        TEXT NOT NULL,
  staff_id         TEXT NOT NULL,
  created_at       TEXT NOT NULL,
  last_at          TEXT NOT NULL,
  parent_read_at   TEXT NOT NULL DEFAULT '',
  staff_read_at    TEXT NOT NULL DEFAULT '',
  UNIQUE (school_id, student_id, parent_id, staff_id)
);
CREATE INDEX IF NOT EXISTS idx_conversations_parent ON conversations(parent_id, last_at);
CREATE INDEX IF NOT EXISTS idx_conversations_staff ON conversations(staff_id, last_at);
CREATE TABLE IF NOT EXISTS conversation_messages (
  id               TEXT PRIMARY KEY,
  conversation_id  TEXT NOT NULL,
  sender_id        TEXT NOT NULL,
  body             TEXT NOT NULL,
  created_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conversation_messages ON conversation_messages(conversation_id, created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessagesMixin:
    """Added to OperationsStore."""

    def open_conversation(self, *, school_id: str, student_id: str, parent_id: str, staff_id: str) -> dict:
        now = _now()
        with self._conn_lock:
            self.conn.execute(
                "INSERT INTO conversations (id, school_id, student_id, parent_id, staff_id, created_at, last_at)"
                " VALUES (?,?,?,?,?,?,?) ON CONFLICT (school_id, student_id, parent_id, staff_id) DO NOTHING",
                (uuid.uuid4().hex, school_id, student_id, parent_id, staff_id, now, now))
            self._commit()
        return self._fetchone(
            "SELECT * FROM conversations WHERE school_id=? AND student_id=? AND parent_id=? AND staff_id=?",
            (school_id, student_id, parent_id, staff_id))

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        return self._fetchone("SELECT * FROM conversations WHERE id=?", (conversation_id,))

    def conversations_for(self, user_id: str, *, school_id: str) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM conversations WHERE school_id=? AND (parent_id=? OR staff_id=?) ORDER BY last_at DESC",
            (school_id, user_id, user_id))

    def add_message(self, conversation_id: str, *, sender_id: str, body: str) -> dict:
        now = _now()
        mid = uuid.uuid4().hex
        with self._conn_lock:
            self.conn.execute(
                "INSERT INTO conversation_messages (id, conversation_id, sender_id, body, created_at) VALUES (?,?,?,?,?)",
                (mid, conversation_id, sender_id, body, now))
            self.conn.execute("UPDATE conversations SET last_at=? WHERE id=?", (now, conversation_id))
            self._commit()
        return {"id": mid, "conversation_id": conversation_id, "sender_id": sender_id, "body": body,
                "created_at": now}

    def messages_of(self, conversation_id: str) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM conversation_messages WHERE conversation_id=? ORDER BY created_at, id", (conversation_id,))

    def last_message(self, conversation_id: str) -> Optional[dict]:
        return self._fetchone(
            "SELECT * FROM conversation_messages WHERE conversation_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
            (conversation_id,))

    def conversation_unread(self, conv: dict, user_id: str) -> int:
        since = conv["parent_read_at"] if user_id == conv["parent_id"] else conv["staff_read_at"]
        row = self._fetchone(
            "SELECT COUNT(*) AS n FROM conversation_messages WHERE conversation_id=? AND sender_id<>? AND created_at>?",
            (conv["id"], user_id, since))
        return int(row["n"]) if row else 0

    def mark_conversation_read(self, conv: dict, user_id: str) -> None:
        col = "parent_read_at" if user_id == conv["parent_id"] else "staff_read_at"
        with self._conn_lock:
            self.conn.execute(f"UPDATE conversations SET {col}=? WHERE id=?", (_now(), conv["id"]))
            self._commit()
