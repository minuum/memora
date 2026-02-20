"""Memora CLI."""

from __future__ import annotations

import argparse
import json
import subprocess

from .memory_manager import build_memory_block
from .session_manager import add_message, init_session, load_session
from .supabase_sync import pull_longterm, pull_session, push_longterm, supabase_status, upsert_session
from .tmux_manager import (
    session_to_tmux_name,
    tmux_attach_command,
    tmux_available,
    tmux_has_session,
    tmux_list_sessions,
    tmux_new_session,
)
from .workspace import workspace_root


def build_prompt(user_input: str) -> str:
    return f"{build_memory_block(user_input=user_input)}\n\n### USER REQUEST\n{user_input}"


def run_external(prompt: str, cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, input=prompt, text=True, shell=True, capture_output=True, check=False)
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def cmd_init(args: argparse.Namespace) -> int:
    print(json.dumps(init_session(session_id=args.session_id, overwrite=args.overwrite), ensure_ascii=False, indent=2))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    print(json.dumps(add_message(role=args.role, content=args.content), ensure_ascii=False, indent=2))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    del args
    print(json.dumps(load_session(), ensure_ascii=False, indent=2))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    print(build_prompt(user_input=args.user_input))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    add_message(role="user", content=args.user_input)
    prompt = build_prompt(user_input=args.user_input)

    if args.dry_run:
        print(prompt)
        return 0

    code, stdout, stderr = run_external(prompt=prompt, cmd=args.cmd)
    output = stdout or stderr or "(empty response)"
    add_message(role="assistant", content=output)
    print(output)
    return code


def _ensure_tmux_or_fail() -> int | None:
    if tmux_available():
        return None
    print("tmux is not installed or not available in PATH.")
    return 1


def cmd_tmux_start(args: argparse.Namespace) -> int:
    missing = _ensure_tmux_or_fail()
    if missing is not None:
        return missing

    session = load_session()
    tmux_name = session_to_tmux_name(session.get("session_id", "default"))
    ok, message = tmux_new_session(tmux_name=tmux_name, command=args.command)
    if not ok:
        print(message)
        return 1
    print(message)
    print(f"attach: {tmux_attach_command(tmux_name)}")
    return 0


def cmd_tmux_status(args: argparse.Namespace) -> int:
    missing = _ensure_tmux_or_fail()
    if missing is not None:
        return missing

    session = load_session()
    tmux_name = session_to_tmux_name(session.get("session_id", "default"))
    payload = {
        "workspace": str(workspace_root()),
        "session_id": session.get("session_id", "default"),
        "tmux_name": tmux_name,
        "exists": tmux_has_session(tmux_name),
        "attach_command": tmux_attach_command(tmux_name),
        "available_sessions": tmux_list_sessions(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    missing = _ensure_tmux_or_fail()
    if missing is not None:
        return missing

    session = load_session()
    tmux_name = session_to_tmux_name(session.get("session_id", "default"))
    ok, message = tmux_new_session(tmux_name=tmux_name, command=args.command)
    if not ok:
        print(message)
        return 1

    attach_cmd = tmux_attach_command(tmux_name)
    print(message)
    print(f"resume: {attach_cmd}")
    if args.attach:
        proc = subprocess.run(attach_cmd, shell=True, check=False)
        return proc.returncode
    return 0


def cmd_supabase_status(args: argparse.Namespace) -> int:
    print(json.dumps(supabase_status(server_id=args.server_id), ensure_ascii=False, indent=2))
    return 0


def cmd_supabase_push_session(args: argparse.Namespace) -> int:
    print(json.dumps(upsert_session(server_id=args.server_id), ensure_ascii=False, indent=2))
    return 0


def cmd_supabase_pull_session(args: argparse.Namespace) -> int:
    payload = pull_session(session_id=args.session_id, server_id=args.server_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


def cmd_supabase_push_longterm(args: argparse.Namespace) -> int:
    print(json.dumps(push_longterm(server_id=args.server_id), ensure_ascii=False, indent=2))
    return 0


def cmd_supabase_pull_longterm(args: argparse.Namespace) -> int:
    print(json.dumps(pull_longterm(server_id=args.server_id), ensure_ascii=False, indent=2))
    return 0


def cmd_where(args: argparse.Namespace) -> int:
    del args
    print(str(workspace_root()))
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Memora: stateful AI workspace memory CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="initialize active session")
    p_init.add_argument("--session-id", default=None)
    p_init.add_argument("--overwrite", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="append message into session")
    p_add.add_argument("--role", required=True, choices=["user", "assistant", "system"])
    p_add.add_argument("--content", required=True)
    p_add.set_defaults(func=cmd_add)

    p_show = sub.add_parser("show", help="show active session")
    p_show.set_defaults(func=cmd_show)

    p_build = sub.add_parser("build", help="build prompt with memory layers")
    p_build.add_argument("--user-input", required=True)
    p_build.set_defaults(func=cmd_build)

    p_run = sub.add_parser("run", help="save request, run command, save response")
    p_run.add_argument("--user-input", required=True)
    p_run.add_argument("--cmd", default="cat", help="command that reads prompt from stdin")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_tmux_start = sub.add_parser("tmux-start", help="start detached tmux session for active session_id")
    p_tmux_start.add_argument("--command", default=None, help="optional bootstrap command in tmux")
    p_tmux_start.set_defaults(func=cmd_tmux_start)

    p_tmux_status = sub.add_parser("tmux-status", help="show tmux mapping and availability")
    p_tmux_status.set_defaults(func=cmd_tmux_status)

    p_resume = sub.add_parser("resume", help="ensure tmux session exists for current session_id")
    p_resume.add_argument("--command", default=None, help="optional bootstrap command if new session is created")
    p_resume.add_argument("--attach", action="store_true", help="attach immediately after ensuring session")
    p_resume.set_defaults(func=cmd_resume)

    p_sb_status = sub.add_parser("supabase-status", help="show Supabase connectivity and recent sessions")
    p_sb_status.add_argument("--server-id", default=None)
    p_sb_status.set_defaults(func=cmd_supabase_status)

    p_sb_push_sess = sub.add_parser("supabase-push-session", help="push active session into Supabase")
    p_sb_push_sess.add_argument("--server-id", default=None)
    p_sb_push_sess.set_defaults(func=cmd_supabase_push_session)

    p_sb_pull_sess = sub.add_parser("supabase-pull-session", help="pull session from Supabase")
    p_sb_pull_sess.add_argument("--session-id", default=None)
    p_sb_pull_sess.add_argument("--server-id", default=None)
    p_sb_pull_sess.set_defaults(func=cmd_supabase_pull_session)

    p_sb_push_lt = sub.add_parser("supabase-push-longterm", help="push long-term memory jsonl to Supabase")
    p_sb_push_lt.add_argument("--server-id", default=None)
    p_sb_push_lt.set_defaults(func=cmd_supabase_push_longterm)

    p_sb_pull_lt = sub.add_parser("supabase-pull-longterm", help="pull long-term memory from Supabase")
    p_sb_pull_lt.add_argument("--server-id", default=None)
    p_sb_pull_lt.set_defaults(func=cmd_supabase_pull_longterm)

    p_where = sub.add_parser("where", help="print active MEMORA_HOME path")
    p_where.set_defaults(func=cmd_where)

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
