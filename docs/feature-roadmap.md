# RiskTrail — Feature Roadmap

> Lista de features planificados, organizados por prioridad y dependencias.
> Última actualización: 2026-09-09

---

## Tier 1 — MVP funcional

Lo que falta para que RiskTrail se use de verdad. Sin auth, todo local.

### 1. Perfil persistente

**Descripción:** Guardar datos del excursionista (peso, carga, fitness, superficie) en localStorage para que no se pierdan al recargar.

**Detalle:**
- Guardar automáticamente al modificar el formulario
- Cargar al abrir la app
- Modo rápido: perfil invitado por defecto (70kg, 10kg, fitness medio, dirt)
- Botón "Restablecer valores por defecto"

**Dependencias:** Ninguna
**Complejidad:** Baja
**Archivos afectados:** `useHikerProfile.ts`, `HikerProfileForm.vue`

---

### 2. Múltiples perfiles

**Descripción:** Crear y permutar entre varios perfiles (para ir con distintas personas o grupos).

**Detalle:**
- Lista de perfiles guardados (máx. 5-10)
- Botón "Nuevo perfil" con nombre descriptivo (ej: "Irvin solo", "Team full", "Con familia")
- Selector rápido antes de analizar
- Editar/eliminar perfiles existentes
- Cada perfil guarda: name, weight_kg, load_kg, fitness_level, surface_type

**Dependencias:** #1 (perfil persistente)
**Complejidad:** Baja
**Archivos afectados:** `useHikerProfile.ts`, `HikerProfileForm.vue`, nuevo componente `ProfileSelector.vue`

---

### 3. Historial de análisis

**Descripción:** Guardar cada análisis completado con fecha, nombre y resumen para poder revisarlo después.

**Detalle:**
- Al terminar un análisis, preguntar "¿Guardar en historial?"
- Guardar en IndexedDB: route_name, route_id, date, source_format, summary (MIDE, distance, time, kcal, elevation), segmentos con geometría y risk_score
- Listado cronológico en sidebar o vista dedicada
- Filtro por nombre o fecha
- Tap en un item → re-abrir el análisis completo

**Dependencias:** Ninguna
**Complejidad:** Media
**Archivos afectados:** `routeStore.ts`, nuevo composable `useHistory.ts`, nuevo componente `HistoryList.vue`

---

### 4. Favoritos

**Descripción:** Marcar rutas del historial como favoritas para acceder rápido.

**Detalle:**
- Estrella toggle en cada item del historial
- Filtro "Solo favoritos" en el listado
- Máximo ilimitado (es solo un flag boolean)
- Persiste en IndexedDB junto al historial

**Dependencias:** #3 (historial)
**Complejidad:** Baja
**Archivos afectados:** `useHistory.ts`, `HistoryList.vue`

---

### 5. Re-analizar con otro clima

**Descripción:** Sobre un análisis guardado, re-ejecutar la simulación climática con parámetros distintos.

**Detalle:**
- Desde el historial, botón "Re-simular"
- Carga los segmentos guardados en el routeStore
- Abre el panel de ClimateSliders
- Permite cambiar temperatura, humedad, precipitación, UV
- Ejecuta la simulación local (backend ya calculó los datos base)
- Muestra comparación real vs nuevo simulado

**Dependencias:** #3 (historial), backend endpoint existente para simulación
**Complejidad:** Media
**Archivos afectados:** `routeStore.ts`, `ClimateSliders.vue`, `HistoryList.vue`

---

## Tier 2 — Ubicación real

Lo que diferencia a RiskTrail de otras apps de hiking. Requiere geolocalización del navegador.

### 6. GPS tracking básico

**Descripción:** Mostrar la posición actual del usuario en el mapa y identificar el tramo más cercano.

**Detalle:**
- Botón flotante "¿Dónde estoy?" en el mapa
- Usa `navigator.geolocation.getCurrentPosition()`
- Centra el mapa en la posición actual
- Muestra badge con: tramo #X, riesgo Y/100, dirección (subida/bajada)
- Requiere permiso de ubicación del usuario
- Funciona sin internet (GPS satelital)

**Dependencias:** Análisis previo con geometría de segmentos
**Complejidad:** Media
**Archivos afectados:** `RouteMap.vue`, nuevo composable `useGeolocation.ts`

---

### 7. Alerta de tramo peligroso

**Descripción:** Notificación cuando el usuario entra a un tramo de riesgo alto o extremo.

**Detalle:**
- Tracking continuo de posición cada 3-5 segundos
- Matching de posición contra tramos (nearestPointOnLine con turf.js)
- Al detectar tramo con risk_score >= 60:
  - Vibración del dispositivo (`navigator.vibrate()`)
  - Badge rojo visible en el mapa
  - Sound de alerta (opcional)
