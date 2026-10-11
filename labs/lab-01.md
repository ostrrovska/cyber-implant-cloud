<!-- Lab1 -->
# Lab 1 — Architecture & project scaffold

## Task
Choose a domain, design the system architecture, and build the base application
+ database skeleton.

## What was built
- **Domain:** Cyber-Implant Cloud Control Center — mass asynchronous OTA firmware
  rollout to a fleet of connected implants.
- **Architecture:** stateless FastAPI API behind a load balancer over PostgreSQL,
  with Redis / message broker / object storage called out as planned-not-built.
  Full write-up in [../docs/architecture.md](../docs/architecture.md); rendered
  diagram in [../docs/architecture-diagram.pdf](../docs/architecture-diagram.pdf).
- **Stack:** FastAPI + async SQLAlchemy 2 + Alembic (async) + PostgreSQL 16.
- **Models:** `Implant`, `FirmwareVersion`, `OtaUpdateJob` (the per-device rollout
  unit). Initial Alembic migration verified against a live container.
- **Toolchain:** Ruff (lint + format), pre-commit hooks, pytest, docker-compose
  for local Postgres (host port 5433).

## Endpoints
- `GET /health` — liveness.
- `GET /health/ready` — readiness (checks the database).

## Verify
```bash
docker compose up -d
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --reload   # GET /health -> 200
```
