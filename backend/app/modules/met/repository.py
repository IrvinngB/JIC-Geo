"""
MET repository — persistence for dynamic biomechanical segment costs.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upsert_segment_costs(
    db: AsyncSession,
    costs: list[dict[str, Any]],
) -> None:
    """Persist dynamic VEL/MET outputs in segment_costs (DAT-06)."""
    if not costs:
        return

    await db.execute(
        text(
            """
            INSERT INTO segment_costs (
                segment_id,
                base_cost,
                base_reverse_cost,
                velocity_kmh,
                cot_j_per_kg_m,
                cot_method,
                metabolic_rate_w,
                risk_score,
                updated_at
            )
            VALUES (
                :segment_id,
                :base_cost,
                :base_reverse_cost,
                :velocity_kmh,
                :cot_j_per_kg_m,
                :cot_method,
                :metabolic_rate_w,
                :risk_score,
                now()
            )
            ON CONFLICT (segment_id) DO UPDATE SET
                base_cost = EXCLUDED.base_cost,
                base_reverse_cost = EXCLUDED.base_reverse_cost,
                velocity_kmh = EXCLUDED.velocity_kmh,
                cot_j_per_kg_m = EXCLUDED.cot_j_per_kg_m,
                cot_method = EXCLUDED.cot_method,
                metabolic_rate_w = EXCLUDED.metabolic_rate_w,
                risk_score = EXCLUDED.risk_score,
                updated_at = now()
            """
        ),
        costs,
    )
