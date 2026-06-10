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


@pytest.mark.asyncio
async def test_get_route_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Upload a route first
    geojson_data = {
        "type": "Feature",
        "properties": {"name": "Test Route for GET"},
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
    files = {"file": ("test.geojson", file_bytes, "application/json")}
    upload_response = await client.post("/api/v1/routes/upload", files=files)
    assert upload_response.status_code == 201
    route_id = upload_response.json()["route_id"]

    # 2. GET the route
    response = await client.get(f"/api/v1/routes/{route_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == route_id
    assert data["name"] == "Test Route for GET"
    assert data["source_format"] == "geojson"
    assert data["segment_count"] > 0
    assert len(data["segments"]) == data["segment_count"]


@pytest.mark.asyncio
async def test_get_route_segments(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # 1. Upload a route
    geojson_data = {
        "type": "Feature",
        "properties": {"name": "Test Segments"},
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
    files = {"file": ("test.geojson", file_bytes, "application/json")}
    upload_response = await client.post("/api/v1/routes/upload", files=files)
    assert upload_response.status_code == 201
    route_id = upload_response.json()["route_id"]
    segment_count = upload_response.json()["segment_count"]

    # 2. GET segments
    response = await client.get(f"/api/v1/routes/{route_id}/segments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == segment_count
    for seg in data:
        assert "id" in seg
        assert "seq" in seg
        assert "length_m" in seg
        assert "slope_pct" in seg


@pytest.mark.asyncio
async def test_get_route_not_found(client: AsyncClient) -> None:
    fake_uuid = "12345678-1234-1234-1234-123456789abc"
    response = await client.get(f"/api/v1/routes/{fake_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_route_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/api/v1/routes/not-a-uuid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_dem_sources_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dem/sources")
    assert response.status_code == 200
    assert response.json() == []
