/**
 * Pinia store — route analysis state.
 * Uses the Phase 1–3 backend flow:
 * upload → process → biomechanical analysis.
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
  mide_global: number;
  mide_dimensions: MideDimensions;
  climate_source: "pending" | "api" | "simulation";
  climate_timestamp: string | null;
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
  geom?: LineString;
}

export interface RouteAnalysis {
  route_id: string;
  route_name: string | null;
  source_format: string;
  summary: RouteSummary;
  segments: Segment[];
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

function calculateRiskScore(
  segment: BiomechanicalResponse["segments"][number],
): number {
  const slopeRisk = Math.min(Math.abs(segment.slope_pct) * 140, 45);
  const metabolicRisk = Math.min(segment.metabolic_rate_w / 12, 35);
  const fatigueRisk = segment.is_eccentric_fatigue ? 15 : 0;
  const offPathRisk = segment.is_on_path ? 0 : 10;
  return Math.min(
    100,
    Math.round(slopeRisk + metabolicRisk + fatigueRisk + offPathRisk),
  );
}

function markTopRiskSegments(segments: Segment[]): Segment[] {
  if (segments.length === 0) return segments;

  const topCount = Math.max(1, Math.ceil(segments.length * 0.1));
  const topSeqs = new Set(
    [...segments]
      .sort((a, b) => b.risk_score - a.risk_score)
      .slice(0, topCount)
      .map((segment) => segment.seq),
  );

  return segments.map((segment) => ({
    ...segment,
    is_top_risk: topSeqs.has(segment.seq),
  }));
}

export const useRouteStore = defineStore("route", () => {
  const analysis = ref<RouteAnalysis | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const selectedSegmentSeq = ref<number | null>(null);
  const isSimulationMode = ref(false);

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

      const segments = markTopRiskSegments(
        biomechanical.segments.map((segment) => ({
          ...segment,
          geom: segment.geom ?? undefined,
          risk_score: calculateRiskScore(segment),
          is_top_risk: false,
        })),
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
          mide_global: biomechanical.summary.mide_effort_level,
          mide_dimensions: {
            severity: 1,
            orientation: 1,
            displacement: Math.min(
              5,
              Math.max(1, Math.ceil(maxAbsSlope(segments) / 0.1)),
            ),
            effort: biomechanical.summary.mide_effort_level,
          },
          climate_source: "pending",
          climate_timestamp: null,
        },
        segments: segments.map((segment) => ({
          ...segment,
          is_eccentric_fatigue:
            segment.is_eccentric_fatigue ||
            Boolean(interpolatedBySeq.get(segment.seq)),
        })),
      };
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
    _scenario: SimulationScenario | object,
  ): Promise<void> {
    error.value =
      "El modo simulación depende de Fase 4/7 y todavía no está disponible.";
    isSimulationMode.value = false;
  }

  function selectSegment(seq: number | null): void {
    selectedSegmentSeq.value = seq;
  }

  function reset(): void {
    analysis.value = null;
    error.value = null;
    selectedSegmentSeq.value = null;
    isSimulationMode.value = false;
  }

  function maxAbsSlope(segments: Segment[]): number {
    return Math.max(
      0,
      ...segments.map((segment) => Math.abs(segment.slope_pct)),
    );
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
  };
});
