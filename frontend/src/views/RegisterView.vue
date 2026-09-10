<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AppIcon from '@/components/icons/AppIcon.vue'

const auth = useAuthStore()
const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const localError = ref('')

async function handleSubmit() {
  localError.value = ''

  if (password.value !== confirmPassword.value) {
    localError.value = 'Las contraseñas no coinciden'
    return
  }

  if (password.value.length < 6) {
    localError.value = 'La contraseña debe tener al menos 6 caracteres'
    return
  }

  try {
    await auth.register(email.value, name.value, password.value)
    router.push('/mapa')
  } catch (e: any) {
    localError.value = e.message
  }
}
</script>

<template>
  <div class="flex min-h-screen bg-base-100">
    <!-- Left: Branding -->
    <div class="relative hidden flex-1 items-center justify-center overflow-hidden lg:flex">
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-success/10 via-base-100 to-primary/5"></div>
      <div class="pointer-events-none absolute -right-40 -top-40 h-[600px] w-[600px] rounded-full bg-primary/8 blur-3xl"></div>
      <div class="pointer-events-none absolute -bottom-40 -left-40 h-[500px] w-[500px] rounded-full bg-success/8 blur-3xl"></div>

      <div class="relative z-10 max-w-md px-8 text-center">
        <AppIcon name="mountain" :size="48" class="mx-auto text-primary" />
        <h1 class="mt-6 text-4xl font-extrabold tracking-tight">
          <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-transparent">RiskTrail</span>
        </h1>
        <p class="mt-4 text-base leading-relaxed text-base-content/60">
          Uní tu perfil, guardá tus análisis y conocé el riesgo de cada tramo con ciencia real.
        </p>
        <div class="mt-8 space-y-3 text-left">
          <div class="flex items-center gap-3 text-sm text-base-content/60">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-success/10 text-success">
              <AppIcon name="shield" :size="14" />
            </div>
            Perfil personalizado con tu peso, carga y condición física
          </div>
          <div class="flex items-center gap-3 text-sm text-base-content/60">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <AppIcon name="route" :size="14" />
            </div>
            Historial de rutas analizadas con comparación lado a lado
          </div>
          <div class="flex items-center gap-3 text-sm text-base-content/60">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-info/10 text-info">
              <AppIcon name="compass" :size="14" />
            </div>
            Alertas de tramo peligroso con tu ubicación GPS
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Form -->
    <div class="flex w-full items-center justify-center px-6 py-12 sm:px-12 lg:w-[480px] lg:shrink-0">
      <div class="w-full max-w-sm">
        <!-- Mobile header -->
        <div class="mb-8 text-center lg:hidden">
          <RouterLink to="/" class="inline-flex items-center gap-2">
            <AppIcon name="mountain" :size="24" class="text-primary" />
            <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-xl font-extrabold text-transparent">
              RiskTrail
            </span>
          </RouterLink>
        </div>

        <div>
          <h2 class="text-2xl font-extrabold tracking-tight">Creá tu cuenta</h2>
          <p class="mt-2 text-sm text-base-content/50">Empezá a analizar tus rutas en segundos</p>
        </div>

        <form class="mt-8 space-y-4" @submit.prevent="handleSubmit">
          <label class="form-control">
            <span class="label-text text-xs font-medium text-base-content/70">Nombre</span>
            <input
              v-model="name"
              type="text"
              placeholder="Tu nombre"
              class="input input-bordered input-sm w-full sm:input-md"
              required
            />
          </label>

          <label class="form-control">
            <span class="label-text text-xs font-medium text-base-content/70">Email</span>
            <input
              v-model="email"
              type="email"
              placeholder="tu@email.com"
              class="input input-bordered input-sm w-full sm:input-md"
              required
            />
          </label>

          <label class="form-control">
            <span class="label-text text-xs font-medium text-base-content/70">Contraseña</span>
            <input
              v-model="password"
              type="password"
              placeholder="Mínimo 6 caracteres"
              class="input input-bordered input-sm w-full sm:input-md"
              minlength="6"
              required
            />
          </label>

          <label class="form-control">
            <span class="label-text text-xs font-medium text-base-content/70">Confirmar contraseña</span>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="Repetí la contraseña"
              class="input input-bordered input-sm w-full sm:input-md"
              required
            />
          </label>

          <div v-if="localError || auth.error" class="rounded-xl border border-error/30 bg-error/10 px-4 py-3 text-xs text-error">
            {{ localError || auth.error }}
          </div>

          <button
            type="submit"
            class="btn btn-primary w-full gap-2 text-white"
            :class="{ 'btn-disabled': auth.isLoading }"
            :disabled="auth.isLoading"
          >
            <span v-if="auth.isLoading" class="loading loading-spinner loading-sm" />
            <AppIcon v-else name="arrow-right" :size="16" />
            {{ auth.isLoading ? 'Creando cuenta...' : 'Crear cuenta' }}
          </button>
        </form>

        <p class="mt-8 text-center text-xs text-base-content/40">
          ¿Ya tenés cuenta?
          <RouterLink to="/login" class="font-semibold text-primary hover:underline">Iniciá sesión</RouterLink>
        </p>

        <p class="mt-4 text-center">
          <RouterLink to="/" class="text-xs text-base-content/30 hover:text-base-content/50">
            ← Volver al inicio
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
