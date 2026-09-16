import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './authStore'

export interface UserProfile {
  id: string
  name: string
  weight_kg: number
  load_kg: number
  fitness_level: string
  surface_type: string
  is_default: boolean
  created_at: string
}

const API_BASE = '/api/v1'

export const useProfileStore = defineStore('profiles', () => {
  const profiles = ref<UserProfile[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const activeProfile = computed(() => profiles.value.find((p) => p.is_default) ?? profiles.value[0] ?? null)

  function headers(): Record<string, string> {
    const auth = useAuthStore()
    return auth.headers()
  }

  async function fetchProfiles(): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/profiles`, { headers: headers() })
      if (!res.ok) throw new Error('Error loading profiles')
      profiles.value = await res.json()
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  async function createProfile(data: {
    name: string
    weight_kg: number
    load_kg: number
    fitness_level: string
    surface_type?: string
  }): Promise<UserProfile | null> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/profiles`, {
        method: 'POST',
        headers: { ...headers(), 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const body = await res.json()
        throw new Error(body.detail || 'Error creating profile')
      }
      const profile = await res.json()
      profiles.value.unshift(profile)
      return profile
    } catch (e: any) {
      error.value = e.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function updateProfile(id: string, data: Partial<UserProfile>): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/profiles/${id}`, {
        method: 'PUT',
        headers: { ...headers(), 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Error updating profile')
      const updated = await res.json()
      const idx = profiles.value.findIndex((p) => p.id === id)
      if (idx !== -1) profiles.value[idx] = updated
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteProfile(id: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/profiles/${id}`, {
        method: 'DELETE',
        headers: headers(),
      })
      if (!res.ok) throw new Error('Error deleting profile')
      profiles.value = profiles.value.filter((p) => p.id !== id)
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function setDefault(id: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/profiles/${id}/default`, {
        method: 'PUT',
        headers: headers(),
      })
      if (!res.ok) throw new Error('Error setting default')
      const updated = await res.json()
      // Update all profiles: the selected one is default, others are not
      profiles.value = profiles.value.map((p) => ({
        ...p,
        is_default: p.id === id,
      }))
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    } finally {
      isLoading.value = false
    }
  }

  return {
    profiles,
    isLoading,
    error,
    activeProfile,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    setDefault,
  }
})
