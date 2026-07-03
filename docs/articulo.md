# RiskTrail: sistema de evaluación dinámica de riesgo para rutas de senderismo mediante modelos biomecánicos y datos meteorológicos en tiempo real

**RiskTrail: dynamic risk assessment system for hiking trails using biomechanical models and real-time meteorological data**

Roy Barrera¹, Kelvin He Wu¹, Irvin Benitez¹, [Nombre Asesor]²*

¹ Facultad de Ingeniería de Sistemas Computacionales, Universidad Tecnológica de Panamá, Ciudad de Panamá, Panamá
² [Unidad / Grupo de Investigación], Universidad Tecnológica de Panamá, Ciudad de Panamá, Panamá

\* Correo de contacto: [correo_asesor@utp.ac.pa]

---

## Resumen

El ecoturismo en ecosistemas neotropicales crece aceleradamente, pero las herramientas de planificación de rutas disponibles emplean modelos estáticos que omiten la interacción dinámica entre topografía, condiciones climáticas y gasto energético humano. Este artículo presenta **RiskTrail**, un prototipo de sistema web de evaluación dinámica de riesgo sustentado en el **Índice Dinámico de Riesgo (IDR)**, diseñado para rutas de senderismo en Panamá. La metodología se enmarcó en *Design Science Research* (DSR), articulando la revisión sistemática de literatura como fase de fundamentación con ciclos iterativos de construcción y evaluación del artefacto bajo el framework Scrum. El sistema integra archivos espaciales GPX, datos meteorológicos en tiempo real de la API Open-Meteo y modelos biomecánicos validados en literatura previa: el Polinomio de Minetti para costo metabólico, la función de Irmischer-Clarke para velocidad predictiva y la ecuación de Pandolf para esfuerzo con carga. La arquitectura comprende una capa de datos espaciales sobre PostgreSQL/PostGIS con pgRouting, un motor de cálculo asíncrono en FastAPI y una interfaz en Vue.js. El IDR se formaliza como suma ponderada lineal de cuatro componentes —metabólico, degradación de velocidad, climático y de terreno— mapeada a cinco niveles MIDE. Los resultados demuestran la **viabilidad técnica** del prototipo y la consistencia interna de su comportamiento con los modelos biomecánicos subyacentes. Este trabajo deliberadamente **no afirma haber validado el IDR como predictor de riesgo real**; la validación empírica de los pesos y de la concordancia con el riesgo percibido constituye el siguiente paso explícito de la investigación.

**Palabras clave:** biomecánica, ecoturismo, índice de riesgo, pgRouting, senderismo.

## Abstract

Ecotourism in neotropical ecosystems is growing rapidly, yet current route planning tools rely on static models that neglect the dynamic interaction between topography, weather conditions, and human energy expenditure. This paper presents **RiskTrail**, a prototype web system based on a proposed **Dynamic Risk Index (DRI)**, designed for hiking trails in Panama. The methodology was framed within *Design Science Research* (DSR), combining a systematic literature review as the grounding phase with iterative build-and-evaluate cycles under the Scrum framework. The system integrates GPX spatial files, real-time meteorological data from the Open-Meteo API, and previously validated biomechanical models: the Minetti polynomial for metabolic cost, the Irmischer-Clarke function for predictive walking speed, and the Pandolf equation for loaded effort. The architecture comprises a PostgreSQL/PostGIS + pgRouting spatial layer, an asynchronous FastAPI computation engine, and a Vue.js visualization interface. The DRI is formalized as a linear weighted sum of four components —metabolic, velocity degradation, climatic and terrain— mapped to five MIDE levels. Results demonstrate **technical feasibility** of the prototype and internal consistency of its behavior with the underlying biomechanical models. This work deliberately **does not claim empirical validation of the DRI as a real-world risk predictor**; empirical calibration of weights and concordance with perceived risk are the explicit next step of the research.

**Keywords:** biomechanics, dynamic risk index, ecotourism, hiking trails, pgRouting.

---

## 1. Introducción

El senderismo se ha consolidado como una de las principales modalidades del ecoturismo en América Latina, dinamizando economías locales y promoviendo la conservación de ecosistemas naturales. Panamá, por su riqueza geográfica y biodiversidad neotropical, posee un alto potencial para esta actividad [14]: senderos como el Camino de Cruces y el Parque Nacional Altos de Campana atraen miles de excursionistas anualmente. Sin embargo, este crecimiento plantea un desafío fundamental: garantizar la seguridad de los visitantes en entornos de alta variabilidad climática y topográfica.

