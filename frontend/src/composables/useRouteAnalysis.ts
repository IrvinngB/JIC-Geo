/**
 * useRouteAnalysis — composable for file upload and route analysis trigger.
 * MAP-03
 */

import { ref } from 'vue'
import { useRouteStore } from '@/stores/routeStore'
import type { HikerProfile } from './useHikerProfile'

export function useRouteAnalysis() {
  const store = useRouteStore()
  const isDragging = ref(false)

  function onDrop(event: DragEvent): void {
    event.preventDefault()
    isDragging.value = false
    const file = event.dataTransfer?.files[0]
    if (file) analyze(file)
  }

  function onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (file) analyze(file)
  }

  async function analyze(file: File, profile?: HikerProfile): Promise<void> {
    const defaultProfile: HikerProfile = profile ?? {
      weight_kg: 70,
      load_kg: 10,
      fitness_level: 'medium',
    }
    await store.uploadAndAnalyze(file, defaultProfile)
  }

  return { isDragging, onDrop, onFileInput, analyze, store }
}
