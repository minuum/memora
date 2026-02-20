"""Supabase sync helpers for session and long-term memory."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from session_manager import load_session, save_session

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
LONGTERM_JSONL_PATH = WORKSPACE_ROOT / "longterm" / "memory.jsonl"


@dataclass
class SupabaseConfig:
    url: str
    service_key: str
    schema: str
    server_id: str


def _read_env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is not None and value.strip():
        return value.strip()
    return default


def load_config(server_id: str | None = None) -> SupabaseConfig:
    url = _read_env("SUPABASE_URL")
    service_key = _read_env("SUPABASE_SERVICE_ROLE_KEY")
    schema = _read_env("SUPABASE_SCHEMA", "public") or "public"
    resolved_server_id = server_id or _read_env("SUPABASE_SERVER_ID", socket.gethostname())

    missing: list[str] = []
    if not url:
        missing.append("SUPABASE_URL")
    if not service_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        keys = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {keys}")

    return SupabaseConfig(url=url.rstrip("/"), service_key=service_key, schema=schema, server_id=resolved_server_id)


def _request_json(
    cfg: SupabaseConfig,
    method: str,
    path: str,
    query: dict[str, str] | None = None,
    payload: Any | None = None,
) -> Any:
    query_part = ""
    if query:
        query_part = "?" + urllib.parse.urlencode(query, doseq=True)

    url = f"{cfg.url}{path}{query_part}"
    data: bytes | None = None
    headers = {
        "apikey": cfg.service_key,
        "Authorization": f"Bearer {cfg.service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }

    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase request failed ({exc.code}): {raw}") from exc


def upsert_session(server_id: str | None = None) -> dict[str, Any]:
    cfg = load_config(server_id=server_id)
    session = load_session()

    row = {
        "server_id": cfg.server_id,
        "session_id": session.get("session_id"),
        "last_updated": session.get("last_updated"),
        "summary": session.get("summary", ""),
        "conversation": session.get("conversation", []),
        "snapshot": session,
    }

    result = _request_json(
        cfg,
        method="POST",
        path="/rest/v1/ai_sessions",
        query={"on_conflict": "server_id,session_id"},
        payload=[row],
    )
    return {"ok": True, "server_id": cfg.server_id, "session_id": row["session_id"], "result": result}


def pull_session(session_id: str | None = None, server_id: str | None = None) -> dict[str, Any]:
    cfg = load_config(server_id=server_id)
    local = load_session()
    resolved_session_id = session_id or local.get("session_id")

    query = {
        "server_id": f"eq.{cfg.server_id}",
        "session_id": f"eq.{resolved_session_id}",
        "select": "session_id,last_updated,summary,conversation,snapshot",
        "limit": "1",
    }
    rows = _request_json(cfg, method="GET", path="/rest/v1/ai_sessions", query=query)
    if not rows:
        return {
            "ok": False,
            "reason": "not_found",
            "server_id": cfg.server_id,
            "session_id": resolved_session_id,
        }

    row = rows[0]
    snapshot = row.get("snapshot") or {}
    restored = {
        "session_id": row.get("session_id", resolved_session_id),
        "last_updated": row.get("last_updated", local.get("last_updated")),
        "summary": row.get("summary", ""),
        "conversation": row.get("conversation", []),
    }

    if isinstance(snapshot, dict):
        restored.update({k: v for k, v in snapshot.items() if k not in {"session_id", "summary", "conversation", "last_updated"}})

    save_session(restored)
    return {"ok": True, "server_id": cfg.server_id, "session_id": restored["session_id"]}


def _load_longterm_rows() -> list[dict[str, Any]]:
    if not LONGTERM_JSONL_PATH.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in LONGTERM_JSONL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        text = str(obj.get("text", "")).strip()
        if not text:
            continue

        metadata = obj.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"value": metadata}

        content_hash = sha256(text.encode("utf-8")).hexdigest()
        rows.append({"text": text, "metadata": metadata, "content_hash": content_hash})
    return rows


def push_longterm(server_id: str | None = None) -> dict[str, Any]:
    cfg = load_config(server_id=server_id)
    rows = _load_longterm_rows()

    payload = [
        {
            "server_id": cfg.server_id,
            "content_hash": row["content_hash"],
            "text": row["text"],
            "metadata": row["metadata"],
        }
        for row in rows
    ]

    if payload:
        _request_json(
            cfg,
            method="POST",
            path="/rest/v1/ai_longterm",
            query={"on_conflict": "server_id,content_hash"},
            payload=payload,
        )

    return {"ok": True, "server_id": cfg.server_id, "rows_pushed": len(payload)}


def pull_longterm(server_id: str | None = None) -> dict[str, Any]:
    cfg = load_config(server_id=server_id)
    rows = _request_json(
        cfg,
        method="GET",
        path="/rest/v1/ai_longterm",
        query={
            "server_id": f"eq.{cfg.server_id}",
            "select": "text,metadata",
            "order": "updated_at.desc",
            "limit": "5000",
        },
    )

    LONGTERM_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_lines: list[str] = []
    for row in rows or []:
        output_lines.append(json.dumps({"text": row.get("text", ""), "metadata": row.get("metadata", {})}, ensure_ascii=False))

    LONGTERM_JSONL_PATH.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
    return {"ok": True, "server_id": cfg.server_id, "rows_pulled": len(output_lines)}


def supabase_status(server_id: str | None = None) -> dict[str, Any]:
    cfg = load_config(server_id=server_id)
    rows = _request_json(
        cfg,
        method="GET",
        path="/rest/v1/ai_sessions",
        query={
            "server_id": f"eq.{cfg.server_id}",
            "select": "session_id,last_updated",
            "order": "last_updated.desc",
            "limit": "5",
        },
    )
    return {
        "ok": True,
        "server_id": cfg.server_id,
        "schema": cfg.schema,
        "recent_sessions": rows or [],
    }
