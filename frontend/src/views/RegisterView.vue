<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useHikerProfile, type FitnessLevel } from '@/composables/useHikerProfile'
import AppIcon from '@/components/icons/AppIcon.vue'

const auth = useAuthStore()
const router = useRouter()
const { setCalibration } = useHikerProfile()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const acceptTerms = ref(true)

const weightKg = ref(72)
const fitnessLevel = ref<FitnessLevel>('medium')

const localError = ref('')
const mounted = ref(false)
const showTerms = ref(false)

onMounted(() => {
  requestAnimationFrame(() => { mounted.value = true })
})

// ── Computeds ─────────────────────────────────────

const passwordStrength = computed(() => {
  const p = password.value
  if (!p) return 0
  let score = 0
  if (p.length >= 6) score += 1
  if (p.length >= 8) score += 1
  if (/[A-Z]/.test(p) || /[0-9]/.test(p)) score += 1
  if (/[^A-Za-z0-9]/.test(p) && p.length >= 8) score += 1
  return Math.min(3, score)
})

const passwordStrengthLabel = computed(() => {
  if (!password.value) return ''
  if (passwordStrength.value <= 1) return 'Básica'
  if (passwordStrength.value === 2) return 'Aceptable'
  return 'Segura'
})

const fitnessLevelLabel = computed(() => {
  switch (fitnessLevel.value) {
    case 'low': return 'Principiante'
    case 'medium': return 'Intermedio'
    case 'high': return 'Avanzado'
    case 'athlete': return 'Atleta'
    default: return 'Intermedio'
  }
})

const profileInitial = computed(() => {
  if (!name.value.trim()) return 'S'
  const parts = name.value.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.value.trim().slice(0, 2).toUpperCase()
})

// ── Submit ────────────────────────────────────────

async function handleSubmit() {
  localError.value = ''

  if (!acceptTerms.value) {
    localError.value = 'Debes aceptar los términos para continuar.'
    return
  }
  if (password.value !== confirmPassword.value) {
    localError.value = 'Las contraseñas no coinciden.'
    return
  }
  if (password.value.length < 6) {
    localError.value = 'La contraseña debe tener al menos 6 caracteres.'
    return
  }

  try {
    setCalibration({
      name: name.value.trim() || undefined,
      weight_kg: Number(weightKg.value) || 70,
      fitness_level: fitnessLevel.value,
    })
    await auth.register(email.value, name.value, password.value)
    router.push('/mapa')
  } catch (e: any) {
    localError.value = e.message
  }
}
</script>

