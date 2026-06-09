<!--
  MapView — Main application view.
  Full-screen map with sidebar panels. Implemented in Phase 8.
  Placeholder styled with Tailwind CSS & DaisyUI.
-->
<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { currentTheme, toggleTheme } = useTheme()

// Components will be added in Phase 8:
// import RouteMap from '@/components/map/RouteMap.vue'
// import RouteSummary from '@/components/sidebar/RouteSummary.vue'
// import FileUploader from '@/components/upload/FileUploader.vue'
// import HikerProfileForm from '@/components/sidebar/HikerProfileForm.vue'
// import ClimateToggle from '@/components/simulation/ClimateToggle.vue'
// import ClimateSliders from '@/components/simulation/ClimateSliders.vue'
</script>

<template>
  <div class="h-screen w-screen flex flex-col md:flex-row bg-base-300 text-base-content overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-full md:w-80 lg:w-96 bg-base-200 border-b md:border-b-0 md:border-r border-base-100 flex flex-col shrink-0">
      <div class="p-6 border-b border-base-100 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-success to-primary bg-clip-text text-transparent">JIC-Geo</h1>
          <p class="text-xs text-base-content/60 mt-1">Dynamic Risk Index for Hikers</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="toggleTheme" class="btn btn-ghost btn-xs btn-circle text-base-content/60 hover:text-base-content" title="Toggle Theme">
            <!-- Sun Icon for dark theme -->
            <svg v-if="currentTheme === 'jic-dark'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4.5 h-4.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m0 13.5V21M5.22 5.22l1.58 1.58m9.75 9.75l1.58 1.58M3 12h2.25m13.5 0H21M5.22 18.78l1.58-1.58m9.75-9.75l1.58-1.58M12 7.5a4.5 4.5 0 110 9 4.5 4.5 0 010-9z" />
            </svg>
            <!-- Moon Icon for light theme -->
            <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4.5 h-4.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
            </svg>
          </button>
          <div class="badge badge-success badge-outline text-xs">v0.1.0</div>
        </div>
      </div>
      
      <div class="p-6 flex-1 overflow-y-auto space-y-6">
        <div class="card bg-base-100 shadow-md">
          <div class="card-body p-4">
            <h2 class="card-title text-sm font-semibold uppercase tracking-wider text-base-content/50">Infrastructure</h2>
            <div class="flex items-center gap-3 mt-2">
              <div class="w-3.5 h-3.5 rounded-full bg-success/20 flex items-center justify-center">
                <div class="w-2 h-2 rounded-full bg-success animate-pulse"></div>
              </div>
              <span class="text-sm font-medium">Vue 3 + Vite + TS</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-3.5 h-3.5 rounded-full bg-success/20 flex items-center justify-center">
                <div class="w-2 h-2 rounded-full bg-success animate-pulse"></div>
              </div>
              <span class="text-sm font-medium">Tailwind + DaisyUI</span>
            </div>
          </div>
        </div>

        <div class="alert alert-info shadow-sm bg-info/10 border-info/20 text-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <div class="text-xs">
            <h3 class="font-bold">Phase 0 Complete</h3>
            <p class="text-base-content/80 mt-0.5">Monorepo structure set up. Next: GPX upload & PostGIS ingestion.</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Map Area (Placeholder) -->
    <main class="flex-1 relative flex items-center justify-center bg-base-300">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]"></div>
      <div class="z-10 text-center max-w-md p-6">
        <h2 class="text-3xl font-extrabold mb-2">Interactive Map Area</h2>
        <p class="text-base-content/70 mb-6">MapLibre GL JS will render the 3D terrain and risk routes here in Phase 8.</p>
        <div class="flex justify-center gap-4">
          <button class="btn btn-primary shadow-lg text-white">Upload GPX</button>
          <button class="btn btn-outline border-base-content/20 hover:border-primary">Simulation Mode</button>
        </div>
      </div>
    </main>
  </div>
</template>
