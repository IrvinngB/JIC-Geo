<script setup lang="ts">
import type { HikerProfile } from '@/composables/useHikerProfile'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseSelect from '@/components/ui/BaseSelect.vue'

const profile = defineModel<HikerProfile>({ required: true })

const props = defineProps<{
  isValid: boolean
  disabled?: boolean
}>()

const fitnessOptions = [
  { value: 'low', label: 'Baja' },
  { value: 'medium', label: 'Media' },
  { value: 'high', label: 'Alta' },
  { value: 'athlete', label: 'Atleta' },
]
</script>

<template>
  <section class="card bg-base-100 shadow-md">
    <div class="card-body gap-3 p-3 sm:gap-4 sm:p-4">
      <div>
        <h2 class="card-title text-xs font-semibold uppercase tracking-wider text-base-content/60 sm:text-sm">
          Perfil del excursionista
        </h2>
        <p class="mt-0.5 text-[11px] text-base-content/60 sm:mt-1 sm:text-xs">
          Estos datos alimentan el modelo biomecánico.
        </p>
      </div>

      <BaseInput
        v-model="profile.name"
        label="Nombre"
        placeholder="Ej. Juan Pérez"
        hint="Opcional"
        :disabled="props.disabled"
      />

      <BaseInput
        v-model.number="profile.weight_kg"
        label="Peso corporal (kg)"
        type="number"
        :disabled="props.disabled"
      />

      <BaseInput
        v-model.number="profile.load_kg"
        label="Carga / mochila (kg)"
        type="number"
        :disabled="props.disabled"
      />

      <BaseSelect
        v-model="profile.fitness_level"
        label="Condición física"
        :options="fitnessOptions"
        placeholder="Seleccionar..."
        :disabled="props.disabled"
      />

      <div v-if="!isValid" class="rounded-xl border border-error/30 bg-error/10 px-4 py-3 text-xs text-error">
        La carga debe ser menor al peso corporal y no puede ser negativa.
      </div>
    </div>
  </section>
</template>
