"""
SIM — Simulation scenarios (SIM-03).
Predefined climate scenarios that override API data.
"""

from app.modules.cli.schemas import ClimateOverride


# SIM-03: predefined named scenarios
SCENARIOS: dict[str, ClimateOverride] = {
    "dry": ClimateOverride(temperature_c=25, humidity_pct=30, precip_mm=0, uv_index=5),
    "light_rain": ClimateOverride(temperature_c=18, humidity_pct=75, precip_mm=8, uv_index=2),
    "heavy_rain": ClimateOverride(temperature_c=15, humidity_pct=95, precip_mm=35, uv_index=1),
    "extreme_heat": ClimateOverride(temperature_c=40, humidity_pct=60, precip_mm=0, uv_index=11),
    "night": ClimateOverride(temperature_c=12, humidity_pct=65, precip_mm=0, uv_index=0),
}


def resolve_simulation_climate(
    scenario: str | None = None,
    override: ClimateOverride | None = None,
) -> ClimateOverride:
    """Resolve manual climate override, preferring explicit values over scenario. SIM-01, SIM-03"""
    if override is not None:
        return override
    if scenario is None:
        raise ValueError("Either scenario or climate override is required.")
    try:
        return SCENARIOS[scenario]
    except KeyError as exc:
        raise ValueError(f"Unknown simulation scenario: {scenario}") from exc
