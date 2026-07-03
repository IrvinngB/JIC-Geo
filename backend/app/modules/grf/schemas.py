"""Pydantic schemas for GRF - pgRouting graph queries."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.cli.schemas import ClimateOverride, ClimateSource
from app.modules.sim.schemas import SimulationScenario

RoutingAlgorithm = Literal["astar", "dijkstra"]


class OptimalPathRequest(BaseModel):
    """Request body for optimal route queries. GRF-03, GRF-04, GRF-07, SIM-01, SIM-03

    Optional climate makes the routing itself climate-aware: a scenario or manual
    override reroutes under simulated weather; omitting both routes under the real
    climate persisted in climate_zones.
    """

    start_node: int
    end_node: int
    waypoints: list[int] = Field(default_factory=list)
    algorithm: RoutingAlgorithm = "astar"
    scenario: SimulationScenario | None = None
    climate: ClimateOverride | None = None


class PathStep(BaseModel):
    seq: int
    node: int
    edge: int
    cost: float
    agg_cost: float


class OptimalPathResponse(BaseModel):
    """Lowest-cost route under the active climate. SIM-02 marks which one was used."""

    algorithm: RoutingAlgorithm
    start_node: int
    end_node: int
    waypoints: list[int]
    total_cost: float
    climate_source: ClimateSource
    steps: list[PathStep]


class GraphNode(BaseModel):
    """A pgRouting topology vertex, for map-based start/end/waypoint pickers."""

    id: int
    lon: float
    lat: float


class GraphEdge(BaseModel):
    """A pgRouting topology edge, mapping back to its source segment."""

    id: int
    seq: int
    source: int
    target: int


class RouteGraphResponse(BaseModel):
    """Graph topology for a route. Required to pick optimal-path nodes from a map. GRF-01, API-06"""

    route_id: uuid.UUID
    nodes: list[GraphNode]
    edges: list[GraphEdge]
