"""Session persistence and crash-safe rotation for AI workspace."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = WORKSPACE_ROOT / "sessions"
ARCHIVE_DIR = SESSIONS_DIR / "archive"
ACTIVE_SESSION_PATH = SESSIONS_DIR / "active_session.json"
ACTIVE_BACKUP_PATH = SESSIONS_DIR / "active_session.backup.json"

MAX_CONVERSATION_TURNS = 20
KEEP_RECENT_TURNS = 10


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_session_dirs() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _default_session(session_id: str | None = None) -> dict[str, Any]:
    return {
        "session_id": session_id or datetime.now(timezone.utc).strftime("%Y-%m-%d-default"),
        "last_updated": utc_now_iso(),
        "conversation": [],
        "summary": "",
    }


def load_session() -> dict[str, Any]:
    ensure_session_dirs()
    if not ACTIVE_SESSION_PATH.exists():
        session = _default_session()
        _atomic_write_json(ACTIVE_SESSION_PATH, session)
        return session

    try:
        return json.loads(ACTIVE_SESSION_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        if ACTIVE_BACKUP_PATH.exists():
            recovered = json.loads(ACTIVE_BACKUP_PATH.read_text(encoding="utf-8"))
            _atomic_write_json(ACTIVE_SESSION_PATH, recovered)
            return recovered

        session = _default_session()
        _atomic_write_json(ACTIVE_SESSION_PATH, session)
        return session


def save_session(session: dict[str, Any]) -> None:
    ensure_session_dirs()
    session["last_updated"] = utc_now_iso()

    if ACTIVE_SESSION_PATH.exists():
        ACTIVE_BACKUP_PATH.write_text(ACTIVE_SESSION_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    _atomic_write_json(ACTIVE_SESSION_PATH, session)


def _compress_messages(messages: list[dict[str, str]], max_chars_per_item: int = 220) -> str:
    lines: list[str] = []
    for item in messages:
        role = item.get("role", "unknown")
        content = (item.get("content", "") or "").strip().replace("\n", " ")
        if len(content) > max_chars_per_item:
            content = content[:max_chars_per_item] + "..."
        lines.append(f"- {role}: {content}")
    return "\n".join(lines)


def summarize_and_prune(session: dict[str, Any]) -> dict[str, Any]:
    conversation = session.get("conversation", [])
    if len(conversation) <= MAX_CONVERSATION_TURNS:
        return session

    old_messages = conversation[:-KEEP_RECENT_TURNS]
    recent_messages = conversation[-KEEP_RECENT_TURNS:]

    compressed = _compress_messages(old_messages)
    current_summary = (session.get("summary") or "").strip()

    if current_summary:
        session["summary"] = f"{current_summary}\n\n[Auto summary @ {utc_now_iso()}]\n{compressed}"
    else:
        session["summary"] = f"[Auto summary @ {utc_now_iso()}]\n{compressed}"

    session["conversation"] = recent_messages

    archive_file = ARCHIVE_DIR / f"{session.get('session_id', 'session')}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    _atomic_write_json(archive_file, session)

    return session


def add_message(role: str, content: str) -> dict[str, Any]:
    role = role.strip().lower()
    if role not in {"user", "assistant", "system"}:
        raise ValueError("role must be one of: user, assistant, system")

    session = load_session()
    session.setdefault("conversation", [])
    session.setdefault("summary", "")

    session["conversation"].append({"role": role, "content": content})
    session = summarize_and_prune(session)
    save_session(session)
    return session


def init_session(session_id: str | None = None, overwrite: bool = False) -> dict[str, Any]:
    ensure_session_dirs()
    if ACTIVE_SESSION_PATH.exists() and not overwrite:
        return load_session()

    session = _default_session(session_id=session_id)
    save_session(session)
    return session
