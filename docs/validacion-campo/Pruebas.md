# Reporte Técnico: Metodología de Pruebas de Campo para RiskTrail
### (Validación de Predicciones Algorítmicas y Fisiológicas — v2.1)

## 1. Resumen Ejecutivo y Alcance del Estudio

Este documento establece el marco metodológico para la validación en campo del motor de cálculo de RiskTrail, un sistema de **predicción** de riesgo y coste metabólico en rutas de senderismo. La prueba se ejecutará sobre una **superficie homogénea de asfalto en ascenso continuo de 3.40 km (Cerro Ancón, Ciudad de Panamá)**, con una muestra heterogénea de 10 participantes de perfiles fisiológicos contrastantes.

**Marco conceptual (crítico para la interpretación):** RiskTrail no monitorea fatiga en tiempo real. El sistema recibe una geometría de ruta, un modelo de elevación, variables climáticas y un perfil de senderista, y **predice** —antes de caminar— el tiempo, el gasto energético y el riesgo por tramo. Por lo tanto, cada criterio de validación contrasta *predicción del modelo para un tramo* contra *observación de un humano real en ese mismo tramo*. No se mide "latencia de respuesta" del sistema, sino exactitud predictiva.

La evidencia se organiza en tres niveles, de mayor a menor fuerza probatoria:

1. **Tiempo real vs. `estimated_time_h`** (objetivo, numérico).
2. **Energía real estimada por frecuencia cardíaca vs. kcal del modelo (Pandolf)** (objetivo, si hay wearables).
3. **Esfuerzo percibido (Borg modificado) vs. riesgo/esfuerzo predicho por tramo** (subjetivo, descriptivo).

Se omiten métricas de usabilidad general para enfocar el esfuerzo analítico en la viabilidad del modelo matemático.

## 2. Variables del Modelo Bajo Prueba

Los únicos inputs del perfil del senderista que procesa el sistema (`HikerProfile`: `weight_kg`, `load_kg`, `fitness_level`) son:

| Variable | Rol en el modelo | Referencia de código |
|---|---|---|
| Peso corporal (`weight_kg`) | Coste energético (Pandolf), presupuesto de fatiga | `met/service.py`, `analysis.py:433-447` |
| Carga (`load_kg`) | Coste energético (Pandolf); **no** afecta velocidad | ídem |
| Forma física (`fitness_level`: low/medium/high/athlete) | Factor de velocidad ×0.70 a ×1.30 | `prf/service.py:32-47` |

**Nota de honestidad metodológica:** la edad **no** es input del modelo y no se registra como variable de calibración. La carga **sí** lo es, y esta campaña la pone a prueba explícitamente (Sección 3). Restricción validada: `load_kg < weight_kg` (PRF-06).

Outputs bajo auditoría por ruta: `estimated_time_h`, `total_kcal`, `time_to_severe_fatigue_h`, riesgo por segmento (bandas MIDE/IDR y semáforo), velocidad por segmento.

## 3. Perfiles de la Muestra (n = 10)

Cada participante registra su perfil real en la app antes de partir. Se garantiza cobertura de las cuatro combinaciones clave:

| Arquetipo | n | Peso | Carga | Forma física | Qué valida |
|---|---|---|---|---|---|
| A — Masa alta / cardio bajo | 2 | ~100 kg | 0 kg | low | Sensibilidad del modelo de energía al peso |
| B — Masa baja / cardio bajo | 2 | ~56 kg | 0 kg | low | Línea base de energía; contraste A vs. B |
| C — Estándar sin carga | 2 | ~72 kg | 0 kg | medium | Caso base |
| D — Estándar con carga | 2 | ~72 kg | 10 kg | medium | **Efecto de `load_kg` en kcal sin cambio de tiempo** |
| E — Masa media / cardio alto | 2 | ~72 kg | 0 kg | high | Factor de velocidad de `fitness_level` en tiempo |

**Hipótesis direccionales del modelo (a contrastar, no a confirmar):**

- A y B: mismo `estimated_time_h` sobre la misma ruta, pero curvas de kcal y de fatiga severa notablemente distintas (el peso entra por la vía energética, no cinemática).
- C y D: mismo tiempo y mismas alertas de riesgo cinemático; D muestra ~30-45% más de kcal y una ventana de fatiga severa más corta. Si el sistema no distingue a D de C, hay un bug en Pandolf.
- E: `estimated_time_h` ≈ 1.15× más rápido que C (factor de fitness), con kcal/s por encima de C.
- Borg real: se espera una progresión monótona creciente a lo largo de los checkpoints. El pico máximo de esfuerzo se registrará en el CP 3 (mirador, km 3.4). A y B mostrarán un despegue temprano en Borg desde el km 2.0.

