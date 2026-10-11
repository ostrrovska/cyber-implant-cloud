# System Architecture

## Overview

The Cyber-Implant Cloud Control Center is the backend platform that manages a fleet of
connected cyber-implants (neural interfaces, prosthetic controllers, and similar
long-lived embedded devices) and pushes Over-The-Air (OTA) firmware updates to them.
The defining load scenario is a **mass asynchronous OTA rollout**: a single firmware
release fanning out, concurrently, to millions of devices, each polling, downloading,
reporting status, and retrying independently.

This document describes the components of the system and how they interact. It marks
clearly what Lab 1 implements versus what later labs are expected to add.

## Components

### Clients

- **Implant devices** — the cyber-implants themselves. Each periodically polls the
  cloud for a pending OTA job, downloads the firmware artifact, applies it, and
  reports success/failure back. Devices are numerous, intermittently connected, and
  cannot be assumed to all be online at once.
- **Operator dashboard** — a web client used by engineers/operators to publish new
  firmware versions, launch rollout campaigns (e.g. canary a version to 1% of a
  fleet before a full rollout), and monitor progress.

### Load balancer

Sits in front of the API layer and distributes incoming HTTP traffic (from both
implants and the operator dashboard) across multiple stateless API instances. Because
OTA polling from millions of devices is bursty and highly concurrent, the API layer
must scale horizontally behind the balancer rather than vertically.

### API layer (FastAPI, implemented in Lab 1)

A stateless, asynchronous FastAPI application. Statelessness is what lets the load
balancer freely distribute requests across any number of running instances — no
instance holds device or session state in memory. Each instance talks to the shared
PostgreSQL database (and, later, the shared cache) for anything it needs to persist
or look up.

Responsibilities:
- Register/authenticate implants and record heartbeats.
- Serve pending OTA jobs to polling devices.
- Accept firmware upload/publish requests and rollout-campaign commands from the
  operator dashboard.
- Track per-device job status (pending → in progress → succeeded/failed).

### Relational database — PostgreSQL (implemented in Lab 1)

The system of record. Lab 1 models three core entities:
- `implants` — device identity, current firmware version, status, last-seen time.
- `firmware_versions` — published firmware builds (version, checksum, artifact
  location, release notes).
- `ota_update_jobs` — one row per (implant, firmware version) rollout unit, carrying
  status, retry count, and timestamps. This is the unit of work that a mass rollout
  fans out into millions of.

A relational database is the right fit here because rollout state is exactly the
kind of consistent, transactional bookkeeping (has this specific device received
this specific update, and did it succeed?) that benefits from foreign keys, unique
constraints, and transactions — not eventual consistency.

### Planned services (not implemented yet — future labs)

These are called out in the design because the domain requires them at scale, but
Lab 1 intentionally ships only the foundation above:

- **Cache layer (Redis)** — will cache firmware manifests and device state that is
  read far more often than it changes (e.g. "what's the latest firmware for model
  X?"), and will back rate limiting so millions of polling devices cannot overwhelm
  the database with identical reads.
- **Message broker + async workers (e.g. RabbitMQ/Kafka + Celery or a task queue)**
  — mass OTA fan-out (turning "roll out version 2.3 to 2,000,000 devices" into
  2,000,000 `ota_update_jobs` rows and dispatching them) is a background, retryable,
  high-throughput job — not something to do synchronously inside an HTTP request.
- **Object storage (S3-compatible)** — firmware binaries themselves are large blobs;
  they belong in object storage with the database holding only a reference
  (`artifact_url` + checksum), not in the relational database.

## Data / control flow

**Publishing a firmware version:** operator dashboard → API → firmware binary
pushed to object storage (future) → `firmware_versions` row created in PostgreSQL.

**Launching a mass rollout:** operator dashboard → API → (future) a fan-out worker
creates one `ota_update_jobs` row per targeted implant, queued via the message
broker. In Lab 1's synchronous foundation, the same rows can be created directly by
the API for smaller batches.

**Device update cycle:** implant polls `GET /implants/{id}/jobs` (future endpoint,
built on the Lab 1 schema) → API reads the implant's pending job from PostgreSQL
(cache-accelerated in the future) → implant downloads the firmware artifact →
implant reports status back → API updates the `ota_update_jobs` row.

**Horizontal scaling path:** load balancer → N stateless FastAPI instances → shared
PostgreSQL (+ future Redis, broker, object storage) — every instance is
interchangeable, so the fleet-facing tier scales by adding instances behind the
balancer, not by growing a single process.

See [architecture-diagram.pdf](architecture-diagram.pdf) for the rendered
architecture diagram.
