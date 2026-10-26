"""Deterministic broad-input invariant matrix for Nurion array shards.

This is a software robustness gate, not an API 581 certification calculation.
Each shard evaluates disjoint generated cases so PBS arrays can run them in
parallel and expose boundary/rounding regressions quickly.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
import sys
import time

# Make this verification script runnable from a source checkout as well as an
# installed Nurion payload.  The latter already has api581 on sys.path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from api581.core import evaluate


def _finite(value):
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(v) for v in value)
    return value is None or (isinstance(value, (int, float)) and math.isfinite(value)) or isinstance(value, (str, bool))


def _run_case(rng: random.Random, index: int) -> None:
    diameter = 1e-4 + rng.random() * 0.25
    pressure = 101325.0 + rng.random() * 8.0e6
    density = 300.0 + rng.random() * 1100.0
    liquid = evaluate("release/liquid", {
        "diameter_m": diameter, "upstream_pressure_pa_abs": pressure,
        "density_kg_m3": density,
    })["outputs"]
    assert liquid["mass_rate_kg_s"] >= 0 and _finite(liquid)

    gas = evaluate("release/gas", {
        "diameter_m": diameter, "upstream_pressure_pa_abs": pressure,
        "temperature_k": 180.0 + rng.random() * 600.0,
        "molecular_weight_kg_kmol": 2.0 + rng.random() * 190.0,
        "heat_capacity_ratio": 1.05 + rng.random() * 0.65,
    })["outputs"]
    assert gas["mass_rate_kg_s"] >= 0 and gas["regime"] in {"sonic", "subsonic"} and _finite(gas)

    rate = rng.random() * 300.0
    available = 1e-9 + rng.random() * 2.0e5
    magnitude = evaluate("release/magnitude", {
        "theoretical_rate_kg_s": rate, "reduction_fraction": rng.random(),
        "available_mass_kg": available, "maximum_duration_s": 1e-6 + rng.random() * 1.0e5,
    })["outputs"]
    assert magnitude["released_mass_kg"] >= 0 and magnitude["released_mass_kg"] <= available * (1 + 1e-12)
    assert _finite(magnitude)

    frequency = rng.random() * 1000.0
    years = 1e-8 + rng.random() * 80.0
    poisson = evaluate("reliability/poisson-probability", {
        "annual_failure_frequency": frequency, "duration_years": years,
    })["outputs"]
    assert 0.0 <= poisson["period_failure_probability"] <= 1.0 and _finite(poisson)

    peak = rng.random() * 300.0
    duration = 1e-5 + rng.random() * 10000.0
    points = [{"time_s": 0.0, "rate_kg_s": 0.0},
              {"time_s": duration / 2, "rate_kg_s": peak},
              {"time_s": duration, "rate_kg_s": 0.0}]
    profile = evaluate("release/integrate-profile", {
        "points": points, "available_mass_kg": peak * duration + 1.0,
    })["outputs"]
    assert profile["released_mass_kg"] >= 0 and _finite(profile)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--cases-per-shard", type=int, default=200)
    parser.add_argument("--seed", type=int, default=581)
    args = parser.parse_args()
    if args.shard_index < 0 or args.shard_count < 1 or args.shard_index >= args.shard_count:
        raise SystemExit("invalid shard coordinates")
    if args.cases_per_shard < 1:
        raise SystemExit("cases-per-shard must be positive")
    started = time.perf_counter()
    rng = random.Random(args.seed + args.shard_index * 100003)
    for offset in range(args.cases_per_shard):
        _run_case(rng, args.shard_index * args.cases_per_shard + offset)
    elapsed = time.perf_counter() - started
    print(json.dumps({"status": "passed", "shard_index": args.shard_index,
                      "shard_count": args.shard_count, "cases": args.cases_per_shard,
                      "elapsed_seconds": elapsed,
                      "cases_per_second": args.cases_per_shard / elapsed if elapsed else None}, indent=2))


if __name__ == "__main__":
    main()
