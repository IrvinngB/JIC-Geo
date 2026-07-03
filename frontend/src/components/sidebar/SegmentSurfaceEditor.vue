<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { Segment } from '@/stores/routeStore'

const props = defineProps<{
  segment: Segment
  disabled?: boolean
}>()

const emit = defineEmits<{
  apply: [payload: { surfaceType: string; canopyDensity: number; wholeRoute: boolean }]
}>()

// Must match the SurfaceType literal accepted by PATCH /routes/{id}/segments.
const SURFACE_OPTIONS = [
  { value: 'asphalt', label: 'Asfalto' },
  { value: 'pavement', label: 'Pavimento' },
  { value: 'dirt', label: 'Tierra' },
  { value: 'scrub', label: 'Matorral' },
  { value: 'dense_scrub', label: 'Matorral denso' },
  { value: 'sand', label: 'Arena' },
  { value: 'mud', label: 'Barro' },
  { value: 'sand_mud', label: 'Arena y barro' },
] as const

const form = reactive({
  surfaceType: props.segment.surface_type,
  canopyDensity: props.segment.canopy_density,
  wholeRoute: false,
})

// Re-sync the form when the user selects a different segment.
watch(
  () => props.segment.seq,
  () => {
    form.surfaceType = props.segment.surface_type
    form.canopyDensity = props.segment.canopy_density
  },
)

const canopyPct = computed(() => Math.round(form.canopyDensity * 100))

const isDirty = computed(
  () =>
    form.surfaceType !== props.segment.surface_type ||
    form.canopyDensity !== props.segment.canopy_density,
)

function apply(): void {
  emit('apply', {
    surfaceType: form.surfaceType,
    canopyDensity: form.canopyDensity,
    wholeRoute: form.wholeRoute,
  })
}
</script>

<template>
  <div class="rounded-box bg-base-200 p-3">
    <h3 class="text-xs font-semibold uppercase tracking-wider text-base-content/60">
      Corregir terreno
    </h3>
    <p class="mt-1 text-xs text-base-content/60">
      La superficie y la sombra afectan velocidad, esfuerzo y riesgo. Ajústalas si conoces el
      terreno real.
    </p>

    <label class="form-control mt-2">
      <span class="label-text text-xs font-medium">Tipo de superficie</span>
      <select
        v-model="form.surfaceType"
        class="select select-bordered select-sm"
        :disabled="disabled"
      >
        <option v-for="option in SURFACE_OPTIONS" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
    </label>

    <label class="form-control mt-2">
      <span class="label-text text-xs font-medium">Cobertura forestal · {{ canopyPct }}%</span>
      <input
        v-model.number="form.canopyDensity"
        type="range"
        min="0"
        max="1"
        step="0.05"
        class="range range-sm"
        :disabled="disabled"
      />
    </label>

    <label class="mt-2 flex cursor-pointer items-center gap-2">
      <input
        v-model="form.wholeRoute"
        type="checkbox"
        class="checkbox checkbox-sm"
        :disabled="disabled"
      />
      <span class="label-text text-xs">Aplicar a toda la ruta</span>
    </label>

    <button
      type="button"
      class="btn btn-primary btn-sm mt-3 w-full"
      :disabled="disabled || (!isDirty && !form.wholeRoute)"
      @click="apply"
    >
      Aplicar y recalcular
    </button>
  </div>
</template>