Las plataformas actuales de planificación —como AllTrails o Wikiloc— presentan un enfoque estático: indican distancia, desnivel y altitud, pero ignoran cómo las condiciones ambientales afectan el cuerpo humano durante el recorrido. Un sendero catalogado como moderado en condiciones secas puede transformarse en un trayecto de alto riesgo tras precipitaciones tropicales, cuando la combinación de barro, pendientes pronunciadas y humedad extrema eleva la probabilidad de resbalones, caídas y agotamiento prematuro. Estudios sobre tribología y estabilidad postural confirman que la degradación del coeficiente de fricción en superficies húmedas es una causa primaria de caídas durante la locomoción [4].

### 1.1 Estado del arte

La literatura biomecánica ofrece modelos de alta precisión para estimar el gasto energético en función del gradiente topográfico. La estimación de tiempos de marcha se fundamentó históricamente en la regla de Naismith [8], que asume una velocidad base lineal e ignora la asimetría del descenso. El Polinomio de Minetti [1] superó esta limitación describiendo una curva asimétrica del costo metabólico que diferencia el esfuerzo de ascenso del de descenso. Los modelos de velocidad de Tobler [5] e Irmischer-Clarke [6] estiman tiempos de recorrido corrigiendo anomalías de los enfoques lineales, y trabajos recientes con telemetría GPS a gran escala [7] han caracterizado la variabilidad individual de la marcha según el perfil del excursionista.

El clima tropical de Panamá exacerba los riesgos: temperaturas superiores a 32 °C con humedad relativa mayor al 80 % desencadenan deriva cardiovascular [3], reduciendo la capacidad aeróbica hasta un 40 % más rápido que en condiciones temperadas [2]. En el ámbito de los Sistemas de Información Geográfica (SIG), PostgreSQL con PostGIS [9] y pgRouting [10] permite recalcular costos en una red topológica asimilando datos dinámicos en tiempo real, enfoque validado en sistemas de enrutamiento de emergencia [11]. La gestión turística de áreas protegidas dispone, a su vez, de un instrumento consolidado: la metodología de Capacidad de Carga Turística de Cifuentes [12], que estima los visitantes máximos admisibles en función de factores físicos, ambientales y de manejo.

A pesar de la madurez individual de estos modelos, **no se identificó en la literatura revisada una plataforma que los integre en un índice unificado y dinámico aplicado a entornos neotropicales**, ni que articule la dimensión biomecánica del riesgo individual con la dimensión de gestión turística agregada. Este es el hueco que RiskTrail busca llenar: no proponer nueva biomecánica, sino construir el sistema de software que combina estos modelos en una sola herramienta operativa.

## 2. Objetivos

**Objetivo general:** diseñar e implementar un prototipo de sistema web de evaluación dinámica de riesgo para rutas de senderismo que integre modelos biomecánicos validados y datos meteorológicos en tiempo real, aplicable a ecosistemas neotropicales panameños.

**Objetivos específicos:**
- Fundamentar mediante revisión sistemática los modelos científicos de costo metabólico, velocidad de marcha y estrés térmico aplicables al senderismo.
- Implementar los modelos de Minetti, Irmischer-Clarke y Pandolf para calcular costo metabólico y velocidad predictiva por segmento de ruta.
- Integrar datos climatológicos en tiempo real mediante Open-Meteo para modelar el estrés térmico (WBGT) y la fricción tribológica en descensos mojados.
- **Formalizar matemáticamente el Índice Dinámico de Riesgo (IDR)** como combinación ponderada lineal de los componentes biomecánicos y ambientales.
- Incorporar la metodología de Capacidad de Carga Turística de Cifuentes [12] como factor de corrección a nivel de ruta complementario al IDR por segmento.
- Construir un motor de enrutamiento topológico con pgRouting con costos asimétricos en los arcos del grafo de red.
- Visualizar el IDR como mapa de calor interactivo en Vue.js con MapLibre GL JS.

## 3. Materiales y Métodos

### 3.1 Enfoque metodológico

El presente trabajo se enmarca en **Design Science Research (DSR)** [16], paradigma de investigación apropiado para estudios cuyo aporte central es un **artefacto de software** que resuelve un problema previamente caracterizado en la literatura. DSR articula seis actividades: (i) identificación del problema, (ii) definición de objetivos de la solución, (iii) diseño y desarrollo del artefacto, (iv) demostración, (v) evaluación y (vi) comunicación. En este trabajo se cubren íntegramente las actividades (i)–(iv) y la actividad (vi); la actividad (v) —evaluación empírica con usuarios reales— se delimita explícitamente como trabajo futuro (sección 6.1), y este alcance acotado es una decisión metodológica consciente, no una omisión.

