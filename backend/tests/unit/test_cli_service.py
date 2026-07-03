from datetime import datetime, timezone

from app.modules.cli.schemas import ClimateOverride
from app.modules.cli.service import (
    calculate_wbgt,
    climate_at,
    climate_cost_multiplier,
    climate_from_override,
    cardiovascular_drift_multiplier,
    constant_timeline,
    normalize_open_meteo_forecast,
)


def _forecast_payload(hours: int, base_temp: float = 20.0) -> dict:
    times = [f"2026-07-04T{h:02d}:00" for h in range(hours)]
    return {
        "elevation": 800.0,
        "hourly": {
            "time": times,
            "temperature_2m": [base_temp + h for h in range(hours)],
            "relative_humidity_2m": [50.0] * hours,
            "precipitation": [0.0] * hours,
            "uv_index": [5.0] * hours,
            "shortwave_radiation": [400.0] * hours,
        },
    }


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


def test_forecast_normalization_skips_hours_before_start() -> None:
    start = datetime(2026, 7, 4, 8, 30, tzinfo=timezone.utc)
    timeline = normalize_open_meteo_forecast(_forecast_payload(12), lat=19.4, lon=-99.1, start=start)

    # 08:30 floors to 08:00 → hours 08..11 remain
    assert len(timeline.hours) == 4
    assert timeline.hours[0].timestamp.hour == 8
    assert timeline.hours[0].source == "forecast"
    assert timeline.reference_elevation_m == 800.0


def test_climate_at_picks_hour_by_elapsed_time() -> None:
    start = datetime(2026, 7, 4, 0, 0, tzinfo=timezone.utc)
    timeline = normalize_open_meteo_forecast(_forecast_payload(6), lat=19.4, lon=-99.1, start=start)

    assert climate_at(timeline, elapsed_min=0).temperature_c == 20.0
    assert climate_at(timeline, elapsed_min=59).temperature_c == 20.0
    assert climate_at(timeline, elapsed_min=60).temperature_c == 21.0
    assert climate_at(timeline, elapsed_min=150).temperature_c == 22.0


def test_climate_at_clamps_to_last_forecast_hour() -> None:
    start = datetime(2026, 7, 4, 0, 0, tzinfo=timezone.utc)
    timeline = normalize_open_meteo_forecast(_forecast_payload(3), lat=19.4, lon=-99.1, start=start)

    assert climate_at(timeline, elapsed_min=600).temperature_c == 22.0


def test_climate_at_applies_lapse_rate_above_reference() -> None:
    start = datetime(2026, 7, 4, 0, 0, tzinfo=timezone.utc)
    timeline = normalize_open_meteo_forecast(_forecast_payload(3), lat=19.4, lon=-99.1, start=start)

    # 1000 m above the 800 m reference → -6.5 degC
    high = climate_at(timeline, elapsed_min=0, elevation_m=1800.0)
    assert high.temperature_c == 13.5
    assert high.wbgt < timeline.hours[0].wbgt


def test_constant_timeline_ignores_elevation() -> None:
    climate = climate_from_override(
        ClimateOverride(temperature_c=25, humidity_pct=50, precip_mm=0, uv_index=3)
    )
    timeline = constant_timeline(climate, datetime(2026, 7, 4, tzinfo=timezone.utc))

    assert climate_at(timeline, elapsed_min=300, elevation_m=2500.0) == climate
