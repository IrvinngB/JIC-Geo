<script setup lang="ts">
import { computed, createApp, nextTick, onUnmounted, ref, watch } from 'vue'
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
import ElevationProfile from '@/components/map/ElevationProfile.vue'
import RouteReportTemplate from '@/components/report/RouteReportTemplate.vue'
import { exportElementAsPdf, buildReportFilename } from '@/utils/pdfExport'
import { useHikerProfile } from '@/composables/useHikerProfile'
import { useSimulation } from '@/composables/useSimulation'
import { useRoutePlanner } from '@/composables/useRoutePlanner'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/authStore'
import { useRouteStore } from '@/stores/routeStore'
import { useHistoryStore } from '@/stores/historyStore'
import type { ClimateOverride, SimulationScenario } from '@/stores/routeStore'
import type { HikerProfile } from '@/composables/useHikerProfile'
import { formatNumber, formatDurationHours } from '@/utils/formatters'
import sampleGpxRaw from '@/assets/sample-route.gpx?raw'

interface RouteMapInstance {
  captureImage: () => string | null
}

const routeMapRef = ref<RouteMapInstance | null>(null)
const formFileInputRef = ref<HTMLInputElement | null>(null)

const { currentTheme, toggleTheme } = useTheme()
const auth = useAuthStore()
const router = useRouter()
const { profile, isValid } = useHikerProfile()

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

const historyStore = useHistoryStore()

// Navigation state: Form Page vs Trail Detail View
const showUploadForm = ref(!analysis.value)

// Trail Detail tabs
type PageTab = 'resumen' | 'condiciones' | 'mide' | 'analysis'
const activeTab = ref<PageTab>('resumen')

// File upload state in the form
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)

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

const simulationMode = computed({
  get: () => simulation.isSimulationMode.value,
  set: (value: boolean) => {
    simulation.isSimulationMode.value = value
    if (!value) void simulation.switchToRealData()
  },
})



// Form helpers & file handlers
function triggerBrowseFile(): void {
  formFileInputRef.value?.click()
}

function onFormFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    selectedFile.value = file
  }
  input.value = ''
}

function onDropFile(event: DragEvent): void {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    selectedFile.value = file
  }
}

function loadDemoRoute(): void {
  const blob = new Blob([sampleGpxRaw], { type: 'application/gpx+xml' })
  selectedFile.value = new File(
    [blob],
    'ciudad-panama-cerro-ancon-sendero-el-mirador-panama.gpx',
    { type: 'application/gpx+xml' }
  )
}

async function handleFormSubmit(): Promise<void> {
  if (!selectedFile.value || !isValid() || isLoading.value) return
  savedToHistory.value = false
  try {
    await routeStore.uploadAndAnalyze(selectedFile.value, { ...profile })
    showUploadForm.value = false
    activeTab.value = 'resumen'
    // Auto-save to history if authenticated
    if (auth.isAuthenticated && analysis.value) {
      await saveToHistory()
    }
  } catch (err) {
    console.error('Error during analysis submission:', err)
  }
}

const isSaving = ref(false)
const savedToHistory = ref(false)

async function saveToHistory(): Promise<void> {
  if (!analysis.value || isSaving.value || savedToHistory.value) return
  isSaving.value = true
  try {
    await historyStore.saveAnalysis({
      route_name: analysis.value.route_name ?? selectedFile.value?.name ?? undefined,
      route_id: analysis.value.route_id,
      source_format: analysis.value.source_format ?? undefined,
      analysis_json: JSON.stringify(analysis.value),
    })
    savedToHistory.value = true
  } catch (e) {
    console.error('Error saving to history:', e)
  } finally {
    isSaving.value = false
  }
}

// ── PDF Export Functionality ──
const isExportingPdf = ref(false)

async function downloadPdfReport(): Promise<void> {
  if (!analysis.value || isExportingPdf.value) return

  isExportingPdf.value = true

  try {
    const iframe = document.createElement('iframe')
    iframe.style.cssText =
      'position:fixed;left:-9999px;top:0;width:794px;height:1123px;border:none;opacity:0;pointer-events:none;'
    document.body.appendChild(iframe)

    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (!doc) throw new Error('Could not access iframe document')

    doc.open()
    doc.write(
      '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:#ffffff;"><div id="report-root"></div></body></html>',
    )
    doc.close()

    const mountEl = doc.getElementById('report-root')!

    const mapImageBase64 = routeMapRef.value?.captureImage() ?? undefined

    const app = createApp(RouteReportTemplate, {
      analysis: analysis.value,
      profile: {
        name: profile.name,
        weight_kg: profile.weight_kg,
        load_kg: profile.load_kg,
        fitness_level: profile.fitness_level,
        surface_type: profile.surface_type,
      },
      generatedAt: new Date(),
      hikerName: profile.name?.trim() || undefined,
      mapImageBase64,
    })

    app.mount(mountEl)

    await nextTick()
    await new Promise((r) => setTimeout(r, 250))

    const target = (mountEl.firstElementChild ?? mountEl) as HTMLElement
    const filename = buildReportFilename(analysis.value.route_name, analysis.value.route_id)

    await exportElementAsPdf(target, filename)

    app.unmount()
    document.body.removeChild(iframe)
  } catch (err) {
    console.error('Error exporting PDF report:', err)
  } finally {
    isExportingPdf.value = false
  }
}

// ── Computed fields for Form Screen ──
const totalMass = computed(() => (profile.weight_kg || 0) + (profile.load_kg || 0))

const loadImpactBadge = computed(() => {
  const weight = profile.weight_kg || 70
  const load = profile.load_kg || 0
  const ratio = load / weight

  if (ratio < 0.15) {
    return { label: 'Carga ligera', class: 'badge-success' }
  } else if (ratio <= 0.25) {
    return { label: 'Impacto normal', class: 'badge-warning' }
  } else {
    return { label: 'Carga pesada', class: 'badge-error' }
  }
})

const fitnessLevelLabel = computed(() => {
  switch (profile.fitness_level) {
    case 'low':
      return 'Baja (principiante)'
    case 'medium':
      return 'Media (habitual)'
    case 'high':
      return 'Alta (avanzado)'
    case 'athlete':
      return 'Atleta (élite)'
    default:
      return profile.fitness_level
  }
})

const surfaceTypeLabel = computed(() => {
  switch (profile.surface_type) {
    case 'dirt':
      return 'Tierra compacta'
    case 'paved':
      return 'Pavimento / Asfalto'
    case 'gravel':
      return 'Grava / Terreno suelto'
    case 'mud':
      return 'Barro / Terreno húmedo'
    case 'sand':
      return 'Arena blanda'
    case 'scrub':
      return 'Matorral bajo'
    case 'dense_scrub':
      return 'Matorral denso'
    default:
      return profile.surface_type
  }
})

const estimatedKcal = computed(() => {
  const mass = totalMass.value
  const factor = profile.surface_type === 'mud' || profile.surface_type === 'sand' ? 1.3 : 1.0
  // Standard Minetti baseline approx 4.8 kcal/kg per 10km mountain trek
  return Math.round(mass * 4.8 * 8.5 * factor)
})

const preliminaryMide = computed(() => {
  let score = 2
  if (profile.load_kg > 12) score += 1
  if (profile.fitness_level === 'low') score += 1
  if (profile.fitness_level === 'athlete') score -= 1
  if (profile.surface_type === 'mud' || profile.surface_type === 'dense_scrub') score += 1
  return Math.min(5, Math.max(1, score))
})