<template>
  <div class="register-page">

    <!-- Ambient background -->
    <div class="register-bg" aria-hidden="true">
      <div class="register-bg__orb register-bg__orb--top" />
      <div class="register-bg__orb register-bg__orb--bottom" />
    </div>

    <!-- Main card -->
    <main class="register-card" :class="{ 'register-card--visible': mounted }">

      <!-- Logo -->
      <div class="register-logo">
        <RouterLink to="/" class="register-logo__link" aria-label="Volver al inicio">
          <div class="register-logo__icon">
            <AppIcon name="footprints" :size="22" />
          </div>
          <span class="register-logo__text">RiskTrail</span>
        </RouterLink>
      </div>

      <!-- Heading -->
      <div class="register-heading">
        <h1 class="register-heading__title">Crear cuenta</h1>
        <p class="register-heading__sub">Configura tu perfil y empezá a analizar rutas.</p>
      </div>

      <!-- Form -->
      <form class="register-form" @submit.prevent="handleSubmit">

        <!-- Name -->
        <div class="register-field">
          <label for="reg-name" class="register-field__label">Nombre completo</label>
          <div class="register-input-wrap">
            <AppIcon name="user" :size="18" class="register-input-wrap__icon" />
            <input
              id="reg-name"
              v-model="name"
              type="text"
              required
              placeholder="Tu nombre"
              class="register-input"
            />
          </div>
        </div>

        <!-- Email -->
        <div class="register-field">
          <label for="reg-email" class="register-field__label">Correo electrónico</label>
          <div class="register-input-wrap">
            <AppIcon name="mail" :size="18" class="register-input-wrap__icon" />
            <input
              id="reg-email"
              v-model="email"
              type="email"
              required
              placeholder="tu@email.com"
              autocomplete="email"
              class="register-input"
            />
          </div>
        </div>

        <!-- Password -->
        <div class="register-field">
          <div class="register-field__row">
            <label for="reg-password" class="register-field__label">Contraseña</label>
            <span v-if="password" class="register-strength-label" :class="passwordStrength >= 2 ? 'register-strength-label--ok' : 'register-strength-label--weak'">
              {{ passwordStrengthLabel }}
            </span>
          </div>
          <div class="register-input-wrap">
            <AppIcon name="lock" :size="18" class="register-input-wrap__icon" />
            <input
              id="reg-password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="Mínimo 6 caracteres"
              autocomplete="new-password"
              class="register-input register-input--password"
            />
            <button
              type="button"
              class="register-input-wrap__toggle"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              @click="showPassword = !showPassword"
            >
              <AppIcon :name="showPassword ? 'eye-off' : 'eye'" :size="16" />
            </button>
          </div>
          <!-- Strength bars -->
          <div class="register-bars">
            <div class="register-bar" :class="passwordStrength >= 1 ? 'register-bar--1' : ''" />
            <div class="register-bar" :class="passwordStrength >= 2 ? 'register-bar--2' : ''" />
            <div class="register-bar" :class="passwordStrength >= 3 ? 'register-bar--3' : ''" />
          </div>
        </div>

        <!-- Confirm password -->
        <div class="register-field">
          <label for="reg-confirm" class="register-field__label">Confirmar contraseña</label>
          <div class="register-input-wrap">
            <AppIcon name="lock" :size="18" class="register-input-wrap__icon" />
            <input
              id="reg-confirm"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="Repite tu contraseña"
              autocomplete="new-password"
              class="register-input"
            />
          </div>
        </div>

        <!-- ── Calibration section (collapsible) ──── -->
        <details class="register-cal">
          <summary class="register-cal__summary">
            <div class="register-cal__icon">
              <AppIcon name="footprints" :size="15" />
            </div>
            <span class="register-cal__title">Calibración biomecánica</span>
            <span class="register-cal__hint">Opcional</span>
            <AppIcon name="chevron-down" :size="16" class="register-cal__chevron" />
          </summary>
          <div class="register-cal__body">
            <p class="register-cal__text">
              Ajustá tu perfil para que las estimaciones de fatiga y calorías se sincronicen desde tu primer sendero.
            </p>
            <div class="register-cal__fields">
              <div class="register-field">
                <label for="reg-weight" class="register-field__label">Peso (kg)</label>
                <div class="register-input-wrap register-input-wrap--short">
                  <input
                    id="reg-weight"
                    v-model.number="weightKg"
                    type="number"
                    min="35"
                    max="200"
                    required
                    class="register-input register-input--short"
                  />
                  <span class="register-input-wrap__unit">kg</span>
                </div>
              </div>
              <div class="register-field">
                <label for="reg-fitness" class="register-field__label">Nivel</label>
                <select
                  id="reg-fitness"
                  v-model="fitnessLevel"
                  class="register-select"
                >
                  <option value="low">Principiante</option>
                  <option value="medium">Intermedio</option>
                  <option value="high">Avanzado</option>
                  <option value="athlete">Atleta</option>
                </select>
              </div>
            </div>
          </div>
        </details>

        <!-- Live profile preview -->
        <div class="register-preview">
          <div class="register-preview__top">
            <div class="register-preview__avatar">{{ profileInitial }}</div>
            <div>
              <div class="register-preview__name">{{ name.trim() || 'Senderista' }}</div>
              <div class="register-preview__meta">{{ fitnessLevelLabel }} · {{ weightKg }} kg</div>
            </div>
          </div>
        </div>

        <!-- Terms -->
        <label class="register-terms">
          <input
            v-model="acceptTerms"
            type="checkbox"
            class="register-terms__check"
          />
          <span class="register-terms__text">
            Acepto los
            <button type="button" class="register-terms__link" @click.prevent="showTerms = true">Términos de Servicio</button>
            y entiendo que los cálculos son herramientas de estimación para seguridad en montaña.
          </span>
        </label>

        <!-- Error -->
        <Transition name="error">
          <div v-if="localError || auth.error" class="register-error" role="alert">
            <AppIcon name="alert-triangle" :size="14" />
            <span>{{ localError || auth.error }}</span>
          </div>
        </Transition>

        <!-- Submit -->
        <button type="submit" class="register-submit" :disabled="auth.isLoading">
          <span v-if="auth.isLoading" class="register-spinner" />
          <template v-else>
            <span>Crear cuenta</span>
            <AppIcon name="arrow-right" :size="16" />
          </template>
        </button>
      </form>

      <!-- Footer links -->
      <div class="register-footer">
        <p>
          ¿Ya tenés cuenta?
          <RouterLink to="/login" class="register-footer__link">Iniciar sesión</RouterLink>
        </p>
        <RouterLink to="/" class="register-footer__back">← Volver al inicio</RouterLink>
      </div>
    </main>

    <!-- ═══════════════════════════════════════════════
         TERMS MODAL
         ═══════════════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showTerms" class="modal-overlay" @click.self="showTerms = false">
          <div class="modal-card">
            <div class="modal-header">
              <h2 class="modal-title">Términos de Servicio</h2>
              <button class="modal-close" aria-label="Cerrar" @click="showTerms = false">
                <AppIcon name="x" :size="18" />
              </button>
            </div>
            <div class="modal-body">
              <div class="modal-section">
                <h3>1. Uso de la plataforma</h3>
                <p>RiskTrail es una herramienta de estimación biomecánica para senderismo. Los cálculos de fatiga, calorías, severidad MIDE y costo metabólico Minetti son aproximaciones basadas en modelos científicos y no sustituyen el juicio profesional de un guía montañero certificado.</p>
              </div>
              <div class="modal-section">
                <h3>2. Datos personales</h3>
                <p>Tu peso, nivel de fitness y datos de rutas se almacenan localmente en tu navegador (localStorage). No se envían a servidores externos ni se comparten con terceros. El correo electrónico se utiliza exclusivamente para autenticación.</p>
              </div>
              <div class="modal-section">
                <h3>3. Limitación de responsabilidad</h3>
                <p>Los resultados proporcionados por RiskTrail son orientativos. El usuario es responsable de evaluar sus propias capacidades y las condiciones del terreno. RiskTrail no se responsabiliza por accidentes derivados del uso de la información presentada.</p>
              </div>
              <div class="modal-section">
                <h3>4. Modelos científicos</h3>
                <p>El índice MIDE sigue la Norma Técnica de la FEDME. El modelo de gasto metabólico se basa en Minetti et al. (2002). La corrección GPS utiliza filtros Savitzky-Golay. Estos modelos tienen limitaciones conocidas y no cubren todas las variables posibles.</p>
              </div>
              <div class="modal-section">
                <h3>5. Modificaciones</h3>
                <p>RiskTrail se distribuye bajo licencia MIT. Los términos pueden actualizarse sin previo aviso. El uso continuado de la plataforma implica la aceptación de los términos vigentes.</p>
              </div>
            </div>
            <div class="modal-footer">
              <button class="modal-accept" @click="acceptTerms = true; showTerms = false">
                Aceptar y continuar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════
   APPLE DESIGN — Register Page
   ═══════════════════════════════════════════════════ */

