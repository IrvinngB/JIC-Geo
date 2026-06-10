"""
Biomechanical analysis endpoint — integrates VEL + MET + PRF with segments.
Phase 3: Motor Biomecánico.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.modules.met.service import minetti_cot, pandolf_metabolic_rate, terrain_eta
from app.modules.prf.schemas import HikerProfile
from app.modules.prf.service import velocity_factor
from app.modules.rut import repository as rut_repo
from app.modules.rut.schemas import SegmentProcessedOut
from app.modules.vel.service import VelocityModel, calculate_velocity

router = APIRouter()


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
    time_min: float
    kcal: float


class BiomechanicalSummary(BaseModel):
    """Route-level biomechanical summary."""

    total_distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float
    estimated_time_h: float
    total_kcal: float
    high_confidence_segments_pct: float
    mide_effort_level: int  # 1-5 based on total effort


class BiomechanicalRequest(BaseModel):
    """Input for biomechanical analysis."""

    profile: HikerProfile = Field(default_factory=HikerProfile)
    velocity_model: VelocityModel = VelocityModel.TOBLER
    segment_length_m: float = Field(default=settings.segment_length_m, gt=0)


class BiomechanicalResponse(BaseModel):
    """Full biomechanical analysis response."""

    route_id: uuid.UUID
    summary: BiomechanicalSummary
    segments: list[BiomechanicalSegmentOut]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/{route_id}/biomechanical", response_model=BiomechanicalResponse)
async def analyze_biomechanical(
    route_id: str,
    payload: BiomechanicalRequest,
    db: AsyncSession = Depends(get_db),
) -> BiomechanicalResponse:
    """
    Analyze a route using the biomechanical engine (VEL + MET + PRF).

    - Calculates velocity per segment (Tobler or Irmischer-Clarke).
    - Applies off-path and Langmuir corrections.
    - Adjusts for hiker fitness level.
    - Computes metabolic cost (Minetti + Pandolf).
    - Returns segment-level and route-level summaries.
    """
    try:
        route_uuid = uuid.UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        )

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

    profile = payload.profile
    v_factor = velocity_factor(profile)
    eta = terrain_eta("dirt")  # default until surface_type is user-editable

    segments_out: list[BiomechanicalSegmentOut] = []
    total_kcal = 0.0
    total_time_h = 0.0
    total_distance_km = 0.0
    elevation_gain = 0.0
    elevation_loss = 0.0
    exact_segments = 0

    for seg in segments_db:
        slope = seg.slope_pct or 0.0
        length_m = seg.length_m or 0.0
        length_km = length_m / 1000.0

        # Velocity
        velocity_kmh = calculate_velocity(
            slope=slope,
            model=payload.velocity_model,
            is_on_path=True,
            apply_langmuir_correction=True,
        )
        velocity_kmh *= v_factor

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

        # Eccentric fatigue
        is_eccentric = slope < -0.10

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
                time_min=round(time_min, 2),
                kcal=round(kcal, 1),
            )
        )

    high_confidence_pct = (
        (exact_segments / len(segments_db)) * 100 if segments_db else 0
    )

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

    summary = BiomechanicalSummary(
        total_distance_km=round(total_distance_km, 2),
        elevation_gain_m=round(elevation_gain, 1),
        elevation_loss_m=round(elevation_loss, 1),
        estimated_time_h=round(total_time_h, 2),
        total_kcal=round(total_kcal, 1),
        high_confidence_segments_pct=round(high_confidence_pct, 1),
        mide_effort_level=effort_level,
    )

    return BiomechanicalResponse(
        route_id=route_uuid,
        summary=summary,
        segments=segments_out,
    )
