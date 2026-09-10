<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import AppIcon, { type IconName } from '@/components/icons/AppIcon.vue'

const { currentTheme, toggleTheme } = useTheme()

const painPoints = [
  { icon: 'map' as IconName, title: 'Mapas estáticos', text: 'Solo muestran distancia y elevación, ignorando el estado del terreno.' },
  { icon: 'sun' as IconName, title: 'Clima ignorado', text: 'Un sendero "moderado" en sol puede ser peligroso bajo lluvia tropical.' },
  { icon: 'thermometer' as IconName, title: 'Humedad extrema', text: 'Drena tu energía sin advertencia, aumentando el riesgo de agotamiento.' },
  { icon: 'alert-triangle' as IconName, title: 'Descensos peligrosos', text: 'Bajar una loma mojada es más riesgoso que subirla: resbalones y caídas.' },
]

const features: Array<{ icon: IconName; title: string; description: string }> = [
  {
    icon: 'compass',
    title: 'Índice MIDE dinámico',
    description: 'Severidad, orientación y esfuerzo calculados tramo a tramo con modelos biomecánicos reales, no estimaciones genéricas.',
  },
  {
    icon: 'cloud-rain',
    title: 'Simulación climática',
    description: 'Compara la ruta en seco, lluvia o calor extremo. El clima ajusta el costo metabólico y el riesgo en vivo.',
  },
  {
    icon: 'route',
    title: 'Ruta óptima',
    description: 'El motor encuentra el camino de menor costo considerando pendiente, superficie, clima y tu perfil.',
  },
]

const steps = [
  { number: '01', title: 'Sube tu ruta', description: 'GPX o GeoJSON. Interpolamos elevación y corregimos puntos sueltos.' },
  { number: '02', title: 'Analizamos el esfuerzo', description: 'Velocidad, calorías, fatiga y riesgo por cada tramo del recorrido.' },
  { number: '03', title: 'Simula condiciones', description: 'Cambia el clima y observa cómo cambia el riesgo y el tiempo estimado.' },
  { number: '04', title: 'Encuentra el mejor camino', description: 'La ruta óptima evita los tramos más costosos según tu perfil.' },
]

const differentiators = [
  { icon: 'brain' as IconName, title: 'Motor biomecánico real', description: 'Costo metabólico con fórmulas científicas, no suposiciones.' },
  { icon: 'wind' as IconName, title: 'WBGT en vivo', description: 'Estrés térmico con temperatura, humedad y radiación solar.' },
  { icon: 'shield' as IconName, title: 'Alertas de fatiga', description: 'Detecta cuándo alcanzarás agotamiento severo.' },
  { icon: 'footprints' as IconName, title: 'Corrección GPS', description: 'Savitzky-Golay suaviza errores de elevación.' },
]

const impactMetrics = [
  { value: '40%', label: 'Menos accidentes', description: 'Reducción potencial de resbalones en descensos mojados.' },
  { value: 'Real', label: 'Biomecánica', description: 'Modelos científicos, no estimaciones de fitness apps.' },
  { value: 'Vivo', label: 'Clima en tiempo real', description: 'Datos meteorológicos cruzados con cada tramo.' },
]

const techStack = [
  { category: 'Backend', items: ['Python', 'FastAPI', 'PostgreSQL', 'pgRouting', 'PostGIS'] },
  { category: 'Frontend', items: ['Vue 3', 'TypeScript', 'MapLibre GL', 'Tailwind CSS', 'DaisyUI'] },
]

