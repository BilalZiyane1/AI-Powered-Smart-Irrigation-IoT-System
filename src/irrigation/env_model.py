"""Deterministic, intentionally simplified soil environment model."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Measurement:
    timestamp_minute: float
    soil_moisture: float
    air_temperature: float
    rainfall: float
    evaporation: float
    irrigation: float
    anomaly_labels: tuple[str, ...] = ()


class SoilEnv:
    """Simulate moisture dynamics for repeatable closed-loop experiments.

    This is a control and testing model, not a validated physical crop model.
    """

    def __init__(
        self,
        *,
        initial_moisture: float = 50.0,
        seed: int | None = 0,
        moisture_per_minute_pump: float = 0.12,
        noise_std: float = 0.25,
    ) -> None:
        self.initial_moisture = float(initial_moisture)
        self.moisture_per_minute_pump = float(moisture_per_minute_pump)
        self.noise_std = float(noise_std)
        self.reset(seed)

    def reset(self, seed: int | None = None) -> Measurement:
        self.rng = np.random.default_rng(seed)
        self.minute = 0.0
        self._true_moisture = self.initial_moisture
        self._stuck_value: float | None = None
        self._drift = 0.0
        return self._measurement(0.0, False)

    def inject_anomaly(self, anomaly: str, *, value: float | None = None) -> None:
        """Enable one supported sensor/actuator fault for subsequent steps."""
        if anomaly == "stuck_sensor":
            self._stuck_value = self._true_moisture if value is None else float(value)
        elif anomaly == "sensor_drift":
            self._drift = 0.1
        elif anomaly == "pump_failure":
            self._pump_failure = True
        elif anomaly == "sudden_spike":
            self._spike_next = 20.0 if value is None else float(value)
        else:
            raise ValueError(f"Unsupported anomaly: {anomaly}")

    def step(self, dt_min: float, pump_on: bool) -> dict[str, Any]:
        if dt_min <= 0:
            raise ValueError("dt_min must be positive")
        self.minute += float(dt_min)
        hour = (self.minute / 60.0) % 24.0
        daylight = max(0.0, math.sin(math.pi * (hour - 6.0) / 12.0))
        temperature = 18.0 + 10.0 * math.sin(2.0 * math.pi * (hour - 8.0) / 24.0)
        rainfall = float(self.rng.random() < 0.015) * float(self.rng.uniform(0.0, 3.0))
        evaporation = max(0.0, 0.012 * (temperature - 5.0) * (0.25 + daylight))
        irrigation = (
            self.moisture_per_minute_pump * dt_min
            if pump_on and not getattr(self, "_pump_failure", False)
            else 0.0
        )
        self._true_moisture = float(
            np.clip(self._true_moisture + rainfall + irrigation - evaporation, 0.0, 100.0)
        )
        return self._measurement(rainfall, pump_on, temperature, evaporation, irrigation)

    def _measurement(
        self,
        rainfall: float,
        pump_on: bool,
        temperature: float | None = None,
        evaporation: float = 0.0,
        irrigation: float = 0.0,
    ) -> Measurement:
        if temperature is None:
            hour = (self.minute / 60.0) % 24.0
            temperature = 18.0 + 10.0 * math.sin(2.0 * math.pi * (hour - 8.0) / 24.0)
        labels: list[str] = []
        observed = self._true_moisture + float(self.rng.normal(0.0, self.noise_std))
        if self._stuck_value is not None:
            observed = self._stuck_value
            labels.append("stuck_sensor")
        if self._drift:
            self._drift += 0.1
            observed += self._drift
            labels.append("sensor_drift")
        if hasattr(self, "_spike_next"):
            observed += self._spike_next
            del self._spike_next
            labels.append("sudden_spike")
        if pump_on and irrigation == 0.0:
            labels.append("pump_failure")
        return Measurement(
            timestamp_minute=self.minute,
            soil_moisture=float(np.clip(observed, 0.0, 100.0)),
            air_temperature=float(temperature),
            rainfall=float(rainfall),
            evaporation=float(evaporation),
            irrigation=float(irrigation),
            anomaly_labels=tuple(labels),
        )
