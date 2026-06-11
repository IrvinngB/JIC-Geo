"""GRF router - optimal path endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.grf import repository as grf_repo
from app.modules.grf.schemas import OptimalPathRequest, OptimalPathResponse, PathStep
from app.modules.grf.service import build_node_pairs

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


@router.post("/optimal-path", response_model=OptimalPathResponse)
async def optimal_path(
    payload: OptimalPathRequest,
    db: AsyncSession = DB_DEPENDENCY,
) -> OptimalPathResponse:
    """Return the lowest-cost route between graph nodes. API-06, GRF-03, GRF-04, GRF-07"""
    await grf_repo.sync_edges_from_segments(db)
    await grf_repo.create_topology(db)

    all_steps: list[PathStep] = []
    total_cost = 0.0
    seq_offset = 0
    for start_node, end_node in build_node_pairs(
        payload.start_node,
        payload.end_node,
        payload.waypoints,
    ):
        rows = await grf_repo.shortest_path(db, start_node, end_node, payload.algorithm)
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
        steps=all_steps,
    )
