<!-- Lab2 -->
# Lab 2 — Users, roles & access control

## Task
- Add a users database and at least two roles (admin + regular user).
- Registration for regular users; login for all user types.
- Role-specific home pages.
- Grow the product into an MVP with real business logic (+ additional task).
- Cover authorization with unit/integration tests (+ additional task): anonymous
  → 401, good/bad login → 200/401, vertical role separation → 403, horizontal
  (IDOR) → 403.

## Design decisions
- **Auth:** stateless **JWT bearer** tokens (matches the stateless-API decision
  in the architecture) — password hashing with argon2 (`pwdlib`), tokens with
  `pyjwt`.
- **RBAC = owner model.** Regular users **own** the implants they register;
  admins (operators) publish firmware and launch rollouts. This gives a clean,
  testable mapping of every required access-control scenario onto the domain:
  - **Anonymous → 401:** any `/api/v1/...` business route without a token.
  - **Vertical → 403:** a regular user calling an admin-only action
    (publish firmware, launch rollout, admin dashboard).
  - **Horizontal / IDOR → 403:** a user reading or modifying another user's
    implant or OTA job.

## What was built
- **Model:** `User` (email, hashed password, `role` enum); `Implant` gains
  `owner_id` (FK → users). Migration `0696799b75d0_add_users_and_implant_owner`.
- **Layers:** `app/schemas/` (Pydantic I/O), `app/services/` (business logic),
  `app/core/security.py` (hash + JWT), `app/core/errors.py` (RFC-9457
  `problem+json` + typed domain errors), `app/api/deps.py`
  (`get_current_user`, `require_admin`, ownership guard).
- **Endpoints** (under `/api/v1`):
  - `auth`: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
  - `implants`: CRUD, scoped to the owner (admin sees all)
  - `firmware`: `POST` (admin only), `GET` (any authenticated user)
  - `ota`: `POST /ota/rollouts` (admin), `GET /ota/jobs`, `POST /ota/jobs/{id}/status`
  - role home pages: `GET /me/dashboard`, `GET /admin/dashboard`
- **Tests:** `tests/test_auth.py`, `tests/test_rbac.py`, `tests/test_mvp.py`
  (+ `tests/conftest.py` with an isolated `cyberimplant_test` database and
  user/token fixtures). All required scenarios covered.

## How to demo
```powershell
# Postgres up, migrations applied, server running:
docker compose up -d
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m uvicorn app.main:app

# In another shell — one script runs the whole flow + the 401/403 paths:
./scripts/lab2_demo.ps1
```
The script seeds an admin, registers two users, registers an implant, publishes
firmware, launches a rollout, views/reports jobs, then shows anonymous → 401,
vertical → 403, and IDOR → 403.

## Verify
```bash
.venv/Scripts/python -m pytest        # 14 passed
.venv/Scripts/ruff check .
```

## You do (manual)
Nothing external — just run the demo script.
