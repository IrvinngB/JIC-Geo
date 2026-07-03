"""CLI repository — climate API and climate zone persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.cli.schemas import ClimateData, ClimateTimeline
from app.modules.cli.service import (
    grid_zone_id,
    normalize_open_meteo_forecast,
    normalize_open_meteo_payload,
)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_open_meteo(lat: float, lon: float) -> ClimateData:
    """Fetch current weather from Open-Meteo. CLI-01"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "uv_index",
                "shortwave_radiation",
            ]
        ),
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
    return normalize_open_meteo_payload(response.json(), lat=lat, lon=lon)


async def fetch_open_meteo_forecast(
    lat: float,
    lon: float,
    *,
    start: datetime,
    forecast_hours: int = 36,
) -> ClimateTimeline:
    """Fetch an hourly forecast window covering the hike from Open-Meteo. CLI-10.

    `forecast_hours` bounds the window after `start`; Open-Meteo serves up to
    16 days ahead, beyond that the request fails and the caller falls back.
    """
    end = start + timedelta(hours=forecast_hours)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "uv_index",
                "shortwave_radiation",
            ]
        ),
        "timezone": "UTC",
        "start_date": start.astimezone(timezone.utc).date().isoformat(),
        "end_date": end.astimezone(timezone.utc).date().isoformat(),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
    return normalize_open_meteo_forecast(response.json(), lat=lat, lon=lon, start=start)


async def get_cached_climate(
    db: AsyncSession,
    lat: float,
    lon: float,
    ttl_seconds: int | None = None,
) -> ClimateData | None:
    """Return cached climate data for a grid cell if fresh. CLI-07"""
    ttl = ttl_seconds or settings.climate_api_ttl_seconds
    zone_id = grid_zone_id(lat, lon)
    result = await db.execute(
        text(
            """
            SELECT zone_id, wbgt, precip_mm, uv_index, temperature_c, humidity_pct, source, updated_at
            FROM climate_zones
            WHERE zone_id = :zone_id
              AND updated_at >= :fresh_after
            """
        ),
        {
            "zone_id": zone_id,
            "fresh_after": datetime.now(timezone.utc) - timedelta(seconds=ttl),
        },
    )
    row = result.mappings().one_or_none()
    if row is None:
        return None
    return ClimateData(
        temperature_c=row["temperature_c"],
        humidity_pct=row["humidity_pct"],
        precip_mm=row["precip_mm"],
        uv_index=row["uv_index"],
        wbgt=row["wbgt"],
        source=row["source"],
        timestamp=row["updated_at"],
        zone_id=row["zone_id"],
    )


async def upsert_climate_zone(
    db: AsyncSession,
    climate: ClimateData,
    lat: float,
    lon: float,
) -> None:
    """Persist current climate in a small grid-cell polygon. CLI-07, GRF-08"""
    zone_id = climate.zone_id or grid_zone_id(lat, lon)
    delta = 0.01
    await db.execute(
        text(
            """
            INSERT INTO climate_zones (
                zone_id, geom, wbgt, precip_mm, uv_index,
                temperature_c, humidity_pct, source, updated_at
            )
            VALUES (
                :zone_id,
                ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326),
                :wbgt, :precip_mm, :uv_index,
                :temperature_c, :humidity_pct, :source, :updated_at
            )
            ON CONFLICT (zone_id) DO UPDATE SET
                geom = EXCLUDED.geom,
                wbgt = EXCLUDED.wbgt,
                precip_mm = EXCLUDED.precip_mm,
                uv_index = EXCLUDED.uv_index,
                temperature_c = EXCLUDED.temperature_c,
                humidity_pct = EXCLUDED.humidity_pct,
                source = EXCLUDED.source,
                updated_at = EXCLUDED.updated_at
            """
        ),
        {
            "zone_id": zone_id,
            "min_lon": lon - delta,
            "min_lat": lat - delta,
            "max_lon": lon + delta,
            "max_lat": lat + delta,
            "wbgt": climate.wbgt,
            "precip_mm": climate.precip_mm,
            "uv_index": climate.uv_index,
            "temperature_c": climate.temperature_c,
            "humidity_pct": climate.humidity_pct,
            "source": climate.source,
            "updated_at": climate.timestamp,
        },
    )


async def get_route_centroid(db: AsyncSession, route_id: str) -> tuple[float, float] | None:
    """Return (lat, lon) centroid for a persisted route."""
    result = await db.execute(
        text(
            """
            SELECT ST_Y(ST_Centroid(geom)) AS lat, ST_X(ST_Centroid(geom)) AS lon
            FROM routes
            WHERE id = :route_id
            """
        ),
        {"route_id": route_id},
    )
    row = result.mappings().one_or_none()
    if row is None or row["lat"] is None or row["lon"] is None:
        return None
    return float(row["lat"]), float(row["lon"])
