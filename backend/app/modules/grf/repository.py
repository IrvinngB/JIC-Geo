"""GRF repository - pgRouting SQL queries."""

from __future__ import annotations

import logging
import math
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _sql_float(value: float) -> str:
    """Render a finite float as a SQL numeric literal — the only injection-safe
    way to push a simulated climate value across pgRouting's text boundary.

    pgr_bdAstar/pgr_dijkstra take the edge query as a *string*, so bound params
    never reach inside it. A Python float's repr is always a numeric token
    (never a quote or statement), so interpolating it cannot inject SQL. The
    finiteness guard rejects inf/nan, which would otherwise render as bare
    identifiers and fail inside the multiplier call.
    """
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Climate override values must be finite numbers.")
    return repr(number)


async def create_topology(db: AsyncSession, tolerance: float = 0.00001) -> None:
    """Create pgRouting topology over edges. GRF-01

    Runs incrementally (clean := false, the pgRouting default): edges whose
    source/target are already set keep their vertex ids. With clean := true,
    every call truncates edges_vertices_pgr and reassigns vertex ids from
    scratch, so node ids returned by /graph would go stale as soon as
    /optimal-path re-runs this — both endpoints call it on every request.
    """
    await db.execute(
        text(
            """
            SELECT pgr_createTopology(
                'edges',
                :tolerance,
                'geom_2d',
                'id',
                'source',
                'target'
            )
            """
        ),
        {"tolerance": tolerance},
    )


async def sync_edges_from_segments(db: AsyncSession) -> None:
    """Populate/update static edge table from processed segments. RUT-07, GRF-02, GRF-05"""
    await db.execute(
        text(
            """
            INSERT INTO edges (
                segment_id, geom, geom_2d, base_cost, base_reverse_cost,
                surface_type, canopy_density, slope_pct
            )
            SELECT
                s.id,
                s.geom,
                ST_Force2D(s.geom),
                COALESCE(sc.base_cost, ABS(COALESCE(s.slope_pct, 0)) * COALESCE(s.length_m, 1)),
                COALESCE(sc.base_reverse_cost, ABS(COALESCE(s.slope_pct, 0)) * COALESCE(s.length_m, 1)),
                s.surface_type,
                s.canopy_density,
                s.slope_pct
            FROM segments s
            LEFT JOIN segment_costs sc ON sc.segment_id = s.id
            ON CONFLICT (segment_id) DO UPDATE SET
                geom = EXCLUDED.geom,
                geom_2d = EXCLUDED.geom_2d,
                base_cost = EXCLUDED.base_cost,
                base_reverse_cost = EXCLUDED.base_reverse_cost,
                surface_type = EXCLUDED.surface_type,
                canopy_density = EXCLUDED.canopy_density,
                slope_pct = EXCLUDED.slope_pct
            """
        )
    )


def _edge_sql(wbgt: float | None = None, precip_mm: float | None = None) -> str:
    """Edge cost query for pgRouting. GRF-03, GRF-04, GRF-10.

    Real climate (wbgt/precip None): values come from the climate_zones JOIN —
    the persisted, trigger-updated dynamic cost layer (Formulas §7.5, GRF-05/06).

    Simulated climate (wbgt/precip given): values are request-scoped literals and
    the zone is bypassed entirely — a what-if, not the world (SIM-01). Either way
    the static geometry is never touched (Formulas §7.2); only the climate source
    of the multiplier changes, so the cost/reverse_cost asymmetry (§5) holds.
    """
    if wbgt is None or precip_mm is None:
        wbgt_expr = "COALESCE(cz.wbgt, 25.0)"
        precip_expr = "COALESCE(cz.precip_mm, 0.0)"
        climate_join = "LEFT JOIN climate_zones cz ON ST_Intersects(e.geom_2d, cz.geom)"
    else:
        wbgt_expr = _sql_float(wbgt)
        precip_expr = _sql_float(precip_mm)
        climate_join = ""

    return f"""
        SELECT
          e.id,
          e.source,
          e.target,
          GREATEST(0.0001, COALESCE(e.base_cost, 1.0))
            * climate_cost_multiplier(
                {wbgt_expr},
                {precip_expr},
                COALESCE(e.slope_pct, 0.0),
                COALESCE(e.canopy_density, 0.5)
              ) AS cost,
          GREATEST(0.0001, COALESCE(e.base_reverse_cost, 1.0))
            * climate_cost_multiplier(
                {wbgt_expr},
                {precip_expr},
                -COALESCE(e.slope_pct, 0.0),
                COALESCE(e.canopy_density, 0.5)
              ) AS reverse_cost,
          ST_X(ST_StartPoint(e.geom_2d)) AS x1,
          ST_Y(ST_StartPoint(e.geom_2d)) AS y1,
          ST_X(ST_EndPoint(e.geom_2d)) AS x2,
          ST_Y(ST_EndPoint(e.geom_2d)) AS y2
        FROM edges e
        {climate_join}
        WHERE e.source IS NOT NULL AND e.target IS NOT NULL
    """


