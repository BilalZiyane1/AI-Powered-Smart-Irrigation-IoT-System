"""Dataset loading and chronological replay helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd
import yaml


@dataclass(frozen=True)
class DatasetConfig:
    root: Path
    processed_template: str
    sector: int
    timezone: str
    sampling_interval_minutes: int
    columns: dict[str, str]


def load_config(path: str | Path = "config.yaml") -> DatasetConfig:
    with Path(path).open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    dataset = raw["dataset"]
    return DatasetConfig(
        root=Path(dataset["root"]),
        processed_template=dataset["processed_template"],
        sector=int(dataset["sector"]),
        timezone=dataset["timezone"],
        sampling_interval_minutes=int(dataset["sampling_interval_minutes"]),
        columns=dict(dataset["columns"]),
    )


def load_sector_frame(config: DatasetConfig) -> pd.DataFrame:
    path = config.root / config.processed_template.format(sector=config.sector)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset sector file does not exist: {path}")
    frame = pd.read_csv(path)
    timestamp_column = config.columns["timestamp"]
    if timestamp_column not in frame.columns:
        raise ValueError(f"Missing configured timestamp column {timestamp_column!r} in {path}")
    frame[timestamp_column] = normalize_timestamps(
        frame[timestamp_column], timezone=config.timezone
    )
    frame = frame.dropna(subset=[timestamp_column]).sort_values(timestamp_column)
    duplicate_count = int(frame.duplicated(timestamp_column).sum())
    if duplicate_count:
        frame = frame.drop_duplicates(timestamp_column, keep="first")
    return frame.reset_index(drop=True)


def normalize_timestamps(values: pd.Series, *, timezone: str) -> pd.Series:
    timestamps = pd.to_datetime(values, errors="coerce")
    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize(
            timezone, ambiguous="NaT", nonexistent="shift_forward"
        )
    return timestamps.dt.tz_convert("UTC")


def replay_rows(frame: pd.DataFrame, config: DatasetConfig) -> Iterator[dict[str, object]]:
    mapping = config.columns
    timestamp_column = mapping["timestamp"]
    for row in frame.to_dict(orient="records"):
        yield {
            "timestamp": row[timestamp_column].isoformat(),
            "sector": config.sector,
            "soil_moisture": _number(row.get(mapping["soil_moisture"])),
            "air_temperature": _number(row.get(mapping["air_temperature"])),
            "rainfall": _number(row.get(mapping["rainfall"])),
            "irrigation_duration_minutes": _number(row.get(mapping["irrigation_duration"])),
            "applied_water_liters": _number(row.get(mapping["applied_water"])),
        }


def _number(value: object) -> float | None:
    return None if pd.isna(value) else float(value)
