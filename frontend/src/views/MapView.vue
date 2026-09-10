<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import RouteMap from '@/components/map/RouteMap.vue'
import HikerProfileForm from '@/components/sidebar/HikerProfileForm.vue'
import RouteSummary from '@/components/sidebar/RouteSummary.vue'
import MideIndicator from '@/components/sidebar/MideIndicator.vue'
import FileUploader from '@/components/upload/FileUploader.vue'
import ClimateSliders from '@/components/simulation/ClimateSliders.vue'
import ClimateToggle from '@/components/simulation/ClimateToggle.vue'
import RoutePlanner from '@/components/routing/RoutePlanner.vue'
import AppIcon, { type IconName } from '@/components/icons/AppIcon.vue'
import { useHikerProfile } from '@/composables/useHikerProfile'
import { useSimulation } from '@/composables/useSimulation'
import { useRoutePlanner } from '@/composables/useRoutePlanner'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/authStore'
import { useRouteStore } from '@/stores/routeStore'
import type { ClimateOverride, SimulationScenario } from '@/stores/routeStore'
import type { HikerProfile } from '@/composables/useHikerProfile'

interface RouteMapInstance {
  captureImage: () => string | null
}

const routeMapRef = ref<RouteMapInstance | null>(null)

const { currentTheme, toggleTheme } = useTheme()
const auth = useAuthStore()
const router = useRouter()
const { profile, isValid } = useHikerProfile()

// Sidebar tabs
type SidebarTab = 'analysis' | 'profiles' | 'history'
const activeTab = ref<SidebarTab>('analysis')
const simulation = useSimulation()
const routeStore = useRouteStore()
const {
  analysis,
  error,
  isLoading,
  selectedSegment,
  climateComparison,
  routeGraph,
  optimalPath,
  optimalPathFeatures,
} = storeToRefs(routeStore)

const routePlanner = useRoutePlanner()
const {
  isActive: routingActive,
  algorithm: routingAlgorithm,
  start: routingStart,
  end: routingEnd,
  waypoints: routingWaypoints,
  canCompute: canComputeRoute,
  toggleNode: toggleRoutingNode,
  clear: clearRouting,
  compute: computeOptimalRoute,
} = routePlanner

async function toggleRouting(): Promise<void> {
  if (routingActive.value) {
    routePlanner.deactivate()
  } else {
    await routePlanner.activate()
  }
}

function handleLogout() {
  auth.logout()
  router.push('/')
}

// On mobile the side panel becomes a bottom sheet. This drives its open state;
// on desktop (md+) it is ignored because the panel is a static sidebar.
const sheetOpen = ref(false)

// Desktop-only sidebar resize (drag the right edge). Ignored on mobile, where
// the panel is a bottom sheet instead.
const SIDEBAR_MIN_WIDTH = 320
const SIDEBAR_MAX_WIDTH = 640
const sidebarWidth = ref(384)
let isResizingSidebar = false

function startSidebarResize(event: MouseEvent): void {
  isResizingSidebar = true
  event.preventDefault()
  window.addEventListener('mousemove', onSidebarResize)
  window.addEventListener('mouseup', stopSidebarResize)
}

function onSidebarResize(event: MouseEvent): void {
  if (!isResizingSidebar) return
  sidebarWidth.value = Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, event.clientX))
}

function stopSidebarResize(): void {
  isResizingSidebar = false
  window.removeEventListener('mousemove', onSidebarResize)
  window.removeEventListener('mouseup', stopSidebarResize)
}

onUnmounted(stopSidebarResize)
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
  if (score >= 80) return 'Extremo'
  if (score >= 60) return 'Alto'
  if (score >= 40) return 'Medio'
  if (score >= 20) return 'Moderado'
  return 'Bajo'
})

const selectedRiskClass = computed(() => {
  const score = selectedSegment.value?.risk_score ?? 0
  if (score >= 80) return 'badge-secondary'
  if (score >= 60) return 'badge-error'
  if (score >= 40) return 'badge-warning'
  if (score >= 20) return 'badge-warning badge-outline'
  return 'badge-success'
})

