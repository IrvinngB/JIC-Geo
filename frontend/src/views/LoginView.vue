<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AppIcon from '@/components/icons/AppIcon.vue'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const localError = ref('')
const mounted = ref(false)

onMounted(() => {
  requestAnimationFrame(() => {
    mounted.value = true
  })
})

async function handleSubmit() {
  localError.value = ''
  if (!email.value.trim() || !password.value) {
    localError.value = 'Ingresá tu correo y contraseña.'
    return
  }

  try {
    await auth.login(email.value.trim(), password.value)
    router.push('/mapa')
  } catch (e: any) {
    localError.value = e.message || 'Error al iniciar sesión.'
  }
}

function handleFormKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    handleSubmit()
  }
}
</script>

<template>
  <div class="login-page">

    <!-- Crisp background with rich subtle gradient (no heavy blur artifacts) -->
    <div class="login-bg" aria-hidden="true">
      <div class="login-bg__pattern" />
    </div>

    <!-- Main card — Crisp Apple card -->
    <main
      class="login-card"
      :class="{ 'login-card--visible': mounted }"
    >
      <!-- Logo -->
      <div class="login-logo">
        <RouterLink to="/" class="login-logo__link" aria-label="Volver al inicio">
          <div class="login-logo__icon">
            <AppIcon name="footprints" :size="20" />
          </div>
          <span class="login-logo__text">RiskTrail</span>
        </RouterLink>
      </div>

      <!-- Heading -->
      <div class="login-heading">
        <h1 class="login-heading__title">Iniciar sesión</h1>
        <p class="login-heading__sub">Accedé a tus rutas y análisis biomecánico.</p>
      </div>

      <!-- Form -->
      <form
        class="login-form"
        autocomplete="on"
        @submit.prevent="handleSubmit"
        @keydown="handleFormKeydown"
      >
        <!-- Email -->
        <div class="login-field">
          <label for="login-email" class="login-field__label">Correo electrónico</label>
          <div class="login-input-wrap">
            <AppIcon name="mail" :size="18" class="login-input-wrap__icon" />
            <input
              id="login-email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="tu@email.com"
              class="login-input"
            />
          </div>
        </div>

        <!-- Password -->
        <div class="login-field">
          <label for="login-password" class="login-field__label">Contraseña</label>
          <div class="login-input-wrap">
            <AppIcon name="lock" :size="18" class="login-input-wrap__icon" />
            <input
              id="login-password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              autocomplete="current-password"
              placeholder="••••••••"
              class="login-input login-input--password"
            />
            <button
              type="button"
              class="login-input-wrap__toggle"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              @click="showPassword = !showPassword"
            >
              <AppIcon :name="showPassword ? 'eye-off' : 'eye'" :size="16" />
            </button>
          </div>
        </div>

        <!-- Error Alert -->
        <Transition name="error">
          <div
            v-if="localError || auth.error"
            class="login-error"
            role="alert"
          >
            <AppIcon name="alert-triangle" :size="16" class="shrink-0" />
            <span>{{ localError || auth.error }}</span>
          </div>
        </Transition>

        <!-- Submit Button -->
        <button
          type="submit"
          class="login-submit"
          :disabled="auth.isLoading"
        >
          <span v-if="auth.isLoading" class="login-spinner" />
          <template v-else>
            <span>Ingresar</span>
            <AppIcon name="arrow-right" :size="16" />
          </template>
        </button>
      </form>

      <!-- Footer links -->
      <div class="login-footer">
        <p>
          ¿No tenés cuenta?
          <RouterLink to="/register" class="login-footer__link">
            Registrate
          </RouterLink>
        </p>
        <RouterLink to="/" class="login-footer__back">
          &larr; Volver al inicio
        </RouterLink>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ── Page Layout ────────────────────────────────── */
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  overflow: hidden;
  background-color: #f4f4f5;
  background-image: 
    radial-gradient(at 50% 0%, rgba(16, 185, 129, 0.08) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.05) 0px, transparent 50%);
}

:global(html[data-theme="jic-dark"]) .login-page {
  background-color: #090d16;
  background-image: 
    radial-gradient(at 50% 0%, rgba(16, 185, 129, 0.12) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.08) 0px, transparent 50%);
}

/* ── Ambient Background Pattern ─────────────────── */
.login-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.login-bg__pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px);
  background-size: 24px 24px;
}

:global(html[data-theme="jic-dark"]) .login-bg__pattern {
  background-image: radial-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px);
}