async def shortest_path(
    db: AsyncSession,
    start_node: int,
    end_node: int,
    algorithm: str = "astar",
    wbgt: float | None = None,
    precip_mm: float | None = None,
) -> list[dict[str, Any]]:
    """Run A* bidirectional or Dijkstra with climate multiplier on-the-fly. GRF-03, GRF-04, GRF-06

    Passing wbgt/precip_mm reroutes under simulated climate (SIM-01); leaving them
    None routes under the real climate persisted in climate_zones.
    """
    edge_sql = _edge_sql(wbgt, precip_mm)
    query = (
        """
        SELECT seq, node, edge, cost, agg_cost
        FROM pgr_dijkstra(
            CAST(:edge_sql AS text),
            CAST(:start_node AS bigint),
            CAST(:end_node AS bigint),
            directed := true
        )
        """
        if algorithm == "dijkstra"
        else """
        SELECT seq, node, edge, cost, agg_cost
        FROM pgr_bdAstar(
            CAST(:edge_sql AS text),
            CAST(:start_node AS bigint),
            CAST(:end_node AS bigint),
            directed := true
        )
        """
    )
    result = await db.execute(
        text(query),
        {"edge_sql": edge_sql, "start_node": start_node, "end_node": end_node},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_route_nodes(db: AsyncSession, route_id: uuid.UUID) -> list[dict[str, Any]]:
    """Return topology vertices touching this route's edges, with coordinates.

    Needed because pgRouting vertex ids (edges_vertices_pgr.id) are opaque
    integers with no map-friendly representation otherwise.
    """
    result = await db.execute(
        text(
            """
            SELECT DISTINCT v.id, ST_X(v.the_geom) AS lon, ST_Y(v.the_geom) AS lat
            FROM edges_vertices_pgr v
            JOIN edges e ON v.id = e.source OR v.id = e.target
            JOIN segments s ON s.id = e.segment_id
            WHERE s.route_id = :route_id
            ORDER BY v.id
            """
        ),
        {"route_id": str(route_id)},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_route_edges(db: AsyncSession, route_id: uuid.UUID) -> list[dict[str, Any]]:
    """Return topology edges for this route, mapped back to segment seq.

    Lets the frontend translate optimal-path steps (which reference edge ids)
    into segment geometries it already has for rendering.
    """
    result = await db.execute(
        text(
            """
            SELECT e.id, s.seq, e.source, e.target
            FROM edges e
            JOIN segments s ON s.id = e.segment_id
            WHERE s.route_id = :route_id
              AND e.source IS NOT NULL AND e.target IS NOT NULL
            ORDER BY s.seq
            """
        ),
        {"route_id": str(route_id)},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_climate_multiplier_trace(db: AsyncSession) -> list[dict[str, Any]]:
    """Return multiplier trace by climate zone for logging. GRF-11"""
    result = await db.execute(
        text(
            """
            SELECT
              COALESCE(cz.zone_id, 'unmatched') AS zone_id,
              AVG(climate_cost_multiplier(
                COALESCE(cz.wbgt, 25.0),
                COALESCE(cz.precip_mm, 0.0),
                COALESCE(e.slope_pct, 0.0),
                COALESCE(e.canopy_density, 0.5)
              )) AS avg_multiplier,
              COUNT(*) AS edge_count
            FROM edges e
            LEFT JOIN climate_zones cz ON ST_Intersects(e.geom_2d, cz.geom)
            GROUP BY COALESCE(cz.zone_id, 'unmatched')
            """
        )
    )
    rows = [dict(row) for row in result.mappings().all()]
    logger.info("Climate routing multipliers: %s", rows)
    return rows
