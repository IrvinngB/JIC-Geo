<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import { createApp } from 'vue'
import type { RouteAnalysis } from '@/stores/routeStore'
import type { HikerProfile } from '@/composables/useHikerProfile'
import RouteReportTemplate from '@/components/report/RouteReportTemplate.vue'
import RouteMap from '@/components/map/RouteMap.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { exportElementAsPdf, buildReportFilename } from '@/utils/pdfExport'
import { formatNumber, formatDurationHours } from '@/utils/formatters'

interface RouteMapInstance {
  captureImage: () => string | null
}

const props = defineProps<{
  analysis: RouteAnalysis | null
  profile?: HikerProfile
  routeMap?: RouteMapInstance | null
}>()

const effortLabel = computed(() => {
  const mide = props.analysis?.summary.mide_global ?? 0
  if (mide <= 1) return 'Fácil'
  if (mide === 2) return 'Moderada'
  if (mide === 3) return 'Exigente'
  if (mide === 4) return 'Difícil'
  return 'Muy difícil'
})

const effortClass = computed(() => {
  const mide = props.analysis?.summary.mide_global ?? 0
  if (mide <= 2) return 'alert-success'
  if (mide === 3) return 'alert-warning'
  return 'alert-error'
})

const routeInterpretation = computed(() => {
  if (!props.analysis) return ''

  const summary = props.analysis.summary
  const fatigueH = summary.time_to_severe_fatigue_h
  const estimatedH = summary.estimated_time_h

  let fatigueText = ''
  if (fatigueH != null) {
    if (fatigueH <= estimatedH) {
      fatigueText = ` Atención: la fatiga fuerte podría aparecer a los ${formatDurationHours(fatigueH)}, antes de terminar el recorrido.`
    } else {
      fatigueText = ` Margen adecuado: la ruta concluye antes de alcanzar fatiga severa (autonomía estimada: ${formatDurationHours(fatigueH)}).`
    }
  }

  if (summary.mide_global <= 2) {
    return `Ruta manejable para la mayoría de personas con condición física acorde.${fatigueText}`
  }
  if (summary.mide_global === 3) {
    return `Ruta exigente: requiere buen ritmo, hidratación y pausas planificadas.${fatigueText}`
  }
  return `Ruta pesada: conviene revisarla por tramos y evitar hacerla sin preparación.${fatigueText}`
})

const correctedPointsLabel = computed(() => {
  const count = props.analysis?.summary.points_corrected ?? 0
  if (count === 0) return 'No se detectaron saltos raros de elevación.'
  if (count <= 3) return 'Se corrigieron pocos puntos ruidosos de elevación.'
  return 'Hubo varias correcciones de elevación; revisar la calidad del GPX/DEM.'
})

// ── PDF Export ────────────────────────────────────────────────────────────────

const isExporting = ref(false)

async function downloadPdf(): Promise<void> {
  if (!props.analysis || isExporting.value) return

  isExporting.value = true

  try {
    // Mount inside an isolated iframe so DaisyUI oklch stylesheets are never inherited
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;left:-9999px;top:0;width:794px;height:1123px;border:none;opacity:0;pointer-events:none;'
    document.body.appendChild(iframe)

    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (!doc) throw new Error('Could not access iframe document')

    doc.open()
    doc.write('<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:#ffffff;"><div id="report-root"></div></body></html>')
    doc.close()

    const mountEl = doc.getElementById('report-root')!

    const mapImageBase64 = props.routeMap?.captureImage() ?? undefined

    const app = createApp(RouteReportTemplate, {
      analysis: props.analysis,
      profile: props.profile ?? {
        weight_kg: 70,
        load_kg: 10,
        fitness_level: 'medium' as const,
        surface_type: 'dirt' as const,
      },
      generatedAt: new Date(),
      hikerName: props.profile?.name?.trim() || undefined,
      mapImageBase64,
    })

    app.mount(mountEl)

    await nextTick()
    await new Promise((r) => setTimeout(r, 250))

    const target = (mountEl.firstElementChild ?? mountEl) as HTMLElement
    const filename = buildReportFilename(props.analysis.route_name, props.analysis.route_id)

    await exportElementAsPdf(target, filename)

    app.unmount()
    document.body.removeChild(iframe)
  } catch (err) {
    console.error('Error exporting PDF report:', err)
  } finally {
    isExporting.value = false
  }
}
</script>

