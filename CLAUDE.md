# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

RiskTrail (product name — internal DB name `jicgeo` and DaisyUI themes `jic-light`/`jic-dark` are unrelated and must not be renamed) is a GIS routing engine that computes a dynamic risk index for hiking routes. It correlates biomechanical models (metabolic cost, velocity profiles) with spatial data (DEM elevations, gradients) and real-time/simulated weather (WBGT, precipitation) to flag safety issues and design climate-adapted optimal routes.

Stack: FastAPI + SQLAlchemy(GeoAlchemy2) + Alembic on Python 3.12/`uv` (backend); Vue 3 + Vite + TS + Pinia + MapLibre GL JS + Tailwind/DaisyUI on `pnpm` (frontend); PostgreSQL 16 + PostGIS + pgRouting (db); Docker Compose ties them together.

The project is mid-migration from MVP to a full platform (auth, profiles, history, sharing, GPS tracking were added on top of the original single-shot analysis flow) — expect some rough edges and evolving conventions outside the core domain modules, which are held to a stricter standard (see Architecture Rules below).

## Commands

Host has no Python/`uv` installed — **backend commands only work inside Docker.** `make backend`/`make test`/`make lint` invoke `uv` directly and will fail on a bare host unless `uv` is installed locally.

```bash
# Infra
cp .env.example .env
make dev              # docker compose up — db + backend + frontend
make db-only           # just the db container (for native backend dev)
make db-reset           # ⚠️ destroys and recreates the db volume

# Backend (run via Docker unless uv is installed on host)
docker compose run --rm backend uv run alembic upgrade head   # migrate
docker compose run --rm backend uv run pytest tests/ -v       # all tests
docker compose run --rm backend uv run pytest tests/unit/test_vel_service.py -v   # single file
docker compose run --rm backend uv run pytest tests/unit/test_vel_service.py::TestClass::test_name -v  # single test
docker compose run --rm backend uv run ruff check .           # lint
docker compose run --rm backend uv run mypy app                # type check
# equivalents if uv is installed natively: `make migrate`, `make backend`, `make test`, `make lint`

# Frontend (pnpm everywhere: host, Makefile and the frontend Docker image via corepack)
cd frontend && pnpm install
pnpm dev        # vite dev server on :5173, proxies /api -> $VITE_API_PROXY_TARGET (default localhost:8000)
pnpm build      # vue-tsc --build && vite build
pnpm test       # vitest
pnpm lint       # eslint . --fix
```

Backend tests need a live Postgres/PostGIS connection (`tests/conftest.py` opens a real `AsyncSession` against `settings.database_url` and rolls back per-test in a savepoint) — the `db` container must be up. Unit tests (`backend/tests/unit/`) test one pure function each and never touch the DB; integration tests (`backend/tests/integration/`) do. Test files are named `test_<module>_<layer>.py`.

There is no CI workflow in this repo (`.github/workflows` does not exist) — `make lint`/`make test` are the only checks.

## Architecture

### Domain modules (the scientific core)

`backend/app/modules/` is organized one directory per domain, each following a **mandatory** four-file layout (`docs/documentacion/architecture.md`):

- `schemas.py` — Pydantic I/O models only
- `service.py` — pure functions only, **no DB/HTTP calls**, must be importable without a running database; this is where the biomechanical/climate/risk math lives
- `repository.py` — all DB/PostGIS queries, no business logic
- `router.py` — thin FastAPI wiring only

Module boundaries are enforced: one module must not reach into another's internals, only through its `service`/`repository` public functions. Formula-implementing functions cite a requirement ID in their docstring (e.g. `MET-01`, `RIE-02`) traceable to `docs/documentacion/Formulas.md` / `Requerimientos.md`.

Domain module glossary (short Spanish-derived codes, not obvious from the name alone):

| Code | Domain | Key content |
|---|---|---|
| `dat` | Data ingestion | GPX upload parsing |
| `rut` | Route processing | DEM elevation extraction, spike detection/repair, segmentation |
| `vel` | Velocity models | Tobler, Irmischer-Clarke hiking speed functions |
| `met` | Metabolic/biomechanics | Minetti cost-of-transport, Pandolf metabolic rate, fatigue estimation |
| `prf` | Hiker profile | fitness level, weight/load, velocity adjustment factor |
| `cli` | Climate | WBGT/wet-bulb calculation, cardiovascular drift multiplier, rain velocity factor |
| `sim` | Climate simulation | resolves manual climate overrides vs. real data |
| `rie` | Risk engine (riesgo) | AHP-weighted segment risk, Cifuentes factor, MIDE scoring |
| `grf` | Routing graph (grafo) | pgRouting node/edge helpers |
| `auth`, `his`, `share`, `track` | Platform layer | JWT auth, saved-analysis history, public share links, GPS track recording |