- Al salir del tramo peligroso: alerta se limpia
- Toggle para activar/desactivar alertas

**Dependencias:** #6 (GPS tracking), turf.js
**Complejidad:** Media-Alta
**Archivos afectados:** `useGeolocation.ts`, `RouteMap.vue`, `MapView.vue`

---

### 8. Registro de ruta real

**Descripción:** Guardar el recorrido GPS real del usuario y compararlo con la ruta planificada.

**Detalle:**
- Al iniciar tracking, grabar puntos GPS cada 5 segundos
- Al terminar, guardar la polilínea real en IndexedDB
- Vista de comparación: ruta planificada (azul) vs ruta real (verde)
- Métricas: distancia real vs estimada, tiempo real vs estimado, desviación máxima
- Opcional: exportar la ruta real como GPX

**Dependencias:** #6 (GPS tracking)
**Complejidad:** Alta
**Archivos afectados:** `useGeolocation.ts`, nuevo componente `RouteComparison.vue`, `routeStore.ts`

---

### 9. Comparar análisis

**Descripción:** Elegir dos análisis del historial y verlos lado a lado.

**Detalle:**
- Checkbox de selección en el historial (máx. 2)
- Botón "Comparar" se activa con 2 seleccionados
- Vista split: cada ruta con su MIDE, tiempo, distancia, kcal, riesgo máximo
- Highlight de diferencias (ej: "esta ruta tiene 30% más de riesgo")
- Responsive: en mobile, apilados verticalmente

**Dependencias:** #3 (historial)
**Complejidad:** Media
**Archivos afectados:** `HistoryList.vue`, nuevo componente `ComparisonView.vue`

---

## Tier 3 — Offline

Para que RiskTrail funcione en el campo sin señal.

### 10. Cache de análisis

**Descripción:** Almacenar el análisis completo (segmentos + geometría + risk) en IndexedDB para uso offline.

**Detalle:**
- Al completar un análisis, guardar automáticamente en IndexedDB
- Estructura: segmentos con geom (LineString), risk_score, velocity, slope, etc.
- Al abrir historial sin internet, los análisis siguen accesibles
- Límite de storage: ~50 análisis (configurable)
- Estrategia LRU: borrar los más viejos al superar el límite

**Dependencias:** #3 (historial)
**Complejidad:** Media
**Archivos afectados:** `useHistory.ts`, schema de IndexedDB

---

### 11. Cache de tiles del mapa

**Descripción:** Descargar los tiles del mapa de la zona de hiking para uso offline.

**Detalle:**
- Antes de ir al sendero, botón "Descargar zona" en el mapa
- Calcula bounding box del área visible + buffer de 5km
- Descarga tiles del base map seleccionado (streets/topo/satellite)
- Almacena en Cache API (service worker)
- indicador de progreso de descarga
- Al usar mapa sin internet, sirve tiles del cache
- Eliminar zona descargada cuando ya no se necesite

**Dependencias:** Service worker (nuevo), MapLibre offline plugin
**Complejidad:** Alta
**Archivos afectados:** nuevo `sw.js`, `RouteMap.vue`, nuevo componente `OfflineManager.vue`

---

### 12. Matching offline tramo↔posición

**Descripción:** Determinar en qué tramo está el usuario usando solo datos cacheados.

**Detalle:**
- Sin backend: usa turf.js `nearestPointOnLine()` contra segmentos en IndexedDB
- Calcula distancia del punto actual a cada segmento
- Retorna el tramo más cercano dentro de un radio máximo (ej: 100m)
- Si está fuera de radio → "Fuera de la ruta"
- Performance: pre-filtrar por bounding box antes del cálculo completo
- Actualización cada 3-5 segundos

**Dependencias:** #6 (GPS tracking), #10 (cache de análisis), turf.js
**Complejidad:** Media
**Archivos afectados:** `useGeolocation.ts`, utils de geo

---

## Tier 4 — Social y utilidades

Features que amplían el alcance y la utilidad social.

### 13. Compartir análisis

**Descripción:** Generar un link público con el resumen del análisis de una ruta.

**Detalle:**
- Botón "Compartir" en el análisis
- Genera un ID corto (ej: `/share/abc123`)
- Backend crea registro público con: route_name, MIDE, distancia, tiempo, riesgo máximo, mapa estático
- Link accesible sin login
- Preview con imagen OG para WhatsApp/social
- Opcional: incluir perfil del excursionista (sin datos sensibles)

**Dependencias:** #3 (historial), backend endpoint nuevo
**Complejidad:** Media
**Archivos afectados:** backend nuevo router `share.py`, frontend nuevo componente `ShareView.vue`

---

### 14. Alerta meteorológica

**Descripción:** Notificar al usuario si el clima pronosticado cambia para una ruta que tiene guardada como "próxima salida".

