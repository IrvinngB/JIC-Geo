# Reporte Técnico: Metodología de Pruebas de Campo para RiskTrail
### (Validación de Predicciones Algorítmicas y Fisiológicas — v2)

## 1. Resumen Ejecutivo y Alcance del Estudio

Este documento establece el marco metodológico para la validación en campo del motor de cálculo de RiskTrail, un sistema de **predicción** de riesgo y coste metabólico en rutas de senderismo. La prueba se ejecutará en un entorno controlado de 3.0 km de asfalto, con una muestra heterogénea de 10 participantes de perfiles fisiológicos contrastantes.

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
- Borg real: se espera que A y B reporten valores altos en el tramo de ascenso (1.0-2.0 km) y que el riesgo **predicho** por el sistema para ese tramo sea el más alto del perfil. La validación es tramo-por-tramo, no en tiempo real.

## 4. Topografía del Sendero de Prueba (3 km en Pavimento)

El asfalto elimina ruido físico (lodo, grava, off-path) y aísla los dos factores que el modelo sí procesa:

- **Pendiente geométrica** — extraída del DEM procesado en PostGIS (segmentación ~100 m, corrección Savitzky-Golay).
- **Estrés ambiental** — temperatura, radiación y viento vía Open-Meteo (WBGT de Stull + Tg aproximada).

| Tramo | Descripción | Predicción del sistema a auditar |
|---|---|---|
| Km 0.0 – 1.0 (llano-leve) | Calentamiento | Velocidad ≈ 3.9 km/h × factor fitness; riesgo verde |
| Km 1.0 – 2.0 (ascenso) | Tramo crítico | Caída de velocidad por pendiente; pico de riesgo segmentario; mayor kcal/s |
| Km 2.0 – 3.0 (descenso) | Recuperación | Efecto Langmuir (±10 min/300 m según gradiente); riesgo decreciente |

**Referencia altimétrica:** antes de la campaña se releva el perfil real con un dispositivo GNSS de precisión centimétrica o se compara contra una segunda fuente DEM (p. ej. Copernicus vs. SRTM). Sin referencia, el criterio "resolución altimétrica" no es medible.

## 5. Protocolo de Ejecución en Campo

### A. Fase Previa (oficina, día anterior)

1. Subir el GPX de la ruta y ejecutar el análisis **una sola vez**, con los 10 perfiles registrados. Exportar y **congelar** las predicciones (JSON por participante: tiempo, kcal, fatiga, riesgo por tramo de 1 km). Las predicciones se fijan **antes** de observar ningún dato humano (cegamiento simple: evita sesgo retrospectivo).
2. Verificar en el JSON exportado que `climate_source == "api"` para el día/hora previstos. **Si el sistema caería al fallback silencioso (25 °C / 50 % RH), la prueba de estrés ambiental no es válida y se reprograma.**
3. Chequeo de clima del día de prueba: si el WBGT proyectado es ≤ 28 °C, registrar que la rama de *drift cardiovascular* (activa solo con WBGT > 28 y > 20 min de marcha) **no será ejercitada** por la prueba, y reportarlo como limitación. Ideal: programar la salida entre 11:00 y 14:00 en día soleado para activarla.

### B. Preparación de Participantes

- Constancia de aptitud para esfuerzo moderado-alto; hidratación obligatoria; criterio de corte por golpe de calor (Borg ≥ 9, mareo o náusea → detener).
- Registro en la app de peso real (min. ropa de campo), carga y forma física según arquetipo asignado.
- Cada participante lleva un registrador de tiempo objetivo: reloj GPS o teléfono con tracking (distancia, duración real, y FC si hay pulsera). El dispositivo **no** muestra la predicción de la app durante la marcha.

### C. Salida y Checkpoints

- Dos subgrupos de 5, con desfase de 15 min entre subgrupos. **Dentro de cada subgrupo, los participantes caminan espaciados ≥ 2 minutos** (sino el ritmo grupal contamina la variable dependiente principal: tiempo real). Ritmo auto-seleccionado, instrucción verbal única: "caminá a tu ritmo normal de senderismo".
- **CP 1 (km 1.0), CP 2 (km 2.0, cima del ascenso), CP 3 (km 3.0):** registro inmediato de Borg modificado (CR10), FC instantánea si hay wearable, y hora de paso (precisión 1 min). La app **no** se consulta en campo; la contrastación es posterior.
- Registro de condiciones observadas por tramo: sol/sombra, viento, percepción de calor (para interpretar desvíos junto con el clima real del período, no solo el de la predicción).

