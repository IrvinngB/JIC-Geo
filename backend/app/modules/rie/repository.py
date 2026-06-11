"""RIE repository — persistence for risk outputs."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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
