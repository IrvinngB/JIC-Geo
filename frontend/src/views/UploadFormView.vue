<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppIcon, { type IconName } from '@/components/icons/AppIcon.vue'
import { useHikerProfile } from '@/composables/useHikerProfile'
import { useAuthStore } from '@/stores/authStore'
import { useRouteStore } from '@/stores/routeStore'
import sampleGpxRaw from '@/assets/sample-route.gpx?raw'

const router = useRouter()
const { profile, isValid } = useHikerProfile()
const auth = useAuthStore()
const routeStore = useRouteStore()

// Props (optional — when used as standalone route, profile comes from store)
const props = defineProps<{
  isLoading?: boolean
  error?: string | null
  hasAnalysis?: boolean
}>()

// Internal state
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const formFileInputRef = ref<HTMLInputElement | null>(null)
const mounted = ref(false)
const localLoading = ref(false)
const localError = ref('')

const isLoading = computed(() => props.isLoading ?? localLoading.value)
const error = computed(() => props.error ?? localError.value)
const hasAnalysis = computed(() => props.hasAnalysis ?? !!routeStore.analysis)

onMounted(() => {
  requestAnimationFrame(() => {
    mounted.value = true
  })
})

// Form helpers
function triggerBrowseFile(): void {
  formFileInputRef.value?.click()
}

function onFormFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    selectedFile.value = file
  }
  input.value = ''
}

function onDropFile(event: DragEvent): void {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    selectedFile.value = file
  }
}

function loadDemoRoute(): void {
  const blob = new Blob([sampleGpxRaw], { type: 'application/gpx+xml' })
  selectedFile.value = new File(
    [blob],
    'ciudad-panama-cerro-ancon-sendero-el-mirador-panama.gpx',
    { type: 'application/gpx+xml' }
  )
}

async function handleSubmit(): Promise<void> {
  if (!selectedFile.value || isLoading.value || !isValid()) return
  localError.value = ''

  try {
    await routeStore.uploadAndAnalyze(selectedFile.value, { ...profile })
    router.push('/mapa')
  } catch (e: any) {
    localError.value = e.message || 'Error al analizar la ruta.'
  }
}

