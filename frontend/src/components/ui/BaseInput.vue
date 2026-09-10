<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: string | number | undefined
    label?: string
    type?: string
    placeholder?: string
    error?: string
    hint?: string
    disabled?: boolean
    required?: boolean
    size?: 'sm' | 'md'
  }>(),
  {
    type: 'text',
    placeholder: '',
    size: 'md',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <label class="form-control">
    <div v-if="label || $slots.label" class="label pb-1 pt-0">
      <span class="label-text text-xs font-medium text-base-content/70">
        <slot name="label">{{ label }}</slot>
        <span v-if="required" class="ml-0.5 text-error">*</span>
      </span>
    </div>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      class="input input-bordered w-full transition-colors"
      :class="[
        size === 'sm' ? 'input-sm' : '',
        error ? 'input-error' : '',
      ]"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <div v-if="hint && !error" class="label pb-0 pt-1">
      <span class="label-text-alt text-[11px] text-base-content/40">{{ hint }}</span>
    </div>
    <div v-if="error" class="label pb-0 pt-1">
      <span class="label-text-alt text-[11px] text-error">{{ error }}</span>
    </div>
  </label>
</template>
