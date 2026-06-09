# JIC-Geo — Índice Dinámico de Riesgo en Senderismo

JIC-Geo es un Sistema de Información Geográfica (SIG) y motor de enrutamiento que calcula un índice dinámico de riesgo para rutas de senderismo. Correlaciona modelos biométricos (costo metabólico, perfiles de velocidad) con datos espaciales (elevaciones DEM, gradientes) y condiciones meteorológicas en tiempo real (WBGT, precipitación) para identificar problemas de seguridad y diseñar rutas óptimas con enrutamiento adaptado al clima.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy (GeoAlchemy2) · Alembic · Scipy |
| **Frontend** | Vue 3 (Vite + TS) · Pinia · MapLibre GL JS · Tailwind CSS · DaisyUI |
| **Base de Datos** | PostgreSQL 16 · PostGIS (Espacial y Ráster) · pgRouting |
| **Contenedores** | Docker · Docker Compose |

---

## Estructura de Directorios

```
JIC-Geo/
├── backend/                  # API REST FastAPI y tests unitarios
│   ├── app/
│   │   ├── api/v1/           # Rutas de la API (endpoints REST)
│   │   ├── db/               # Modelos SQLAlchemy y sesiones de DB
│   │   └── modules/          # Servicios de dominio (dat, rut, vel, met, prf, cli, sim, rie, grf)
│   └── tests/                # Suites de tests unitarios e integración con Pytest
├── frontend/                 # Aplicación de Página Única en Vue 3
│   ├── src/
│   │   ├── assets/           # Estilos (directivas Tailwind)
│   │   ├── components/       # Componentes Vue (map, sidebar, simulation, upload)
│   │   ├── composables/      # Helpers de estado compartido y controladores de tema
│   │   └── stores/           # Stores de Pinia (estado global)
│   ├── tailwind.config.cjs
│   └── postcss.config.cjs
├── db/                       # Scripts SQL para inicializar extensiones de la base de datos
├── docs/                     # Requerimientos, fórmulas, especificaciones y arquitectura
│   ├── architecture.md       # Reglas de arquitectura a seguir
│   ├── Requerimientos.md     # Requerimientos base del sistema
│   ├── Formulas.md           # Fórmulas biomecánicas y climáticas
│   ├── mitigacion.md         # Optimizaciones y mitigaciones de PostGIS
│   ├── plan.md               # Plan de implementación en 8 fases
│   └── issues.md             # Backlog de issues por fase
├── data/                     # Archivos DEM y muestras GPX (en .gitignore)
└── docker-compose.yml        # Composición Docker para la base de datos
```

---

## Inicio Rápido (Docker)

### Requisitos
Tener Docker y `make` instalados.

### Configuración y ejecución
1. Copiar la plantilla de variables de entorno:
   ```bash
   cp .env.example .env
   ```
2. Levantar la infraestructura:
   ```bash
   make dev
   ```
   *Inicia PostgreSQL + PostGIS + pgRouting en segundo plano.*

3. Levantar el servidor de desarrollo del frontend:
   ```bash
   make frontend
   ```
   *El frontend corre en `http://localhost:5173`.*

4. Levantar el backend localmente (opcional si no usás Docker):
   ```bash
   make backend
   ```
   *La API estará disponible en `http://localhost:8000/docs` (Swagger UI).*

---

## Instalación Nativa (macOS — alternativa sin Docker)

Si preferís correr la base de datos de forma nativa con Homebrew:

1. **Instalar PostgreSQL y PostGIS:**
   ```bash
   brew install postgresql@16 postgis pgrouting
   ```

2. **Iniciar el servicio de base de datos:**
   ```bash
   brew services start postgresql@16
   ```

3. **Inicializar la base de datos:**
   ```bash
   createdb jicgeo
   psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS postgis_raster;"
   psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"
   ```

4. **Verificar las instalaciones:**
   ```bash
   psql jicgeo -c "SELECT postgis_full_version();"
   psql jicgeo -c "SELECT pgr_version();"
   ```

---

## Comandos de Desarrollo

El `Makefile` en la raíz automatiza las tareas más comunes:

| Comando | Acción |
|---|---|
| `make dev` | Levanta el contenedor de la base de datos PostgreSQL/PostGIS. |
| `make db-only` | Inicia solo el contenedor de DB (útil para desarrollo nativo del backend). |
| `make migrate` | Aplica las migraciones de Alembic a la base de datos activa. |
| `make backend` | Inicia la aplicación FastAPI localmente con reload habilitado. |
| `make frontend` | Lanza el servidor de desarrollo Vite para el frontend. |
| `make lint` | Ejecuta `ruff` y `mypy` sobre el código del backend. |
| `make test` | Corre los tests unitarios de Python con `pytest`. |
| `make db-reset` | Destruye el volumen de la DB y lo reconstruye desde cero (⚠️ destructivo). |

---

## Documentación Interna

Para detalles específicos sobre fórmulas, optimizaciones e issues:
* **Reglas de Arquitectura:** [architecture.md](docs/architecture.md)
* **Requerimientos del Sistema:** [Requerimientos.md](docs/Requerimientos.md)
* **Fórmulas Biomecánicas y Climáticas:** [Formulas.md](docs/Formulas.md)
* **Optimizaciones y Mitigaciones PostGIS:** [mitigacion.md](docs/mitigacion.md)
* **Plan de Implementación:** [plan.md](docs/plan.md)
* **Backlog de Issues:** [issues.md](docs/issues.md)