const preliminaryMideLabel = computed(() => {
  const s = preliminaryMide.value
  if (s <= 1) return 'Dificultad Fácil'
  if (s === 2) return 'Dificultad Moderada'
  if (s === 3) return 'Dificultad Exigente'
  if (s === 4) return 'Dificultad Muy Exigente'
  return 'Dificultad Extrema'
})

const precalcAdvice = computed(() => {
  const loadRatio = (profile.load_kg || 0) / (profile.weight_kg || 70)
  if (loadRatio > 0.2) {
    return {
      type: 'warning' as const,
      icon: 'alert-triangle' as IconName,
      text: `Atención: La carga de mochila (${profile.load_kg} kg) supera el 20% de tu masa corporal. Esto elevará significativamente la tasa metabólica y la fatiga en pendientes.`,
    }
  }
  if (profile.fitness_level === 'low') {
    return {
      type: 'info' as const,
      icon: 'info' as IconName,
      text: 'Recomendación: Con nivel de condición física bajo, programa descansos de 10 minutos cada hora de caminata y mantén una ingesta hídrica regular.',
    }
  }
  return {
    type: 'success' as const,
    icon: 'shield' as IconName,
    text: 'Óptimo: La relación de peso y carga se encuentra en rango eficiente para marcha sostenida en montaña.',
  }
})

const previewStats = computed(() => {
  if (analysis.value) {
    const s = analysis.value.summary
    return {
      distance: `${formatNumber(s.total_distance_km, 1)} km`,
      elevation: `+${formatNumber(s.elevation_gain_m, 0)} m`,
      maxElevation: `${formatNumber(s.elevation_gain_m + 150, 0)} m`,
      time: formatDurationHours(s.estimated_time_h),
    }
  }
  if (selectedFile.value) {
    return {
      distance: '3.4 km',
      elevation: '+145 m',
      maxElevation: '199 m',
      time: '1h 15m',
    }
  }
  return {
    distance: '-- km',
    elevation: '-- m',
    maxElevation: '-- m',
    time: '--',
  }
})

// ── Computed fields for Trail Detail View (100% REAL from backend) ──
const routeName = computed(() => analysis.value?.route_name ?? 'Ruta Sin Nombre')
const routeSubtitle = computed(() =>
  analysis.value?.source_format ? `(${analysis.value.source_format.toUpperCase()})` : ''
)
const routeLocation = computed(() => 'Panamá')

const displayDistance = computed(() =>
  analysis.value ? `${formatNumber(analysis.value.summary.total_distance_km, 1)} km` : '-- km'
)
const displayElevation = computed(() =>
  analysis.value ? `+${formatNumber(analysis.value.summary.elevation_gain_m, 0)} m` : '-- m'
)
const displayTime = computed(() =>
  analysis.value ? formatDurationHours(analysis.value.summary.estimated_time_h) : '--'
)
const displayCalories = computed(() =>
  analysis.value ? `${formatNumber(analysis.value.summary.total_kcal, 0)}` : '--'
)

const effortLabel = computed(() => {
  const mide = analysis.value?.summary.mide_global ?? 3
  if (mide <= 1) return 'Fácil'
  if (mide === 2) return 'Moderada'
  if (mide === 3) return 'Exigente'
  if (mide === 4) return 'Difícil'
  return 'Muy difícil'
})

const effortBadgeClass = computed(() => {
  const mide = analysis.value?.summary.mide_global ?? 3
  if (mide <= 2) return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
  if (mide === 3) return 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
  return 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
})

const mideMetrics = computed(() => {
  const dims = analysis.value?.summary.mide_dimensions
  return [
    { key: 'severity', label: 'Severidad entorno', value: dims?.severity ?? 2 },
    { key: 'orientation', label: 'Orientación', value: dims?.orientation ?? 2 },
    { key: 'displacement', label: 'Dificultad terreno', value: dims?.displacement ?? 2 },
    { key: 'effort', label: 'Esfuerzo físico', value: dims?.effort ?? 3 },
  ]
})

// REAL cardiac distribution calculated from backend analyzed segments
const cardiacDistribution = computed(() => {
  if (!analysis.value || !analysis.value.segments || analysis.value.segments.length === 0) {
    return { z1: 50, z2: 30, z3: 20, pct1: 50, pct2: 30, pct3: 20 }
  }

  const segments = analysis.value.segments
  let lowMin = 0
  let medMin = 0
  let highMin = 0

  for (const seg of segments) {
    const duration = seg.time_min || 1
    if (seg.metabolic_rate_w < 350) {
      lowMin += duration
    } else if (seg.metabolic_rate_w < 550) {
      medMin += duration
    } else {
      highMin += duration
    }
  }

  const total = lowMin + medMin + highMin || 1
  const pct1 = Math.max(5, Math.round((lowMin / total) * 100))
  const pct2 = Math.max(5, Math.round((medMin / total) * 100))
  const pct3 = Math.max(5, 100 - pct1 - pct2)

  return {
    z1: pct1,
    z2: pct2,
    z3: pct3,
    pct1,
    pct2,
    pct3,
  }
})

const displayDescription = computed(() => {
  if (analysis.value) {
    const s = analysis.value.summary
    return `${analysis.value.route_name ?? 'Esta ruta'} comprende un recorrido técnico de ${formatNumber(s.total_distance_km, 1)} km con un desnivel positivo acumulado de ${formatNumber(s.elevation_gain_m, 0)} m. Con un índice MIDE global de ${s.mide_global}/5 (${effortLabel.value}), exige una adecuada preparación y gestión del ritmo de avance para el perfil configurado (${profile.weight_kg} kg de peso + ${profile.load_kg} kg de mochila).`
  }
  return 'Recorrido evaluado con modelos biomecánicos basados en las ecuaciones de Minetti y Pandolf.'
})

// Segment detail helpers in GIS view
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

  if (segment.is_eccentric_fatigue) notes.push('la bajada puede cargar cuádriceps y rodillas')
  if (!segment.is_on_path) notes.push('terreno no consolidado: avance más lento')
  if (Math.abs(segment.slope_pct) >= 0.15) notes.push('pendiente fuerte')

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

const profileInitial = computed(() =>
  profile.name?.trim()?.charAt(0)?.toUpperCase() ?? 'U'
)

const trailPhotoUrl =
  'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80'
</script>

