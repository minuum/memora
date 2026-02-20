"""Bootstrap helpers for Memora init flows."""

from __future__ import annotations

import os
from pathlib import Path


def default_skills_root() -> Path:
    explicit = os.environ.get("MEMORA_SKILLS_DIR")
    if explicit and explicit.strip():
        return Path(explicit).expanduser().resolve()

    codex_home = os.environ.get("CODEX_HOME")
    if codex_home and codex_home.strip():
        return (Path(codex_home).expanduser().resolve() / "skills").resolve()

    return (Path.home() / ".codex" / "skills").resolve()


def _skill_header(name: str, description: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
    )


def _skill_openai_yaml(name: str, short_description: str, default_prompt: str) -> str:
    return (
        "version: 1\n"
        "interface:\n"
        f"  display_name: {name}\n"
        f"  short_description: {short_description}\n"
        f"  default_prompt: {default_prompt}\n"
    )


def _skill_catalog() -> dict[str, dict[str, object]]:
    return {
        "memora-bootstrap": {
            "description": "Install Memora globally, set PATH/alias, and verify command availability.",
            "body": (
                "# Memora Bootstrap\n\n"
                "## Workflow\n\n"
                "1. Verify local executable: `./memora/memora --help`\n"
                "2. Install globally (`pip install --user .` or symlink)\n"
                "3. Ensure PATH has `~/.local/bin`\n"
                "4. Rehash and verify: `hash -r && memora --help`\n"
            ),
            "scripts": {
                "install_global.sh": (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "ROOT_DIR=\"${1:-$(pwd)}\"\n"
                    "cd \"$ROOT_DIR\"\n"
                    "python3 -m pip install --user --no-build-isolation .\n"
                    "echo 'export PATH=\"$HOME/.local/bin:$PATH\"'\n"
                    "echo 'Run: source ~/.bashrc && hash -r && memora --help'\n"
                )
            },
            "prompt": "Help me install memora globally and verify command availability.",
        },
        "memora-ops-check": {
            "description": "Run local health checks, gitignore hygiene checks, and backup readiness checks.",
            "body": (
                "# Memora Ops Check\n\n"
                "## Workflow\n\n"
                "1. `memora where`\n"
                "2. `memora status`\n"
                "3. Verify runtime ignore rules in `.gitignore`\n"
                "4. Verify Supabase env readiness\n"
            ),
            "scripts": {
                "ops_check.sh": (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "memora where\n"
                    "memora status\n"
                    "if [ -n \"${SUPABASE_URL:-}\" ] && [ -n \"${SUPABASE_SERVICE_ROLE_KEY:-}\" ]; then\n"
                    "  echo \"OK: Supabase env configured\"\n"
                    "else\n"
                    "  echo \"WARN: Supabase env missing\"\n"
                    "fi\n"
                )
            },
            "prompt": "Run memora operational checks and summarize pass/fail results.",
        },
        "memora-session-capture": {
            "description": "Save current conversation into local Memora and optionally back up to Supabase.",
            "body": (
                "# Memora Session Capture\n\n"
                "## Workflow\n\n"
                "1. `memora start --session-id <id>`\n"
                "2. Add compact user/assistant summaries with `memora add`\n"
                "3. Confirm with `memora status`\n"
                "4. Optional backup: `memora backup push`\n"
            ),
            "scripts": {
                "capture_to_memora.sh": (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "SESSION_ID=\"${1:-dev-$(date +%F)}\"\n"
                    "USER_SUMMARY=\"${2:-사용자 요청 요약}\"\n"
                    "ASSIST_SUMMARY=\"${3:-수행 결과 요약}\"\n"
                    "memora start --session-id \"$SESSION_ID\"\n"
                    "memora add --role user --content \"$USER_SUMMARY\"\n"
                    "memora add --role assistant --content \"$ASSIST_SUMMARY\"\n"
                    "memora status\n"
                )
            },
            "prompt": "Capture this chat into memora session and show final status.",
        },
        "memora-session-recovery": {
            "description": "Recover Memora context after SSH disconnects, crashes, or migration.",
            "body": (
                "# Memora Session Recovery\n\n"
                "## Workflow\n\n"
                "1. `memora where` and `memora status`\n"
                "2. `memora resume` (or `--attach`)\n"
                "3. Verify with `memora show`\n"
                "4. Optional cloud restore: `memora backup pull --session-id <id>`\n"
            ),
            "scripts": {
                "recover_now.sh": (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "memora where\n"
                    "memora status\n"
                    "memora resume\n"
                    "memora show\n"
                )
            },
            "prompt": "Recover memora session context after a disconnect.",
        },
        "memora-supabase-backup": {
            "description": "Back up or restore Memora data with Supabase while keeping local as source of truth.",
            "body": (
                "# Memora Supabase Backup\n\n"
                "## Workflow\n\n"
                "1. Confirm local state: `memora status`\n"
                "2. Check env keys: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`\n"
                "3. Backup: `memora backup push`\n"
                "4. Restore: `memora backup pull --session-id <id>`\n"
            ),
            "scripts": {
                "backup_cycle.sh": (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "memora status\n"
                    "memora backup push\n"
                    "echo \"Backup done\"\n"
                )
            },
            "prompt": "Run a memora backup/restore readiness check for Supabase.",
        },
        "memora-start-guide": {
            "description": "Guide first-time command order for memora from start through status checks.",
            "body": (
                "# Memora Start Guide\n\n"
                "## Recommended Order\n\n"
                "1. `memora --help`\n"
                "2. `memora start --session-id dev-YYYY-MM-DD`\n"
                "3. `memora ask \"...\" --cmd \"codex\"`\n"
                "4. `memora status`\n"
                "5. `memora where`\n"
            ),
            "scripts": {
                "start_guide.sh": (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "SESSION_ID=\"${1:-dev-$(date +%F)}\"\n"
                    "memora start --session-id \"$SESSION_ID\"\n"
                    "memora status\n"
                    "memora where\n"
                )
            },
            "prompt": "Teach me the first-run memora command order.",
        },
    }


