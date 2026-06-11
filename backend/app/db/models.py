"""
SQLAlchemy ORM models for JIC-Geo.
Geometric columns use GeoAlchemy2.
Migrations are managed by Alembic — do not alter table definitions manually.
"""

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# DAT — Spatial Data
# ---------------------------------------------------------------------------


class Route(Base):
    """Uploaded hiking route — full geometry stored as 3DZ LineString."""

    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(Text)
    source_format: Mapped[str] = mapped_column(String(10))  # 'gpx' | 'geojson'
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    geom = mapped_column(Geometry("LINESTRINGZ", srid=4326))

    segments: Mapped[list["Segment"]] = relationship(back_populates="route", cascade="all, delete-orphan")


class Segment(Base):
    """
    Static geometry of a route segment — never mutated after creation.
    Dynamic costs live in SegmentCosts (DAT-06).
    """

    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    geom = mapped_column(Geometry("LINESTRINGZ", srid=4326))
    length_m: Mapped[float | None] = mapped_column(Float)
    elevation_start: Mapped[float | None] = mapped_column(Float)
    elevation_end: Mapped[float | None] = mapped_column(Float)
    slope_pct: Mapped[float | None] = mapped_column(Float)  # S = Δh/Δx (RUT-02)
    surface_type: Mapped[str] = mapped_column(String(20), default="dirt")  # DAT-07
    canopy_density: Mapped[float] = mapped_column(Float, default=0.5)  # DAT-08 (0.0–1.0)
    dem_source: Mapped[str | None] = mapped_column(String(50))  # DAT-09
    dem_resolution_m: Mapped[float | None] = mapped_column(Float)  # DAT-09
    elevation_interpolated: Mapped[bool] = mapped_column(Boolean, default=False)  # RUT-11

    route: Mapped["Route"] = relationship(back_populates="segments")
    costs: Mapped["SegmentCosts | None"] = relationship(back_populates="segment", uselist=False)


class SegmentCosts(Base):
    """Dynamic cost attributes per segment — updated when climate or profile changes (DAT-06)."""

    __tablename__ = "segment_costs"

    segment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("segments.id", ondelete="CASCADE"), primary_key=True)
    base_cost: Mapped[float | None] = mapped_column(Float)        # Minetti ascent cost
    base_reverse_cost: Mapped[float | None] = mapped_column(Float)  # Minetti descent cost
    velocity_kmh: Mapped[float | None] = mapped_column(Float)    # VEL output
    cot_j_per_kg_m: Mapped[float | None] = mapped_column(Float)  # MET-01 CoT
    cot_method: Mapped[str | None] = mapped_column(String(20))   # 'exact'|'extrapolated' (MET-07)
    metabolic_rate_w: Mapped[float | None] = mapped_column(Float)  # MET-02 Pandolf output
    risk_score: Mapped[float | None] = mapped_column(Float)      # RIE-01
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    segment: Mapped["Segment"] = relationship(back_populates="costs")


class DEMSource(Base):
    """Registry of available DEM rasters (DAT-09, DAT-10)."""

    __tablename__ = "dem_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    resolution_m: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # higher = preferred
    rast_table: Mapped[str] = mapped_column(String(100), nullable=False)


# ---------------------------------------------------------------------------
# CLI — Climate Zones
# ---------------------------------------------------------------------------


class ClimateZone(Base):
    """
    Polygon covering a geographic zone with homogeneous climate conditions.
    Updated by the climate API on a TTL schedule — NOT per-edge (GRF-08).
    """

    __tablename__ = "climate_zones"

    zone_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    geom = mapped_column(Geometry("POLYGON", srid=4326))
    wbgt: Mapped[float | None] = mapped_column(Float)         # CLI-02
    precip_mm: Mapped[float | None] = mapped_column(Float)
    uv_index: Mapped[float | None] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(20), default="api")  # 'api'|'simulation' (SIM-02)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# GRF — pgRouting edges
# ---------------------------------------------------------------------------


class Edge(Base):
    """
    pgRouting edge table.
    base_cost / base_reverse_cost are static (Minetti × η).
    Climate multiplier is applied on-the-fly during routing queries (GRF-05, GRF-06).
    """

    __tablename__ = "edges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[int | None] = mapped_column(BigInteger)  # populated by pgr_createTopology
    target: Mapped[int | None] = mapped_column(BigInteger)
    segment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("segments.id"))
    geom = mapped_column(Geometry("LINESTRINGZ", srid=4326))
    geom_2d = mapped_column(Geometry("LINESTRING", srid=4326))
    base_cost: Mapped[float | None] = mapped_column(Float)        # ascent
    base_reverse_cost: Mapped[float | None] = mapped_column(Float)  # descent
    surface_type: Mapped[str | None] = mapped_column(String(20))
    canopy_density: Mapped[float | None] = mapped_column(Float)
    slope_pct: Mapped[float | None] = mapped_column(Float)