/* ── Page ───────────────────────────────────────── */
.register-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  overflow: hidden;
  background: #fafafa;
}

.register-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
.register-bg__orb { position: absolute; border-radius: 9999px; filter: blur(100px); }

.register-bg__orb--top {
  top: -15%; left: 50%; transform: translateX(-50%);
  width: 600px; height: 350px;
  background: radial-gradient(circle, rgba(16,185,129,0.12) 0%, transparent 70%);
  opacity: 0; animation: orb-fade-in 1.2s ease-out 0.2s forwards;
}

.register-bg__orb--bottom {
  bottom: -10%; right: -10%;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%);
  opacity: 0; animation: orb-fade-in 1.2s ease-out 0.5s forwards;
}

@keyframes orb-fade-in { to { opacity: 1; } }

/* ── Card ───────────────────────────────────────── */
.register-card {
  position: relative; z-index: 10;
  width: 100%; max-width: 440px;
  padding: 40px 32px;
  border-radius: 24px;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.02), 0 4px 24px rgba(0,0,0,0.06), 0 24px 64px rgba(0,0,0,0.04);
  opacity: 0; transform: translateY(24px) scale(0.98);
  transition: opacity 0.5s cubic-bezier(0.2,0.8,0.2,1), transform 0.5s cubic-bezier(0.2,0.8,0.2,1);
}