La construcción del artefacto se gestionó bajo el framework **Scrum**, con sprints de duración fija y revisión incremental al final de cada uno. Esto permitió alinear el desarrollo iterativo del prototipo con las fases epistémicas de DSR sin sacrificar trazabilidad: cada sprint se cerró con un incremento funcional revisado contra los objetivos específicos del trabajo.

**Tabla 1.** Mapeo de actividades DSR a sprints de desarrollo

| Actividad DSR | Sprint | Producto del incremento |
|---|---|---|
| Identificación del problema | Sprint 0 | Revisión sistemática de literatura y caracterización del hueco |
| Definición de objetivos | Sprint 0 | Especificación funcional y criterios de aceptación |
| Diseño y desarrollo | Sprint 1 | Capa de datos: PostGIS + pgRouting, ingesta GPX, geometrías 3D |
| Diseño y desarrollo | Sprint 2 | Implementación de los modelos biomecánicos (módulos `vel`, `met`) |
| Diseño y desarrollo | Sprint 3 | Integración climática (módulo `cli`) y motor IDR (módulo `rie`) |
| Diseño y desarrollo | Sprint 4 | Capa de presentación: mapa de calor en Vue 3 + MapLibre GL JS |
| Demostración | Sprint 5 | Despliegue en contenedores Docker y pruebas con rutas reales |

### 3.2 Fase de fundamentación: revisión sistemática de literatura

La identificación de los modelos científicos que sustentan el IDR se realizó mediante una búsqueda sistemática en **Google Scholar, Semantic Scholar y Connected Papers**, empleando términos clave asociados a la biomecánica de la marcha, el costo metabólico de transporte, las funciones de velocidad en senderismo y el enrutamiento espacial dinámico. Los criterios de inclusión fueron: (a) modelos con fundamento experimental publicados en revistas con revisión por pares o reportes técnicos institucionales, (b) aplicabilidad demostrada a marcha humana en terreno irregular, y (c) disponibilidad de la formalización matemática completa. Se excluyeron trabajos limitados a marcha en plano o sin parámetros publicados.

El cribado, la organización temática y la síntesis de los documentos recuperados se apoyaron en **NotebookLM** para extraer de forma estructurada los hallazgos relevantes de cada fuente. La formalización matemática de los modelos seleccionados —Minetti, Irmischer-Clarke y Pandolf— y su adaptación algorítmica al IDR se asistió con el modelo de lenguaje **Claude (Opus)**, verificando en cada caso la correspondencia entre las ecuaciones implementadas en el sistema y sus fuentes científicas originales mediante revisión manual cruzada por al menos dos miembros del equipo.

### 3.3 Fase de diseño: arquitectura del sistema

RiskTrail adopta una arquitectura desacoplada en tres capas. La capa de datos emplea **PostgreSQL 16 con PostGIS 3.4 y pgRouting 3.6** para almacenamiento y análisis de geometrías tridimensionales en SRID 4326. La capa lógica implementa un microservicio asíncrono en **FastAPI (Python 3.12)** con SQLAlchemy y GeoAlchemy2, organizado en cinco módulos de dominio independientes:

- `rut` — segmentación de rutas y cálculo de gradientes a partir de GPX.
- `vel` — modelo de velocidad predictiva (Irmischer-Clarke).
- `met` — modelo metabólico (Minetti + Pandolf con carga).
- `cli` — orquestación climática (Open-Meteo + cálculo WBGT).
- `rie` — motor de riesgo (composición del IDR).

La capa de presentación es una aplicación de página única en **Vue 3** con TypeScript, Pinia, MapLibre GL JS y Tailwind CSS. La tabla 2 resume el stack tecnológico y la Figura 6 ilustra la arquitectura.

**Tabla 2.** Stack tecnológico de RiskTrail

| Capa | Tecnología |
|---|---|
| Base de datos | PostgreSQL 16, PostGIS 3.4, pgRouting 3.6 |
| Backend | FastAPI, SQLAlchemy, GeoAlchemy2 |
| Frontend | Vue 3, MapLibre GL JS, Pinia |
| Contenedores | Docker, Docker Compose |
| Datos clima | API Open-Meteo (código abierto) |

*[Figura 6. Diagrama de arquitectura de tres capas de RiskTrail — imagen por insertar]*

### 3.4 Fase de construcción: modelos biomecánicos

El sistema RiskTrail no desarrolla modelos matemáticos propios: adopta tres fórmulas científicas validadas en la literatura y las combina en un índice compuesto.

