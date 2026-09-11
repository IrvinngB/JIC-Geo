<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useProfileStore, type UserProfile } from '@/stores/profileStore'
import AppIcon from '@/components/icons/AppIcon.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const auth = useAuthStore()
const profileStore = useProfileStore()
const router = useRouter()

const showForm = ref(false)
const editingId = ref<string | null>(null)

const form = ref({
  name: '',
  weight_kg: 70,
  load_kg: 10,
  fitness_level: 'medium',
  surface_type: 'dirt',
})

onMounted(() => {
  if (!auth.isAuthenticated) {
    router.push('/login')
    return
  }
  profileStore.fetchProfiles()
})

function openCreate() {
  editingId.value = null
  form.value = { name: '', weight_kg: 70, load_kg: 10, fitness_level: 'medium', surface_type: 'dirt' }
  showForm.value = true
}

function openEdit(profile: UserProfile) {
  editingId.value = profile.id
  form.value = {
    name: profile.name,
    weight_kg: profile.weight_kg,
    load_kg: profile.load_kg,
    fitness_level: profile.fitness_level,
    surface_type: profile.surface_type,
  }
  showForm.value = true
}

async function handleSubmit() {
  if (editingId.value) {
    await profileStore.updateProfile(editingId.value, form.value)
  } else {
    await profileStore.createProfile(form.value)
  }
  showForm.value = false
}

async function handleDelete(id: string) {
  if (confirm('¿Eliminar este perfil?')) {
    await profileStore.deleteProfile(id)
  }
}

async function handleSetDefault(id: string) {
  await profileStore.setDefault(id)
}

const fitnessLabels: Record<string, string> = { low: 'Baja', medium: 'Media', high: 'Alta', athlete: 'Atleta' }
const surfaceLabels: Record<string, string> = {
  dirt: 'Tierra', paved: 'Pavimento', gravel: 'Grava', mud: 'Barro', sand: 'Arena', scrub: 'Matorral', dense_scrub: 'Matorral denso',
}
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <header class="sticky top-0 z-40 border-b border-base-200 bg-base-100 px-4 shadow-xs sm:px-8">
      <div class="mx-auto flex h-14 max-w-4xl items-center justify-between">
        <div class="flex items-center gap-3">
          <RouterLink to="/mapa" class="text-xs text-base-content/50 hover:text-base-content">← Mapa</RouterLink>
          <h1 class="text-sm font-bold">Perfiles</h1>
        </div>
        <BaseButton size="sm" @click="openCreate">
          <AppIcon name="arrow-right" :size="14" /> Nuevo
        </BaseButton>
      </div>
    </header>

    <main class="mx-auto max-w-4xl px-4 py-6 sm:px-8">
      <!-- Profile list -->
      <div v-if="!showForm" class="space-y-3">
        <div v-if="profileStore.profiles.length === 0" class="rounded-2xl border border-dashed border-base-300 py-12 text-center">
          <AppIcon name="footprints" :size="40" class="mx-auto mb-3 text-base-content/20" />
          <p class="text-sm text-base-content/50">No tenés perfiles guardados</p>
          <BaseButton size="sm" class="mt-4" @click="openCreate">Crear primer perfil</BaseButton>
        </div>

        <div
          v-for="p in profileStore.profiles"
          :key="p.id"
          class="flex items-center justify-between rounded-2xl border border-base-200 bg-base-100 p-4 transition hover:border-primary/30"
        >
          <div class="flex items-center gap-4">
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary font-bold">
              {{ p.name?.charAt(0)?.toUpperCase() ?? '?' }}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="font-bold text-sm">{{ p.name }}</span>
                <span v-if="p.is_default" class="badge badge-success badge-xs">Default</span>
              </div>
              <div class="mt-0.5 text-xs text-base-content/50">
                {{ p.weight_kg }}kg · {{ p.load_kg }}kg carga · {{ fitnessLabels[p.fitness_level] ?? p.fitness_level }} · {{ surfaceLabels[p.surface_type] ?? p.surface_type }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button v-if="!p.is_default" class="btn btn-ghost btn-xs text-base-content/40" @click="handleSetDefault(p.id)">Default</button>
            <button class="btn btn-ghost btn-xs text-base-content/40" @click="openEdit(p)">Editar</button>
            <button class="btn btn-ghost btn-xs text-error/60" @click="handleDelete(p.id)">Eliminar</button>
          </div>
        </div>
      </div>

      <!-- Create/Edit form -->
      <div v-else class="rounded-2xl border border-base-200 bg-base-100 p-6">
        <h2 class="mb-4 font-bold">{{ editingId ? 'Editar perfil' : 'Nuevo perfil' }}</h2>
        <form class="space-y-4" @submit.prevent="handleSubmit">
          <BaseInput v-model="form.name" label="Nombre" placeholder="Ej: Irvin solo" required />
          <div class="grid grid-cols-2 gap-4">
            <BaseInput v-model.number="form.weight_kg" label="Peso (kg)" type="number" required />
            <BaseInput v-model.number="form.load_kg" label="Carga (kg)" type="number" required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <label class="form-control">
              <span class="label-text text-xs font-medium text-base-content/70">Condición física</span>
              <select v-model="form.fitness_level" class="select select-bordered select-sm w-full">
                <option value="low">Baja</option>
                <option value="medium">Media</option>
                <option value="high">Alta</option>
                <option value="athlete">Atleta</option>
              </select>
            </label>
            <label class="form-control">
              <span class="label-text text-xs font-medium text-base-content/70">Superficie</span>
              <select v-model="form.surface_type" class="select select-bordered select-sm w-full">
                <option value="dirt">Tierra</option>
                <option value="paved">Pavimento</option>
                <option value="gravel">Grava</option>
                <option value="mud">Barro</option>
                <option value="sand">Arena</option>
                <option value="scrub">Matorral</option>
                <option value="dense_scrub">Matorral denso</option>
              </select>
            </label>
          </div>
          <div class="flex gap-2 pt-2">
            <BaseButton type="submit" :loading="profileStore.isLoading">Guardar</BaseButton>
            <BaseButton variant="ghost" @click="showForm = false">Cancelar</BaseButton>
          </div>
        </form>
      </div>
    </main>
  </div>
</template>
