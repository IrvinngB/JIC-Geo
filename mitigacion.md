# Mitigaciones Técnicas — Problemas Críticos del Índice de Riesgo

---

## Problema 1: GIGO con el DEM (afecta DAT-04, RUT-02)

### Raíz del problema

El gradiente `S = Δh / Δx` amplifica cualquier ruido en la señal de elevación.
Un spike de ±5 m en una ventana de 20 m produce `S = 0.25` irreal.
SRTM en zona boscosa densa tiene error vertical de ±10–16 m.

### Mitigaciones en capas

**Capa 1 — Extracción del DEM con interpolación bilinear (PostGIS)**

No usar nearest-neighbor al samplear el ráster. Bilinear suaviza los discontinuos del píxel:

```sql
-- MAL: extracción directa, un valor por píxel
ST_Value(rast, geom)

-- BIEN: interpolación bilinear entre píxeles vecinos
ST_Value(rast, geom, resample := 'Bilinear')
```

**Capa 2 — Suavizado de la serie de elevaciones (antes de calcular gradiente)**

Aplicar un filtro de ventana deslizante (media móvil o Savitzky-Golay) sobre el vector de elevaciones extraídas antes de derivar pendientes:

```python
import numpy as np
from scipy.signal import savgol_filter

def smooth_elevations(elevations: list[float], window: int = 5) -> list[float]:
    """
    Savitzky-Golay preserva mejor los picos reales que una media móvil simple.
    window debe ser impar y >= 5. Ajustar según densidad de puntos GPX.
    """
    if len(elevations) < window:
        return elevations
    return savgol_filter(elevations, window_length=window, polyorder=2).tolist()
```

**Capa 3 — Detección y reparación de spikes outlier**

Antes del suavizado, eliminar puntos con gradiente imposible para humanos (>75% = ~36°):

```python
MAX_PLAUSIBLE_GRADIENT = 0.75  # límite físico humano absoluto

def remove_elevation_spikes(points: list[dict]) -> list[dict]:
    clean = [points[0]]
    for i in range(1, len(points)):
        dh = points[i]["elevation"] - points[i-1]["elevation"]
        dx = points[i]["distance_from_prev"]
        if dx > 0 and abs(dh / dx) > MAX_PLAUSIBLE_GRADIENT:
            # Interpolación lineal entre vecino anterior y siguiente válido
            points[i]["elevation"] = (points[i-1]["elevation"] + points[min(i+1, len(points)-1)]["elevation"]) / 2
            points[i]["elevation_interpolated"] = True
        clean.append(points[i])
    return clean
```

**Capa 4 — Metadato de calidad por segmento**

Cada segmento debe cargar con su nivel de confianza de elevación:

| Fuente DEM | Resolución | Confianza en zona boscosa |
|---|---|---|
| SRTM 30m | Baja | ⚠️ Requiere suavizado agresivo |
| ALOS AW3D30 12.5m | Media | ⚠️ Requiere suavizado moderado |
| Copernicus DEM 10m | Media-Alta | ✅ Suavizado leve |
| LiDAR / UAV 1m | Alta | ✅ Suavizado mínimo |

### Requisitos nuevos

| ID | Requisito |
|---|---|
| DAT-09 | El sistema debe registrar la fuente y resolución del DEM usado por cada segmento como metadato de calidad. |
| DAT-10 | El sistema debe soportar al menos dos fuentes de DEM configurables y permitir priorización por resolución. |
| RUT-08 | El sistema debe aplicar interpolación bilinear al extraer elevaciones del ráster DEM (no nearest-neighbor). |
| RUT-09 | El sistema debe aplicar un filtro Savitzky-Golay (window configurable, default: 5 puntos) sobre la serie de elevaciones antes de calcular gradientes. |
| RUT-10 | El sistema debe detectar y reemplazar por interpolación lineal los puntos con gradiente implausible (`\|S\| > 0.75`) antes del suavizado. |
| RUT-11 | El sistema debe incluir en la respuesta de análisis la cantidad de puntos de elevación corregidos/interpolados como indicador de confianza del cálculo. |

---

## Problema 2: Rango válido de Minetti (afecta MET-01)

### Raíz del problema

El polinomio de grado 5 es no-monotónico fuera del dominio `[-0.45, +0.45]`.
Con `i = +0.60`:
```
C(0.60) = 280.5(0.60)⁵ − ... ≈ valores que no tienen sentido fisiológico
```
El término `280.5i⁵` domina y puede producir outputs negativos o astronómicos.

### Mitigaciones en capas

**Capa 1 — Clipping con flag de advertencia (primera línea de defensa)**

