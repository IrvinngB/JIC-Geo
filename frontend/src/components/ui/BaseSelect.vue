<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: string | number
    label?: string
    options: Array<{ value: string | number; label: string }>
    placeholder?: string
    error?: string
    disabled?: boolean
    size?: 'sm' | 'md'
  }>(),
  {
    placeholder: 'Seleccionar...',
    size: 'md',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <label class="form-control">
    <div v-if="label" class="label pb-1 pt-0">
      <span class="label-text text-xs font-medium text-base-content/70">{{ label }}</span>
    </div>
    <select
      :value="modelValue"
      :disabled="disabled"
      class="select select-bordered w-full transition-colors"
      :class="[
        size === 'sm' ? 'select-sm' : '',
        error ? 'select-error' : '',
      ]"
      @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option disabled value="">{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
    <div v-if="error" class="label pb-0 pt-1">
      <span class="label-text-alt text-[11px] text-error">{{ error }}</span>
    </div>
  </label>
</template>
