<script setup lang="ts">
import type { ClimateOverride, SimulationScenario } from '@/stores/routeStore'

const props = defineProps<{
  modelValue: ClimateOverride
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ClimateOverride]
  run: []
  scenario: [value: SimulationScenario]
}>()

function update<K extends keyof ClimateOverride>(key: K, value: number): void {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <section class="space-y-3 rounded-box bg-base-100 p-4 shadow-sm">
    <div class="grid grid-cols-2 gap-2">
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'dry')">Seco</button>
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'light_rain')">Lluvia leve</button>
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'heavy_rain')">Lluvia fuerte</button>
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'extreme_heat')">Calor extremo</button>
    </div>

    <label class="block text-xs font-semibold">
      Temperatura: {{ props.modelValue.temperature_c }} C
      <input
        type="range"
        min="0"
        max="45"
        class="range range-primary range-xs"
        :value="props.modelValue.temperature_c"
        :disabled="props.disabled"
        @input="update('temperature_c', Number(($event.target as HTMLInputElement).value))"
      />
    </label>

    <label class="block text-xs font-semibold">
      Humedad: {{ props.modelValue.humidity_pct }}%
      <input
        type="range"
        min="0"
        max="100"
        class="range range-primary range-xs"
        :value="props.modelValue.humidity_pct"
        :disabled="props.disabled"
        @input="update('humidity_pct', Number(($event.target as HTMLInputElement).value))"
      />
    </label>

    <label class="block text-xs font-semibold">
      Precipitacion: {{ props.modelValue.precip_mm }} mm
      <input
        type="range"
        min="0"
        max="60"
        class="range range-primary range-xs"
        :value="props.modelValue.precip_mm"
        :disabled="props.disabled"
        @input="update('precip_mm', Number(($event.target as HTMLInputElement).value))"
      />
    </label>

    <label class="block text-xs font-semibold">
      UV: {{ props.modelValue.uv_index }}
      <input
        type="range"
        min="0"
        max="12"
        class="range range-primary range-xs"
        :value="props.modelValue.uv_index"
        :disabled="props.disabled"
        @input="update('uv_index', Number(($event.target as HTMLInputElement).value))"
      />
    </label>

    <button class="btn btn-primary btn-sm w-full" :disabled="props.disabled" @click="emit('run')">
      Simular clima
    </button>
  </section>
</template>
