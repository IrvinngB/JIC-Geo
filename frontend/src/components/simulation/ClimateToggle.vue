<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<template>
  <div class="form-control rounded-box bg-base-100 p-2.5 shadow-sm sm:p-3">
    <label class="label cursor-pointer gap-2.5 p-0 sm:gap-3">
      <span>
        <span class="block text-xs font-semibold sm:text-sm">Clima simulado</span>
        <span class="text-[11px] text-base-content/60 sm:text-xs">
          Ajusta temperatura, lluvia, humedad y UV.
        </span>
      </span>
      <input
        type="checkbox"
        class="toggle toggle-primary toggle-sm sm:toggle-md"
        :checked="props.modelValue"
        :disabled="props.disabled"
        @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
    </label>
  </div>
</template>