**Velocidad predictiva.** La velocidad de caminata según la inclinación del terreno se estima con la función de Irmischer y Clarke [6]:

$$v(i) = \left[0.11 + e^{-(i + 0.0506)^2 / (2 \cdot 0.2043^2)}\right] \cdot 3.6 \quad (1)$$

donde $v$ es la velocidad en km/h e $i$ el gradiente como fracción decimal. Se eligió Irmischer-Clarke por sobre Tobler [5] porque, en pendientes pronunciadas (|i| > 0.30), Tobler predice velocidades excesivamente altas en descenso que no corresponden al comportamiento humano real de marcha cautelosa — limitación documentada por Campbell et al. [7] al comparar contra trazas GPS de excursionistas.

**Costo metabólico de transporte.** El costo de transporte $C(i)$ en J/(kg·m) se calcula con el Polinomio de Minetti [1], válido para $i \in [-0.45, +0.45]$:

$$C(i) = 280.5\,i^5 - 58.7\,i^4 - 76.8\,i^3 + 51.9\,i^2 + 19.6\,i + 2.5 \quad (2)$$

Esta fórmula no es simétrica respecto al signo de $i$: dentro del rango implementado, el costo de ascenso supera siempre al costo de descenso de igual magnitud, con un mínimo de costo de transporte entre $i=-0.10$ y $i=-0.20$ (descenso suave, $C\approx1.1$ J/(kg·m)) y un incremento progresivo conforme el descenso se vuelve más pronunciado ($C\approx3.6$ J/(kg·m) en $i=-0.45$), reflejando la transición de un patrón de marcha eficiente a uno de frenado muscular excéntrico. Esta no linealidad —y no una inversión de la asimetría ascenso/descenso— es la base sobre la que el sistema diferencia el costo metabólico por dirección de marcha.

**Esfuerzo con carga.** Para excursionistas con carga $L$ (kg) se aplica la ecuación de Pandolf [15]:

$$M = 1.5W + 2.0(W+L)\left(\frac{L}{W}\right)^2 + n(W+L)(1.5V^2 + 0.35VG) \quad (3)$$

donde $W$ es el peso corporal (kg), $V$ la velocidad (m/s), $G$ el gradiente (%) y $n$ el coeficiente de terreno (1.0 asfalto; 1.2 tierra; 2.1 barro). En la implementación, la ecuación (3) requiere la velocidad calculada por (1) como entrada; el orquestador de la API (capa de aplicación) garantiza que los módulos `vel` y `met` se ejecuten en el orden de dependencia correcto antes de invocar a `rie`.

### 3.5 Fase de construcción: modelado del estrés climático

El estrés térmico se cuantifica mediante una estimación del índice de Globo de Bulbo Húmedo (WBGT) a partir de las variables disponibles en Open-Meteo:

$$WBGT \approx 0.7\,T_w + 0.2\,T_g + 0.1\,T_a \quad (4)$$

donde $T_w$, $T_g$ y $T_a$ son las temperaturas de bulbo húmedo, globo y ambiente respectivamente. La **deriva cardiovascular** [3] se modela como un factor temporal acumulativo: tras superar 20 minutos bajo condiciones por encima del umbral crítico (WBGT > 28 °C), el sistema introduce una penalización progresiva sobre los segmentos siguientes que refleja la pérdida acumulada de capacidad aeróbica documentada por Maughan et al. [2]. La **degradación tribológica** se modela como factor activado por la combinación de pendiente descendente superior al 10 % y precipitación reciente, reflejando la pérdida de coeficiente de fricción en superficies húmedas reportada por Lockhart et al. [4].

### 3.6 Formalización del Índice Dinámico de Riesgo (IDR)

El IDR es la contribución central de software de este trabajo: una suma ponderada lineal de cuatro componentes normalizados en $[0,1]$, con los pesos actuales del prototipo ya sustituidos:

$$IDR(s) = 0.35\,\tilde{M}(s) + 0.25\,\tilde{V}(s) + 0.25\,\tilde{C}(s) + 0.15\,\tilde{T}(s) \quad (5)$$

Los cuatro componentes, todos normalizados en $[0,1]$:
- **Metabólico** ($\tilde{M}$) — costo de transporte de Minetti (ec. 2) ajustado por carga según Pandolf (ec. 3), normalizado contra el máximo teórico en $|i|=0.45$.
- **Degradación de velocidad** ($\tilde{V}$) — proporción de velocidad perdida respecto al óptimo de la ecuación (1); penaliza tramos donde la marcha se ralentiza significativamente.
- **Climático** ($\tilde{C}$) — derivado del WBGT (ec. 4), modulado por la deriva cardiovascular acumulada (sección 3.5).
- **Terreno** ($\tilde{T}$) — activado por pendiente descendente combinada con precipitación reciente (sección 3.5).

