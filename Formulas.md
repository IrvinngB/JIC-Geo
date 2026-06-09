# Fórmulas y Consideraciones: Índice Dinámico de Riesgo en Senderismo

> Compilación técnica extraída de la revisión de literatura científica.  
> Organizada por módulo funcional para implementación backend.

---

## 1. Modelos de Velocidad de Marcha

### 1.1 Regla de Naismith (1892) — Base histórica / heurística

**Velocidad base:**
```
v_base = 5 km/h  (terreno llano)
```

**Penalización por ascenso:**
```
t_extra = 1 hora por cada 600 m de desnivel positivo
```

**Factor de equivalencia de Scarf:**
```
8 unidades de distancia plana ≈ 1 unidad de escalada vertical
(relación 8:1)
```

**Correcciones de Langmuir para descensos:**
```
pendiente suave  (5° – 12°):  −10 min por cada 300 m de descenso
pendiente abrupta (> 12°):   +10 min por cada 300 m de descenso
```

> **Limitación crítica:** Naismith asume que la velocidad de descenso = velocidad en plano.  
> No usar como único modelo. Usar como cota inferior de estimación.

---

### 1.2 Función de Excursionismo de Tobler (1993) — Modelo exponencial continuo

```
W = 6 × e^(−3.5 × |S + 0.05|)
```

| Variable | Descripción | Unidades |
|---|---|---|
| `W` | Velocidad de marcha | km/h |
| `S` | Pendiente = dh / dx (diferencial de elevación / distancia horizontal) | adimensional |

**Propiedades clave:**
- Velocidad máxima teórica ≈ **6 km/h** en pendiente de **−5% (−2.86°)**
- En terreno plano (S = 0): W ≈ 5 km/h
- La velocidad cae **exponencialmente** a ambos lados del óptimo

**Corrección para terreno no consolidado (off-path):**
```
W_offpath = 0.6 × W
```

---

### 1.3 Función Gaussiana de Irmischer & Clarke (2018) — Optimización moderna

Para **hombres en sendero estructurado (on-path)**:

```
v(S) = [ 0.11 + e^( −(S + 0.0506)² / (2 × 0.2043²) ) ] × 3.6
```

| Variable | Descripción | Unidades |
|---|---|---|
| `v(S)` | Velocidad | km/h |
| `S` | Gradiente | % (como decimal, e.g. 10% = 0.10) |

**Ventajas sobre Tobler:**
- Evita velocidades irreales en ángulos extremos
- Curvas más apegadas a excursionistas reales y ecoturistas
- Separación por género y tipo de vía (on-path / off-path)

> **Referencia validada por Strava (Campbell et al., 2019):** con 421,247 actividades GPS se determinó que **funciones de Lorentz asimétricas** son el mejor ajuste por percentiles de condición física.  
> Considerar segmentar usuarios por nivel atlético para mayor precisión del riesgo temporal.

---

## 2. Costo Metabólico de Transporte (CoT)

### 2.1 Polinomio de Minetti et al. (2002) — Costo energético por gradiente

```
C(i) = 280.5i⁵ − 58.7i⁴ − 76.8i³ + 51.9i² + 19.6i + 2.5
```

| Variable | Descripción | Unidades |
|---|---|---|
| `C(i)` | Costo Metabólico de Transporte | J / (kg·m) |
| `i` | Gradiente topográfico | adimensional (e.g. 0.10 = 10%) |

**Valores de referencia para calibración:**

| Gradiente | Situación | C(i) aproximado (J/kg·m) |
|---|---|---|
| 0 | Terreno plano | ~1.64 |
| −0.10 | Descenso óptimo (~−5.7°) | ~0.81 ← mínimo absoluto |
| −0.45 | Descenso extremo | ~3.46 |
| +0.45 | Ascenso extremo | ~17.33 |

**Consideraciones:**
- La curva es **parabólica asimétrica en "J"** — no es lineal
- El descenso pronunciado (< −0.10) **aumenta paradójicamente** el costo porque los cuádriceps trabajan en contracción excéntrica
- Rango validado experimentalmente: gradiente entre **−0.45 y +0.45**

---

### 2.2 Ecuación de Pandolf (1977, adaptada por Santee) — Carga externa

```
M = 1.5W + 2.0(W + L)(L/W)² + η(W + L)(1.5V² + 0.35VG)
```

| Variable | Descripción | Unidades |
|---|---|---|
| `M` | Tasa metabólica total | Vatios (W) |
| `W` | Peso corporal del excursionista | kg |
| `L` | Carga externa (mochila) | kg |
| `V` | Velocidad de marcha | m/s |
| `G` | Pendiente del terreno | % |
| `η` | Coeficiente de terreno | adimensional (ver tabla) |

**Valores del coeficiente de terreno `η`:**

