/**
 * Pinia store — route analysis state.
 * Connects to the JIC-Geo API and holds current route data.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LineString } from 'geojson'

// --- Types ---

export interface MideDimensions {
  severity: number
  orientation: number
  displacement: number
  effort: number
}

export interface RouteSummary {
  total_distance_km: number
  elevation_gain_m: number
  elevation_loss_m: number
  estimated_time_h: number
  total_kcal: number
  high_confidence_segments_pct: number
  points_corrected: number
  mide_global: number
  mide_dimensions: MideDimensions
  climate_source: 'api' | 'simulation'
  climate_timestamp: string
}

export interface Segment {
  seq: number
  slope_pct: number
  direction: 'ascent' | 'descent' | 'flat'
  velocity_kmh: number
  velocity_model: string
  cot_j_per_kg_m: number
  cot_method: 'exact' | 'extrapolated'
  metabolic_rate_w: number
  risk_score: number
  is_top_risk: boolean
  geom: LineString
}

export interface RouteAnalysis {
  route_id: string
  summary: RouteSummary
  segments: Segment[]
}

export type SimulationScenario = 'dry' | 'light_rain' | 'heavy_rain' | 'extreme_heat' | 'night'

// --- Store ---

export const useRouteStore = defineStore('route', () => {
  const analysis = ref<RouteAnalysis | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const selectedSegmentSeq = ref<number | null>(null)
  const isSimulationMode = ref(false)

  const selectedSegment = computed(() =>
    analysis.value?.segments.find((s) => s.seq === selectedSegmentSeq.value) ?? null,
  )

  const highRiskSegments = computed(
    () => analysis.value?.segments.filter((s) => s.is_top_risk) ?? [],
  )

  async function uploadAndAnalyze(file: File, profile: object): Promise<void> {
    isLoading.value = true
    error.value = null

    const formData = new FormData()
    formData.append('file', file)
    formData.append('profile', JSON.stringify(profile))

    try {
      const res = await fetch('/api/v1/routes/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) throw new Error(`API error: ${res.status}`)

      analysis.value = await res.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
    } finally {
      isLoading.value = false
    }
  }

  async function runSimulation(scenario: SimulationScenario | object): Promise<void> {
    if (!analysis.value) return

    isLoading.value = true
    try {
      const res = await fetch(`/api/v1/routes/${analysis.value.route_id}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          typeof scenario === 'string' ? { scenario_name: scenario } : { climate: scenario },
        ),
      })

      if (!res.ok) throw new Error(`Simulation error: ${res.status}`)

      analysis.value = await res.json()
      isSimulationMode.value = true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
    } finally {
      isLoading.value = false
    }
  }

  function selectSegment(seq: number | null): void {
    selectedSegmentSeq.value = seq
  }

  function reset(): void {
    analysis.value = null
    error.value = null
    selectedSegmentSeq.value = null
    isSimulationMode.value = false
  }

  return {
    analysis,
    isLoading,
    error,
    selectedSegment,
    highRiskSegments,
    isSimulationMode,
    uploadAndAnalyze,
    runSimulation,
    selectSegment,
    reset,
  }
})
