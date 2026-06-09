import { ref } from 'vue'

const currentTheme = ref<'jic-light' | 'jic-dark'>('jic-dark')

export function useTheme() {
  const toggleTheme = () => {
    currentTheme.value = currentTheme.value === 'jic-light' ? 'jic-dark' : 'jic-light'
    document.documentElement.setAttribute('data-theme', currentTheme.value)
    localStorage.setItem('theme', currentTheme.value)
  }

  const initTheme = () => {
    const saved = localStorage.getItem('theme') as 'jic-light' | 'jic-dark' | null
    if (saved) {
      currentTheme.value = saved
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      currentTheme.value = prefersDark ? 'jic-dark' : 'jic-light'
    }
    document.documentElement.setAttribute('data-theme', currentTheme.value)
  }

  return {
    currentTheme,
    toggleTheme,
    initTheme,
  }
}
