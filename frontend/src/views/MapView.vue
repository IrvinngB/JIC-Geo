<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import RouteMap from '@/components/map/RouteMap.vue'
import HikerProfileForm from '@/components/sidebar/HikerProfileForm.vue'
import RouteSummary from '@/components/sidebar/RouteSummary.vue'
import FileUploader from '@/components/upload/FileUploader.vue'
import ClimateSliders from '@/components/simulation/ClimateSliders.vue'
import ClimateToggle from '@/components/simulation/ClimateToggle.vue'
import { useHikerProfile } from '@/composables/useHikerProfile'
import { useSimulation } from '@/composables/useSimulation'
import { useTheme } from '@/composables/useTheme'
import { useRouteStore } from '@/stores/routeStore'
import type { ClimateOverride, SimulationScenario } from '@/stores/routeStore'
import type { HikerProfile } from '@/composables/useHikerProfile'

const { currentTheme, toggleTheme } = useTheme()
const { profile, isValid } = useHikerProfile()
const simulation = useSimulation()
const routeStore = useRouteStore()
const { analysis, error, isLoading, selectedSegment } = storeToRefs(routeStore)

// On mobile the side panel becomes a bottom sheet. This drives its open state;
// on desktop (md+) it is ignored because the panel is a static sidebar.
const sheetOpen = ref(false)
const simulationMode = computed({
  get: () => simulation.isSimulationMode.value,
  set: (value: boolean) => {
    simulation.isSimulationMode.value = value
    if (!value) void simulation.switchToRealData()
  },
})

// Raise the sheet automatically when a segment is selected so its detail is
// visible without an extra tap.
watch(selectedSegment, (segment) => {
  if (segment) sheetOpen.value = true
})

const selectedRiskLabel = computed(() => {
  const score = selectedSegment.value?.risk_score ?? 0
  if (score >= 75) return 'Alto'
  if (score >= 45) return 'Medio'
  return 'Bajo'
})

const selectedRiskClass = computed(() => {
  const score = selectedSegment.value?.risk_score ?? 0
  if (score >= 75) return 'badge-error'
  if (score >= 45) return 'badge-warning'
  return 'badge-success'
})

const selectedSegmentMeaning = computed(() => {
  const segment = selectedSegment.value
  if (!segment) return ''

  const notes: string[] = []
  if (segment.risk_score >= 75) notes.push('tramo crítico: conviene bajar el ritmo')
  else if (segment.risk_score >= 45) notes.push('tramo de atención: puede cansar más de lo normal')
  else notes.push('tramo relativamente cómodo')

  if (segment.is_eccentric_fatigue) {
    notes.push('la bajada puede cargar cuádriceps y rodillas')
  }
  if (!segment.is_on_path) {
    notes.push('terreno no consolidado: avance más lento')
  }
  if (Math.abs(segment.slope_pct) >= 0.15) {
    notes.push('pendiente fuerte')
  }

  return `Este es un ${notes.join('; ')}.`
})

function directionLabel(direction: string): string {
  if (direction === 'ascent') return 'Subida'
  if (direction === 'descent') return 'Bajada'
  return 'Plano'
}

async function analyzeRoute(file: File, selectedProfile: HikerProfile): Promise<void> {
  await routeStore.uploadAndAnalyze(file, selectedProfile)
}

function updateClimate(value: ClimateOverride): void {
  Object.assign(simulation.climate, value)
}

async function applyScenario(scenario: SimulationScenario): Promise<void> {
  simulation.applyScenario(scenario)
  await simulation.runSimulation()
}
</script>

