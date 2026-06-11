/**
 * Pinia store - route analysis state.
 * Uses the backend flow: upload -> process -> biomechanical/risk analysis.
 */

import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type { LineString } from "geojson";
import type { HikerProfile } from "@/composables/useHikerProfile";

export interface MideDimensions {
  severity: number;
  orientation: number;
  displacement: number;
  effort: number;
}

export interface RouteSummary {
  total_distance_km: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  estimated_time_h: number;
  total_kcal: number;
  high_confidence_segments_pct: number;
  points_corrected: number;
  time_to_severe_fatigue_h: number | null;
  ccr: number;
  mide_global: number;
  mide_dimensions: MideDimensions;
  climate_source: "pending" | "api" | "simulation";
  climate_timestamp: string | null;
}

export interface ClimateFactors {
  wbgt: number;
  precip_mm: number;
  uv_index: number;
  cardiovascular_multiplier: number;
  climate_cost_multiplier: number;
  fc_precipitation: number;
  fc_erodability: number;
  fc_anegamiento: number;
  fc_brillo_solar: number;
}

export interface Segment {
  seq: number;
  slope_pct: number;
  direction: "ascent" | "descent" | "flat";
  velocity_kmh: number;
  velocity_model: string;
  cot_j_per_kg_m: number;
  cot_method: "exact" | "extrapolated";
  metabolic_rate_w: number;
  is_eccentric_fatigue: boolean;
  surface_type: string;
  is_on_path: boolean;
  time_min: number;
  kcal: number;
  risk_score: number;
  is_top_risk: boolean;
  mide_dimensions?: MideDimensions;
  climate_factors?: ClimateFactors;
  geom?: LineString;
}

export interface RouteAnalysis {
  route_id: string;
  route_name: string | null;
  source_format: string;
  summary: RouteSummary;
  segments: Segment[];
}

export interface ClimateOverride {
  temperature_c: number;
  humidity_pct: number;
  precip_mm: number;
  uv_index: number;
}

interface UploadResponse {
  route_id: string;
  name: string | null;
  source_format: string;
}

interface ProcessResponse {
  route_id: string;
  points_corrected: number;
  segments: Array<{
    seq: number;
    elevation_interpolated?: boolean;
  }>;
}

interface BiomechanicalResponse {
  route_id: string;
  summary: {
    total_distance_km: number;
    elevation_gain_m: number;
    elevation_loss_m: number;
    estimated_time_h: number;
    total_kcal: number;
    high_confidence_segments_pct: number;
    time_to_severe_fatigue_h: number | null;
    mide_effort_level: number;
    mide_global: number;
    mide_dimensions: MideDimensions;
    ccr: number;
    climate_source: "api" | "simulation";
    climate_timestamp: string | null;
  };
  segments: Array<{
    seq: number;
    slope_pct: number;
    direction: "ascent" | "descent" | "flat";
    velocity_kmh: number;
    velocity_model: string;
    cot_j_per_kg_m: number;
    cot_method: "exact" | "extrapolated";
    metabolic_rate_w: number;
    is_eccentric_fatigue: boolean;
    surface_type: string;
    is_on_path: boolean;
    time_min: number;
    kcal: number;
    risk_score: number;
    is_top_risk: boolean;
    mide_dimensions?: MideDimensions;
    climate_factors?: ClimateFactors;
    geom: LineString | null;
  }>;
}

export type SimulationScenario =
  | "dry"
  | "light_rain"
  | "heavy_rain"
  | "extreme_heat"
  | "night";

const API_BASE = "/api/v1";

async function parseApiError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    return JSON.stringify(body.detail ?? body);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

function mapBackendSegment(
  segment: BiomechanicalResponse["segments"][number],
  interpolatedBySeq?: Map<number, boolean>,
): Segment {
  return {
    ...segment,
    geom: segment.geom ?? undefined,
    is_eccentric_fatigue:
      segment.is_eccentric_fatigue || Boolean(interpolatedBySeq?.get(segment.seq)),
  };
}

