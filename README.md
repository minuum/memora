<<<<<<< HEAD
# memora
=======
# Memora

Stateful AI workspace memory CLI.

- L1: Core memory (always included)
- L2: Session memory (crash-safe + auto-summary)
- L3: Long-term memory (jsonl search + Supabase sync)
- SSH recovery via tmux

## Quick Start (local repo)

```bash
cd ai-workspace
./memora init --session-id 2026-02-20-dev1
./memora run --user-input "다음 작업 제안" --dry-run
./memora tmux-start
./memora resume
```

`vla` is kept as a compatibility alias:

```bash
./vla show
```

## Install As Package

### Option A: pipx (recommended)

```bash
cd ai-workspace
pipx install .
memora --help
```

### Option B: pip

```bash
cd ai-workspace
python -m pip install .
memora --help
```

By default, runtime data is saved to `./.memora` from your current working directory.
You can override with:

```bash
export MEMORA_HOME=/path/to/memora-home
```

## Supabase Sync

1. Apply SQL schema: `sql/supabase_schema.sql`
2. Set env vars:

```bash
export SUPABASE_URL="https://<project>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service_role_key>"
export SUPABASE_SERVER_ID="dev-server-01"
```

3. Sync:

```bash
memora supabase-push-session
memora supabase-push-longterm
memora supabase-pull-session --session-id 2026-02-20-dev1 --server-id dev-server-01
```

## GitHub Repo Split (from current monorepo)

If you want `ai-workspace` as an independent `memora` repository:

```bash
# from monorepo root
git subtree split --prefix=ai-workspace -b memora-split

# create new empty GitHub repo first, then:
git push <new-memora-remote-url> memora-split:main
```

Or just copy `ai-workspace/` to a new directory and run:

```bash
cd memora
git init
git add .
git commit -m "feat: initial memora package"
git remote add origin <new-memora-remote-url>
git push -u origin main
```

## Main Commands

```bash
memora init --session-id <id>
memora run --user-input "..." --cmd "codex"
memora show
memora build --user-input "..."
memora tmux-start
memora resume --attach
memora supabase-status
memora where
```
>>>>>>> d98cf4d (feat: bootstrap memora package and cli)
