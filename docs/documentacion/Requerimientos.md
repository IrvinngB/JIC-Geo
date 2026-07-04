# Requisitos Atómicos — Índice Dinámico de Riesgo (Senderismo)

> Plataforma: API REST + Mapa web interactivo  
> Perfil de excursionista: configurable (peso, carga, condición física)  
> Clima: tiempo real + modo simulación

---

## Convenciones

| Prefijo | Dominio |
|---|---|
| `DAT` | Datos espaciales e ingesta |
| `RUT` | Procesamiento de rutas |
| `VEL` | Modelado de velocidad |
| `MET` | Costo metabólico |
| `PRF` | Perfil del excursionista |
| `CLI` | Integración climática |
| `RIE` | Cálculo del índice de riesgo |
| `GRF` | Grafo y enrutamiento (pgRouting) |
| `API` | Endpoints REST |
| `SIM` | Modo simulación |
| `MAP` | Mapa web interactivo |

---

## DAT — Datos Espaciales

| ID | Requisito |
|---|---|
| DAT-01 | El sistema debe almacenar geometrías de rutas en formato 3DZ (latitud, longitud, elevación) usando PostGIS. |
| DAT-02 | El sistema debe aceptar la importación de rutas en formato GPX. |
| DAT-03 | El sistema debe aceptar la importación de rutas en formato GeoJSON. |
| DAT-04 | El sistema debe almacenar al menos un Modelo Digital de Elevación (DEM) en formato ráster dentro de PostGIS Raster. |
| DAT-05 | El sistema debe indexar todas las geometrías con índice R-Tree (GiST) para consultas espaciales eficientes. |
| DAT-06 | El sistema debe separar la tabla de geometrías estáticas de la tabla de atributos de costo dinámicos. |
| DAT-07 | El sistema debe permitir registrar el tipo de superficie de cada segmento de ruta (asfalto, tierra, maleza, barro, arena). |
| DAT-08 | El sistema debe permitir registrar el porcentaje estimado de cobertura forestal (dosel) por segmento. |

---

## RUT — Procesamiento de Rutas

| ID | Requisito |
|---|---|
| RUT-01 | El sistema debe segmentar automáticamente una ruta importada en tramos de longitud configurable (default: 100 m). |
| RUT-02 | El sistema debe calcular el gradiente topográfico `S = Δh / Δx` para cada segmento cruzando la traza GPX con el DEM ráster. |
| RUT-03 | El sistema debe detectar y marcar los segmentos con gradiente positivo (ascenso) y negativo (descenso) de forma independiente. |
| RUT-04 | El sistema debe calcular la distancia horizontal real (no euclidiana plana) de cada segmento. |
| RUT-05 | El sistema debe calcular el desnivel acumulado positivo total de una ruta completa. |
| RUT-06 | El sistema debe calcular el desnivel acumulado negativo total de una ruta completa. |
| RUT-07 | El sistema debe persistir los segmentos calculados como aristas en la topología del grafo de pgRouting. |

---

## VEL — Modelado de Velocidad

| ID | Requisito |
|---|---|
| VEL-01 | El sistema debe calcular la velocidad estimada por segmento usando la Función de Tobler: `W = 6 × e^(−3.5 × \|S + 0.05\|)`. |
| VEL-02 | El sistema debe calcular la velocidad usando la función gaussiana de Irmischer-Clarke como alternativa a Tobler. |
| VEL-03 | El sistema debe exponer un parámetro de selección de modelo de velocidad (Tobler / Irmischer-Clarke) por solicitud. |
| VEL-04 | El sistema debe aplicar el factor reductor `×0.6` sobre la velocidad calculada cuando el segmento está marcado como off-path (sin sendero consolidado). |
| VEL-05 | El sistema debe aplicar las correcciones de Langmuir sobre segmentos de descenso: `−10 min / 300 m` en pendiente 5°–12°, `+10 min / 300 m` en pendiente >12°. |
| VEL-06 | El sistema debe devolver la velocidad en km/h por segmento como parte de la respuesta de análisis de ruta. |

---

## MET — Costo Metabólico

| ID | Requisito |
|---|---|
| MET-01 | El sistema debe calcular el Costo Metabólico de Transporte (CoT) por segmento usando el polinomio de Minetti: `C(i) = 280.5i⁵ − 58.7i⁴ − 76.8i³ + 51.9i² + 19.6i + 2.5`. |
| MET-02 | El sistema debe calcular la tasa metabólica total con la ecuación de Pandolf: `M = 1.5W + 2.0(W+L)(L/W)² + η(W+L)(1.5V² + 0.35VG)`. |
| MET-03 | El sistema debe usar el coeficiente de terreno `η` asignado al tipo de superficie del segmento en el cálculo de Pandolf. |
| MET-04 | El sistema debe acumular el gasto energético total de la ruta en kilocalorías. |
| MET-05 | El sistema debe calcular y exponer el tiempo proyectado antes de fatiga severa basado en el perfil del excursionista y el gasto acumulado. |
| MET-06 | El sistema debe marcar los segmentos con gradiente < −0.10 como de **fatiga excéntrica** (cuádriceps), diferenciándolos de fatiga metabólica por ascenso. |