<template>
  <div class="relative flex h-screen w-screen flex-col overflow-hidden bg-base-300 text-base-content md:flex-row">
    <aside
      class="fixed inset-x-0 bottom-0 z-30 flex h-[85vh] flex-col rounded-t-2xl bg-base-200 shadow-2xl transition-transform duration-300 ease-out md:static md:z-auto md:h-auto md:w-96 md:shrink-0 md:translate-y-0 md:rounded-none md:border-r md:border-base-100 md:shadow-none"
      :class="sheetOpen ? 'translate-y-0' : 'translate-y-[calc(85vh_-_3.5rem)] md:translate-y-0'"
    >
      <button
        type="button"
        class="flex shrink-0 flex-col items-center gap-1 px-4 pb-2 pt-3 md:hidden"
        @click="sheetOpen = !sheetOpen"
      >
        <span class="h-1.5 w-12 rounded-full bg-base-content/25"></span>
        <span class="text-xs font-semibold text-base-content/70">
          {{ sheetOpen ? 'Ocultar panel ▾' : analysis ? 'Ver perfil y resumen ▴' : 'Perfil y carga de ruta ▴' }}
        </span>
      </button>

      <div class="flex items-center justify-between border-b border-base-100 p-5">
        <div>
          <h1
            class="bg-gradient-to-r from-success to-primary bg-clip-text text-2xl font-extrabold tracking-tight text-transparent"
          >
            JIC-Geo
          </h1>
          <p class="mt-1 text-xs text-base-content/60">Índice dinámico de riesgo en senderismo</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content"
            title="Cambiar tema"
            @click="toggleTheme"
          >
            <span v-if="currentTheme === 'jic-dark'">☀️</span>
            <span v-else>🌙</span>
          </button>
          <div class="badge badge-success badge-outline text-xs">FE alpha</div>
        </div>
      </div>

      <div class="flex-1 space-y-4 overflow-y-auto overscroll-contain p-4">
        <HikerProfileForm v-model="profile" :is-valid="isValid()" :disabled="isLoading" />

        <FileUploader
          :profile="profile"
          :can-submit="isValid()"
          :is-loading="isLoading"
          @analyze="analyzeRoute"
        />

        <div v-if="error" class="alert alert-error text-xs shadow-md">
          <span>{{ error }}</span>
        </div>

        <RouteSummary :analysis="analysis" />

        <ClimateToggle
          v-if="analysis"
          v-model="simulationMode"
          :disabled="isLoading"
        />

        <ClimateSliders
          v-if="analysis && simulationMode"
          :model-value="simulation.climate"
          :disabled="isLoading"
          @update:model-value="updateClimate"
          @scenario="applyScenario"
          @run="simulation.runSimulation"
        />

        <section v-if="selectedSegment" class="card bg-base-100 shadow-md">
          <div class="card-body p-4 text-sm">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h2 class="font-bold">Tramo #{{ selectedSegment.seq }}</h2>
                <p class="text-xs text-base-content/60">{{ directionLabel(selectedSegment.direction) }}</p>
              </div>
              <span class="badge" :class="selectedRiskClass">
                Riesgo {{ selectedRiskLabel }} · {{ selectedSegment.risk_score }}/100
              </span>
            </div>

            <div class="mt-3 rounded-box bg-base-200 p-3 text-xs leading-relaxed text-base-content/70">
              {{ selectedSegmentMeaning }}
            </div>

            <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Velocidad esperada</span>
                <strong>{{ selectedSegment.velocity_kmh }} km/h</strong>
                <p class="mt-1 text-base-content/50">Más bajo = tramo más lento.</p>
              </div>
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Pendiente</span>
                <strong>{{ selectedSegment.slope_pct }}</strong>
                <p class="mt-1 text-base-content/50">+ sube, - baja.</p>
              </div>
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Costo por metro</span>
                <strong>{{ selectedSegment.cot_j_per_kg_m }} J/kg·m</strong>
                <p class="mt-1 text-base-content/50">Energía por peso y distancia.</p>
              </div>
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Esfuerzo instantáneo</span>
                <strong>{{ selectedSegment.metabolic_rate_w }} W</strong>
                <p class="mt-1 text-base-content/50">Qué tan fuerte trabaja el cuerpo.</p>
              </div>
            </div>

            <div class="mt-3 flex flex-wrap gap-2">
              <span class="badge badge-ghost">Superficie: {{ selectedSegment.surface_type }}</span>
              <span class="badge" :class="selectedSegment.is_on_path ? 'badge-success' : 'badge-warning'">
                {{ selectedSegment.is_on_path ? 'sendero consolidado' : 'off-path' }}
              </span>
              <span v-if="selectedSegment.is_eccentric_fatigue" class="badge badge-error">
                bajada fatigante
              </span>
            </div>
          </div>
        </section>
      </div>
    </aside>

    <main class="absolute inset-0 md:static md:min-h-0 md:flex-1">
      <RouteMap
        :analysis="analysis"
        :selected-seq="selectedSegment?.seq ?? null"
        @select-segment="routeStore.selectSegment"
      />
    </main>
  </div>
</template>
