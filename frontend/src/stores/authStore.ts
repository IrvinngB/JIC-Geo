import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  email: string
  name: string
  created_at: string
}

const API_BASE = '/api/v1'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('rt_token'))
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('rt_token', newToken)
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('rt_token')
  }

  function headers(): Record<string, string> {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return
    try {
      const res = await fetch(`${API_BASE}/auth/me`, { headers: headers() })
      if (!res.ok) {
        clearAuth()
        return
      }
      user.value = await res.json()
    } catch {
      clearAuth()
    }
  }

  async function register(email: string, name: string, password: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, password }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Error al registrar')
      }
      const data = await res.json()
      setToken(data.access_token)
      // Fetch user in background — don't block or throw on failure
      fetchUser().catch(() => {})
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function login(email: string, password: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Credenciales inválidas')
      }
      const data = await res.json()
      setToken(data.access_token)
      // Fetch user in background — don't block or throw on failure
      fetchUser().catch(() => {})
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    clearAuth()
  }

  // Auto-fetch user on init if token exists
  if (token.value) {
    fetchUser()
  }

  return {
    token,
    user,
    isLoading,
    error,
    isAuthenticated,
    headers,
    fetchUser,
    register,
    login,
    logout,
  }
})