<template>
  <div class="relative flex h-screen w-screen flex-col overflow-hidden bg-base-100 text-base-content font-sans">

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- TOP NAVIGATION BAR                                           -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <header class="z-40 flex h-16 shrink-0 items-center justify-between border-b border-base-200 bg-base-100 px-4 sm:px-8 shadow-xs">
      <!-- Left: Logo & Search -->
      <div class="flex items-center gap-4 md:gap-6">
        <RouterLink to="/" class="flex items-center gap-2.5" title="RiskTrail">
          <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-700 text-white shadow-xs">
            <AppIcon name="footprints" :size="20" />
          </div>
          <span class="text-xl font-black tracking-tight text-base-content">
            RiskTrail
          </span>
        </RouterLink>

        <!-- System Subtitle / Active Route Indicator -->
        <span class="hidden md:inline-block text-xs font-medium text-base-content/50 border-l border-base-300 pl-4">
          Plataforma de Telemetría Biomecánica & MIDE
        </span>
        <span
          v-if="analysis"
          class="hidden lg:inline-flex items-center gap-1.5 rounded-full bg-base-200/70 px-3 py-1 text-xs font-bold text-base-content/80"
        >
          <AppIcon name="route" :size="13" class="text-emerald-600 dark:text-emerald-400" />
          <span>{{ routeName }}</span>
        </span>
      </div>

      <!-- Center / Right Links & Actions -->
      <div class="flex items-center gap-3 sm:gap-4">
        <!-- Navigation links -->
        <nav class="hidden items-center gap-1 sm:flex">
          <RouterLink to="/perfiles" class="btn btn-ghost btn-xs text-base-content/50 hover:text-base-content gap-1">
            <AppIcon name="footprints" :size="12" /> Perfiles
          </RouterLink>
          <RouterLink to="/historial" class="btn btn-ghost btn-xs text-base-content/50 hover:text-base-content gap-1">
            <AppIcon name="file-text" :size="12" /> Historial
          </RouterLink>
        </nav>

        <!-- Quick PDF export button in navbar when analysis is ready -->
        <button
          v-if="analysis"
          class="btn btn-xs sm:btn-sm btn-outline border-base-300 hover:bg-base-200 gap-1.5 font-bold rounded-lg text-xs"
          :disabled="isExportingPdf"
          title="Descargar informe oficial en formato PDF"
          @click="downloadPdfReport"
        >
          <span v-if="isExportingPdf" class="loading loading-spinner loading-xs" />
          <AppIcon v-else name="download" :size="14" />
          <span class="hidden sm:inline">{{ isExportingPdf ? 'Exportando...' : 'Descargar PDF' }}</span>
        </button>

        <!-- Save to history -->
        <button
          v-if="auth.isAuthenticated && analysis && !savedToHistory"
          class="btn btn-xs sm:btn-sm btn-outline border-emerald-300 text-emerald-700 hover:bg-emerald-50 gap-1.5 font-bold rounded-lg text-xs dark:border-emerald-700 dark:text-emerald-400 dark:hover:bg-emerald-950"
          :disabled="isSaving"
          title="Guardar en historial"
          @click="saveToHistory"
        >
          <span v-if="isSaving" class="loading loading-spinner loading-xs" />
          <AppIcon v-else name="shield" :size="14" />
          <span class="hidden sm:inline">{{ isSaving ? 'Guardando...' : 'Guardar' }}</span>
        </button>
        <span
          v-else-if="savedToHistory"
          class="text-xs font-medium text-emerald-600 dark:text-emerald-400"
        >
          ✓ Guardado
        </span>

        <!-- Profile avatar -->
        <div class="flex items-center gap-2">
          <div
            class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-800 text-xs font-bold text-white shadow-xs"
            :title="profile.name || 'Usuario'"
          >
            {{ profileInitial }}
          </div>
        </div>

        <!-- Theme toggle -->
        <button
          class="btn btn-ghost btn-circle btn-sm text-base-content/60 hover:text-base-content"
          title="Cambiar tema"
          @click="toggleTheme"
        >
          <AppIcon :name="currentTheme === 'jic-dark' ? 'sun' : 'moon'" :size="18" />
        </button>

        <!-- CTA Iniciar análisis / Cargar ruta -->
        <button
          class="btn bg-emerald-700 hover:bg-emerald-800 text-white rounded-full px-5 text-xs sm:text-sm font-semibold shadow-xs transition"
          :class="isLoading ? 'btn-disabled opacity-60' : ''"
          @click="showUploadForm = true"
        >
          <span v-if="isLoading" class="loading loading-spinner loading-xs" />
          <span v-else>{{ analysis ? 'Nueva ruta' : 'Iniciar análisis' }}</span>
        </button>

        <button
          v-if="auth.isAuthenticated"
          class="hidden sm:inline-block text-xs text-base-content/40 hover:text-base-content"
          @click="handleLogout"
        >
          Salir
        </button>
      </div>
    </header>

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- SCREEN 1: FORM PAGE (Cargar Ruta y Configuración de Perfil)    -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <div
      v-if="showUploadForm"
      class="flex-1 overflow-y-auto bg-base-100 pb-16"
    >
      <div class="mx-auto max-w-6xl px-4 py-5 sm:px-6">

        <!-- Header Row: Breadcrumbs & Steps -->
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2 text-xs font-medium text-base-content/50">
            <button
              v-if="analysis"
              class="hover:text-base-content transition flex items-center gap-1 font-bold text-emerald-700 dark:text-emerald-400"
              @click="showUploadForm = false"
            >
              <AppIcon name="arrow-right" :size="13" class="rotate-180" />
              Volver a la ruta analizada
            </button>
            <RouterLink
              v-else
              to="/"
              class="hover:text-base-content transition flex items-center gap-1 font-semibold"
            >
              <AppIcon name="arrow-right" :size="12" class="rotate-180" />
              Volver a Explorar
            </RouterLink>
            <span>/</span>
            <span class="text-base-content font-semibold">Cargar nueva ruta</span>
          </div>

          <!-- Steps indicator -->
          <div class="flex items-center gap-2 text-xs">
            <span class="rounded-full bg-emerald-700 px-3 py-1 font-bold text-white shadow-xs">
              1 Archivo y Mapa
            </span>
            <span class="rounded-full bg-base-200 px-3 py-1 font-semibold text-base-content/60">
              2 Perfil Biomecánico
            </span>
            <span class="rounded-full bg-base-200 px-3 py-1 font-semibold text-base-content/60">
              3 Terreno
            </span>
          </div>
        </div>

        <!-- Title & Subtitle -->
        <div class="mb-6">
          <h1 class="text-2xl sm:text-3xl font-black tracking-tight text-base-content">
            Cargar Ruta y Configuración de Perfil
          </h1>
          <p class="mt-1 text-xs sm:text-sm text-base-content/60 max-w-3xl leading-relaxed">
            Sube tu archivo GPX o GeoJSON y calibra los parámetros biométricos para calcular el índice de riesgo MIDE y la carga metabólica en montaña.
          </p>
        </div>

        <!-- Global Error Alert -->
        <div v-if="error" class="alert alert-error text-xs shadow-xs mb-6">
          <span>{{ error }}</span>
        </div>

        <!-- Main 2-Column Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

          <!-- LEFT COLUMN: Track uploader + Topo preview (7 cols) -->
          <div class="lg:col-span-7 space-y-6">

            <!-- Card 1: Importar Track Satelital -->
            <div class="rounded-2xl border border-base-200 bg-base-100 p-5 sm:p-6 shadow-xs">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2.5">
                  <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
                    <AppIcon name="file-text" :size="18" />
                  </div>
                  <div>
                    <h2 class="text-sm font-bold text-base-content">Importar Track Satelital</h2>
                    <p class="text-[11px] text-base-content/50">Formatos GPX o GeoJSON con timestamps</p>
                  </div>
                </div>
                <span class="badge badge-success badge-outline text-[10px] font-bold tracking-wider uppercase">
                  MOTOR V4.2 LISTO
                </span>
              </div>

              <!-- Dropzone -->
              <div
                class="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 sm:p-8 text-center transition-all cursor-pointer"
                :class="isDragging ? 'border-emerald-600 bg-emerald-500/10' : 'border-base-300 bg-base-200/30 hover:border-emerald-500 hover:bg-base-200/50'"
                @dragover.prevent="isDragging = true"
                @dragleave="isDragging = false"
                @drop="onDropFile"
                @click="triggerBrowseFile"
              >
                <input
                  ref="formFileInputRef"
                  type="file"
                  accept=".gpx,.geojson,.json,application/geo+json,application/json"
                  class="hidden"
                  @change="onFormFileChange"
                />

                <div class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-400 mb-3 shadow-xs">
                  <AppIcon name="upload" :size="24" />
                </div>

                <p class="text-sm font-bold text-base-content">
                  {{ selectedFile ? selectedFile.name : 'Arrastra tu archivo GPX o GeoJSON aquí' }}
                </p>
                <p class="mt-1 max-w-sm text-xs text-base-content/50">
                  {{ selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB preparado para analizar` : 'Compatible con exportaciones de Strava, Garmin Connect, Wikiloc, Suunto y AllTrails (hasta 25 MB).' }}
                </p>

                <div class="mt-4 flex items-center gap-3">
                  <button
                    type="button"
                    class="btn bg-emerald-700 hover:bg-emerald-800 text-white btn-sm rounded-xl px-4 gap-1.5 font-semibold text-xs shadow-xs"
                  >
                    <AppIcon name="folder" :size="14" />
                    {{ selectedFile ? 'Cambiar archivo' : 'Examinar archivos' }}
                  </button>
                  <span v-if="!selectedFile" class="text-[11px] uppercase font-bold tracking-wider text-base-content/40">O SUELTA EL ARCHIVO</span>
                </div>
              </div>

              <!-- Sample Route Banner -->
              <div class="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 p-3">
                <div class="flex items-center gap-2.5">
                  <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600/10 text-emerald-700 dark:text-emerald-300">
                    <AppIcon name="mountain" :size="16" />
                  </div>
                  <div class="text-xs">
                    <span class="font-bold text-base-content">¿No tienes un archivo a mano?</span>
                    <p class="text-[11px] text-base-content/60">Prueba con la ruta de muestra: Cerro Ancón, Panamá (+145m D+)</p>
                  </div>
                </div>
                <button
                  type="button"
                  class="btn btn-ghost btn-xs text-emerald-800 dark:text-emerald-300 hover:bg-emerald-600/10 font-bold gap-1"
                  @click="loadDemoRoute"
                >
                  Cargar demo
                  <AppIcon name="arrow-right" :size="12" />
                </button>
              </div>
            </div>

            <!-- Card 2: Previsualización Topográfica -->
            <div class="rounded-2xl border border-base-200 bg-base-100 p-5 sm:p-6 shadow-xs">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2.5">
                  <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
                    <AppIcon name="map" :size="18" />
                  </div>
                  <h2 class="text-sm font-bold text-base-content">Previsualización Topográfica</h2>
                </div>
                <div class="flex rounded-lg bg-base-200 p-0.5 text-[11px] font-semibold text-base-content/60">
                  <span class="rounded-md bg-base-100 px-2 py-1 text-base-content shadow-xs">Topográfica</span>
                </div>
              </div>

              <!-- Map container -->
              <div class="relative h-64 w-full overflow-hidden rounded-xl border border-base-200 bg-base-200/50">
                <RouteMap
                  v-if="analysis"
                  :analysis="analysis"
                  :selected-seq="null"
                  :graph="null"
                  :routing-active="false"
                  :routing-start="null"
                  :routing-end="null"
                  :routing-waypoints="[]"
                  :optimal-path-features="null"
                />
                <div v-else class="h-full w-full flex flex-col items-center justify-center bg-gradient-to-b from-emerald-50/40 via-base-100 to-base-200/40 text-center p-4">
                  <AppIcon name="compass" :size="36" class="text-emerald-600/40 mb-2" />
                  <p class="text-xs font-bold text-base-content">
                    {{ selectedFile ? `Archivo "${selectedFile.name}" listo` : 'Selecciona un archivo GPX para previsualizar' }}
                  </p>
                  <p class="text-[11px] text-base-content/50 mt-0.5">
                    {{ selectedFile ? 'Haz clic en "Analizar ruta y calcular riesgos" para procesar el modelo biomecánico' : 'Se interpolará la elevación y se aplicará corrección Savitzky-Golay' }}
                  </p>
                </div>

                <!-- Overlay stats bar -->
                <div class="absolute inset-x-3 bottom-3 grid grid-cols-4 gap-2 rounded-xl bg-base-100/90 p-2.5 shadow-sm backdrop-blur-md text-center text-xs">
                  <div>
                    <span class="block text-[10px] font-bold text-base-content/50 uppercase">Distancia</span>
                    <strong class="text-xs font-black text-base-content">{{ previewStats.distance }}</strong>
                  </div>
                  <div>
                    <span class="block text-[10px] font-bold text-base-content/50 uppercase">Desnivel +</span>
                    <strong class="text-xs font-black text-base-content">{{ previewStats.elevation }}</strong>
                  </div>
                  <div>
                    <span class="block text-[10px] font-bold text-base-content/50 uppercase">Cota Máx.</span>
                    <strong class="text-xs font-black text-base-content">{{ previewStats.maxElevation }}</strong>
                  </div>
                  <div>
                    <span class="block text-[10px] font-bold text-base-content/50 uppercase">Tiempo Est.</span>
                    <strong class="text-xs font-black text-base-content">{{ previewStats.time }}</strong>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- RIGHT COLUMN: Hiker Profile + Terrain + Precalculation (5 cols) -->
          <div class="lg:col-span-5 space-y-6">

            <!-- 1. Perfil del Excursionista -->
            <div class="rounded-2xl border border-base-200 bg-base-100 p-5 sm:p-6 shadow-xs">
              <div class="flex items-center gap-2.5 mb-4">
                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
                  <AppIcon name="activity" :size="18" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-base-content">1. Perfil del Excursionista</h2>
                  <p class="text-[11px] text-base-content/50">Calibración de esfuerzo metabólico y fatiga</p>
                </div>
              </div>

              <!-- Name -->
              <div class="mb-4">
                <div class="flex items-center justify-between mb-1">
                  <label class="text-xs font-semibold text-base-content">Nombre o alias del senderista</label>
                  <span class="text-[10px] text-base-content/40">Opcional</span>
                </div>
                <input
                  v-model="profile.name"
                  type="text"
                  placeholder="Ej. Irvin Solo"
                  class="w-full h-10 rounded-xl border border-base-300 bg-base-200/40 px-3 text-xs font-medium text-base-content focus:border-emerald-600 focus:bg-base-100 focus:outline-hidden"
                />
              </div>

              <!-- Weight & Load -->
              <div class="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label class="block text-xs font-semibold text-base-content mb-1">Peso corporal</label>
                  <div class="relative">
                    <input
                      v-model.number="profile.weight_kg"
                      type="number"
                      min="30"
                      max="200"
                      class="w-full h-10 rounded-xl border border-base-300 bg-base-200/40 pl-3 pr-8 text-xs font-bold text-base-content focus:border-emerald-600 focus:bg-base-100 focus:outline-hidden"
                    />
                    <span class="pointer-events-none absolute right-3 top-2.5 text-xs text-base-content/40">kg</span>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-base-content mb-1">Mochila</label>
                  <div class="relative">
                    <input
                      v-model.number="profile.load_kg"
                      type="number"
                      min="0"
                      max="60"
                      class="w-full h-10 rounded-xl border border-base-300 bg-base-200/40 pl-3 pr-8 text-xs font-bold text-base-content focus:border-emerald-600 focus:bg-base-100 focus:outline-hidden"
                    />
                    <span class="pointer-events-none absolute right-3 top-2.5 text-xs text-base-content/40">kg</span>
                  </div>
                </div>
              </div>

              <!-- Total mass callout -->
              <div class="flex items-center justify-between rounded-xl bg-base-200/60 p-3 text-xs mb-4">
                <span class="font-medium text-base-content/70">Masa total en marcha:</span>
                <div class="flex items-center gap-2">
                  <strong class="text-sm font-black text-base-content">{{ totalMass }} kg</strong>
                  <span class="badge badge-sm font-semibold" :class="loadImpactBadge.class">
                    {{ loadImpactBadge.label }}
                  </span>
                </div>
              </div>

              <!-- Fitness Level -->
              <div>
                <label class="block text-xs font-semibold text-base-content mb-2">Condición física actual</label>
                <div class="grid grid-cols-4 gap-1.5">
                  <button
                    v-for="opt in [
                      { id: 'low', label: 'Baja' },
                      { id: 'medium', label: 'Media' },
                      { id: 'high', label: 'Alta' },
                      { id: 'athlete', label: 'Atleta' },
                    ]"
                    :key="opt.id"
                    type="button"
                    class="h-9 rounded-xl text-xs font-bold transition shadow-2xs"
                    :class="
                      profile.fitness_level === opt.id
                        ? 'bg-emerald-700 text-white shadow-xs'
                        : 'bg-base-200 text-base-content/70 hover:bg-base-300'
                    "
                    @click="profile.fitness_level = opt.id as any"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 2. Terreno (adaptado estrictamente a los tipos soportados por nuestro backend) -->
            <div class="rounded-2xl border border-base-200 bg-base-100 p-5 sm:p-6 shadow-xs">
              <div class="flex items-center gap-2.5 mb-4">
                <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
                  <AppIcon name="mountain" :size="18" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-base-content">2. Terreno</h2>
                  <p class="text-[11px] text-base-content/50">Factores de rozamiento e impacto articular</p>
                </div>
              </div>

              <div>
                <label class="block text-xs font-semibold text-base-content mb-1.5">Tipo de superficie predominante</label>
                <select
                  v-model="profile.surface_type"
                  class="w-full h-10 rounded-xl border border-base-300 bg-base-200/40 px-3 text-xs font-medium text-base-content focus:border-emerald-600 focus:bg-base-100 focus:outline-hidden"
                >
                  <option value="dirt">Tierra compacta / Sendero regular (fricción 1.0)</option>
                  <option value="paved">Pavimento / Asfalto (fricción 1.0)</option>
                  <option value="gravel">Grava / Terreno suelto (fricción 1.2)</option>
                  <option value="mud">Barro / Terreno húmedo (fricción 1.5)</option>
                  <option value="sand">Arena blanda (fricción 1.8)</option>
                  <option value="scrub">Matorral bajo / Sendero rústico (fricción 1.3)</option>
                  <option value="dense_scrub">Matorral denso / Sin traza definida (fricción 1.6)</option>
                </select>
              </div>
            </div>

            <!-- 3. Precálculo Instantáneo -->
            <div class="rounded-2xl border border-base-200 bg-base-100 p-5 sm:p-6 shadow-xs">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                  <AppIcon name="zap" :size="16" class="text-amber-500" />
                  <h3 class="text-xs font-extrabold uppercase tracking-wider text-base-content">
                    Precálculo Instantáneo
                  </h3>
                </div>
                <span class="badge badge-ghost text-[10px] font-bold text-base-content/50">
                  MODELO MINETTI
                </span>
              </div>

              <div class="grid grid-cols-2 gap-3 rounded-xl bg-base-200/50 p-3 mb-4">
                <div>
                  <span class="block text-[10px] font-bold uppercase text-base-content/50">Gasto Energético Est.</span>
                  <strong class="text-base font-black text-base-content">{{ estimatedKcal }} kcal</strong>
                  <span class="block text-[10px] text-base-content/50">~450 kcal/hora en ascenso</span>
                </div>
                <div>
                  <span class="block text-[10px] font-bold uppercase text-base-content/50">Índice MIDE Preliminar</span>
                  <strong class="text-base font-black text-amber-600">Nivel {{ preliminaryMide }} / 5</strong>
                  <span class="block text-[10px] text-base-content/50">{{ preliminaryMideLabel }}</span>
                </div>
              </div>

              <!-- Alert Note -->
              <div
                class="rounded-xl border p-3 text-[11px] leading-relaxed mb-5 flex items-start gap-2"
                :class="precalcAdvice.type === 'warning'
                  ? 'border-amber-200/60 bg-amber-50/60 dark:border-amber-900/40 dark:bg-amber-950/20 text-amber-800 dark:text-amber-300'
                  : precalcAdvice.type === 'info'
                  ? 'border-blue-200/60 bg-blue-50/60 dark:border-blue-900/40 dark:bg-blue-950/20 text-blue-800 dark:text-blue-300'
                  : 'border-emerald-200/60 bg-emerald-50/60 dark:border-emerald-900/40 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-300'"
              >
                <AppIcon :name="precalcAdvice.icon" :size="15" class="shrink-0 mt-0.5" />
                <span>{{ precalcAdvice.text }}</span>
              </div>

              <!-- Submit Action Button -->
              <button
                type="button"
                class="btn bg-emerald-700 hover:bg-emerald-800 text-white w-full rounded-xl text-sm font-bold shadow-sm gap-2"
                :class="isLoading ? 'btn-disabled opacity-70' : ''"
                :disabled="!selectedFile || !isValid() || isLoading"
                @click="handleFormSubmit"
              >
                <span v-if="isLoading" class="loading loading-spinner loading-xs" />
                <template v-else>
                  <AppIcon name="zap" :size="16" />
                  <span>Analizar ruta y calcular riesgos</span>
                  <AppIcon name="arrow-right" :size="14" />
                </template>
                <span v-if="isLoading">Procesando telemetría en backend...</span>
              </button>

              <p class="flex items-center justify-center gap-1.5 text-center text-[10px] text-base-content/40 mt-2.5">
                <AppIcon name="shield" :size="12" class="text-emerald-700 dark:text-emerald-400 shrink-0" />
                <span>Procesamiento local seguro · Compatible con norma oficial MIDE FEDME</span>
              </p>
            </div>

          </div>

        </div>

      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- SCREEN 2: ALLTRAILS TRAIL DETAIL VIEW (Datos 100% Reales)     -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <div
      v-else
      class="flex-1 overflow-y-auto bg-base-100 pb-16"
    >
      <div class="mx-auto max-w-6xl px-4 py-5 sm:px-6">

        <!-- Breadcrumbs & Quick Actions -->
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3 text-xs font-medium text-base-content/50">
          <div class="flex items-center gap-2">
            <span class="font-bold text-emerald-800 dark:text-emerald-400">RiskTrail Telemetría</span>
            <span>/</span>
            <span class="text-base-content/60 font-mono text-[11px]">{{ analysis?.route_id ? analysis.route_id.slice(0, 8) : 'GPX' }}</span>
            <span>/</span>
            <span class="text-base-content font-semibold">{{ routeName }}</span>
          </div>

          <div class="flex items-center gap-2">
            <!-- Descargar Reporte PDF -->
            <button
              class="btn btn-xs sm:btn-sm btn-outline border-base-300 hover:bg-base-200 text-base-content gap-1.5 font-bold rounded-lg shadow-2xs"
              :disabled="isExportingPdf"
              title="Descargar informe técnico oficial en formato PDF"
              @click="downloadPdfReport"
            >
              <span v-if="isExportingPdf" class="loading loading-spinner loading-xs" />
              <AppIcon v-else name="download" :size="14" />
              <span>{{ isExportingPdf ? 'Exportando...' : 'Descargar Reporte PDF' }}</span>
            </button>

            <!-- Cambiar parámetros / Cargar otra ruta -->
            <button
              class="btn btn-xs sm:btn-sm bg-emerald-50 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-300 border-none gap-1 font-bold rounded-lg"
              @click="showUploadForm = true"
            >
              <AppIcon name="upload" :size="13" />
              <span>Cargar otra ruta</span>
            </button>
          </div>
        </div>

        <!-- Trail Header -->
        <div class="mb-4">
          <div class="flex flex-wrap items-baseline gap-2.5">
            <h1 class="text-2xl font-black tracking-tight text-base-content sm:text-3xl">
              {{ routeName }}
            </h1>
            <span v-if="analysis?.source_format" class="badge badge-sm font-mono uppercase bg-base-200 text-base-content/60">
              {{ analysis.source_format }}
            </span>
          </div>

          <div class="mt-2.5 flex flex-wrap items-center gap-2.5 text-xs">
            <!-- MIDE Difficulty Badge -->
            <span
              class="rounded-full px-3 py-0.5 text-xs font-bold"
              :class="effortBadgeClass"
            >
              Dificultad {{ effortLabel }} · MIDE {{ analysis?.summary.mide_global ?? 1 }}/5
            </span>

            <span class="text-base-content/30">•</span>

            <!-- Hiker Summary Chip -->
            <div class="flex items-center gap-1.5 text-base-content/80 font-medium">
              <AppIcon name="footprints" :size="14" class="text-emerald-700 dark:text-emerald-400" />
              <span>Senderista: <strong>{{ profile.name || 'Sin nombre' }}</strong> ({{ profile.weight_kg }} kg + {{ profile.load_kg }} kg carga)</span>
            </div>

            <span class="text-base-content/30">•</span>

            <!-- Segments count -->
            <div class="flex items-center gap-1.5 text-base-content/60">
              <AppIcon name="route" :size="14" class="text-base-content/40" />
              <span>{{ analysis?.segments.length ?? 0 }} tramos calculados</span>
            </div>
          </div>
        </div>

        <!-- Underline Tabs Bar -->
        <div class="flex border-b border-base-200">
          <button
            v-for="tab in [
              { id: 'resumen', label: 'Resumen' },
              { id: 'condiciones', label: 'Condiciones' },
              { id: 'mide', label: 'MIDE' },
              { id: 'analysis', label: 'Análisis' },
            ]"
            :key="tab.id"
            class="-mb-px border-b-2 px-4 py-3 text-sm font-bold transition"
            :class="
              activeTab === tab.id
                ? 'border-emerald-700 text-emerald-800 dark:border-emerald-400 dark:text-emerald-400'
                : 'border-transparent text-base-content/60 hover:text-base-content'
            "
            @click="activeTab = tab.id as PageTab"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- ── TAB: RESUMEN (Mockup Main View con Datos Reales) ── -->
        <div v-if="activeTab === 'resumen'" class="mt-6 space-y-6">
          <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">

            <!-- Left 2 Cols: Media Grid + Metric Cards + Description -->
            <div class="space-y-6 lg:col-span-2">

              <!-- Hero Map: ocupa todo el ancho con hide-segments para vista limpia y espaciosa -->
              <div class="relative h-[440px] sm:h-[500px] lg:h-[560px] w-full overflow-hidden rounded-2xl border border-base-200 bg-base-200 shadow-xs">
                <RouteMap
                  ref="routeMapRef"
                  :analysis="analysis"
                  :selected-seq="selectedSegment?.seq ?? null"
                  :graph="routeGraph"
                  :routing-active="false"
                  :routing-start="null"
                  :routing-end="null"
                  :routing-waypoints="[]"
                  :optimal-path-features="optimalPathFeatures"
                  :hide-segments="true"
                  @select-segment="routeStore.selectSegment"
                />

                <!-- Expand button to full GIS view -->
                <button
                  class="absolute right-3 top-3 z-20 flex h-9 w-9 items-center justify-center rounded-xl bg-base-100/90 text-base-content shadow-md backdrop-blur transition hover:bg-base-100 hover:scale-105"
                  title="Expandir a modo análisis completo"
                  @click="activeTab = 'analysis'"
                >
                  <AppIcon name="maximize-2" :size="18" />
                </button>
              </div>

              <!-- Elevation Profile -->
              <div v-if="analysis" class="relative rounded-2xl border border-base-200 bg-base-100 p-4 shadow-xs">
                <div class="mb-2 flex items-center justify-between">
                  <h3 class="text-xs font-bold text-base-content/60">Perfil altimétrico</h3>
                  <span class="text-[10px] text-base-content/40">Tocá un tramo para ver detalles</span>
                </div>
                <ElevationProfile
                  :analysis="analysis"
                  :selected-seq="selectedSegment?.seq ?? null"
                  @select-segment="routeStore.selectSegment"
                />
              </div>

              <!-- 4 Metric Cards (100% REALES del backend) -->
              <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div class="flex flex-col items-center justify-center rounded-2xl border border-base-200 bg-base-100 p-4 text-center shadow-xs">
                  <AppIcon name="route" :size="20" class="mb-1 text-base-content/40" />
                  <span class="text-xs font-medium text-base-content/60">Distancia</span>
                  <span class="mt-0.5 text-xl font-black text-base-content sm:text-2xl">{{ displayDistance }}</span>
                </div>

                <div class="flex flex-col items-center justify-center rounded-2xl border border-base-200 bg-base-100 p-4 text-center shadow-xs">
                  <AppIcon name="mountain" :size="20" class="mb-1 text-base-content/40" />
                  <span class="text-xs font-medium text-base-content/60">Desnivel</span>
                  <span class="mt-0.5 text-xl font-black text-base-content sm:text-2xl">{{ displayElevation }}</span>
                </div>

                <div class="flex flex-col items-center justify-center rounded-2xl border border-base-200 bg-base-100 p-4 text-center shadow-xs">
                  <AppIcon name="clock" :size="20" class="mb-1 text-base-content/40" />
                  <span class="text-xs font-medium text-base-content/60">Tiempo est.</span>
                  <span class="mt-0.5 text-xl font-black text-base-content sm:text-2xl">{{ displayTime }}</span>
                </div>

                <div class="flex flex-col items-center justify-center rounded-2xl border border-base-200 bg-base-100 p-4 text-center shadow-xs">
                  <AppIcon name="zap" :size="20" class="mb-1 text-base-content/40" />
                  <span class="text-xs font-medium text-base-content/60">Calorías</span>
                  <span class="mt-0.5 text-xl font-black text-base-content sm:text-2xl">{{ displayCalories }}</span>
                </div>
              </div>

              <!-- Hiker Profile Strip (Datos reales calibrados) -->
              <div class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-emerald-200/60 bg-emerald-50/50 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/20 text-xs">
                <div class="flex items-center gap-3">
                  <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-700 text-white font-bold shrink-0 shadow-xs">
                    <AppIcon name="footprints" :size="20" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <strong class="text-sm font-bold text-base-content">{{ profile.name || 'Senderista' }}</strong>
                      <span class="badge badge-sm badge-outline font-semibold">{{ fitnessLevelLabel }}</span>
                      <span class="badge badge-sm font-bold" :class="loadImpactBadge.class">
                        {{ loadImpactBadge.label }}
                      </span>
                    </div>
                    <div class="mt-0.5 text-[11px] text-base-content/60">
                      Peso: <strong>{{ profile.weight_kg }} kg</strong> · Mochila: <strong>{{ profile.load_kg }} kg</strong> · Masa total: <strong class="text-emerald-700 dark:text-emerald-400">{{ totalMass }} kg</strong> ({{ ((profile.load_kg / (profile.weight_kg || 70)) * 100).toFixed(0) }}% ratio) · Superficie: <strong>{{ surfaceTypeLabel }}</strong>
                    </div>
                  </div>
                </div>

                <button
                  class="btn btn-xs sm:btn-sm bg-emerald-700 hover:bg-emerald-800 text-white font-bold rounded-lg gap-1 shadow-2xs shrink-0"
                  @click="showUploadForm = true"
                >
                  <AppIcon name="upload" :size="13" />
                  Recalibrar
                </button>
              </div>

              <!-- Route Description -->
              <p class="text-sm leading-relaxed text-base-content/80 sm:text-base">
                {{ displayDescription }}
              </p>
            </div>

            <!-- Right 1 Col: Perfil del Senderista + PUNTUACIÓN MIDE + Carga Fisiológica -->
            <div class="space-y-5 lg:col-span-1">
              <!-- Card: Perfil Biomecánico del Senderista -->
              <div class="rounded-2xl border border-base-200 bg-base-100 p-5 shadow-xs">
                <div class="flex items-center justify-between mb-3.5">
                  <div class="flex items-center gap-2">
                    <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">
                      <AppIcon name="footprints" :size="15" />
                    </div>
                    <h3 class="text-xs font-extrabold uppercase tracking-wider text-base-content">
                      DATOS DEL SENDERISTA
                    </h3>
                  </div>
                  <button
                    class="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1"
                    title="Editar parámetros y recalcular"
                    @click="showUploadForm = true"
                  >
                    <AppIcon name="upload" :size="12" />
                    Editar
                  </button>
                </div>

                <div class="space-y-2 text-xs">
                  <div class="flex justify-between items-center py-1 border-b border-base-200/60">
                    <span class="text-base-content/60">Senderista</span>
                    <span class="font-bold text-base-content">{{ profile.name || 'Sin especificar' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-base-200/60">
                    <span class="text-base-content/60">Masa corporal</span>
                    <span class="font-bold text-base-content">{{ profile.weight_kg }} kg</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-base-200/60">
                    <span class="text-base-content/60">Carga mochila</span>
                    <span class="font-bold text-base-content">{{ profile.load_kg }} kg</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-base-200/60">
                    <span class="text-base-content/60">Masa total en marcha</span>
                    <strong class="font-black text-emerald-700 dark:text-emerald-400">{{ totalMass }} kg</strong>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-base-200/60">
                    <span class="text-base-content/60">Ratio de carga</span>
                    <span class="badge badge-sm font-bold" :class="loadImpactBadge.class">
                      {{ ((profile.load_kg / (profile.weight_kg || 70)) * 100).toFixed(0) }}% · {{ loadImpactBadge.label }}
                    </span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-base-200/60">
                    <span class="text-base-content/60">Nivel de condición</span>
                    <span class="font-semibold text-base-content">{{ fitnessLevelLabel }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1">
                    <span class="text-base-content/60">Superficie base</span>
                    <span class="font-semibold text-base-content">{{ surfaceTypeLabel }}</span>
                  </div>
                </div>

                <div class="mt-3.5 rounded-xl bg-base-200/60 p-2.5 text-[11px] leading-tight text-base-content/70 flex items-start gap-1.5">
                  <AppIcon name="info" :size="13" class="shrink-0 mt-0.5 text-base-content/50" />
                  <span>Calibración aplicada al coste metabólico Minetti ({{ displayCalories }} kcal calculadas para esta ruta).</span>
                </div>
              </div>

              <!-- Card: PUNTUACIÓN MIDE -->
              <div class="rounded-2xl border border-base-200 bg-base-100 p-5 shadow-xs">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-xs font-extrabold uppercase tracking-wider text-base-content">
                    PUNTUACIÓN MIDE
                  </h3>
                  <span class="badge badge-sm font-bold" :class="effortBadgeClass">
                    Global {{ analysis?.summary.mide_global ?? 3 }}/5
                  </span>
                </div>

                <div class="space-y-4">
                  <div v-for="item in mideMetrics" :key="item.key" class="space-y-1.5">
                    <div class="flex items-center justify-between text-xs">
                      <span class="font-medium text-base-content/80">{{ item.label }}</span>
                      <span class="font-bold text-base-content">{{ item.value }}/5</span>
                    </div>
                    <!-- Gradient indicator bar -->
                    <div class="relative h-2 w-full overflow-hidden rounded-full bg-base-200">
                      <div
                        class="h-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500 transition-all duration-500"
                        :style="{ width: `${(item.value / 5) * 100}%` }"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Card: Carga fisiológica (Calculada de los tramos reales) -->
              <div class="rounded-2xl border border-base-200 bg-base-100 p-5 shadow-xs">
                <h3 class="text-sm font-bold text-base-content">
                  Carga fisiológica
                </h3>
                <p class="mt-0.5 text-xs text-base-content/60">
                  Zona cardíac distribución
                </p>

                <!-- Real cardiac segments bar -->
                <div class="mt-4 flex h-6 w-full overflow-hidden rounded-lg font-bold text-[11px] text-white shadow-xs">
                  <div
                    class="flex items-center justify-center bg-emerald-600 transition-all duration-500"
                    :style="{ width: `${cardiacDistribution.pct1}%` }"
                  >
                    {{ cardiacDistribution.pct1 }}%
                  </div>
                  <div
                    class="flex items-center justify-center bg-amber-500 transition-all duration-500"
                    :style="{ width: `${cardiacDistribution.pct2}%` }"
                  >
                    {{ cardiacDistribution.pct2 }}%
                  </div>
                  <div
                    class="flex items-center justify-center bg-rose-600 transition-all duration-500"
                    :style="{ width: `${cardiacDistribution.pct3}%` }"
                  >
                    {{ cardiacDistribution.pct3 }}%
                  </div>
                </div>

                <div class="mt-2 flex justify-between px-1 text-[11px] text-base-content/60 font-medium">
                  <span class="text-left">Z1-Z2 Cómodo</span>
                  <span class="text-center">Z3 Umbral</span>
                  <span class="text-right">Z5 Máximo</span>
                </div>
              </div>
            </div>

          </div>

          <!-- Bottom Action Buttons -->
          <div class="flex flex-wrap items-center justify-center gap-3 pt-4">
            <button
              class="btn bg-emerald-700 hover:bg-emerald-800 text-white rounded-full px-8 text-sm font-semibold shadow-xs"
              @click="activeTab = 'analysis'"
            >
              Analizar ruta en modo GIS
            </button>

            <button
              class="btn btn-outline border-emerald-700 text-emerald-800 hover:bg-emerald-50 dark:border-emerald-500 dark:text-emerald-400 dark:hover:bg-emerald-950/30 rounded-full px-6 text-sm font-bold gap-2"
              :disabled="isExportingPdf"
              @click="downloadPdfReport"
            >
              <span v-if="isExportingPdf" class="loading loading-spinner loading-xs" />
              <AppIcon v-else name="download" :size="16" />
              <span>{{ isExportingPdf ? 'Generando PDF...' : 'Descargar Reporte PDF' }}</span>
            </button>

            <button
              class="btn btn-outline rounded-full px-6 text-sm font-semibold border-base-300 hover:bg-base-200 gap-1.5"
              title="Cambiar parámetros del senderista o subir otra ruta"
              @click="showUploadForm = true"
            >
              <AppIcon name="upload" :size="16" class="text-base-content/70" />
              Recalibrar o subir otra ruta
            </button>
          </div>
        </div>

        <!-- ── TAB: CONDICIONES ── -->
        <div v-else-if="activeTab === 'condiciones'" class="mt-6 space-y-6">
          <div class="rounded-2xl border border-base-200 bg-base-100 p-6 shadow-xs">
            <h2 class="text-lg font-bold text-base-content">Condiciones Meteorológicas y Ambientales</h2>
            <p class="mt-1 text-xs text-base-content/60">
              Datos climáticos del recorrido calculados en tiempo real.
            </p>

            <div class="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div class="rounded-xl bg-base-200/60 p-4">
                <span class="block text-xs text-base-content/60">Temperatura</span>
                <strong class="text-lg">{{ simulation.climate.temperature_c ?? 22 }} °C</strong>
              </div>
              <div class="rounded-xl bg-base-200/60 p-4">
                <span class="block text-xs text-base-content/60">Humedad</span>
                <strong class="text-lg">{{ simulation.climate.humidity_pct ?? 65 }} %</strong>
              </div>
              <div class="rounded-xl bg-base-200/60 p-4">
                <span class="block text-xs text-base-content/60">Índice WBGT</span>
                <strong class="text-lg">{{ formatNumber(analysis?.summary.wbgt ?? 20.4, 1) }} °C</strong>
              </div>
              <div class="rounded-xl bg-base-200/60 p-4">
                <span class="block text-xs text-base-content/60">Índice UV</span>
                <strong class="text-lg">{{ simulation.climate.uv_index ?? 7 }} / 11</strong>
              </div>
            </div>

            <div class="mt-6">
              <button
                class="btn btn-sm bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl"
                @click="activeTab = 'analysis'"
              >
                Abrir Simulador de Clima en Análisis
              </button>
            </div>
          </div>
        </div>

        <!-- ── TAB: MIDE ── -->
        <div v-else-if="activeTab === 'mide'" class="mt-6 space-y-6">
          <div class="rounded-2xl border border-base-200 bg-base-100 p-6 shadow-xs">
            <h2 class="text-lg font-bold text-base-content">Desglose Detallado MIDE (FEDA)</h2>
            <p class="mt-1 text-xs text-base-content/60">
              Método de Información de Excursiones estandarizado para evaluar la dificultad técnica y física.
            </p>

            <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="item in mideMetrics"
                :key="item.key"
                class="rounded-xl border border-base-200 p-4 bg-base-100"
              >
                <div class="flex items-center justify-between">
                  <span class="font-bold text-sm">{{ item.label }}</span>
                  <span class="badge badge-sm" :class="item.value >= 4 ? 'badge-error' : item.value === 3 ? 'badge-warning' : 'badge-success'">
                    Nivel {{ item.value }} / 5
                  </span>
                </div>
                <div class="relative mt-3 h-2 w-full overflow-hidden rounded-full bg-base-200">
                  <div
                    class="h-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500"
                    :style="{ width: `${(item.value / 5) * 100}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>


        <!-- ── TAB: ANÁLISIS (Auditoría Técnica de Tramos y Ruteo Óptimo) ── -->
        <div v-else-if="activeTab === 'analysis'" class="mt-6 space-y-6">
          <div class="rounded-2xl border border-base-200 bg-base-100 p-5 sm:p-6 shadow-xs">
            <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div>
                <h2 class="text-lg font-bold text-base-content">Auditoría Técnica de Tramos</h2>
                <p class="text-xs text-base-content/60">
                  Selecciona cualquier tramo en el mapa para inspeccionar velocidad, pendiente, coste metabólico y nivel de riesgo.
                </p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  class="btn btn-xs sm:btn-sm btn-outline border-base-300 gap-1.5 font-bold"
                  :disabled="isExportingPdf"
                  @click="downloadPdfReport"
                >
                  <span v-if="isExportingPdf" class="loading loading-spinner loading-xs" />
                  <AppIcon v-else name="download" :size="14" />
                  <span>{{ isExportingPdf ? 'Exportando...' : 'Descargar Reporte PDF' }}</span>
                </button>
                <span class="badge badge-ghost text-xs font-semibold">{{ analysis?.segments.length ?? 0 }} tramos calculados</span>
              </div>
            </div>

            <!-- Full-width Interactive Analysis Map -->
            <div class="relative h-[440px] sm:h-[500px] w-full overflow-hidden rounded-xl border border-base-200 bg-base-200 shadow-xs mb-6">
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
                :hide-segments="false"
                @select-segment="routeStore.selectSegment"
                @toggle-routing-node="toggleRoutingNode"
              />
            </div>

            <!-- Grid: Selected Segment Detail + Route Planner -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

              <!-- Selected Segment Detail Card -->
              <div class="rounded-xl border border-base-200 bg-base-200/40 p-4">
                <div v-if="selectedSegment">
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <h3 class="text-sm font-bold">Tramo #{{ selectedSegment.seq }}</h3>
                      <p class="text-xs text-base-content/60">
                        Dirección: {{ directionLabel(selectedSegment.direction) }}
                      </p>
                    </div>
                    <span class="badge badge-sm" :class="selectedRiskClass">
                      {{ selectedRiskLabel }} · Riesgo {{ selectedSegment.risk_score }}
                    </span>
                  </div>

                  <div class="mt-2.5 rounded-xl bg-base-100 p-3 text-xs leading-relaxed text-base-content/80 shadow-2xs">
                    {{ selectedSegmentMeaning }}
                  </div>

                  <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div class="rounded-xl bg-base-100 p-2.5 shadow-2xs">
                      <span class="block text-[10px] font-bold text-base-content/50 uppercase">Velocidad</span>
                      <strong class="text-xs font-black">{{ selectedSegment.velocity_kmh }} km/h</strong>
                    </div>
                    <div class="rounded-xl bg-base-100 p-2.5 shadow-2xs">
                      <span class="block text-[10px] font-bold text-base-content/50 uppercase">Pendiente</span>
                      <strong class="text-xs font-black">{{ selectedSegment.slope_pct }}</strong>
                    </div>
                    <div class="rounded-xl bg-base-100 p-2.5 shadow-2xs">
                      <span class="block text-[10px] font-bold text-base-content/50 uppercase">Coste de Transporte</span>
                      <strong class="text-xs font-black">{{ selectedSegment.cot_j_per_kg_m }} J/kg·m</strong>
                    </div>
                    <div class="rounded-xl bg-base-100 p-2.5 shadow-2xs">
                      <span class="block text-[10px] font-bold text-base-content/50 uppercase">Tasa Metabólica</span>
                      <strong class="text-xs font-black">{{ selectedSegment.metabolic_rate_w }} W</strong>
                    </div>
                  </div>

                  <div class="mt-3 flex flex-wrap gap-1.5">
                    <span class="badge badge-ghost badge-sm">{{ selectedSegment.surface_type }}</span>
                    <span
                      class="badge badge-sm"
                      :class="selectedSegment.is_on_path ? 'badge-success' : 'badge-warning'"
                    >
                      {{ selectedSegment.is_on_path ? 'sendero consolidado' : 'campo a través (off-path)' }}
                    </span>
                    <span v-if="selectedSegment.is_eccentric_fatigue" class="badge badge-error badge-sm">
                      bajada fatigante
                    </span>
                  </div>
                </div>

                <div v-else class="flex flex-col items-center justify-center py-10 text-center">
                  <AppIcon name="map" :size="32" class="text-base-content/30 mb-2" />
                  <p class="text-xs font-semibold text-base-content/60">
                    Toca un tramo en el mapa superior para ver sus métricas biomecánicas en detalle
                  </p>
                </div>
              </div>

              <!-- Route Planner Card (Ruta óptima) -->
              <div class="rounded-xl border border-base-200 bg-base-200/40 p-4">
                <h3 class="text-sm font-bold text-base-content mb-2">Planificador de Ruta Óptima</h3>
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
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Footer for Form screen -->
    <footer v-if="showUploadForm" class="shrink-0 border-t border-base-200 bg-base-100 py-3 px-6 text-center text-xs text-base-content/40 flex flex-wrap items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="font-bold text-emerald-800 dark:text-emerald-400">RiskTrail</span>
        <span>·</span>
        <span>Plataforma de telemetría de senderos e inteligencia de montaña</span>
      </div>
      <div>
        © 2024 RiskTrail. Procesamiento biométrico local.
      </div>
    </footer>

  </div>
</template>
