<script setup lang="ts">
import { computed, ref } from 'vue'
import type { HikerProfile } from '@/composables/useHikerProfile'

const props = defineProps<{
  isLoading: boolean
  profile: HikerProfile
  canSubmit: boolean
}>()

const emit = defineEmits<{
  analyze: [file: File, profile: HikerProfile]
}>()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)

const fileLabel = computed(() => selectedFile.value?.name ?? 'GPX o GeoJSON')

function setFile(file: File | undefined): void {
  if (!file) return
  selectedFile.value = file
}

function onFileInput(event: Event): void {
  const input = event.target as HTMLInputElement
  setFile(input.files?.[0])
}

function onDrop(event: DragEvent): void {
  event.preventDefault()
  isDragging.value = false
  setFile(event.dataTransfer?.files[0])
}

function submit(): void {
  if (!selectedFile.value || !props.canSubmit || props.isLoading) return
  emit('analyze', selectedFile.value, { ...props.profile })
}
</script>

<template>
  <section class="card bg-base-100 shadow-md">
    <div class="card-body p-4 gap-4">
      <div>
        <h2 class="card-title text-sm font-semibold uppercase tracking-wider text-base-content/60">
          Cargar ruta
        </h2>
        <p class="mt-1 text-xs text-base-content/60">
          Sube un archivo GPX o GeoJSON para procesarlo con el backend.
        </p>
      </div>

      <label
        class="flex cursor-pointer flex-col items-center justify-center rounded-box border border-dashed p-5 text-center transition"
        :class="isDragging ? 'border-primary bg-primary/10' : 'border-base-content/20 bg-base-200/50'"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop="onDrop"
      >
        <input
          type="file"
          accept=".gpx,.geojson,.json,application/geo+json,application/json"
          class="hidden"
          :disabled="isLoading"
          @change="onFileInput"
        />
        <span class="text-sm font-semibold">{{ fileLabel }}</span>
        <span class="mt-1 text-xs text-base-content/50">Arrastra aquí o haz click para seleccionar</span>
      </label>

      <button
        class="btn btn-primary text-white"
        :class="isLoading ? 'btn-disabled' : ''"
        :disabled="!selectedFile || !canSubmit || isLoading"
        @click="submit"
      >
        <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
        {{ isLoading ? 'Analizando...' : 'Analizar ruta' }}
      </button>
    </div>
  </section>
</template>
