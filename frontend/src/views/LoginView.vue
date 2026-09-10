<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AppIcon from '@/components/icons/AppIcon.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

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
  <div class="flex min-h-screen bg-base-200">
    <!-- Left: Branding -->
    <div class="relative hidden flex-1 items-center justify-center overflow-hidden lg:flex">
      <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-success/10 via-base-100 to-primary/5"></div>
      <div class="pointer-events-none absolute -right-40 -top-40 h-[600px] w-[600px] rounded-full bg-primary/8 blur-3xl"></div>
      <div class="pointer-events-none absolute -bottom-40 -left-40 h-[500px] w-[500px] rounded-full bg-success/8 blur-3xl"></div>

      <div class="relative z-10 max-w-md px-8 text-center">
        <AppIcon name="mountain" :size="48" class="mx-auto text-primary" />
        <h1 class="mt-6 text-4xl font-extrabold tracking-tight text-base-content">
          <span class="bg-gradient-to-r from-success to-primary bg-clip-text text-transparent">RiskTrail</span>
        </h1>
        <p class="mt-4 text-base leading-relaxed text-base-content/60">
          Conocé el riesgo de tus rutas antes de caminarlas. Análisis biomecánico en tiempo real.
        </p>
        <div class="mt-8 flex flex-wrap justify-center gap-4 text-sm text-base-content/50">
          <span class="flex items-center gap-2"><span class="h-1.5 w-1.5 rounded-full bg-primary"></span> MIDE dinámico</span>
          <span class="flex items-center gap-2"><span class="h-1.5 w-1.5 rounded-full bg-info"></span> Clima en vivo</span>
          <span class="flex items-center gap-2"><span class="h-1.5 w-1.5 rounded-full bg-secondary"></span> Ruta óptima</span>
        </div>
      </div>
    </div>

    <!-- Right: Form -->
    <div class="flex w-full items-center justify-center bg-base-100 px-6 py-12 sm:px-12 lg:w-[480px] lg:shrink-0">
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
          <h2 class="text-2xl font-extrabold tracking-tight text-base-content">Bienvenido de vuelta</h2>
          <p class="mt-2 text-sm text-base-content/50">Iniciá sesión para analizar tus rutas</p>
        </div>

        <form class="mt-8 space-y-4" @submit.prevent="handleSubmit">
          <BaseInput
            v-model="email"
            label="Email"
            type="email"
            placeholder="tu@email.com"
            required
          />

          <BaseInput
            v-model="password"
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            required
          />

          <div v-if="localError || auth.error" class="rounded-xl border border-error/30 bg-error/10 px-4 py-3 text-xs text-error">
            {{ localError || auth.error }}
          </div>

          <BaseButton type="submit" block :loading="auth.isLoading">
            <AppIcon name="arrow-right" :size="16" />
            {{ auth.isLoading ? 'Ingresando...' : 'Iniciar sesión' }}
          </BaseButton>
        </form>

        <p class="mt-8 text-center text-xs text-base-content/40">
          ¿No tenés cuenta?
          <RouterLink to="/register" class="font-semibold text-primary hover:underline">Registrate gratis</RouterLink>
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