Several modules (`vel`, `met`, `sim`, `rie`, `cli`) have **no standalone router** wired into `app/api/v1/router.py` — they're internal services composed together, not by their own routers. The composition point is `app/api/v1/endpoints/analysis.py` (`POST /api/v1/routes/analysis`), which imports across `dat`, `rut`, `vel`, `met`, `prf`, `cli`, `rie`, `sim` to run the full biomechanical/risk pipeline against an uploaded route and returns per-segment + route-level risk/MIDE/climate output. Read this file first when touching the risk-calculation pipeline — it's the one place that shows how the domain modules actually compose.

Routed modules live under `/api/v1/` with prefixes: `/auth`, `/profiles` (via `prf.user_router`), `/history`, `/share`, `/tracking`, `/routes` (dat/rut/analysis/grf all share this prefix), `/dem`, `/climate`.

### Database

All schema changes go through Alembic (`backend/alembic/`) — never modify schema from application code. All geometry is SRID 4326, `GeoAlchemy2.Geometry(...)` typed, GIST-indexed. Async SQLAlchemy everywhere except Alembic migration scripts (sync engine). Models (`backend/app/db/models.py`): `User`, `Route`, `Segment`, `SegmentCosts`, `DEMSource`, `ClimateZone`, `Edge`, `Profile`, `RouteHistory`, `SharedRoute`, `GpsTrack`.

### Frontend

Layer boundaries (`docs/documentacion/architecture.md`): `views/` may read stores/composables and navigate, never fetch directly; `components/` read props/store read-only and emit up, never mutate store; `composables/` encapsulate a *behavior* using local refs (not data — data lives in stores) and may write to stores; `stores/` own their own domain exclusively and never call another store's actions directly. All `fetch`/API calls live inside Pinia actions, which must always manage explicit `isLoading`/`error` state.

Component subfolders are responsibility-scoped: `map/` (MapLibre rendering, no state mutation), `sidebar/` (read-only display panels), `upload/`, `simulation/` (climate-scenario controls) — each delegates side effects to composables rather than doing them inline.

The main tool UI lives at `/mapa` (not `/app` — that route collided with something else historically); `/mapa/nueva` is the upload/new-analysis flow (`UploadFormView.vue`). Routes under `meta: { requiresAuth: true }` redirect to `/login` via the `router.beforeEach` guard, which checks `localStorage['rt_token']`.

Frontend talks to the backend exclusively via the Vite dev proxy: requests to `/api/*` are forwarded to `VITE_API_PROXY_TARGET` (default `http://localhost:8000`; set to `http://backend:8000` inside Docker Compose).

Styling: DaisyUI semantic tokens only (`text-primary`, `bg-base-100`, etc.), never raw Tailwind color utilities or hardcoded hex — themes are `jic-light`/`jic-dark`.

### Cross-cutting conventions

- Conventional Commits required (`feat(met): ...`, `fix(rut): ...`); no AI co-author attribution in commits.
- Config values are centralized as Pydantic settings fields in `backend/app/config.py` with documented defaults (includes the AHP risk weights, Minetti domain bounds, segment length default) — never scatter magic numbers/URLs through the domain code.
- `.env` is never committed; `.env.example` is the template, and Docker Compose reads it via `${VAR:-default}`.

## Spec-Driven Development (SDD)

Non-trivial changes in this project go through the SDD workflow. Artifacts are file-based under `openspec/` (Engram persistence is not connected in every environment — check `openspec/config.yaml` for the active mode before assuming otherwise).

- `/sdd-explore <topic>` — investigate an idea/feature before committing to a change; reads the codebase, no files written
- `/sdd-new <change>` — run exploration then write a proposal for a new change
- `/sdd-ff <name>` — fast-forward planning: proposal → specs → design → tasks
- `/sdd-continue [change]` — run the next dependency-ready phase
- `/sdd-apply [change]` — implement tasks in batches, checking items off as it goes
- `/sdd-verify [change]` — validate the implementation against specs/design/tasks
- `/sdd-archive [change]` — close a verified change, merging its delta specs into `openspec/specs/`

Dependency chain: `proposal -> specs -> tasks -> apply -> verify -> archive` (`design` feeds into `specs`). Active change artifacts live under `openspec/changes/{change-name}/`; closed changes move to `openspec/changes/archive/`.

Given the scientific-accuracy requirement on domain logic (routing/risk/climate math), `sdd-propose`/`sdd-spec`/`sdd-design` for changes in `vel`/`met`/`cli`/`rie`/`sim` must justify formulas against `docs/documentacion/Formulas.md` / `Requerimientos.md`, not just describe the engineering approach — see `openspec/config.yaml` rules.

Strict TDD is enabled (`openspec/config.yaml` `strict_tdd: true`): backend has a real pytest suite (unit + integration) driving this; frontend has Vitest wired but no spec files yet, so TDD there is aspirational until test scaffolding exists. Test/lint/build commands used by `sdd-apply`/`sdd-verify` are the same ones in the Commands section above.