<template>
  <section class="card bg-base-100 shadow-md">
    <div class="card-body p-4">
      <div class="flex items-start justify-between gap-3">
      <div>
          <h2 class="card-title text-sm font-semibold uppercase tracking-wider text-base-content/60">
            Resumen
          </h2>
          <p v-if="props.analysis" class="mt-1 text-xs text-base-content/60">
            {{ props.analysis.route_name ?? 'Ruta sin nombre' }} · {{ props.analysis.source_format }}
          </p>
        </div>
        <div v-if="props.analysis" class="flex flex-col items-end gap-1 min-w-[80px]">
          <div class="badge badge-primary badge-outline whitespace-nowrap">MIDE {{ props.analysis.summary.mide_global }}</div>
          <p class="text-xs font-semibold text-base-content/70">{{ effortLabel }}</p>
        </div>
      </div>

      <div v-if="!props.analysis" class="mt-4 rounded-box bg-base-200 p-4 text-sm text-base-content/60">
        Aún no hay una ruta analizada.
      </div>

      <div v-else class="mt-4 space-y-4">
        <div class="alert text-sm shadow-sm" :class="effortClass">
          <div>
            <h3 class="font-bold">Lectura rápida: {{ effortLabel }}</h3>
            <p class="text-xs leading-relaxed">{{ routeInterpretation }}</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-box bg-base-200 p-3">
            <div class="text-xs text-base-content/50">Distancia total</div>
            <div class="text-xl font-extrabold">{{ formatNumber(props.analysis.summary.total_distance_km, 2) }} km</div>
            <p class="mt-1 text-xs text-base-content/50">Qué tanto vas a caminar.</p>
          </div>
          <div class="rounded-box bg-base-200 p-3">
            <div class="text-xs text-base-content/50">Tiempo estimado</div>
            <div class="text-xl font-extrabold">{{ formatDurationHours(props.analysis.summary.estimated_time_h) }}</div>
            <p class="mt-1 text-xs text-base-content/50">Sin clima ni pausas largas.</p>
          </div>
          <div class="rounded-box bg-base-200 p-3">
            <div class="text-xs text-base-content/50">Subida acumulada</div>
            <div class="text-xl font-extrabold">{{ formatNumber(props.analysis.summary.elevation_gain_m, 0) }} m</div>
            <p class="mt-1 text-xs text-base-content/50">Lo que más pega en piernas y cardio.</p>
          </div>
          <div class="rounded-box bg-base-200 p-3">
            <div class="text-xs text-base-content/50">Energía estimada</div>
            <div class="text-xl font-extrabold">{{ formatNumber(props.analysis.summary.total_kcal, 0) }} kcal</div>
            <p class="mt-1 text-xs text-base-content/50">Gasto según tu peso/carga.</p>
          </div>
        </div>

        <div class="rounded-box bg-base-200 p-3 text-xs text-base-content/70">
          <h3 class="mb-2 font-bold text-base-content">Calidad del cálculo</h3>
          <div class="space-y-2">
            <div class="flex justify-between gap-3">
              <span>Descenso acumulado</span>
              <strong>{{ formatNumber(props.analysis.summary.elevation_loss_m, 0) }} m</strong>
            </div>
            <div class="flex justify-between gap-3">
              <span>Segmentos analizados</span>
              <strong>{{ props.analysis.segments.length }}</strong>
            </div>
            <div class="flex justify-between gap-3">
              <span>Puntos de elevación corregidos</span>
              <strong>{{ props.analysis.summary.points_corrected }}</strong>
            </div>
            <p class="text-base-content/60">{{ correctedPointsLabel }}</p>
            <div class="flex justify-between gap-3">
              <span>Segmentos dentro del rango confiable Minetti</span>
              <strong>{{ formatNumber(props.analysis.summary.high_confidence_segments_pct, 1) }}%</strong>
            </div>
          </div>
        </div>

        <div
          v-if="props.analysis.summary.wbgt != null"
          class="rounded-box bg-base-200 p-3 text-xs text-base-content/70"
        >
          <h3 class="mb-2 font-bold text-base-content">
            Condiciones climáticas
            <span class="badge badge-xs ml-1" :class="props.analysis.summary.climate_source === 'api' ? 'badge-success' : 'badge-info'">
              {{ props.analysis.summary.climate_source === 'api' ? 'Tiempo real' : 'Simulado' }}
            </span>
          </h3>
          <div class="space-y-2">
            <div class="flex justify-between gap-3">
              <span>Temperatura</span>
              <strong>{{ formatNumber(props.analysis.summary.temperature_c ?? 0, 1) }} °C</strong>
            </div>
            <div class="flex justify-between gap-3">
              <span>Humedad</span>
              <strong>{{ formatNumber(props.analysis.summary.humidity_pct ?? 0, 0) }}%</strong>
            </div>
            <div class="flex justify-between gap-3">
              <span>WBGT</span>
              <strong :class="(props.analysis.summary.wbgt ?? 0) >= 28 ? 'text-error' : ''">
                {{ formatNumber(props.analysis.summary.wbgt ?? 0, 1) }} °C
              </strong>
            </div>
            <div class="flex justify-between gap-3">
              <span>Precipitación</span>
              <strong>{{ formatNumber(props.analysis.summary.precip_mm ?? 0, 1) }} mm</strong>
            </div>
            <div class="flex justify-between gap-3">
              <span>Índice UV</span>
              <strong :class="(props.analysis.summary.uv_index ?? 0) >= 8 ? 'text-warning' : ''">
                {{ formatNumber(props.analysis.summary.uv_index ?? 0, 1) }}
              </strong>
            </div>
          </div>
        </div>
        <!-- PDF Download button -->
        <button
          type="button"
          class="btn btn-sm btn-outline btn-success w-full gap-2"
          :disabled="isExporting"
          :class="{ 'opacity-60 cursor-not-allowed': isExporting }"
          @click="downloadPdf"
        >
          <span v-if="isExporting" class="loading loading-spinner loading-xs" />
          <AppIcon v-else name="download" :size="15" />
          {{ isExporting ? 'Generando informe...' : 'Descargar Informe PDF' }}
        </button>
      </div>
    </div>
  </section>
</template>
