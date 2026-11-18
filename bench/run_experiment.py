"""Compare rule-based and predictive irrigation in the closed-loop SoilEnv."""

from __future__ import annotations

import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from src.irrigation.controllers import ControllerConfig, PredictiveController, RuleController
from src.irrigation.env_model import SoilEnv


def run_policy(policy: str, seed: int, days: int) -> tuple[dict[str, float | int | str], list[float]]:
    env = SoilEnv(initial_moisture=50, seed=seed, noise_std=0)
    config = ControllerConfig()
    controller = RuleController(config) if policy == "rule" else PredictiveController(config)
    moisture_values: list[float] = []
    water = 0.0
    stress_minutes = 0.0
    saturated_minutes = 0.0
    activations = 0
    previous = False
    trajectory: list[float] = []
    for _step in range(days * 24 * 6):
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
        trajectory.append(measurement.soil_moisture)
        water += measurement.irrigation
        stress_minutes += 10 if measurement.soil_moisture < config.low_threshold else 0
        saturated_minutes += 10 if measurement.soil_moisture >= config.high_threshold else 0
    return ({
        "policy": policy,
        "seed": seed,
        "days": days,
        "water_liters": round(water, 3),
        "stress_minutes": stress_minutes,
        "activations": activations,
        "mean_moisture": sum(moisture_values) / len(moisture_values),
        "minimum_moisture": min(moisture_values),
        "above_high_threshold_minutes": saturated_minutes,
    }, trajectory)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--output", default="results/irrigation/comparison.csv")
    args = parser.parse_args()
    results = [
        run_policy(policy, seed, args.days)
        for seed in range(args.seeds)
        for policy in ("rule", "predictive")
    ]
    rows = [item[0] for item in results]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} closed-loop results to {output}")
    plots = output.parent
    plot_policy_trajectories(results, plots)
    write_markdown(rows, plots)


def plot_policy_trajectories(
    results: list[tuple[dict[str, float | int | str], list[float]]],
    output: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for item in results:
        row, trajectory = item
        ax.plot(np.arange(len(trajectory)) * 10 / 1440, trajectory, alpha=0.35,
                label=f"{row['policy']} seed {row['seed']}")
    ax.axhline(40, color="tab:red", linestyle="--", label="Stress threshold")
    ax.set_xlabel("Simulated days")
    ax.set_ylabel("Soil moisture (%)")
    ax.set_title("Closed-loop moisture trajectories")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "moisture_trajectories.png", dpi=150)
    plt.close(fig)


def write_markdown(rows: list[dict[str, float | int | str]], output: Path) -> None:
    policies = sorted({str(row["policy"]) for row in rows})
    lines = ["# Closed-loop irrigation comparison", "",
             "| Policy | Seeds | Water (mean +/- sd) | Stress min (mean +/- sd) | Activations (mean +/- sd) | Mean moisture (mean +/- sd) |",
             "|---|---:|---:|---:|---:|---:|"]
    for policy in policies:
        subset = [row for row in rows if row["policy"] == policy]
        def stats(field: str) -> tuple[float, float]:
            values = np.asarray([float(row[field]) for row in subset])
            return float(values.mean()), float(values.std())
        water_mean, water_sd = stats("water_liters")
        stress_mean, stress_sd = stats("stress_minutes")
        activation_mean, activation_sd = stats("activations")
        moisture_mean, moisture_sd = stats("mean_moisture")
        lines.append(
            f"| {policy} | {len(subset)} | {water_mean:.2f} +/- {water_sd:.2f} "
            f"| {stress_mean:.1f} +/- {stress_sd:.1f} "
            f"| {activation_mean:.1f} +/- {activation_sd:.1f} "
            f"| {moisture_mean:.2f} +/- {moisture_sd:.2f} |"
        )
    lines.extend(["", "## Limitation", "",
                  "These results come from a simplified deterministic/seeded soil model and do not validate agronomic performance."])
    (output / "comparison.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
