# Fórmulas Implementadas en JIC-Geo

> Estado: **auditado contra el código fuente** — Junio 2026  
> Este documento refleja las fórmulas **realmente implementadas** en el backend, no las propuestas teóricas.

---

## 1. Modelos de Velocidad de Marcha

### 1.1 Tobler (1993) — Implementado ✅

**Archivo:** `backend/app/modules/vel/service.py:15-22`

```
W = 6 × e^(−3.5 × |S + 0.05|)
```

| Variable | Descripción |
|---|---|
| `W` | Velocidad de marcha (km/h) |
| `S` | Pendiente = dh/dx (adimensional, e.g. 0.10 = 10%) |

**Corrección off-path:** `W_offpath = W × 0.6`

**Corrección de Langmuir para descensos:** Implementada en `apply_langmuir()` (líneas 37-65):
- Pendiente suave (5°–12°): −10 min por cada 300 m → aumento de velocidad
- Pendiente abrupta (>12°): +10 min por cada 300 m → disminución de velocidad

### 1.2 Irmischer & Clarke (2018) — Implementado ✅

**Archivo:** `backend/app/modules/vel/service.py:25-34`

```
v(S) = [ 0.11 + e^( −(S + 0.0506)² / (2 × 0.2043²) ) ] × 3.6
```

| Variable | Descripción |
|---|---|
| `v(S)` | Velocidad (km/h) |
| `S` | Gradiente (adimensional) |

**Corrección off-path:** `v_offpath = v × 0.6`

### 1.3 Naismith (1892) — NO implementado ❌

Solo documentado en `docs/Formulas.md`. No hay código que lo use.

---

## 2. Costo Metabólico de Transporte (CoT)

### 2.1 Minetti et al. (2002) — Implementado ✅

**Archivo:** `backend/app/modules/met/service.py:35-57`

```
C(i) = 280.5i⁵ − 58.7i⁴ − 76.8i³ + 51.9i² + 19.6i + 2.5
```

| Variable | Descripción |
|---|---|
| `C(i)` | Costo Metabólico de Transporte (J/kg·m) |
| `i` | Gradiente topográfico (adimensional) |

**Dominio válido:** [−0.45, +0.45]  
**Fuera de dominio:** extrapolación lineal desde el boundary usando la derivada del polinomio.

### 2.2 Pandolf (1977) — Implementado ✅

**Archivo:** `backend/app/modules/met/service.py:60-83`

```
M = 1.5W + 2.0(W + L)(L/W)² + η(W + L)(1.5V² + 0.35VG)
```

| Variable | Descripción | Unidades |
|---|---|---|
| `M` | Tasa metabólica total | Vatios (W) |
| `W` | Peso corporal | kg |
| `L` | Carga externa (mochila) | kg |
| `V` | Velocidad de marcha | m/s |
| `G` | Pendiente del terreno | % (valor entero, e.g. 10 para 10%) |
| `η` | Coeficiente de terreno | adimensional |

**Nota importante:** En la implementación, `slope_pct` se pasa como `slope * 100` (de decimal a porcentaje). Ver `analysis.py:425`.

**Valores de η implementados:**

| Superficie | η |
|---|---|
| asphalt, pavement | 1.0 |
| dirt | 1.2 |
| scrub | 1.5 |
| dense_scrub | 1.8 |
| sand, mud, sand_mud | 2.1 |

---

## 3. Factores Climáticos

### 3.1 WBGT (Wet Bulb Globe Temperature) — Implementado ✅

**Archivo:** `backend/app/modules/cli/service.py:50-59`

```
WBGT = 0.7 × Tw + 0.2 × Tg + 0.1 × Ta
```

| Variable | Descripción |
|---|---|
| `Tw` | Temperatura de bulbo húmedo (aproximada con fórmula de Stull) |
| `Tg` | Temperatura de globo negro (aproximada desde radiación solar + UV) |
| `Ta` | Temperatura de aire ambiente |

**Tw (Stull):** Aproximación cuando no hay dato directo de bulbo húmedo (`approximate_wet_bulb_c`, líneas 21-36).

**Tg (aproximada):** `Ta + min(12.0, radiación/120.0 + max(0, UV-3) × 0.25)` (`approximate_globe_temperature_c`, líneas 39-47).

### 3.2 Deriva Cardiovascular (CV Drift) — Implementado ✅

**Archivo:** `backend/app/modules/cli/service.py:127-137`

