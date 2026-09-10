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
    <div class="card-body gap-3 p-3 sm:gap-4 sm:p-4">
      <div>
        <h2 class="card-title text-xs font-semibold uppercase tracking-wider text-base-content/60 sm:text-sm">
          Cargar ruta
        </h2>
        <p class="mt-0.5 text-[11px] text-base-content/60 sm:mt-1 sm:text-xs">
          Sube un archivo GPX o GeoJSON para procesarlo con el backend.
        </p>
      </div>

      <label
        class="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed p-4 text-center transition sm:rounded-box sm:p-5"
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
        <span class="text-xs font-semibold sm:text-sm">{{ fileLabel }}</span>
        <span class="mt-0.5 text-[11px] text-base-content/50 sm:mt-1 sm:text-xs">Arrastra o haz click para seleccionar</span>
      </label>

      <button
        class="btn btn-primary btn-sm text-white sm:btn-md"
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