---

## PRF — Perfil del Excursionista

| ID | Requisito |
|---|---|
| PRF-01 | El sistema debe aceptar el peso corporal del excursionista `W` en kg como parámetro de entrada. |
| PRF-02 | El sistema debe aceptar el peso de la carga externa (mochila) `L` en kg como parámetro de entrada. |
| PRF-03 | El sistema debe aceptar el nivel de condición física del excursionista mediante una escala categórica (Bajo / Medio / Alto / Atleta). |
| PRF-04 | El sistema debe mapear el nivel de condición física a un percentil de velocidad para seleccionar la curva de Lorentz correspondiente. |
| PRF-05 | El sistema debe usar valores por defecto para excursionista promedio si no se proveen parámetros de perfil: `W = 70 kg`, `L = 10 kg`, nivel = Medio. |
| PRF-06 | El sistema debe validar que `W > 0`, `L >= 0` y que `L < W` antes de procesar cualquier cálculo. |

---

## CLI — Integración Climática

| ID | Requisito |
|---|---|
| CLI-01 | El sistema debe consumir datos de temperatura, humedad y precipitación desde una API meteorológica externa para la ubicación geográfica de la ruta. |
| CLI-02 | El sistema debe calcular el índice WBGT a partir de los datos recibidos: `WBGT = 0.7×Tw + 0.2×Tg + 0.1×Ta`. |
| CLI-03 | El sistema debe definir un umbral de WBGT configurable a partir del cual se activa la penalización por deriva cardiovascular. |
| CLI-04 | El sistema debe aplicar un multiplicador exponencial de costo temporal en segmentos cuando: `tiempo_continuo > 20 min` Y `WBGT > umbral_crítico`. |
| CLI-05 | El sistema debe aplicar una penalización de fricción en segmentos de descenso con pendiente >10° cuando la API reporta precipitación reciente. |
| CLI-06 | El sistema debe aplicar una penalización por radiación UV en segmentos con cobertura forestal baja cuando la API reporta alerta UV alta. |
| CLI-07 | El sistema debe cachear los datos climáticos por zona geográfica con TTL configurable (default: 10 minutos) para no saturar la API externa. |
| CLI-08 | El sistema debe exponer el estado del clima usado en el cálculo (timestamp, fuente, valores WBGT) en la respuesta de análisis. |

---

## SIM — Modo Simulación

| ID | Requisito |
|---|---|
| SIM-01 | El sistema debe permitir inyectar valores climáticos manuales (temperatura, humedad, precipitación, UV) como parámetros de entrada, sobrescribiendo la API externa. |
| SIM-02 | El sistema debe marcar claramente en la respuesta si el cálculo usó datos reales o simulados. |
| SIM-03 | El sistema debe permitir simular escenarios nombrados predefinidos: `seco`, `lluvia_leve`, `lluvia_intensa`, `calor_extremo`, `noche`. |
| SIM-04 | El sistema debe permitir comparar en una sola petición el riesgo de una ruta en dos escenarios climáticos distintos (real vs. simulado). |

---

## RIE — Índice de Riesgo

| ID | Requisito |
|---|---|
| RIE-01 | El sistema debe calcular un score de riesgo por segmento combinando: costo metabólico (Minetti), velocidad degradada por clima y perfil de fatiga acumulada. |
| RIE-02 | El sistema debe calcular los factores de corrección de Cifuentes aplicables: `Fc_i = 1 − (ml_i / mt)`. |
| RIE-03 | El sistema debe aplicar el factor `Fc_precipitación` como penalizador sobre segmentos marcados con lluvia limitante. |
| RIE-04 | El sistema debe aplicar el factor `Fc_erodabilidad` sobre segmentos con arcilla + pendiente >10%, con penalización ×1.5 en pendiente severa. |
| RIE-05 | El sistema debe aplicar el factor `Fc_anegamiento` sobre segmentos con estancamiento de agua registrado. |
| RIE-06 | El sistema debe aplicar el factor `Fc_brillo_solar` sobre segmentos con cobertura forestal baja bajo alerta UV. |
| RIE-07 | El sistema debe calcular la Capacidad de Carga Real: `CCR = CCF × ΠFc_i`. |
| RIE-08 | El sistema debe traducir el score de riesgo final a la escala MIDE (1–5) para cada una de las 4 dimensiones: severidad, orientación, desplazamiento y esfuerzo. |
| RIE-09 | El sistema debe devolver un nivel MIDE global (1–5) como síntesis ponderada de las 4 dimensiones. |
| RIE-10 | El sistema debe identificar y marcar los segmentos de mayor riesgo de la ruta (top 10% por score). |

