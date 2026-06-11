<script setup lang="ts">
import { computed } from 'vue'
import type { RouteAnalysis } from '@/stores/routeStore'

const props = defineProps<{
  analysis: RouteAnalysis | null
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
  const fatigueText = fatigueH == null ? '' : ` La fatiga fuerte podría aparecer alrededor de ${formatNumber(fatigueH, 1)} h.`

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

function formatNumber(value: number, digits = 1): string {
  return value.toLocaleString('es-MX', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
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
        <div v-if="props.analysis" class="text-right">
          <div class="badge badge-primary badge-outline">MIDE {{ props.analysis.summary.mide_global }}</div>
          <p class="mt-1 text-xs font-semibold text-base-content/70">{{ effortLabel }}</p>
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
            <div class="text-xl font-extrabold">{{ formatNumber(props.analysis.summary.estimated_time_h, 2) }} h</div>
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
      </div>
    </div>
  </section>
</template>
