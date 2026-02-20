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
memora init --session-id dev-2026-02-20
memora ask "현재 작업 이어서 정리해줘" --cmd "codex"
memora status
```

`init`은 아래를 한 번에 수행합니다.
- 로컬 세션 초기화
- 사용자 설정 마법사(이름/이메일/LLM/Supabase)
- 실행환경 점검(tmux/Supabase/gitignore)
- Codex용 기본 memora 스킬 세트 자동 생성(`~/.codex/skills`)

## 직관 명령어

```bash
memora init --session-id <id>      # 첫 실행 권장(체크 + 스킬 부트스트랩)
memora start --session-id <id>     # 세션 시작/초기화
memora ask "..." --cmd "codex"     # 메모리 포함 질의 (추천)
memora status                      # 로컬 상태 요약
memora resume --attach             # SSH 재접속 후 tmux 복구
memora backup push                 # 로컬 -> Supabase 백업
memora backup pull --session-id <id> # Supabase -> 로컬 복원
memora where                       # 현재 MEMORA_HOME 확인
```

기존 호환 명령(`run`, `show`, `supabase-*`)도 계속 동작합니다.

`init` 옵션:

```bash
memora init --interactive                 # 설정 마법사 강제 실행
memora init --configure                   # 기존 config 있어도 다시 입력
memora init --no-with-skills            # 스킬 생성 스킵
memora init --skills-dir /path/skills   # 생성 경로 지정
memora init --overwrite-skills          # 기존 스킬 덮어쓰기
memora init --user-name minuum --user-email me@example.com
memora init --llm-cmd codex
memora init --supabase-url https://<project>.supabase.co
memora init --supabase-service-role-key <service_role_key>
```

설정은 로컬 워크스페이스의 `./.memora/config.json`에 저장되며, 이후 `ask`/`backup`에서 자동 재사용됩니다.
환경변수(`MEMORA_LLM_CMD`, `SUPABASE_*`)가 있으면 설정값보다 우선 적용됩니다.

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

## PyPI 배포

GitHub Actions 기반 배포가 포함되어 있습니다.

- `CI Package`: PR/`main`에서 빌드 + `twine check`
- `Publish TestPyPI`: 수동 실행으로 TestPyPI 업로드
- `Publish PyPI`: `v*` 태그 push 시 PyPI 업로드

사전 1회 설정:
1. PyPI/TestPyPI에 프로젝트 생성
2. 각 인덱스에서 Trusted Publisher 등록
3. Trusted Publisher의 repository/workflow를 아래와 정확히 일치:
- owner: `minuum`
- repo: `memora`
- workflow: `publish-pypi.yml` (PyPI), `publish-testpypi.yml` (TestPyPI)

릴리스 절차:

```bash
cd memora
# 버전 갱신 (pyproject.toml)
git add .
git commit -m "chore: release v0.1.1"
git tag v0.1.1
git push origin main --tags
```

설치 확인:

```bash
pipx install memora
# 또는
python -m pip install memora
memora --help
```

## 저장소 분리/푸시

```bash
cd memora
git remote add origin <new-memora-remote-url>
git push -u origin main
```
