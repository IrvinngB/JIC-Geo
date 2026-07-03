/**
 * useSimulation — composable managing climate simulation state.
 * SIM-01 to SIM-04, MAP-06, MAP-07.
 */

import { reactive, ref } from 'vue'
import { useRouteStore, type ClimateOverride } from '@/stores/routeStore'

export type SimulationScenario = 'dry' | 'light_rain' | 'heavy_rain' | 'extreme_heat' | 'night'

const SCENARIO_PRESETS: Record<SimulationScenario, ClimateOverride> = {
  dry: { temperature_c: 25, humidity_pct: 30, precip_mm: 0, uv_index: 5 },
  light_rain: { temperature_c: 18, humidity_pct: 75, precip_mm: 8, uv_index: 2 },
  heavy_rain: { temperature_c: 15, humidity_pct: 95, precip_mm: 35, uv_index: 1 },
  extreme_heat: { temperature_c: 40, humidity_pct: 60, precip_mm: 0, uv_index: 11 },
  night: { temperature_c: 12, humidity_pct: 65, precip_mm: 0, uv_index: 0 },
}

export function useSimulation() {
  const store = useRouteStore()
  const isSimulationMode = ref(false)
  const activeScenario = ref<SimulationScenario | null>(null)

  const climate = reactive<ClimateOverride>({
    temperature_c: 20,
    humidity_pct: 50,
    precip_mm: 0,
    uv_index: 3,
  })

  function applyScenario(scenario: SimulationScenario): void {
    const preset = SCENARIO_PRESETS[scenario]
    Object.assign(climate, preset)
    activeScenario.value = scenario
  }

  async function runSimulation(): Promise<void> {
    await store.runSimulation({ ...climate })
    isSimulationMode.value = true
  }

  async function switchToRealData(): Promise<void> {
    isSimulationMode.value = false
    activeScenario.value = null
    await store.refreshRealClimate()
  }

  return {
    isSimulationMode,
    activeScenario,
    climate,
    applyScenario,
    runSimulation,
    switchToRealData,
    SCENARIO_PRESETS,
  }
}
