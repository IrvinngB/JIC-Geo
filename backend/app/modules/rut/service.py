"""
RUT — Route segmentation and gradient processing service.
Implements the pipeline: DEM extraction → spike detection → Savitzky-Golay
→ segmentation → gradient calculation.

All functions are pure (no I/O). RUT-01 to RUT-11.
"""

from __future__ import annotations

import math
from typing import Any

from scipy.signal import savgol_filter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EARTH_RADIUS_M = 6_371_000.0
MAX_PLAUSIBLE_GRADIENT = 0.75  # RUT-10


# ---------------------------------------------------------------------------
# DEM elevation extraction
# ---------------------------------------------------------------------------


def extract_elevations_from_dem(
    coords: list[tuple[float, float, float]],
    dem_values: list[float | None],
) -> list[tuple[float, float, float]]:
    """
    Replace GPX elevations with DEM elevations where available.
    RUT-08: Interpolation is assumed done by PostGIS ST_Value(Bilinear).

    Parameters
    ----------
    coords: list of (lon, lat, elev)
    dem_values: list of float | None, same length as coords

    Returns
    -------
    list of (lon, lat, elev) with DEM elevations where available.
    """
    result = []
    for (lon, lat, elev), dem_elev in zip(coords, dem_values, strict=True):
        if dem_elev is not None:
            result.append((lon, lat, float(dem_elev)))
        else:
            result.append((lon, lat, elev))
    return result


# ---------------------------------------------------------------------------
# Spike detection & repair
# ---------------------------------------------------------------------------


def detect_and_repair_spikes(
    points: list[tuple[float, float, float]],
) -> tuple[list[tuple[float, float, float]], int]:
    """
    Detect points with implausible gradient |S| > 0.75 and replace elevation
    by linear interpolation between the previous and next valid point.

    RUT-10

    Returns
    -------
    (cleaned_points, points_corrected)
    """
    clean, corrected_indexes = _detect_and_repair_spikes_with_indexes(points)
    return clean, len(corrected_indexes)


def _detect_and_repair_spikes_with_indexes(
    points: list[tuple[float, float, float]],
) -> tuple[list[tuple[float, float, float]], set[int]]:
    """Internal variant that keeps the indexes corrected for RUT-11 persistence."""
    if len(points) < 2:
        return list(points), set()

    corrected_indexes: set[int] = set()
    clean = list(points)

    for i in range(1, len(clean)):
        dh = clean[i][2] - clean[i - 1][2]
        dx = _haversine_m(clean[i - 1][0], clean[i - 1][1], clean[i][0], clean[i][1])
        if dx > 0 and abs(dh / dx) > MAX_PLAUSIBLE_GRADIENT:
            prev_elev = clean[i - 1][2]
            next_elev = clean[min(i + 1, len(clean) - 1)][2]
            clean[i] = (
                clean[i][0],
                clean[i][1],
                (prev_elev + next_elev) / 2.0,
            )
            corrected_indexes.add(i)

    return clean, corrected_indexes


# ---------------------------------------------------------------------------
# Savitzky-Golay smoothing
# ---------------------------------------------------------------------------


def smooth_elevations(
    points: list[tuple[float, float, float]],
    window: int = 5,
) -> list[tuple[float, float, float]]:
    """
    Apply Savitzky-Golay filter to the elevation series.
    RUT-09

    Parameters
    ----------
    points: list of (lon, lat, elev)
    window: window length (must be odd, >= 5)

    Returns
    -------
    list of (lon, lat, smoothed_elev)
    """
    if window % 2 == 0:
        raise ValueError("Savitzky-Golay window must be odd.")

    if len(points) < window:
        return list(points)

    elevations = [p[2] for p in points]
    smoothed = savgol_filter(elevations, window_length=window, polyorder=2).tolist()

    return [(lon, lat, float(elev)) for (lon, lat, _), elev in zip(points, smoothed, strict=True)]


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------


