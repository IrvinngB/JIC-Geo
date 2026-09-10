# RiskTrail — Architecture Plan

> Panorama completo del sistema: auth, perfiles, historial, GPS tracking, sharing.
> Todo pensado como plataforma desde el día uno.

---

## 1. Database Schema (PostgreSQL)

### Tabla `users`

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    name          VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url    TEXT,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);
```

### Tabla `profiles`

Cada usuario tiene múltiples perfiles de excursionista.

```sql
CREATE TABLE profiles (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name           VARCHAR(100) NOT NULL,          -- "Irvin solo", "Team full"
    weight_kg      NUMERIC(5,1) NOT NULL,
    load_kg        NUMERIC(5,1) DEFAULT 0,
    fitness_level  VARCHAR(20) DEFAULT 'medium',   -- low|medium|high|athlete
    surface_type   VARCHAR(20) DEFAULT 'dirt',     -- dirt|paved|gravel|mud|sand|scrub|dense_scrub
    is_default     BOOLEAN DEFAULT false,
    created_at     TIMESTAMPTZ DEFAULT now(),
    updated_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_profiles_user ON profiles(user_id);
```

### Tabla `route_history`

Cada análisis guardado.

```sql
CREATE TABLE route_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id      UUID REFERENCES profiles(id) ON DELETE SET NULL,
    route_name      VARCHAR(200),
    route_id        VARCHAR(50) NOT NULL,           -- ID interno del análisis
    source_format   VARCHAR(10),                    -- GPX, GEOJSON
    is_favorite     BOOLEAN DEFAULT false,

    -- Resumen del análisis (denormalizado para listados rápidos)
    mide_global     SMALLINT,
    total_distance_km NUMERIC(7,2),
    estimated_time_h  NUMERIC(7,2),
    total_kcal      NUMERIC(7,0),
    elevation_gain_m NUMERIC(7,0),
    risk_max        SMALLINT,

    -- Datos completos del análisis (para re-abrir sin re-analizar)
    analysis_json   JSONB NOT NULL,

    -- Metadatos
    weather_snapshot JSONB,                         -- clima al momento del análisis
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_history_user ON route_history(user_id);
CREATE INDEX idx_history_favorites ON route_history(user_id, is_favorite) WHERE is_favorite = true;
CREATE INDEX idx_history_created ON route_history(user_id, created_at DESC);
```

### Tabla `route_segments` (opcional, para GPS tracking)

Almacena geometría de segmentos para matching offline/sin re-analizar.

```sql
CREATE TABLE route_segments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    history_id      UUID NOT NULL REFERENCES route_history(id) ON DELETE CASCADE,
    seq             SMALLINT NOT NULL,
    geom            GEOMETRY(LineString, 4326),
    risk_score      SMALLINT,
    velocity_kmh    NUMERIC(4,1),
    slope_pct       NUMERIC(5,2),
    direction       VARCHAR(10),
    surface_type    VARCHAR(20),
    is_top_risk     BOOLEAN DEFAULT false
);

CREATE INDEX idx_segments_history ON route_segments(history_id);
CREATE INDEX idx_segments_geom ON route_segments USING GIST(geom);
```

### Tabla `gps_tracks` (para registro de ruta real)

```sql
CREATE TABLE gps_tracks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    history_id      UUID NOT NULL REFERENCES route_history(id) ON DELETE CASCADE,
    recorded_at     TIMESTAMPTZ DEFAULT now(),
    geom            GEOMETRY(LineString, 4326),
    total_distance_m NUMERIC(7,0),
    duration_s      INTEGER,
    avg_speed_kmh   NUMERIC(4,1)
);

CREATE INDEX idx_tracks_history ON gps_tracks(history_id);
```

### Tabla `shared_routes`

Links públicos para compartir análisis.

```sql
CREATE TABLE shared_routes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    history_id      UUID NOT NULL REFERENCES route_history(id) ON DELETE CASCADE,
    share_code      VARCHAR(10) UNIQUE NOT NULL,   -- corto: "abc123"
    created_by      UUID REFERENCES users(id),
    view_count      INTEGER DEFAULT 0,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_shared_code ON shared_routes(share_code);
```

### Tabla `offline_cache_metadata`

Registro de qué zonas tiene cacheadas el usuario (para sync).

```sql
CREATE TABLE offline_cache_metadata (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    history_id      UUID REFERENCES route_history(id) ON DELETE SET NULL,
    bbox            GEOMETRY(Polygon, 4326),
    tile_count      INTEGER,
    cached_at       TIMESTAMPTZ DEFAULT now()
);
```

---

## 2. API Endpoints (FastAPI)

### Auth

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Registro (email, nombre, password) |
| POST | `/api/v1/auth/login` | Login → returns access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Renueva access token |
| GET | `/api/v1/auth/me` | Retorna usuario actual |

### Profiles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/profiles` | Listar perfiles del usuario |
| POST | `/api/v1/profiles` | Crear perfil |
| PUT | `/api/v1/profiles/{id}` | Actualizar perfil |
| DELETE | `/api/v1/profiles/{id}` | Eliminar perfil |
| PUT | `/api/v1/profiles/{id}/default` | Marcar como default |