const authors = [
  {
    name: 'Irvin Benitez',
    role: 'Full Stack & Arquitectura',
    github: 'https://github.com/IrvinngB',
    githubUser: 'IrvinngB',
    portfolio: 'https://irvincodes.dev/',
    linkedin: 'https://www.linkedin.com/in/irvin-benitez-11313231b',
    avatar: 'https://avatars.githubusercontent.com/u/157191495',
  },
  {
    name: 'Kelvin He Wu',
    role: 'Backend',
    github: 'https://github.com/kelvinhe04',
    githubUser: 'kelvinhe04',
    portfolio: 'https://kelvin-he.netlify.app/',
    linkedin: 'https://www.linkedin.com/in/kelvin-he-wu/?locale=es',
    avatar: 'https://avatars.githubusercontent.com/u/91310516',
  },
  {
    name: 'Roy Barrera',
    role: 'Backend & Database',
    github: 'https://github.com/Roy-x24',
    githubUser: 'Roy-x24',
    linkedin: 'https://www.linkedin.com/in/roy-barrera-0077b1340/',
    avatar: 'https://ui-avatars.com/api/?name=Roy+Barrera&background=random',
  },
]
</script>

<template>
  <div class="min-h-screen bg-base-100 text-base-content">
    <!-- Navbar -->
    <header class="sticky top-0 z-50 border-b border-base-300/60 bg-base-100/80 backdrop-blur-lg">
      <nav class="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
        <div class="flex items-center gap-2">
          <AppIcon name="mountain" :size="22" class="text-primary" />
          <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-xl font-extrabold tracking-tight text-transparent">
            RiskTrail
          </span>
        </div>
        <div class="hidden items-center gap-1 sm:flex">
          <a href="#como-funciona" class="btn btn-ghost btn-sm text-base-content/60 hover:text-base-content">Cómo funciona</a>
          <a href="#equipo" class="btn btn-ghost btn-sm text-base-content/60 hover:text-base-content">Equipo</a>
          <button class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content" title="Cambiar tema" @click="toggleTheme">
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="18" />
          </button>
          <RouterLink to="/mapa" class="btn btn-primary btn-sm text-white">Abrir app</RouterLink>
        </div>
        <div class="flex items-center gap-2 sm:hidden">
          <button class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content" title="Cambiar tema" @click="toggleTheme">
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="18" />
          </button>
          <RouterLink to="/mapa" class="btn btn-primary btn-sm text-white">Abrir app</RouterLink>
        </div>
      </nav>
    </header>

    <!-- Hero -->
    <section class="relative overflow-hidden pb-20 pt-24 md:pb-28 md:pt-32">
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-success/8 via-base-100 to-primary/5"></div>
      <div class="pointer-events-none absolute -right-40 -top-40 h-[600px] w-[600px] rounded-full bg-primary/8 blur-3xl"></div>
      <div class="pointer-events-none absolute -bottom-40 -left-40 h-[500px] w-[500px] rounded-full bg-success/8 blur-3xl"></div>

      <div class="relative mx-auto max-w-6xl px-5">
        <div class="max-w-3xl">
          <div class="badge badge-success badge-outline mb-6 gap-2">
            <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-success"></span>
            Análisis biomecánico de senderos
          </div>
          <h1 class="text-4xl font-extrabold leading-[1.1] tracking-tight md:text-6xl">
            Conoce el riesgo
            <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-transparent">
              antes de caminarlo
            </span>
          </h1>
          <p class="mt-6 max-w-xl text-lg leading-relaxed text-base-content/70">
            Los mapas tradicionales ignoran un punto ciego: <strong class="text-base-content">cómo el entorno afecta tu cuerpo.</strong> Un sendero "moderado" puede ser letal tras un aguacero tropical.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <RouterLink to="/mapa" class="btn btn-primary btn-lg gap-2 text-white">
              Analizar mi ruta
              <AppIcon name="arrow-right" :size="20" />
            </RouterLink>
            <a href="#como-funciona" class="btn btn-ghost btn-lg">Cómo funciona</a>
          </div>
          <div class="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-sm text-base-content/50">
            <span class="flex items-center gap-2"><span class="h-1.5 w-1.5 rounded-full bg-primary"></span> MIDE dinámico</span>
            <span class="flex items-center gap-2"><span class="h-1.5 w-1.5 rounded-full bg-info"></span> Clima en vivo</span>
            <span class="flex items-center gap-2"><span class="h-1.5 w-1.5 rounded-full bg-secondary"></span> Ruta óptima</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Problem + Solution unified -->
    <section class="border-y border-base-300/60 bg-base-200/20 py-20">
      <div class="mx-auto max-w-6xl px-5">
        <!-- Problem -->
        <div class="mb-16">
          <div class="mb-10 max-w-2xl">
            <h2 class="text-3xl font-bold tracking-tight">El problema</h2>
            <p class="mt-2 text-base-content/60">Los mapas tradicionales ignoran cómo el entorno transforma tu cuerpo en tiempo real.</p>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div v-for="point in painPoints" :key="point.title" class="flex items-start gap-4 rounded-2xl border border-base-300/40 bg-base-100 p-5">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-error/10 text-error">
                <AppIcon :name="point.icon" :size="20" />
              </div>
              <div>
                <h3 class="font-bold text-sm">{{ point.title }}</h3>
                <p class="mt-1 text-xs leading-relaxed text-base-content/60">{{ point.text }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Solution -->
        <div>
          <div class="mb-10 max-w-2xl">
            <h2 class="text-3xl font-bold tracking-tight">La solución</h2>
            <p class="mt-2 text-base-content/60">Un sistema que transforma mapas estáticos en herramientas de seguridad vivas.</p>
          </div>
          <div class="grid gap-5 md:grid-cols-3">
            <article v-for="feature in features" :key="feature.title" class="group rounded-2xl border border-base-300/60 bg-base-100 p-6 transition hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl">
              <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary transition group-hover:bg-primary/20">
                <AppIcon :name="feature.icon" :size="24" />
              </div>
              <h3 class="text-lg font-bold">{{ feature.title }}</h3>
              <p class="mt-2 text-sm leading-relaxed text-base-content/60">{{ feature.description }}</p>
            </article>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="como-funciona" class="py-20">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-12 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Cómo funciona</h2>
          <p class="mt-2 text-base-content/60">De un archivo a una decisión informada en cuatro pasos.</p>
        </div>
        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="(step, i) in steps" :key="step.number" class="relative">
            <!-- Connector line (hidden on mobile, last item) -->
            <div v-if="i < steps.length - 1" class="absolute left-10 top-5 hidden h-px w-full bg-base-300/40 lg:block"></div>
            <div class="relative rounded-2xl border border-base-300/40 bg-base-100 p-6">
              <span class="inline-flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-success to-primary text-sm font-extrabold text-white">{{ step.number }}</span>
              <h3 class="mt-4 font-bold">{{ step.title }}</h3>
              <p class="mt-2 text-sm leading-relaxed text-base-content/60">{{ step.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Why different + Impact -->
    <section class="border-y border-base-300/60 bg-base-200/20 py-20">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-12 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Por qué es diferente</h2>
          <p class="mt-2 text-base-content/60">No es una app de fitness. Es un motor de riesgo con ciencia real.</p>
        </div>

        <div class="grid gap-10 lg:grid-cols-5">
          <!-- Differentials -->
          <div class="grid gap-4 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-2">
            <div v-for="item in differentiators" :key="item.title" class="flex items-start gap-4 rounded-2xl border border-base-300/40 bg-base-100 p-5">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <AppIcon :name="item.icon" :size="20" />
              </div>
              <div>
                <h3 class="font-bold text-sm">{{ item.title }}</h3>
                <p class="mt-1 text-xs leading-relaxed text-base-content/60">{{ item.description }}</p>
              </div>
            </div>
          </div>

          <!-- Impact metrics -->
          <div class="flex flex-col gap-4 lg:col-span-2">
            <div v-for="metric in impactMetrics" :key="metric.label" class="flex items-center gap-4 rounded-2xl bg-base-100 p-5 shadow-sm border border-base-300/40">
              <div class="text-3xl font-extrabold text-success">{{ metric.value }}</div>
              <div>
                <div class="font-bold text-sm">{{ metric.label }}</div>
                <p class="text-xs text-base-content/50">{{ metric.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20">
      <div class="mx-auto max-w-6xl px-5">
        <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-success to-primary px-8 py-16 text-center shadow-xl">
          <div class="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-white/10 blur-3xl"></div>
          <div class="pointer-events-none absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-white/10 blur-3xl"></div>
          <h2 class="text-3xl font-extrabold text-white md:text-4xl">Tu próxima ruta, sin sorpresas</h2>
          <p class="mx-auto mt-4 max-w-xl text-white/80">Sube tu recorrido y obtén el análisis completo en segundos. Sin registro.</p>
          <RouterLink to="/mapa" class="btn btn-lg mt-8 gap-2 border-0 bg-white text-primary hover:bg-white/90">
            Empezar ahora
            <AppIcon name="arrow-right" :size="20" />
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Tech Stack -->
    <section class="border-y border-base-300/60 bg-base-200/20 py-16">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Stack tecnológico</h2>
          <p class="mt-2 text-base-content/60">Herramientas de producción real aplicadas a seguridad en senderismo.</p>
        </div>
        <div class="grid gap-5 sm:grid-cols-2">
          <div v-for="group in techStack" :key="group.category" class="rounded-2xl border border-base-300/40 bg-base-100 p-5">
            <h3 class="mb-3 font-bold text-sm text-primary">{{ group.category }}</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="item in group.items" :key="item" class="rounded-lg bg-base-200/60 px-3 py-1 text-xs font-medium">{{ item }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Team -->
    <section id="equipo" class="py-20">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-12 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Equipo</h2>
          <p class="mt-2 text-base-content/60">Tres desarrolladores, una visión: que ningún sendero tome por sorpresa.</p>
        </div>
        <div class="grid gap-5 sm:grid-cols-3">
          <div v-for="author in authors" :key="author.name" class="group rounded-2xl border border-base-300/40 bg-base-100 p-6 text-center transition hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl">
            <img :src="author.avatar" :alt="author.name" class="mx-auto h-20 w-20 rounded-full object-cover ring-2 ring-base-300/40 transition group-hover:ring-primary/40" />
            <h3 class="mt-4 font-bold">{{ author.name }}</h3>
            <p class="mt-1 text-xs text-base-content/50">{{ author.role }}</p>
            <div class="mt-3 flex items-center justify-center gap-3">
              <a :href="author.github" target="_blank" class="text-base-content/30 transition hover:text-primary" title="GitHub">
                <AppIcon name="github" :size="16" />
              </a>
              <a v-if="author.portfolio" :href="author.portfolio" target="_blank" class="text-base-content/30 transition hover:text-primary" title="Portfolio">
                <AppIcon name="globe" :size="16" />
              </a>
              <a v-if="author.linkedin" :href="author.linkedin" target="_blank" class="text-base-content/30 transition hover:text-primary" title="LinkedIn">
                <AppIcon name="linkedin" :size="16" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- License -->
    <section class="border-y border-base-300/60 bg-base-200/20 py-10">
      <div class="mx-auto flex max-w-6xl flex-col items-center gap-3 px-5 text-center sm:flex-row sm:text-left">
        <AppIcon name="shield" :size="18" class="text-success" />
        <p class="text-sm text-base-content/50">
          Licenciado bajo <strong class="text-base-content/70">MIT</strong> · © 2026 Irvin Benitez, Roy Barrera, Kelvin He ·
          <a href="https://github.com/IrvinngB/JIC-Geo/blob/main/LICENSE" target="_blank" class="text-primary hover:underline">Ver licencia</a>
        </p>
      </div>
    </section>

    <!-- Footer -->
    <footer>
      <div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-8 text-sm text-base-content/40 sm:flex-row">
        <div class="flex items-center gap-2">
          <AppIcon name="mountain" :size="14" class="text-primary/60" />
          <span class="font-semibold text-base-content/50">RiskTrail</span>
          <span>· Índice dinámico de riesgo en senderismo</span>
        </div>
        <div class="flex items-center gap-4">
          <a href="https://github.com/IrvinngB/JIC-Geo" target="_blank" class="link link-hover">GitHub</a>
          <RouterLink to="/mapa" class="link link-hover text-primary">Abrir la app</RouterLink>
        </div>
      </div>
    </footer>
  </div>
</template>
