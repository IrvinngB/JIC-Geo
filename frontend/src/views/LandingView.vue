<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import AppIcon, { type IconName } from '@/components/icons/AppIcon.vue'

const { currentTheme, toggleTheme } = useTheme()

const features: Array<{ icon: IconName; title: string; description: string }> = [
  {
    icon: 'compass',
    title: 'Índice MIDE dinámico',
    description: 'Severidad, orientación, desplazamiento y esfuerzo calculados tramo a tramo con biomecánica real (Pandolf y Tobler), no estimaciones genéricas.',
  },
  {
    icon: 'cloud-rain',
    title: 'Simulación climática',
    description: 'Compara la ruta en seco, lluvia, calor extremo o de noche. El clima ajusta el costo metabólico y el riesgo de cada segmento en vivo.',
  },
  {
    icon: 'route',
    title: 'Ruta óptima con pgRouting',
    description: 'Elige inicio, fin y paradas sobre el mapa. El motor encuentra el camino de menor costo considerando pendiente, superficie y clima.',
  },
]

const steps = [
  { number: '01', title: 'Sube tu ruta', description: 'Un archivo GPX o GeoJSON. Interpolamos elevación y corregimos puntos sueltos.' },
  { number: '02', title: 'Analizamos el esfuerzo', description: 'Velocidad, calorías, fatiga excéntrica y riesgo por cada tramo del recorrido.' },
  { number: '03', title: 'Simula condiciones', description: 'Cambia el clima y observa cómo se mueve el riesgo y el tiempo estimado.' },
  { number: '04', title: 'Encuentra el mejor camino', description: 'La ruta óptima evita los tramos más caros según tu perfil y el terreno.' },
]

const painPoints = [
  { icon: 'map' as IconName, title: 'Mapas estáticos', text: 'Solo muestran distancia y elevación, ignorando el estado del terreno.' },
  { icon: 'sun' as IconName, title: 'Clima ignorado', text: 'Un sendero "moderado" en sol puede ser peligroso bajo lluvia tropical.' },
  { icon: 'thermometer' as IconName, title: 'Humedad extrema', text: 'Drena tu energía sin advertencia, aumentando el riesgo de agotamiento.' },
  { icon: 'alert-triangle' as IconName, title: 'Descensos peligrosos', text: 'Bajar una loma mojada es más riesgoso que subirla: resbalones y caídas.' },
]

const impactMetrics = [
  { icon: 'trending-down' as IconName, value: '40%', label: 'Menos accidentes', description: 'Reducción potencial de resbalones en descensos mojados.' },
  { icon: 'zap' as IconName, value: 'Real', label: 'Biomecánica real', description: 'Pandolf y Minetti, no estimaciones genéricas de fitness apps.' },
  { icon: 'droplets' as IconName, value: 'Vivo', label: 'Clima en tiempo real', description: 'Datos meteorológicos cruzados con cada tramo del sendero.' },
]

