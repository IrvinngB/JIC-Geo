"""
Integration tests for biomechanical analysis endpoint.
"""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from app.modules.prf.schemas import FitnessLevel


@pytest.mark.asyncio
async def test_biomechanical_analysis_success(
    client: AsyncClient,
) -> None:
    # 1. Upload a route
    geojson_data = {
        "type": "Feature",
        "properties": {"name": "Biomechanical Test"},
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
    files = {"file": ("bio.geojson", file_bytes, "application/json")}
    upload_response = await client.post("/api/v1/routes/upload", files=files)
    assert upload_response.status_code == 201
    route_id = upload_response.json()["route_id"]

    # 2. Process the route
    process_response = await client.post(f"/api/v1/routes/{route_id}/process")
    assert process_response.status_code == 200

    # 3. Analyze biomechanics
    payload = {
        "profile": {
            "weight_kg": 70,
            "load_kg": 10,
            "fitness_level": "medium",
        },
        "velocity_model": "tobler",
    }
    analysis_response = await client.post(
        f"/api/v1/routes/{route_id}/biomechanical",
        json=payload,
    )
    assert analysis_response.status_code == 200
    data = analysis_response.json()
    assert data["route_id"] == route_id
    assert "summary" in data
    assert "segments" in data
    assert len(data["segments"]) > 0
    for seg in data["segments"]:
        assert "velocity_kmh" in seg
        assert "cot_j_per_kg_m" in seg
        assert "metabolic_rate_w" in seg


@pytest.mark.asyncio
async def test_biomechanical_analysis_invalid_route(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/routes/12345678-1234-1234-1234-123456789abc/biomechanical",
        json={},
    )
    assert response.status_code == 404