function handleKeydown(e: KeyboardEvent): void {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

// Computed fields
const totalMass = computed(() => (profile.weight_kg || 0) + (profile.load_kg || 0))

const loadImpactBadge = computed(() => {
  const weight = profile.weight_kg || 70
  const load = profile.load_kg || 0
  const ratio = load / weight

  if (ratio < 0.15) {
    return { label: 'Carga ligera', class: 'badge-success' }
  } else if (ratio <= 0.25) {
    return { label: 'Impacto normal', class: 'badge-warning' }
  } else {
    return { label: 'Carga pesada', class: 'badge-error' }
  }
})

const isFormValid = computed(() => {
  return (
    selectedFile.value !== null &&
    profile.weight_kg > 0 &&
    profile.load_kg >= 0 &&
    profile.load_kg < profile.weight_kg
  )
})
</script>

<template>
  <div class="uf-page" :class="{ 'uf-page--visible': mounted }">

    <!-- Main Card -->
    <main class="uf-card">

      <!-- Back Link -->
      <div class="uf-breadcrumb">
        <button
          v-if="hasAnalysis"
          class="uf-breadcrumb__link"
          @click="router.push('/mapa')"
        >
          <AppIcon name="arrow-right" :size="13" class="uf-breadcrumb__icon--rotate" />
          Volver a la ruta analizada
        </button>
        <RouterLink
          v-else
          to="/"
          class="uf-breadcrumb__link"
        >
          <AppIcon name="arrow-right" :size="12" class="uf-breadcrumb__icon--rotate" />
          Volver a Explorar
        </RouterLink>
        <span class="uf-breadcrumb__sep">/</span>
        <span class="uf-breadcrumb__current">Cargar nueva ruta</span>
      </div>

      <!-- Title -->
      <div class="uf-heading">
        <h1 class="uf-heading__title">Cargar Ruta y Configuración de Perfil</h1>
        <p class="uf-heading__sub">
          Sube tu archivo GPX o GeoJSON y calibra los parámetros biométricos para calcular el índice de riesgo MIDE y la carga metabólica en montaña.
        </p>
      </div>

      <!-- Error Alert -->
      <Transition name="error">
        <div v-if="error" class="uf-error" role="alert">
          <AppIcon name="alert-triangle" :size="16" class="shrink-0" />
          <span>{{ error }}</span>
        </div>
      </Transition>

      <!-- 2-Column Grid -->
      <div class="uf-grid" @keydown="handleKeydown">

        <!-- LEFT COLUMN (7 cols): Dropzone + Map Preview -->
        <div class="uf-grid__left">

          <!-- Card: Importar Track -->
          <div class="uf-card-inner">
            <div class="uf-card-inner__header">
              <div class="uf-card-inner__title-group">
                <div class="uf-card-inner__icon-wrap">
                  <AppIcon name="file-text" :size="18" />
                </div>
                <div>
                  <h2 class="uf-card-inner__title">Importar Track Satelital</h2>
                  <p class="uf-card-inner__sub">Formatos GPX o GeoJSON con timestamps</p>
                </div>
              </div>
              <span class="uf-badge uf-badge--success">MOTOR V4.2 LISTO</span>
            </div>

            <!-- Dropzone -->
            <div
              class="uf-dropzone"
              :class="{ 'uf-dropzone--active': isDragging }"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
              @drop="onDropFile"
              @click="triggerBrowseFile"
            >
              <input
                ref="formFileInputRef"
                type="file"
                accept=".gpx,.geojson,.json,application/geo+json,application/json"
                class="uf-dropzone__input"
                @change="onFormFileChange"
              />

              <div class="uf-dropzone__icon">
                <AppIcon name="upload" :size="24" />
              </div>

              <p class="uf-dropzone__label">
                {{ selectedFile ? selectedFile.name : 'Arrastra tu archivo GPX o GeoJSON aquí' }}
              </p>
              <p class="uf-dropzone__hint">
                {{ selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB preparado para analizar` : 'Compatible con exportaciones de Strava, Garmin Connect, Wikiloc, Suunto y AllTrails (hasta 25 MB).' }}
              </p>

              <div class="uf-dropzone__actions">
                <button
                  type="button"
                  class="uf-btn uf-btn--primary uf-btn--sm"
                  @click.stop="triggerBrowseFile"
                >
                  <AppIcon name="folder" :size="14" />
                  {{ selectedFile ? 'Cambiar archivo' : 'Examinar archivos' }}
                </button>
                <span v-if="!selectedFile" class="uf-dropzone__hint--uppercase">O SUELTA EL ARCHIVO</span>
              </div>
            </div>

            <!-- Demo Route Banner -->
            <div class="uf-demo-banner">
              <div class="uf-demo-banner__content">
                <div class="uf-demo-banner__icon">
                  <AppIcon name="mountain" :size="16" />
                </div>
                <div class="uf-demo-banner__text">
                  <span class="uf-demo-banner__label">¿No tienes un archivo a mano?</span>
                  <p class="uf-demo-banner__sub">Prueba con la ruta de muestra: Cerro Ancón, Panamá (+145m D+)</p>
                </div>
              </div>
              <button
                type="button"
                class="uf-btn uf-btn--ghost uf-btn--sm"
                @click="loadDemoRoute"
              >
                Cargar demo
                <AppIcon name="arrow-right" :size="12" />
              </button>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN (5 cols): Profile + Terrain + Submit -->
        <div class="uf-grid__right">

          <!-- Card: Hiker Profile -->
          <div class="uf-card-inner">
            <div class="uf-card-inner__header">
              <div class="uf-card-inner__title-group">
                <div class="uf-card-inner__icon-wrap">
                  <AppIcon name="activity" :size="18" />
                </div>
                <div>
                  <h2 class="uf-card-inner__title">1. Perfil del Excursionista</h2>
                  <p class="uf-card-inner__sub">Calibración de esfuerzo metabólico y fatiga</p>
                </div>
              </div>
            </div>

            <!-- Name -->
            <div class="uf-field">
              <div class="uf-field__header">
                <label class="uf-field__label">Nombre o alias del senderista</label>
                <span class="uf-field__optional">Opcional</span>
              </div>
              <input
                v-model="profile.name"
                type="text"
                placeholder="Ej. Irvin Solo"
                class="uf-input"
              />
            </div>

            <!-- Weight & Load -->
            <div class="uf-field-row">
              <div class="uf-field">
                <label class="uf-field__label">Peso corporal</label>
                <div class="uf-input-wrap">
                  <input
                    v-model.number="profile.weight_kg"
                    type="number"
                    min="30"
                    max="200"
                    class="uf-input uf-input--number"
                  />
                  <span class="uf-input-wrap__unit">kg</span>
                </div>
              </div>
              <div class="uf-field">
                <label class="uf-field__label">Mochila</label>
                <div class="uf-input-wrap">
                  <input
                    v-model.number="profile.load_kg"
                    type="number"
                    min="0"
                    max="60"
                    class="uf-input uf-input--number"
                  />
                  <span class="uf-input-wrap__unit">kg</span>
                </div>
              </div>
            </div>

            <!-- Total Mass -->
            <div class="uf-mass-callout">
              <span class="uf-mass-callout__label">Masa total en marcha:</span>
              <div class="uf-mass-callout__value">
                <strong class="uf-mass-callout__number">{{ totalMass }} kg</strong>
                <span class="uf-badge" :class="loadImpactBadge.class">
                  {{ loadImpactBadge.label }}
                </span>
              </div>
            </div>

            <!-- Fitness Level (Segmented Control) -->
            <div class="uf-field">
              <label class="uf-field__label">Condición física actual</label>
              <div class="uf-segment-control">
                <button
                  v-for="opt in [
                    { id: 'low', label: 'Baja' },
                    { id: 'medium', label: 'Media' },
                    { id: 'high', label: 'Alta' },
                    { id: 'athlete', label: 'Atleta' },
                  ]"
                  :key="opt.id"
                  type="button"
                  class="uf-segment-control__item"
                  :class="{ 'uf-segment-control__item--active': profile.fitness_level === opt.id }"
                  @click="profile.fitness_level = opt.id as any"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- Card: Terrain -->
          <div class="uf-card-inner">
            <div class="uf-card-inner__header">
              <div class="uf-card-inner__title-group">
                <div class="uf-card-inner__icon-wrap">
                  <AppIcon name="mountain" :size="18" />
                </div>
                <div>
                  <h2 class="uf-card-inner__title">2. Terreno</h2>
                  <p class="uf-card-inner__sub">Factores de rozamiento e impacto articular</p>
                </div>
              </div>
            </div>

            <div class="uf-field">
              <label class="uf-field__label">Tipo de superficie predominante</label>
              <select v-model="profile.surface_type" class="uf-select">
                <option value="dirt">Tierra compacta / Sendero regular (fricción 1.0)</option>
                <option value="paved">Pavimento / Asfalto (fricción 1.0)</option>
                <option value="gravel">Grava / Terreno suelto (fricción 1.2)</option>
                <option value="mud">Barro / Terreno húmedo (fricción 1.5)</option>
                <option value="sand">Arena blanda (fricción 1.8)</option>
                <option value="scrub">Matorral bajo / Sendero rústico (fricción 1.3)</option>
                <option value="dense_scrub">Matorral denso / Sin traza definida (fricción 1.6)</option>
              </select>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="uf-card-inner">
            <button
              type="button"
              class="uf-submit"
              :class="{ 'uf-submit--disabled': !isFormValid || isLoading }"
              :disabled="!isFormValid || isLoading"
              @click="handleSubmit"
            >
              <span v-if="isLoading" class="uf-spinner" />
              <template v-else>
                <AppIcon name="zap" :size="16" />
                <span>Analizar ruta</span>
                <AppIcon name="arrow-right" :size="14" />
              </template>
              <span v-if="isLoading">Procesando...</span>
            </button>

            <p class="uf-submit__disclaimer">
              <AppIcon name="shield" :size="12" class="uf-icon--green" />
              <span>El backend calcula MIDE, Minetti y riesgo con datos reales de la ruta</span>
            </p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ── Page Layout ────────────────────────────────── */
.uf-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 32px 16px;
  overflow-x: hidden;
  overflow-y: auto;
  background-color: #f4f4f5;
  background-image:
    radial-gradient(at 50% 0%, rgba(16, 185, 129, 0.06) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.04) 0px, transparent 50%);

  /* Spring entrance */
  opacity: 0;
  transform: translateY(12px) scale(0.98);
  transition:
    opacity 350ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 350ms cubic-bezier(0.16, 1, 0.3, 1);
}

.uf-page--visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* ── Main Card ──────────────────────────────────── */
.uf-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 1200px;
  padding: 32px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #e4e4e7;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.03),
    0 12px 32px -4px rgba(0, 0, 0, 0.08);
}

/* ── Breadcrumb ─────────────────────────────────── */
.uf-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 12px;
  font-weight: 500;
  color: #71717a;
}

.uf-breadcrumb__link {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #059669;
  font-weight: 700;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  text-decoration: none;
  transition: color 150ms ease, transform 100ms ease-out;
}

.uf-breadcrumb__link:hover {
  color: #047857;
  text-decoration: underline;
}

.uf-breadcrumb__link:active {
  transform: scale(0.96);
}

.uf-breadcrumb__icon--rotate {
  transform: rotate(180deg);
}

.uf-breadcrumb__sep {
  color: #a1a1aa;
}

.uf-breadcrumb__current {
  font-weight: 600;
  color: #18181b;
}

/* ── Heading ────────────────────────────────────── */
.uf-heading {
  margin-bottom: 24px;
}

.uf-heading__title {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #18181b;
  margin: 0;
}

.uf-heading__sub {
  font-size: 13px;
  color: #71717a;
  margin: 6px 0 0;
  max-width: 640px;
  line-height: 1.5;
}

/* ── Error Alert ────────────────────────────────── */
.uf-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 24px;
}

.error-enter-active,
.error-leave-active {
  transition: opacity 150ms ease, transform 150ms ease;
}

.error-enter-from,
.error-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── Grid Layout ────────────────────────────────── */
.uf-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.uf-grid__left,
.uf-grid__right {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (min-width: 1024px) {
  .uf-grid {
    grid-template-columns: 7fr 5fr;
  }
}

/* ── Inner Card ─────────────────────────────────── */
.uf-card-inner {
  border-radius: 16px;
  border: 1px solid #e4e4e7;
  background: #ffffff;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 150ms ease;
}

.uf-card-inner:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.uf-card-inner__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.uf-card-inner__title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.uf-card-inner__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  flex-shrink: 0;
}

.uf-card-inner__title {
  font-size: 14px;
  font-weight: 700;
  color: #18181b;
  margin: 0;
}

.uf-card-inner__title--uppercase {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #18181b;
  margin: 0;
}

.uf-card-inner__sub {
  font-size: 11px;
  color: #71717a;
  margin: 2px 0 0;
}

/* ── Badge ──────────────────────────────────────── */
.uf-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.uf-badge--success {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.uf-badge--ghost {
  background: transparent;
  color: #71717a;
}

/* ── Dropzone ───────────────────────────────────── */
.uf-dropzone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  border: 2px dashed #d4d4d8;
  background: #fafafa;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition:
    border-color 150ms ease,
    background-color 150ms ease,
    transform 100ms ease-out;
}

.uf-dropzone:hover {
  border-color: #059669;
  background: rgba(16, 185, 129, 0.03);
}

.uf-dropzone:active {
  transform: scale(0.99);
}

.uf-dropzone--active {
  border-color: #059669;
  background: rgba(16, 185, 129, 0.06);
}

.uf-dropzone__input {
  display: none;
}

.uf-dropzone__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.uf-dropzone__label {
  font-size: 14px;
  font-weight: 700;
  color: #18181b;
  margin: 0;
}

.uf-dropzone__hint {
  font-size: 12px;
  color: #71717a;
  margin: 4px 0 0;
  max-width: 420px;
  line-height: 1.4;
}

.uf-dropzone__hint--uppercase {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #a1a1aa;
}

.uf-dropzone__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

/* ── Demo Banner ────────────────────────────────── */
.uf-demo-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(16, 185, 129, 0.04);
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.uf-demo-banner__content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.uf-demo-banner__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
  flex-shrink: 0;
}

.uf-demo-banner__text {
  font-size: 12px;
}

.uf-demo-banner__label {
  font-weight: 700;
  color: #18181b;
}

.uf-demo-banner__sub {
  font-size: 11px;
  color: #71717a;
  margin: 2px 0 0;
}

/* ── Map Container ──────────────────────────────── */







/* ── Fields ─────────────────────────────────────── */
.uf-field {
  margin-bottom: 16px;
}

.uf-field:last-child {
  margin-bottom: 0;
}

.uf-field__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.uf-field__label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #27272a;
  letter-spacing: -0.01em;
}

.uf-field__optional {
  font-size: 10px;
  color: #a1a1aa;
}

.uf-field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

/* ── Input ──────────────────────────────────────── */
.uf-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid #d4d4d8;
  background: #ffffff;
  font-size: 13px;
  font-family: inherit;
  font-weight: 500;
  color: #18181b;
  outline: none;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.uf-input::placeholder {
  color: #a1a1aa;
}

.uf-input:focus {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
}

.uf-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.uf-input--number {
  padding-right: 36px;
  font-weight: 700;
}

.uf-input-wrap__unit {
  position: absolute;
  right: 12px;
  font-size: 12px;
  color: #a1a1aa;
  pointer-events: none;
}

/* ── Select ─────────────────────────────────────── */
.uf-select {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid #d4d4d8;
  background: #ffffff;
  font-size: 13px;
  font-family: inherit;
  font-weight: 500;
  color: #18181b;
  outline: none;
  cursor: pointer;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.uf-select:focus {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
}

/* ── Mass Callout ───────────────────────────────── */
.uf-mass-callout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(244, 244, 245, 0.8);
  margin-bottom: 16px;
}

.uf-mass-callout__label {
  font-size: 12px;
  font-weight: 500;
  color: #52525b;
}

.uf-mass-callout__value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uf-mass-callout__number {
  font-size: 14px;
  font-weight: 800;
  color: #18181b;
}

/* ── Segmented Control ─────────────────────────── */
.uf-segment-control {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.uf-segment-control__item {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e4e4e7;
  border-radius: 10px;
  background: #ffffff;
  font-size: 12px;
  font-weight: 700;
  font-family: inherit;
  color: #71717a;
  cursor: pointer;
  transition:
    background 150ms ease,
    color 150ms ease,
    border-color 150ms ease,
    box-shadow 150ms ease,
    transform 100ms ease-out;
}

.uf-segment-control__item:hover {
  background: #f4f4f5;
  color: #18181b;
}

.uf-segment-control__item:active {
  transform: scale(0.97);
}

.uf-segment-control__item--active {
  background: #059669;
  color: #ffffff;
  border-color: #059669;
  box-shadow: 0 1px 3px rgba(5, 150, 105, 0.3);
}

.uf-segment-control__item--active:hover {
  background: #047857;
  color: #ffffff;
}

/* ── Precalc Grid ───────────────────────────────── */






/* ── Advice ─────────────────────────────────────── */





/* ── Submit Button ──────────────────────────────── */
.uf-submit {
  position: relative;
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #059669, #047857);
  color: white;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  letter-spacing: -0.01em;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
  transition:
    transform 100ms ease-out,
    background 150ms ease,
    box-shadow 150ms ease;
}

.uf-submit:hover:not(.uf-submit--disabled) {
  box-shadow: 0 4px 14px rgba(5, 150, 105, 0.4);
}

.uf-submit:active:not(.uf-submit--disabled) {
  transform: scale(0.97);
  box-shadow: 0 1px 4px rgba(5, 150, 105, 0.2);
}

.uf-submit--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.uf-submit__disclaimer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  font-size: 10px;
  color: #a1a1aa;
  margin-top: 10px;
}

/* ── Spinner ────────────────────────────────────── */
.uf-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: uf-spin 600ms linear infinite;
}

@keyframes uf-spin {
  to { transform: rotate(360deg); }
}

/* ── Utility Icons ──────────────────────────────── */
.uf-icon--amber {
  color: #d97706;
}

.uf-icon--green {
  color: #059669;
}

.shrink-0 {
  flex-shrink: 0;
}
</style>

<style>
/* ── Dark Mode Overrides (non-scoped) ───────────── */
html[data-theme="jic-dark"] .uf-page {
  background-color: #090d16;
  background-image:
    radial-gradient(at 50% 0%, rgba(16, 185, 129, 0.1) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.06) 0px, transparent 50%);
}

html[data-theme="jic-dark"] .uf-card {
  background: rgba(24, 24, 27, 0.75);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.03),
    0 4px 24px rgba(0, 0, 0, 0.3),
    0 24px 64px rgba(0, 0, 0, 0.2);
}

html[data-theme="jic-dark"] .uf-breadcrumb {
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-breadcrumb__link {
  color: #10b981;
}

html[data-theme="jic-dark"] .uf-breadcrumb__current {
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-heading__title {
  color: #fafafa;
}

html[data-theme="jic-dark"] .uf-heading__sub {
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-error {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

html[data-theme="jic-dark"] .uf-card-inner {
  background: rgba(39, 39, 42, 0.5);
  border-color: rgba(255, 255, 255, 0.06);
}

html[data-theme="jic-dark"] .uf-card-inner:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

html[data-theme="jic-dark"] .uf-card-inner__icon-wrap {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

html[data-theme="jic-dark"] .uf-card-inner__title,
html[data-theme="jic-dark"] .uf-card-inner__title--uppercase {
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-card-inner__sub {
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-badge--success {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.25);
}

html[data-theme="jic-dark"] .uf-badge--ghost {
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-dropzone {
  border-color: #334155;
  background: rgba(39, 39, 42, 0.4);
}

html[data-theme="jic-dark"] .uf-dropzone:hover {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.06);
}

html[data-theme="jic-dark"] .uf-dropzone--active {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

html[data-theme="jic-dark"] .uf-dropzone__icon {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

html[data-theme="jic-dark"] .uf-dropzone__label {
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-dropzone__hint {
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-dropzone__hint--uppercase {
  color: #52525b;
}

html[data-theme="jic-dark"] .uf-demo-banner {
  background: rgba(16, 185, 129, 0.06);
  border-color: rgba(16, 185, 129, 0.2);
}

html[data-theme="jic-dark"] .uf-demo-banner__icon {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

html[data-theme="jic-dark"] .uf-demo-banner__label {
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-demo-banner__sub {
  color: #9ca3af;
}








html[data-theme="jic-dark"] .uf-field__label {
  color: #e4e4e7;
}

html[data-theme="jic-dark"] .uf-field__optional {
  color: #52525b;
}

html[data-theme="jic-dark"] .uf-input {
  border-color: #334155;
  background: rgba(39, 39, 42, 0.6);
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-input::placeholder {
  color: #52525b;
}

html[data-theme="jic-dark"] .uf-input:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
  background: rgba(39, 39, 42, 0.8);
}

html[data-theme="jic-dark"] .uf-input-wrap__unit {
  color: #52525b;
}

html[data-theme="jic-dark"] .uf-select {
  border-color: #334155;
  background: rgba(39, 39, 42, 0.6);
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-select:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

html[data-theme="jic-dark"] .uf-mass-callout {
  background: rgba(39, 39, 42, 0.4);
}

html[data-theme="jic-dark"] .uf-mass-callout__label {
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-mass-callout__number {
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-segment-control__item {
  border-color: #334155;
  background: rgba(39, 39, 42, 0.5);
  color: #9ca3af;
}

html[data-theme="jic-dark"] .uf-segment-control__item:hover {
  background: rgba(39, 39, 42, 0.8);
  color: #f4f4f5;
}

html[data-theme="jic-dark"] .uf-segment-control__item--active {
  background: #10b981;
  color: #022c22;
  border-color: #10b981;
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.35);
}








html[data-theme="jic-dark"] .uf-submit {
  background: linear-gradient(135deg, #34d399, #10b981);
  color: #022c22;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
}

html[data-theme="jic-dark"] .uf-submit--disabled {
  opacity: 0.5;
}

html[data-theme="jic-dark"] .uf-spinner {
  border-color: rgba(0, 0, 0, 0.2);
  border-top-color: #022c22;
}

html[data-theme="jic-dark"] .uf-submit__disclaimer {
  color: #52525b;
}

html[data-theme="jic-dark"] .uf-icon--green {
  color: #10b981;
}

html[data-theme="jic-dark"] .uf-icon--amber {
  color: #fbbf24;
}
</style>
