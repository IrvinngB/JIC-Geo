<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useHistoryStore } from '@/stores/historyStore'
import { useRouteStore } from '@/stores/routeStore'
import AppIcon from '@/components/icons/AppIcon.vue'

const auth = useAuthStore()
const historyStore = useHistoryStore()
const routeStore = useRouteStore()
const router = useRouter()

const filter = ref<'all' | 'favorites'>('all')

onMounted(() => {
  if (!auth.isAuthenticated) {
    router.push('/login')
    return
  }
  historyStore.fetchHistory()
})

function toggleFilter() {
  filter.value = filter.value === 'all' ? 'favorites' : 'all'
  historyStore.fetchHistory({ favorites_only: filter.value === 'favorites' })
}

async function handleToggleFavorite(id: string) {
  await historyStore.toggleFavorite(id)
}

async function handleDelete(id: string) {
  if (confirm('¿Eliminar este análisis del historial?')) {
    await historyStore.deleteHistory(id)
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-PA', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatMide(mide: number | null): string {
  if (mide == null) return '--'
  if (mide <= 1) return 'Fácil'
  if (mide === 2) return 'Moderada'
  if (mide === 3) return 'Exigente'
  if (mide === 4) return 'Difícil'
  return 'Muy difícil'
}

function mideClass(mide: number | null): string {
  if (!mide || mide <= 2) return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
  if (mide === 3) return 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
  return 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
}

async function loadAnalysis(id: string) {
  const detail = await historyStore.getDetail(id)
  if (!detail) return
  try {
    const analysisData = JSON.parse(detail.analysis_json)
    routeStore.setAnalysis(analysisData)
    router.push('/mapa')
  } catch (e) {
    console.error('Error loading analysis:', e)
  }
}
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <header class="sticky top-0 z-40 border-b border-base-200 bg-base-100 px-4 shadow-xs sm:px-8">
      <div class="mx-auto flex h-14 max-w-4xl items-center justify-between">
        <div class="flex items-center gap-3">
          <RouterLink to="/mapa" class="text-xs text-base-content/50 hover:text-base-content">← Mapa</RouterLink>
          <h1 class="text-sm font-bold">Historial</h1>
          <span v-if="historyStore.total" class="badge badge-ghost badge-sm">{{ historyStore.total }}</span>
        </div>
        <button
          class="btn btn-xs gap-1.5 font-bold"
          :class="filter === 'favorites' ? 'btn-primary text-white' : 'btn-ghost text-base-content/50'"
          @click="toggleFilter"
        >
          <AppIcon name="shield" :size="12" />
          Favoritos
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-4xl px-4 py-6 sm:px-8">
      <!-- Loading -->
      <div v-if="historyStore.isLoading && historyStore.items.length === 0" class="space-y-3">
        <div v-for="i in 3" :key="i" class="h-20 animate-pulse rounded-2xl bg-base-200" />
      </div>

      <!-- Empty state -->
      <div v-else-if="historyStore.items.length === 0" class="rounded-2xl border border-dashed border-base-300 py-12 text-center">
        <AppIcon name="file-text" :size="40" class="mx-auto mb-3 text-base-content/20" />
        <p class="text-sm text-base-content/50">
          {{ filter === 'favorites' ? 'No tenés favoritos' : 'No hay análisis guardados' }}
        </p>
        <RouterLink to="/mapa" class="btn btn-primary btn-sm mt-4 text-white">Analizar una ruta</RouterLink>
      </div>

      <!-- History list -->
      <div v-else class="space-y-3">
        <div
          v-for="item in historyStore.items"
          :key="item.id"
          class="group flex items-center justify-between rounded-2xl border border-base-200 bg-base-100 p-4 transition hover:border-primary/30"
        >
          <div class="flex items-center gap-4">
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary font-bold text-xs">
              {{ item.mide_global ?? '--' }}
            </div>
            <div>
              <div class="font-bold text-sm">{{ item.route_name ?? 'Ruta sin nombre' }}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-base-content/50">
                <span>{{ formatDate(item.created_at) }}</span>
                <span v-if="item.total_distance_km" class="flex items-center gap-1">
                  <AppIcon name="route" :size="10" />
                  {{ item.total_distance_km.toFixed(1) }} km
                </span>
                <span v-if="item.estimated_time_h" class="flex items-center gap-1">
                  <AppIcon name="compass" :size="10" />
                  {{ item.estimated_time_h.toFixed(1) }}h
                </span>
                <span v-if="item.source_format" class="rounded bg-base-200 px-1.5 py-0.5 text-[10px] font-bold uppercase">
                  {{ item.source_format }}
                </span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-1">
            <span class="badge badge-sm mr-2" :class="mideClass(item.mide_global)">
              {{ formatMide(item.mide_global) }}
            </span>
            <button
              class="btn btn-ghost btn-xs text-primary opacity-0 group-hover:opacity-100 transition"
              title="Cargar en el mapa"
              @click="loadAnalysis(item.id)"
            >
              <AppIcon name="route" :size="14" />
            </button>
            <button
              class="btn btn-ghost btn-xs"
              :class="item.is_favorite ? 'text-amber-500' : 'text-base-content/30'"
              :title="item.is_favorite ? 'Quitar de favoritos' : 'Marcar como favorito'"
              @click="handleToggleFavorite(item.id)"
            >
              <AppIcon name="shield" :size="14" />
            </button>
            <button
              class="btn btn-ghost btn-xs text-error/40 opacity-0 group-hover:opacity-100 transition"
              title="Eliminar"
              @click="handleDelete(item.id)"
            >
              <AppIcon name="x" :size="14" />
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
