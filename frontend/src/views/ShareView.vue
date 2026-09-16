<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { formatNumber, formatDurationHours } from '@/utils/formatters'

const route = useRoute()
const code = route.params.code as string

const data = ref<any>(null)
const isLoading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await fetch(`/api/v1/share/${code}`)
    if (!res.ok) throw new Error('No encontrado')
    data.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
})

const mideLabel = computed(() => {
  const m = data.value?.mide_global ?? 0
  if (m <= 1) return 'Fácil'
  if (m === 2) return 'Moderada'
  if (m === 3) return 'Exigente'
  if (m === 4) return 'Difícil'
  return 'Muy difícil'
})

const mideColor = computed(() => {
  const m = data.value?.mide_global ?? 0
  if (m <= 2) return 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-400'
  if (m === 3) return 'text-amber-600 bg-amber-50 dark:bg-amber-950/40 dark:text-amber-400'
  return 'text-rose-600 bg-rose-50 dark:bg-rose-950/40 dark:text-rose-400'
})

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
}
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <!-- Loading -->
    <div v-if="isLoading" class="flex min-h-screen items-center justify-center">
      <span class="loading loading-spinner loading-lg text-primary" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex min-h-screen items-center justify-center">
      <div class="text-center">
        <AppIcon name="alert-triangle" :size="48" class="mx-auto mb-4 text-error/40" />
        <h1 class="text-xl font-bold">Ruta no encontrada</h1>
        <p class="mt-2 text-sm text-base-content/50">Este enlace ya no existe o fue eliminado.</p>
        <RouterLink to="/" class="btn btn-primary btn-sm mt-6 text-white">Volver al inicio</RouterLink>
      </div>
    </div>

    <!-- Shared route -->
    <div v-else-if="data" class="mx-auto max-w-2xl px-4 py-12">
      <!-- Header -->
      <div class="mb-8 text-center">
        <div class="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-primary">
          <AppIcon name="mountain" :size="18" />
          <span class="text-sm font-bold">RiskTrail</span>
        </div>
        <h1 class="text-2xl font-extrabold tracking-tight sm:text-3xl">
          {{ data.route_name ?? 'Ruta sin nombre' }}
        </h1>
        <p class="mt-2 text-sm text-base-content/50">
          Compartido {{ data.view_count }} veces
        </p>
      </div>

      <!-- MIDE badge -->
      <div class="mb-6 flex justify-center">
        <div class="flex items-center gap-3 rounded-2xl px-6 py-4" :class="mideColor">
          <span class="text-4xl font-black">{{ data.mide_global }}</span>
          <div>
            <div class="font-bold">{{ mideLabel }}</div>
            <div class="text-xs opacity-70">Dificultad MIDE</div>
          </div>
        </div>
      </div>

      <!-- Stats grid -->
      <div class="mb-8 grid grid-cols-2 gap-4">
        <div class="rounded-2xl border border-base-200 bg-base-100 p-4 text-center">
          <AppIcon name="route" :size="20" class="mx-auto mb-1 text-base-content/30" />
          <div class="text-2xl font-black">{{ formatNumber(data.total_distance_km, 1) }} km</div>
          <div class="text-xs text-base-content/50">Distancia</div>
        </div>
        <div class="rounded-2xl border border-base-200 bg-base-100 p-4 text-center">
          <AppIcon name="clock" :size="20" class="mx-auto mb-1 text-base-content/30" />
          <div class="text-2xl font-black">{{ formatDurationHours(data.estimated_time_h) }}</div>
          <div class="text-xs text-base-content/50">Tiempo estimado</div>
        </div>
        <div class="rounded-2xl border border-base-200 bg-base-100 p-4 text-center">
          <AppIcon name="mountain" :size="20" class="mx-auto mb-1 text-base-content/30" />
          <div class="text-2xl font-black">+{{ formatNumber(data.elevation_gain_m, 0) }} m</div>
          <div class="text-xs text-base-content/50">Desnivel</div>
        </div>
        <div class="rounded-2xl border border-base-200 bg-base-100 p-4 text-center">
          <AppIcon name="zap" :size="20" class="mx-auto mb-1 text-base-content/30" />
          <div class="text-2xl font-black">{{ formatNumber(data.total_kcal, 0) }}</div>
          <div class="text-xs text-base-content/50">Calorías</div>
        </div>
      </div>

      <!-- Share link -->
      <div class="rounded-2xl border border-base-200 bg-base-100 p-4 text-center">
        <p class="mb-3 text-xs text-base-content/50">Compartir esta ruta</p>
        <button class="btn btn-primary btn-sm gap-2 text-white" @click="copyLink">
          <AppIcon name="download" :size="14" />
          Copiar enlace
        </button>
      </div>

      <!-- Footer -->
      <p class="mt-8 text-center text-xs text-base-content/30">
        Analizado con RiskTrail · Índice dinámico de riesgo en senderismo
      </p>
    </div>
  </div>
</template>
