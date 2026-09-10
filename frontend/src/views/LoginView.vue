<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AppIcon from '@/components/icons/AppIcon.vue'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const localError = ref('')

async function handleSubmit() {
  localError.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/mapa')
  } catch (e: any) {
    localError.value = e.message
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-base-200 px-4">
    <div class="w-full max-w-sm">
      <!-- Header -->
      <div class="mb-8 text-center">
        <RouterLink to="/" class="inline-flex items-center gap-2">
          <AppIcon name="mountain" :size="28" class="text-primary" />
          <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-2xl font-extrabold text-transparent">
            RiskTrail
          </span>
        </RouterLink>
        <p class="mt-2 text-sm text-base-content/60">Iniciá sesión para continuar</p>
      </div>

      <!-- Form -->
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <label class="form-control">
          <span class="label-text text-xs font-medium">Email</span>
          <input
            v-model="email"
            type="email"
            placeholder="tu@email.com"
            class="input input-bordered w-full"
            required
          />
        </label>

        <label class="form-control">
          <span class="label-text text-xs font-medium">Contraseña</span>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            class="input input-bordered w-full"
            required
          />
        </label>

        <div v-if="localError || auth.error" class="alert alert-error text-xs">
          <span>{{ localError || auth.error }}</span>
        </div>

        <button
          type="submit"
          class="btn btn-primary w-full text-white"
          :class="{ 'btn-disabled': auth.isLoading }"
          :disabled="auth.isLoading"
        >
          <span v-if="auth.isLoading" class="loading loading-spinner loading-sm" />
          {{ auth.isLoading ? 'Ingresando...' : 'Iniciar sesión' }}
        </button>
      </form>

      <p class="mt-6 text-center text-xs text-base-content/50">
        ¿No tenés cuenta?
        <RouterLink to="/register" class="link link-primary">Registrate</RouterLink>
      </p>
    </div>
  </div>
</template>
