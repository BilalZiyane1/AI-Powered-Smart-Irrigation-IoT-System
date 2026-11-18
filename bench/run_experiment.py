"""Compare rule-based and predictive irrigation in the closed-loop SoilEnv."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.irrigation.controllers import ControllerConfig, PredictiveController, RuleController
from src.irrigation.env_model import SoilEnv


def run_policy(policy: str, seed: int, days: int) -> dict[str, float | int | str]:
    env = SoilEnv(initial_moisture=50, seed=seed, noise_std=0)
    config = ControllerConfig()
    controller = RuleController(config) if policy == "rule" else PredictiveController(config)
    moisture_values: list[float] = []
    water = 0.0
    stress_minutes = 0.0
    saturated_minutes = 0.0
    activations = 0
    previous = False
    for _ in range(days * 24 * 6):
        current = env._true_moisture
        if policy == "rule":
            pump = controller.decide(minute=env.minute, moisture=current)
        else:
            predicted = current - 0.8
            pump = controller.decide(
                minute=env.minute,
                moisture=current,
                predicted_moisture=predicted,
            )
        if pump and not previous:
            activations += 1
        measurement = env.step(10, pump)
        previous = pump
        moisture_values.append(measurement.soil_moisture)
        water += measurement.irrigation
        stress_minutes += 10 if measurement.soil_moisture < config.low_threshold else 0
        saturated_minutes += 10 if measurement.soil_moisture >= config.high_threshold else 0
    return {
        "policy": policy,
        "seed": seed,
        "days": days,
        "water_liters": round(water, 3),
        "stress_minutes": stress_minutes,
        "activations": activations,
        "mean_moisture": sum(moisture_values) / len(moisture_values),
        "minimum_moisture": min(moisture_values),
        "above_high_threshold_minutes": saturated_minutes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--output", default="results/irrigation/comparison.csv")
    args = parser.parse_args()
    rows = [
        run_policy(policy, seed, args.days)
        for seed in range(args.seeds)
        for policy in ("rule", "predictive")
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} closed-loop results to {output}")


if __name__ == "__main__":
    main()
