import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './authStore'

export interface HistoryItem {
  id: string
  route_name: string | null
  route_id: string
  source_format: string | null
  is_favorite: boolean
  mide_global: number | null
  total_distance_km: number | null
  estimated_time_h: number | null
  total_kcal: number | null
  elevation_gain_m: number | null
  risk_max: number | null
  created_at: string
}

export interface HistoryDetail extends HistoryItem {
  profile_id: string | null
  analysis_json: string
}

const API_BASE = '/api/v1'

export const useHistoryStore = defineStore('history', () => {
  const items = ref<HistoryItem[]>([])
  const total = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  function headers(): Record<string, string> {
    const auth = useAuthStore()
    return auth.headers()
  }

  async function fetchHistory(opts?: { favorites_only?: boolean; search?: string }): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (opts?.favorites_only) params.set('favorites_only', 'true')
      if (opts?.search) params.set('search', opts.search)
      const qs = params.toString()
      const res = await fetch(`${API_BASE}/history${qs ? '?' + qs : ''}`, { headers: headers() })
      if (!res.ok) throw new Error('Error loading history')
      const data = await res.json()
      items.value = data.items
      total.value = data.total
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  async function saveAnalysis(data: {
    route_name?: string
    route_id: string
    source_format?: string
    profile_id?: string
    analysis_json: string
  }): Promise<HistoryItem | null> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/history`, {
        method: 'POST',
        headers: { ...headers(), 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Error saving analysis')
      const item = await res.json()
      items.value.unshift(item)
      total.value++
      return item
    } catch (e: any) {
      error.value = e.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function getDetail(id: string): Promise<HistoryDetail | null> {
    try {
      const res = await fetch(`${API_BASE}/history/${id}`, { headers: headers() })
      if (!res.ok) throw new Error('Error loading detail')
      return await res.json()
    } catch (e: any) {
      error.value = e.message
      return null
    }
  }

  async function deleteHistory(id: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/history/${id}`, {
        method: 'DELETE',
        headers: headers(),
      })
      if (!res.ok) throw new Error('Error deleting')
      items.value = items.value.filter((i) => i.id !== id)
      total.value--
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  async function toggleFavorite(id: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/history/${id}/favorite`, {
        method: 'PUT',
        headers: headers(),
      })
      if (!res.ok) throw new Error('Error toggling favorite')
      const updated = await res.json()
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx !== -1) items.value[idx].is_favorite = updated.is_favorite
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  return {
    items,
    total,
    isLoading,
    error,
    fetchHistory,
    saveAnalysis,
    getDetail,
    deleteHistory,
    toggleFavorite,
  }
})
