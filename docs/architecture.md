# Architecture Rules — RiskTrail

This document defines the architecture conventions and constraints that govern every code change in this repository. It applies to the backend (FastAPI / Python) and the frontend (Vue 3 / TypeScript).

**Breaking these rules requires a written justification in the PR description.**

---

## Core Principles

1. **Concepts before code.** If you cannot explain what a module does in one sentence, it is not ready to be coded.
2. **Boundaries are sacred.** No module is allowed to reach directly into another module's internals. Always go through the public interface (service or repository).
3. **Purity first.** Domain logic lives in `service.py` and has no I/O side effects. I/O (DB queries, HTTP calls) lives exclusively in `repository.py`.
4. **One reason to change.** Each file, function, and component has one responsibility. If adding a feature requires modifying two conceptually different reasons in the same file, the file needs to be split first.
5. **Tests travel with the code.** A unit that has no test is considered incomplete, not done.

---

## Backend Architecture

### Module Layout (Mandatory)

Every domain in `backend/app/modules/<domain>/` follows this exact layout:

```
<domain>/
├── __init__.py       # Empty or re-exports only
├── schemas.py        # Pydantic models for input/output validation
├── service.py        # Pure business logic — NO database calls, NO HTTP calls
├── repository.py     # All database queries (SQLAlchemy, raw SQL) — NO business logic
└── router.py         # FastAPI endpoints — thin wiring only, no logic
```

> [!IMPORTANT]
> `service.py` must be importable without a running database. If it requires a DB call to function, move that logic to `repository.py` and inject it.

### Responsibility Rules Per Layer

| Layer | Allowed | Forbidden |
|---|---|---|
| `schemas.py` | Pydantic models, field validators, type aliases | Business logic, DB imports |
| `service.py` | Pure computation, domain rules, algorithm implementations | SQLAlchemy sessions, HTTP clients, `requests`, `httpx` |
| `repository.py` | DB queries, PostGIS functions, raw SQL | Business logic, Pydantic models (use plain dicts or dataclasses as return) |
| `router.py` | Dependency injection, HTTP wiring, status codes | Logic beyond a single-line call to service or repository |

### Naming Conventions

- **Functions:** `snake_case`, verb-first (`calculate_velocity`, `get_segment_by_id`).
- **Pydantic models:** `PascalCase`, noun (`HikerProfile`, `SegmentCostOut`).
- **Enums:** `PascalCase` class, `SCREAMING_SNAKE` members (`VelocityModel.TOBLER`).
- **Constants:** `SCREAMING_SNAKE_CASE` at module level (`TERRAIN_ETA`, `MINETTI_MAX`).

### Service Layer Rules

- Every `service.py` function must be **a pure function**: same inputs → same output, no global state mutation.
- Mathematical formulas must include the requirement ID they implement in the docstring (e.g., `VEL-01`, `MET-03`).
- When a formula has a known domain (e.g., Minetti `[-0.45, +0.45]`), define the limits as named module-level constants, not magic numbers.

```python
# Correct
MINETTI_MIN = -0.45
MINETTI_MAX = 0.45

def minetti_cot(gradient: float) -> tuple[float, CotMethod]:
    """Returns (J/kg·m, method). MET-01"""
    if MINETTI_MIN <= gradient <= MINETTI_MAX:
        ...

# Wrong — magic numbers, silent domain violation
def minetti_cot(g):
    if -0.45 <= g <= 0.45:
        ...
```

### Database Rules

- **All spatial geometry** is stored in SRID 4326. Never assume a different CRS without explicit conversion.
- **Geometry columns** use GeoAlchemy2 `Geometry(...)` type annotations in ORM models.
- **Async sessions only.** Never use synchronous SQLAlchemy in application code. Only Alembic migration scripts use a synchronous engine.
- **Indices** are mandatory for all geometry columns (`GIST`) and all FK/join columns used in route queries.
- **Alembic migrations** are the sole way to change the DB schema. Never modify the schema from application code.

### API Design Rules

- All endpoints live under `/api/v1/`.
- Request and response bodies are always typed with a Pydantic schema — never a raw `dict`.
- Endpoints return `400` for validation errors, `404` for not-found resources, `422` for unprocessable entities (Pydantic default), and `500` only for truly unexpected server errors.
- HTTP methods must match semantics: `GET` is idempotent, `POST` creates or triggers, `PATCH` partially updates.
- Health check at `GET /health` must always respond with a structured JSON body that includes DB connectivity status.

---

## Frontend Architecture

### Component Layer Rules

Components are organized by responsibility and must not cross their layer:

```
components/
├── map/          # MapLibre-related components — render only, no state mutation
├── sidebar/      # Display panels — read from store, no direct API calls
├── upload/       # File-input and drag-drop logic — delegate to composables
└── simulation/   # Controls for climate simulation — delegate to composables
```

| Layer | Reads from | Writes to | Forbidden |
|---|---|---|---|
| `views/` | store, composables | route navigation | Direct fetch calls |
| `components/` | props, store (read-only) | emits up | Modifying store directly |
| `composables/` | store | store (write) | Rendering HTML, DOM access |
| `stores/` | nothing | own state | Calling other stores' actions directly |

### Component Rules

- **Every component has a single job.** `RouteMap.vue` renders the map. `FileUploader.vue` handles file input. If you are adding a second job, create a second component.
- **No business logic in templates.** Derived values belong in `computed` properties or composables, not in `v-if` expressions.
- **Props are typed.** Use TypeScript `defineProps<{...}>()` always — never untyped props.
- **Emits are typed.** Use `defineEmits<{...}>()`.
- **No inline styles.** Styling is done exclusively via Tailwind utility classes or DaisyUI component classes.

### State Management Rules (Pinia)

- **One store, one domain.** The `routeStore` owns route data. A future `climateStore` would own climate state. Stores do not read from each other's state directly.
- **Actions own API calls.** All `fetch` calls live inside Pinia actions. Components and composables call actions, never `fetch` directly.
- **Loading and error state are always explicit.** Every async action must manage `isLoading` and `error` states.

```typescript
// Correct
async function uploadAndAnalyze(file: File, profile: object): Promise<void> {
  isLoading.value = true
  error.value = null
  try { ... } catch (err) { error.value = ... } finally { isLoading.value = false }
}

// Wrong — fire and forget, no error handling
async function uploadAndAnalyze(file: File) {
  const res = await fetch(...)
  analysis.value = await res.json()
}
```

### Composable Rules

- A composable encapsulates a **behavior**, not data. Data lives in stores.
- A composable must be callable multiple times across different components without side effects leaking between instances (use local `ref` inside the function, not module-level state).
- Exception: `useTheme` uses module-level `ref` intentionally to share theme state globally — this is a documented, explicit exception.

### Styling Rules

- Use the `jic-light` / `jic-dark` DaisyUI themes. Never hardcode hex colors directly in components.
- Use semantic color tokens: `text-primary`, `bg-base-100`, `text-error`, `bg-success` — not `text-green-500`.
- Responsive layouts are built with Tailwind's `md:` and `lg:` breakpoint prefixes.

---

## Cross-Cutting Rules

### Conventional Commits

All commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

feat(met): implement Pandolf metabolic rate formula
fix(rut): correct Savitzky-Golay window size for short segments
docs(readme): add native macOS installation guide
test(vel): add Tobler boundary case for extreme descent
refactor(dat): extract GPX parser into dedicated module
```

Valid types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `style`, `perf`.

### No AI Attribution in Commits

Never add `Co-Authored-By` or any AI attribution to commits. Commits reflect human authorship.

### Testing Rules

- **Unit tests** live in `backend/tests/unit/`. They test a single pure function and never touch the database or network.
- **Integration tests** live in `backend/tests/integration/`. They may use the database.
- Each unit test includes at least one **reference value** from `Formulas.md` to validate the mathematical implementation against the scientific source.
- Test files are named `test_<module>_<layer>.py` (e.g., `test_vel_service.py`).

### Environment & Secrets

- Never commit `.env`. Only `.env.example` is committed.
- All configurable values (URLs, credentials, TTLs) go into `backend/app/config.py` as Pydantic settings fields with documented defaults.
- Docker Compose reads variables from `.env` at the root via `${VAR:-default}` syntax.

---

## Decision Log

| Decision | Reason | Date |
|---|---|---|
| FastAPI over Django/Flask | Async-native, Pydantic-first, self-documenting OpenAPI | 2026-06 |
| GeoAlchemy2 over raw PostGIS SQL | ORM-level type safety for geometry columns | 2026-06 |
| MapLibre GL JS over Leaflet | WebGL rendering for large segment counts, no Mapbox token required | 2026-06 |
| Tailwind v3 + DaisyUI v4 | DaisyUI v5 is in beta — v3+v4 is stable production-ready | 2026-06 |
| uv over Poetry | Faster dependency resolution, cleaner lockfile | 2026-06 |
| Module-per-domain over a single services layer | Each domain grows independently without coupling | 2026-06 |
| `service.py` purity as hard constraint | Enables deterministic unit testing without DB fixtures | 2026-06 |