El peso mayor recae en el componente metabólico, presente en toda marcha; la degradación de velocidad y el estrés climático actúan como amplificadores comparables del esfuerzo percibido; el componente de terreno recibe el peso menor por ser condicional a la precipitación reciente y, por tanto, presente solo en una fracción de los recorridos. **Este conjunto de pesos constituye una propuesta inicial razonada, no el resultado de calibración empírica**; dicha calibración es parte explícita del protocolo de validación futura (sección 6.1).

La puntuación resultante $IDR(s) \in [0, 1]$ se mapea a cinco niveles discretos alineados con la metodología MIDE [13]:

**Tabla 3.** Escala del Índice Dinámico de Riesgo

| Nivel | Rango IDR | Condición predominante | Color / Acción |
|---|---|---|---|
| 1 | [0.00, 0.20) | Sin riesgos relevantes | Verde / Sin restricción |
| 2 | [0.20, 0.40) | Fatiga moderada esperada | Amarillo / Recomendación |
| 3 | [0.40, 0.60) | Estrés térmico o velocidad degradada | Naranja / Alerta |
| 4 | [0.60, 0.80) | Riesgo tribológico alto | Rojo / Advertencia |
| 5 | [0.80, 1.00] | Peligro extremo combinado | Morado / Restricción |

### 3.7 Capacidad de carga turística como factor a nivel de ruta

Complementariamente al IDR por segmento, el sistema incorpora la **metodología de Capacidad de Carga Turística (CCR)** de Cifuentes [12] como factor agregado a nivel de ruta completa. La CCR estima la afluencia máxima admisible aplicando factores de corrección físicos, ambientales y de manejo a una capacidad teórica inicial. En la implementación actual, el CCR se calcula como propiedad independiente de la ruta (módulo `rie`, función dedicada) y se reporta junto al IDR como información de gestión turística. **La fusión metodológica del CCR agregado con el IDR dinámico por segmento —de modo que la capacidad de carga ambiental module también el riesgo individual reportado al excursionista— constituye trabajo futuro (sección 6.2).**

### 3.8 Procesamiento espacial

Los archivos GPX se transforman en linestrings 3D en la base de datos. La función `ST_3DDistance` de PostGIS extrae la distancia planimétrica y el diferencial de elevación entre vértices para calcular gradientes exactos. pgRouting construye un grafo topológico con **costos asimétricos**: el costo directo emplea $C(+i)$ de la ecuación (2) y el costo inverso $C(-i)$, reflejando la asimetría fisiológica ascenso-descenso. Los datos meteorológicos se recuperan de forma asíncrona desde Open-Meteo en el centroide de cada segmento.

## 4. Resultados

El prototipo de RiskTrail fue desplegado en contenedores Docker y probado con archivos GPX de rutas representativas de parques nacionales panameños. Esta sección presenta resultados de **viabilidad técnica y consistencia interna**; la evaluación empírica del IDR contra riesgo percibido o incidentes reales **no forma parte del alcance de este trabajo** (decisión metodológica explicitada en sección 3.1) y se presenta como protocolo concreto en la sección 6.

### 4.1 Rendimiento del motor de cálculo

Se midió el tiempo de respuesta de la API ejecutando el análisis completo (subida + segmentación + biomecánica) sobre los dos GPX reales descritos en la sección 3.2. Con segmentación de 100 m, la ruta del Volcán Barú (27.82 km) se dividió en 279 segmentos con una respuesta de 1.38 s, y el Camino de Cruces (23.53 km) en 236 segmentos con 1.33 s. Reduciendo la longitud de segmento a 50 m, Volcán Barú generó 557 segmentos con una respuesta de 1.62 s. Estos tiempos confirman que la arquitectura asíncrona sostiene respuestas por debajo de los 2 segundos para rutas de hasta ~560 segmentos; no se evaluó el comportamiento para rutas sustancialmente más largas.

### 4.2 Comparación de modelos de velocidad

**Tabla 4.** Comparación de modelos de velocidad implementados

| Modelo | Forma funcional | Comportamiento en pendientes extremas (|i| > 0.30) | Asimetría asc/desc |
|---|---|---|---|
| Naismith [8] | Lineal | No modela; extrapola sin sustento físico | No |
| Tobler [5] | Gaussiana asimétrica | Sobrestima velocidad en descensos pronunciados respecto a observaciones GPS [7] | Sí (asimetría irreal) |
| **Irmischer-Clarke [6]** | Gaussiana con parámetros recalibrados | Predicción consistente con literatura biomecánica en todo el rango | Sí (asimetría documentada) |

