# Project Backlog & Issues

This document defines the GitHub/GitLab issues representing the remaining phases of the JIC-Geo project. Each issue is formulated following conventional commit standards and includes detailed descriptions, acceptance criteria (Definition of Done), and affected modules.

---

## Quick Path to Creation

You can create these issues directly using the GitHub CLI (`gh`). For example:
```bash
gh issue create --title "feat(backend): implement DAT spatial ingestion (GPX/GeoJSON upload) and DEM models" --body-file docs/issues.md --label "enhancement,status:needs-review"
```

---

## Phase-by-Phase Backlog

### Issue 1: `feat(backend): implement DAT spatial ingestion (GPX/GeoJSON upload) and DEM models`
* **Phase:** 1 — DAT Ingesta de Datos Espaciales
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Set up the core spatial database models and route ingestion pipeline. The system needs to accept GPX or GeoJSON files, parse their geometric properties, and store them as 3D Linestrings (3DZ, SRID 4326) in PostGIS. Additionally, configure the DEM (Digital Elevation Model) metadata registry table to prepare for elevation extraction.

#### Acceptance Criteria
- [ ] Implement `Route`, `Segment`, `SegmentCosts`, and `DEMSource` ORM models in `backend/app/db/models.py`.
- [ ] Create Alembic migration verifying spatial indices (`idx_routes_geom` and `idx_segments_geom` using GIST).
- [ ] Implement parser service for GPX/GeoJSON files.
- [ ] Expose `POST /routes/upload` that receives a GPX or GeoJSON file, parses it, and populates the `routes` table with 3DZ geometry.
- [ ] Write integration test uploading a sample GPX/GeoJSON and validating it was stored with Z coordinates.

---

### Issue 2: `feat(backend): implement RUT route segmentation, interpolation, and gradient smoothing`
* **Phase:** 2 — RUT Segmentación y Gradiente
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Implement the route processing pipeline. Routes must be segmented into equal-distance segments (default 100m). For each segment point, retrieve clean elevation from the DEM using bilinear interpolation. Implement noise-mitigation filters (Savitzky-Golay) to smooth elevations, detect slope spikes ($|S| > 0.75$), and calculate segment gradients ($S = \Delta h / \Delta x$).

#### Acceptance Criteria
- [ ] Implement segmentation function in `backend/app/modules/rut/service.py` to divide lines into 100m sub-lines.
- [ ] Implement bilinear interpolation query to extract elevation from `postgis_raster`.
- [ ] Integrate `scipy.signal.savgol_filter` for elevation smoothing.
- [ ] Implement spike detection and mark corrected points in `elevation_interpolated`.
- [ ] Calculate gradient ($S$) and accumulation values (positive and negative gain).
- [ ] Unit tests for the elevation smoothing and segmentation logic.

---

### Issue 3: `feat(backend): implement biomechanical models (Tobler velocity & Minetti/Pandolf metabolic cost)`
* **Phase:** 3 — VEL + MET + PRF Motor Biomecánico
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Implement core human movement and energy expenditure calculations. This includes Tobler's hiking function (and Irmischer-Clarke alternative) for velocity estimation based on slope, Minetti's Cost of Transport (CoT) with safe linear extrapolation for steep slopes, and Pandolf's metabolic rate formula. Incorporate hiker profile settings (weight, load, fitness level).

#### Acceptance Criteria
- [ ] Implement Tobler and Irmischer-Clarke velocity functions in `backend/app/modules/vel/service.py`.
- [ ] Implement Minetti formula with safe linear extrapolation ($|S| > 0.60$) in `backend/app/modules/met/service.py`.
- [ ] Implement Pandolf metabolic rate formula (Watts) including terrain factor ($\eta$) lookup.
- [ ] Add Pydantic validation for `HikerProfile` ensuring load weight < body weight.
- [ ] Verify calculations against formulas reference values via unit tests (e.g., flat terrain CoT $\approx 2.5$ J/kg·m).

---

### Issue 4: `feat(backend): implement CLI meteorology service with WBGT calculation and CLI/SIM simulations`
* **Phase:** 4 — CLI + SIM Integración Climática
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Integrate meteorological factors. Fetch live weather data (from Open-Meteo), approximate Wet Bulb Globe Temperature (WBGT) using temperature, humidity, and solar radiation, and apply velocity/cardiovascular drift degradation. Allow manual climate override via simulations and configure predefined scenarios (heavy rain, extreme heat, night, etc.).

