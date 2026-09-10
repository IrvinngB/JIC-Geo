<script setup lang="ts">
import type { OptimalPathResult, RoutingAlgorithm } from '@/stores/routeStore'
import AppIcon from '@/components/icons/AppIcon.vue'

const props = defineProps<{
  isActive: boolean
  algorithm: RoutingAlgorithm
  start: number | null
  end: number | null
  waypoints: number[]
  canCompute: boolean
  optimalPath: OptimalPathResult | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  toggleActive: []
  'update:algorithm': [value: RoutingAlgorithm]
  removeNode: [nodeId: number]
  compute: []
  clear: []
}>()
</script>

<template>
  <div class="form-control space-y-2.5 rounded-box bg-base-100 p-2.5 shadow-sm sm:space-y-3 sm:p-3">
    <label class="label cursor-pointer gap-2.5 p-0 sm:gap-3">
      <span>
        <span class="block text-xs font-semibold sm:text-sm">Ruta óptima</span>
        <span class="text-[11px] text-base-content/60 sm:text-xs">
          Toca puntos del mapa: inicio, fin y paradas.
        </span>
      </span>
      <input
        type="checkbox"
        class="toggle toggle-primary toggle-sm sm:toggle-md"
        :checked="props.isActive"
        :disabled="props.disabled"
        @change="emit('toggleActive')"
      />
    </label>

    <template v-if="props.isActive">
      <label class="block text-[11px] font-semibold sm:text-xs">
        Algoritmo
        <select
          class="select select-bordered select-sm mt-1 w-full"
          :value="props.algorithm"
          :disabled="props.disabled"
          @change="
            emit('update:algorithm', ($event.target as HTMLSelectElement).value as RoutingAlgorithm)
          "
        >
          <option value="astar">A* (rápido)</option>
          <option value="dijkstra">Dijkstra (exhaustivo)</option>
        </select>
      </label>

      <div class="space-y-1 text-[11px] sm:text-xs">
        <div class="flex items-center justify-between rounded-box bg-base-200 px-2 py-1">
          <span><span class="badge badge-success badge-xs mr-1.5 sm:mr-2"></span>Inicio</span>
          <span v-if="props.start !== null" class="flex items-center gap-1.5">
            #{{ props.start }}
            <button class="btn btn-ghost btn-xs px-0.5" @click="emit('removeNode', props.start)">
              <AppIcon name="x" :size="12" />
            </button>
          </span>
          <span v-else class="text-base-content/50">Toca un punto</span>
        </div>

        <div class="flex items-center justify-between rounded-box bg-base-200 px-2 py-1">
          <span><span class="badge badge-error badge-xs mr-1.5 sm:mr-2"></span>Fin</span>
          <span v-if="props.end !== null" class="flex items-center gap-1.5">
            #{{ props.end }}
            <button class="btn btn-ghost btn-xs px-0.5" @click="emit('removeNode', props.end)">
              <AppIcon name="x" :size="12" />
            </button>
          </span>
          <span v-else class="text-base-content/50">Toca otro punto</span>
        </div>

        <div
          v-for="waypoint in props.waypoints"
          :key="waypoint"
          class="flex items-center justify-between rounded-box bg-base-200 px-2 py-1"
        >
          <span><span class="badge badge-info badge-xs mr-1.5 sm:mr-2"></span>Parada</span>
          <span class="flex items-center gap-1.5">
            #{{ waypoint }}
            <button class="btn btn-ghost btn-xs px-0.5" @click="emit('removeNode', waypoint)">
              <AppIcon name="x" :size="12" />
            </button>
          </span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-1.5 sm:gap-2">
        <button
          class="btn btn-primary btn-xs sm:btn-sm"
          :disabled="props.disabled || !props.canCompute"
          @click="emit('compute')"
        >
          Calcular ruta
        </button>
        <button class="btn btn-ghost btn-xs sm:btn-sm" :disabled="props.disabled" @click="emit('clear')">
          Limpiar
        </button>
      </div>

      <div v-if="props.optimalPath" class="rounded-box bg-base-200 p-2 text-[11px] sm:text-xs">
        <p>Costo total: <strong>{{ props.optimalPath.total_cost.toFixed(2) }}</strong></p>
        <p>Pasos: <strong>{{ props.optimalPath.steps.length }}</strong></p>
      </div>
    </template>
  </div>
</template>
