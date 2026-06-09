"""
Unit tests for DAT service — parsing and segment splitting.
These tests run without a database (pure logic only).
"""

from __future__ import annotations

import io
import json
import math
import textwrap

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.modules.dat.service import (
    DEFAULT_SEGMENT_LENGTH_M,
    _haversine_m,
    _split_into_segments,
    _coords_to_linestring_wkt,
    _parse_geojson,
    _parse_gpx,
)


# ---------------------------------------------------------------------------
# Helper: build an UploadFile-like bytes object
# ---------------------------------------------------------------------------


def make_upload(content: bytes, filename: str) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers=Headers({}),
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


class TestHaversine:
    def test_same_point_is_zero(self) -> None:
        assert _haversine_m(0, 0, 0, 0) == pytest.approx(0.0)

    def test_one_degree_latitude(self) -> None:
        # 1° of latitude ≈ 111 km
        d = _haversine_m(0.0, 0.0, 0.0, 1.0)
        assert 110_000 < d < 112_000

    def test_equator_one_degree_longitude(self) -> None:
        # On the equator, 1° longitude ≈ 111 km
        d = _haversine_m(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 112_000


class TestLineStringWKT:
    def test_2d_fallback(self) -> None:
        coords = [(10.0, 20.0, 0.0), (10.1, 20.1, 100.0)]
        wkt = _coords_to_linestring_wkt(coords)
        assert wkt.startswith("LINESTRINGZ(")
        assert "10.0 20.0 0.0" in wkt
        assert "10.1 20.1 100.0" in wkt


# ---------------------------------------------------------------------------
# Segment splitting
# ---------------------------------------------------------------------------


class TestSegmentSplitting:
    def _straight_line(
        self,
        n_points: int = 200,
        step_m: float = 10.0,
    ) -> list[tuple[float, float, float]]:
        """
        Build a straight-north line with `n_points` at `step_m` spacing.
        Longitude fixed at 0°; latitude advances northward.
        Each point is 1 m higher than the previous.
        """
        # 1° latitude ≈ 111_195 m
        deg_per_m = 1.0 / 111_195.0
        return [
            (0.0, i * step_m * deg_per_m, float(i))
            for i in range(n_points)
        ]

    def test_segment_count_matches_total_length(self) -> None:
        coords = self._straight_line(n_points=200, step_m=10.0)
        # Total ≈ 1990 m → expect ceil(1990/100) = 20 segments
        segs = _split_into_segments(coords, segment_length_m=100.0)
        total = sum(s["length_m"] for s in segs)
        assert total == pytest.approx(1990.0, abs=5.0)  # allow 5m floating-point drift
        assert len(segs) == 20

    def test_sequence_numbers_are_contiguous(self) -> None:
        coords = self._straight_line(n_points=100, step_m=10.0)
        segs = _split_into_segments(coords)
        seqs = [s["seq"] for s in segs]
        assert seqs == list(range(len(segs)))

    def test_each_segment_has_required_keys(self) -> None:
        coords = self._straight_line(n_points=50, step_m=10.0)
        segs = _split_into_segments(coords)
        required = {"seq", "geom_wkt", "length_m", "elevation_start", "elevation_end", "slope_pct"}
        for seg in segs:
            assert required.issubset(seg.keys())

    def test_slope_sign_for_ascent(self) -> None:
        # All points go uphill → slope_pct should be positive
        coords = self._straight_line(n_points=150, step_m=10.0)
        segs = _split_into_segments(coords)
        for seg in segs:
            assert seg["slope_pct"] >= 0.0

    def test_slope_sign_for_descent(self) -> None:
        coords = self._straight_line(n_points=150, step_m=10.0)
        # Reverse elevation to make it downhill
        descending = [(lon, lat, float(len(coords) - i)) for i, (lon, lat, _) in enumerate(coords)]
        segs = _split_into_segments(descending)
        for seg in segs:
            assert seg["slope_pct"] <= 0.0

    def test_two_point_route_produces_one_segment(self) -> None:
        coords = [(0.0, 0.0, 0.0), (0.0, 0.0005, 5.0)]
        segs = _split_into_segments(coords)
        assert len(segs) == 1


# ---------------------------------------------------------------------------
# GeoJSON parser (pure, no DB)
# ---------------------------------------------------------------------------


class TestGeoJSONParser:
    def _make_line_feature(
        self,
        coords: list[list[float]],
        name: str | None = None,
    ) -> bytes:
        feature = {
            "type": "Feature",
            "properties": {"name": name} if name else {},
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
        }
        return json.dumps(feature).encode()

    def test_parses_linstring_feature(self) -> None:
        raw = self._make_line_feature([[0.0, 0.0, 0.0], [0.1, 0.1, 100.0], [0.2, 0.2, 200.0]])
        result = _parse_geojson(raw)
        assert result["source_format"] == "geojson"
        assert len(result["coords"]) == 3
        assert result["coords"][0] == pytest.approx((0.0, 0.0, 0.0))

    def test_extracts_name_from_properties(self) -> None:
        raw = self._make_line_feature([[0.0, 0.0], [0.1, 0.1]], name="Test Trail")
        result = _parse_geojson(raw)
        assert result["name"] == "Test Trail"

    def test_missing_elevation_defaults_to_zero(self) -> None:
        raw = self._make_line_feature([[0.0, 0.0], [0.1, 0.1]])
        result = _parse_geojson(raw)
        for coord in result["coords"]:
            assert coord[2] == pytest.approx(0.0)

    def test_feature_collection_is_supported(self) -> None:
        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [0.1, 0.1]]},
                }
            ],
        }
        result = _parse_geojson(json.dumps(fc).encode())
        assert len(result["coords"]) == 2

    def test_invalid_json_raises_422(self) -> None:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _parse_geojson(b"not json")
        assert exc_info.value.status_code == 422

    def test_single_point_raises_422(self) -> None:
        from fastapi import HTTPException
        raw = self._make_line_feature([[0.0, 0.0]])
        with pytest.raises(HTTPException) as exc_info:
            _parse_geojson(raw)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# GPX parser (pure, no DB)
# ---------------------------------------------------------------------------


GPX_SAMPLE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
      <trk>
        <name>Test Track</name>
        <trkseg>
          <trkpt lat="9.0" lon="-79.5"><ele>10.0</ele></trkpt>
          <trkpt lat="9.01" lon="-79.49"><ele>50.0</ele></trkpt>
          <trkpt lat="9.02" lon="-79.48"><ele>100.0</ele></trkpt>
        </trkseg>
      </trk>
    </gpx>
""").encode()


class TestGPXParser:
    def test_parses_track_name(self) -> None:
        result = _parse_gpx(GPX_SAMPLE)
        assert result["name"] == "Test Track"

    def test_parses_coordinates_with_elevation(self) -> None:
        result = _parse_gpx(GPX_SAMPLE)
        assert len(result["coords"]) == 3
        # GPX uses lat/lon order — service stores as (lon, lat, elev)
        lon, lat, elev = result["coords"][0]
        assert lat == pytest.approx(9.0)
        assert lon == pytest.approx(-79.5)
        assert elev == pytest.approx(10.0)

    def test_source_format_is_gpx(self) -> None:
        result = _parse_gpx(GPX_SAMPLE)
        assert result["source_format"] == "gpx"

    def test_wkt_is_linestringz(self) -> None:
        result = _parse_gpx(GPX_SAMPLE)
        assert result["geom_wkt"].startswith("LINESTRINGZ(")

    def test_invalid_gpx_raises_422(self) -> None:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _parse_gpx(b"<not>gpx</not>")
        assert exc_info.value.status_code == 422
