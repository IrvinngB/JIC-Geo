# Backlog de Issues — JIC-Geo

Este documento define los issues de GitHub que representan las fases restantes del proyecto JIC-Geo. Cada issue sigue la convención de Conventional Commits e incluye descripción detallada, criterios de aceptación (Definición de Hecho) y módulos afectados.

---

## Creación Rápida con GitHub CLI

Podés crear los issues directamente usando `gh`:
```bash
gh issue create \
  --title "feat(dat): implementar ingesta espacial GPX/GeoJSON y modelos DEM" \
  --body-file docs/issues.md \
  --label "enhancement,status:needs-review"
```

---

## Backlog por Fase

### Issue 1: `feat(dat): implementar ingesta espacial GPX/GeoJSON y registro de fuentes DEM`
* **Fase:** 1 — DAT Ingesta de Datos Espaciales
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Configurar los modelos de base de datos espacial y el pipeline de ingesta de rutas. El sistema debe aceptar archivos GPX o GeoJSON, parsear sus propiedades geométricas y almacenarlas como LineString 3D (3DZ, SRID 4326) en PostGIS. Además, configurar la tabla de registro de fuentes DEM para preparar la extracción de elevaciones.

#### Criterios de Aceptación
- [ ] Implementar modelos ORM `Route`, `Segment`, `SegmentCosts` y `DEMSource` en `backend/app/db/models.py`.
- [ ] Crear migración Alembic que verifique índices espaciales (`idx_routes_geom` e `idx_segments_geom` con GIST).
- [ ] Implementar servicio de parseo de archivos GPX y GeoJSON en `backend/app/modules/dat/service.py`.
- [ ] Exponer `POST /routes/upload` que reciba un archivo GPX o GeoJSON, lo parsee y persista en la tabla `routes` con geometría 3DZ.
- [ ] Test de integración que suba un GPX de muestra y valide que se almacenó con coordenadas Z.

---

### Issue 2: `feat(rut): implementar segmentación de rutas, interpolación DEM y suavizado de gradiente`
* **Fase:** 2 — RUT Segmentación y Gradiente
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Implementar el pipeline de procesamiento de rutas. Las rutas deben segmentarse en tramos de igual distancia (por defecto 100m). Para cada punto del segmento, obtener la elevación limpia del DEM usando interpolación bilineal. Implementar filtros de reducción de ruido (Savitzky-Golay) para suavizar elevaciones, detectar spikes de gradiente ($|S| > 0.75$) y calcular el gradiente por segmento ($S = \Delta h / \Delta x$).

#### Criterios de Aceptación
- [ ] Implementar función de segmentación en `backend/app/modules/rut/service.py` que divida las líneas en sub-tramos de 100m.
- [ ] Implementar query de interpolación bilineal para extraer elevación desde `postgis_raster`.
- [ ] Integrar `scipy.signal.savgol_filter` para el suavizado de elevaciones.
- [ ] Implementar detección de spikes y marcar puntos corregidos en `elevation_interpolated`.
- [ ] Calcular gradiente ($S$) y acumulación de desniveles (positivo y negativo).
- [ ] Tests unitarios para el suavizado de elevaciones y la lógica de segmentación.

---

### Issue 3: `feat(vel,met,prf): implementar modelos biomecánicos (Tobler, Minetti/Pandolf) y perfil del excursionista`
* **Fase:** 3 — VEL + MET + PRF Motor Biomecánico
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Implementar los cálculos de movimiento humano y gasto energético. Incluye la función de senderismo de Tobler (y la alternativa Irmischer-Clarke) para la estimación de velocidad según la pendiente, el Costo de Transporte de Minetti (CoT) con extrapolación lineal segura para pendientes pronunciadas, y la fórmula de tasa metabólica de Pandolf. Incorporar el perfil del excursionista (peso, carga, nivel de condición física).

#### Criterios de Aceptación
- [ ] Implementar funciones de velocidad de Tobler e Irmischer-Clarke en `backend/app/modules/vel/service.py`.
- [ ] Implementar la fórmula de Minetti con extrapolación lineal segura ($|S| > 0.60$) en `backend/app/modules/met/service.py`.
- [ ] Implementar la fórmula de tasa metabólica de Pandolf (Watts) con lookup del factor de terreno ($\eta$).
- [ ] Agregar validación Pydantic en `HikerProfile` que garantice que la carga < peso corporal.
- [ ] Verificar los cálculos contra los valores de referencia de `Formulas.md` (ej: CoT en terreno plano $\approx 2.5$ J/kg·m).

---

### Issue 4: `feat(cli,sim): implementar servicio meteorológico, cálculo WBGT y escenarios de simulación`
* **Fase:** 4 — CLI + SIM Integración Climática
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Integrar los factores meteorológicos. Obtener datos climáticos en tiempo real (de Open-Meteo), aproximar la Temperatura de Globo de Bulbo Húmedo (WBGT) con temperatura, humedad y radiación solar, y aplicar degradación de velocidad por estrés cardiovascular. Permitir override manual del clima mediante simulaciones y configurar los escenarios predefinidos (lluvia intensa, calor extremo, noche, etc.).

