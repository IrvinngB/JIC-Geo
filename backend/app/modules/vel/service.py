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


def irmischer_clarke(slope: float) -> float:
    """
    Irmischer & Clarke (2018) — on-path, male.
    v(S) = [0.11 + e^(−(S + 0.0506)² / (2 × 0.2043²))] × 3.6
    Returns velocity in km/h.
    VEL-02
    """
    exponent = -((slope + 0.0506) ** 2) / (2 * (0.2043**2))
    return (0.11 + math.exp(exponent)) * 3.6


def apply_langmuir(velocity_kmh: float, slope_deg: float, is_descent: bool) -> float:
    """
    Langmuir descent corrections (VEL-05):
      Gentle descent (5°–12°):  −10 min per 300 m → speed increase
      Steep descent  (>12°):   +10 min per 300 m → speed decrease
    Returns adjusted velocity in km/h.
    """
    # TODO: implement full Langmuir time-based correction
    # Placeholder: return unmodified until Phase 3
    return velocity_kmh


def calculate_velocity(
    slope: float,
    model: VelocityModel = VelocityModel.TOBLER,
    is_on_path: bool = True,
) -> float:
    """
    Dispatch to the selected velocity model.
    Returns velocity in km/h.
    VEL-03, VEL-06
    """
    if model == VelocityModel.TOBLER:
        return tobler(slope, is_on_path)
    return irmischer_clarke(slope)
