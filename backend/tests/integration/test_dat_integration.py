"""
Integration tests for DAT — Route Ingestion API.
Verifies HTTP endpoints against the database.
"""

from __future__ import annotations

import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Route, Segment


@pytest.mark.asyncio
async def test_upload_route_geojson_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Prepare a mock GeoJSON file with elevation (3D)
    geojson_data = {
        "type": "Feature",
        "properties": {"name": "Senda del Puma"},
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-79.5000, 9.0000, 100.0],
                [-79.5005, 9.0005, 150.0],
                [-79.5010, 9.0010, 200.0],
            ],
        },
    }
    file_bytes = json.dumps(geojson_data).encode("utf-8")

    # 2. Upload file via the POST /api/v1/routes/upload endpoint
    files = {"file": ("puma.geojson", file_bytes, "application/json")}
    response = await client.post("/api/v1/routes/upload", files=files)

    # 3. Assert HTTP response
    assert response.status_code == 201
    data = response.json()
    assert "route_id" in data
    assert data["name"] == "Senda del Puma"
    assert data["source_format"] == "geojson"
    assert data["segment_count"] > 0
    assert data["total_length_m"] > 0

    route_id = uuid.UUID(data["route_id"])

    # 4. Assert data was written to the PostgreSQL / PostGIS database
    result = await db_session.execute(
        select(Route)
        .where(Route.id == route_id)
        .options(selectinload(Route.segments))
    )
    route_db = result.scalar_one_or_none()
    assert route_db is not None
    assert route_db.name == "Senda del Puma"
    assert route_db.source_format == "geojson"

    # Verify segments exist in DB and have geometries
    assert len(route_db.segments) == data["segment_count"]
    for segment in route_db.segments:
        assert segment.geom is not None
        assert segment.length_m > 0
        assert segment.slope_pct is not None
        # Verify elevation columns were populated
        assert segment.elevation_start is not None
        assert segment.elevation_end is not None


@pytest.mark.asyncio
async def test_upload_unsupported_format(client: AsyncClient) -> None:
    files = {"file": ("puma.txt", b"random content", "text/plain")}
    response = await client.post("/api/v1/routes/upload", files=files)
    assert response.status_code == 415
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_invalid_geojson(client: AsyncClient) -> None:
    files = {"file": ("puma.geojson", b"{invalid json}", "application/json")}
    response = await client.post("/api/v1/routes/upload", files=files)
    assert response.status_code == 422
    assert "Invalid JSON" in response.json()["detail"]