#### Criterios de Aceptación
- [ ] Configurar cliente para solicitar datos climáticos desde Open-Meteo en `backend/app/modules/cli/service.py`.
- [ ] Implementar la fórmula de aproximación WBGT.
- [ ] Crear tabla `climate_zones` en la DB y configurar TTL de caché.
- [ ] Implementar el servicio de simulación que inyecte parámetros climáticos personalizados.
- [ ] Implementar los 5 escenarios predefinidos (`dry`, `light_rain`, `heavy_rain`, `extreme_heat`, `night`).

---

### Issue 5: `feat(rie): implementar motor de score de riesgo e índice MIDE`
* **Fase:** 5 — RIE Índice de Riesgo y MIDE
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Combinar variables fisiológicas, de velocidad y climáticas en un score de riesgo único por segmento usando pesos AHP (Proceso Analítico Jerárquico). Traducir las métricas de riesgo agregadas a la escala MIDE española estándar (1-5 en 4 dimensiones: Severidad, Orientación, Desplazamiento y Esfuerzo). Identificar el top 10% de segmentos de mayor riesgo para alertas.

#### Criterios de Aceptación
- [ ] Implementar cálculo de Risk Score por segmento en `backend/app/modules/rie/service.py` combinando costo metabólico, degradación de velocidad, clima y terreno.
- [ ] Configurar pesos AHP ajustables.
- [ ] Implementar mapeador del índice MIDE (4 dimensiones) tanto a nivel de segmento como de ruta completa.
- [ ] Filtrar y marcar el top 10% de segmentos de mayor riesgo de la ruta.
- [ ] Tests unitarios que verifiquen las restricciones de las dimensiones MIDE.

---

### Issue 6: `feat(grf): implementar topología pgRouting y grafo de enrutamiento dinámico`
* **Fase:** 6 — GRF Grafo y Enrutamiento pgRouting
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Construir la topología de rutas y configurar pgRouting. Transformar los segmentos de ruta en aristas con nodos para soportar análisis de red. Implementar queries de enrutamiento dinámico usando A* (o Dijkstra como alternativa) con costos asimétricos (costo ascenso ≠ costo descenso). Incorporar el multiplicador climático de costo como función inmutable de la base de datos.

#### Criterios de Aceptación
- [ ] Crear tabla `edges` y ejecutar `pgr_createTopology` para construir los nodos.
- [ ] Implementar `climate_cost_multiplier` como función SQL `IMMUTABLE PARALLEL SAFE` con tope máximo de 3x.
- [ ] Implementar queries de búsqueda de ruta usando A* Bidireccional en `backend/app/modules/grf/repository.py`.
- [ ] Soportar waypoints intermedios y modificación de costos on-the-fly.

---

### Issue 7: `feat(api): exponer endpoints REST para análisis de rutas, simulaciones y enrutamiento óptimo`
* **Fase:** 7 — API Endpoints REST
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Exponer todas las capacidades del backend via endpoints REST limpios de FastAPI. Incluye upload y análisis de rutas, triggers de simulación, recuperación de datos de segmentos y queries de pathfinding óptimo. Asegurar payloads con schemas de validación Pydantic.

#### Criterios de Aceptación
- [ ] Implementar `POST /routes/analyze` (maneja upload, procesamiento y retorno de segmentos + índices MIDE).
- [ ] Implementar `POST /routes/{route_id}/simulate` para comparar clima real vs. simulado.
- [ ] Implementar `POST /routes/optimal-path` para ejecutar queries de pgRouting entre puntos.
- [ ] Documentar todos los endpoints usando la documentación OpenAPI/Swagger generada por FastAPI.

---

### Issue 8: `feat(map): construir mapa interactivo de rutas y dashboard del perfil del excursionista`
* **Fase:** 8 — MAP Mapa Web Interactivo (Vue 3)
* **Labels:** `enhancement`, `status:needs-review`

#### Descripción
Implementar la interfaz de usuario final. Integrar MapLibre GL JS para mostrar las rutas coloreadas por score de riesgo (verde → amarillo → rojo). Agregar popups con detalles de segmento, un componente de file uploader, un panel lateral con el formulario del perfil del excursionista y sliders de clima para simulación manual.

#### Criterios de Aceptación
- [ ] Configurar MapLibre GL JS y renderizar los segmentos GeoJSON de la ruta coloreados por score de riesgo.
- [ ] Implementar eventos de click en segmentos que muestren métricas detalladas en un popup.
- [ ] Agregar formulario de perfil del excursionista que actualice el estado en Pinia de forma dinámica.
- [ ] Integrar sliders de clima que disparen simulaciones reactivas sin recargar la página.
- [ ] Mostrar indicadores MIDE de 4 dimensiones y marcar el top 10% de segmentos de riesgo en el mapa.
