#!/usr/bin/env python3
"""Compare Tobler vs Irmischer-Clarke on real GPX routes."""
import json
import time
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
BASE_DIR = Path(__file__).resolve().parent.parent

GPX_FILES = [
    ("Volcan Baru", str(BASE_DIR / "data" / "samples" / "volcan-baru-chiriqui-panama.gpx")),
    ("Camino de Cruces", str(BASE_DIR / "data" / "samples" / "sendero-camino-real-de-cruces-gamboa-venta-de-cruces-av-madd (1).gpx")),
]
MODELS = ["tobler", "irmischer_clarke"]

def risk_level(score: int) -> int:
    """Map 0-100 risk score to 1-5 level."""
    if score < 20:
        return 1
    if score < 40:
        return 2
    if score < 60:
        return 3
    if score < 80:
        return 4
    return 5

def run_analysis(route_name: str, gpx_path: str, model: str) -> dict:
    """Upload, process, and analyze a GPX route."""
    print(f"\n{'='*60}")
    print(f"  {route_name} — {model}")
    print(f"{'='*60}")

    with open(gpx_path, "rb") as f:
        upload = httpx.post(
            f"{BASE}/routes/upload",
            files={"file": (gpx_path.split("/")[-1], f, "application/gpx+xml")},
            timeout=30,
        )
    if upload.status_code != 201:
        print(f"  ERROR upload: {upload.status_code} {upload.text[:200]}")
        return {}
    route_id = upload.json()["route_id"]
    print(f"  Route ID: {route_id}")

    t0 = time.time()
    process = httpx.post(f"{BASE}/routes/{route_id}/process", timeout=60)
    process_time = time.time() - t0
    if process.status_code != 200:
        print(f"  ERROR process: {process.status_code} {process.text[:200]}")
        return {}
    segments_count = process.json().get("segment_count", "?")
    print(f"  Segments: {segments_count} (process time: {process_time:.2f}s)")

    t0 = time.time()
    analysis = httpx.post(
        f"{BASE}/routes/{route_id}/biomechanical",
        json={
            "profile": {"weight_kg": 70, "load_kg": 10, "fitness_level": "medium"},
            "velocity_model": model,
        },
        timeout=60,
    )
    api_time = time.time() - t0
    if analysis.status_code != 200:
        print(f"  ERROR analysis: {analysis.status_code} {analysis.text[:200]}")
        return {}

    data = analysis.json()
    summary = data["summary"]
    segments = data["segments"]

    # Risk distribution
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for seg in segments:
        level = risk_level(seg["risk_score"])
        dist[level] += 1

    print(f"  API time: {api_time:.2f}s")
    print(f"  Total distance: {summary['total_distance_km']:.2f} km")
    print(f"  Est. time: {summary['estimated_time_h']:.2f} h")
    print(f"  Elevation gain: {summary['elevation_gain_m']:.0f} m / loss: {summary['elevation_loss_m']:.0f} m")
    print(f"  Total kcal: {summary['total_kcal']:.0f}")
    print(f"  MIDE global: {summary['mide_global']}")
    print(f"  MIDE effort: {summary['mide_effort_level']}")
    print(f"  CCR: {summary['ccr']:.0f}")
    print(f"  Risk distribution: {dist}")
    print(f"  Max risk score: {max(s['risk_score'] for s in segments)}")

    # Avg velocity
    avg_vel = sum(s["velocity_kmh"] for s in segments) / len(segments)
    print(f"  Avg velocity: {avg_vel:.2f} km/h")

    # Min/Max velocity
    min_vel = min(s["velocity_kmh"] for s in segments)
    max_vel = max(s["velocity_kmh"] for s in segments)
    print(f"  Velocity range: {min_vel:.2f} - {max_vel:.2f} km/h")

    return {
        "route_name": route_name,
        "model": model,
        "segments_count": len(segments),
        "api_time": round(api_time, 2),
        "total_distance_km": round(summary["total_distance_km"], 2),
        "estimated_time_h": round(summary["estimated_time_h"], 2),
        "elevation_gain_m": round(summary["elevation_gain_m"], 0),
        "elevation_loss_m": round(summary["elevation_loss_m"], 0),
        "total_kcal": round(summary["total_kcal"], 0),
        "mide_global": summary["mide_global"],
        "mide_effort": summary["mide_effort_level"],
        "ccr": round(summary["ccr"], 0),
        "risk_distribution": dist,
        "max_risk_score": max(s["risk_score"] for s in segments),
        "avg_velocity_kmh": round(avg_vel, 2),
        "min_velocity_kmh": round(min_vel, 2),
        "max_velocity_kmh": round(max_vel, 2),
    }


def main():
    results = []
    for route_name, gpx_path in GPX_FILES:
        for model in MODELS:
            r = run_analysis(route_name, gpx_path, model)
            if r:
                results.append(r)

    # Summary table
    print(f"\n\n{'='*80}")
    print("  RESUMEN COMPARATIVO")
    print(f"{'='*80}")

    for route_name in ["Volcan Baru", "Camino de Cruces"]:
        route_results = [r for r in results if r["route_name"] == route_name]
        if len(route_results) < 2:
            continue

        tobler = route_results[0]
        irmischer = route_results[1]

        print(f"\n--- {route_name} ---")
        print(f"  {'Metric':<25} {'Tobler':>12} {'Irmischer':>12} {'Diff':>10}")
        print(f"  {'-'*60}")
        for key in ["segments_count", "api_time", "estimated_time_h", "total_kcal",
                     "max_risk_score", "avg_velocity_kmh", "min_velocity_kmh", "max_velocity_kmh",
                     "mide_global", "ccr"]:
            tv = tobler.get(key, "?")
            iv = irmischer.get(key, "?")
            try:
                diff = iv - tv if isinstance(tv, (int, float)) and isinstance(iv, (int, float)) else "?"
                if isinstance(diff, float):
                    diff = f"{diff:+.2f}"
                elif isinstance(diff, int):
                    diff = f"{diff:+d}"
            except:
                diff = "?"
            print(f"  {key:<25} {tv:>12} {iv:>12} {diff:>10}")

        print(f"\n  Risk Distribution:")
        print(f"  {'Level':<10} {'Tobler':>10} {'Irmischer':>10}")
        for level in [1, 2, 3, 4, 5]:
            print(f"  {level:<10} {tobler['risk_distribution'][level]:>10} {irmischer['risk_distribution'][level]:>10}")

    print(f"\n{'='*80}")

    # Save results
    with open("/tmp/velocity_comparison.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /tmp/velocity_comparison.json")


if __name__ == "__main__":
    main()
