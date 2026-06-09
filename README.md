# JIC-Geo — Dynamic Risk Index for Hiking Routes

JIC-Geo is a Geographic Information System (GIS) and routing engine designed to compute a dynamic risk index for hiking trails. By correlating biometric models (metabolic cost, velocity profiles) with spatial data (DEM elevations, gradients) and real-time meteorological conditions (WBGT, precipitation), it identifies safety issues and designs optimal paths with climate-adaptive routing.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy (GeoAlchemy2) · Alembic · Scipy |
| **Frontend** | Vue 3 (Vite + TS) · Pinia · MapLibre GL JS · Tailwind CSS · DaisyUI |
| **Database** | PostgreSQL 16 · PostGIS (Spatial & Raster) · pgRouting |
| **Containers** | Docker · Docker Compose |

---

## Directory Structure

```
JIC-Geo/
├── backend/                  # FastAPI REST API & Unit Tests
│   ├── app/
│   │   ├── api/v1/           # API routes (REST endpoints)
│   │   ├── db/               # SQLAlchemy models & DB sessions
│   │   └── modules/          # Domain services (dat, rut, vel, met, prf, cli, sim, rie, grf)
│   └── tests/                # Pytest unit & integration suites
├── frontend/                 # Vue 3 Single Page Application
│   ├── src/
│   │   ├── assets/           # Styles (Tailwind directives)
│   │   ├── components/       # Vue components (map, sidebar, simulation, upload)
│   │   ├── composables/      # Shared state helpers & theme controllers
│   │   └── stores/           # Pinia stores (global state)
│   ├── tailwind.config.cjs
│   └── postcss.config.cjs
├── db/                       # SQL scripts to bootstrap database extensions
├── docs/                     # System requirements, math formulas, and specs
│   ├── Requerimientos.md     # Base requirements
│   ├── Formulas.md           # Biomechanical and climate formulas
│   ├── mitigacion.md         # Database optimizations and mitigations
│   ├── plan.md               # 8-Phase implementation plan
│   └── issues.md             # Backlog of GitHub issues
├── data/                     # DEM files and GPX samples (gitignored)
└── docker-compose.yml        # Docker composition for database
```

---

## Quick Start (Docker-First)

### Requirements
Ensure you have Docker and `make` installed.

### Setup & Run
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Spin up the infrastructure:
   ```bash
   make dev
   ```
   *This starts the PostgreSQL + PostGIS + pgRouting database in the background.*

3. Spin up the frontend development server:
   ```bash
   make frontend
   ```
   *The frontend runs at `http://localhost:5173`.*

4. Spin up the backend natively (optional if not running via Docker):
   ```bash
   make backend
   ```
   *The API will be available at `http://localhost:8000/docs` (Swagger UI).*

---

## Native Installation (macOS Fallback)

If you prefer to run the database natively on macOS using Homebrew:

1. **Install PostgreSQL and PostGIS:**
   ```bash
   brew install postgresql@16 postgis pgrouting
   ```

2. **Start the database service:**
   ```bash
   brew services start postgresql@16
   ```

3. **Initialize the Database:**
   ```bash
   createdb jicgeo
   psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS postgis_raster;"
   psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"
   ```

4. **Verify Installations:**
   ```bash
   psql jicgeo -c "SELECT postgis_full_version();"
   psql jicgeo -c "SELECT pgr_version();"
   ```

---

## Development Commands

A `Makefile` is configured in the root to automate common tasks:

| Command | Action |
|---|---|
| `make dev` | Spins up the PostgreSQL/PostGIS database container. |
| `make db-only` | Starts only the DB container (useful for native backend development). |
| `make migrate` | Applies Alembic migrations to the active database. |
| `make backend` | Starts the FastAPI application locally with reload enabled. |
| `make frontend` | Launches the Vite frontend development server. |
| `make lint` | Runs `ruff` check and `mypy` type checker on the backend. |
| `make test` | Runs the Python unit tests with `pytest`. |
| `make db-reset` | Destroys the database volume and rebuilds it fresh (warning: destructive). |

---

## Internal Documentation References

For specific details regarding formulas, optimizations, and issues:
* **Architecture Rules:** [architecture.md](file:///Users/Irvinng/Developer/Proyectos/JIC-Geo/docs/architecture.md)
* **Requirements & Specs:** [Requerimientos.md](file:///Users/Irvinng/Developer/Proyectos/JIC-Geo/docs/Requerimientos.md)
* **Mathematical & Biomechanical Formulas:** [Formulas.md](file:///Users/Irvinng/Developer/Proyectos/JIC-Geo/docs/Formulas.md)
* **Optimization & PostGIS Mitigations:** [mitigacion.md](file:///Users/Irvinng/Developer/Proyectos/JIC-Geo/docs/mitigacion.md)
* **Roadmap Plan:** [plan.md](file:///Users/Irvinng/Developer/Proyectos/JIC-Geo/docs/plan.md)
* **Issues Backlog:** [issues.md](file:///Users/Irvinng/Developer/Proyectos/JIC-Geo/docs/issues.md)
