"""Integration tests for GRF — pgRouting optimal path."""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.grf import repository as grf_repo


@pytest.mark.asyncio
async def test_optimal_path_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    geojson_data = {
        "type": "Feature",
        "properties": {"name": "Routing Test"},
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-79.5000, 9.0000, 100.0],
                [-79.5005, 9.0005, 150.0],
                [-79.5010, 9.0010, 200.0],
            ],
        },
    }
    files = {"file": ("routing.geojson", json.dumps(geojson_data).encode(), "application/json")}
    upload_response = await client.post("/api/v1/routes/upload", files=files)
    assert upload_response.status_code == 201
    route_id = upload_response.json()["route_id"]

    process_response = await client.post(f"/api/v1/routes/{route_id}/process")
    assert process_response.status_code == 200

    analysis_response = await client.post(
        f"/api/v1/routes/{route_id}/biomechanical",
        json={
            "profile": {"weight_kg": 70, "load_kg": 10, "fitness_level": "medium"},
            "velocity_model": "tobler",
        },
    )
    assert analysis_response.status_code == 200

    await grf_repo.sync_edges_from_segments(db_session)
    await grf_repo.create_topology(db_session)
    nodes_result = await db_session.execute(
        text(
            """
            SELECT source, target
            FROM edges
            WHERE source IS NOT NULL AND target IS NOT NULL
            ORDER BY id
            LIMIT 1
            """
        )
    )
    edge = nodes_result.mappings().one()

    response = await client.post(
        "/api/v1/routes/optimal-path",
        json={
            "start_node": edge["source"],
            "end_node": edge["target"],
            "algorithm": "astar",
            "waypoints": [],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "astar"
    assert data["total_cost"] > 0
    assert len(data["steps"]) >= 1