const selectedSegmentMeaning = computed(() => {
  const segment = selectedSegment.value
  if (!segment) return ''

  const notes: string[] = []
  if (segment.risk_score >= 80) notes.push('tramo de peligro extremo: no continuar sin preparación')
  else if (segment.risk_score >= 60) notes.push('tramo crítico: conviene bajar el ritmo')
  else if (segment.risk_score >= 40) notes.push('tramo de atención: puede cansar más de lo normal')
  else if (segment.risk_score >= 20) notes.push('tramo con fatiga moderada esperada')
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
      class="fixed inset-x-0 bottom-0 z-30 flex h-[85vh] flex-col rounded-t-2xl bg-base-200 shadow-2xl transition-transform duration-300 ease-out md:relative md:z-auto md:h-auto md:w-[var(--sidebar-width)] md:shrink-0 md:translate-y-0 md:rounded-none md:border-r md:border-base-100 md:shadow-none"
      :class="sheetOpen ? 'translate-y-0' : 'translate-y-[calc(85vh_-_3rem)] md:translate-y-0'"
      :style="{ '--sidebar-width': `${sidebarWidth}px` }"
    >
      <div
        class="absolute inset-y-0 right-0 z-10 hidden w-1.5 cursor-col-resize touch-none select-none hover:bg-primary/40 active:bg-primary/60 md:block"
        title="Arrastrar para cambiar el ancho del panel"
        @mousedown="startSidebarResize"
      ></div>
      <!-- Mobile drag handle -->
      <button
        type="button"
        class="flex shrink-0 flex-col items-center gap-1.5 px-4 pb-2 pt-3 md:hidden"
        @click="sheetOpen = !sheetOpen"
      >
        <span class="h-1 w-10 rounded-full bg-base-content/20"></span>
        <span class="flex items-center gap-1.5 text-[11px] font-medium text-base-content/50">
          <AppIcon :name="sheetOpen ? 'chevron-down' : 'chevron-up'" :size="12" />
          {{ sheetOpen ? 'Ocultar panel' : analysis ? 'Perfil y resumen' : 'Perfil y carga' }}
        </span>
      </button>

      <div class="flex items-center justify-between border-b border-base-100 p-3 sm:p-5">
        <RouterLink to="/" class="group flex items-center gap-2" title="Volver al inicio">
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition group-hover:bg-primary/20 sm:h-8 sm:w-8"
          >
            <AppIcon name="mountain" :size="16" />
          </span>
          <div>
            <h1
              class="bg-gradient-to-r from-success to-primary bg-clip-text text-lg font-extrabold tracking-tight text-transparent sm:text-2xl"
            >
              RiskTrail
            </h1>
            <p class="hidden text-xs text-base-content/60 sm:block">Análisis de riesgo en senderismo</p>
          </div>
        </RouterLink>
        <div class="flex items-center gap-2">
          <button
            class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content"
            title="Cambiar tema"
            @click="toggleTheme"
          >
            <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="18" />
          </button>
          <button
            v-if="auth.isAuthenticated"
            class="btn btn-ghost btn-sm text-[10px] text-base-content/50 sm:text-xs"
            title="Cerrar sesión"
            @click="handleLogout"
          >
            Salir
          </button>
          <div class="badge badge-success badge-outline text-[10px] sm:text-xs">FE alpha</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-base-300/60 px-3 sm:px-4">
        <button
          v-for="tab in [
            { id: 'analysis' as SidebarTab, label: 'Análisis', icon: 'compass' as IconName },
            { id: 'profiles' as SidebarTab, label: 'Perfiles', icon: 'footprints' as IconName },
            { id: 'history' as SidebarTab, label: 'Historial', icon: 'file-text' as IconName },
          ]"
          :key="tab.id"
          class="flex flex-1 items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition sm:text-xs"
          :class="activeTab === tab.id
            ? 'border-b-2 border-primary text-primary'
            : 'text-base-content/40 hover:text-base-content/60'"
          @click="activeTab = tab.id"
        >
          <AppIcon :name="tab.icon" :size="14" />
          {{ tab.label }}
        </button>
      </div>

      <div class="flex-1 overflow-y-auto overscroll-contain p-3 sm:p-4">
        <!-- Tab: Análisis -->
        <div v-if="activeTab === 'analysis'" class="space-y-3 sm:space-y-4">
          <HikerProfileForm v-model="profile" :is-valid="isValid()" :disabled="isLoading" />

          <FileUploader
            :profile="profile"
            :can-submit="isValid()"
            :is-loading="isLoading"
            @analyze="analyzeRoute"
          />

          <div v-if="error" class="alert alert-error text-[11px] shadow-md sm:text-xs">
            <span>{{ error }}</span>
          </div>

          <RouteSummary :analysis="analysis" :profile="profile" :route-map="routeMapRef" />

          <MideIndicator
            v-if="analysis"
            :dimensions="analysis.summary.mide_dimensions"
            :global="analysis.summary.mide_global"
          />

          <ClimateToggle
            v-if="analysis"
            v-model="simulationMode"
            :disabled="isLoading"
          />

          <ClimateSliders
            v-if="analysis && simulationMode"
            :model-value="simulation.climate"
            :disabled="isLoading"
            :comparison="climateComparison"
            @update:model-value="updateClimate"
            @scenario="applyScenario"
            @run="simulation.runSimulation"
          />

          <RoutePlanner
            v-if="analysis"
            :is-active="routingActive"
            :algorithm="routingAlgorithm"
            :start="routingStart"
            :end="routingEnd"
            :waypoints="routingWaypoints"
            :can-compute="canComputeRoute"
            :optimal-path="optimalPath"
            :disabled="isLoading"
            @toggle-active="toggleRouting"
            @update:algorithm="routingAlgorithm = $event"
            @remove-node="toggleRoutingNode"
            @compute="computeOptimalRoute"
            @clear="clearRouting"
          />

          <section v-if="selectedSegment" class="card bg-base-100 shadow-md">
            <div class="card-body p-3 sm:p-4">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h2 class="font-bold text-sm">Tramo #{{ selectedSegment.seq }}</h2>
                <p class="text-[11px] text-base-content/60">{{ directionLabel(selectedSegment.direction) }}</p>
              </div>
              <span class="badge badge-sm" :class="selectedRiskClass">
                {{ selectedRiskLabel }} · {{ selectedSegment.risk_score }}
              </span>
            </div>

            <div class="mt-2 rounded-box bg-base-200 p-2.5 text-[11px] leading-relaxed text-base-content/70 sm:mt-3 sm:text-xs">
              {{ selectedSegmentMeaning }}
            </div>

            <div class="mt-2 grid grid-cols-2 gap-1.5 text-[11px] sm:mt-3 sm:gap-2 sm:text-xs">
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Velocidad</span>
                <strong>{{ selectedSegment.velocity_kmh }} km/h</strong>
              </div>
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Pendiente</span>
                <strong>{{ selectedSegment.slope_pct }}</strong>
              </div>
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">CoT</span>
                <strong>{{ selectedSegment.cot_j_per_kg_m }} J/kg·m</strong>
              </div>
              <div class="rounded-box bg-base-200 p-2">
                <span class="block text-base-content/50">Esfuerzo</span>
                <strong>{{ selectedSegment.metabolic_rate_w }} W</strong>
              </div>
            </div>

            <div class="mt-2 flex flex-wrap gap-1.5 sm:mt-3 sm:gap-2">
              <span class="badge badge-ghost badge-sm">{{ selectedSegment.surface_type }}</span>
              <span class="badge badge-sm" :class="selectedSegment.is_on_path ? 'badge-success' : 'badge-warning'">
                {{ selectedSegment.is_on_path ? 'consolidado' : 'off-path' }}
              </span>
              <span v-if="selectedSegment.is_eccentric_fatigue" class="badge badge-error badge-sm">
                bajada fatigante
              </span>
            </div>
          </div>
        </section>
        </div>

        <!-- Tab: Perfiles -->
        <div v-if="activeTab === 'profiles'" class="space-y-3">
          <div class="text-center text-xs text-base-content/40 py-8">
            <AppIcon name="footprints" :size="32" class="mx-auto mb-3 text-base-content/20" />
            <p>Gestión de perfiles</p>
            <p class="mt-1 text-[10px]">Próximamente</p>
          </div>
        </div>

        <!-- Tab: Historial -->
        <div v-if="activeTab === 'history'" class="space-y-3">
          <div class="text-center text-xs text-base-content/40 py-8">
            <AppIcon name="file-text" :size="32" class="mx-auto mb-3 text-base-content/20" />
            <p>Historial de análisis</p>
            <p class="mt-1 text-[10px]">Próximamente</p>
          </div>
        </div>
      </div>
    </aside>

    <main class="absolute inset-0 md:static md:min-h-0 md:flex-1">
      <RouteMap
        ref="routeMapRef"
        :analysis="analysis"
        :selected-seq="selectedSegment?.seq ?? null"
        :graph="routeGraph"
        :routing-active="routingActive"
        :routing-start="routingStart"
        :routing-end="routingEnd"
        :routing-waypoints="routingWaypoints"
        :optimal-path-features="optimalPathFeatures"
        @select-segment="routeStore.selectSegment"
        @toggle-routing-node="toggleRoutingNode"
      />
    </main>
  </div>
</template>
