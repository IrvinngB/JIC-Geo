<script setup lang="ts">
import type { HikerProfile } from '@/composables/useHikerProfile'

const profile = defineModel<HikerProfile>({ required: true })

const props = defineProps<{
  isValid: boolean
  disabled?: boolean
}>()
</script>

<template>
  <section class="card bg-base-100 shadow-md">
    <div class="card-body p-4 gap-4">
      <div>
        <h2 class="card-title text-sm font-semibold uppercase tracking-wider text-base-content/60">
          Perfil del excursionista
        </h2>
        <p class="mt-1 text-xs text-base-content/60">
          Estos datos alimentan Pandolf y el ajuste de condición física.
        </p>
      </div>

      <label class="form-control">
        <span class="label-text text-xs font-medium">Peso corporal (kg)</span>
        <input
          v-model.number="profile.weight_kg"
          type="number"
          min="1"
          class="input input-bordered input-sm"
          :disabled="props.disabled"
        />
      </label>

      <label class="form-control">
        <span class="label-text text-xs font-medium">Carga / mochila (kg)</span>
        <input
          v-model.number="profile.load_kg"
          type="number"
          min="0"
          class="input input-bordered input-sm"
          :disabled="props.disabled"
        />
      </label>

      <label class="form-control">
        <span class="label-text text-xs font-medium">Condición física</span>
        <select
          v-model="profile.fitness_level"
          class="select select-bordered select-sm"
          :disabled="props.disabled"
        >
          <option value="low">Baja</option>
          <option value="medium">Media</option>
          <option value="high">Alta</option>
          <option value="athlete">Atleta</option>
        </select>
      </label>

      <div v-if="!isValid" class="alert alert-error py-2 text-xs">
        La carga debe ser menor al peso corporal y no puede ser negativa.
      </div>
    </div>
  </section>
</template>
