"""
DAT service — file parsing and geometry extraction.

Handles:
  - GPX files via gpxpy (tracks → LineString 3DZ)
  - GeoJSON files with LineString or MultiLineString features
  - Segment splitting at fixed intervals (default 100 m)
  - Slope and elevation extraction per segment

Domain rule: coordinates are always (lon, lat, elev) in SRID 4326.
"""

from __future__ import annotations

import io
import json
import math
import re
from typing import Any

import gpxpy
import gpxpy.gpx
from fastapi import HTTPException, UploadFile, status

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EARTH_RADIUS_M = 6_371_000.0
DEFAULT_SEGMENT_LENGTH_M = 100.0

# GeoTIFF magic bytes (LE and BE variants of the TIFF header)
_TIFF_MAGIC_LE = b"\x49\x49\x2a\x00"
_TIFF_MAGIC_BE = b"\x4d\x4d\x00\x2a"

MAX_DEM_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB — ST_FromGDALRaster loads the whole file
DEM_TILE_SIZE_PX = 100                 # pixel edge length per raster tile


# ---------------------------------------------------------------------------
# Public entry points — routes
# ---------------------------------------------------------------------------


async def parse_upload(file: UploadFile) -> dict[str, Any]:
    """
    Parse an uploaded GPX or GeoJSON file and return route geometry data.

    Returns
    -------
    dict with keys:
        name: str | None
        source_format: 'gpx' | 'geojson'
        coords: list[tuple[lon, lat, elev]]  — full 3DZ coordinate list
        geom_wkt: WKT of the full LineString
        segments_data: list of segment dicts ready for the repository
    """
    raw = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".gpx"):
        return _parse_gpx(raw)
    if filename.endswith(".geojson") or filename.endswith(".json"):
        return _parse_geojson(raw)

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Unsupported file format. Upload a .gpx or .geojson file.",
    )


def _raise_422(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Public entry points — DEM (DAT-04)
# ---------------------------------------------------------------------------


async def read_and_validate_dem(file: UploadFile) -> bytes:
    """
    Read a DEM upload and validate it is a GeoTIFF.

    Returns the raw bytes ready for PostGIS ingestion via ST_FromGDALRaster.
    Raises HTTPException on format or size violations.
    """
    raw = await file.read()

    if len(raw) > MAX_DEM_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"DEM file exceeds the {MAX_DEM_SIZE_BYTES // (1024 * 1024)} MB limit.",
        )

    if not (raw[:4] == _TIFF_MAGIC_LE or raw[:4] == _TIFF_MAGIC_BE):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="DEM must be a GeoTIFF file (.tif / .tiff).",
        )

    return raw


def make_dem_table_name(name: str) -> str:
    """
    Convert an arbitrary DEM name to a safe, predictable PostgreSQL table name.

    Example: 'Copernicus DEM 30m' → 'dem_copernicus_dem_30m'
    """
    clean = re.sub(r"[^a-z0-9]", "_", name.lower())
    clean = re.sub(r"_+", "_", clean).strip("_") or "raster"
    return f"dem_{clean}"


# ---------------------------------------------------------------------------
# GPX parser
# ---------------------------------------------------------------------------


def _parse_gpx(raw: bytes) -> dict[str, Any]:
    try:
        gpx = gpxpy.parse(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid GPX file: {exc}",
        ) from exc

    coords: list[tuple[float, float, float]] = []
    name: str | None = None

    for track in gpx.tracks:
        if name is None:
            name = track.name
        for segment in track.segments:
            for point in segment.points:
                elev = point.elevation or 0.0
                coords.append((point.longitude, point.latitude, elev))

    if len(coords) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="GPX file must contain at least 2 track points.",
        )

    return _build_result(coords, name=name, source_format="gpx")


# ---------------------------------------------------------------------------
# GeoJSON parser
# ---------------------------------------------------------------------------


def _parse_geojson(raw: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid JSON: {exc}",
        ) from exc

    coords: list[tuple[float, float, float]] = []
    name: str | None = None

    features = _extract_features(data)

    for feature in features:
        geom = feature.get("geometry") if isinstance(feature, dict) else feature
        props = feature.get("properties") or {} if isinstance(feature, dict) else {}

        if name is None:
            name = props.get("name") or props.get("title")

        geom_type = geom.get("type", "")
        raw_coords = geom.get("coordinates", [])

        if geom_type == "LineString":
            coords.extend(_normalise_coords(raw_coords))
        elif geom_type == "MultiLineString":
            for line in raw_coords:
                coords.extend(_normalise_coords(line))
        else:
            # Skip non-line features silently
            continue

    if len(coords) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="GeoJSON must contain a LineString or MultiLineString with at least 2 points.",
        )

    return _build_result(coords, name=name, source_format="geojson")


def _extract_features(data: dict) -> list[dict]:
    """Normalise FeatureCollection, Feature, or bare geometry."""
    if data.get("type") == "FeatureCollection":
        return data.get("features", [])
    if data.get("type") == "Feature":
        return [data]
    # Bare geometry
    return [{"geometry": data, "properties": {}}]


def _normalise_coords(
    raw: list[list[float]],
) -> list[tuple[float, float, float]]:
    """Ensure every coordinate triplet has (lon, lat, elev). Elev defaults to 0."""
    result = []
    for c in raw:
        lon, lat = float(c[0]), float(c[1])
        elev = float(c[2]) if len(c) > 2 else 0.0
        result.append((lon, lat, elev))
    return result


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _build_result(
    coords: list[tuple[float, float, float]],
    *,
    name: str | None,
    source_format: str,
) -> dict[str, Any]:
    geom_wkt = _coords_to_linestring_wkt(coords)
    segments_data = _split_into_segments(coords)
    return {
        "name": name,
        "source_format": source_format,
        "coords": coords,
        "geom_wkt": geom_wkt,
        "segments_data": segments_data,
    }


def _coords_to_linestring_wkt(coords: list[tuple[float, float, float]]) -> str:
    """Build a WKT LINESTRINGZ from a list of (lon, lat, elev) tuples."""
    pts = ", ".join(f"{lon} {lat} {elev}" for lon, lat, elev in coords)
    return f"LINESTRINGZ({pts})"


def _haversine_m(
    lon1: float, lat1: float, lon2: float, lat2: float
) -> float:
    """Horizontal distance in metres between two WGS-84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _split_into_segments(
    coords: list[tuple[float, float, float]],
    segment_length_m: float = DEFAULT_SEGMENT_LENGTH_M,
) -> list[dict[str, Any]]:
    """
    Walk the coordinate list and emit a segment dict every `segment_length_m` metres.
    The last segment may be shorter than the target length.

    Each segment dict contains:
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
            # Interpolate a closing point exactly at the segment boundary
            fraction = remaining / step_m if step_m > 0 else 0.0
            closing = _interpolate(prev, curr, fraction)
            current_pts.append(closing)
            segments.append(_make_segment(seq, current_pts, current_len + remaining))
            seq += 1

            # The rest of the step becomes the start of a new segment
            leftover_m = step_m - remaining
            current_pts = [closing]
            current_len = 0.0

            # If the leftover is already longer than a full segment, keep splitting
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

            # Leftover becomes the first partial step of the next segment
            current_pts.append(curr)
            current_len = leftover_m
        else:
            current_pts.append(curr)
            current_len += step_m

    # Flush whatever remains as the final (possibly short) segment
    if len(current_pts) >= 2:
        segments.append(_make_segment(seq, current_pts, current_len))

    return segments


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


def _make_segment(
    seq: int,
    pts: list[tuple[float, float, float]],
    length_m: float,
) -> dict[str, Any]:
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
    }
