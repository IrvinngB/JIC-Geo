<script setup lang="ts">
withDefaults(
  defineProps<{
    type?: 'button' | 'submit' | 'reset'
    variant?: 'primary' | 'ghost' | 'outline'
    size?: 'sm' | 'md' | 'lg'
    loading?: boolean
    disabled?: boolean
    block?: boolean
  }>(),
  {
    type: 'button',
    variant: 'primary',
    size: 'md',
  },
)

const variantClasses: Record<string, string> = {
  primary: 'btn-primary text-white',
  ghost: 'btn-ghost text-base-content/60 hover:text-base-content',
  outline: 'btn-outline',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="btn gap-2 transition-all"
    :class="[
      variantClasses[variant],
      size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '',
      block ? 'w-full' : '',
      (disabled || loading) ? 'btn-disabled' : '',
    ]"
  >
    <span v-if="loading" class="loading loading-spinner loading-sm" />
    <slot v-else />
  </button>
</template>
