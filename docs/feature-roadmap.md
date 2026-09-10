# RiskTrail — Feature Roadmap

> Lista de features planificados, organizados por prioridad y dependencias.
> Todo pensado como plataforma desde el día uno: auth → perfiles → historial → GPS.
> Arquitectura completa: `docs/architecture-plan.md`
> Última actualización: 2026-09-10

---

## Tier 0 — Auth (fundamento)

Sin esto nada funciona. Es la base de todo.

### 19. Auth + sistema de usuarios

**Descripción:** Registro, login y gestión de sesiones. Base para perfiles, historial y sharing por usuario.

**Detalle:**
- Tabla `users` en PostgreSQL (id, email, name, password_hash, created_at)
- Registro: email + nombre + contraseña (bcrypt hashing)
- Login: JWT access token + refresh token
- Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
- Middleware JWT en FastAPI para proteger endpoints
- Frontend: `authStore.ts` (Pinia), `LoginView.vue`, `RegisterView.vue`
- Protected routes en Vue Router
- httpOnly cookies para tokens (más seguro que localStorage)

**Dependencias:** Ninguna
**Complejidad:** Alta
**Archivos afectados:** `backend/app/modules/auth/`, `backend/app/db/models.py`, `frontend/src/stores/authStore.ts`, `frontend/src/views/LoginView.vue`, `frontend/src/views/RegisterView.vue`, `frontend/src/router/index.ts`

---

## Tier 1 — Perfil + Historial

Lo que falta para que RiskTrail se use de verdad. Todo persiste en PostgreSQL, asociado al usuario via auth.

### 1. Perfil persistente

**Descripción:** Guardar datos del excursionista (peso, carga, fitness, superficie) en PostgreSQL, asociado al usuario autenticado.

**Detalle:**
- Tabla `profiles` en PostgreSQL con `user_id` NOT NULL (FK → users)
- Endpoint `GET /api/v1/profiles` (solo retorna los del usuario actual)
- Soporte de perfil por defecto (`is_default = true`)
- Modo rápido: perfil por defecto inicial (70kg, 10kg, fitness medio, dirt)
- Botón "Restablecer valores por defecto"

**Dependencias:** #19 (auth)
**Complejidad:** Baja
**Archivos afectados:** `backend/app/db/models.py`, `backend/app/modules/prf/`, `backend/alembic/versions/`, `frontend/src/stores/profileStore.ts`, `frontend/src/components/HikerProfileForm.vue`

---

### 2. Múltiples perfiles

**Descripción:** Crear y permutar entre varios perfiles de excursionistas (para salidas individuales o en grupo).

**Detalle:**
- CRUD completo en backend: `GET`, `POST`, `PUT`, `DELETE /api/v1/profiles/{id}`
- Endpoints: `PUT /api/v1/profiles/{id}/default` para marcar como default
- Validación de negocio en backend (load < weight, límites plausibles)
- Selector rápido de perfil activo antes de analizar
- Modal/panel para administrar perfiles
- Cada perfil: `name`, `weight_kg`, `load_kg`, `fitness_level`, `surface_type`, `is_default`

**Dependencias:** #1 (perfil persistente)
**Complejidad:** Media
**Archivos afectados:** `backend/app/modules/prf/` (repository, router, schemas, service), `frontend/src/stores/profileStore.ts`, nuevo componente `ProfileSelector.vue`

---

### 3. Historial de análisis

**Descripción:** Guardar cada análisis completado en PostgreSQL con resumen denormalizado y resultado completo.

**Detalle:**
- Tabla `route_history` con `user_id` (FK → users), resumen (MIDE, distancia, tiempo, kcal, elevación, riesgo máx.) y `analysis_json` (JSONB)
- Índices: fecha creación descendente, favoritos
- Endpoints:
  - `POST /api/v1/history` → guardar análisis
  - `GET /api/v1/history` → listar (filtros: favorito, búsqueda, fecha)
  - `GET /api/v1/history/{id}` → obtener completo
  - `DELETE /api/v1/history/{id}` → eliminar
