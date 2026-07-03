"""GRF router - optimal path endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.cli.schemas import ClimateData
from app.modules.cli.service import climate_from_override
from app.modules.grf import repository as grf_repo
from app.modules.grf.schemas import (
    GraphEdge,
    GraphNode,
    OptimalPathRequest,
    OptimalPathResponse,
    PathStep,
    RouteGraphResponse,
)
from app.modules.grf.service import build_node_pairs
from app.modules.sim.service import resolve_simulation_climate

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


@router.get("/{route_id}/graph", response_model=RouteGraphResponse)
async def get_route_graph(
    route_id: str,
    db: AsyncSession = DB_DEPENDENCY,
) -> RouteGraphResponse:
    """Return graph topology (nodes + edges) for a route. GRF-01, GRF-07, API-06

    Lets a map UI pick start/end/waypoint nodes for /optimal-path and translate
    the resulting steps back into segment geometries.
    """
    try:
        route_uuid = uuid.UUID(route_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route_id format. Must be a valid UUID.",
        ) from None

    await grf_repo.sync_edges_from_segments(db)
    await grf_repo.create_topology(db)

    edges = await grf_repo.get_route_edges(db, route_uuid)
    if not edges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{route_id}' has no graph topology. Process it first.",
        )

    nodes = await grf_repo.get_route_nodes(db, route_uuid)
    await db.commit()

    return RouteGraphResponse(
        route_id=route_uuid,
        nodes=[GraphNode(**node) for node in nodes],
        edges=[GraphEdge(**edge) for edge in edges],
    )


@router.post("/optimal-path", response_model=OptimalPathResponse)
async def optimal_path(
    payload: OptimalPathRequest,
    db: AsyncSession = DB_DEPENDENCY,
) -> OptimalPathResponse:
    """Return the lowest-cost route between graph nodes. API-06, GRF-03, GRF-04, GRF-07, SIM-01

    A scenario or manual climate override reroutes under simulated weather;
    omitting both routes under the real climate in climate_zones.
    """
    await grf_repo.sync_edges_from_segments(db)
    await grf_repo.create_topology(db)

    # Resolve simulated climate, if any, so it can steer the routing itself.
    sim_climate: ClimateData | None = None
    if payload.scenario is not None or payload.climate is not None:
        try:
            override = resolve_simulation_climate(payload.scenario, payload.climate)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        sim_climate = climate_from_override(override)
    wbgt = sim_climate.wbgt if sim_climate else None
    precip_mm = sim_climate.precip_mm if sim_climate else None

    all_steps: list[PathStep] = []
    total_cost = 0.0
    seq_offset = 0
    for start_node, end_node in build_node_pairs(
        payload.start_node,
        payload.end_node,
        payload.waypoints,
    ):
        rows = await grf_repo.shortest_path(
            db, start_node, end_node, payload.algorithm, wbgt=wbgt, precip_mm=precip_mm
        )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No graph path found between {start_node} and {end_node}.",
            )
        for row in rows:
            step = PathStep(
                seq=int(row["seq"]) + seq_offset,
                node=int(row["node"]),
                edge=int(row["edge"]),
                cost=round(float(row["cost"]), 4),
                agg_cost=round(total_cost + float(row["agg_cost"]), 4),
            )
            all_steps.append(step)
        total_cost = all_steps[-1].agg_cost
        seq_offset = all_steps[-1].seq + 1

    await grf_repo.get_climate_multiplier_trace(db)
    await db.commit()
    return OptimalPathResponse(
        algorithm=payload.algorithm,
        start_node=payload.start_node,
        end_node=payload.end_node,
        waypoints=payload.waypoints,
        total_cost=round(total_cost, 4),
        climate_source=sim_climate.source if sim_climate else "api",
        steps=all_steps,
    )