La diferencia operacional entre Tobler e Irmischer-Clarke es la calibración de los parámetros de la curva gaussiana sobre datos empíricos modernos; en términos prácticos, para los gradientes típicos de senderos panameños esto se traduce en estimaciones de tiempo más conservadoras y consistentes con la marcha cautelosa observada en descensos pronunciados.

### 4.3 Consistencia con la asimetría fisiológica

Se verificó el comportamiento de la asimetría ascenso-descenso con datos reales de Volcán Barú. Un segmento en ascenso con pendiente +33 % obtuvo un costo de transporte de 12.16 J/(kg·m) y una puntuación de riesgo de 35 (nivel 2); un segmento en descenso de magnitud comparable (-35 %) obtuvo 2.91 J/(kg·m) y una puntuación de riesgo de 17 (nivel 1). El sistema reproduce así, de forma consistente con la ecuación (2), que **el ascenso es siempre más costoso metabólicamente que el descenso de igual magnitud** dentro del rango $i \in [-0.45, 0.45]$; en los datos de prueba no se observó ningún caso donde el descenso superara al ascenso equivalente. Esto corrige una hipótesis inicial del equipo —que el descenso pronunciado sería más riesgoso por fatiga excéntrica—: dentro del rango de pendientes modelado, el componente metabólico-mecánico siempre favorece el ascenso como dirección de mayor riesgo; un riesgo elevado en descensos pronunciados, cuando ocurre, debe provenir del componente de terreno o clima (ec. 5), no del componente metabólico. Aun así, el sistema representa una diferencia cualitativa respecto a herramientas como AllTrails o Wikiloc, que tratan los segmentos como simétricos sin distinguir dirección de marcha.

### 4.4 Sensibilidad climática

El módulo de simulación climática (Figura 4) permite comparar la misma ruta bajo distintas condiciones ambientales. Se simuló el escenario `heavy_rain` (35 mm de precipitación) sobre las dos rutas de prueba mediante el endpoint `/simulate`. En Camino de Cruces la distribución de niveles de riesgo por segmento no cambió respecto al clima real (185 segmentos en nivel 1, 51 en nivel 2 antes y después). En Volcán Barú —la ruta con pendientes más pronunciadas disponible— la simulación movió 9 segmentos de nivel 1 a nivel 2, sin que ningún segmento alcanzara los niveles 4 o 5; la puntuación máxima de riesgo se mantuvo en 46 (nivel 3) antes y después de la simulación. Este resultado es más modesto que lo planteado inicialmente y se reporta como tal: el componente de terreno $\tilde{T}$ (ec. 5) responde a la precipitación simulada, pero con una magnitud insuficiente, en los datos de prueba disponibles, para producir reclasificaciones de varios niveles. Calibrar la sensibilidad de $\tilde{T}$ contra escenarios más severos o sobre rutas con descensos más prolongados queda como trabajo futuro (sección 6.2).

### 4.5 Visualización del IDR

El mapa de calor del IDR (Figura 2) permite identificar de un vistazo los tramos del recorrido que requieren precaución: segmentos seguros en verde (nivel 1) y de mayor riesgo en rojo o morado (niveles 4 y 5). La escala MIDE aparece en la barra lateral como referencia de dificultad reconocida internacionalmente, dando contexto inmediato al usuario sin necesidad de interpretar valores numéricos del IDR.

*[Figura 1. Flujo del sistema — Figura 2. Mapa IDR — Figura 3. Detalle de segmento crítico — Figura 4. Simulación climática — Figura 5. Selección de ruta óptima con pgRouting]*

## 5. Discusión

Los resultados muestran que es **técnicamente viable** integrar modelos biomecánicos con datos espaciales y meteorológicos en tiempo real para producir una clasificación de riesgo por segmento, superando arquitectónicamente el enfoque estático de plataformas como AllTrails o Wikiloc.

El modelo de velocidad de Irmischer-Clarke demostró ser adecuado para el contexto panameño en términos de consistencia con la literatura, especialmente en senderos con pendientes pronunciadas donde la formulación previa de Tobler produce estimaciones que sobrepasan el rango observado en estudios GPS contemporáneos [7]. La variabilidad individual de la marcha [7] abre la puerta a personalizar las estimaciones del sistema en versiones futuras.