```python
MINETTI_MIN = -0.45
MINETTI_MAX = +0.45

def minetti_cot(i: float) -> tuple[float, bool]:
    """
    Retorna (costo_J_per_kg_m, fue_clipeado).
    El flag permite al caller registrar que el segmento es aproximado.
    """
    clipped_i = max(MINETTI_MIN, min(MINETTI_MAX, i))
    was_clipped = abs(clipped_i - i) > 1e-9

    cot = (280.5 * clipped_i**5
         -  58.7 * clipped_i**4
         -  76.8 * clipped_i**3
         +  51.9 * clipped_i**2
         +  19.6 * clipped_i
         +   2.5)

    return cot, was_clipped
```

**Capa 2 — Fallback con extrapolación lineal para gradientes extremos**

Si el gradiente real (post-suavizado) es genuinamente >0.45 (sí existen senderos así),
cliquearlo silenciosamente subestima el riesgo real. Mejor extrapolar usando la derivada
del polinomio en el límite del dominio:

```python
def minetti_safe(i: float) -> tuple[float, str]:
    """
    Dentro del dominio [-0.45, +0.45]: Minetti exacto.
    Fuera del dominio: extrapolación lineal desde el borde usando la derivada.
    Retorna (costo, método_usado).
    """
    if -0.45 <= i <= 0.45:
        return _minetti_poly(i), "exact"

    # Derivada del polinomio evaluada en el límite
    limit = 0.45 if i > 0 else -0.45
    slope = _minetti_derivative(limit)
    extrapolated = _minetti_poly(limit) + slope * (i - limit)
    return max(extrapolated, 0.0), "extrapolated"  # nunca negativo

def _minetti_derivative(i: float) -> float:
    """dC/di del polinomio de Minetti."""
    return (5 * 280.5 * i**4
          - 4 *  58.7 * i**3
          - 3 *  76.8 * i**2
          + 2 *  51.9 * i
          +      19.6)
```

**Capa 3 — Estrategia por defecto según origen del gradiente**

| Origen del gradiente extremo | Acción recomendada |
|---|---|
| Spike de GPS / error DEM | Debe haber sido eliminado en RUT-10 antes de llegar aquí |
| Terreno genuinamente extremo | Usar extrapolación lineal + marcar segmento como `risk_level = EXTREME` |
| Segmento de menos de 10 m con desnivel brusco | Fusionar con segmento vecino antes de calcular |

### Requisitos nuevos / actualizados

| ID | Requisito |
|---|---|
| MET-01 *(actualizado)* | El sistema debe calcular el CoT usando el polinomio de Minetti. Para `i` fuera de `[-0.45, +0.45]`, debe aplicar extrapolación lineal desde el límite del dominio usando la derivada del polinomio, nunca retornar un valor negativo. |
| MET-07 | El sistema debe incluir en la respuesta por segmento el campo `cot_method`: `"exact"`, `"extrapolated"`, o `"clipped"`. |
| MET-08 | El sistema debe agregar un campo `high_confidence_segments_pct` en el resumen de ruta indicando qué porcentaje de segmentos usó Minetti en su dominio exacto. |

---

## Problema 3: Cuello de botella en pgRouting (afecta GRF-05, GRF-06)

### Raíz del problema

```
10.000 aristas × UPDATE cada 10 min = escritura masiva constante en disco
```
Con grafos grandes y clima cambiante, persistir el costo climático en la tabla
de aristas es un anti-patrón de escritura.

### Estrategia de decisión por escala

```
Nodos en el grafo     →  Estrategia de costos climáticos
─────────────────────────────────────────────────────────
< 5.000 aristas       →  Persistir en tabla (simple, ok)
5.000 – 50.000        →  Multiplicador on-the-fly en la query SQL
> 50.000              →  Tabla de zonas climáticas (N zonas << N aristas)
```

### Mitigación recomendada: Multiplicador on-the-fly en la query

La topología y el `base_cost` son estáticos.
Los modificadores climáticos se calculan en la query del A*, no se persisten.

**Estructura de tablas:**

```sql
-- Tabla estática (nunca se actualiza después de la importación)
CREATE TABLE edges (
    id          BIGSERIAL PRIMARY KEY,
    source      BIGINT,
    target      BIGINT,
    geom        GEOMETRY(LINESTRING, 4326),
    base_cost         FLOAT,   -- Minetti + Tobler, condiciones ideales
    base_reverse_cost FLOAT,
    surface_type      TEXT,    -- 'asphalt', 'dirt', 'scrub', 'mud'
    canopy_density    FLOAT,   -- 0.0 – 1.0
    slope_pct         FLOAT
);

-- Tabla de zonas climáticas (filas = zonas del parque, no aristas)
-- Se actualiza cada N minutos. Puede tener 10 filas para un parque entero.
CREATE TABLE climate_zones (
    zone_id     TEXT PRIMARY KEY,
    geom        GEOMETRY(POLYGON, 4326),
    wbgt        FLOAT,
    precip_mm   FLOAT,
    uv_index    FLOAT,
    updated_at  TIMESTAMPTZ DEFAULT now()
);
```