- Frontend: `historyStore.ts`, listado cronológico, re-apertura en mapa

**Dependencias:** #19 (auth), opcionalmente #1 (profile_id)
**Complejidad:** Media
**Archivos afectados:** `backend/app/db/models.py`, `backend/app/modules/his/`, `backend/alembic/versions/`, `frontend/src/stores/historyStore.ts`, nuevo componente `HistoryList.vue`

---

### 4. Favoritos

**Descripción:** Marcar rutas del historial como favoritas para acceso rápido.

**Detalle:**
- Columna `is_favorite` en `route_history` con índice condicional
- Endpoint `PUT /api/v1/history/{id}/favorite` (toggle)
- Filtro "Solo favoritos" en frontend
- Toggle reactivo desde tarjeta del historial

**Dependencias:** #3 (historial)
**Complejidad:** Baja
**Archivos afectados:** `backend/app/modules/his/`, `frontend/src/stores/historyStore.ts`, `HistoryList.vue`

---

### 5. Re-analizar con otro clima

**Descripción:** Sobre un análisis guardado en PostgreSQL, re-ejecutar la simulación climática sin re-subir el archivo.

**Detalle:**
- Desde historial, botón "Re-simular"
- Carga datos base guardados en `routeStore`
- Abre panel de ClimateSliders
- Ejecuta `POST /api/v1/analysis/simulate` en backend
- Muestra comparación real vs nuevo simulado

**Dependencias:** #3 (historial), backend endpoint de simulación
**Complejidad:** Media
**Archivos afectados:** `frontend/src/stores/routeStore.ts`, `ClimateSliders.vue`, `HistoryList.vue`

---

## Tier 2 — Ubicación real

Lo que diferencia a RiskTrail de otras apps. Requiere geolocalización del navegador.

### 6. GPS tracking básico

**Descripción:** Mostrar la posición actual del usuario en el mapa e identificar el tramo más cercano.

**Detalle:**
- Botón flotante "¿Dónde estoy?" en el mapa
- `navigator.geolocation.getCurrentPosition()`
- Centra mapa en posición actual
- Badge: tramo #X, riesgo Y/100, dirección
- Requiere permiso de ubicación
- Funciona sin internet (GPS satelital)

**Dependencias:** Análisis previo con geometría de segmentos
**Complejidad:** Media
**Archivos afectados:** `RouteMap.vue`, nuevo composable `useGeolocation.ts`

---

### 7. Alerta de tramo peligroso

**Descripción:** Notificación cuando el usuario entra a un tramo de riesgo alto o extremo.

**Detalle:**
- Tracking continuo cada 3-5 segundos
- Matching posición↔tramo con turf.js `nearestPointOnLine()`
- Si risk_score >= 60: vibración, badge rojo, sonido (opcional)
- Al salir del tramo: alerta se limpia
- Toggle activar/desactivar alertas

**Dependencias:** #6 (GPS tracking), turf.js
**Complejidad:** Media-Alta
**Archivos afectados:** `useGeolocation.ts`, `RouteMap.vue`, `MapView.vue`

---

### 8. Registro de ruta real

**Descripción:** Guardar el recorrido GPS real en PostgreSQL y comparar con la ruta planificada.

**Detalle:**
- Al iniciar tracking, grabar puntos GPS cada 5 segundos
- Al terminar, guardar LineString en tabla `gps_tracks` (FK → route_history)
- Vista de comparación: planificada (azul) vs real (verde)
- Métricas: distancia real vs estimada, tiempo, desviación máxima
- Opcional: exportar ruta real como GPX

**Dependencias:** #6 (GPS tracking), #3 (historial)
**Complejidad:** Alta
**Archivos afectados:** `useGeolocation.ts`, `backend/app/modules/tracking/`, nuevo componente `RouteComparison.vue`

---

### 9. Comparar análisis

