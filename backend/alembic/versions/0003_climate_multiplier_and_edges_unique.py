"""add climate multiplier function and unique edge segment index

Revision ID: 0003_climate_multiplier_edges
Revises: 0002_add_segments_route_index
Create Date: 2026-06-11
"""

from __future__ import annotations

from alembic import op

revision: str = "0003_climate_multiplier_edges"
down_revision: str = "0002_add_segments_route_index"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_index("uq_edges_segment_id", "edges", ["segment_id"], unique=True)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION climate_cost_multiplier(
            wbgt FLOAT,
            precip_mm FLOAT,
            slope_pct FLOAT,
            canopy FLOAT
        ) RETURNS FLOAT AS $$
        DECLARE
            multiplier FLOAT := 1.0;
        BEGIN
            IF wbgt > 28.0 THEN
                multiplier := multiplier * (1.0 + 0.05 * (wbgt - 28.0));
            END IF;

            IF precip_mm > 5.0 AND slope_pct < -0.1763 THEN
                multiplier := multiplier * 1.35;
            END IF;

            IF canopy < 0.2 AND wbgt > 30.0 THEN
                multiplier := multiplier * 1.15;
            END IF;

            RETURN LEAST(multiplier, 3.0);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS climate_cost_multiplier(FLOAT, FLOAT, FLOAT, FLOAT)")
    op.drop_index("uq_edges_segment_id", table_name="edges")
