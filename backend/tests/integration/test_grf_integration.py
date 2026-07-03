"""Integration tests for GRF — graph topology and pgRouting optimal path."""

from __future__ import annotations

import json
import uuid

import pytest
from httpx import AsyncClient


async def _upload_and_analyze_route(client: AsyncClient) -> str:
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

    return route_id


@pytest.mark.asyncio
async def test_route_graph_and_optimal_path(client: AsyncClient) -> None:
    route_id = await _upload_and_analyze_route(client)

    graph_response = await client.get(f"/api/v1/routes/{route_id}/graph")
    assert graph_response.status_code == 200
    graph = graph_response.json()
    assert graph["route_id"] == route_id
    assert len(graph["nodes"]) >= 2
    assert len(graph["edges"]) >= 1

    # Contract the frontend relies on: each graph edge maps to a distinct segment
    # seq, so optimal-path steps can be translated back into segment geometries
    # (routeStore.optimalPathFeatures). Seq must therefore be unique per edge.
    edge_seqs = [e["seq"] for e in graph["edges"]]
    assert len(edge_seqs) == len(set(edge_seqs))

    edge = graph["edges"][0]

    response = await client.post(
        "/api/v1/routes/optimal-path",
        json={
            "start_node": edge["source"],
            "end_node": edge["target"],
            "algorithm": "astar",
            "waypoints": [],
        },
    )

    # optimal-path routes over the GLOBAL edge graph (every processed route in the
    # DB), so its steps may legitimately traverse edges outside this route. We only
    # assert it returns a usable path; per-route edge ownership is not guaranteed.
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "astar"
    assert data["total_cost"] > 0
    assert len(data["steps"]) >= 1


@pytest.mark.asyncio
async def test_route_graph_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/api/v1/routes/not-a-uuid/graph")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_route_graph_not_found_for_unknown_route(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/routes/{uuid.uuid4()}/graph")
    assert response.status_code == 404