## 4. Topografía del Sendero de Prueba (Cerro Ancón — 3.40 km en Ascenso)

La vía de acceso vehicular/peatonal en asfalto a Cerro Ancón aísla los dos factores nucleares del motor:

- **Pendiente geométrica continua:** desde la cota base (54.6 m) hasta el Mirador (177.4 m), con un desnivel positivo acumulado de +134 m (+122.8 m neto) y gradientes crecientes.
- **Estrés térmico y ambiental tropical:** Ciudad de Panamá ofrece un entorno de alta temperatura (~30–33 °C) y humedad relativa elevada (~75–85%), situando el WBGT estimado en > 28 °C de manera sostenida entre las 10:00 y las 14:00.

| Tramo | Cota inicio → fin | Pendiente media | Predicción del sistema a auditar |
|---|---|---|---|
| **Km 0.0 – 1.0** (Calentamiento) | 54.6 m → 62.0 m (+7.4 m) | ~0.7% (falso llano) | Velocidad crucero (~3.9 km/h × factor fitness); riesgo bajo (verde). |
| **Km 1.0 – 2.0** (Transición) | 62.0 m → 89.6 m (+27.6 m) | ~2.8% (ascenso moderado) | Inicio de degradación por pendiente. Tras ~20 min de marcha bajo calor, entra en juego el *cardiovascular drift* (`cli/service.py:162`). |
| **Km 2.0 – 3.0** (Rampa Fuerte) | 89.6 m → 148.1 m (+58.5 m) | ~5.8% (ascenso pronunciado) | Caída pronunciada de velocidad (Irmischer-Clarke); salto de riesgo a amarillo; incremento notable de kcal/s. |
| **Km 3.0 – 3.4** (Rampa Final a la Cima) | 148.1 m → 177.4 m (+29.3 m) | ~7.3% (máxima exigencia) | Pico máximo de riesgo segmentario acumulado; umbral crítico de fatiga en perfiles low fitness. |

**Referencia altimétrica:** antes de la campaña se cotejan las cotas extraídas por PostGIS desde el DEM contra los puntos de referencia del track GPX versionado (base 55 m, mirador 177 m) y la **ganancia acumulada por kilómetro**. Las pendientes por segmento del GPX **no** se usan como referencia directa: el error vertical del GPS de consumo (±3–5 m) supera la tolerancia de 1 pp a escala de segmento de 100 m y dominaría la medición.

## 5. Protocolo de Ejecución en Campo

### A. Fase Previa (oficina, día anterior)

1. Subir el GPX `data/samples/ciudad-panama-cerro-ancon-sendero-el-mirador-panama.gpx` y ejecutar el análisis **una sola vez**, con los 10 perfiles registrados. Exportar y **congelar** las predicciones (JSON por participante con `git_commit_hash`, tiempo, kcal, fatiga, riesgo por segmento). Las predicciones se fijan **antes** de observar ningún dato humano.
2. Verificar en el JSON exportado que `climate_source == "api"`.
3. Chequeo térmico: en Cerro Ancón el WBGT superará previsiblemente los 28 °C en horas centrales; confirmar que la duración prevista (> 45 min) activará el multiplicador de drift cardiovascular tras el minuto 20.

### B. Preparación de Participantes

- Constancia de aptitud física; hidratación obligatoria; criterio de corte por golpe de calor (Borg ≥ 9 con mareo/náusea → detener).
- Registro de peso real, carga asignada y forma física en la app.
- Tracker GPS personal (distancia, duración real y FC si hay wearable), sin consultar la app durante la subida.

### C. Salida y Checkpoints

- Dos subgrupos de 5 participantes, con desfase de 15 min. Salida individualizada espaciada ≥ 2 min entre participantes para ritmo natural e independiente.
- **Puntos de Control (Checkpoints):**
  - **CP 1 (Km 1.0 — Fin del tramo llano):** hora de paso, Borg (CR10), FC. Baseline de esfuerzo.
  - **CP 2 (Km 2.0 — Inicio de rampa fuerte):** hora de paso, Borg, FC. ≈33 min de marcha en perfil medio; la marca de los 20 min del drift se cruza antes (~km 1.2) y el multiplicador ya está activo en este punto.
  - **CP 3 (Km 3.4 — Cima / Mirador de Cerro Ancón):** registro final de llegada. Pico máximo de fatiga y cierre de cronometraje.
