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
    <div class="card-body gap-3 p-3 sm:gap-4 sm:p-4">
      <div>
        <h2 class="card-title text-xs font-semibold uppercase tracking-wider text-base-content/60 sm:text-sm">
          Perfil del excursionista
        </h2>
        <p class="mt-0.5 text-[11px] text-base-content/60 sm:mt-1 sm:text-xs">
          Estos datos alimentan el modelo biomecánico.
        </p>
      </div>

      <label class="form-control">
        <span class="label-text text-xs font-medium">Nombre <span class="text-base-content/40 font-normal">(opcional)</span></span>
        <input
          v-model="profile.name"
          type="text"
          placeholder="Ej. Juan Pérez"
          class="input input-bordered input-sm"
          :disabled="props.disabled"
        />
      </label>

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

      <label class="form-control">
        <span class="label-text text-xs font-medium">Tipo de superficie</span>
        <select
          v-model="profile.surface_type"
          class="select select-bordered select-sm"
          :disabled="props.disabled"
        >
          <option value="dirt">Tierra compacta</option>
          <option value="paved">Pavimento</option>
          <option value="gravel">Grava</option>
          <option value="mud">Barro</option>
          <option value="sand">Arena</option>
          <option value="scrub">Matorral</option>
          <option value="dense_scrub">Matorral denso</option>
        </select>
        <span class="label-text-alt text-xs text-base-content/50 mt-1">
          Barro, arena y matorral reducen velocidad y suben la orientación MIDE.
        </span>
      </label>

      <div v-if="!isValid" class="alert alert-error py-2 text-xs">
        La carga debe ser menor al peso corporal y no puede ser negativa.
      </div>
    </div>
  </section>
</template>
