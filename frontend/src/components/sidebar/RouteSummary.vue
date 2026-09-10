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
    <div class="card-body p-3 sm:p-4">
      <div class="flex items-start justify-between gap-2">
      <div>
          <h2 class="card-title text-xs font-semibold uppercase tracking-wider text-base-content/60 sm:text-sm">
            Resumen
          </h2>
          <p v-if="props.analysis" class="mt-0.5 text-[11px] text-base-content/60 sm:mt-1 sm:text-xs">
            {{ props.analysis.route_name ?? 'Ruta sin nombre' }} · {{ props.analysis.source_format }}
          </p>
        </div>
        <div v-if="props.analysis" class="flex flex-col items-end gap-0.5 min-w-[60px] sm:gap-1 sm:min-w-[80px]">
          <div class="badge badge-primary badge-outline badge-sm whitespace-nowrap sm:badge-md">MIDE {{ props.analysis.summary.mide_global }}</div>
          <p class="text-[11px] font-semibold text-base-content/70 sm:text-xs">{{ effortLabel }}</p>
        </div>
      </div>

      <div v-if="!props.analysis" class="mt-3 rounded-box bg-base-200 p-3 text-xs text-base-content/60 sm:mt-4 sm:p-4">
        Aún no hay una ruta analizada.
      </div>

      <div v-else class="mt-3 space-y-3 sm:mt-4 sm:space-y-4">
        <div class="alert text-xs shadow-sm sm:text-sm" :class="effortClass">
          <div>
            <h3 class="font-bold">Lectura rápida: {{ effortLabel }}</h3>
            <p class="text-[11px] leading-relaxed sm:text-xs">{{ routeInterpretation }}</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 sm:gap-3">
          <div class="rounded-box bg-base-200 p-2 sm:p-3">
            <div class="text-[11px] text-base-content/50 sm:text-xs">Distancia</div>
            <div class="text-lg font-extrabold sm:text-xl">{{ formatNumber(props.analysis.summary.total_distance_km, 2) }} km</div>
          </div>
          <div class="rounded-box bg-base-200 p-2 sm:p-3">
            <div class="text-[11px] text-base-content/50 sm:text-xs">Tiempo</div>
            <div class="text-lg font-extrabold sm:text-xl">{{ formatDurationHours(props.analysis.summary.estimated_time_h) }}</div>
          </div>
          <div class="rounded-box bg-base-200 p-2 sm:p-3">
            <div class="text-[11px] text-base-content/50 sm:text-xs">Subida</div>
            <div class="text-lg font-extrabold sm:text-xl">{{ formatNumber(props.analysis.summary.elevation_gain_m, 0) }} m</div>
          </div>
          <div class="rounded-box bg-base-200 p-2 sm:p-3">
            <div class="text-[11px] text-base-content/50 sm:text-xs">Energía</div>
            <div class="text-lg font-extrabold sm:text-xl">{{ formatNumber(props.analysis.summary.total_kcal, 0) }} kcal</div>
          </div>
        </div>

        <div class="rounded-box bg-base-200 p-2.5 text-[11px] text-base-content/70 sm:p-3 sm:text-xs">
          <h3 class="mb-1.5 font-bold text-base-content sm:mb-2">Calidad del cálculo</h3>
          <div class="space-y-1.5 sm:space-y-2">
            <div class="flex justify-between gap-2">
              <span>Descenso</span>
              <strong>{{ formatNumber(props.analysis.summary.elevation_loss_m, 0) }} m</strong>
            </div>
            <div class="flex justify-between gap-2">
              <span>Segmentos</span>
              <strong>{{ props.analysis.segments.length }}</strong>
            </div>
            <div class="flex justify-between gap-2">
              <span>Corregidos</span>
              <strong>{{ props.analysis.summary.points_corrected }}</strong>
            </div>
            <p class="text-base-content/60">{{ correctedPointsLabel }}</p>
            <div class="flex justify-between gap-2">
              <span>Confiable Minetti</span>
              <strong>{{ formatNumber(props.analysis.summary.high_confidence_segments_pct, 1) }}%</strong>
            </div>
          </div>
        </div>

        <div
          v-if="props.analysis.summary.wbgt != null"
          class="rounded-box bg-base-200 p-2.5 text-[11px] text-base-content/70 sm:p-3 sm:text-xs"
        >
          <h3 class="mb-1.5 font-bold text-base-content sm:mb-2">
            Clima
            <span class="badge badge-xs ml-1" :class="props.analysis.summary.climate_source === 'api' ? 'badge-success' : 'badge-info'">
              {{ props.analysis.summary.climate_source === 'api' ? 'Real' : 'Simulado' }}
            </span>
          </h3>
          <div class="space-y-1.5 sm:space-y-2">
            <div class="flex justify-between gap-2">
              <span>Temperatura</span>
              <strong>{{ formatNumber(props.analysis.summary.temperature_c ?? 0, 1) }} °C</strong>
            </div>
            <div class="flex justify-between gap-2">
              <span>Humedad</span>
              <strong>{{ formatNumber(props.analysis.summary.humidity_pct ?? 0, 0) }}%</strong>
            </div>
            <div class="flex justify-between gap-2">
              <span>WBGT</span>
              <strong :class="(props.analysis.summary.wbgt ?? 0) >= 28 ? 'text-error' : ''">
                {{ formatNumber(props.analysis.summary.wbgt ?? 0, 1) }} °C
              </strong>
            </div>
            <div class="flex justify-between gap-2">
              <span>UV</span>
              <strong :class="(props.analysis.summary.uv_index ?? 0) >= 8 ? 'text-warning' : ''">
                {{ formatNumber(props.analysis.summary.uv_index ?? 0, 1) }}
              </strong>
            </div>
          </div>
        </div>
        <!-- PDF Download button -->
        <button
          type="button"
          class="btn btn-xs btn-outline btn-success w-full gap-2 sm:btn-sm"
          :disabled="isExporting"
          :class="{ 'opacity-60 cursor-not-allowed': isExporting }"
          @click="downloadPdf"
        >
          <span v-if="isExporting" class="loading loading-spinner loading-xs" />
          <AppIcon v-else name="download" :size="14" />
          {{ isExporting ? 'Generando...' : 'Descargar Informe PDF' }}
        </button>
      </div>
    </div>
  </section>
</template>