La incorporación del WBGT como disparador de la deriva cardiovascular es especialmente relevante para el clima tropical panameño. Maughan et al. [2] documentan que en entornos con humedad absoluta alta el agotamiento se instala hasta un 40 % más rápido que en condiciones temperadas, factor ignorado por las herramientas actuales.

### 5.1 Sobre el alcance de las afirmaciones

Este trabajo presenta un **prototipo arquitectónico y un índice propuesto**, no un sistema de seguridad validado empíricamente. El IDR es una **combinación razonada** de modelos individualmente validados en su literatura original; **la validez del índice compuesto y sus pesos como predictores de riesgo real es una hipótesis abierta**. El sistema está pensado como **herramienta de apoyo a la decisión**, no como garantía de seguridad: su uso en campo debe complementarse siempre con el criterio del excursionista y con información oficial de los gestores del área protegida.

### 5.2 Limitaciones del prototipo

1. **Ausencia de validación de campo.** Las clasificaciones del IDR no han sido contrastadas contra percepción de esfuerzo, tiempos reales de recorrido ni incidentes documentados.
2. **Pesos del IDR sin calibración empírica.** Los valores $w_m=0.35$, $w_v=0.25$, $w_c=0.25$, $w_t=0.15$ son una propuesta inicial razonada, no el resultado de ajuste contra datos reales. Pesos calibrados podrían diferir significativamente.
3. **Resolución del DEM.** La precisión de los gradientes calculados depende de la resolución del Modelo Digital de Elevación disponible, lo que puede subestimar pendientes en tramos cortos muy escarpados.
4. **Perfil del excursionista genérico.** El sistema no considera condición física individual, edad, sexo, ni historial de lesiones.
5. **Dependencia de conectividad.** El sistema requiere internet para obtener datos meteorológicos en tiempo real, limitando su uso en senderos sin cobertura.
6. **WBGT estimado, no medido.** La ecuación (4) se aproxima a partir de variables disponibles en Open-Meteo; un WBGT instrumentado en sitio sería más preciso.
7. **CCR y IDR aún desacoplados.** La capacidad de carga turística se calcula a nivel de ruta pero no modula aún el IDR por segmento (ver sección 6.2).
8. **Sensibilidad insuficiente del componente de terreno.** Las pruebas de simulación climática (sección 4.4) mostraron que $\tilde{T}$ responde débilmente a precipitación simulada incluso en la ruta más empinada disponible; no se observaron reclasificaciones a niveles 4-5 en los escenarios probados (ver sección 6.2).

## 6. Conclusiones y trabajo futuro

RiskTrail demuestra la **viabilidad técnica** de un sistema de evaluación dinámica de riesgo que integra modelos biomecánicos validados en literatura, datos meteorológicos en tiempo real y enrutamiento espacial adaptativo. La arquitectura desacoplada en tres capas, la formalización del IDR como combinación ponderada lineal de cuatro componentes (ec. 5) y la reproducción de la asimetría fisiológica ascenso-descenso constituyen las contribuciones de software principales de este trabajo. La metodología DSR articulada sobre Scrum permitió mantener trazabilidad entre la fundamentación científica y los incrementos funcionales del artefacto.

El sistema sienta las bases para herramientas de planificación de senderismo en ecosistemas neotropicales panameños donde la variabilidad climática es extrema, sobre una arquitectura modular escalable.

### 6.1 Protocolo de validación de campo (corto plazo)

La prioridad inmediata es la calibración empírica del IDR. Se propone un estudio piloto en el Parque Nacional Camino de Cruces con el siguiente diseño:

- **Muestra:** N ≥ 20 excursionistas voluntarios estratificados por nivel de experiencia (principiante / intermedio / experto).
- **Rutas:** dos rutas representativas del parque (una predominantemente ascendente, una mixta con descensos pronunciados).
- **Condiciones:** repetición de cada ruta en condición seca y dentro de las 24 h posteriores a precipitación.
- **Variables medidas:**
  - *Esfuerzo percibido* mediante escala de Borg RPE 6-20 al final de cada segmento principal.
  - *Tiempo real* de recorrido por segmento (cronometraje GPS).
  - *Incidentes* (resbalones, caídas, paradas no planificadas) registrados por el excursionista o un observador.
  - *Frecuencia cardiaca* opcional mediante monitor de muñeca compatible.
- **Métricas de éxito:**
  - Correlación de Spearman $\rho \geq 0.6$ entre IDR por segmento y RPE reportado.
  - Error porcentual medio en predicción de tiempo de recorrido ≤ 15 % respecto al cronometraje GPS.
  - Concordancia ≥ 70 % entre nivel IDR predicho y nivel MIDE asignado por excursionistas expertos en post-test.
