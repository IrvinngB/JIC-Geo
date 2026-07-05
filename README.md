# RiskTrail — Índice Dinámico de Riesgo en Senderismo

RiskTrail es un Sistema de Información Geográfica (SIG) y motor de enrutamiento que calcula un índice dinámico de riesgo para rutas de senderismo. Correlaciona modelos biométricos (costo metabólico, perfiles de velocidad) con datos espaciales (elevaciones DEM, gradientes) y condiciones meteorológicas en tiempo real (WBGT, precipitación) para identificar problemas de seguridad y diseñar rutas óptimas con enrutamiento adaptado al clima.

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
RiskTrail/
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

## Instalación Nativa (Linux — Ubuntu / Debian)

Si estás en Linux y preferís no usar Docker:

1. **Agregar el repositorio de PostgreSQL:**
   ```bash
   sudo apt install -y curl ca-certificates
   curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
   echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
     | sudo tee /etc/apt/sources.list.d/pgdg.list
   sudo apt update
   ```

2. **Instalar PostgreSQL 16, PostGIS y pgRouting:**
   ```bash
   sudo apt install -y postgresql-16 postgresql-16-postgis-3 postgresql-16-pgrouting
   ```

3. **Iniciar el servicio:**
   ```bash
   sudo systemctl enable --now postgresql
   ```

4. **Inicializar la base de datos:**
   ```bash
   sudo -u postgres createdb jicgeo
   sudo -u postgres psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   sudo -u postgres psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS postgis_raster;"
   sudo -u postgres psql jicgeo -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"
   ```

5. **Verificar las instalaciones:**
   ```bash
   sudo -u postgres psql jicgeo -c "SELECT postgis_full_version();"
   sudo -u postgres psql jicgeo -c "SELECT pgr_version();"
   ```

> **Nota:** Para conectarte sin `sudo -u postgres`, configurá un usuario de PostgreSQL propio:
> ```bash
> sudo -u postgres createuser --superuser $USER
> ```

---

## Instalación Nativa (Windows)

> **Recomendación fuerte:** usá **WSL2** (Windows Subsystem for Linux). Es el camino más sencillo y evita problemas de compatibilidad con `make` y herramientas de terminal.

### Opción A — WSL2 (Recomendado)

1. **Instalar WSL2** desde PowerShell (admin):
   ```powershell
   wsl --install
   ```
   Esto instala Ubuntu por defecto. Reiniciá cuando lo pida.

2. **Dentro de WSL2**, seguí los mismos pasos de la sección **Linux** arriba.

3. Para correr Docker Desktop desde WSL2, activá la integración en **Docker Desktop → Settings → Resources → WSL Integration**.

### Opción B — Windows Nativo

> ⚠️ `make` no está disponible en Windows nativo. Necesitás instalar `make` via [Chocolatey](https://chocolatey.org/) o usar los comandos equivalentes directamente.

1. **Instalar `make`** (PowerShell admin):
   ```powershell
   choco install make
   ```

2. **Instalar PostgreSQL 16** desde el instalador oficial:
   [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
   - Durante la instalación, incluir Stack Builder.
   - Desde Stack Builder, instalar **PostGIS** y **pgRouting** para PostgreSQL 16.

3. **Inicializar la base de datos** desde la terminal de PostgreSQL (psql) o pgAdmin:
   ```sql
   CREATE DATABASE jicgeo;
   \c jicgeo
   CREATE EXTENSION IF NOT EXISTS postgis;
   CREATE EXTENSION IF NOT EXISTS postgis_raster;
   CREATE EXTENSION IF NOT EXISTS pgrouting;
   ```

4. **Instalar Node.js** (para el frontend) desde [https://nodejs.org/](https://nodejs.org/).

5. **Instalar Python 3.12** desde [https://www.python.org/](https://www.python.org/) e instalar `uv`:
   ```powershell
   pip install uv
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

---

## Licencia

Software propietario. Todos los derechos reservados. Ver [LICENSE](LICENSE).
* **Backlog de Issues:** [issues.md](docs/issues.md)