export const useRouteStore = defineStore("route", () => {
  const analysis = ref<RouteAnalysis | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const selectedSegmentSeq = ref<number | null>(null);
  const isSimulationMode = ref(false);
  const currentProfile = ref<HikerProfile | null>(null);

  const selectedSegment = computed(
    () =>
      analysis.value?.segments.find(
        (segment) => segment.seq === selectedSegmentSeq.value,
      ) ?? null,
  );

  const highRiskSegments = computed(
    () =>
      analysis.value?.segments.filter((segment) => segment.is_top_risk) ?? [],
  );

  async function uploadAndAnalyze(
    file: File,
    profile: HikerProfile,
  ): Promise<void> {
    isLoading.value = true;
    error.value = null;
    selectedSegmentSeq.value = null;
    currentProfile.value = { ...profile };

    try {
      const upload = await uploadRoute(file);
      const processed = await processRoute(upload.route_id);
      const biomechanical = await analyzeBiomechanics(upload.route_id, profile);

      const interpolatedBySeq = new Map(
        processed.segments.map((segment) => [
          segment.seq,
          Boolean(segment.elevation_interpolated),
        ]),
      );

      analysis.value = {
        route_id: upload.route_id,
        route_name: upload.name,
        source_format: upload.source_format,
        summary: {
          total_distance_km: biomechanical.summary.total_distance_km,
          elevation_gain_m: biomechanical.summary.elevation_gain_m,
          elevation_loss_m: biomechanical.summary.elevation_loss_m,
          estimated_time_h: biomechanical.summary.estimated_time_h,
          total_kcal: biomechanical.summary.total_kcal,
          high_confidence_segments_pct:
            biomechanical.summary.high_confidence_segments_pct,
          points_corrected: processed.points_corrected,
          time_to_severe_fatigue_h:
            biomechanical.summary.time_to_severe_fatigue_h,
          ccr: biomechanical.summary.ccr,
          mide_global: biomechanical.summary.mide_global,
          mide_dimensions: biomechanical.summary.mide_dimensions,
          climate_source: biomechanical.summary.climate_source,
          climate_timestamp: biomechanical.summary.climate_timestamp,
        },
        segments: biomechanical.segments.map((segment) =>
          mapBackendSegment(segment, interpolatedBySeq),
        ),
      };
      isSimulationMode.value = false;
    } catch (err) {
      error.value =
        err instanceof Error
          ? err.message
          : "Error desconocido al analizar la ruta";
    } finally {
      isLoading.value = false;
    }
  }

  async function uploadRoute(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/routes/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok)
      throw new Error(`Upload failed: ${await parseApiError(response)}`);
    return response.json() as Promise<UploadResponse>;
  }

  async function processRoute(routeId: string): Promise<ProcessResponse> {
    const response = await fetch(`${API_BASE}/routes/${routeId}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ segment_length_m: 100, savgol_window: 5 }),
    });

    if (!response.ok)
      throw new Error(`Processing failed: ${await parseApiError(response)}`);
    return response.json() as Promise<ProcessResponse>;
  }

  async function analyzeBiomechanics(
    routeId: string,
    profile: HikerProfile,
  ): Promise<BiomechanicalResponse> {
    const response = await fetch(
      `${API_BASE}/routes/${routeId}/biomechanical`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, velocity_model: "tobler" }),
      },
    );

    if (!response.ok)
      throw new Error(
        `Biomechanical analysis failed: ${await parseApiError(response)}`,
      );
    return response.json() as Promise<BiomechanicalResponse>;
  }

  async function runSimulation(
    climate: SimulationScenario | ClimateOverride,
  ): Promise<void> {
    if (!analysis.value) {
      error.value = "Primero carga y analiza una ruta.";
      return;
    }

    isLoading.value = true;
    error.value = null;
    try {
      const body =
        typeof climate === "string"
          ? { scenario: climate, profile: currentProfile.value ?? undefined }
          : { climate, profile: currentProfile.value ?? undefined };
      const response = await fetch(
        `${API_BASE}/routes/${analysis.value.route_id}/simulate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );

      if (!response.ok)
        throw new Error(`Simulation failed: ${await parseApiError(response)}`);

      const simulated = (await response.json()) as BiomechanicalResponse;
      analysis.value = {
        ...analysis.value,
        summary: {
          ...analysis.value.summary,
          total_distance_km: simulated.summary.total_distance_km,
          elevation_gain_m: simulated.summary.elevation_gain_m,
          elevation_loss_m: simulated.summary.elevation_loss_m,
          estimated_time_h: simulated.summary.estimated_time_h,
          total_kcal: simulated.summary.total_kcal,
          high_confidence_segments_pct:
            simulated.summary.high_confidence_segments_pct,
          time_to_severe_fatigue_h: simulated.summary.time_to_severe_fatigue_h,
          ccr: simulated.summary.ccr,
          mide_global: simulated.summary.mide_global,
          mide_dimensions: simulated.summary.mide_dimensions,
          climate_source: simulated.summary.climate_source,
          climate_timestamp: simulated.summary.climate_timestamp,
        },
        segments: simulated.segments.map((segment) => mapBackendSegment(segment)),
      };
      isSimulationMode.value = true;
    } catch (err) {
      error.value =
        err instanceof Error ? err.message : "Error desconocido al simular clima";
      isSimulationMode.value = false;
    } finally {
      isLoading.value = false;
    }
  }

  async function refreshRealClimate(): Promise<void> {
    if (!analysis.value) return;

    isLoading.value = true;
    error.value = null;
    try {
      const simulated = await analyzeBiomechanics(
        analysis.value.route_id,
        currentProfile.value ?? {
          weight_kg: 70,
          load_kg: 10,
          fitness_level: "medium",
        },
      );
      analysis.value = {
        ...analysis.value,
        summary: {
          ...analysis.value.summary,
          total_distance_km: simulated.summary.total_distance_km,
          elevation_gain_m: simulated.summary.elevation_gain_m,
          elevation_loss_m: simulated.summary.elevation_loss_m,
          estimated_time_h: simulated.summary.estimated_time_h,
          total_kcal: simulated.summary.total_kcal,
          high_confidence_segments_pct:
            simulated.summary.high_confidence_segments_pct,
          time_to_severe_fatigue_h: simulated.summary.time_to_severe_fatigue_h,
          ccr: simulated.summary.ccr,
          mide_global: simulated.summary.mide_global,
          mide_dimensions: simulated.summary.mide_dimensions,
          climate_source: simulated.summary.climate_source,
          climate_timestamp: simulated.summary.climate_timestamp,
        },
        segments: simulated.segments.map((segment) => mapBackendSegment(segment)),
      };
      isSimulationMode.value = false;
    } catch (err) {
      error.value =
        err instanceof Error
          ? err.message
          : "Error desconocido al volver a clima real";
    } finally {
      isLoading.value = false;
    }
  }

  function selectSegment(seq: number | null): void {
    selectedSegmentSeq.value = seq;
  }

  function reset(): void {
    analysis.value = null;
    error.value = null;
    selectedSegmentSeq.value = null;
    isSimulationMode.value = false;
    currentProfile.value = null;
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
    refreshRealClimate,
    selectSegment,
    reset,
  };
});
