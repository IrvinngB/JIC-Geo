"""
MET — Metabolic cost service.
Implements Minetti polynomial and Pandolf equation (Phase 3).
"""

from typing import Literal

MINETTI_MIN = -0.45
MINETTI_MAX = 0.45

CotMethod = Literal["exact", "extrapolated"]

# Terrain coefficient η values for Pandolf (Formulas.md Table 2.2)
TERRAIN_ETA: dict[str, float] = {
    "asphalt": 1.0,
    "pavement": 1.0,
    "dirt": 1.2,
    "scrub": 1.5,
    "dense_scrub": 1.8,
    "sand_mud": 2.1,
    "mud": 2.1,
    "sand": 2.1,
}

OFF_PATH_SURFACES = {"scrub", "dense_scrub", "sand_mud", "mud", "sand"}

FATIGUE_KCAL_PER_KG_BY_FITNESS: dict[str, float] = {
    "low": 5.0,
    "medium": 7.0,
    "high": 9.0,
    "athlete": 11.0,
}


def _minetti_poly(i: float) -> float:
    return 280.5 * i**5 - 58.7 * i**4 - 76.8 * i**3 + 51.9 * i**2 + 19.6 * i + 2.5


def _minetti_derivative(i: float) -> float:
    """dC/di at boundary — used for linear extrapolation (mitigacion.md, Problema 2)."""
    return 5 * 280.5 * i**4 - 4 * 58.7 * i**3 - 3 * 76.8 * i**2 + 2 * 51.9 * i + 19.6


def minetti_cot(gradient: float) -> tuple[float, CotMethod]:
    """
    Metabolic cost of transport using Minetti et al. (2002).
    Domain: [-0.45, +0.45]. Outside domain: linear extrapolation from boundary.
    Returns (J/kg·m, method).
    MET-01 (updated per mitigacion.md), MET-07
    """
    if MINETTI_MIN <= gradient <= MINETTI_MAX:
        return _minetti_poly(gradient), "exact"

    limit = MINETTI_MAX if gradient > 0 else MINETTI_MIN
    slope = _minetti_derivative(limit)
    extrapolated = _minetti_poly(limit) + slope * (gradient - limit)
    return max(extrapolated, 0.0), "extrapolated"  # never negative


def pandolf_metabolic_rate(
    weight_kg: float,
    load_kg: float,
    velocity_ms: float,
    slope_pct: float,
    terrain_eta: float,
) -> float:
    """
    Pandolf (1977) metabolic rate equation.
    M = 1.5W + 2.0(W+L)(L/W)² + η(W+L)(1.5V² + 0.35VG)
    Returns Watts.
    MET-02, MET-03
    """
    weight = weight_kg
    load = load_kg
    velocity = velocity_ms
    gradient = slope_pct
    eta = terrain_eta

    return (
        1.5 * weight
        + 2.0 * (weight + load) * (load / weight) ** 2
        + eta * (weight + load) * (1.5 * velocity**2 + 0.35 * velocity * gradient)
    )


def is_eccentric_fatigue(slope_pct: float) -> bool:
    """
    Segments with gradient < -0.10 cause eccentric (quadriceps) fatigue.
    MET-06
    """
    return slope_pct < -0.10


def terrain_eta(surface_type: str) -> float:
    """Return the terrain coefficient η for a surface type (MET-03)."""
    return TERRAIN_ETA.get(surface_type, 1.2)  # default: dirt


def is_on_path_surface(surface_type: str) -> bool:
    """Return whether a surface should be treated as consolidated path (VEL-04)."""
    return surface_type not in OFF_PATH_SURFACES


def estimate_time_to_severe_fatigue_h(
    *,
    weight_kg: float,
    fitness_level: str,
    total_kcal: float,
    elapsed_time_h: float,
) -> float | None:
    """
    Estimate projected hours until severe fatigue from current burn rate.

    MET-05. This is a conservative profile-based threshold until a richer fatigue
    model is introduced in the risk phase.
    """
    if elapsed_time_h <= 0 or total_kcal <= 0:
        return None

    kcal_per_kg = FATIGUE_KCAL_PER_KG_BY_FITNESS.get(fitness_level, 7.0)
    severe_fatigue_kcal = weight_kg * kcal_per_kg
    burn_rate_kcal_h = total_kcal / elapsed_time_h

    if burn_rate_kcal_h <= 0:
        return None

    return severe_fatigue_kcal / burn_rate_kcal_h
