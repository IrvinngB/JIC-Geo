"""create initial spatial tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-06-09

Tables created:
    routes         — full 3DZ LineString geometries (DAT)
    segments       — 100m sub-segments with slope and elevation (DAT/RUT)
    segment_costs  — dynamic biomechanical costs per segment (VEL/MET/RIE)
    dem_sources    — registry of available DEM raster sources (DAT)
    climate_zones  — per-zone WBGT and climate data (CLI)
    edges          — pgRouting edge table (GRF)

Spatial indexes:
    idx_routes_geom    GIST on routes.geom
    idx_segments_geom  GIST on segments.geom
    idx_edges_geom     GIST on edges.geom
    idx_climate_geom   GIST on climate_zones.geom
"""

from __future__ import annotations

import sqlalchemy as sa
import geoalchemy2
from alembic import op

# revision identifiers
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # routes
    # ------------------------------------------------------------------
    op.create_table(
        "routes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=True),
        sa.Column("source_format", sa.String(10), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry("LINESTRINGZ", srid=4326, dimension=3, spatial_index=False),
            nullable=True,
        ),
    )
    op.create_index("idx_routes_geom", "routes", ["geom"], postgresql_using="gist")

    # ------------------------------------------------------------------
    # segments
    # ------------------------------------------------------------------
    op.create_table(
        "segments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "route_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("routes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry("LINESTRINGZ", srid=4326, dimension=3, spatial_index=False),
            nullable=True,
        ),
        sa.Column("length_m", sa.Float, nullable=True),
        sa.Column("elevation_start", sa.Float, nullable=True),
        sa.Column("elevation_end", sa.Float, nullable=True),
        sa.Column("slope_pct", sa.Float, nullable=True),
        sa.Column("surface_type", sa.String(20), nullable=False, server_default="dirt"),
        sa.Column("canopy_density", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("dem_source", sa.String(50), nullable=True),
        sa.Column("dem_resolution_m", sa.Float, nullable=True),
        sa.Column("elevation_interpolated", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("idx_segments_geom", "segments", ["geom"], postgresql_using="gist")

    # ------------------------------------------------------------------
    # segment_costs
    # ------------------------------------------------------------------
    op.create_table(
        "segment_costs",
        sa.Column("segment_id", sa.BigInteger, sa.ForeignKey("segments.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("base_cost", sa.Float, nullable=True),
        sa.Column("base_reverse_cost", sa.Float, nullable=True),
        sa.Column("velocity_kmh", sa.Float, nullable=True),
        sa.Column("cot_j_per_kg_m", sa.Float, nullable=True),
        sa.Column("cot_method", sa.String(20), nullable=True),
        sa.Column("metabolic_rate_w", sa.Float, nullable=True),
        sa.Column("risk_score", sa.Float, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # dem_sources
    # ------------------------------------------------------------------
    op.create_table(
        "dem_sources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("resolution_m", sa.Float, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rast_table", sa.String(100), nullable=False),
    )

    # ------------------------------------------------------------------
    # climate_zones
    # ------------------------------------------------------------------
    op.create_table(
        "climate_zones",
        sa.Column("zone_id", sa.String(50), primary_key=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry("POLYGON", srid=4326, dimension=2, spatial_index=False),
            nullable=True,
        ),
        sa.Column("wbgt", sa.Float, nullable=True),
        sa.Column("precip_mm", sa.Float, nullable=True),
        sa.Column("uv_index", sa.Float, nullable=True),
        sa.Column("temperature_c", sa.Float, nullable=True),
        sa.Column("humidity_pct", sa.Float, nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="api"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_climate_geom", "climate_zones", ["geom"], postgresql_using="gist")

    # ------------------------------------------------------------------
    # edges (pgRouting)
    # ------------------------------------------------------------------
    op.create_table(
        "edges",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("source", sa.BigInteger, nullable=True),
        sa.Column("target", sa.BigInteger, nullable=True),
        sa.Column("segment_id", sa.BigInteger, sa.ForeignKey("segments.id"), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry("LINESTRINGZ", srid=4326, dimension=3, spatial_index=False),
            nullable=True,
        ),
        sa.Column("base_cost", sa.Float, nullable=True),
        sa.Column("base_reverse_cost", sa.Float, nullable=True),
        sa.Column("surface_type", sa.String(20), nullable=True),
        sa.Column("canopy_density", sa.Float, nullable=True),
        sa.Column("slope_pct", sa.Float, nullable=True),
    )
    op.create_index("idx_edges_geom", "edges", ["geom"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_table("edges")
    op.drop_table("climate_zones")
    op.drop_table("dem_sources")
    op.drop_table("segment_costs")
    op.drop_table("segments")
    op.drop_table("routes")
