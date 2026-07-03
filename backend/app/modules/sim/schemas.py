"""Pydantic schemas for SIM — climate simulation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.cli.schemas import ClimateOverride
from app.modules.prf.schemas import HikerProfile
from app.modules.vel.service import VelocityModel

SimulationScenario = Literal["dry", "light_rain", "heavy_rain", "extreme_heat", "night"]


class SimulationRequest(BaseModel):
    """Request body for route climate simulation. SIM-01, SIM-03, SIM-04"""

    scenario: SimulationScenario | None = None
    climate: ClimateOverride | None = None
    compare_with_real: bool = False
    profile: HikerProfile = Field(default_factory=HikerProfile)
    velocity_model: VelocityModel = VelocityModel.IRMISCHER_CLARKE
    start_datetime: datetime | None = Field(
        default=None,
        description="Hike start (UTC); keeps the real-climate baseline aligned with the analysis (CLI-10).",
    )
