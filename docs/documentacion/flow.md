# Flujo del Sistema — RiskTrail

Este documento describe el flujo end-to-end de una solicitud de análisis de ruta, desde la carga del archivo en el frontend hasta la respuesta con métricas de riesgo. Para las reglas de arquitectura y convenciones de código, ver [`architecture.md`](./architecture.md).

---

## 1. Visión general

```
┌──────────────┐     HTTP/JSON      ┌──────────────────┐     SQL/PostGIS    ┌─────────────┐
│   Frontend    │ ─────────────────▶│      Backend       │ ──────────────────▶│  PostgreSQL  │
│  Vue 3 + Vite │◀───────────────── │  FastAPI (async)   │◀────────────────── │ PostGIS +    │
│  MapLibre GL  │                    │                    │                    │ pgRouting    │
└──────────────┘                    └──────────┬─────────┘                    └─────────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │  Open-Meteo API   │
                                        │ (clima externo)    │
                                        └─────────────────┘
```

Servicios orquestados con Docker Compose: `db` (PostGIS/pgRouting), `backend` (puerto 8000), `frontend` (puerto 5173, proxy a `backend` vía `VITE_API_PROXY_TARGET`).

---

## 2. Flujo paso a paso

### Paso 1 — Carga de ruta (frontend → backend)

El usuario sube un archivo GPX/GeoJSON desde `MapView.vue`. El store `routeStore.ts` ejecuta la acción de subida contra `POST /api/v1/routes/upload`, gestionando `isLoading` y `error`.

### Paso 2 — Segmentación (módulo RUT)

El backend divide la ruta en segmentos de longitud fija (50 m por defecto):
- Extrae elevación desde el DEM.
- Detecta anomalías de altura.
- Aplica filtro Savitzky-Golay para suavizar el perfil.
- Calcula pendiente por segmento (`Δh/Δx`, expresada en porcentaje).

Persiste los segmentos en la tabla `Segment` (geometría, elevación inicial/final, pendiente, tipo de superficie, densidad de dosel, fuente del DEM).

### Paso 3 — Velocidad de marcha (módulo VEL)

Para cada segmento, calcula la velocidad esperada usando el modelo **Tobler** o **Irmischer-Clarke**, según configuración:
- Aplica factor de penalización fuera de sendero (0.6).
- Aplica correcciones de Langmuir en descensos pronunciados.
- Incorpora el perfil del senderista (peso, carga, nivel de fitness) si se proporcionó.

### Paso 4 — Costo metabólico (módulo MET)

Calcula el gasto energético por segmento combinando dos modelos:
- **Minetti et al. (2002)**: costo de transporte (CoT, J/kg·m) en función de la pendiente.
- **Ecuación de Pandolf**: tasa metabólica (Watts):

  ```
  M = 1.5W + 2.0(W+L)(L/W)² + η(W+L)(1.5V² + 0.35VG)
  ```

  Donde `W` = peso corporal, `L` = carga, `V` = velocidad, `G` = pendiente (%), `η` = coeficiente de terreno.

### Paso 5 — Clima (módulo CLI)

- Si el análisis usa clima real, consulta la API externa **Open-Meteo** (temperatura, humedad, radiación solar/UV).
- Si usa clima simulado (`POST /{route_id}/simulate`), genera condiciones sintéticas y opcionalmente las compara contra datos reales.
- Calcula **WBGT** (Wet-Bulb Globe Temperature) combinando temperatura, humedad y radiación.
- Aplica multiplicadores de estrés cardiovascular y costo climático adicional en segmentos con exposición térmica prolongada.

### Paso 6 — Riesgo agregado (módulo RIE)

Pondera el riesgo por segmento usando factores AHP sobre:
- Costo metabólico.
- Degradación de velocidad.
- Estrés climático (WBGT).
- Fricción de terreno.

Aplica correcciones de Cifuentes (precipitación, erodabilidad, anegamiento, brillo solar) para ajustar el índice final.

### Paso 7 — Respuesta y persistencia

El endpoint retorna `BiomechanicalResponse`: resumen a nivel de ruta + arrays de métricas por segmento. El índice de riesgo se persiste y queda disponible vía `GET /{route_id}/risk` sin recalcular.

### Paso 8 — Render en el frontend

`routeStore.ts` almacena el resultado del análisis. `RouteMap.vue` (MapLibre GL) colorea los segmentos según su nivel de riesgo sobre el mapa interactivo en la ruta `/mapa`. Los composables exponen lógica reutilizable para el perfil del senderista y el simulador de clima sin acceder al DOM directamente.

---

## 3. Endpoints principales

| Método | Ruta | Función |
|---|---|---|
| `POST` | `/api/v1/routes/upload` | Carga el archivo GPX/GeoJSON |
| `POST` | `/api/v1/routes/{id}/process` | Ejecuta segmentación (RUT) |
| `POST` | `/api/v1/routes/analyze` | Carga + análisis biomecánico en un solo paso |
| `POST` | `/api/v1/routes/{id}/biomechanical` | Reanaliza con perfil de senderista personalizado |
| `POST` | `/api/v1/routes/{id}/simulate` | Analiza con clima simulado (real vs. simulado) |
| `GET` | `/api/v1/routes/{id}/risk` | Devuelve el índice de riesgo persistido |
| `GET` | `/api/v1/routes/{id}/graph` | Topología de la ruta para ruteo dinámico (pgRouting) |

---

## 4. Referencias de implementación

- Segmentación y pendiente: `backend/app/modules/rut/service.py`
- Velocidad (Tobler/Irmischer-Clarke): `backend/app/modules/vel/service.py`
- Pandolf y Minetti: `backend/app/modules/met/service.py`
- WBGT y clima: `backend/app/modules/cli/service.py`
- Riesgo agregado (AHP, Cifuentes): `backend/app/modules/rie/service.py`
- Endpoints de análisis: `backend/app/api/v1/endpoints/analysis.py`
- Modelos de datos: `backend/app/db/models.py`
- Store del frontend: `frontend/src/stores/routeStore.ts`
- Vista principal del mapa: `frontend/src/views/MapView.vue` (ruta `/mapa`)