- **Salida:** recalibración de los pesos $w_m, w_v, w_c, w_t$ por regresión sobre los datos recogidos, comparada contra los valores iniciales propuestos en la ecuación (5).

### 6.2 Mediano plazo

- **Fusión metodológica CCR–IDR.** El sistema ya calcula la Capacidad de Carga Turística de Cifuentes a nivel de ruta como factor independiente; el siguiente paso es integrar la CCR como modulador del IDR por segmento, de modo que un sendero con capacidad excedida eleve el componente ambiental del riesgo reportado al excursionista.
- **Calibración de sensibilidad del componente de terreno ($\tilde{T}$).** Las pruebas de simulación climática (sección 4.4) mostraron una respuesta menor a la esperada del componente tribológico ante precipitación simulada; se requiere ajustar su función de activación o su peso ($w_t$) contra escenarios más severos y rutas con descensos más prolongados.
- **Telemetría GPS en tiempo real** para actualizar el IDR del recorrido restante a medida que el excursionista avanza.
- **Personalización del perfil del usuario** (edad, condición física autoreportada, historial de lesiones), aprovechando la variabilidad individual de la marcha documentada por Campbell et al. [7].
- **Módulo de recomendación de rutas óptimas** mediante pgRouting con función de costo basada en IDR calibrado.
- **Sensores IoT** (anemómetro, pluviómetro, termohigrómetro) instalados en senderos críticos para reducir la dependencia de Open-Meteo en zonas sin cobertura celular y mejorar la precisión del WBGT.

## Referencias

[1] A. E. Minetti, C. Moia, G. S. Roi, D. Susta y G. Ferretti, "Energy cost of walking and running at extreme uphill and downhill slopes," *J. Appl. Physiol.*, vol. 93, no. 3, pp. 1039-1046, 2002.

[2] R. J. Maughan, J. E. Wingo y E. F. Coyle, "Delineating the impacts of air temperature and humidity for endurance exercise," *Exp. Physiol.*, vol. 107, no. 5, pp. 386-395, 2022.

[3] L. B. Rowell, "Cardiovascular drift during prolonged exercise: new perspectives," *Med. Sci. Sports Exerc.*, vol. 15, no. 4, pp. 367-379, 1983.

[4] T. E. Lockhart et al., "Slips and falls," Arizona State University, Ira A. Fulton Schools of Engineering, 2016.

[5] W. Tobler, "Three presentations on geographical analysis and modeling," National Center for Geographic Information and Analysis, Informe Técnico 93-1, 1993.

[6] I. J. Irmischer y K. C. Clarke, "Hiking with Tobler: tracking movement and calibrating a cost function for personalized 3D accessibility," *Findings*, 2018.

[7] M. J. Campbell, P. E. Dennison y M. P. Thompson, "Predicting the variability in pedestrian travel rates and times using crowdsourced GPS data," *Comput. Environ. Urban Syst.*, vol. 97, p. 101866, 2022.

[8] W. Naismith, "Naismith's rule," *Scottish Mountaineering Club Journal*, vol. 2, no. 3, p. 136, 1892.

[9] The PostGIS Development Team, "PostGIS 3.4 Reference Manual," 2024. [En línea]. Disponible: https://postgis.net/docs/

[10] pgRouting Development Team, "pgRouting 3.6 Documentation," 2024. [En línea]. Disponible: https://docs.pgrouting.org/

[11] S. Choosumrong, R. Raghavan, V. Pundt y N. Intajag, "Implementation of dynamic routing as a web service for emergency routing decision planning," *Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci.*, vol. XL-2, pp. 59-63, 2014.

[12] M. Cifuentes, "Determinación de capacidad de carga turística en áreas protegidas," CATIE, Turrialba, Informe Técnico 194, 1992.

[13] Montaña Segura, "Manual MIDE: Método para Información de Excursiones," Federación Española de Deportes de Montaña y Escalada, s.f.

[14] Geoversity, "GIS in the jungle: Experiential Environmental Education (EEE) in Panama," 2021.

[15] K. B. Pandolf, B. Givoni y R. F. Goldman, "Predicting energy expenditure with loads while standing or walking very slowly," *J. Appl. Physiol.*, vol. 43, no. 4, pp. 577-581, 1977.

[16] K. Peffers, T. Tuunanen, M. A. Rothenberger y S. Chatterjee, "A design science research methodology for information systems research," *J. Manage. Inf. Syst.*, vol. 24, no. 3, pp. 45-77, 2007.