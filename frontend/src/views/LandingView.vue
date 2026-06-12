<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import AppIcon, { type IconName } from '@/components/icons/AppIcon.vue'

const { currentTheme, toggleTheme } = useTheme()

const features: Array<{ icon: IconName; title: string; description: string }> = [
  {
    icon: 'compass',
    title: 'Índice MIDE dinámico',
    description:
      'Severidad, orientación, desplazamiento y esfuerzo calculados tramo a tramo con biomecánica real (Pandolf y Tobler), no estimaciones genéricas.',
  },
  {
    icon: 'cloud-rain',
    title: 'Simulación climática',
    description:
      'Compara la ruta en seco, lluvia, calor extremo o de noche. El clima ajusta el costo metabólico y el riesgo de cada segmento en vivo.',
  },
  {
    icon: 'route',
    title: 'Ruta óptima con pgRouting',
    description:
      'Elige inicio, fin y paradas sobre el mapa. El motor encuentra el camino de menor costo considerando pendiente, superficie y clima.',
  },
]

const steps = [
  {
    number: '01',
    title: 'Sube tu ruta',
    description: 'Un archivo GPX o GeoJSON. Interpolamos elevación y corregimos puntos sueltos.',
  },
  {
    number: '02',
    title: 'Analizamos el esfuerzo',
    description: 'Velocidad, calorías, fatiga excéntrica y riesgo por cada tramo del recorrido.',
  },
  {
    number: '03',
    title: 'Simula condiciones',
    description: 'Cambia el clima y observa cómo se mueve el riesgo y el tiempo estimado.',
  },
  {
    number: '04',
    title: 'Encuentra el mejor camino',
    description: 'La ruta óptima evita los tramos más caros según tu perfil y el terreno.',
  },
]
</script>

<template>
  <div class="min-h-screen bg-base-100 text-base-content">
    <!-- Navbar -->
    <header
      class="sticky top-0 z-50 border-b border-base-300/60 bg-base-100/80 backdrop-blur-lg"
    >
      <nav class="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
        <div class="flex items-center gap-2">
          <AppIcon name="mountain" :size="22" class="text-primary" />
          <span
            class="bg-gradient-to-r from-success to-primary bg-clip-text text-xl font-extrabold tracking-tight text-transparent"
          >
            RiskTrail
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content"
            title="Cambiar tema"
            @click="toggleTheme"
          >
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="18" />
          </button>
          <RouterLink to="/mapa" class="btn btn-primary btn-sm text-white">
            Abrir app
          </RouterLink>
        </div>
      </nav>
    </header>

    <!-- Hero -->
    <section class="relative overflow-hidden">
      <!-- Decorative nature gradient backdrop -->
      <div
        class="pointer-events-none absolute inset-0 bg-gradient-to-br from-success/20 via-base-100 to-primary/10"
      ></div>
      <div
        class="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-primary/20 blur-3xl"
      ></div>
      <div
        class="pointer-events-none absolute -bottom-40 -left-24 h-96 w-96 rounded-full bg-success/20 blur-3xl"
      ></div>

      <div class="relative mx-auto max-w-6xl px-5 py-20 md:py-28">
        <div class="max-w-3xl">
          <div class="badge badge-success badge-outline mb-5 gap-2">
            <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-success"></span>
            Análisis biomecánico de senderos
          </div>
          <h1 class="text-4xl font-extrabold leading-tight tracking-tight md:text-6xl">
            Conoce el riesgo
            <span
              class="bg-gradient-to-r from-success to-primary bg-clip-text text-transparent"
            >
              antes de caminarlo
            </span>
          </h1>
          <p class="mt-6 max-w-2xl text-lg text-base-content/70">
            RiskTrail convierte tu GPX en un índice dinámico de riesgo: esfuerzo real tramo a tramo,
            simulación de clima y la ruta de menor costo sobre el mapa.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <RouterLink to="/mapa" class="btn btn-primary btn-lg gap-2 text-white">
              Analizar mi ruta
              <AppIcon name="arrow-right" :size="20" />
            </RouterLink>
            <a href="#como-funciona" class="btn btn-ghost btn-lg">
              Cómo funciona
            </a>
          </div>

          <!-- Feature pills -->
          <div class="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-sm text-base-content/60">
            <span class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full bg-primary"></span> MIDE dinámico
            </span>
            <span class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full bg-info"></span> Clima en vivo
            </span>
            <span class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full bg-secondary"></span> Ruta óptima
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="mx-auto max-w-6xl px-5 py-16">
      <div class="mb-10 max-w-2xl">
        <h2 class="text-3xl font-bold tracking-tight">Qué hace por ti</h2>
        <p class="mt-2 text-base-content/60">
          Tres motores trabajando sobre la misma ruta para que decidas con datos.
        </p>
      </div>
      <div class="grid gap-5 md:grid-cols-3">
        <article
          v-for="feature in features"
          :key="feature.title"
          class="group rounded-2xl border border-base-300/60 bg-base-200/40 p-6 transition hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl"
        >
          <div
            class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary"
          >
            <AppIcon :name="feature.icon" :size="24" />
          </div>
          <h3 class="text-lg font-bold">{{ feature.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-base-content/70">
            {{ feature.description }}
          </p>
        </article>
      </div>
    </section>

    <!-- How it works -->
    <section id="como-funciona" class="border-y border-base-300/60 bg-base-200/30">
      <div class="mx-auto max-w-6xl px-5 py-16">
        <div class="mb-10 max-w-2xl">
          <h2 class="text-3xl font-bold tracking-tight">Cómo funciona</h2>
          <p class="mt-2 text-base-content/60">De un archivo a una decisión informada en cuatro pasos.</p>
        </div>
        <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="step in steps"
            :key="step.number"
            class="relative rounded-2xl bg-base-100 p-6 shadow-sm"
          >
            <span
              class="bg-gradient-to-r from-success to-primary bg-clip-text text-4xl font-extrabold text-transparent"
            >
              {{ step.number }}
            </span>
            <h3 class="mt-3 font-bold">{{ step.title }}</h3>
            <p class="mt-2 text-sm text-base-content/70">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="mx-auto max-w-6xl px-5 py-20">
      <div
        class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-success to-primary px-8 py-14 text-center shadow-xl"
      >
        <div
          class="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl"
        ></div>
        <h2 class="text-3xl font-extrabold text-white md:text-4xl">
          Tu próxima ruta, sin sorpresas
        </h2>
        <p class="mx-auto mt-3 max-w-xl text-white/80">
          Sube tu recorrido y obtén el análisis completo en segundos. Sin registro.
        </p>
        <RouterLink
          to="/mapa"
          class="btn btn-lg mt-7 gap-2 border-0 bg-white text-primary hover:bg-white/90"
        >
          Empezar ahora
          <AppIcon name="arrow-right" :size="20" />
        </RouterLink>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-base-300/60">
      <div
        class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-8 text-sm text-base-content/50 sm:flex-row"
      >
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
