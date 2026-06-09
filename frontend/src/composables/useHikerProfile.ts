/**
 * useHikerProfile — composable managing hiker profile form state.
 * PRF-01 to PRF-05.
 */

import { reactive } from 'vue'

export type FitnessLevel = 'low' | 'medium' | 'high' | 'athlete'

export interface HikerProfile {
  weight_kg: number
  load_kg: number
  fitness_level: FitnessLevel
}

export function useHikerProfile() {
  const profile = reactive<HikerProfile>({
    weight_kg: 70,
    load_kg: 10,
    fitness_level: 'medium',
  })

  function isValid(): boolean {
    return profile.weight_kg > 0 && profile.load_kg >= 0 && profile.load_kg < profile.weight_kg
  }

  return { profile, isValid }
}