- Registro de condiciones reales de cobertura vegetal/sombra y radiación solar observadas.

## 6. Métricas de Análisis de Resultados

**Declaración estadística:** con n = 10, el estudio es **exploratorio/descriptivo**. Se reportan medianas, rangos intercuartílicos y direccionalidad matemática sin asumir significancia inferencial.

| # | Métrica | Cálculo | Criterio de solidez |
|---|---|---|---|
| M1 | Error de tiempo total | \|T_real − T_pred\| / T_pred por participante | Mediana ≤ 15%; sin sesgo direccional sistemático por perfil |
| M2 | Sensibilidad al fitness | Ratio T_real(C) / T_real(E) vs. ratio predicho 1.15 | Concordancia dentro de ±0.15 |
| M3 | Error energético (con FC) | kcal por FC (Keytel) vs. Pandolf | Mediana ≤ 25% |
| M4 | Efecto carga | Δkcal(D−C) real vs. predicho | Mismo signo y orden de magnitud (+30-45%) |
| M5 | Monotonicidad Borg vs. Riesgo | Correlación ordinal entre Borg en CP1/CP2/CP3 y el riesgo predicho para esos tramos | Crecimiento monótono (CP3 > CP2 > CP1) coincidente con la pendiente |
| M6 | Error altimétrico | Error de la ganancia acumulada por km PostGIS/DEM vs. GPX, más cotas de referencia (55 m base, 177 m mirador) | ≤ 10% por kilómetro; no se compara pendiente por segmento (ruido GPS del GPX > tolerancia) |
| M7 | Coherencia interna de inputs | ¿A y B tuvieron idéntico tiempo predicho y distinto gasto/fatiga? | Coherencia estricta exigida por diseño del código |

## 7. Matriz de Evaluación (Criterios de Éxito vs. Falla)

| Métrica | Escenario favorable | Escenario de falla algorítmica |
|---|---|---|
| M1 Tiempo | Desvíos ≤ 15% sin patrón sistemático | Subestimación sistemática (> 25%) por aplanamiento del DEM en pendientes fuertes |
| M4 Carga | Diferencia clara de kcal entre C y D sin variación en tiempo | Kcal idénticas → fallo en la propagación de `load_kg` al servicio metabólico |
| M5 Borg | CP3 reporta el máximo Borg y coincide con la banda de riesgo más alta | CP3 clasificado como riesgo verde o inferior a CP1 |
| M6 Altimetría | PostGIS reproduce la rampa final (km 3.0–3.4, ~7.4%) y la ganancia acumulada por km está dentro de tolerancia | El DEM promedia la rampa final dejándola por debajo del 3% |
| M7 Perfiles | Tiempo desacoplado del peso corporal | El tiempo estimado varía según el peso del usuario |

## 8. Limitaciones Conocidas y Confounds Declarados

1. **Prueba exclusivamente de ascenso:** al ser una ruta de subida pura a Cerro Ancón, la corrección de velocidad en descenso de Langmuir (`vel/service.py:apply_langmuir`) queda formalmente fuera del alcance empírico de esta campaña y se declara para trabajo futuro.
2. **Tiempo en movimiento:** el tiempo predicho no contempla pausas; debe descontarse el tiempo detenido en los checkpoints para la comparación objetiva.
3. **Dependencia climática:** si la prueba se realiza en horario muy temprano con temperatura fresca, el WBGT podría quedar en ≤ 28 °C y no activar el drift cardiovascular.
4. **Borg subjetivo:** ordinal y auto-reportado; útil para monotonicidad, no para calibración fina de constantes fisiológicas.
5. **Muestra acotada:** n = 10 permite auditar consistencia física y lógica del código, no validación biomédica de población amplia.

## 9. Orden de Reporte Sugerido para el Documento Final

1. Trazabilidad: commit hash → predicciones congeladas → telemetría de campo → tablas M1-M7.
2. Validación biomecánica y física: tiempos objetivos y curvas de gasto energético.
3. Validación perceptual: correlación del esfuerzo reportado con las alertas segmentarias.
4. Conclusiones técnicas y recomendaciones de calibración para el motor de RiskTrail.
