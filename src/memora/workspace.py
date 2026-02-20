"""Workspace path helpers for Memora."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_CORE_MEMORY = """# Master Core Memory

이 파일은 Memora 프롬프트에 항상 포함되는 핵심 메모리입니다.

- 프로젝트의 장기 목표
- 개발 철학
- 금지 규칙
- 일관되게 유지할 아키텍처 원칙
"""


def workspace_root() -> Path:
    env_home = os.environ.get("MEMORA_HOME")
    if env_home and env_home.strip():
        return Path(env_home).expanduser().resolve()
    return (Path.cwd() / ".memora").resolve()


def core_memory_path() -> Path:
    return workspace_root() / "core" / "master_memory.md"


def sessions_dir() -> Path:
    return workspace_root() / "sessions"


def archive_dir() -> Path:
    return sessions_dir() / "archive"


def active_session_path() -> Path:
    return sessions_dir() / "active_session.json"


def backup_session_path() -> Path:
    return sessions_dir() / "active_session.backup.json"


def longterm_jsonl_path() -> Path:
    return workspace_root() / "longterm" / "memory.jsonl"


def chroma_db_dir() -> Path:
    return workspace_root() / "longterm" / "chroma_db"


def ensure_workspace_layout() -> None:
    (workspace_root() / "core").mkdir(parents=True, exist_ok=True)
    archive_dir().mkdir(parents=True, exist_ok=True)
    chroma_db_dir().mkdir(parents=True, exist_ok=True)

    core_path = core_memory_path()
    if not core_path.exists():
        core_path.write_text(DEFAULT_CORE_MEMORY, encoding="utf-8")
