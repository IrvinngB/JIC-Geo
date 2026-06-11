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
  <div class="form-control rounded-box bg-base-100 p-3 shadow-sm">
    <label class="label cursor-pointer gap-3 p-0">
      <span>
        <span class="block text-sm font-semibold">Clima simulado</span>
        <span class="text-xs text-base-content/60">
          Ajusta temperatura, lluvia, humedad y UV.
        </span>
      </span>
      <input
        type="checkbox"
        class="toggle toggle-primary"
        :checked="props.modelValue"
        :disabled="props.disabled"
        @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
    </label>
  </div>
</template>
