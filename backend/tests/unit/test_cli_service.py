from app.modules.cli.schemas import ClimateOverride
from app.modules.cli.service import (
    calculate_wbgt,
    climate_cost_multiplier,
    climate_from_override,
    cardiovascular_drift_multiplier,
)


def test_wbgt_increases_with_heat_and_humidity() -> None:
    mild = calculate_wbgt(25, 40, uv_index=3, shortwave_radiation_w_m2=200)
    tropical = calculate_wbgt(35, 85, uv_index=10, shortwave_radiation_w_m2=850)

    assert tropical > mild
    assert tropical > 28


def test_climate_cost_multiplier_caps_at_three() -> None:
    multiplier = climate_cost_multiplier(
        wbgt=60,
        precip_mm=80,
        slope_pct=-0.4,
        canopy_density=0,
    )

    assert multiplier == 3.0


def test_cardiovascular_drift_after_twenty_minutes() -> None:
    assert cardiovascular_drift_multiplier(10, 32) == 1.0
    assert cardiovascular_drift_multiplier(60, 32) > 1.0


def test_climate_from_override_marks_simulation() -> None:
    climate = climate_from_override(
        ClimateOverride(temperature_c=40, humidity_pct=60, precip_mm=0, uv_index=11)
    )

    assert climate.source == "simulation"
    assert climate.wbgt > 28
