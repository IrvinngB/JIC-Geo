"""RIE repository — persistence for risk outputs."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_persisted_risk(
    db: AsyncSession,
    route_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Return persisted per-segment risk for a route, ordered by seq. API-03, RIE-01.

    Only includes segments that already have a risk score (i.e. the route has
    been analyzed at least once). Returns seq, risk_score and GeoJSON geometry.
    """
    result = await db.execute(
        text(
            """
            SELECT s.seq AS seq,
                   sc.risk_score AS risk_score,
                   ST_AsGeoJSON(s.geom)::text AS geom_geojson
            FROM segments s
            JOIN segment_costs sc ON sc.segment_id = s.id
            WHERE s.route_id = :route_id
              AND sc.risk_score IS NOT NULL
            ORDER BY s.seq
            """
        ),
        {"route_id": str(route_id)},
    )
    return [
        {
            "seq": int(row.seq),
            "risk_score": int(row.risk_score),
            "geom_geojson": row.geom_geojson,
        }
        for row in result.fetchall()
    ]


async def update_segment_risk_scores(db: AsyncSession, scores_by_segment_id: dict[int, int]) -> None:
    """Persist risk scores in segment_costs. RIE-01"""
    if not scores_by_segment_id:
        return
    await db.execute(
        text(
            """
            UPDATE segment_costs
            SET risk_score = :risk_score,
                updated_at = now()
            WHERE segment_id = :segment_id
            """
        ),
        [
            {"segment_id": segment_id, "risk_score": risk_score}
            for segment_id, risk_score in scores_by_segment_id.items()
        ],
    )