---

## GRF — Grafo y Enrutamiento

| ID | Requisito |
|---|---|
| GRF-01 | El sistema debe generar la topología de la red de senderos usando `pgr_createTopology`. |
| GRF-02 | El sistema debe asignar columnas `cost` y `reverse_cost` asimétricas por arista, reflejando que ascender ≠ descender. |
| GRF-03 | El sistema debe calcular la ruta de menor costo entre dos nodos usando el algoritmo A* bidireccional de pgRouting. |
| GRF-04 | El sistema debe soportar Dijkstra como algoritmo alternativo configurable por parámetro. |
| GRF-05 | El sistema debe actualizar los valores de `cost` en la tabla dinámica cuando los datos climáticos cambian, sin modificar la geometría estática. |
| GRF-06 | El sistema debe ejecutar la actualización de costos a través de un trigger o job asíncrono al recibir nueva información climática. |
| GRF-07 | El sistema debe soportar múltiples nodos de paso intermedios (waypoints) en una misma consulta de ruta. |

---

## API — Endpoints REST

| ID | Método | Endpoint | Descripción |
|---|---|---|---|
| API-01 | `POST` | `/routes/analyze` | Recibe GPX o GeoJSON + perfil excursionista, devuelve análisis completo de ruta con riesgo por segmento. |
| API-02 | `POST` | `/routes/upload` | Persiste una ruta en la base de datos y retorna su `route_id`. |
| API-03 | `GET` | `/routes/{route_id}/risk` | Devuelve el índice de riesgo actual de una ruta persistida, usando clima en tiempo real. |
| API-04 | `POST` | `/routes/{route_id}/simulate` | Calcula el riesgo de una ruta con clima simulado provisto en el body. |
| API-05 | `GET` | `/routes/{route_id}/segments` | Devuelve los segmentos de una ruta con sus atributos: gradiente, velocidad, costo, score de riesgo. |
| API-06 | `POST` | `/routes/optimal-path` | Dado un origen y destino (nodos del grafo), devuelve la ruta de menor costo energético bajo condiciones actuales. |
| API-07 | `GET` | `/climate/current` | Devuelve los datos climáticos actuales cacheados para una ubicación `lat,lon`. |
| API-08 | `GET` | `/health` | Health check del sistema, incluye estado de conexión a PostGIS y API climática. |

---

## MAP — Mapa Web Interactivo

| ID | Requisito |
|---|---|
| MAP-01 | El mapa debe renderizar la ruta completa con segmentos coloreados por nivel de riesgo (gradiente de color: verde → amarillo → rojo). |
| MAP-02 | Al hacer click en un segmento, el mapa debe mostrar un panel con: gradiente, velocidad estimada, costo metabólico, score de riesgo y factores climáticos activos. |
| MAP-03 | El mapa debe permitir cargar un archivo GPX o GeoJSON directamente desde el navegador. |
| MAP-04 | El mapa debe mostrar un panel lateral con el resumen de la ruta: distancia total, desnivel +/−, tiempo estimado, kcal, nivel MIDE global. |
| MAP-05 | El mapa debe permitir configurar el perfil del excursionista (peso, carga, condición física) desde un formulario antes de analizar la ruta. |
| MAP-06 | El mapa debe mostrar un toggle visible para alternar entre datos climáticos en tiempo real y modo simulación. |
| MAP-07 | En modo simulación, el mapa debe mostrar controles deslizantes para temperatura, humedad, precipitación e intensidad UV. |
| MAP-08 | El mapa debe actualizar el coloreado de segmentos automáticamente cuando cambian los parámetros de simulación, sin recargar la página. |
| MAP-09 | El mapa debe marcar visualmente los segmentos de alto riesgo (top 10%) con un ícono de advertencia. |
| MAP-10 | El mapa debe mostrar el nivel MIDE como un indicador de 4 dimensiones (severidad, orientación, desplazamiento, esfuerzo) con iconografía clara. |
| MAP-11 | El mapa debe ser usable en dispositivos móviles (responsive, touch-friendly). |

---

## Dependencias entre módulos

```
GPX/GeoJSON
    └── DAT (almacenamiento 3DZ)
            └── RUT (segmentación + gradiente desde DEM)
                    ├── VEL (velocidad por segmento)
                    ├── MET (costo metabólico × perfil PRF)
                    ├── CLI (modificadores climáticos)
                    └── RIE (score final + MIDE)
                            └── GRF (costos en grafo pgRouting)
                                    └── API → MAP
```

---

## Fuera de alcance (v1)

- Autenticación de usuarios / cuentas con historial
- Generación de rutas desde cero (solo análisis de rutas existentes)
- Integración con sensores IMU en tiempo real
- Notificaciones push a dispositivos en campo
- Modo offline en app móvil