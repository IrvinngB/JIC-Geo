"""CLI service — pure climate calculations and cache helpers."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from app.modules.cli.schemas import ClimateData, ClimateOverride, ClimateTimeline

WBGT_CRITICAL_C = 28.0
PRECIP_FRICTION_MM = 5.0
DESCENT_FRICTION_SLOPE = -0.1763  # tan(-10 degrees)
LOW_CANOPY_THRESHOLD = 0.2
LAPSE_RATE_C_PER_M = 0.0065  # standard atmosphere: -6.5 degC per km of ascent


def grid_zone_id(lat: float, lon: float, precision: int = 2) -> str:
    """Return a stable cache key for climate data near a coordinate. CLI-07"""
    return f"grid:{round(lat, precision):.{precision}f}:{round(lon, precision):.{precision}f}"


def approximate_wet_bulb_c(temperature_c: float, humidity_pct: float) -> float:
    """
    Approximate wet-bulb temperature in Celsius using Stull's formula. CLI-02

    Valid enough for outdoor heat-stress screening when direct wet-bulb data is
    unavailable from free weather APIs.
    """
    rh = max(1.0, min(100.0, humidity_pct))
    t = temperature_c
    return (
        t * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(t + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * rh**1.5 * math.atan(0.023101 * rh)
        - 4.686035
    )


def approximate_globe_temperature_c(
    temperature_c: float,
    shortwave_radiation_w_m2: float | None,
    uv_index: float,
) -> float:
    """Approximate black-globe temperature from solar load. CLI-02"""
    radiation = max(0.0, shortwave_radiation_w_m2 or 0.0)
    uv_heat = max(0.0, uv_index - 3.0) * 0.25
    return temperature_c + min(12.0, radiation / 120.0 + uv_heat)


def calculate_wbgt(
    temperature_c: float,
    humidity_pct: float,
    uv_index: float,
    shortwave_radiation_w_m2: float | None = None,
) -> float:
    """Return WBGT in Celsius. CLI-02"""
    tw = approximate_wet_bulb_c(temperature_c, humidity_pct)
    tg = approximate_globe_temperature_c(temperature_c, shortwave_radiation_w_m2, uv_index)
    return (0.7 * tw) + (0.2 * tg) + (0.1 * temperature_c)


def normalize_open_meteo_payload(payload: dict, lat: float, lon: float) -> ClimateData:
    """Convert Open-Meteo current payload into internal climate data. CLI-01, CLI-08"""
    current = payload.get("current") or {}
    temperature = float(current.get("temperature_2m", 25.0))
    humidity = float(current.get("relative_humidity_2m", 50.0))
    precip = float(current.get("precipitation", 0.0))
    uv_index = float(current.get("uv_index", 0.0))
    radiation = current.get("shortwave_radiation")
    timestamp_raw = current.get("time")
    timestamp = (
        datetime.fromisoformat(str(timestamp_raw)).replace(tzinfo=timezone.utc)
        if timestamp_raw
        else datetime.now(timezone.utc)
    )
    return ClimateData(
        temperature_c=temperature,
        humidity_pct=humidity,
        precip_mm=precip,
        uv_index=uv_index,
        wbgt=round(calculate_wbgt(temperature, humidity, uv_index, radiation), 2),
        source="api",
        timestamp=timestamp,
        zone_id=grid_zone_id(lat, lon),
    )


def normalize_open_meteo_forecast(
    payload: dict,
    lat: float,
    lon: float,
    start: datetime,
) -> ClimateTimeline:
    """Convert an Open-Meteo hourly forecast into a ClimateTimeline. CLI-10.

    Keeps only hours at or after `start` (floored to the hour) so that index N
    in the timeline is the climate N hours into the hike.
    """
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    temperatures = hourly.get("temperature_2m") or []
    humidities = hourly.get("relative_humidity_2m") or []
    precips = hourly.get("precipitation") or []
    uv_indexes = hourly.get("uv_index") or []
    radiations = hourly.get("shortwave_radiation") or []

    floor_start = start.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    zone_id = grid_zone_id(lat, lon)

    hours: list[ClimateData] = []
    for i, time_raw in enumerate(times):
        hour_ts = datetime.fromisoformat(str(time_raw)).replace(tzinfo=timezone.utc)
        if hour_ts < floor_start:
            continue
        temperature = float(temperatures[i])
        humidity = float(humidities[i])
        uv_index = max(0.0, float(uv_indexes[i] if uv_indexes[i] is not None else 0.0))
        radiation = float(radiations[i]) if i < len(radiations) and radiations[i] is not None else None
        hours.append(
            ClimateData(
                temperature_c=temperature,
                humidity_pct=humidity,
                precip_mm=max(0.0, float(precips[i])),
                uv_index=uv_index,
                wbgt=round(calculate_wbgt(temperature, humidity, uv_index, radiation), 2),
                source="forecast",
                timestamp=hour_ts,
                zone_id=zone_id,
                shortwave_radiation_w_m2=radiation,
            )
        )

    if not hours:
        raise ValueError("Forecast payload has no hours at or after the hike start")

    elevation = payload.get("elevation")
    return ClimateTimeline(
        start=floor_start,
        hours=hours,
        reference_elevation_m=float(elevation) if elevation is not None else None,
    )


def constant_timeline(climate: ClimateData, start: datetime) -> ClimateTimeline:
    """Wrap a single climate observation as a timeline (override/fallback paths).

    No reference elevation: constant climates represent user-fixed or unknown
    conditions, so no lapse-rate adjustment is applied.
    """
    return ClimateTimeline(start=start, hours=[climate], reference_elevation_m=None)


def climate_at(
    timeline: ClimateTimeline,
    elapsed_min: float,
    elevation_m: float | None = None,
) -> ClimateData:
    """Return the climate for a segment reached `elapsed_min` into the hike. CLI-10.

    Picks the forecast hour by elapsed time (clamped to the last available hour)
    and, when both elevations are known, corrects temperature by the standard
    lapse rate and recomputes WBGT accordingly.
    """
    index = min(int(max(0.0, elapsed_min) // 60), len(timeline.hours) - 1)
    base = timeline.hours[index]

    if elevation_m is None or timeline.reference_elevation_m is None:
        return base

    delta_m = elevation_m - timeline.reference_elevation_m
    temperature = base.temperature_c - LAPSE_RATE_C_PER_M * delta_m
    return base.model_copy(
        update={
            "temperature_c": round(temperature, 2),
            "wbgt": round(
                calculate_wbgt(
                    temperature,
                    base.humidity_pct,
                    base.uv_index,
                    base.shortwave_radiation_w_m2,
                ),
                2,
            ),
        }
    )


def climate_from_override(override: ClimateOverride) -> ClimateData:
    """Build simulated climate data from manually supplied values. SIM-01, SIM-02"""
    return ClimateData(
        temperature_c=override.temperature_c,
        humidity_pct=override.humidity_pct,
        precip_mm=override.precip_mm,
        uv_index=override.uv_index,
        wbgt=round(
            calculate_wbgt(
                override.temperature_c,
                override.humidity_pct,
                override.uv_index,
                shortwave_radiation_w_m2=override.uv_index * 90.0,
            ),
            2,
        ),
        source="simulation",
        timestamp=datetime.now(timezone.utc),
    )


def climate_cost_multiplier(
    wbgt: float,
    precip_mm: float,
    slope_pct: float,
    canopy_density: float,
    cap: float = 3.0,
) -> float:
    """Return bounded climate multiplier for graph/risk costs. CLI-04, CLI-05, CLI-06, GRF-10"""
    multiplier = 1.0
    if wbgt > WBGT_CRITICAL_C:
        multiplier *= 1.0 + 0.05 * (wbgt - WBGT_CRITICAL_C)
    if precip_mm > PRECIP_FRICTION_MM and slope_pct < DESCENT_FRICTION_SLOPE:
        multiplier *= 1.35
    if canopy_density < LOW_CANOPY_THRESHOLD and wbgt > 30.0:
        multiplier *= 1.15
    return round(min(multiplier, cap), 4)


SOFT_SURFACES = {"mud", "sand", "scrub", "dense_scrub", "sand_mud"}


def velocity_rain_factor(
    precip_mm: float,
    surface_type: str,
    min_factor: float = 0.5,
) -> float:
    """Return a velocity multiplier for rain conditions. CLI-09

    Curve: max(min_factor, 1.0 - 0.005 * precip_mm)
    Soft surfaces (mud, sand, scrub) amplify the degradation by 1.5x.

    Examples:
        precip=0  → 1.0 (no effect)
        precip=10 → 0.95 (dirt) / 0.925 (mud)
        precip=35 → 0.825 (dirt) / 0.738 (mud)
        precip=80 → 0.60 (dirt) / 0.50 (mud, hits floor)
    """
    if precip_mm <= 0.0:
        return 1.0

    degradation = 0.005 * precip_mm  # 5 mm → 2.5%, 35 mm → 17.5%
    if surface_type in SOFT_SURFACES:
        degradation *= 1.5  # amplify on soft ground

    return max(min_factor, round(1.0 - degradation, 4))


def cardiovascular_drift_multiplier(
    elapsed_time_min: float,
    wbgt: float,
    threshold_c: float = WBGT_CRITICAL_C,
) -> float:
    """Exponential time penalty after 20 minutes under heat stress. CLI-03, CLI-04"""
    if elapsed_time_min <= 20.0 or wbgt <= threshold_c:
        return 1.0
    heat_excess = wbgt - threshold_c
    exposure_h = (elapsed_time_min - 20.0) / 60.0
    return round(min(3.0, math.exp(0.045 * heat_excess * exposure_h)), 4)
