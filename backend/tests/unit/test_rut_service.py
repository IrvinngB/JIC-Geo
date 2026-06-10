"""
Unit tests for RUT service — pure logic, no database.
Validates against reference values from Formulas.md and plan.md.
"""

from __future__ import annotations

import math

import pytest

from app.modules.rut.service import (
    EARTH_RADIUS_M,
    _haversine_m,
    calculate_route_elevation_stats,
    detect_and_repair_spikes,
    extract_elevations_from_dem,
    mark_ascent_descent,
    process_route_pipeline,
    smooth_elevations,
    split_into_segments,
)


# ---------------------------------------------------------------------------
# DEM extraction
# ---------------------------------------------------------------------------


class TestExtractElevationsFromDem:
    def test_replaces_elevation_when_dem_available(self):
        coords = [(0.0, 0.0, 100.0), (0.0, 0.0, 100.0)]
        dem = [150.0, None]
        result = extract_elevations_from_dem(coords, dem)
        assert result[0][2] == 150.0
        assert result[1][2] == 100.0


# ---------------------------------------------------------------------------
# Spike detection
# ---------------------------------------------------------------------------


class TestDetectAndRepairSpikes:
    def test_no_correction_on_flat_terrain(self):
        pts = [(0.0, 0.0, 0.0), (0.0, 0.001, 0.0)]  # ~111 m flat
        clean, corrected = detect_and_repair_spikes(pts)
        assert corrected == 0
        assert clean[1][2] == 0.0

    def test_corrects_implausible_spike(self):
        # 10 m horizontal, 100 m vertical → S = 10.0 (impossible)
        pts = [(0.0, 0.0, 0.0), (0.0, 0.00009, 100.0), (0.0, 0.00018, 0.0)]
        clean, corrected = detect_and_repair_spikes(pts)
        assert corrected == 1
        # Interpolated between previous (0) and next (0)
        assert clean[1][2] == pytest.approx(0.0, abs=0.1)

    def test_corrects_multiple_spikes(self):
        pts = [
            (0.0, 0.0, 0.0),
            (0.0, 0.00009, 100.0),  # spike
            (0.0, 0.00018, 0.0),
        ]
        clean, corrected = detect_and_repair_spikes(pts)
        assert corrected == 1


# ---------------------------------------------------------------------------
# Savitzky-Golay
# ---------------------------------------------------------------------------


class TestSmoothElevations:
    def test_preserves_length(self):
        pts = [(0.0, 0.0, float(i)) for i in range(10)]
        smoothed = smooth_elevations(pts, window=5)
        assert len(smoothed) == len(pts)

    def test_short_input_returns_unchanged(self):
        pts = [(0.0, 0.0, 1.0), (0.0, 0.0, 2.0)]
        smoothed = smooth_elevations(pts, window=5)
        assert smoothed == pts

    def test_smooths_noise(self):
        pts = [(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0)]
        smoothed = smooth_elevations(pts, window=5)
        # With a symmetric parabola, the middle point should be close to average
        assert smoothed[2][2] == pytest.approx(0.686, abs=0.1)


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------


class TestSplitIntoSegments:
    def test_count_matches_length(self):
        # 200 points at ~10 m spacing = ~1990 m → 20 segments of 100 m
        deg_per_m = 1.0 / 111_195.0
        coords = [(0.0, i * 10.0 * deg_per_m, float(i)) for i in range(200)]
        segs = split_into_segments(coords, segment_length_m=100.0)
        total = sum(s["length_m"] for s in segs)
        assert total == pytest.approx(1990.0, abs=10.0)
        assert len(segs) == 20

    def test_slope_sign_for_descent(self):
        coords = [(0.0, 0.0, 100.0), (0.0, 0.001, 50.0)]
        segs = split_into_segments(coords, segment_length_m=1000.0)
        assert segs[0]["slope_pct"] < 0

    def test_segment_has_required_keys(self):
        coords = [(0.0, 0.0, 0.0), (0.0, 0.001, 10.0)]
        segs = split_into_segments(coords)
        required = {"seq", "geom_wkt", "length_m", "elevation_start", "elevation_end", "slope_pct"}
        assert required.issubset(segs[0].keys())


# ---------------------------------------------------------------------------
# Direction & stats
# ---------------------------------------------------------------------------


class TestMarkAscentDescent:
    def test_positive_slope_is_ascent(self):
        segs = [{"slope_pct": 0.05}]
        result = mark_ascent_descent(segs)
        assert result[0]["direction"] == "ascent"

    def test_negative_slope_is_descent(self):
        segs = [{"slope_pct": -0.05}]
        result = mark_ascent_descent(segs)
        assert result[0]["direction"] == "descent"


class TestCalculateRouteElevationStats:
    def test_mixed_segments(self):
        segs = [
            {"elevation_start": 0.0, "elevation_end": 10.0},
            {"elevation_start": 10.0, "elevation_end": 5.0},
            {"elevation_start": 5.0, "elevation_end": 15.0},
        ]
        stats = calculate_route_elevation_stats(segs)
        assert stats["elevation_gain_m"] == 20.0
        assert stats["elevation_loss_m"] == 5.0


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------


class TestProcessRoutePipeline:
    def test_pipeline_without_dem(self):
        coords = [(0.0, 0.0, 0.0), (0.0, 0.001, 10.0), (0.0, 0.002, 20.0)]
        result = process_route_pipeline(coords, segment_length_m=1000.0)
        assert result["points_corrected"] == 0
        assert result["elevation_gain_m"] == pytest.approx(20.0, abs=1.0)
        assert len(result["segments"]) > 0

    def test_pipeline_with_dem(self):
        coords = [(0.0, 0.0, 0.0), (0.0, 0.001, 10.0)]
        dem = [5.0, 15.0]
        result = process_route_pipeline(coords, dem_values=dem, segment_length_m=1000.0)
        assert result["segments"][0]["elevation_start"] == pytest.approx(5.0, abs=0.1)
        assert result["segments"][0]["elevation_end"] == pytest.approx(15.0, abs=0.1)

    def test_pipeline_detects_spikes(self):
        # ~10 m horizontal, 100 m vertical
        coords = [(0.0, 0.0, 0.0), (0.0, 0.00009, 100.0), (0.0, 0.00018, 0.0)]
        result = process_route_pipeline(coords)
        assert result["points_corrected"] >= 1
