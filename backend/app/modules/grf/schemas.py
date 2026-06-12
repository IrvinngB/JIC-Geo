"""Pydantic schemas for GRF - pgRouting graph queries."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

RoutingAlgorithm = Literal["astar", "dijkstra"]


class OptimalPathRequest(BaseModel):
    """Request body for optimal route queries. GRF-03, GRF-04, GRF-07"""

    start_node: int
    end_node: int
    waypoints: list[int] = Field(default_factory=list)
    algorithm: RoutingAlgorithm = "astar"


class PathStep(BaseModel):
    seq: int
    node: int
    edge: int
    cost: float
    agg_cost: float


class OptimalPathResponse(BaseModel):
    algorithm: RoutingAlgorithm
    start_node: int
    end_node: int
    waypoints: list[int]
    total_cost: float
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
