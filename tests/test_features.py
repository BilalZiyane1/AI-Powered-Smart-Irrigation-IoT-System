import pandas as pd
import pytest

from src.irrigation.features import add_forecasting_features


def test_features_use_only_past_values():
    frame = pd.DataFrame(
        {
            "ts": pd.date_range("2025-01-01", periods=10, freq="10min"),
            "soil_moisture": range(10),
            "weather_temp": [20] * 10,
            "weather_humidity": [50] * 10,
            "weather_rain": [0] * 10,
            "weather_wind_speed": [1] * 10,
            "weather_radiation": [0] * 10,
            "irrigation_duration_minutes": [0] * 10,
            "liters_total": [0] * 10,
        }
    )
    result, target = add_forecasting_features(frame, horizon_minutes=20)
    assert result.loc[3, "soil_moisture_lag_1"] == 2
    assert result.loc[3, target] == 5


def test_horizon_must_match_sampling_grid():
    with pytest.raises(ValueError):
        add_forecasting_features(pd.DataFrame({"ts": [], "soil_moisture": []}), horizon_minutes=15)