/* ── Crisp Card ─────────────────────────────────── */
.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 410px;
  padding: 36px 32px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #e4e4e7;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.03),
    0 12px 32px -4px rgba(0, 0, 0, 0.08);

  /* Spring-like entrance */
  opacity: 0;
  transform: translateY(12px) scale(0.98);
  transition:
    opacity 350ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 350ms cubic-bezier(0.16, 1, 0.3, 1);
}

.login-card--visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

:global(html[data-theme="jic-dark"]) .login-card {
  background: #121824;
  border-color: #1e293b;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.3),
    0 16px 40px -4px rgba(0, 0, 0, 0.5);
}

/* ── Logo Header ────────────────────────────────── */
.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.login-logo__link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  transition: transform 100ms ease-out;
}

.login-logo__link:active {
  transform: scale(0.96);
}

.login-logo__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #059669;
  color: white;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.25);
}

:global(html[data-theme="jic-dark"]) .login-logo__icon {
  background: #10b981;
  color: #022c22;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
}

.login-logo__text {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #18181b;
}

:global(html[data-theme="jic-dark"]) .login-logo__text {
  color: #f4f4f5;
}

/* ── Heading ────────────────────────────────────── */
.login-heading {
  text-align: center;
  margin-bottom: 28px;
}

.login-heading__title {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #18181b;
  margin: 0;
}

.login-heading__sub {
  font-size: 13px;
  color: #71717a;
  margin: 6px 0 0;
  line-height: 1.4;
}

:global(html[data-theme="jic-dark"]) .login-heading__title {
  color: #f4f4f5;
}

:global(html[data-theme="jic-dark"]) .login-heading__sub {
  color: #9ca3af;
}

/* ── Form ───────────────────────────────────────── */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ── Field ──────────────────────────────────────── */
.login-field__label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #27272a;
  margin-bottom: 6px;
  letter-spacing: -0.01em;
}

:global(html[data-theme="jic-dark"]) .login-field__label {
  color: #e4e4e7;
}

/* ── Input Wrapper ──────────────────────────────── */
.login-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.login-input-wrap__icon {
  position: absolute;
  left: 14px;
  color: #9ca3af;
  pointer-events: none;
  transition: color 150ms ease;
  z-index: 1;
}

.login-input-wrap:focus-within .login-input-wrap__icon {
  color: #059669;
}

:global(html[data-theme="jic-dark"]) .login-input-wrap__icon {
  color: #6b7280;
}

:global(html[data-theme="jic-dark"]) .login-input-wrap:focus-within .login-input-wrap__icon {
  color: #10b981;
}

/* ── Input ──────────────────────────────────────── */
.login-input {
  width: 100%;
  height: 46px;
  padding: 0 14px 0 42px;
  border-radius: 12px;
  border: 1px solid #d4d4d8;
  background: #ffffff;
  font-size: 14px;
  font-family: inherit;
  color: #18181b;
  outline: none;
  transition:
    border-color 150ms ease,
    box-shadow 150ms ease;
}

.login-input--password {
  padding-right: 44px;
}

.login-input::placeholder {
  color: #a1a1aa;
}

.login-input:focus {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.12);
}

:global(html[data-theme="jic-dark"]) .login-input {
  border-color: #334155;
  background: #1e293b;
  color: #f4f4f5;
}

:global(html[data-theme="jic-dark"]) .login-input::placeholder {
  color: #64748b;
}

:global(html[data-theme="jic-dark"]) .login-input:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

/* ── Password Toggle ────────────────────────────── */
.login-input-wrap__toggle {
  position: absolute;
  right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #71717a;
  cursor: pointer;
  transition: transform 100ms ease-out, color 150ms ease, background 150ms ease;
}

.login-input-wrap__toggle:hover {
  color: #18181b;
  background: rgba(0, 0, 0, 0.05);
}

.login-input-wrap__toggle:active {
  transform: scale(0.9);
}

:global(html[data-theme="jic-dark"]) .login-input-wrap__toggle {
  color: #9ca3af;
}

:global(html[data-theme="jic-dark"]) .login-input-wrap__toggle:hover {
  color: #f4f4f5;
  background: rgba(255, 255, 255, 0.08);
}

/* ── Error ──────────────────────────────────────── */
.login-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  font-size: 13px;
  font-weight: 500;
}

:global(html[data-theme="jic-dark"]) .login-error {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.error-enter-active, .error-leave-active {
  transition: opacity 150ms ease, transform 150ms ease;
}

.error-enter-from, .error-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── Submit Button ──────────────────────────────── */
.login-submit {
  position: relative;
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-radius: 12px;
  background: #059669;
  color: white;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  letter-spacing: -0.01em;
  cursor: pointer;
  margin-top: 4px;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.25);
  transition: transform 100ms ease-out, background 150ms ease, box-shadow 150ms ease;
}