| Tipo de superficie | η |
|---|---|
| Asfalto / pavimento | 1.0 |
| Camino de tierra firme | 1.2 |
| Maleza ligera / sendero marcado | 1.5 |
| Maleza densa / sin sendero | ~1.8 |
| Arena suelta / barro | 2.1 |

> **Integración recomendada:** usar Tobler/Irmischer para proyectar velocidad → pasar esa velocidad a Pandolf para calcular consumo metabólico total → usar Minetti para modular el costo por gradiente en cada segmento.

---

## 3. Factores Climáticos y Fisiológicos (Clima Tropical)

### 3.1 Deriva Cardiovascular (CV Drift)

**Umbral de activación:**
```
t_cvdrift = 20 minutos de ejercicio submáximo continuo
bajo condiciones de estrés térmico significativo (WBGT alto)
```

**Comportamiento:**
- Frecuencia cardíaca (HR) **aumenta progresivamente**
- Volumen sistólico (SV) **disminuye**
- El producto (HR × SV = gasto cardíaco) se degrada

**Efecto sobre el VO₂max:**
```
ΔVO₂max = f(deshidratación, hipertermia)
Δtemperatura central > 0.5 °C/h bajo exposición solar directa
```

**Implementación en el índice de riesgo:**
```
si (tiempo_marcha_continua > 20 min) Y (WBGT > umbral_critico):
    costo_temporal += multiplicador_exponencial(t)
    nivel_alerta_médica += incremento(t)
```

---

### 3.2 Índice WBGT (Wet Bulb Globe Temperature)

El WBGT integra temperatura, humedad y radiación solar para cuantificar estrés térmico. Es la variable de entrada clave desde la API meteorológica.

```
WBGT = 0.7 × Tw + 0.2 × Tg + 0.1 × Ta
```

| Variable | Descripción |
|---|---|
| `Tw` | Temperatura de bulbo húmedo (humedad absoluta) |
| `Tg` | Temperatura de globo negro (radiación solar) |
| `Ta` | Temperatura de aire ambiente |

> **Consideración crítica:** el factor limitante en clima tropical es la **humedad absoluta** (presión de vapor del aire), no la humedad relativa. Si la presión de vapor del aire > presión de vapor de la piel, el sudor no se evapora y el enfriamiento se anula.

---

### 3.3 Tribología: Coeficiente de Fricción Dinámica

**Condición de resbalón:**
```
F_horizontal > F_friccion
```

**Fricción disponible:**
```
F_friccion = μ × F_normal
```

**Penalización algorítmica por lluvia:**
```
si (precipitación_reciente == true) Y (pendiente > 10°):
    μ_efectivo = μ_base × factor_lluvia  (factor < 1)
    costo_segmento_descenso += penalizacion_triologica
```

> Aplicar a partir de los **30 minutos de descenso prolongado** bajo fatiga acumulada, ya que la fuerza de recuperación post-resbalón se vuelve inviable para músculo fatigado.

---

## 4. Capacidad de Carga Turística — Metodología Cifuentes

### 4.1 Capacidad de Carga Física (CCF)

```
CCF = (L / sp) × NV
```

| Variable | Descripción |
|---|---|
| `L` | Longitud del sendero disponible (m) |
| `sp` | Espacio mínimo por grupo (m/grupo) |
| `NV` | Número de veces que el sendero puede ser visitado por día |

```
NV = Hv / tv
```

| Variable | Descripción |
|---|---|
| `Hv` | Horario de visita (horas disponibles/día) |
| `tv` | Tiempo necesario para recorrer el sendero (horas) |

---

### 4.2 Factores de Corrección (Fc)

Cada factor reduce la CCF según la presencia de variables limitantes:

```
Fc_i = 1 − (ml_i / mt)
```

| Variable | Descripción |
|---|---|
| `ml_i` | Magnitud limitante del factor i (horas, metros, etc.) |
| `mt` | Magnitud total del mismo parámetro |

**Factores aplicables:**

| Factor | Variable de entrada | Lógica |
|---|---|---|
| **Fc_precipitación** | Horas/año de lluvia limitante | Horas en que la marcha es inviable |
| **Fc_erodabilidad** | % del sendero con arcilla + pendiente >10-20% | Laderas vulnerables a pisada; penalización ×1.5 en pendiente severa |
| **Fc_anegamiento** | % del sendero con estancamiento de agua | Sectores que dificultan la locomoción |
| **Fc_brillo solar** | % del recorrido sin cobertura forestal | Estrés térmico por exposición solar directa |

---

### 4.3 Capacidad de Carga Real (CCR)

```
CCR = CCF × Fc_1 × Fc_2 × Fc_3 × ... × Fc_n
```

> Equivale a multiplicar la CCF por el **producto de todos los factores de corrección**.

