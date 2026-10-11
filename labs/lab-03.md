<!-- Lab3 -->
# Lab 3 — Config split, environments & CI/CD

## Task
- Split configuration via environment variables (sandbox / production env files),
  no hardcoded secrets.
- Isolate databases for sandbox vs production.
- Security modes: `DEBUG=False` in production; no internal stacktraces shown to
  users on a 500.
- Update the README with run instructions for both environments.
- Additional task — **Variant A (CI/CD):** a pipeline that runs on PR and on
  push to `main`, running linters and the pytest suite, with the main branch
  protected by the required checks.

## What was built
- **Config split:** `app/core/config.py` selects the env file from `APP_ENV`
  (`config/.env.sandbox`, `config/.env.production`) layered over `config/.env`,
  and exposes a `debug` flag. Templates: `config/.env.sandbox.example`,
  `config/.env.production.example` (real files are git-ignored).
- **DB isolation:** separate `cyberimplant_sandbox` and `cyberimplant_prod`
  databases — created on a fresh volume by
  `config/postgres-init/01-create-databases.sql`, or on an existing one by
  `python -m scripts.init_databases`.
- **Security modes:** the catch-all handler in `app/core/errors.py` returns the
  real message when `debug` is on and a generic `problem+json` (no stacktrace)
  when off. A gated `GET /internal/demo-error` route (off by default) exists to
  demonstrate this.
- **CI/CD:** `.github/workflows/ci.yml` — parallel `lint` (ruff check + format)
  and `test` (Postgres service + pytest) jobs on `pull_request` and
  `push: main`. Branch protection in `docs/devops/main-branch-ruleset.json`
  requires a PR and the `lint` + `test` checks to pass.

## How to demo (local)
```powershell
# One script: config split, DB isolation, security modes, and the CI mirror.
./scripts/lab3_demo.ps1
```
It prepares both env files + databases, migrates each, prints the resolved
config per environment (different DB, different DEBUG), shows a 500 returning a
**detailed** body under sandbox and a **generic** body under production, then
runs ruff + pytest locally.

## You do (manual — GitHub UI)
CI only runs on GitHub, so after the branch is pushed:
1. Open a PR into `main` → confirm the `lint` and `test` checks appear and pass.
2. **Settings → Rules → Rulesets → New ruleset → Import** →
   `docs/devops/main-branch-ruleset.json` → Create. This requires a PR and makes
   `lint` / `test` required.
3. Open one deliberately-broken PR (e.g. add `assert False` to a test) → show the
   red checks and that **merge is blocked**. Capture screenshots for the defence.

## Verify
```bash
.venv/Scripts/ruff check . && .venv/Scripts/ruff format --check .
.venv/Scripts/python -m pytest        # 14 passed
```
