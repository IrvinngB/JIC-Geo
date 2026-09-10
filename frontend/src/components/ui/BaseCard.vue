<script setup lang="ts">
withDefaults(
  defineProps<{
    padding?: boolean
    hover?: boolean
  }>(),
  {
    padding: true,
    hover: false,
  },
)
</script>

<template>
  <div
    class="rounded-2xl border border-base-300/60 bg-base-100 shadow-sm transition-all"
    :class="[
      padding ? 'p-5 sm:p-6' : '',
      hover ? 'hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl' : '',
    ]"
  >
    <slot />
  </div>
</template>
