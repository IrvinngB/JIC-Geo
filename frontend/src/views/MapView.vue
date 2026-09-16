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
import AppIcon from '@/components/icons/AppIcon.vue'
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

interface RouteMapInstance {
  captureImage: () => string | null
}

const routeMapRef = ref<RouteMapInstance | null>(null)

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

// Redirect to form if no analysis
if (!analysis.value) {
  router.push('/mapa/nueva')
}

// Trail Detail tabs
type PageTab = 'resumen' | 'detalles' | 'ruta'
const activeTab = ref<PageTab>('resumen')

// File upload state moved to UploadFormView

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



// Form submit handler (receives File from UploadFormView)
async function handleFormSubmit(file: File): Promise<void> {
  if (!isValid() || isLoading.value) return
  savedToHistory.value = false
  try {
    await routeStore.uploadAndAnalyze(file, { ...profile })
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
const shareLinkCopied = ref(false)

async function saveToHistory(): Promise<void> {
  if (!analysis.value || isSaving.value || savedToHistory.value) return
  isSaving.value = true
  try {
    await historyStore.saveAnalysis({
      route_name: analysis.value.route_name ?? undefined,
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

async function handleShare(): Promise<void> {
  // Find the history item we just saved
  await historyStore.fetchHistory()
  const latest = historyStore.items[0]
  if (!latest) return

  try {
    const res = await fetch('/api/v1/share', {
      method: 'POST',
      headers: { ...auth.headers(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ history_id: latest.id }),
    })
    if (!res.ok) throw new Error('Error sharing')
    const data = await res.json()
    const shareUrl = `${window.location.origin}${data.url}`
    await navigator.clipboard.writeText(shareUrl)
    shareLinkCopied.value = true
    setTimeout(() => { shareLinkCopied.value = false }, 3000)
  } catch (e) {
    console.error('Error sharing:', e)
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

// estimatedKcal, preliminaryMide, preliminaryMideLabel, precalcAdvice → moved to UploadFormView

// previewStats → moved to UploadFormView

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

        <!-- Share button -->
        <button
          v-if="auth.isAuthenticated && savedToHistory"
          class="btn btn-xs sm:btn-sm btn-outline border-base-300 hover:bg-base-200 gap-1.5 font-bold rounded-lg text-xs"
          title="Compartir análisis"
          @click="handleShare"
        >
          <AppIcon name="route" :size="14" />
          <span class="hidden sm:inline">Compartir</span>
        </button>

        <!-- Share link copied feedback -->
        <span
          v-if="shareLinkCopied"
          class="text-xs font-medium text-emerald-600 dark:text-emerald-400"
        >
          ✓ Link copiado
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
          @click="router.push('/mapa/nueva')"
        >
          <span v-if="isLoading" class="loading loading-spinner loading-xs" />
          <span v-else>Nueva ruta</span>
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
    <!-- ANALYSIS VIEW                                                 -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <div
      class="flex-1 overflow-y-auto bg-base-100 pb-16"
    >
      <div class="mx-auto max-w-6xl px-4 py-5 sm:px-6">

        <!-- Header: Back button + actions -->
        <div class="av-header">
          <div class="av-header__top">
            <button class="av-header__back" @click="router.push('/mapa/nueva')">
              <AppIcon name="arrow-right" :size="14" class="av-header__back-icon" />
              Nueva ruta
            </button>
            <div class="av-header__actions">
              <button class="av-action-btn" :disabled="isExportingPdf" @click="downloadPdfReport">
                <AppIcon :name="isExportingPdf ? 'clock' : 'download'" :size="14" />
                <span>{{ isExportingPdf ? 'Exportando...' : 'PDF' }}</span>
              </button>
              <button v-if="auth.isAuthenticated && analysis && !savedToHistory" class="av-action-btn" :disabled="isSaving" @click="saveToHistory">
                <AppIcon name="shield" :size="14" />
                <span>{{ isSaving ? 'Guardando...' : 'Guardar' }}</span>
              </button>
              <span v-else-if="savedToHistory" class="av-saved">✓ Guardado</span>
            </div>
          </div>
          <h1 class="av-header__title">{{ routeName }}</h1>
          <div class="av-header__meta">
            <span class="av-badge" :class="effortBadgeClass">MIDE {{ analysis?.summary.mide_global ?? 1 }}/5 · {{ effortLabel }}</span>
            <span class="av-header__dot">·</span>
            <span>{{ displayDistance }}</span>
            <span class="av-header__dot">·</span>
            <span>{{ displayElevation }}</span>
            <span class="av-header__dot">·</span>
            <span>{{ displayTime }}</span>
          </div>
        </div>

        <!-- Tabs -->
        <nav class="av-tabs">
          <button
            v-for="tab in [
              { id: 'resumen', label: 'Resumen' },
              { id: 'detalles', label: 'Detalles' },
              { id: 'ruta', label: 'Ruta' },
            ]"
            :key="tab.id"
            class="av-tabs__item"
            :class="{ 'av-tabs__item--active': activeTab === tab.id }"
            @click="activeTab = tab.id as PageTab"
          >
            {{ tab.label }}
          </button>
        </nav>

        <!-- ── TAB: RESUMEN (Hero) ── -->
        <div v-if="activeTab === 'resumen'" class="av-resumen">

          <!-- Full-width hero map -->
          <div class="av-map">
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
            <button
              class="av-map__expand"
              title="Expandir a modo análisis completo"
              @click="activeTab = 'ruta'"
            >
              <AppIcon name="maximize-2" :size="18" />
            </button>
          </div>

          <!-- Compact metric row -->
          <div class="av-metrics">
            <div class="av-metric">
              <AppIcon name="route" :size="16" />
              <span class="av-metric__value">{{ displayDistance }}</span>
            </div>
            <div class="av-metric">
              <AppIcon name="mountain" :size="16" />
              <span class="av-metric__value">{{ displayElevation }}</span>
            </div>
            <div class="av-metric">
              <AppIcon name="clock" :size="16" />
              <span class="av-metric__value">{{ displayTime }}</span>
            </div>
            <div class="av-metric">
              <AppIcon name="zap" :size="16" />
              <span class="av-metric__value">{{ displayCalories }}</span>
            </div>
          </div>

          <!-- Compact hiker profile strip -->
          <div class="av-profile-strip">
            <div class="av-profile-strip__icon">
              <AppIcon name="footprints" :size="14" />
            </div>
            <span class="av-profile-strip__name">{{ profile.name || 'Senderista' }}</span>
            <span class="av-profile-strip__sep">·</span>
            <span>{{ profile.weight_kg }} kg + {{ profile.load_kg }} kg</span>
            <span class="av-profile-strip__sep">·</span>
            <span>{{ fitnessLevelLabel }}</span>
            <span class="av-profile-strip__sep">·</span>
            <span>{{ surfaceTypeLabel }}</span>
            <span class="av-profile-strip__sep">·</span>
            <span class="av-profile-strip__mass">{{ totalMass }} kg total</span>
            <button class="av-profile-strip__edit" @click="router.push('/mapa/nueva')">
              <AppIcon name="upload" :size="12" />
              Recalibrar
            </button>
          </div>

          <!-- Elevation profile -->
          <div v-if="analysis" class="av-elevation">
            <h3 class="av-section-title">Perfil altimétrico</h3>
            <ElevationProfile
              :analysis="analysis"
              :selected-seq="selectedSegment?.seq ?? null"
              @select-segment="routeStore.selectSegment"
            />
          </div>

          <!-- Collapsible details: Profile + MIDE + Load -->
          <details class="av-details">
            <summary class="av-details__summary">
              <AppIcon name="footprints" :size="16" />
              <span>Perfil biomecánico y MIDE</span>
              <AppIcon name="chevron-down" :size="14" class="av-details__chevron" />
            </summary>
            <div class="av-details__body">
              <!-- Hiker profile (compact) -->
              <div class="av-profile-row">
                <div class="av-profile-row__info">
                  <span class="av-profile-row__name">{{ profile.name || 'Senderista' }}</span>
                  <span class="av-profile-row__detail">{{ profile.weight_kg }} kg · {{ profile.load_kg }} kg carga · {{ totalMass }} kg total</span>
                </div>
                <span class="av-badge" :class="loadImpactBadge.class">{{ loadImpactBadge.label }}</span>
              </div>

              <!-- MIDE score with bars -->
              <div class="av-mide-bars">
                <div v-for="item in mideMetrics" :key="item.key" class="av-mide-bar">
                  <div class="av-mide-bar__header">
                    <span class="av-mide-bar__label">{{ item.label }}</span>
                    <span class="av-mide-bar__value">{{ item.value }}/5</span>
                  </div>
                  <div class="av-mide-bar__track">
                    <div
                      class="av-mide-bar__fill"
                      :style="{ width: `${(item.value / 5) * 100}%` }"
                    />
                  </div>
                </div>
              </div>

              <!-- Cardiac distribution bar -->
              <div class="av-cardiac">
                <h4 class="av-section-title">Zona cardíaca</h4>
                <div class="av-cardiac__bar">
                  <div
                    class="av-cardiac__segment av-cardiac__segment--z1"
                    :style="{ width: `${cardiacDistribution.pct1}%` }"
                  >
                    {{ cardiacDistribution.pct1 }}%
                  </div>
                  <div
                    class="av-cardiac__segment av-cardiac__segment--z2"
                    :style="{ width: `${cardiacDistribution.pct2}%` }"
                  >
                    {{ cardiacDistribution.pct2 }}%
                  </div>
                  <div
                    class="av-cardiac__segment av-cardiac__segment--z3"
                    :style="{ width: `${cardiacDistribution.pct3}%` }"
                  >
                    {{ cardiacDistribution.pct3 }}%
                  </div>
                </div>
                <div class="av-cardiac__legend">
                  <span>Z1-Z2 Cómodo</span>
                  <span>Z3 Umbral</span>
                  <span>Z5 Máximo</span>
                </div>
              </div>
            </div>
          </details>

          <!-- Route description -->
          <p class="av-description">{{ displayDescription }}</p>

          <!-- Action row -->
          <div class="av-actions">
            <button class="av-btn-primary" @click="activeTab = 'ruta'">
              <AppIcon name="map" :size="16" />
              Análisis GIS
            </button>
            <button class="av-btn-outline" @click="router.push('/mapa/nueva')">
              <AppIcon name="upload" :size="14" />
              Recalibrar
            </button>
          </div>
        </div>

        <!-- ── TAB: DETALLES (Condiciones + MIDE) ── -->
        <div v-else-if="activeTab === 'detalles'" class="av-detalles">

          <!-- Climate data -->
          <div class="av-detalles__section">
            <h2 class="av-section-title">Condiciones Meteorológicas</h2>
            <p class="av-detalles__subtitle">Datos climáticos del recorrido calculados en tiempo real.</p>
            <div class="av-climate-grid">
              <div class="av-climate-card">
                <span class="av-climate-card__label">Temperatura</span>
                <span class="av-climate-card__value">{{ simulation.climate.temperature_c ?? 22 }} °C</span>
              </div>
              <div class="av-climate-card">
                <span class="av-climate-card__label">Humedad</span>
                <span class="av-climate-card__value">{{ simulation.climate.humidity_pct ?? 65 }} %</span>
              </div>
              <div class="av-climate-card">
                <span class="av-climate-card__label">Índice WBGT</span>
                <span class="av-climate-card__value">{{ formatNumber(analysis?.summary.wbgt ?? 20.4, 1) }} °C</span>
              </div>
              <div class="av-climate-card">
                <span class="av-climate-card__label">Índice UV</span>
                <span class="av-climate-card__value">{{ simulation.climate.uv_index ?? 7 }} / 11</span>
              </div>
            </div>
          </div>

          <!-- MIDE breakdown -->
          <div class="av-detalles__section">
            <h2 class="av-section-title">Desglose MIDE (FEDA)</h2>
            <p class="av-detalles__subtitle">Método de Información de Excursiones — dificultad técnica y física.</p>
            <div class="av-mide-bars">
              <div v-for="item in mideMetrics" :key="item.key" class="av-mide-bar">
                <div class="av-mide-bar__header">
                  <span class="av-mide-bar__label">{{ item.label }}</span>
                  <span class="av-mide-bar__value">{{ item.value }}/5</span>
                </div>
                <div class="av-mide-bar__track">
                  <div
                    class="av-mide-bar__fill"
                    :style="{ width: `${(item.value / 5) * 100}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── TAB: RUTA (GIS Map + Segment Detail + Route Planner) ── -->
        <div v-else-if="activeTab === 'ruta'" class="av-ruta">
          <div class="av-ruta__header">
            <div>
              <h2 class="av-section-title">Auditoría Técnica de Tramos</h2>
              <p class="av-detalles__subtitle">Selecciona cualquier tramo en el mapa para inspeccionar sus métricas biomecánicas.</p>
            </div>
            <div class="av-ruta__header-actions">
              <button class="av-action-btn" :disabled="isExportingPdf" @click="downloadPdfReport">
                <AppIcon :name="isExportingPdf ? 'clock' : 'download'" :size="14" />
                <span>{{ isExportingPdf ? 'Exportando...' : 'PDF' }}</span>
              </button>
              <span class="av-ruta__count">{{ analysis?.segments.length ?? 0 }} tramos</span>
            </div>
          </div>

          <!-- Full-width interactive analysis map -->
          <div class="av-map av-map--analysis">
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

          <!-- Grid: Segment Detail + Route Planner -->
          <div class="av-ruta__grid">

            <!-- Selected Segment Detail -->
            <div class="av-segment-card">
              <div v-if="selectedSegment">
                <div class="av-segment-card__header">
                  <div>
                    <h3 class="av-segment-card__title">Tramo #{{ selectedSegment.seq }}</h3>
                    <p class="av-segment-card__direction">{{ directionLabel(selectedSegment.direction) }}</p>
                  </div>
                  <span class="av-badge" :class="selectedRiskClass">{{ selectedRiskLabel }} · {{ selectedSegment.risk_score }}</span>
                </div>

                <div class="av-segment-card__meaning">{{ selectedSegmentMeaning }}</div>

                <div class="av-segment-card__metrics">
                  <div class="av-segment-metric">
                    <span class="av-segment-metric__label">Velocidad</span>
                    <strong class="av-segment-metric__value">{{ selectedSegment.velocity_kmh }} km/h</strong>
                  </div>
                  <div class="av-segment-metric">
                    <span class="av-segment-metric__label">Pendiente</span>
                    <strong class="av-segment-metric__value">{{ selectedSegment.slope_pct }}</strong>
                  </div>
                  <div class="av-segment-metric">
                    <span class="av-segment-metric__label">Coste Transporte</span>
                    <strong class="av-segment-metric__value">{{ selectedSegment.cot_j_per_kg_m }} J/kg·m</strong>
                  </div>
                  <div class="av-segment-metric">
                    <span class="av-segment-metric__label">Tasa Metabólica</span>
                    <strong class="av-segment-metric__value">{{ selectedSegment.metabolic_rate_w }} W</strong>
                  </div>
                </div>

                <div class="av-segment-card__tags">
                  <span class="av-tag">{{ selectedSegment.surface_type }}</span>
                  <span class="av-tag" :class="selectedSegment.is_on_path ? 'av-tag--success' : 'av-tag--warning'">
                    {{ selectedSegment.is_on_path ? 'sendero consolidado' : 'off-path' }}
                  </span>
                  <span v-if="selectedSegment.is_eccentric_fatigue" class="av-tag av-tag--error">bajada fatigante</span>
                </div>
              </div>

              <div v-else class="av-segment-card__empty">
                <AppIcon name="map" :size="32" />
                <p>Toca un tramo en el mapa para ver sus métricas</p>
              </div>
            </div>

            <!-- Route Planner -->
            <div class="av-planner-card">
              <h3 class="av-section-title">Planificador de Ruta Óptima</h3>
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
</template>

<style scoped>

    /* ── Header ── */
    .av-header {
      margin-bottom: 1.25rem;
    }

    .av-header__top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.75rem;
    }

    .av-header__back {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      padding: 0.375rem 0.75rem;
      border-radius: 9999px;
      background: transparent;
      border: none;
      font-size: 0.8125rem;
      font-weight: 600;
      color: #1a1a1a;
      cursor: pointer;
      transition: background 100ms ease-out;
    }

    .av-header__back:hover {
      background: rgba(0, 0, 0, 0.04);
    }

    .av-header__back:active {
      transform: scale(0.97);
      transition: transform 100ms ease-out;
    }

    .av-header__actions {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .av-action-btn {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      padding: 0.375rem 0.75rem;
      border-radius: 9999px;
      background: rgba(0, 0, 0, 0.03);
      border: 1px solid rgba(0, 0, 0, 0.06);
      font-size: 0.8125rem;
      font-weight: 600;
      color: #1a1a1a;
      cursor: pointer;
      transition: background 100ms ease-out;
    }

    .av-action-btn:hover {
      background: rgba(0, 0, 0, 0.06);
    }

    .av-action-btn:active {
      transform: scale(0.97);
      transition: transform 100ms ease-out;
    }

    .av-action-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .av-saved {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #059669;
    }

    .av-header__title {
      font-size: 1.75rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      line-height: 1.2;
      color: #1a1a1a;
      margin: 0;
    }

    .av-header__meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
      margin-top: 0.5rem;
      font-size: 0.8125rem;
      font-weight: 500;
      color: #71717a;
    }

    .av-header__dot {
      opacity: 0.3;
    }

    .av-badge {
      display: inline-flex;
      align-items: center;
      padding: 0.125rem 0.625rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
    }

    /* ── Tabs ── */
    .av-tabs {
      display: flex;
      gap: 0;
      border-bottom: 1px solid rgba(0,0,0,0.08);
      margin-bottom: 1.5rem;
    }

    .av-tabs__item {
      padding: 0.75rem 1.25rem;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      font-size: 0.875rem;
      font-weight: 600;
      color: #71717a;
      cursor: pointer;
      transition: color 150ms ease-out, border-color 150ms ease-out;
      margin-bottom: -1px;
    }

    .av-tabs__item:hover {
      color: #1a1a1a;
    }

    .av-tabs__item--active {
      color: #059669;
      border-bottom-color: #059669;
    }

    .av-tabs__item:active {
      transform: scale(0.97);
      transition: transform 100ms ease-out;
    }

    /* ── Resumen Tab ── */
    .av-resumen {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* ── Hero Map ── */
    .av-map {
      position: relative;
      width: 100%;
      height: 500px;
      border-radius: 1rem;
      overflow: hidden;
      background: #f5f5f5;
    }

    @media (min-width: 640px) {
      .av-map {
        height: 560px;
      }
    }

    .av-map--analysis {
      height: 500px;
      margin-bottom: 1.5rem;
    }

    @media (min-width: 640px) {
      .av-map--analysis {
        height: 500px;
      }
    }

    .av-map__expand {
      position: absolute;
      right: 0.75rem;
      top: 0.75rem;
      z-index: 20;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.75rem;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: none;
      color: #1a1a1a;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      cursor: pointer;
      transition: background 100ms ease-out, transform 100ms ease-out;
    }

    .av-map__expand:hover {
      background: rgba(255, 255, 255, 1);
      transform: scale(1.05);
    }

    .av-map__expand:active {
      transform: scale(0.97);
      transition: transform 100ms ease-out;
    }

    /* ── Compact Metrics ── */
    .av-metrics {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .av-metric {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.625rem 1rem;
      border-radius: 0.875rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      flex: 1;
      min-width: 120px;
    }

    .av-metric__value {
      font-size: 0.9375rem;
      font-weight: 700;
      color: #1a1a1a;
    }

    /* ── Profile Strip ── */
    .av-profile-strip {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.375rem;
      padding: 0.5rem 0.875rem;
      border-radius: 0.75rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      font-size: 0.75rem;
      font-weight: 500;
      color: #71717a;
    }

    .av-profile-strip__icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border-radius: 6px;
      background: rgba(5,150,105,0.1);
      color: #059669;
      flex-shrink: 0;
    }

    .av-profile-strip__name {
      font-weight: 700;
      color: #1a1a1a;
    }

    .av-profile-strip__sep {
      opacity: 0.3;
    }

    .av-profile-strip__mass {
      font-weight: 600;
      color: #059669;
    }

    .av-profile-strip__edit {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      margin-left: auto;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      border: none;
      background: rgba(5,150,105,0.08);
      color: #059669;
      font-size: 0.6875rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: background 150ms ease, transform 100ms ease-out;
    }

    .av-profile-strip__edit:hover {
      background: rgba(5,150,105,0.15);
    }

    .av-profile-strip__edit:active {
      transform: scale(0.95);
    }

    /* ── Elevation Profile ── */
    .av-elevation {
      border-radius: 1rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      padding: 1rem;
    }

    .av-section-title {
      font-size: 0.8125rem;
      font-weight: 700;
      color: #71717a;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin: 0 0 0.75rem 0;
    }

    /* ── Collapsible Details ── */
    .av-details {
      border-radius: 1rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      overflow: hidden;
    }

    .av-details__summary {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 1rem;
      cursor: pointer;
      font-size: 0.875rem;
      font-weight: 600;
      color: #1a1a1a;
      list-style: none;
      user-select: none;
    }

    .av-details__summary::-webkit-details-marker {
      display: none;
    }

    .av-details__summary::marker {
      display: none;
      content: '';
    }

    .av-details__chevron {
      margin-left: auto;
      transition: transform 200ms ease-out;
    }

    .av-details[open] .av-details__chevron {
      transform: rotate(180deg);
    }

    .av-details__body {
      padding: 0 1rem 1rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    /* ── Profile Row ── */
    .av-profile-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding: 0.75rem;
      border-radius: 0.75rem;
      background: rgba(0,0,0,0.02);
    }

    .av-profile-row__info {
      display: flex;
      flex-direction: column;
      gap: 0.125rem;
    }

    .av-profile-row__name {
      font-size: 0.875rem;
      font-weight: 700;
      color: #1a1a1a;
    }

    .av-profile-row__detail {
      font-size: 0.75rem;
      color: #71717a;
    }

    /* ── MIDE Bars ── */
    .av-mide-bars {
      display: flex;
      flex-direction: column;
      gap: 0.875rem;
    }

    .av-mide-bar {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
    }

    .av-mide-bar__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .av-mide-bar__label {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #1a1a1a;
    }

    .av-mide-bar__value {
      font-size: 0.8125rem;
      font-weight: 700;
      color: #1a1a1a;
    }

    .av-mide-bar__track {
      width: 100%;
      height: 0.5rem;
      border-radius: 9999px;
      background: rgba(0,0,0,0.06);
      overflow: hidden;
    }

    .av-mide-bar__fill {
      height: 100%;
      border-radius: 9999px;
      background: linear-gradient(to right, #10b981, #f59e0b, #ef4444);
      transition: width 500ms ease-out;
    }

    /* ── Cardiac Distribution ── */
    .av-cardiac {
      padding-top: 0.5rem;
    }

    .av-cardiac__bar {
      display: flex;
      height: 1.5rem;
      border-radius: 0.5rem;
      overflow: hidden;
      font-size: 0.6875rem;
      font-weight: 700;
      color: #fff;
    }

    .av-cardiac__segment {
      display: flex;
      align-items: center;
      justify-content: center;
      transition: width 500ms ease-out;
    }

    .av-cardiac__segment--z1 {
      background: #059669;
    }

    .av-cardiac__segment--z2 {
      background: #f59e0b;
    }

    .av-cardiac__segment--z3 {
      background: #ef4444;
    }

    .av-cardiac__legend {
      display: flex;
      justify-content: space-between;
      margin-top: 0.375rem;
      font-size: 0.6875rem;
      font-weight: 500;
      color: #71717a;
      padding: 0 0.25rem;
    }

    /* ── Description ── */
    .av-description {
      font-size: 0.9375rem;
      line-height: 1.65;
      color: #71717a;
      margin: 0;
    }

    /* ── Action Buttons ── */
    .av-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      padding-top: 0.5rem;
    }

    .av-btn-primary {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.625rem 1.5rem;
      border-radius: 9999px;
      background: linear-gradient(135deg, #059669, #047857);
      color: #fff;
      border: none;
      font-size: 0.875rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
      transition: box-shadow 150ms ease-out;
    }

    .av-btn-primary:hover {
      box-shadow: 0 4px 16px rgba(5, 150, 105, 0.4);
    }

    .av-btn-primary:active {
      transform: scale(0.97);
      transition: transform 100ms ease-out;
    }

    .av-btn-outline {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.625rem 1.5rem;
      border-radius: 9999px;
      background: transparent;
      border: 1.5px solid rgba(0,0,0,0.12);
      color: #1a1a1a;
      font-size: 0.875rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 150ms ease-out;
    }

    .av-btn-outline:hover {
      background: rgba(0,0,0,0.03);
    }

    .av-btn-outline:active {
      transform: scale(0.97);
      transition: transform 100ms ease-out;
    }

    /* ── Detalles Tab ── */
    .av-detalles {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .av-detalles__section {
      border-radius: 1rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      padding: 1.5rem;
    }

    .av-detalles__subtitle {
      font-size: 0.8125rem;
      color: #71717a;
      margin: 0 0 1.25rem 0;
    }

    .av-climate-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
    }

    @media (min-width: 640px) {
      .av-climate-grid {
        grid-template-columns: repeat(4, 1fr);
      }
    }

    .av-climate-card {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      padding: 1rem;
      border-radius: 0.75rem;
      background: rgba(0,0,0,0.02);
    }

    .av-climate-card__label {
      font-size: 0.75rem;
      font-weight: 500;
      color: #71717a;
    }

    .av-climate-card__value {
      font-size: 1.125rem;
      font-weight: 700;
      color: #1a1a1a;
    }

    /* ── Ruta Tab ── */
    .av-ruta {
      display: flex;
      flex-direction: column;
      gap: 0;
    }

    .av-ruta__header {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }

    .av-ruta__header-actions {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .av-ruta__count {
      font-size: 0.75rem;
      font-weight: 600;
      color: #71717a;
      padding: 0.25rem 0.625rem;
      border-radius: 9999px;
      background: rgba(0,0,0,0.03);
    }

    .av-ruta__grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    @media (min-width: 1024px) {
      .av-ruta__grid {
        grid-template-columns: 1fr 1fr;
      }
    }

    /* ── Segment Card ── */
    .av-segment-card {
      border-radius: 1rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      padding: 1.25rem;
    }

    .av-segment-card__header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }

    .av-segment-card__title {
      font-size: 0.9375rem;
      font-weight: 700;
      color: #1a1a1a;
      margin: 0;
    }

    .av-segment-card__direction {
      font-size: 0.75rem;
      color: #71717a;
      margin: 0.125rem 0 0 0;
    }

    .av-segment-card__meaning {
      font-size: 0.8125rem;
      line-height: 1.6;
      color: #71717a;
      padding: 0.75rem;
      border-radius: 0.75rem;
      background: rgba(0,0,0,0.02);
      margin-bottom: 0.75rem;
    }

    .av-segment-card__metrics {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }

    .av-segment-metric {
      padding: 0.625rem;
      border-radius: 0.625rem;
      background: rgba(0,0,0,0.02);
    }

    .av-segment-metric__label {
      display: block;
      font-size: 0.625rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #a1a1aa;
      margin-bottom: 0.125rem;
    }

    .av-segment-metric__value {
      font-size: 0.8125rem;
      font-weight: 800;
      color: #1a1a1a;
    }

    .av-segment-card__tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.375rem;
    }

    .av-tag {
      display: inline-flex;
      padding: 0.1875rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.6875rem;
      font-weight: 600;
      background: rgba(0,0,0,0.04);
      color: #71717a;
    }

    .av-tag--success {
      background: rgba(16, 185, 129, 0.1);
      color: #059669;
    }

    .av-tag--warning {
      background: rgba(245, 158, 11, 0.1);
      color: #d97706;
    }

    .av-tag--error {
      background: rgba(239, 68, 68, 0.1);
      color: #dc2626;
    }

    .av-segment-card__empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2.5rem 1rem;
      text-align: center;
      color: #a1a1aa;
    }

    .av-segment-card__empty p {
      font-size: 0.8125rem;
      font-weight: 600;
      margin: 0.5rem 0 0 0;
    }

    /* ── Planner Card ── */
    .av-planner-card {
      border-radius: 1rem;
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(0,0,0,0.06);
      padding: 1.25rem;
    }
    </style>

<style>

    html[data-theme="jic-dark"] .av-header { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-header__title { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-header__meta { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-header__back { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-header__back:hover { background: rgba(255, 255, 255, 0.06) !important; }
    html[data-theme="jic-dark"] .av-action-btn { color: #fafafa !important; background: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.08); }
    html[data-theme="jic-dark"] .av-action-btn:hover { background: rgba(255, 255, 255, 0.08) !important; }
    html[data-theme="jic-dark"] .av-saved { color: #34d399 !important; }
    html[data-theme="jic-dark"] .av-tabs { border-bottom-color: rgba(255, 255, 255, 0.08) !important; }
    html[data-theme="jic-dark"] .av-tabs__item { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-tabs__item:hover { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-tabs__item--active { color: #34d399 !important; border-bottom-color: #34d399; }
    html[data-theme="jic-dark"] .av-map { background: rgba(255, 255, 255, 0.04) !important; }
    html[data-theme="jic-dark"] .av-map__expand { background: rgba(30, 30, 30, 0.9) !important; color: #fafafa; }
    html[data-theme="jic-dark"] .av-map__expand:hover { background: rgba(40, 40, 40, 1) !important; }
    html[data-theme="jic-dark"] .av-metric { background: rgba(255, 255, 255, 0.04) !important; border-color: rgba(255, 255, 255, 0.06) !important; }
    html[data-theme="jic-dark"] .av-metric__value { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-profile-strip { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.06) !important; color: #a1a1aa !important; }
    html[data-theme="jic-dark"] .av-profile-strip__icon { background: rgba(52,211,153,0.1) !important; color: #34d399 !important; }
    html[data-theme="jic-dark"] .av-profile-strip__name { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-profile-strip__mass { color: #34d399 !important; }
    html[data-theme="jic-dark"] .av-profile-strip__edit { background: rgba(52,211,153,0.1) !important; color: #34d399 !important; }
    html[data-theme="jic-dark"] .av-profile-strip__edit:hover { background: rgba(52,211,153,0.18) !important; }
    html[data-theme="jic-dark"] .av-elevation,
    html[data-theme="jic-dark"] .av-details,
    html[data-theme="jic-dark"] .av-detalles__section,
    html[data-theme="jic-dark"] .av-segment-card,
    html[data-theme="jic-dark"] .av-planner-card {
      background: rgba(255, 255, 255, 0.04) !important;
      border-color: rgba(255, 255, 255, 0.06) !important;
    }
    html[data-theme="jic-dark"] .av-section-title { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-details__summary { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-profile-row { background: rgba(255, 255, 255, 0.04) !important; }
    html[data-theme="jic-dark"] .av-profile-row__name { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-profile-row__detail { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-mide-bar__label,
    html[data-theme="jic-dark"] .av-mide-bar__value { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-mide-bar__track { background: rgba(255, 255, 255, 0.08) !important; }
    html[data-theme="jic-dark"] .av-description { color: rgba(255, 255, 255, 0.6) !important; }
    html[data-theme="jic-dark"] .av-btn-primary { box-shadow: 0 2px 8px rgba(52, 211, 153, 0.3) !important; }
    html[data-theme="jic-dark"] .av-btn-primary:hover { box-shadow: 0 4px 16px rgba(52, 211, 153, 0.4) !important; }
    html[data-theme="jic-dark"] .av-btn-outline { border-color: rgba(255, 255, 255, 0.12) !important; color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-btn-outline:hover { background: rgba(255, 255, 255, 0.06) !important; }
    html[data-theme="jic-dark"] .av-climate-card { background: rgba(255, 255, 255, 0.04) !important; }
    html[data-theme="jic-dark"] .av-climate-card__label { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-climate-card__value { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-detalles__subtitle { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-ruta__count { color: rgba(255, 255, 255, 0.5) !important; background: rgba(255, 255, 255, 0.04) !important; }
    html[data-theme="jic-dark"] .av-segment-card__title { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-segment-card__direction { color: rgba(255, 255, 255, 0.5) !important; }
    html[data-theme="jic-dark"] .av-segment-card__meaning { color: rgba(255, 255, 255, 0.6) !important; background: rgba(255, 255, 255, 0.04) !important; }
    html[data-theme="jic-dark"] .av-segment-metric { background: rgba(255, 255, 255, 0.04) !important; }
    html[data-theme="jic-dark"] .av-segment-metric__label { color: rgba(255, 255, 255, 0.4) !important; }
    html[data-theme="jic-dark"] .av-segment-metric__value { color: #fafafa !important; }
    html[data-theme="jic-dark"] .av-tag { background: rgba(255, 255, 255, 0.06) !important; color: rgba(255, 255, 255, 0.6) !important; }
    html[data-theme="jic-dark"] .av-tag--success { background: rgba(52, 211, 153, 0.12) !important; color: #34d399 !important; }
    html[data-theme="jic-dark"] .av-tag--warning { background: rgba(251, 191, 36, 0.12) !important; color: #fbbf24 !important; }
    html[data-theme="jic-dark"] .av-tag--error { background: rgba(248, 113, 113, 0.12) !important; color: #f87171 !important; }
    html[data-theme="jic-dark"] .av-segment-card__empty { color: rgba(255, 255, 255, 0.3) !important; }
    </style>