## 6. Métricas de Análisis de Resultados

**Declaración estadística:** con n = 10 por brazo de comparación, la campaña es **exploratoria/descriptiva**. No se realizan pruebas de hipótesis inferenciales ni se citan umbrales porcentuales como "85% de correlación": con esta muestra, un solo participante mueve el resultado 10 puntos. Se reportan magnitudes, direccionalidad y dispersiones (mediana, rango intercuartílico), que es lo que el tamaño de muestra permite sostener honestamente.

| # | Métrica | Cálculo | Criterio de solidez |
|---|---|---|---|
| M1 | Error de tiempo | \|T_real − T_pred\| / T_pred por participante | Mediana ≤ 15%; sin sesgo direccional sistemático por fitness |
| M2 | Sensibilidad al fitness | Ratio T_real(C) / T_real(E) vs. ratio predicho 1.15 | Mismo orden de magnitud (±0.15) |
| M3 | Error energético (si hay FC) | kcal estimadas por FC (p. ej. ecuación Keytel) vs. Pandolf | Mediana ≤ 25% |
| M4 | Efecto carga | Δkcal(D−C) real vs. predicho | Mismo signo y orden de magnitud |
| M5 | borg vs. riesgo predicho | Spearman (ordinal) entre Borg por tramo y banda de riesgo predicha para ese tramo, con medidas repetidas agrupadas por participante | ρ positivo claro (≥ 0.5) y monotonicidad en CP2 > CP1/CP3 |
| M6 | Error altimétrico | Error medio absoluto de pendiente por segmento vs. referencia (Sección 4) | ≤ 1 punto porcentual de pendiente en el tramo de ascenso |
| M7 | Coherencia interna | ¿A y B compartieron tiempo predicho y difirieron en kcal/fatiga, tal como diseña el modelo? | Debe cumplirse exactamente; si no, es bug de implementación, no de validación |

## 7. Matriz de Evaluación (Criterios de Éxito vs. Falla)

| Métrica | Escenario favorable | Escenario de falla algorítmica |
|---|---|---|
| M1 Tiempo | Desvíos ≤ 15% sin patrón sistemático | El sistema subestima consistentemente (> 25%) → recalibrar modelo de velocidad o verificar que la segmentación no esté aplanando pendientes |
| M4 Carga | La app distingue C de D en energía, no en tiempo | Mismo kcal para C y D → Pandolf no recibe `load_kg` (bug de cableado, no de ciencia) |
| M5 Borg | El pico subjetivo cae en el tramo que el modelo marcó más riesgoso | Pico de Borg en tramo "verde" del modelo → revisar pesos de riesgo o DEM |
| M6 Altimetría | El DEM captura el ascenso del km 1-2 con error ≤ 1 pp | Pendiente aplastada → el esfuerzo real supera al predicho en CP2; reportar resolución mínima de DEM requerida |
| M7 Perfiles | Diferenciación por la vía correcta (energía ≠ tiempo) | El tiempo varía con el peso → contradice el modelo documentado y la defensa ante jurado |

## 8. Limitaciones Conocidas y Confounds Declarados

Se reportan explícitamente en la campaña (declararlos resta más valor ocultarlos):

1. **El tiempo no depende del peso ni de la carga** en el modelo actual (decisión de diseño coherente con Naismith/Tobler/Irmischer–Clarke). La prueba no puede "falsar" esa elección; solo puede mostrar si el tiempo real de A difiere del de B. Si difiere sistemáticamente, es evidencia para *considerar* un factor de carga en trabajo futuro.
2. El modelo predice **tiempo en movimiento**: sin pausas. El T_real incluye las paradas de los checkpoints → corregir T_real descontando ~2-3 min de paradas, o reportar ambos.
3. El drift cardiovascular puede no activarse si el WBGT real queda ≤ 28 °C o el ritmo es rápido (menos de 20 min de marcha).
4. Borg es ordinal y auto-reportado; dos personas con el mismo puntaje pueden tener FC muy distinta.
5. Clima puntual (centroid de la ruta) vs. microclima experimentado tramo a tramo.
6. n = 10, medida repetida, sin grupo de control cruzado (cada participante camina una sola vez).

## 9. Orden de Reporte Sugerido para el Documento Final

1. Trazabilidad: predicciones congeladas → datos de campo → tablas M1-M7.
2. Primero los resultados objetivos (tiempo, energía), después los perceptuales (Borg).
3. Cerrar con limitaciones (Sección 8) y trabajo futuro (factor de carga sobre velocidad en descenso; validación con n mayor y múltiples rutas).