**Detalle:**
- Marcar una ruta del historial como "próxima salida" (con fecha estimada)
- Cada 6 horas, consultar API meteorológica para la zona
- Si el pronóstico cambia significativamente (lluvia repentina, calor extremo, UV alto):
  - Notificación push (si el browser lo soporta)
  - Badge en la app
- Requiere backend con job scheduler (ej: Celery o cron)
- Requiere API de clima (OpenWeather, visualcrossing, etc.)

**Dependencias:** #3 (historial), API meteorológica, backend scheduler
**Complejidad:** Alta
**Archivos afectados:** backend nuevo servicio `weather_alerts.py`, frontend notificaciones

---

### 15. Condiciones del trail (crowd-sourced)

**Descripción:** Reportes de otros usuarios sobre el estado actual del sendero.

**Detalle:**
- Botón "Reportar condición" en el mapa (por tramo)
- Categorías: limpio, embarrado, árbol caído, inundado, cerrado
- Opcional: foto del estado
- Los reportes se muestran como iconos en el mapa
- Expiran después de 30 días (o configurable)
- Requiere auth (para accountability)

**Dependencias:** Auth (#19), backend modelo `TrailReport`
**Complejidad:** Alta
**Archivos afectados:** backend nuevo router `reports.py`, frontend nuevo componente `TrailReports.vue`

---

### 16. Exportar a GPS device

**Descripción:** Exportar la ruta óptima como GPX para Garmin u otros dispositivos GPS.

**Detalle:**
- Botón "Exportar GPX" en la ruta óptima
- Genera GPX con: waypoints (inicio, fin, paradas), tracklog de la ruta óptima
- Incluye metadata: nombre, descripción, elevación
- Descarga como archivo `.gpx`
- Compatible con Garmin, Suunto, Coros, Komoot

**Dependencias:** Ruta óptima calculada (# routing existente)
**Complejidad:** Baja
**Archivos afectados:** nuevo util `gpxExport.ts`

---

## Tier 5 — Growth y plataforma

Features de escala que convierten RiskTrail en plataforma.

### 17. Ruta sugerida

**Descripción:** "Quiero10km nivel medio" → sugerir rutas del catálogo.

**Detalle:**
- Formulario: distancia deseada, dificultad máxima, tipo de superficie, ubicación
- Backend busca en rutas pre-analizadas que cumplan los criterios
- Retorna top5 con preview de MIDE, distancia, tiempo
- Requiere catálogo de rutas pre-analizadas (alimentado manual o por upload masivo)

**Dependencias:** Catálogo de rutas, backend búsqueda
**Complejidad:** Alta
**Archivos afectados:** backend nuevo endpoint `suggest.py`, frontend nuevo componente `RouteSuggester.vue`

---

### 18. Foto por segmento

**Descripción:** Adjuntar fotos a tramos del historial para documentar el recorrido.

**Detalle:**
- Durante el tracking o después, asociar foto a un tramo específico
- Almacenar foto comprimida en IndexedDB (max 500KB por foto)
- Mostrar thumbnail en el detalle del tramo
- Galería de fotos del recorrido completo
- Opcional: exif data para geolocalizar la foto

**Dependencias:** #8 (registro de ruta real) o #3 (historial)
**Complejidad:** Media
**Archivos afectados:** `routeStore.ts`, nuevo componente `SegmentPhotos.vue`

---

### 19. Auth + sync multi-dispositivo

**Descripción:** Sistema de autenticación para sincronizar perfiles, historial y configuración entre dispositivos.

**Detalle:**
- Registro: email + contraseña (bcrypt hashing)
- Login: JWT access token + refresh token
- Endpoints CRUD para perfiles e historial por usuario
- Sync: al tener conexión, subir datos locales al backend
- Migración: importar datos de localStorage al primer login
- Protected routes en frontend (Pinia auth store)

**Dependencias:** Backend user model, JWT middleware
**Complejidad:** Alta
**Archivos afectados:** backend nuevo router `auth.py`, `users.py`, frontend nuevo store `authStore.ts`, nuevos componentes `LoginView.vue`, `RegisterView.vue`

---

## Sprint Plan

### Sprint1 — Perfil + Historial (1-2 semanas)

| Feature | Días estimados |
|---------|---------------|
| #1 Perfil persistente | 0.5 |
| #2 Múltiples perfiles | 1 |
| #3 Historial | 2 |
| #4 Favoritos | 0.5 |
| **Total** | **4 días** |

### Sprint2 — GPS + Alertas (1-2 semanas)

| Feature | Días estimados |
|---------|---------------|
| #6 GPS tracking | 1.5 |
| #7 Alerta tramo peligroso | 1.5 |
| #10 Cache de análisis | 1 |
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
- #19 Auth + sync