.register-card--visible { opacity: 1; transform: translateY(0) scale(1); }

/* ── Logo ───────────────────────────────────────── */
.register-logo { margin-bottom: 28px; }

.register-logo__link {
  display: inline-flex; align-items: center; gap: 10px; text-decoration: none;
  transition: transform 100ms ease-out;
}
.register-logo__link:active { transform: scale(0.96); }

.register-logo__icon {
  display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: 12px;
  background: linear-gradient(135deg, #059669, #047857);
  color: white; box-shadow: 0 2px 8px rgba(5,150,105,0.3);
}

.register-logo__text {
  font-size: 20px; font-weight: 800; letter-spacing: -0.03em; color: #18181b;
}

/* ── Heading ────────────────────────────────────── */
.register-heading { margin-bottom: 28px; }

.register-heading__title {
  font-size: 26px; font-weight: 800; letter-spacing: -0.035em;
  color: #18181b; margin: 0; line-height: 1.2;
}

.register-heading__sub {
  font-size: 14px; color: #71717a; margin: 6px 0 0; line-height: 1.4;
}

/* ── Form ───────────────────────────────────────── */
.register-form { display: flex; flex-direction: column; gap: 18px; }

/* ── Field ──────────────────────────────────────── */
.register-field__label {
  display: block; font-size: 13px; font-weight: 600;
  color: #3f3f46; margin-bottom: 6px; letter-spacing: -0.01em;
}

.register-field__row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}