const whyDifferent = [
  { icon: 'brain' as IconName, title: 'Motor biomecánico real', description: 'Calcula costo metabólico con fórmulas científicas, no suposiciones.' },
  { icon: 'wind' as IconName, title: 'WBGT en vivo', description: 'Índice de estrés térmico que combina temperatura, humedad y radiación solar.' },
  { icon: 'shield' as IconName, title: 'Alertas de fatiga', description: 'Detecta cuándo el excursionista alcanzará agotamiento severo.' },
  { icon: 'footprints' as IconName, title: 'Corrección de pendiente', description: 'Savitzky-Golay suaviza errores GPS y corrige spikes de elevación.' },
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
        <div class="flex items-center gap-2">
          <button class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content" title="Cambiar tema" @click="toggleTheme">
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="18" />
          </button>
          <RouterLink to="/mapa" class="btn btn-primary btn-sm text-white">Abrir app</RouterLink>
        </div>
      </nav>
    </header>

    <!-- Hero -->
    <section class="relative flex min-h-screen items-center overflow-hidden">
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-success/10 via-base-100 to-primary/5"></div>
      <div class="pointer-events-none absolute -right-32 -top-32 h-[500px] w-[500px] rounded-full bg-primary/10 blur-3xl"></div>
      <div class="pointer-events-none absolute -bottom-40 -left-24 h-[500px] w-[500px] rounded-full bg-success/10 blur-3xl"></div>

      <div class="relative mx-auto max-w-6xl px-5 py-20 md:py-28">
        <div class="max-w-3xl">
          <div class="badge badge-success badge-outline mb-5 gap-2">
            <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-success"></span>
            Análisis biomecánico de senderos
          </div>
          <h1 class="text-4xl font-extrabold leading-tight tracking-tight md:text-6xl">
            Conoce el riesgo
            <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-transparent">
              antes de caminarlo
            </span>
          </h1>
          <p class="mt-6 max-w-2xl text-lg text-base-content/70">
            El ecoturismo crece, pero los mapas tradicionales ignoran un punto ciego gigante: <strong class="text-base-content">cómo el entorno afecta tu cuerpo.</strong> Un sendero "moderado" en un día soleado puede ser letal después de un aguacero tropical.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <RouterLink to="/mapa" class="btn btn-primary btn-lg gap-2 text-white">
              Analizar mi ruta
              <AppIcon name="arrow-right" :size="20" />
            </RouterLink>
            <a href="#como-funciona" class="btn btn-ghost btn-lg">Cómo funciona</a>
          </div>
          <div class="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-sm text-base-content/60">
            <span class="flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-primary"></span> MIDE dinámico</span>
            <span class="flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-info"></span> Clima en vivo</span>
            <span class="flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-secondary"></span> Ruta óptima</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Pain Points -->
    <section class="border-y border-base-300/60 bg-base-200/20 py-16">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">El problema con los mapas tradicionales</h2>
          <p class="mt-2 text-base-content/60">Ignoran cómo el entorno transforma tu cuerpo en tiempo real.</p>
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <div v-for="point in painPoints" :key="point.title" class="flex items-start gap-4 rounded-2xl border border-base-300/40 bg-base-100 p-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-error/10 text-error">
              <AppIcon :name="point.icon" :size="20" />
            </div>
            <div>
              <h3 class="font-bold text-sm">{{ point.title }}</h3>
              <p class="mt-1 text-xs text-base-content/70">{{ point.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-16">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">La solución</h2>
          <p class="mt-2 text-base-content/60">Un sistema que transforma mapas estáticos en herramientas de seguridad vivas.</p>
        </div>
        <div class="grid gap-5 md:grid-cols-3">
          <article v-for="feature in features" :key="feature.title" class="group rounded-2xl border border-base-300/60 bg-base-200/40 p-6 transition hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl">
            <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <AppIcon :name="feature.icon" :size="24" />
            </div>
            <h3 class="text-lg font-bold">{{ feature.title }}</h3>
            <p class="mt-2 text-sm leading-relaxed text-base-content/70">{{ feature.description }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="como-funciona" class="border-y border-base-300/60 bg-base-200/30 py-16">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Cómo funciona</h2>
          <p class="mt-2 text-base-content/60">De un archivo a una decisión informada en cuatro pasos.</p>
        </div>
        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="step in steps" :key="step.number" class="relative rounded-2xl bg-base-100 p-6 shadow-sm">
            <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-4xl font-extrabold text-transparent">{{ step.number }}</span>
            <h3 class="mt-3 font-bold">{{ step.title }}</h3>
            <p class="mt-2 text-sm text-base-content/70">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Why Different -->
    <section class="py-16">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Por qué es diferente</h2>
          <p class="mt-2 text-base-content/60">No es una app de fitness. Es un motor científico de riesgo.</p>
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <div v-for="item in whyDifferent" :key="item.title" class="flex items-start gap-4 rounded-2xl border border-base-300/40 bg-base-100 p-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <AppIcon :name="item.icon" :size="20" />
            </div>
            <div>
              <h3 class="font-bold text-sm">{{ item.title }}</h3>
              <p class="mt-1 text-xs text-base-content/70">{{ item.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Impact -->
    <section class="py-16">
      <div class="mx-auto max-w-6xl px-5">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">El impacto</h2>
          <p class="mt-2 text-base-content/60">Más que una aplicación de mapas: un escudo de prevención.</p>
        </div>
        <div class="grid gap-5 md:grid-cols-3">
          <div v-for="metric in impactMetrics" :key="metric.label" class="rounded-2xl bg-base-100 p-6 shadow-sm border border-base-300/40">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-success/10 text-success">
                <AppIcon :name="metric.icon" :size="20" />
              </div>
              <div class="text-3xl font-extrabold text-success">{{ metric.value }}</div>
            </div>
            <h3 class="mt-3 font-bold text-sm">{{ metric.label }}</h3>
            <p class="mt-1 text-xs text-base-content/70">{{ metric.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20">
      <div class="mx-auto max-w-6xl px-5">
        <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-success to-primary px-8 py-14 text-center shadow-xl">
          <div class="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl"></div>
          <div class="pointer-events-none absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-white/10 blur-2xl"></div>
          <h2 class="text-3xl font-extrabold text-white md:text-4xl">Tu próxima ruta, sin sorpresas</h2>
          <p class="mx-auto mt-3 max-w-xl text-white/80">Sube tu recorrido y obtén el análisis completo en segundos. Sin registro.</p>
          <RouterLink to="/mapa" class="btn btn-lg mt-7 gap-2 border-0 bg-white text-primary hover:bg-white/90">
            Empezar ahora
            <AppIcon name="arrow-right" :size="20" />
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-base-300/60">
      <div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-8 text-sm text-base-content/50 sm:flex-row">
        <div class="flex items-center gap-2">
          <AppIcon name="mountain" :size="16" class="text-primary" />
          <span class="font-semibold text-base-content/70">RiskTrail</span>
          <span>· Índice dinámico de riesgo en senderismo</span>
        </div>
        <RouterLink to="/mapa" class="link link-hover text-primary">Abrir la app</RouterLink>
      </div>
    </footer>
  </div>
</template>
