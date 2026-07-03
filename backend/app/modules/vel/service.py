"""
VEL — Velocity modeling service.
Implements Tobler's hiking function and Irmischer-Clarke (Phase 3).
"""

import math
from enum import StrEnum


class VelocityModel(StrEnum):
    TOBLER = "tobler"
    IRMISCHER_CLARKE = "irmischer_clarke"


def tobler(slope: float, is_on_path: bool = True) -> float:
    """
    Tobler's hiking function: W = 6 × e^(−3.5 × |S + 0.05|)
    Returns velocity in km/h.
    VEL-01, VEL-04
    """
    w = 6.0 * math.exp(-3.5 * abs(slope + 0.05))
    return w * 0.6 if not is_on_path else w  # VEL-04: off-path factor


def irmischer_clarke(slope: float, is_on_path: bool = True) -> float:
    """
    Irmischer & Clarke (2018) — on-path, male.
    v(S) = [0.11 + e^(−(S + 0.0506)² / (2 × 0.2043²))] × 3.6
    Returns velocity in km/h.
    VEL-02, VEL-04
    """
    exponent = -((slope + 0.0506) ** 2) / (2 * (0.2043**2))
    velocity = (0.11 + math.exp(exponent)) * 3.6
    return velocity * 0.6 if not is_on_path else velocity


def apply_langmuir(velocity_kmh: float, slope_deg: float, is_descent: bool) -> float:
    """
    Langmuir descent corrections (VEL-05):
      Gentle descent (5°–12°):  −10 min per 300 m → speed increase
      Steep descent  (>12°):   +10 min per 300 m → speed decrease
    Returns adjusted velocity in km/h.
    """
    if not is_descent:
        return velocity_kmh

    if 5.0 <= slope_deg <= 12.0:
        correction_per_300m = -10.0  # minutes saved
    elif slope_deg > 12.0:
        correction_per_300m = +10.0  # minutes added
    else:
        return velocity_kmh

    # Convert to hours per 300 m
    correction_hours_per_300m = correction_per_300m / 60.0

    # For a segment at velocity_kmh, time to travel 0.3 km
    base_time_h = 0.3 / velocity_kmh
    adjusted_time_h = base_time_h + correction_hours_per_300m

    # Prevent non-positive time
    if adjusted_time_h <= 0:
        return velocity_kmh

    return 0.3 / adjusted_time_h


def _slope_pct_to_deg(slope_pct: float) -> float:
    """Convert gradient (Δh/Δx) to degrees."""
    return math.degrees(math.atan(slope_pct))


def calculate_velocity(
    slope: float,
    model: VelocityModel = VelocityModel.IRMISCHER_CLARKE,
    is_on_path: bool = True,
    apply_langmuir_correction: bool = True,
) -> float:
    """
    Dispatch to the selected velocity model and apply Langmuir if needed.
    Returns velocity in km/h.
    VEL-03, VEL-05, VEL-06
    """
    base = (
        tobler(slope, is_on_path)
        if model == VelocityModel.TOBLER
        else irmischer_clarke(slope, is_on_path)
    )

    if apply_langmuir_correction and slope < 0:
        slope_deg = _slope_pct_to_deg(abs(slope))
        base = apply_langmuir(base, slope_deg, is_descent=True)

    return base
