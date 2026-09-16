<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useHistoryStore, type HistoryDetail } from '@/stores/historyStore'
import AppIcon from '@/components/icons/AppIcon.vue'
import { formatNumber, formatDurationHours } from '@/utils/formatters'

const auth = useAuthStore()
const historyStore = useHistoryStore()
const router = useRouter()

const left = ref<HistoryDetail | null>(null)
const right = ref<HistoryDetail | null>(null)
const isLoading = ref(true)

onMounted(async () => {
  if (!auth.isAuthenticated) {
    router.push('/login')
    return
  }

  // Get IDs from query params
  const leftId = new URLSearchParams(window.location.search).get('left')
  const rightId = new URLSearchParams(window.location.search).get('right')

  if (!leftId || !rightId) {
    router.push('/historial')
    return
  }

  try {
    const [l, r] = await Promise.all([
      historyStore.getDetail(leftId),
      historyStore.getDetail(rightId),
    ])
    left.value = l
    right.value = r
  } catch (e) {
    console.error('Error loading comparison:', e)
  } finally {
    isLoading.value = false
  }
})

function diff(a: number | null, b: number | null): string {
  if (a == null || b == null) return '--'
  const d = a - b
  const sign = d > 0 ? '+' : ''
  return `${sign}${d.toFixed(1)}`
}

function diffClass(a: number | null, b: number | null, lowerIsBetter = true): string {
  if (a == null || b == null) return ''
  if (a === b) return ''
  const isBetter = lowerIsBetter ? a < b : a > b
  return isBetter ? 'text-emerald-600' : 'text-rose-600'
}
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <header class="sticky top-0 z-40 border-b border-base-200 bg-base-100 px-4 shadow-xs sm:px-8">
      <div class="mx-auto flex h-14 max-w-6xl items-center justify-between">
        <div class="flex items-center gap-3">
          <RouterLink to="/historial" class="text-xs text-base-content/50 hover:text-base-content">← Historial</RouterLink>
          <h1 class="text-sm font-bold">Comparar</h1>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 py-6 sm:px-8">
      <div v-if="isLoading" class="space-y-4">
        <div class="h-40 animate-pulse rounded-2xl bg-base-200" />
        <div class="h-40 animate-pulse rounded-2xl bg-base-200" />
      </div>

      <div v-else-if="left && right" class="space-y-6">
        <!-- Route names -->
        <div class="grid grid-cols-[1fr_auto_1fr] gap-4 items-center">
          <h2 class="text-lg font-extrabold text-right">{{ left.route_name ?? 'Ruta 1' }}</h2>
          <span class="text-xs font-bold text-base-content/30">VS</span>
          <h2 class="text-lg font-extrabold">{{ right.route_name ?? 'Ruta 2' }}</h2>
        </div>

        <!-- Stats comparison -->
        <div class="space-y-3">
          <div v-for="stat in [
            { label: 'Distancia', leftVal: left.total_distance_km, rightVal: right.total_distance_km, unit: ' km', decimals: 1 },
            { label: 'Tiempo', leftVal: left.estimated_time_h, rightVal: right.estimated_time_h, unit: 'h', decimals: 1, isTime: true },
            { label: 'Desnivel', leftVal: left.elevation_gain_m, rightVal: right.elevation_gain_m, unit: ' m', decimals: 0 },
            { label: 'Calorías', leftVal: left.total_kcal, rightVal: right.total_kcal, unit: ' kcal', decimals: 0 },
            { label: 'MIDE', leftVal: left.mide_global, rightVal: right.mide_global, unit: '', decimals: 0 },
          ]" :key="stat.label" class="grid grid-cols-[1fr_120px_1fr] gap-4 items-center rounded-xl border border-base-200 bg-base-100 px-4 py-3">
            <div class="text-right">
              <span class="text-xl font-black" :class="diffClass(stat.leftVal, stat.rightVal, stat.label !== 'MIDE')">
                {{ stat.isTime ? formatDurationHours(stat.leftVal ?? 0) : formatNumber(stat.leftVal ?? 0, stat.decimals) }}{{ !stat.isTime ? stat.unit : '' }}
              </span>
            </div>
            <div class="text-center">
              <span class="text-xs font-bold text-base-content/40">{{ stat.label }}</span>
              <div class="text-[10px]" :class="diffClass(stat.leftVal, stat.rightVal, stat.label !== 'MIDE')">
                {{ diff(stat.leftVal, stat.rightVal) }}{{ !stat.isTime ? stat.unit : '' }}
              </div>
            </div>
            <div>
              <span class="text-xl font-black" :class="diffClass(stat.rightVal, stat.leftVal, stat.label !== 'MIDE')">
                {{ stat.isTime ? formatDurationHours(stat.rightVal ?? 0) : formatNumber(stat.rightVal ?? 0, stat.decimals) }}{{ !stat.isTime ? stat.unit : '' }}
              </span>
            </div>
          </div>
        </div>

        <!-- MIDE breakdown -->
        <div class="grid grid-cols-2 gap-4">
          <div v-for="(side, idx) in [left, right]" :key="idx" class="rounded-2xl border border-base-200 bg-base-100 p-4">
            <h3 class="mb-3 text-xs font-bold text-base-content/50">
              {{ idx === 0 ? 'Ruta 1' : 'Ruta 2' }}: {{ side.route_name ?? 'Sin nombre' }}
            </h3>
            <div v-if="side.analysis_json" class="space-y-2 text-xs">
              <div v-for="(dim, key) in JSON.parse(side.analysis_json)?.summary?.mide_dimensions ?? {}" :key="key" class="flex justify-between">
                <span class="text-base-content/60">{{ key }}</span>
                <span class="font-bold">{{ dim }}/5</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-12">
        <AppIcon name="alert-triangle" :size="40" class="mx-auto mb-3 text-base-content/20" />
        <p class="text-sm text-base-content/50">No se pudieron cargar las rutas para comparar</p>
      </div>
    </main>
  </div>
</template>
