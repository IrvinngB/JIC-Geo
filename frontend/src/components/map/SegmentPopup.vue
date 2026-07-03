<script setup lang="ts">
import type { Segment } from '@/stores/routeStore'

const props = defineProps<{
  segment: Segment
  x: number
  y: number
}>()

const emit = defineEmits<{
  close: []
  viewDetail: []
}>()

function directionLabel(direction: string): string {
  if (direction === 'ascent') return 'Subida'
  if (direction === 'descent') return 'Bajada'
  return 'Plano'
}

function riskBadgeClass(score: number): string {
  if (score >= 75) return 'badge-error'
  if (score >= 45) return 'badge-warning'
  return 'badge-success'
}
</script>

<template>
  <div
    class="absolute z-20 rounded-box bg-base-100 shadow-xl p-3 border border-base-300 pointer-events-auto min-w-[220px]"
    :style="{ left: `${x}px`, top: `${y}px`, transform: 'translate(-50%, -115%)' }"
  >
    <!-- Arrow pointer -->
    <div class="absolute left-1/2 bottom-0 -translate-x-1/2 translate-y-1/2 w-3 h-3 bg-base-100 border-b border-r border-base-300 rotate-45"></div>
    
    <div class="flex items-center justify-between gap-3 mb-2">
      <h3 class="font-bold text-sm">Tramo #{{ segment.seq }}</h3>
      <span class="badge badge-sm" :class="riskBadgeClass(segment.risk_score)">
        {{ segment.risk_score }}/100
      </span>
    </div>
    
    <div class="text-xs space-y-1 text-base-content/70">
      <div class="flex justify-between">
        <span>{{ directionLabel(segment.direction) }}</span>
        <span class="font-medium">{{ segment.slope_pct }}% pendiente</span>
      </div>
      <div class="flex justify-between">
        <span>Velocidad</span>
        <span class="font-medium">{{ segment.velocity_kmh }} km/h</span>
      </div>
      <div class="flex justify-between">
        <span>CoT</span>
        <span class="font-medium">{{ segment.cot_j_per_kg_m }} J/kg·m</span>
      </div>
    </div>
    
    <div v-if="segment.is_top_risk" class="mt-2 flex items-center gap-1 text-xs text-error font-semibold">
      <span>⚠</span> Top 10% de riesgo
    </div>
    
    <div class="mt-2 pt-2 border-t border-base-200 flex justify-between items-center">
      <span v-if="segment.is_eccentric_fatigue" class="text-[10px] text-error">Bajada fatigante</span>
      <button class="btn btn-xs btn-primary ml-auto" @click="emit('viewDetail')">
        Ver detalle
      </button>
    </div>
  </div>
</template>