### Route History

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/history` | Listar historial (filtros: favorite, search, date) |
| GET | `/api/v1/history/{id}` | Obtener análisis completo |
| POST | `/api/v1/history` | Guardar nuevo análisis (recibe analysis_json) |
| DELETE | `/api/v1/history/{id}` | Eliminar del historial |
| PUT | `/api/v1/history/{id}/favorite` | Toggle favorito |

### Analysis (existentes + nuevos)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/analysis/upload` | Subir GPX/GeoJSON + perfil → análisis completo |
| POST | `/api/v1/analysis/simulate` | Re-simular clima sobre análisis existente |
| GET | `/api/v1/analysis/{id}/segments` | Obtener segmentos con geometría |

### GPS Tracking

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/tracking/save` | Guardar registro GPS de ruta real |
| GET | `/api/v1/tracking/{history_id}` | Obtener track real guardado |

### Sharing

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/share` | Crear link público |
| GET | `/api/v1/share/{code}` | Obtener análisis público (sin auth) |

### Offline

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/offline/manifest` | Recibir manifest de tiles a descargar |
| GET | `/api/v1/offline/analysis/{id}` | Download análisis completo para cache local |

---

## 3. Frontend Architecture

### Stores (Pinia)

```
stores/
├── authStore.ts        # user, token, login/logout/register
├── profileStore.ts     # profiles[], activeProfile, CRUD
├── historyStore.ts     # history[], favorites, CRUD
├── routeStore.ts       # análisis actual (ya existe)
├── simulationStore.ts  # clima simulado (ya existe)
└── trackingStore.ts    # GPS tracking state
```

### Auth Flow

```
1. Usuario abre /login
2. Ingresa email + password
3. POST /auth/login → { access_token, refresh_token }
4. Guardar tokens en httpOnly cookie o Pinia store
5. Todos los requests llevan Authorization: Bearer <token>
6. Si 401 → intentar refresh → si falla → logout
```

### Protected Routes

```typescript
// router/index.ts
const routes = [
  { path: '/', component: LandingView },           // público
  { path: '/login', component: LoginView },         // público
  { path: '/register', component: RegisterView },   // público
  { path: '/share/:code', component: ShareView },   // público
  { path: '/mapa', component: MapView, meta: { requiresAuth: true } },
  { path: '/historial', component: HistoryView, meta: { requiresAuth: true } },
  { path: '/perfil', component: ProfileView, meta: { requiresAuth: true } },
]
```

### Composables Nuevos

| Composable | Función |
|------------|---------|
| `useAuth()` | login, register, logout, user, isAuthenticated |
| `useProfiles()` | profiles, activeProfile, create/update/delete |
| `useHistory()` | history, favorites, save/load/delete |
| `useTracking()` | start/stop tracking, record GPS points |
| `useOffline()` | cache management, sync status |

---

## 4. Data Flow

### Flujo completo: Analizar y guardar

```
1. User login → authStore.user
2. User selecciona profile → profileStore.activeProfile
3. User sube GPX → POST /analysis/upload
4. Backend analiza → retorna analysis + segments con geom
5. Frontend muestra resultado en mapa
6. User hace click "Guardar" → POST /history
   - Guarda: analysis_json, resumen denormalizado, profile_id
7. User puede re-abrir desde historial → GET /history/{id}
8. User puede re-simular clima → POST /analysis/simulate
```

### Flujo: GPS Tracking

```
1. User tiene análisis abierto
2. Activa tracking → navigator.geolocation.watchPosition()
3. Cada 3-5s: capturar punto GPS
4. Matching local: ¿en qué tramo estoy?
5. Si tramo peligroso → vibración/alerta
6. User detiene tracking → POST /tracking/save
   - Guarda: LineString GPS real, duración, distancia
7. Después: comparar ruta real vs planificada
```

### Flujo: Compartir

```
1. User tiene análisis guardado
2. Click "Compartir" → POST /share
3. Backend genera share_code corto
4. Retorna URL: /share/abc123
5. Cualquiera con el link puede ver → GET /share/{code}
6. Sin auth requerida para ver
```

---

## 5. Migración gradual (Sin romper nada)

### Fase 1 — Solo backend, sin auth

- Crear tablas `route_history`, `profiles` SIN user_id
- User_id se agrega como NULLABLE después
- Endpoints funcionan sin auth (dev mode)
- Frontend guarda en localStorage por ahora

### Fase 2 — Agregar auth

- Crear tabla `users`
- Agregar user_id NOT NULL a profiles y history
- Migrar datos de localStorage al primer login
- Protected routes en frontend

### Fase 3 — GPS + Offline

- Tabla `route_segments` y `gps_tracks`
- Service worker para offline
- Matching offline con turf.js

---

## 6. Tech Stack Adicional

| Necesidad | Solución |
|-----------|----------|
| Auth | FastAPI Security + JWT (python-jose) + bcrypt |
| Password hashing | passlib[bcrypt] |
| Rate limiting | slowapi |
| Session/Token storage | httpOnly cookies (más seguro que localStorage) |
| Geospatial queries | PostGIS (ya instalado) |
| Offline cache | Service Worker + Cache API |
| Position matching | turf.js (client-side) |
| GPS | Navigator Geolocation API |

---

## 7. Estimación de esfuerzo

| Fase | Features | Días estimados |
|------|----------|---------------|
| **Fase1** | DB schema + endpoints básicos (history, profiles) | 3-4 días |
| **Fase2** | Auth completo (register, login, JWT, protected routes) | 3-4 días |
| **Fase3** | Frontend: auth views, profile management, history view | 3-4 días |
| **Fase4** | GPS tracking + alertas + registro | 3-4 días |
| **Fase5** | Offline (service worker + cache) | 3-4 días |
| **Fase6** | Sharing + extras | 2-3 días |
| **Total** | | **17-23 días** |