**Query pgRouting con multiplicador on-the-fly:**

```sql
-- El JOIN climate_zones se resuelve en memoria durante la query.
-- Cero UPDATEs en edges. Solo se actualizan las N filas de climate_zones.

SELECT * FROM pgr_aStar(
  $$
    SELECT
      e.id,
      e.source,
      e.target,
      e.base_cost
        * climate_cost_multiplier(cz.wbgt, cz.precip_mm, e.slope_pct, e.canopy_density)
        AS cost,
      e.base_reverse_cost
        * climate_cost_multiplier(cz.wbgt, cz.precip_mm, -e.slope_pct, e.canopy_density)
        AS reverse_cost,
      ST_X(ST_StartPoint(e.geom)) AS x1,
      ST_Y(ST_StartPoint(e.geom)) AS y1,
      ST_X(ST_EndPoint(e.geom))   AS x2,
      ST_Y(ST_EndPoint(e.geom))   AS y2
    FROM edges e
    JOIN climate_zones cz
      ON ST_Intersects(e.geom, cz.geom)
  $$,
  :start_node, :end_node,
  directed := true
);
```

**Función de multiplicador (en PostgreSQL o Python según arquitectura):**

```sql
CREATE OR REPLACE FUNCTION climate_cost_multiplier(
    wbgt        FLOAT,
    precip_mm   FLOAT,
    slope_pct   FLOAT,
    canopy      FLOAT
) RETURNS FLOAT AS $$
DECLARE
    multiplier FLOAT := 1.0;
BEGIN
    -- CV Drift: WBGT alto aumenta costo temporal
    IF wbgt > 28.0 THEN
        multiplier := multiplier * (1.0 + 0.05 * (wbgt - 28.0));
    END IF;

    -- Lluvia + descenso: fricción reducida
    IF precip_mm > 5.0 AND slope_pct < -10.0 THEN
        multiplier := multiplier * 1.35;
    END IF;

    -- UV sin dosel
    IF canopy < 0.2 AND wbgt > 30.0 THEN
        multiplier := multiplier * 1.15;
    END IF;

    RETURN LEAST(multiplier, 3.0);  -- cap: nunca más de 3× el costo base
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;
```

> `IMMUTABLE PARALLEL SAFE` permite a PostgreSQL paralelizar el cálculo de la función
> en múltiples workers durante el scan de la tabla de aristas.

### Trade-offs de la estrategia

| Criterio | Persistir en disco | On-the-fly en query |
|---|---|---|
| Complejidad de implementación | Baja | Media |
| Carga de escritura en DB | Alta (UPDATEs masivos) | Nula |
| Carga de lectura en query | Baja (ya calculado) | Media (función en cada fila) |
| Consistencia temporal | Puede haber ventana stale | Siempre usa clima actual del JOIN |
| Escalabilidad a grafos grandes | ❌ | ✅ |
| Debuggeable / trazable | Fácil | Requiere logging explícito |

### Requisitos nuevos / actualizados

| ID | Requisito |
|---|---|
| GRF-05 *(actualizado)* | El sistema debe almacenar `base_cost` y `base_reverse_cost` estáticos por arista. Los modificadores climáticos **no** deben persistirse en la tabla de aristas. |
| GRF-06 *(actualizado)* | El sistema debe aplicar los modificadores climáticos como una función `climate_cost_multiplier` calculada on-the-fly durante la ejecución de la query pgRouting, haciendo JOIN con la tabla `climate_zones`. |
| GRF-08 | El sistema debe modelar el área geográfica cubierta en zonas climáticas (`climate_zones`), donde cada zona es un polígono que agrupa múltiples aristas bajo condiciones climáticas homogéneas. |
| GRF-09 | La función `climate_cost_multiplier` debe estar definida en PostgreSQL como `IMMUTABLE PARALLEL SAFE` para permitir ejecución paralela. |
| GRF-10 | El sistema debe aplicar un cap máximo al multiplicador climático (default: `3.0×`) para evitar que condiciones extremas produzcan costos computacionalmente irresolubles. |
| GRF-11 | El sistema debe registrar en el log de cada query el valor del multiplicador climático aplicado por zona, para trazabilidad y debugging. |

---

## Resumen de requisitos adicionales por problema

| Problema | Requisitos nuevos | Requisitos actualizados |
|---|---|---|
| GIGO DEM | DAT-09, DAT-10, RUT-08, RUT-09, RUT-10, RUT-11 | — |
| Rango Minetti | MET-07, MET-08 | MET-01 |
| Cuello pgRouting | GRF-08, GRF-09, GRF-10, GRF-11 | GRF-05, GRF-06 |

**Total acumulado: 84 requisitos atómicos.**