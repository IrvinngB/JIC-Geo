<script setup lang="ts">
import type { MideDimensions } from '@/stores/routeStore'

const props = defineProps<{
  dimensions: MideDimensions | null
  global?: number
}>()

const labels: Record<keyof MideDimensions, string> = {
  severity: 'Severidad',
  orientation: 'Orientación',
  displacement: 'Desplazamiento',
  effort: 'Esfuerzo',
}

function barColor(value: number): string {
  if (value <= 1) return 'bg-success'
  if (value === 2) return 'bg-success/70'
  if (value === 3) return 'bg-warning'
  if (value === 4) return 'bg-warning/80'
  return 'bg-error'
}
</script>

<template>
  <div v-if="dimensions" class="card bg-base-100 shadow-md">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold uppercase tracking-wider text-base-content/60">
        Índice MIDE
      </h2>
      <div class="mt-3 space-y-2">
        <div
          v-for="(value, key) in dimensions"
          :key="key"
          class="space-y-1"
        >
          <div class="flex items-center justify-between text-xs">
            <span class="font-medium text-base-content/70">{{ labels[key as keyof MideDimensions] }}</span>
            <span class="font-bold text-xs" :class="barColor(value).replace('bg-', 'text-')">{{ value }}/5</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex-1 rounded-full bg-base-200 h-1.5 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="barColor(value)"
                :style="{ width: `${(value / 5) * 100}%` }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