def ensure_default_skills(skills_root: Path, overwrite: bool = False) -> dict[str, object]:
    catalog = _skill_catalog()
    skills_root.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    errors: list[dict[str, str]] = []

    for name, spec in catalog.items():
        try:
            description = str(spec["description"])
            body = str(spec["body"])
            scripts = dict(spec.get("scripts", {}))
            prompt = str(spec.get("prompt", "Guide me through this memora workflow."))

            skill_dir = skills_root / name
            scripts_dir = skill_dir / "scripts"
            refs_dir = skill_dir / "references"
            agents_dir = skill_dir / "agents"
            skill_dir.mkdir(parents=True, exist_ok=True)
            scripts_dir.mkdir(parents=True, exist_ok=True)
            refs_dir.mkdir(parents=True, exist_ok=True)
            agents_dir.mkdir(parents=True, exist_ok=True)

            existed_before = (skill_dir / "SKILL.md").exists()

            files_to_write: dict[Path, str] = {
                skill_dir / "SKILL.md": _skill_header(name=name, description=description) + body,
                agents_dir / "openai.yaml": _skill_openai_yaml(
                    name=name.replace("-", " ").title(),
                    short_description=description,
                    default_prompt=prompt,
                ),
                refs_dir / "quickstart.md": (
                    f"# {name}\n\n"
                    "This skill was generated by `memora init`.\n"
                    "Edit this file with team-specific examples.\n"
                ),
            }

            for script_name, script_content in scripts.items():
                files_to_write[scripts_dir / script_name] = str(script_content)

            if existed_before and not overwrite:
                skipped.append(name)
                continue

            for file_path, content in files_to_write.items():
                file_path.write_text(content, encoding="utf-8")
                if file_path.parent.name == "scripts":
                    file_path.chmod(0o755)

            if existed_before:
                updated.append(name)
            else:
                created.append(name)
        except OSError as exc:
            errors.append({"skill": name, "error": str(exc)})

    return {
        "skills_root": str(skills_root),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "ok": not errors,
    }
