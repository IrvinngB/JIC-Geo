"""
SIM — Simulation scenarios (SIM-03).
Predefined climate scenarios that override API data.
"""

from pydantic import BaseModel


class ClimateData(BaseModel):
    temperature_c: float
    humidity_pct: float
    precip_mm: float
    uv_index: float


# SIM-03: predefined named scenarios
SCENARIOS: dict[str, ClimateData] = {
    "dry": ClimateData(temperature_c=25, humidity_pct=30, precip_mm=0, uv_index=5),
    "light_rain": ClimateData(temperature_c=18, humidity_pct=75, precip_mm=8, uv_index=2),
    "heavy_rain": ClimateData(temperature_c=15, humidity_pct=95, precip_mm=35, uv_index=1),
    "extreme_heat": ClimateData(temperature_c=40, humidity_pct=60, precip_mm=0, uv_index=11),
    "night": ClimateData(temperature_c=12, humidity_pct=65, precip_mm=0, uv_index=0),
}
