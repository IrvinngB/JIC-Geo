"""GRF service - pure graph request helpers."""

from __future__ import annotations


def build_node_pairs(start_node: int, end_node: int, waypoints: list[int]) -> list[tuple[int, int]]:
    """Return consecutive route legs including waypoints. GRF-07"""
    nodes = [start_node, *waypoints, end_node]
    return [(nodes[index], nodes[index + 1]) for index in range(len(nodes) - 1)]
