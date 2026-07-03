<script setup lang="ts">
import type {
  ClimateComparison,
  ClimateOverride,
  SimulationScenario,
} from '@/stores/routeStore'

const props = defineProps<{
  modelValue: ClimateOverride
  disabled?: boolean
  comparison?: ClimateComparison | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ClimateOverride]
  run: []
  scenario: [value: SimulationScenario]
}>()

function update<K extends keyof ClimateOverride>(key: K, value: number): void {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function formatNumber(value: number, digits = 0): string {
  return value.toLocaleString('es-MX', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}
</script>

<template>
  <section class="space-y-3 rounded-box bg-base-100 p-4 shadow-sm">
    <div class="grid grid-cols-2 gap-2">
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'dry')">Seco</button>
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'light_rain')">Lluvia leve</button>
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'heavy_rain')">Lluvia fuerte</button>
      <button class="btn btn-xs" :disabled="props.disabled" @click="emit('scenario', 'extreme_heat')">Calor extremo</button>
      <button class="btn btn-xs col-span-2" :disabled="props.disabled" @click="emit('scenario', 'night')">Noche</button>
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

    <div v-if="props.comparison" class="rounded-box bg-base-200 p-3 text-xs">
      <h3 class="mb-2 font-bold">Real vs simulado</h3>
      <div class="grid grid-cols-3 gap-1 text-center">
        <span class="text-base-content/50"></span>
        <span class="font-semibold text-base-content/70">Real</span>
        <span class="font-semibold text-primary">Simulado</span>

        <span class="text-left text-base-content/50">MIDE</span>
        <span>{{ props.comparison.real.mide_global }}</span>
        <span class="font-semibold">{{ props.comparison.simulated.mide_global }}</span>

        <span class="text-left text-base-content/50">Tiempo (h)</span>
        <span>{{ formatNumber(props.comparison.real.estimated_time_h, 1) }}</span>
        <span class="font-semibold">{{ formatNumber(props.comparison.simulated.estimated_time_h, 1) }}</span>

        <span class="text-left text-base-content/50">kcal</span>
        <span>{{ formatNumber(props.comparison.real.total_kcal) }}</span>
        <span class="font-semibold">{{ formatNumber(props.comparison.simulated.total_kcal) }}</span>

        <span class="text-left text-base-content/50">CCR</span>
        <span>{{ formatNumber(props.comparison.real.ccr) }}</span>
        <span class="font-semibold">{{ formatNumber(props.comparison.simulated.ccr) }}</span>
      </div>
    </div>
  </section>
</template>
