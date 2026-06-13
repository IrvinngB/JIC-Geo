<script setup lang="ts">
import { computed } from 'vue'
import type { MideDimensions } from '@/stores/routeStore'

const props = defineProps<{
  dimensions: MideDimensions | null
  global?: number
  compact?: boolean
}>()

const labels: Record<keyof MideDimensions, string> = {
  severity: 'Severidad',
  orientation: 'Orientación',
  displacement: 'Desplazamiento',
  effort: 'Esfuerzo',
}

const descriptions: Record<keyof MideDimensions, string> = {
  severity: 'Gravedad potencial de lesiones',
  orientation: 'Claridad de la ruta',
  displacement: 'Dificultad de rescate',
  effort: 'Esfuerzo físico requerido',
}

function barColor(value: number): string {
  if (value <= 1) return 'bg-success'
  if (value === 2) return 'bg-success/70'
  if (value === 3) return 'bg-warning'
  if (value === 4) return 'bg-warning/80'
  return 'bg-error'
}

const textColor = (value: number) => barColor(value).replace('bg-', 'text-')
</script>

<template>
  <div v-if="dimensions" class="space-y-3">
    <div v-if="global !== undefined" class="flex items-center gap-2 mb-3">
      <span class="badge badge-lg" :class="barColor(global).replace('bg-', 'badge-')">MIDE {{ global }}</span>
      <span class="text-xs text-base-content/60">Índice global de riesgo</span>
    </div>
    <div
      v-for="(value, key) in dimensions"
      :key="key"
      class="space-y-1"
    >
      <div class="flex items-center justify-between text-xs">
        <span class="font-medium text-base-content/70">{{ labels[key as keyof MideDimensions] }}</span>
        <span class="font-bold" :class="textColor(value)">{{ value }}/5</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="flex-1 rounded-full bg-base-200 h-2 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="barColor(value)"
            :style="{ width: `${(value / 5) * 100}%` }"
          />
        </div>
      </div>
      <p v-if="!compact" class="text-[10px] text-base-content/40">{{ descriptions[key as keyof MideDimensions] }}</p>
    </div>
  </div>
</template>