.register-strength-label {
  font-size: 11px; font-weight: 700;
}
.register-strength-label--ok { color: #059669; }
.register-strength-label--weak { color: #d97706; }

/* ── Input ──────────────────────────────────────── */
.register-input-wrap {
  position: relative; display: flex; align-items: center;
}

.register-input-wrap__icon {
  position: absolute; left: 14px; color: #a1a1aa;
  pointer-events: none; transition: color 150ms ease; z-index: 1;
}

.register-input-wrap:focus-within .register-input-wrap__icon { color: #059669; }

.register-input-wrap__toggle {
  position: absolute; right: 12px;
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border: none; border-radius: 8px;
  background: transparent; color: #71717a; cursor: pointer;
  transition: transform 100ms ease-out, color 150ms ease, background 150ms ease;
}
.register-input-wrap__toggle:hover { color: #3f3f46; background: rgba(0,0,0,0.04); }
.register-input-wrap__toggle:active { transform: scale(0.88); }

.register-input-wrap__unit {
  position: absolute; right: 14px; font-size: 13px;
  font-weight: 600; color: #a1a1aa; pointer-events: none;
}

.register-input {
  width: 100%; height: 48px; padding: 0 14px 0 42px;
  border-radius: 14px; border: 1.5px solid #e4e4e7;
  background: rgba(255,255,255,0.6); font-size: 15px;
  font-family: inherit; color: #18181b; outline: none;
  transition: border-color 150ms ease, box-shadow 150ms ease, background 150ms ease;
}

.register-input--password { padding-right: 44px; }

.register-input--short { padding-right: 36px; }

.register-input::placeholder { color: #a1a1aa; }
.register-input:focus { border-color: #059669; box-shadow: 0 0 0 3px rgba(5,150,105,0.12); background: rgba(255,255,255,0.9); }
.register-input:active { background: #fafafa; }

/* ── Select ─────────────────────────────────────── */
.register-select {
  width: 100%; height: 48px; padding: 0 14px;
  border-radius: 14px; border: 1.5px solid #e4e4e7;
  background: rgba(255,255,255,0.6); font-size: 15px;
  font-family: inherit; color: #18181b; outline: none; cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.register-select:focus { border-color: #059669; box-shadow: 0 0 0 3px rgba(5,150,105,0.12); }

/* ── Strength bars ──────────────────────────────── */
.register-bars { display: flex; gap: 4px; margin-top: 8px; }

.register-bar {
  flex: 1; height: 3px; border-radius: 2px;
  background: #e4e4e7; transition: background 200ms ease;
}
.register-bar--1 { background: #d97706; }
.register-bar--2 { background: #059669; }
.register-bar--3 { background: #047857; }

/* ── Calibration (collapsible details) ───────────── */
.register-cal {
  border-radius: 16px;
  background: rgba(5,150,105,0.04);
  border: 1px solid rgba(5,150,105,0.12);
  overflow: hidden;
}

.register-cal[open] {
  background: rgba(5,150,105,0.04);
}

.register-cal__summary {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 16px;
  cursor: pointer;
  list-style: none;
  user-select: none;
  transition: background 150ms ease;
}

.register-cal__summary::-webkit-details-marker { display: none; }
.register-cal__summary::marker { display: none; content: ''; }

.register-cal__summary:hover { background: rgba(5,150,105,0.06); }

.register-cal__icon {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 8px;
  background: rgba(5,150,105,0.1); color: #059669;
  flex-shrink: 0;
}

.register-cal__title {
  font-size: 13px; font-weight: 700; color: #059669;
  flex: 1;
}

.register-cal__hint {
  font-size: 10px; font-weight: 600; color: #a1a1aa;
  text-transform: uppercase; letter-spacing: 0.05em;
}

.register-cal__chevron {
  color: #059669;
  transition: transform 200ms ease;
}

.register-cal[open] .register-cal__chevron {
  transform: rotate(180deg);
}

.register-cal__body {
  padding: 0 16px 16px;
}

.register-cal__text {
  font-size: 12px; line-height: 1.5; color: #71717a; margin: 0 0 14px;
}

.register-cal__fields {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
}

/* ── Profile preview ────────────────────────────── */
.register-preview {
  padding: 14px 16px; border-radius: 14px;
  background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.04);
}

.register-preview__top {
  display: flex; align-items: center; gap: 12px;
}

.register-preview__avatar {
  width: 40px; height: 40px; border-radius: 10px;
  background: linear-gradient(135deg, #059669, #047857);
  color: white; font-size: 14px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.register-preview__name {
  font-size: 14px; font-weight: 700; color: #18181b;
}

.register-preview__meta {
  font-size: 12px; color: #a1a1aa; margin-top: 1px;
}

/* ── Terms ──────────────────────────────────────── */
.register-terms {
  display: flex; align-items: flex-start; gap: 10px;
  cursor: pointer; font-size: 12px; color: #71717a; line-height: 1.5;
}

.register-terms__check {
  width: 16px; height: 16px; margin-top: 1px;
  accent-color: #059669; flex-shrink: 0; cursor: pointer;
}

.register-terms__link {
  color: #059669; font-weight: 700; text-decoration: underline;
  text-decoration-style: dotted; text-underline-offset: 2px;
  background: none; border: none; padding: 0; cursor: pointer;
  font-size: inherit; font-family: inherit;
  transition: color 150ms ease;
}
.register-terms__link:hover { color: #047857; }

/* ── Error ──────────────────────────────────────── */
.register-error {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 14px; border-radius: 12px;
  background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
  color: #dc2626; font-size: 13px; font-weight: 500;
}

.error-enter-active { transition: opacity 200ms ease-out, transform 200ms cubic-bezier(0.2,0.8,0.2,1); }
.error-leave-active { transition: opacity 150ms ease-in, transform 150ms ease-in; }
.error-enter-from { opacity: 0; transform: translateY(-8px); }
.error-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Submit ─────────────────────────────────────── */
.register-submit {
  position: relative; width: 100%; height: 48px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  border: none; border-radius: 14px;
  background: linear-gradient(135deg, #059669, #047857);
  color: white; font-size: 15px; font-weight: 700;
  font-family: inherit; letter-spacing: -0.01em;
  cursor: pointer; margin-top: 4px;
  box-shadow: 0 2px 12px rgba(5,150,105,0.3);
  transition: transform 100ms ease-out, box-shadow 200ms ease, opacity 200ms ease;
  overflow: hidden;
}

.register-submit:active:not(:disabled) { transform: scale(0.97); box-shadow: 0 1px 4px rgba(5,150,105,0.2); }
.register-submit:hover:not(:disabled) { box-shadow: 0 4px 20px rgba(5,150,105,0.4); }
.register-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.register-spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
  border-radius: 50%; animation: spin 600ms linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Footer ─────────────────────────────────────── */
.register-footer {
  margin-top: 24px; text-align: center; font-size: 13px;
  color: #71717a; line-height: 1.6;
}

.register-footer__link {
  color: #059669; font-weight: 700; text-decoration: none;
  transition: transform 100ms ease-out; display: inline-block;
}
.register-footer__link:active { transform: scale(0.96); }
.register-footer__link:hover { text-decoration: underline; }

.register-footer__back {
  display: block; margin-top: 8px; color: #a1a1aa;
  text-decoration: none; font-size: 12px;
  transition: transform 100ms ease-out, color 150ms ease;
}
.register-footer__back:active { transform: scale(0.97); }
.register-footer__back:hover { color: #71717a; }

/* ── Modal ──────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.modal-card {
  width: 100%; max-width: 520px; max-height: 80vh;
  display: flex; flex-direction: column;
  border-radius: 20px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 24px 64px rgba(0,0,0,0.2);
  overflow: hidden;
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 1px solid rgba(0,0,0,0.06);
  flex-shrink: 0;
}

.modal-title {
  font-size: 17px; font-weight: 800; letter-spacing: -0.02em;
  color: #18181b; margin: 0;
}

.modal-close {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border: none; border-radius: 8px;
  background: transparent; color: #71717a; cursor: pointer;
  transition: transform 100ms ease-out, background 150ms ease;
}
.modal-close:hover { background: rgba(0,0,0,0.04); }
.modal-close:active { transform: scale(0.88); }

.modal-body {
  padding: 20px 24px; overflow-y: auto; flex: 1;
  font-size: 13px; line-height: 1.6; color: #52525b;
}

.modal-section { margin-bottom: 18px; }
.modal-section:last-child { margin-bottom: 0; }

.modal-section h3 {
  font-size: 13px; font-weight: 700; color: #18181b;
  margin: 0 0 4px;
}

.modal-section p { margin: 0; }

.modal-footer {
  padding: 16px 24px; border-top: 1px solid rgba(0,0,0,0.06);
  flex-shrink: 0;
}

.modal-accept {
  width: 100%; height: 44px;
  display: flex; align-items: center; justify-content: center;
  border: none; border-radius: 12px;
  background: #059669; color: white;
  font-size: 14px; font-weight: 700; font-family: inherit;
  cursor: pointer;
  transition: transform 100ms ease-out, box-shadow 200ms ease;
}
.modal-accept:hover { box-shadow: 0 2px 12px rgba(5,150,105,0.3); }
.modal-accept:active { transform: scale(0.97); }

/* Modal transition */
.modal-enter-active { transition: opacity 200ms ease-out; }
.modal-leave-active { transition: opacity 150ms ease-in; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

.modal-enter-active .modal-card {
  transition: transform 300ms cubic-bezier(0.2,0.8,0.2,1), opacity 200ms ease-out;
}
.modal-leave-active .modal-card {
  transition: transform 150ms ease-in, opacity 150ms ease-in;
}
.modal-enter-from .modal-card { transform: translateY(16px) scale(0.97); opacity: 0; }
.modal-leave-to .modal-card { transform: translateY(8px) scale(0.98); opacity: 0; }

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 480px) {
  .register-card { padding: 28px 20px; border-radius: 20px; }
  .register-heading__title { font-size: 22px; }
  .register-cal__fields { grid-template-columns: 1fr; }
}
</style>

<style>
/* ═══════════════════════════════════════════════════
   Dark mode overrides (non-scoped → wins over DaisyUI)
   ═══════════════════════════════════════════════════ */
html[data-theme="jic-dark"] .register-page { background: #0b0f19 !important; }
html[data-theme="jic-dark"] .register-card { background: rgba(24,24,27,0.75) !important; border-color: rgba(255,255,255,0.08) !important; box-shadow: 0 0 0 1px rgba(255,255,255,0.03), 0 4px 24px rgba(0,0,0,0.3), 0 24px 64px rgba(0,0,0,0.2) !important; }
html[data-theme="jic-dark"] .register-logo__text { color: #fafafa !important; }
html[data-theme="jic-dark"] .register-heading__title { color: #fafafa !important; }
html[data-theme="jic-dark"] .register-heading__sub { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .register-field__label { color: #d4d4d8 !important; }
html[data-theme="jic-dark"] .register-input-wrap__icon { color: #52525b !important; }
html[data-theme="jic-dark"] .register-input-wrap:focus-within .register-input-wrap__icon { color: #34d399 !important; }
html[data-theme="jic-dark"] .register-input-wrap__toggle { color: #71717a !important; }
html[data-theme="jic-dark"] .register-input-wrap__toggle:hover { color: #d4d4d8 !important; background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .register-input-wrap__unit { color: #52525b !important; }
html[data-theme="jic-dark"] .register-input { border-color: #27272a !important; background: rgba(39,39,42,0.6) !important; color: #fafafa !important; }
html[data-theme="jic-dark"] .register-input::placeholder { color: #52525b !important; }
html[data-theme="jic-dark"] .register-input:focus { border-color: #34d399 !important; box-shadow: 0 0 0 3px rgba(52,211,153,0.15) !important; background: rgba(39,39,42,0.8) !important; }
html[data-theme="jic-dark"] .register-input:active { background: rgba(39,39,42,0.9) !important; }
html[data-theme="jic-dark"] .register-select { border-color: #27272a !important; background-color: rgba(39,39,42,0.6) !important; color: #fafafa !important; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") !important; }
html[data-theme="jic-dark"] .register-select:focus { border-color: #34d399 !important; box-shadow: 0 0 0 3px rgba(52,211,153,0.15) !important; }
html[data-theme="jic-dark"] .register-bar { background: #27272a !important; }
html[data-theme="jic-dark"] .register-bar--1 { background: #fbbf24 !important; }
html[data-theme="jic-dark"] .register-bar--2 { background: #34d399 !important; }
html[data-theme="jic-dark"] .register-bar--3 { background: #10b981 !important; }
html[data-theme="jic-dark"] .register-strength-label--ok { color: #34d399 !important; }
html[data-theme="jic-dark"] .register-strength-label--weak { color: #fbbf24 !important; }
html[data-theme="jic-dark"] .register-cal { background: rgba(52,211,153,0.06) !important; border-color: rgba(52,211,153,0.15) !important; }
html[data-theme="jic-dark"] .register-cal__summary:hover { background: rgba(52,211,153,0.08) !important; }
html[data-theme="jic-dark"] .register-cal__icon { background: rgba(52,211,153,0.1) !important; color: #34d399 !important; }
html[data-theme="jic-dark"] .register-cal__title { color: #34d399 !important; }
html[data-theme="jic-dark"] .register-cal__hint { color: #52525b !important; }
html[data-theme="jic-dark"] .register-cal__chevron { color: #34d399 !important; }
html[data-theme="jic-dark"] .register-cal__text { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .register-preview { background: rgba(255,255,255,0.03) !important; border-color: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .register-preview__name { color: #fafafa !important; }
html[data-theme="jic-dark"] .register-preview__meta { color: #71717a !important; }
html[data-theme="jic-dark"] .register-terms { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .register-terms__link { color: #34d399 !important; }
html[data-theme="jic-dark"] .register-terms__link:hover { color: #10b981 !important; }
html[data-theme="jic-dark"] .register-error { background: rgba(239,68,68,0.1) !important; border-color: rgba(239,68,68,0.25) !important; color: #f87171 !important; }
html[data-theme="jic-dark"] .register-submit { background: linear-gradient(135deg,#34d399,#10b981) !important; color: #022c22 !important; }
html[data-theme="jic-dark"] .register-submit:disabled { opacity: 0.5 !important; }
html[data-theme="jic-dark"] .register-spinner { border-color: rgba(0,0,0,0.2) !important; border-top-color: #022c22 !important; }
html[data-theme="jic-dark"] .register-footer__link { color: #34d399 !important; }
html[data-theme="jic-dark"] .register-footer__back { color: #52525b !important; }
html[data-theme="jic-dark"] .register-footer__back:hover { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .modal-card { background: rgba(24,24,27,0.92) !important; border-color: rgba(255,255,255,0.08) !important; box-shadow: 0 24px 64px rgba(0,0,0,0.5) !important; }
html[data-theme="jic-dark"] .modal-header { border-bottom-color: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .modal-title { color: #fafafa !important; }
html[data-theme="jic-dark"] .modal-close { color: #71717a !important; }
html[data-theme="jic-dark"] .modal-close:hover { background: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .modal-body { color: #a1a1aa !important; }
html[data-theme="jic-dark"] .modal-section h3 { color: #fafafa !important; }
html[data-theme="jic-dark"] .modal-footer { border-top-color: rgba(255,255,255,0.06) !important; }
html[data-theme="jic-dark"] .modal-accept { background: #34d399 !important; color: #022c22 !important; }
</style>
