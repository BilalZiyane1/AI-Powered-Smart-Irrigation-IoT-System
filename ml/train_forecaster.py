"""Train chronological soil-moisture forecasting baselines and tree models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.irrigation.data_loader import load_config, load_sector_frame
from src.irrigation.features import DEFAULT_FEATURES, add_forecasting_features, model_matrix


def train(
    *,
    config_path: str = "config.yaml",
    horizon_minutes: int = 60,
    output_dir: str = "results/forecasting",
    model_dir: str = "ml/models",
) -> dict[str, object]:
    config = load_config(config_path)
    frame = load_sector_frame(config)
    frame = frame.rename(
        columns={
            config.columns["timestamp"]: "ts",
            config.columns["air_temperature"]: "weather_temp",
            config.columns["rainfall"]: "weather_rain",
            config.columns["irrigation_duration"]: "irrigation_duration_minutes",
            config.columns["applied_water"]: "liters_total",
        }
    )
    frame["soil_moisture"] = pd.to_numeric(frame["soil_moisture"], errors="coerce")
    frame.loc[~frame["soil_moisture"].between(0, 100), "soil_moisture"] = pd.NA
    frame["soil_moisture"] = frame["soil_moisture"].interpolate(limit=2)
    for column in ("weather_humidity", "weather_wind_speed", "weather_radiation"):
        if column not in frame:
            frame[column] = 0.0
    engineered, target_name = add_forecasting_features(
        frame,
        horizon_minutes=horizon_minutes,
        sampling_interval_minutes=config.sampling_interval_minutes,
    )
    engineered = engineered.dropna(subset=list(DEFAULT_FEATURES) + [target_name]).reset_index(drop=True)
    if len(engineered) < 100:
        raise ValueError(f"Not enough complete rows for training: {len(engineered)}")
    split_train = int(len(engineered) * 0.7)
    split_validation = int(len(engineered) * 0.85)
    train_frame = engineered.iloc[:split_train]
    test_frame = engineered.iloc[split_validation:]
    x_train = model_matrix(train_frame)
    y_train = train_frame[target_name]
    x_test = model_matrix(test_frame)
    y_test = test_frame[target_name]
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    models = {
        "persistence": None,
        "linear_regression": make_pipeline(StandardScaler(), LinearRegression()),
        "random_forest": RandomForestRegressor(
            n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(random_state=42, n_estimators=100),
    }
    metrics: dict[str, dict[str, float]] = {}
    best_name = ""
    best_mae = float("inf")
    for name, model in models.items():
        if model is None:
            predictions = test_frame["soil_moisture"].to_numpy()
        else:
            model.fit(x_train, y_train)
            predictions = model.predict(x_test)
            joblib.dump(model, Path(model_dir) / f"{name}_{horizon_minutes}m.joblib")
        current = {
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(mean_squared_error(y_test, predictions) ** 0.5),
            "r2": float(r2_score(y_test, predictions)),
        }
        metrics[name] = current
        if name != "persistence" and current["mae"] < best_mae:
            best_name, best_mae = name, current["mae"]
    result = {
        "sector": config.sector,
        "horizon_minutes": horizon_minutes,
        "sampling_interval_minutes": config.sampling_interval_minutes,
        "rows_used": len(engineered),
        "features": list(DEFAULT_FEATURES),
        "chronological_split": {"train": split_train, "validation": split_validation},
        "metrics": metrics,
        "best_model": best_name,
    }
    Path(output_dir, f"metrics_{horizon_minutes}m.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--horizon-minutes", type=int, default=60)
    args = parser.parse_args()
    result = train(config_path=args.config, horizon_minutes=args.horizon_minutes)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