.login-submit:hover:not(:disabled) {
  background: #047857;
  box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
}

.login-submit:active:not(:disabled) {
  transform: scale(0.97);
  box-shadow: 0 1px 4px rgba(5, 150, 105, 0.2);
}

.login-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

:global(html[data-theme="jic-dark"]) .login-submit {
  background: #10b981;
  color: #022c22;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
}

:global(html[data-theme="jic-dark"]) .login-submit:hover:not(:disabled) {
  background: #34d399;
}

/* ── Loading Spinner ────────────────────────────── */
.login-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 600ms linear infinite;
}

:global(html[data-theme="jic-dark"]) .login-spinner {
  border-color: rgba(0, 0, 0, 0.2);
  border-top-color: #022c22;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Footer ─────────────────────────────────────── */
.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: #71717a;
  line-height: 1.6;
}

:global(html[data-theme="jic-dark"]) .login-footer {
  color: #9ca3af;
}

.login-footer__link {
  color: #059669;
  font-weight: 700;
  text-decoration: none;
  margin-left: 4px;
}

.login-footer__link:hover {
  text-decoration: underline;
}

:global(html[data-theme="jic-dark"]) .login-footer__link {
  color: #10b981;
}

.login-footer__back {
  display: inline-block;
  margin-top: 8px;
  color: #9ca3af;
  text-decoration: none;
  font-size: 12px;
  transition: color 150ms ease, transform 100ms ease-out;
}

.login-footer__back:hover {
  color: #52525b;
}

.login-footer__back:active {
  transform: scale(0.96);
}

:global(html[data-theme="jic-dark"]) .login-footer__back {
  color: #64748b;
}

:global(html[data-theme="jic-dark"]) .login-footer__back:hover {
  color: #94a3b8;
}
</style>

<style>
html[data-theme="jic-dark"] .login-page { background: #0b0f19 !important; }
html[data-theme="jic-dark"] .login-card { background: rgba(24,24,27,0.75) !important; border-color: rgba(255,255,255,0.08) !important; box-shadow: 0 0 0 1px rgba(255,255,255,0.03), 0 4px 24px rgba(0,0,0,0.3), 0 24px 64px rgba(0,0,0,0.2) !important; }
html[data-theme="jic-dark"] .login-logo__text { color: #fafafa !important; }
html[data-theme="jic-dark"] .login-heading__title { color: #fafafa !important; }
html[data-theme="jic-dark"] .login-heading__sub { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .login-field__label { color: #d4d4d8 !important; }
html[data-theme="jic-dark"] .login-input-wrap__icon { color: #52525b !important; }
html[data-theme="jic-dark"] .login-input-wrap:focus-within .login-input-wrap__icon { color: #34d399 !important; }
html[data-theme="jic-dark"] .login-input { border-color: #27272a !important; background: rgba(39,39,42,0.6) !important; color: #fafafa !important; }
html[data-theme="jic-dark"] .login-input::placeholder { color: #52525b !important; }
html[data-theme="jic-dark"] .login-input:focus { border-color: #34d399 !important; box-shadow: 0 0 0 3px rgba(52,211,153,0.15) !important; background: rgba(39,39,42,0.8) !important; }
html[data-theme="jic-dark"] .login-input:active { background: rgba(39,39,42,0.9) !important; }
html[data-theme="jic-dark"] .login-input-wrap__toggle { color: #71717a !important; }
html[data-theme="jic-dark"] .login-input-wrap__toggle:hover { color: #d4d4d8 !important; background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .login-error { background: rgba(239,68,68,0.1) !important; border-color: rgba(239,68,68,0.25) !important; color: #f87171 !important; }
html[data-theme="jic-dark"] .login-submit { background: linear-gradient(135deg,#34d399,#10b981) !important; color: #022c22 !important; }
html[data-theme="jic-dark"] .login-submit:disabled { opacity: 0.5 !important; }
html[data-theme="jic-dark"] .login-spinner { border-color: rgba(0,0,0,0.2) !important; border-top-color: #022c22 !important; }
html[data-theme="jic-dark"] .login-footer__link { color: #34d399 !important; }
html[data-theme="jic-dark"] .login-footer__back { color: #52525b !important; }
html[data-theme="jic-dark"] .login-footer__back:hover { color: #a1a1aa !important; }
</style>