#### Acceptance Criteria
- [ ] Set up client to request current weather data from Open-Meteo API in `backend/app/modules/cli/service.py`.
- [ ] Implement WBGT approximation formula.
- [ ] Create `climate_zones` database table and check cache TTL.
- [ ] Implement simulation service injecting custom climate parameters.
- [ ] Implement the 5 predefined scenarios (`dry`, `light_rain`, `heavy_rain`, `extreme_heat`, `night`).

---

### Issue 5: `feat(backend): implement RIE Risk Score engine and MIDE index mapping`
* **Phase:** 5 — RIE Índice de Riesgo y MIDE
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Combine physiological, velocity, and climatic variables into a single risk score per segment using AHP (Analytic Hierarchy Process) weights. Translate the aggregated risk metrics into the standard Spanish MIDE scale (1-5 across Severity, Orientation, Displacement, and Effort). Identify the top 10% highest-risk segments for warnings.

#### Acceptance Criteria
- [ ] Implement Risk Score calculation per segment combining metabolic cost, velocity degradation, climate, and terrain in `backend/app/modules/rie/service.py`.
- [ ] Configure adjustable AHP weights.
- [ ] Implement MIDE index mapper (4 dimensions) for both segment-level and overall route level.
- [ ] Filter and flag the top 10% highest risk segments of the route.
- [ ] Unit tests verifying MIDE dimension constraints.

---

### Issue 6: `feat(backend): implement GRF pgRouting topology and dynamic routing graph`
* **Phase:** 6 — GRF Grafo y Enrutamiento pgRouting
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Build path topology and configure pgRouting. Transform route segments into edges with nodes to support network analysis. Implement dynamic routing queries using A* (or Dijkstra as fallback) with asymmetric costs (cost uphill $\neq$ cost downhill). Incorporate the climate cost multiplier as an immutable database function.

#### Acceptance Criteria
- [ ] Create `edges` table and run `pgr_createTopology` to build nodes.
- [ ] Implement `climate_cost_multiplier` as `IMMUTABLE PARALLEL SAFE` SQL function with a maximum 3x multiplier cap.
- [ ] Implement route-finding queries using A* Bidirectional in `backend/app/modules/grf/repository.py`.
- [ ] Support intermediate waypoints and on-the-fly cost modifications.

---

### Issue 7: `feat(backend): expose REST endpoints for route analysis, simulations, and optimal routing`
* **Phase:** 7 — API Endpoints REST
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Expose all backend capabilities via clean FastAPI REST endpoints. This includes route upload and analysis, simulation triggers, segment data retrieval, and optimal pathfinding queries. Secure payloads with Pydantic validation schemas.

#### Acceptance Criteria
- [ ] Implement `POST /routes/analyze` (handles upload, processing, and return of segments + MIDE indices).
- [ ] Implement `POST /routes/{route_id}/simulate` to compare real vs simulated weather.
- [ ] Implement `POST /routes/optimal-path` to run pgRouting queries between points.
- [ ] Document all routes using OpenAPI/Swagger documentation.

---

### Issue 8: `feat(frontend): build MAP interactive route map and hiker profile dashboard`
* **Phase:** 8 — MAP Mapa Web Interactivo (Vue 3)
* **Labels:** `enhancement`, `status:needs-review`

#### Description
Implement the final user interface. Integrate MapLibre GL JS to display routes colored by risk score (green $\rightarrow$ yellow $\rightarrow$ red). Add popups with segment details, a file uploader component, a sidebar for the hiker profile form, and climate sliders for manual weather simulation.

#### Acceptance Criteria
- [ ] Set up MapLibre GL JS and render route geojson segments colored by risk score.
- [ ] Implement segment click events showing detailed metrics in a popup.
- [ ] Add hiker profile form updating state dynamically in Pinia.
- [ ] Integrate climate sliders trigger reactively re-running simulations.
- [ ] Display MIDE 4-dimension indicators and flag top 10% risk segments on the map.
