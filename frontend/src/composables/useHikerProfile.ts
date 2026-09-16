/**
 * useHikerProfile — composable managing hiker profile form state.
 * PRF-01 to PRF-05 with localStorage persistence.
 */

import { reactive, watch } from 'vue'

export type FitnessLevel = 'low' | 'medium' | 'high' | 'athlete'

export interface HikerProfile {
  name?: string
  weight_kg: number
  load_kg: number
  fitness_level: FitnessLevel
  surface_type: string  // Kept for backend compatibility but not shown in UI
}

const STORAGE_KEY = 'rt_hiker_profile'

function getInitialProfile(): HikerProfile {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        return {
          name: parsed.name ?? '',
          weight_kg: parsed.weight_kg ?? 70,
          load_kg: parsed.load_kg ?? 10,
          fitness_level: parsed.fitness_level ?? 'medium',
          surface_type: parsed.surface_type ?? 'dirt',
        }
      }
    } catch {}
  }
  return {
    name: '',
    weight_kg: 70,
    load_kg: 10,
    fitness_level: 'medium',
    surface_type: 'dirt',
  }
}

const sharedProfile = reactive<HikerProfile>(getInitialProfile())

if (typeof window !== 'undefined') {
  watch(
    sharedProfile,
    (val) => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
      } catch {}
    },
    { deep: true },
  )
}

export function useHikerProfile() {
  function isValid(): boolean {
    return (
      sharedProfile.weight_kg > 0 &&
      sharedProfile.load_kg >= 0 &&
      sharedProfile.load_kg < sharedProfile.weight_kg
    )
  }

  function setCalibration(data: Partial<HikerProfile>) {
    Object.assign(sharedProfile, data)
  }

  return { profile: sharedProfile, isValid, setCalibration }
}
