"""Leakage-safe feature engineering for soil-moisture forecasting."""

from __future__ import annotations

from collections.abc import Sequence
import math

import pandas as pd


DEFAULT_FEATURES = (
    "soil_moisture",
    "soil_moisture_lag_1",
    "soil_moisture_lag_3",
    "soil_moisture_lag_6",
    "soil_moisture_rolling_mean_6",
    "soil_moisture_rolling_std_6",
    "moisture_trend_6",
    "weather_temp",
    "weather_humidity",
    "weather_rain",
    "weather_wind_speed",
    "weather_radiation",
    "irrigation_duration_minutes",
    "water_vol_past_4h",
    "hour_sin",
    "hour_cos",
)


def add_forecasting_features(
    frame: pd.DataFrame,
    *,
    timestamp_column: str = "ts",
    sampling_interval_minutes: int = 10,
    horizon_minutes: int = 60,
) -> tuple[pd.DataFrame, str]:
    """Return features and a future target without reading future values as inputs."""
    if horizon_minutes <= 0 or horizon_minutes % sampling_interval_minutes:
        raise ValueError("horizon_minutes must be a positive multiple of sampling_interval_minutes")
    result = frame.copy()
    result[timestamp_column] = pd.to_datetime(result[timestamp_column], utc=True)
    result = result.sort_values(timestamp_column).reset_index(drop=True)
    moisture = result["soil_moisture"].astype(float)
    result["soil_moisture_lag_1"] = moisture.shift(1)
    result["soil_moisture_lag_3"] = moisture.shift(3)
    result["soil_moisture_lag_6"] = moisture.shift(6)
    result["soil_moisture_rolling_mean_6"] = moisture.rolling(6, min_periods=2).mean()
    result["soil_moisture_rolling_std_6"] = moisture.rolling(6, min_periods=2).std().fillna(0)
    result["moisture_trend_6"] = moisture.diff(6)
    hours = result[timestamp_column].dt.hour + result[timestamp_column].dt.minute / 60
    radians = 2 * math.pi * hours / 24
    result["hour_sin"] = radians.map(math.sin)
    result["hour_cos"] = radians.map(math.cos)
    if "water_vol_past_4h" not in result:
        bins = max(1, round(240 / sampling_interval_minutes))
        water = result.get("liters_total", pd.Series(0.0, index=result.index)).fillna(0)
        result["water_vol_past_4h"] = water.rolling(bins, min_periods=1).sum()
    steps = horizon_minutes // sampling_interval_minutes
    target = f"target_soil_moisture_{horizon_minutes}m"
    result[target] = moisture.shift(-steps)
    return result, target


def model_matrix(frame: pd.DataFrame, features: Sequence[str] = DEFAULT_FEATURES) -> pd.DataFrame:
    missing = [name for name in features if name not in frame.columns]
    if missing:
        raise ValueError(f"Missing forecasting features: {missing}")
    return frame.loc[:, list(features)].replace([float("inf"), float("-inf")], pd.NA)
