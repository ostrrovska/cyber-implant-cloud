<!-- Lab1 -->
# Labs

Per-lab task summaries and how to demo each one.

| Lab | Topic | Demo |
|-----|-------|------|
| [lab-01.md](lab-01.md) | Architecture & project scaffold | `uvicorn app.main:app` → `GET /health` |
| [lab-02.md](lab-02.md) | Users, roles & access control (RBAC, MVP, tests) | `./scripts/lab2_demo.ps1` |
| [lab-03.md](lab-03.md) | Config split, environments & CI/CD | `./scripts/lab3_demo.ps1` |

Prerequisites: Postgres up (`docker compose up -d`), deps installed
(`.venv/Scripts/pip install -r requirements-dev.txt`), migrations applied
(`.venv/Scripts/python -m alembic upgrade head`).