---

### 4.4 Capacidad de Carga Efectiva (CCE)

```
CCE = CCR × CE
```

Donde `CE` es la Capacidad de Manejo de la administración del parque (recursos, personal, infraestructura).

---

## 5. Acciones Dinámicas sobre el Grafo (pgRouting)

| Parámetro API (entrada) | Variable Biomecánica afectada | Acción sobre el grafo |
|---|---|---|
| WBGT alto + alta humedad | Deriva cardiovascular, HR escalada | Multiplicador exponencial en `cost` temporal después de >20 min continuos |
| Precipitación intensa reciente | Coeficiente de fricción μ, riesgo de resbalón | Aumento de `cost` en segmentos de descenso con inclinación >10° |
| Alerta UV alta | Estrés térmico por radiación (sin dosel) | Penalización AHP en segmentos con baja densidad de cobertura forestal |
| Vegetación densa (LiDAR/UAV) | Velocidad reducida (off-path) | Factor `η` elevado en Pandolf + corrección ×0.6 en Tobler |

**Estructura de costos asimétricos en pgRouting:**
```sql
-- Los valores de cost y reverse_cost son distintos porque subir ≠ bajar
cost         = C(+i) de Minetti  × multiplicadores_ambientales
reverse_cost = C(−i) de Minetti  × multiplicadores_ambientales
```

---

## 6. Escala MIDE (Método de Información de Excursiones)

Dimensiones evaluadas del 1 al 5:

| Dimensión | Nivel 1 | Nivel 5 |
|---|---|---|
| **Severidad del medio** | Sin riesgos objetivos | Desprendimientos, aislamiento >1h de socorro |
| **Orientación en el itinerario** | Ruta asfaltada señalizada | Navegación técnica fuera de traza, sin referencias |
| **Dificultad de desplazamiento** | Superficie lisa y horizontal | Trepadas, uso de manos, riesgo de avalancha |
| **Cantidad de esfuerzo** | <1 hora continua | >10 horas continuas |

> El Índice Dinámico de Riesgo debe **traducir sus resultados algorítmicos a esta escala** como salida final para el usuario. El MIDE actúa como capa de presentación sobre los cálculos de Minetti, Pandolf, Tobler y Cifuentes.

---

## 7. Consideraciones de Implementación Backend

### 7.1 Coordenadas y DEM

- Almacenar rutas en **3DZ** (lat, lon, elevación) con PostGIS
- Extraer gradiente `S` automáticamente cruzando trazas GPX con el DEM ráster
- En zonas con dosel denso: priorizar datos **LiDAR o UAV fotogramétrico** sobre SRTM (SRTM subestima pendiente real bajo cobertura arbórea densa)

### 7.2 Separación arquitectónica de la topología

```
Tabla estática:   geometrías espaciales (vértices y aristas de la red)
Tabla dinámica:   atributos de costo  ← se actualiza en tiempo real vía API
```

Esta separación permite recalcular rutas sin tocar la geometría base.

### 7.3 Algoritmos de enrutamiento sugeridos

| Algoritmo | Uso recomendado |
|---|---|
| **Dijkstra** | Rutas exactas, grafos sin estimación heurística |
| **A\* Bidireccional** | Rutas largas, rendimiento optimizado con heurística de distancia |
| **TSP** | Rutas de múltiples puntos de interés o evacuación multi-parada |

### 7.4 Proceso de jerarquía analítica (AHP) para pesos de riesgo

Los factores de riesgo (clima, pendiente, vegetación, fatiga) deben combinarse con pesos normalizados vía AHP. Permite que el sistema actualice la importancia relativa de cada factor según condiciones del parque o perfil del excursionista.

### 7.5 Trigger de recálculo automático

```
Evento: API meteorológica notifica precipitación o WBGT > umbral
→ UPDATE tabla_costos SET cost = calcular_nuevo_costo(...)
→ pgRouting recalcula automáticamente en la próxima consulta
```

---

## 8. Resumen de Variables Críticas por Módulo

| Módulo | Variables de entrada clave | Salida |
|---|---|---|
| Velocidad | Pendiente `S`, tipo de terreno | km/h (Tobler / Irmischer) |
| Costo energético | Gradiente `i`, peso `W`, carga `L`, velocidad `V`, `η` | J/(kg·m) y Vatios (Minetti + Pandolf) |
| Fatiga térmica | WBGT, tiempo continuo, humedad absoluta | Multiplicador temporal, nivel de alerta |
| Tribología | Precipitación, pendiente, tiempo en descenso | Factor de penalización en segmentos |
| Capacidad | Longitud, Fc ambientales, horario | CCF → CCR → CCE (máx. excursionistas/día) |
| Presentación | Todos los anteriores combinados | Nivel MIDE 1–5 |