```
si elapsed_time_min > 20 Y wbgt > 28.0:
    multiplier = e^(0.045 × (wbgt − 28.0) × exposure_h)
```

Donde `exposure_h = (elapsed_time_min − 20) / 60.0`

**Umbral:** WBGT > 28.0°C y tiempo > 20 minutos.  
**Tope:** 3.0x

### 3.3 Multiplicador de costo climático — Implementado ✅

**Archivo:** `backend/app/modules/cli/service.py:109-124` (Python)  
**Archivo:** `backend/alembic/versions/0003_climate_multiplier_and_edges_unique.py` (SQL)

```
multiplier = 1.0
si wbgt > 28.0:    multiplier *= 1.0 + 0.05 × (wbgt − 28.0)
si precip > 5.0 Y slope < −0.1763 (≈−10°):  multiplier *= 1.35
si canopy < 0.2 Y wbgt > 30.0:              multiplier *= 1.15
resultado = min(multiplier, 3.0)
```

---

## 4. Tribología / Fricción — Implementado parcialmente ⚠️

**NO hay fórmula de coeficiente de fricción dinámica (μ)** implementada.

Lo que **sí existe** es una penalización climática por lluvia en descenso (ver §3.3 arriba):
- Si `precip_mm > 5.0` y `slope_pct < −0.1763` (≈ −10°), se aplica un multiplicador de 1.35x al costo.

No hay cálculo de `F_friccion = μ × F_normal` ni modelo tribológico.

---

## 5. Capacidad de Carga Turística (Cifuentes) — Implementado ✅

**Archivo:** `backend/app/modules/rie/service.py:53-93`

### 5.1 Factor de corrección Cifuentes

```
Fc_i = 1 − (ml_i / mt)
```

### 5.2 Factores implementados

| Factor | Lógica de `ml_i` |
|---|---|
| `fc_precipitation` | `min(1.0, precip_mm / 40.0)` |
| `fc_erodability` | `min(1.0, |slope| × (1.5 si |slope| > 0.20 else 1.0))` si superficie vulnerable |
| `fc_anegamiento` | `0.7` si `surface_type == "mud"` y `precip_mm > 10.0`, sino `0.0` |
| `fc_brillo_solar` | `(1.0 − canopy_density)` si `uv_index >= 8.0`, sino `0.0` |

### 5.3 CCF (Capacidad de Carga Física)

```
CCF = (L / sp) × NV
NV = Hv / tv
```

Implementado en `calculate_ccf()` con defaults: `sp=2.0m`, `Hv=8h`.

### 5.4 CCR (Capacidad de Carga Real)

```
CCR = CCF × producto(Fc_i)
```

En la práctica se usa un solo factor de corrección derivado del riesgo máximo:
`correction = max(0.1, 1.0 − (max_risk / 100.0) × 0.6)`

### 5.5 CCE (Capacidad de Carga Efectiva) — NO implementado ❌

No hay cálculo de `CCE = CCR × CE` (Capacidad de Manejo).

---

## 6. Escala MIDE — Implementado ✅

**Archivo:** `backend/app/modules/rie/service.py:150-208`

### 6.1 Dimensiones

| Dimensión | Cálculo |
|---|---|
| **Severidad** (1–5) | Basado en `max_risk_score` y `wbgt`: ≥80 o WBGT≥32 → 5, ≥65 o WBGT≥30 → 4, ≥45 o WBGT≥28 → 3, ≥25 → 2 |
| **Orientación** (1–5) | `1 + ceil(off_path_ratio × 4)` |
| **Desplazamiento** (1–5) | Basado en `max_abs_slope`: ≥0.45 → 5, ≥0.30 → 4, ≥0.18 → 3, ≥0.08 → 2 |
| **Esfuerzo** (1–5) | `<1h→1, <3h→2, <5h→3, <8h→4, ≥8h→5` |

### 6.2 MIDE Global

```
MIDE = severity × 0.30 + orientation × 0.20 + displacement × 0.20 + effort × 0.30
```

Redondeado y acotado a [1, 5].

---

## 7. Índice de Riesgo por Segmento (AHP) — Implementado ✅

**Archivo:** `backend/app/modules/rie/service.py:96-134`

### 7.1 Pesos AHP (configurables)

**Archivo:** `backend/app/config.py:23-27`

| Factor | Peso default |
|---|---|
| Costo metabólico | 0.35 |
| Degradación de velocidad | 0.25 |
| Estrés climático | 0.25 |
| Fricción del terreno | 0.15 |