**Descripción:** Elegir dos análisis del historial y verlos lado a lado.

**Detalle:**
- Checkbox selección en historial (máx. 2)
- Botón "Comparar" activo con 2 seleccionados
- Vista split: MIDE, tiempo, distancia, kcal, riesgo máximo
- Highlight de diferencias
- Responsive: apilados en mobile

**Dependencias:** #3 (historial)
**Complejidad:** Media
**Archivos afectados:** `HistoryList.vue`, nuevo componente `ComparisonView.vue`

---

## Tier 3 — Offline

Para que funcione en el campo sin señal. Cache local de datos que ya están en el backend.

### 10. Cache de análisis

**Descripción:** Descargar análisis completo del backend a IndexedDB para uso offline.

**Detalle:**
- Desde historial, botón "Descargar para offline"
- `GET /api/v1/offline/analysis/{id}` → descarga segmentos + geometría
- Guarda en IndexedDB
- Al abrir sin internet, análisis siguen accesibles
- Límite: ~50 análisis (LRU)
- Indicador de "disponible offline" en el historial

**Dependencias:** #3 (historial)
**Complejidad:** Media
**Archivos afectados:** `frontend/src/utils/offlineDb.ts`, `HistoryList.vue`

---

### 11. Cache de tiles del mapa

**Descripción:** Descargar tiles del mapa de la zona para uso offline.

**Detalle:**
- Botón "Descargar zona" en el mapa
- Calcula bounding box + buffer 5km
- Descarga tiles (streets/topo/satellite) a Cache API via service worker
- Indicador de progreso
- Sirve tiles del cache cuando no hay internet
- Eliminar zona descargada

**Dependencias:** Service worker (nuevo), MapLibre
**Complejidad:** Alta
**Archivos afectados:** nuevo `sw.js`, `RouteMap.vue`, nuevo componente `OfflineManager.vue`

---

### 12. Matching offline tramo↔posición

**Descripción:** Determinar tramo actual usando solo datos cacheados en IndexedDB.

**Detalle:**
- turf.js `nearestPointOnLine()` contra segmentos en IndexedDB
- Pre-filtrar por bounding box antes del cálculo completo
- Radio máximo: 100m → fuera de radio = "Fuera de la ruta"
- Actualización cada 3-5 segundos

**Dependencias:** #6 (GPS tracking), #10 (cache de análisis), turf.js
**Complejidad:** Media
**Archivos afectados:** `useGeolocation.ts`, utils de geo

---

## Tier 4 — Social y utilidades

Features que amplían alcance y utilidad social.

### 13. Compartir análisis

**Descripción:** Generar link público con el resumen del análisis.

**Detalle:**
- Botón "Compartir" en el análisis
- Genera share_code corto (ej: `/share/abc123`)
- Backend: tabla `shared_routes` con link a `route_history`
- Link accesible sin login
- Preview con imagen OG para WhatsApp/social

**Dependencias:** #3 (historial), tabla `shared_routes`
**Complejidad:** Media
**Archivos afectados:** `backend/app/modules/share/`, frontend nuevo componente `ShareView.vue`

---

### 14. Alerta meteorológica

**Descripción:** Notificar si el clima pronosticado cambia para una ruta guardada como "próxima salida".

**Detalle:**
- Marcar ruta como "próxima salida" (con fecha)
- Cada 6h consultar API meteorológica
- Si cambia significativamente → notificación push + badge
- Requiere job scheduler en backend (Celery/cron)
- API de clima: OpenWeather, visualcrossing, etc.

**Dependencias:** #3 (historial), API meteorológica, scheduler
**Complejidad:** Alta
**Archivos afectados:** backend nuevo servicio `weather_alerts.py`, frontend notificaciones

---

### 15. Condiciones del trail (crowd-sourced)

**Descripción:** Reportes de usuarios sobre el estado del sendero.

**Detalle:**
- Botón "Reportar condición" por tramo
- Categorías: limpio, embarrado, árbol caído, inundado, cerrado
- Opcional: foto
- Iconos en el mapa
- Expiran a 30 días
- Requiere auth

