"""add 2d geometry column for pgRouting topology

Revision ID: 0004_edges_geom_2d
Revises: 0003_climate_multiplier_edges
Create Date: 2026-06-11
"""

from __future__ import annotations

import geoalchemy2
import sqlalchemy as sa
from alembic import op

revision: str = "0004_edges_geom_2d"
down_revision: str = "0003_climate_multiplier_edges"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column(
        "edges",
        sa.Column(
            "geom_2d",
            geoalchemy2.types.Geometry("LINESTRING", srid=4326, spatial_index=False),
            nullable=True,
        ),
    )
    op.execute("UPDATE edges SET geom_2d = ST_Force2D(geom) WHERE geom IS NOT NULL")
    op.create_index("idx_edges_geom_2d", "edges", ["geom_2d"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("idx_edges_geom_2d", table_name="edges")
    op.drop_column("edges", "geom_2d")
