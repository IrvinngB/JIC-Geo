"""
Biomechanical analysis endpoint — integrates VEL + MET + PRF with segments.
Phase 3: Motor Biomecánico.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.modules.cli import repository as cli_repo
from app.modules.cli.schemas import ClimateData, ClimateOverride
from app.modules.cli.service import climate_from_override
from app.modules.dat import repository as dat_repo
from app.modules.dat import service as dat_service
from app.modules.met import repository as met_repo
from app.modules.met.service import (
    estimate_time_to_severe_fatigue_h,
    is_eccentric_fatigue,
    is_on_path_surface,
    minetti_cot,
    pandolf_metabolic_rate,
    terrain_eta,
)
from app.modules.prf.schemas import FitnessLevel, HikerProfile
from app.modules.prf.service import velocity_factor
from app.modules.rie import repository as rie_repo
from app.modules.rie.schemas import ClimateFactors, MideDimensions, RiskWeights
from app.modules.rie.service import (
    SegmentRiskInput,
    calculate_segment_risk,
    mark_top_risk,
    summarize_route_risk,
)
from app.modules.rut import repository as rut_repo
from app.modules.rut.router import run_rut_pipeline
from app.modules.sim.schemas import SimulationRequest
from app.modules.sim.service import resolve_simulation_climate
from app.modules.vel.service import VelocityModel, calculate_velocity

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BiomechanicalSegmentOut(BaseModel):
    """Per-segment biomechanical analysis."""

    seq: int
    slope_pct: float
    direction: str
    velocity_kmh: float
    velocity_model: str
    cot_j_per_kg_m: float
    cot_method: str
    metabolic_rate_w: float
    is_eccentric_fatigue: bool
    surface_type: str
    is_on_path: bool
    time_min: float
    kcal: float
    risk_score: int
    is_top_risk: bool
    mide_dimensions: MideDimensions | None = None
    climate_factors: ClimateFactors | None = None
    geom: dict[str, Any] | None = None


class BiomechanicalSummary(BaseModel):
    """Route-level biomechanical summary."""

    total_distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float
    estimated_time_h: float
    total_kcal: float
    high_confidence_segments_pct: float
    time_to_severe_fatigue_h: float | None
    mide_effort_level: int  # 1-5 based on total effort
    mide_global: int
    mide_dimensions: MideDimensions
    ccr: float
    climate_source: str
    climate_timestamp: str | None


class BiomechanicalRequest(BaseModel):
    """Input for biomechanical analysis."""

    profile: HikerProfile = Field(default_factory=HikerProfile)
    velocity_model: VelocityModel = VelocityModel.TOBLER
    segment_length_m: float = Field(default=settings.segment_length_m, gt=0)
    climate: ClimateOverride | None = None


class BiomechanicalResponse(BaseModel):
    """Full biomechanical analysis response."""

    route_id: uuid.UUID
    summary: BiomechanicalSummary
    segments: list[BiomechanicalSegmentOut]


class SimulationResponse(BaseModel):
    """SIM-04: simulated-climate result, optionally paired with the real-climate one.

    `real` is populated only when the request sets `compare_with_real=true`, so a
    single call returns both scenarios for side-by-side comparison.
    """

    simulated: BiomechanicalResponse
    real: BiomechanicalResponse | None = None


class SegmentRiskOut(BaseModel):
    """Persisted per-segment risk (API-03)."""

    seq: int
    risk_score: int
    is_top_risk: bool
    geom: dict[str, Any] | None = None


class RouteRiskResponse(BaseModel):
    """Current persisted risk index for a route. API-03, RIE-10."""

    route_id: uuid.UUID
    segment_count: int
    max_risk_score: int
    mean_risk_score: float
    top_risk_seqs: list[int]
    segments: list[SegmentRiskOut]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/{route_id}/biomechanical", response_model=BiomechanicalResponse)
async def analyze_biomechanical(
    route_id: str,
    payload: BiomechanicalRequest,
    db: AsyncSession = DB_DEPENDENCY,
) -> BiomechanicalResponse:
    """
    Analyze a route using the biomechanical engine (VEL + MET + PRF).

    - Calculates velocity per segment (Tobler or Irmischer-Clarke).
    - Applies off-path and Langmuir corrections.
    - Adjusts for hiker fitness level.
    - Computes metabolic cost (Minetti + Pandolf).
    - Returns segment-level and route-level summaries.
    """
    return await _analyze_route(db, route_id, payload)


@router.post("/{route_id}/simulate", response_model=SimulationResponse)
async def simulate_route(
    route_id: str,
    payload: SimulationRequest,
    db: AsyncSession = DB_DEPENDENCY,
) -> SimulationResponse:
    """Analyze a route with simulated climate. SIM-01 to SIM-04, API-04"""
    override = resolve_simulation_climate(payload.scenario, payload.climate)

    # SIM-04: when requested, compute the real-climate baseline FIRST so that the
    # persisted segment costs end in the simulated state the user is viewing.
    real_response: BiomechanicalResponse | None = None
    if payload.compare_with_real:
        real_request = BiomechanicalRequest(
            profile=payload.profile,
            velocity_model=payload.velocity_model,
            climate=None,
        )
        real_response = await _analyze_route(db, route_id, real_request)

    simulated_request = BiomechanicalRequest(
        profile=payload.profile,
        velocity_model=payload.velocity_model,
        climate=override,
    )
    simulated_response = await _analyze_route(db, route_id, simulated_request)

    return SimulationResponse(simulated=simulated_response, real=real_response)


@router.post("/analyze", response_model=BiomechanicalResponse, status_code=status.HTTP_201_CREATED)
async def analyze_route(
    file: UploadFile = File(..., description="GPX or GeoJSON route file"),
    weight_kg: float = Form(default=70.0, gt=0),
    load_kg: float = Form(default=10.0, ge=0),
    fitness_level: FitnessLevel = Form(default=FitnessLevel.MEDIUM),
    velocity_model: VelocityModel = Form(default=VelocityModel.TOBLER),
    segment_length_m: float = Form(default=settings.segment_length_m, gt=0),
    savgol_window: int = Form(default=5, gt=0),
    db: AsyncSession = DB_DEPENDENCY,
) -> BiomechanicalResponse:
    """API-01: upload + process + biomechanical analysis in a single request.

    Bundles what would otherwise be three calls (upload, process, biomechanical)
    so an API client can analyze a GPX/GeoJSON route in one round trip.
    """
    parsed = await dat_service.parse_upload(file)
    route = await dat_repo.save_route(
        db,
        name=parsed["name"],
        source_format=parsed["source_format"],
        geom_wkt=parsed["geom_wkt"],
        segments_data=parsed["segments_data"],
    )

    await run_rut_pipeline(
        db,
        route.id,
        segment_length_m=segment_length_m,
        window=savgol_window,
    )

    profile = HikerProfile(
        weight_kg=weight_kg,
        load_kg=load_kg,
        fitness_level=fitness_level,
    )
    request = BiomechanicalRequest(
        profile=profile,
        velocity_model=velocity_model,
        segment_length_m=segment_length_m,
    )
    return await _analyze_route(db, str(route.id), request)


@router.get("/{route_id}/risk", response_model=RouteRiskResponse)
async def get_route_risk(
    route_id: str,
    db: AsyncSession = DB_DEPENDENCY,
) -> RouteRiskResponse:
    """API-03: return the current persisted risk index for an analyzed route.

    Reads risk scores stored by the last analysis (no recomputation). Recomputes
    the top 10% riskiest segments (RIE-10) from the persisted scores.
    """
    try:
        route_uuid = uuid.UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        ) from None

    rows = await rie_repo.get_persisted_risk(db, route_uuid)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Route '{route_id}' has no persisted risk. "
                "Analyze it first via POST /routes/analyze or /routes/{id}/biomechanical."
            ),
        )

    scores_by_seq = {row["seq"]: row["risk_score"] for row in rows}
    top_risk_seqs = mark_top_risk(scores_by_seq)
    scores = [row["risk_score"] for row in rows]

    segments = [
        SegmentRiskOut(
            seq=row["seq"],
            risk_score=row["risk_score"],
            is_top_risk=row["seq"] in top_risk_seqs,
            geom=json.loads(row["geom_geojson"]) if row["geom_geojson"] else None,
        )
        for row in rows
    ]

    return RouteRiskResponse(
        route_id=route_uuid,
        segment_count=len(rows),
        max_risk_score=max(scores),
        mean_risk_score=round(sum(scores) / len(scores), 1),
        top_risk_seqs=sorted(top_risk_seqs),
        segments=segments,
    )


async def _resolve_climate(
    db: AsyncSession,
    route_uuid: uuid.UUID,
    override: ClimateOverride | None,
) -> ClimateData:
    if override is not None:
        return climate_from_override(override)

    centroid = await cli_repo.get_route_centroid(db, str(route_uuid))
    if centroid is None:
        return climate_from_override(
            ClimateOverride(temperature_c=25, humidity_pct=50, precip_mm=0, uv_index=3)
        )
    lat, lon = centroid
    cached = await cli_repo.get_cached_climate(db, lat, lon)
    if cached is not None:
        return cached
    try:
        climate = await cli_repo.fetch_open_meteo(lat, lon)
    except Exception:
        climate = climate_from_override(
            ClimateOverride(temperature_c=25, humidity_pct=50, precip_mm=0, uv_index=3)
        )
    await cli_repo.upsert_climate_zone(db, climate, lat, lon)
    return climate


async def _analyze_route(
    db: AsyncSession,
    route_id: str,
    payload: BiomechanicalRequest,
) -> BiomechanicalResponse:
    try:
        route_uuid = uuid.UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        ) from None

    route = await rut_repo.get_route_with_segments(db, route_uuid)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{route_id}' not found.",
        )

    # Ensure segments have been processed (RUT)
    segments_db = await rut_repo.get_segments_for_route(db, route_uuid)
    if not segments_db:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Route has no segments. Process the route first via POST /routes/{id}/process.",
        )

    segment_geojson_by_id = await rut_repo.get_segment_geojson_by_id(db, route_uuid)

    profile = payload.profile
    v_factor = velocity_factor(profile)

    climate = await _resolve_climate(db, route_uuid, payload.climate)
    risk_weights = RiskWeights(
        metabolic_cost=settings.ahp_metabolic_cost,
        velocity_degradation=settings.ahp_velocity_degradation,
        climate_stress=settings.ahp_climate_stress,
        terrain_friction=settings.ahp_terrain_friction,
    )

    segments_out: list[BiomechanicalSegmentOut] = []
    costs_to_persist: list[dict[str, Any]] = []
    risk_scores_by_segment_id: dict[int, int] = {}
    risk_scores_by_seq: dict[int, int] = {}
    total_kcal = 0.0
    total_time_h = 0.0
    total_distance_km = 0.0
    elevation_gain = 0.0
    elevation_loss = 0.0
    exact_segments = 0
    elapsed_time_min = 0.0
    off_path_count = 0

    for seg in segments_db:
        slope = seg.slope_pct or 0.0
        length_m = seg.length_m or 0.0
        length_km = length_m / 1000.0

        surface_type = seg.surface_type or "dirt"
        eta = terrain_eta(surface_type)
        is_on_path = is_on_path_surface(surface_type)

        # Velocity
        velocity_kmh = calculate_velocity(
            slope=slope,
            model=payload.velocity_model,
            is_on_path=is_on_path,
            apply_langmuir_correction=True,
        )
        velocity_kmh *= v_factor
        baseline_velocity_kmh = calculate_velocity(
            slope=slope,
            model=payload.velocity_model,
            is_on_path=True,
            apply_langmuir_correction=True,
        )

        # Time
        time_h = length_km / velocity_kmh if velocity_kmh > 0 else 0.0
        time_min = time_h * 60.0

        # MET: Minetti CoT
        cot, cot_method = minetti_cot(slope)
        cot_j_per_kg_m = cot

        # MET: Pandolf
        velocity_ms = (velocity_kmh * 1000.0) / 3600.0
        metabolic_rate_w = pandolf_metabolic_rate(
            weight_kg=profile.weight_kg,
            load_kg=profile.load_kg,
            velocity_ms=velocity_ms,
            slope_pct=slope,
            terrain_eta=eta,
        )

        # Energy (kcal)
        # total_energy_J = metabolic_rate_w * time_seconds
        # kcal = total_energy_J / 4184
        time_s = time_h * 3600.0
        total_energy_j = metabolic_rate_w * time_s
        kcal = total_energy_j / 4184.0

        # Dynamic costs for DAT-06 / MET persistence
        reverse_cot, _ = minetti_cot(-slope)
        costs_to_persist.append(
            {
                "segment_id": seg.id,
                "base_cost": cot_j_per_kg_m * length_m,
                "base_reverse_cost": reverse_cot * length_m,
                "velocity_kmh": velocity_kmh,
                "cot_j_per_kg_m": cot_j_per_kg_m,
                "cot_method": cot_method,
                "metabolic_rate_w": metabolic_rate_w,
                "risk_score": None,
            }
        )

        # Eccentric fatigue
        is_eccentric = is_eccentric_fatigue(slope)
        risk_score, climate_factors = calculate_segment_risk(
            SegmentRiskInput(
                seq=seg.seq,
                slope_pct=slope,
                velocity_kmh=velocity_kmh,
                baseline_velocity_kmh=baseline_velocity_kmh,
                cot_j_per_kg_m=cot_j_per_kg_m,
                metabolic_rate_w=metabolic_rate_w,
                elapsed_time_min=elapsed_time_min,
                segment_time_min=time_min,
                canopy_density=seg.canopy_density or 0.5,
                surface_type=surface_type,
                is_on_path=is_on_path,
                wbgt=climate.wbgt,
                precip_mm=climate.precip_mm,
                uv_index=climate.uv_index,
            ),
            risk_weights,
        )
        risk_scores_by_segment_id[seg.id] = risk_score
        risk_scores_by_seq[seg.seq] = risk_score

        # Accumulate
        total_kcal += kcal
        total_time_h += time_h
        total_distance_km += length_km
        if slope > 0:
            elevation_gain += length_m * slope
        else:
            elevation_loss += abs(length_m * slope)
        if cot_method == "exact":
            exact_segments += 1
        if not is_on_path:
            off_path_count += 1

        segments_out.append(
            BiomechanicalSegmentOut(
                seq=seg.seq,
                slope_pct=round(slope, 2),
                direction="ascent" if slope > 0 else "descent",
                velocity_kmh=round(velocity_kmh, 2),
                velocity_model=payload.velocity_model.value,
                cot_j_per_kg_m=round(cot_j_per_kg_m, 2),
                cot_method=cot_method,
                metabolic_rate_w=round(metabolic_rate_w, 1),
                is_eccentric_fatigue=is_eccentric,
                surface_type=surface_type,
                is_on_path=is_on_path,
                time_min=round(time_min, 2),
                kcal=round(kcal, 1),
                risk_score=risk_score,
                is_top_risk=False,
                climate_factors=climate_factors,
                geom=json.loads(segment_geojson_by_id[seg.id])
                if seg.id in segment_geojson_by_id
                else None,
            )
        )
        elapsed_time_min += time_min

    high_confidence_pct = (exact_segments / len(segments_db)) * 100 if segments_db else 0
    time_to_severe_fatigue_h = estimate_time_to_severe_fatigue_h(
        weight_kg=profile.weight_kg,
        fitness_level=profile.fitness_level.value,
        total_kcal=total_kcal,
        elapsed_time_h=total_time_h,
    )

    await met_repo.upsert_segment_costs(db, costs_to_persist)
    await rie_repo.update_segment_risk_scores(db, risk_scores_by_segment_id)

    # MIDE effort level: map estimated time to 1-5 scale
    # <1h → 1, 1-3h → 2, 3-5h → 3, 5-8h → 4, >8h → 5
    effort_level = 1
    if total_time_h < 1:
        effort_level = 1
    elif total_time_h < 3:
        effort_level = 2
    elif total_time_h < 5:
        effort_level = 3
    elif total_time_h < 8:
        effort_level = 4
    else:
        effort_level = 5

    top_risk_seqs = mark_top_risk(risk_scores_by_seq)
    off_path_ratio = off_path_count / len(segments_db) if segments_db else 0.0
    route_risk = summarize_route_risk(
        scores_by_seq=risk_scores_by_seq,
        max_abs_slope=max((abs(seg.slope_pct or 0.0) for seg in segments_db), default=0.0),
        off_path_ratio=off_path_ratio,
        total_time_h=total_time_h,
        wbgt=climate.wbgt,
        total_length_m=total_distance_km * 1000.0,
    )
    segments_out = [
        segment.model_copy(
            update={
                "is_top_risk": segment.seq in top_risk_seqs,
                "mide_dimensions": route_risk.mide_dimensions,
            }
        )
        for segment in segments_out
    ]

    summary = BiomechanicalSummary(
        total_distance_km=round(total_distance_km, 2),
        elevation_gain_m=round(elevation_gain, 1),
        elevation_loss_m=round(elevation_loss, 1),
        estimated_time_h=round(total_time_h, 2),
        total_kcal=round(total_kcal, 1),
        high_confidence_segments_pct=round(high_confidence_pct, 1),
        time_to_severe_fatigue_h=(
            round(time_to_severe_fatigue_h, 2) if time_to_severe_fatigue_h is not None else None
        ),
        mide_effort_level=effort_level,
        mide_global=route_risk.mide_global,
        mide_dimensions=route_risk.mide_dimensions,
        ccr=route_risk.ccr,
        climate_source=climate.source,
        climate_timestamp=climate.timestamp.isoformat() if climate.timestamp else None,
    )

    return BiomechanicalResponse(
        route_id=route_uuid,
        summary=summary,
        segments=segments_out,
    )