**Dependencias:** #19 (auth), backend modelo `TrailReport`
**Complejidad:** Alta
**Archivos afectados:** `backend/app/modules/reports/`, frontend `TrailReports.vue`

---

### 16. Exportar a GPS device

**Descripción:** Exportar ruta óptima como GPX para Garmin/etc.

**Detalle:**
- Botón "Exportar GPX" en ruta óptima
- Genera GPX: waypoints + tracklog
- Metadata: nombre, descripción, elevación
- Descarga archivo `.gpx`

**Dependencias:** Ruta óptima calculada
**Complejidad:** Baja
**Archivos afectados:** nuevo util `gpxExport.ts`

---

## Tier 5 — Growth

Features de escala.

### 17. Ruta sugerida

**Descripción:** "Quiero10km nivel medio" → sugerir rutas del catálogo.

**Detalle:**
- Formulario: distancia, dificultad, superficie, ubicación
- Backend busca en rutas pre-analizadas
- Top5 con preview
- Requiere catálogo de rutas

**Dependencias:** Catálogo de rutas, backend búsqueda
**Complejidad:** Alta
**Archivos afectados:** `backend/app/modules/suggest/`, `RouteSuggester.vue`

---

### 18. Foto por segmento

**Descripción:** Adjuntar fotos a tramos del historial.

**Detalle:**
- Asociar foto a tramo específico
- Almacenar en backend (S3-compatible o storage local)
- Thumbnail en detalle del tramo
- Galería del recorrido
- EXIF para geolocalizar

**Dependencias:** #8 (registro ruta real) o #3 (historial)
**Complejidad:** Media
**Archivos afectados:** `routeStore.ts`, backend storage, `SegmentPhotos.vue`

---

## Sprint Plan

### Sprint0 — Auth (1 semana)

| Feature | Días estimados |
|---------|---------------|
| DB Schema: tabla `users` + migración | 0.5 |
| Backend: register, login, refresh, me | 2 |
| Frontend: authStore, LoginView, RegisterView | 1.5 |
| Protected routes en Vue Router | 0.5 |
| **Total** | **4.5 días** |

### Sprint1 — Perfil + Historial (1-2 semanas)

| Feature | Días estimados |
|---------|---------------|
| DB Schema: `profiles` + `route_history` + migración | 1 |
| Backend: CRUD perfiles (`/api/v1/profiles`) | 1 |
| Backend: Historial y favoritos (`/api/v1/history`) | 1 |
| Frontend: profileStore + Selector y gestión | 1 |
| Frontend: historyStore + Listado y favoritos | 1 |
| **Total** | **5 días** |

### Sprint2 — GPS + Alertas (1-2 semanas)

| Feature | Días estimados |
|---------|---------------|
| #6 GPS tracking | 1.5 |
| #7 Alerta tramo peligroso | 1.5 |
| #10 Cache de análisis (offline) | 1 |
| **Total** | **4 días** |

### Sprint3 — Comparar + Compartir (1 semana)

| Feature | Días estimados |
|---------|---------------|
| #5 Re-analizar con clima | 1.5 |
| #9 Comparar análisis | 1.5 |
| #13 Compartir análisis | 1.5 |
| **Total** | **4.5 días** |

### Sprint4 — Offline completo (1-2 semanas)

| Feature | Días estimados |
|---------|---------------|
| #11 Cache de tiles | 2 |
| #12 Matching offline | 1.5 |
| #8 Registro de ruta real | 2 |
| **Total** | **5.5 días** |

### Futuro (sin sprint definido)

- #14 Alerta meteorológica
- #15 Condiciones del trail
- #16 Exportar GPX
- #17 Ruta sugerida
- #18 Foto por segmento

---

## Referencia

- Arquitectura completa: `docs/architecture-plan.md`
- DB Schema, API endpoints, Frontend stores, Data flow, Deployment
