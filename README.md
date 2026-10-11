# Cyber-Implant Cloud Control Center

Cloud backend for managing a fleet of connected cyber-implants and pushing
Over-The-Air (OTA) firmware updates to them. The system's defining load
scenario is a **mass asynchronous OTA rollout**: one firmware release fanning
out, concurrently, to millions of devices at once.

## Domain choice

This domain was chosen because it stays relevant for the whole course: it
naturally requires everything a high-load architecture course covers —
asynchronous fan-out to a huge device fleet, staged/canary rollouts, caching
of read-heavy firmware manifests, load-balanced stateless API nodes, a
relational store for transactional rollout bookkeeping, and (later) a message
broker for background job dispatch. See
[docs/context/01-domain-choice.md](docs/context/01-domain-choice.md) for the
full rationale (local file, not tracked in git — see below).

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full component
breakdown and data flow, and [docs/architecture-diagram.pdf](docs/architecture-diagram.pdf)
for the rendered architecture diagram.

## Project layout

```
app/            FastAPI application (core config, API routes, auth, services, ORM models)
migrations/     Alembic migrations (async)
config/         Environment templates and Postgres init scripts
docs/           Architecture docs and DevOps/CI notes
labs/           Per-lab task summaries and how to demo each one
scripts/        Seed and per-lab demo scripts (PowerShell + Python)
tests/          Pytest test suite
.github/        CI pipeline (GitHub Actions)
docker-compose.yml   Local PostgreSQL for development
```

## Local context files

Design decisions and their reasoning are tracked in `CONTEXT.md` and
`docs/context/*.md`. These are intentionally **git-ignored** — they are
working notes for whoever develops this project, not part of the graded
deliverables, so they stay on disk locally rather than in the repository.

## Getting started

1. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   .venv/Scripts/pip install -r requirements-dev.txt
   ```

2. **Start PostgreSQL:**
   ```bash
   docker compose up -d
   ```

3. **Configure environment:**
   ```bash
   cp config/.env.example config/.env
   ```

4. **Apply migrations:**
   ```bash
   .venv/Scripts/python -m alembic upgrade head
   ```

5. **Run the app:**
   ```bash
   .venv/Scripts/python -m uvicorn app.main:app --reload
   ```
   API docs available at `http://localhost:8000/docs`. Liveness at `/health`,
   readiness (checks DB connectivity) at `/health/ready`.

## Environments: sandbox vs production (Lab 3)

Configuration is split per environment. The app selects its env file by the
`APP_ENV` variable, layered over the shared `config/.env`:

| `APP_ENV`     | Env file                    | DEBUG | Database                 |
|---------------|-----------------------------|-------|--------------------------|
| `development` | `config/.env`               | true  | `cyberimplant`           |
| `sandbox`     | `config/.env.sandbox`       | true  | `cyberimplant_sandbox`   |
| `production`  | `config/.env.production`    | false | `cyberimplant_prod`      |

The sandbox and production databases are isolated, so test data never reaches
production. In production, `DEBUG=false` means an unhandled error returns a
generic `application/problem+json` body with no stacktrace; development and
sandbox surface the real message.

```bash
# Prepare the two env files and databases
cp config/.env.sandbox.example config/.env.sandbox
cp config/.env.production.example config/.env.production
.venv/Scripts/python -m scripts.init_databases     # creates both databases

# Run migrations against a chosen environment
APP_ENV=sandbox    .venv/Scripts/python -m alembic upgrade head
APP_ENV=production .venv/Scripts/python -m alembic upgrade head

# Run the app against a chosen environment
APP_ENV=production .venv/Scripts/python -m uvicorn app.main:app
```

On Windows PowerShell, set the variable first: `$env:APP_ENV = "production"`.

## Demo scripts

One script per lab walks the whole feature set end to end (see [labs/](labs/)):

```powershell
./scripts/lab2_demo.ps1    # users, roles, RBAC, OTA MVP (incl. 401/403 paths)
./scripts/lab3_demo.ps1    # config split, DB isolation, security modes, CI mirror
```

## Code quality

[Ruff](https://docs.astral.sh/ruff/) handles both linting and formatting:
```bash
.venv/Scripts/ruff check .
.venv/Scripts/ruff format .
```

## Pre-commit hooks

Pre-commit runs Ruff (lint + format) and basic hygiene checks
(trailing whitespace, end-of-file, YAML/TOML validity, large files, merge
conflict markers) before every commit, blocking commits that fail them.

```bash
.venv/Scripts/pre-commit install     # one-time, registers the git hook
.venv/Scripts/pre-commit run --all-files
```

## Tests

```bash
.venv/Scripts/python -m pytest
```