Los pesos se normalizan para sumar 1.0.

### 7.2 Componentes del score

```
metabolic_component   = min(1.0, max(cot/18.0, metabolic_rate_w/750.0))
velocity_degradation  = 1.0 − min(1.0, velocity_kmh / baseline_velocity_kmh)
climate_component     = min(1.0, ((cv_mult−1)/2.0) + ((cost_mult−1)/2.0))
terrain_component     = min(1.0, |slope|/0.45 + (0.15 si off_path))

score = w_metabolic × metabolic_component
      + w_velocity  × velocity_degradation
      + w_climate   × climate_component
      + w_terrain   × terrain_component

risk_score = round(score × 100), acotado a [0, 100]
```

---

## 8. Energía y Fatiga — Implementado ✅

### 8.1 Conversión energía

**Archivo:** `backend/app/api/v1/endpoints/analysis.py:432-434`

```
total_energy_J = metabolic_rate_w × time_s
kcal = total_energy_J / 4184.0
```

### 8.2 Tiempo hasta fatiga severa

**Archivo:** `backend/app/modules/met/service.py:104-127`

Basado en perfil de condición física:

| Fitness | Umbral kcal/kg |
|---|---|
| low | 5.0 |
| medium | 7.0 |
| high | 9.0 |
| athlete | 11.0 |

```
severe_fatigue_kcal = weight_kg × umbral_fitness
burn_rate_kcal_h = total_kcal / elapsed_time_h
time_to_fatigue_h = severe_fatigue_kcal / burn_rate_kcal_h
```

### 8.3 Fatiga excéntrica

**Archivo:** `backend/app/modules/met/service.py:86-91`

```
is_eccentric_fatigue = slope_pct < −0.10
```

---

## Resumen: ¿Qué está y qué no está?

| Fórmula / Modelo | En Formulas.md | Implementado | Archivo |
|---|---|---|---|
| **Tobler** | ✅ | ✅ | `vel/service.py` |
| **Irmischer & Clarke** | ✅ | ✅ | `vel/service.py` |
| **Langmuir (descensos)** | ✅ | ✅ | `vel/service.py` |
| **Naismith** | ✅ | ❌ | — |
| **Scarf (8:1)** | ✅ | ❌ | — |
| **Minetti CoT** | ✅ | ✅ | `met/service.py` |
| **Pandolf** | ✅ | ✅ | `met/service.py` |
| **WBGT** | ✅ | ✅ | `cli/service.py` |
| **Stull (wet-bulb approx)** | ❌ | ✅ | `cli/service.py` |
| **CV Drift** | ✅ | ✅ | `cli/service.py` |
| **Climate cost multiplier** | ❌ | ✅ | `cli/service.py` + SQL |
| **Tribología (μ)** | ✅ | ❌ | — |
| **Cifuentes CCF** | ✅ | ✅ | `rie/service.py` |
| **Cifuentes CCR** | ✅ | ✅ (simplificado) | `rie/service.py` |
| **Cifuentes CCE** | ✅ | ❌ | — |
| **MIDE** | ✅ | ✅ | `rie/service.py` |
| **AHP weights** | ✅ (mencionado) | ✅ (hardcoded defaults) | `config.py` |
| **Fatiga excéntrica** | ✅ (mencionado) | ✅ | `met/service.py` |
| **Energía kcal** | ❌ | ✅ | `analysis.py` |
| **Time to fatigue** | ❌ | ✅ | `met/service.py` |

### Notas clave

1. **AHP no es dinámico aún:** los pesos están hardcodeados en `config.py`. No hay implementación de pairwise comparisons ni recálculo dinámico de pesos.
2. **Tribología ausente:** no hay modelo de coeficiente de fricción μ. Solo hay una penalización empírica por lluvia en descenso (1.35x).
3. **Naismith no se usa:** es referencia histórica en el doc, pero el código solo usa Tobler o Irmischer.
4. **Stull no está documentado:** la aproximación de temperatura de bulbo húmedo con la fórmula de Stull está implementada pero no aparece en `Formulas.md`.
5. **Climate cost multiplier no está documentado:** la función que combina WBGT, precipitación y dosel forestal está en el código pero no en `Formulas.md`.
6. **CCR simplificado:** en lugar de multiplicar todos los Fc_i individuales, se usa un solo factor derivado del max_risk_score.
