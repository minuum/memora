# Memora

로컬 기본 + Supabase 백업용 상태형 AI 메모리 CLI입니다.

- 기본 저장소: 현재 프로젝트의 `./.memora`
- 세션 복구: `tmux` 연동
- 백업/복원: Supabase (`backup push/pull`)
- 컨텍스트 계층: Core / Session / Long-term

## 기본 운영 방식 (권장)

1. 로컬에서 작업
2. 필요 시 Supabase로 백업
3. 다른 서버에서 Supabase에서 복원

즉, Supabase는 실시간 주 저장소가 아니라 백업/복구 레이어로 사용합니다.

## Quick Start

```bash
# 프로젝트 루트에서
memora start --session-id dev-2026-02-20
memora ask "현재 작업 이어서 정리해줘" --cmd "codex"
memora status
```

## 직관 명령어

```bash
memora start --session-id <id>     # 세션 시작/초기화
memora ask "..." --cmd "codex"     # 메모리 포함 질의 (추천)
memora status                      # 로컬 상태 요약
memora resume --attach             # SSH 재접속 후 tmux 복구
memora backup push                 # 로컬 -> Supabase 백업
memora backup pull --session-id <id> # Supabase -> 로컬 복원
memora where                       # 현재 MEMORA_HOME 확인
```

기존 호환 명령(`init`, `run`, `show`, `supabase-*`)도 계속 동작합니다.

## 자동 .gitignore 반영

Memora가 워크스페이스를 생성할 때, 현재 Git 저장소의 `.gitignore`에 아래 경로를 자동 추가합니다.

```gitignore
.memora/sessions/
.memora/longterm/chroma_db/
.memora/longterm/memory.jsonl
```

- 비활성화: `export MEMORA_AUTO_GITIGNORE=0`
- 커스텀 홈 사용 시: `MEMORA_HOME` 기준 상대 경로로 자동 반영

## Supabase 백업 설정

1. Supabase SQL 적용: `sql/supabase_schema.sql`
2. 환경변수 설정

```bash
export SUPABASE_URL="https://<project>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service_role_key>"
export SUPABASE_SERVER_ID="dev-server-01"
```

3. 백업/복원

```bash
memora backup push
memora backup pull --session-id dev-2026-02-20 --server-id dev-server-01
```

## 설치

```bash
cd memora
python -m pip install .
# 또는
pipx install .
```

## 저장소 분리/푸시

```bash
cd memora
git remote add origin <new-memora-remote-url>
git push -u origin main
```