def split_into_segments(
    coords: list[tuple[float, float, float]],
    segment_length_m: float = 100.0,
) -> list[dict[str, Any]]:
    """
    Walk the coordinate list and emit a segment dict every `segment_length_m`.
    RUT-01

    Each segment contains:
        seq, geom_wkt, length_m, elevation_start, elevation_end, slope_pct
    """
    segments: list[dict[str, Any]] = []
    current_pts: list[tuple[float, float, float]] = [coords[0]]
    current_len = 0.0
    seq = 0

    for i in range(1, len(coords)):
        prev = coords[i - 1]
        curr = coords[i]
        step_m = _haversine_m(prev[0], prev[1], curr[0], curr[1])

        remaining = segment_length_m - current_len

        if step_m >= remaining:
            fraction = remaining / step_m if step_m > 0 else 0.0
            closing = _interpolate(prev, curr, fraction)
            current_pts.append(closing)
            segments.append(_make_segment(seq, current_pts, current_len + remaining))
            seq += 1

            leftover_m = step_m - remaining
            current_pts = [closing]
            current_len = 0.0

            start_frac = fraction
            while leftover_m >= segment_length_m:
                end_frac = start_frac + (segment_length_m / step_m)
                end_pt = _interpolate(prev, curr, end_frac)
                current_pts.append(end_pt)
                segments.append(_make_segment(seq, current_pts, segment_length_m))
                seq += 1
                current_pts = [end_pt]
                leftover_m -= segment_length_m
                start_frac = end_frac

            current_pts.append(curr)
            current_len = leftover_m
        else:
            current_pts.append(curr)
            current_len += step_m

    if len(current_pts) >= 2:
        segments.append(_make_segment(seq, current_pts, current_len))

    return segments


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Horizontal distance in metres between two WGS-84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _interpolate(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    """Linear interpolation between two 3D points at fraction t ∈ [0, 1]."""
    return (
        a[0] + t * (b[0] - a[0]),
        a[1] + t * (b[1] - a[1]),
        a[2] + t * (b[2] - a[2]),
    )


def _coords_to_linestring_wkt(
    coords: list[tuple[float, float, float]],
) -> str:
    """Build a WKT LINESTRINGZ from a list of (lon, lat, elev) tuples."""
    pts = ", ".join(f"{lon} {lat} {elev}" for lon, lat, elev in coords)
    return f"LINESTRINGZ({pts})"


def _make_segment(
    seq: int,
    pts: list[tuple[float, float, float]],
    length_m: float,
) -> dict[str, Any]:
    """Build a segment dict with elevation and slope."""
    elev_start = pts[0][2]
    elev_end = pts[-1][2]
    delta_h = elev_end - elev_start
    slope_pct = (delta_h / length_m) if length_m > 0 else 0.0

    return {
        "seq": seq,
        "geom_wkt": _coords_to_linestring_wkt(pts),
        "length_m": round(length_m, 3),
        "elevation_start": round(elev_start, 3),
        "elevation_end": round(elev_end, 3),
        "slope_pct": round(slope_pct, 6),
        "elevation_interpolated": False,
    }


def _mark_segments_with_corrected_points(
    segments: list[dict[str, Any]],
    corrected_points: list[tuple[float, float, float]],
) -> list[dict[str, Any]]:
    """Mark segments whose geometry contains a corrected elevation point (RUT-11)."""
    if not corrected_points:
        return segments

    corrected_xy = {(round(lon, 8), round(lat, 8)) for lon, lat, _ in corrected_points}

    for segment in segments:
        segment_xy = _coords_from_linestring_wkt(segment["geom_wkt"])
        segment["elevation_interpolated"] = bool(corrected_xy.intersection(segment_xy))

    return segments


def _coords_from_linestring_wkt(wkt: str) -> set[tuple[float, float]]:
    body = wkt.removeprefix("LINESTRINGZ(").removesuffix(")")
    coords: set[tuple[float, float]] = set()
    for raw_point in body.split(","):
        parts = raw_point.strip().split()
        if len(parts) >= 2:
            coords.add((round(float(parts[0]), 8), round(float(parts[1]), 8)))
    return coords


# ---------------------------------------------------------------------------
# Direction & elevation stats
# ---------------------------------------------------------------------------


def mark_ascent_descent(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    RUT-03: Mark each segment as 'ascent' or 'descent'.
    """
    for seg in segments:
        seg["direction"] = "ascent" if seg["slope_pct"] > 0 else "descent"
    return segments


def calculate_route_elevation_stats(
    segments: list[dict[str, Any]],
) -> dict[str, float]:
    """
    RUT-05, RUT-06: Calculate total elevation gain and loss.
    """
    gain = 0.0
    loss = 0.0
    for seg in segments:
        dh = seg["elevation_end"] - seg["elevation_start"]
        if dh > 0:
            gain += dh
        else:
            loss += abs(dh)
    return {"elevation_gain_m": gain, "elevation_loss_m": loss}


# ---------------------------------------------------------------------------
# High-level pipeline (pure orchestration)
# ---------------------------------------------------------------------------


def process_route_pipeline(
    coords: list[tuple[float, float, float]],
    dem_values: list[float | None] | None = None,
    segment_length_m: float = 100.0,
    window: int = 5,
) -> dict[str, Any]:
    """
    Pure pipeline that applies the full RUT processing chain.

    Parameters
    ----------
    coords: raw (lon, lat, elev) from GPX
    dem_values: optional DEM elevations, same length as coords
    segment_length_m: target segment length
    window: Savitzky-Golay window

    Returns
    -------
    dict with keys:
        segments, points_corrected, elevation_gain_m, elevation_loss_m,
        processed_coords
    """
    # RUT-08: DEM interpolation
    if dem_values:
        coords = extract_elevations_from_dem(coords, dem_values)

    # RUT-10: Spike detection
    cleaned, corrected_indexes = _detect_and_repair_spikes_with_indexes(coords)
    corrected_points = [cleaned[i] for i in sorted(corrected_indexes)]

    # RUT-09: Savitzky-Golay
    smoothed = smooth_elevations(cleaned, window=window)

    # RUT-01: Segmentation
    segments = split_into_segments(smoothed, segment_length_m)
    segments = _mark_segments_with_corrected_points(segments, corrected_points)

    # RUT-03: Ascent / descent
    segments = mark_ascent_descent(segments)

    # RUT-05 / RUT-06: Stats
    stats = calculate_route_elevation_stats(segments)

    return {
        "segments": segments,
        "points_corrected": len(corrected_indexes),
        "elevation_gain_m": stats["elevation_gain_m"],
        "elevation_loss_m": stats["elevation_loss_m"],
        "processed_coords": smoothed,
    }
