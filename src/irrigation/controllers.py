"""Irrigation controller policies used by orchestration and experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerConfig:
    low_threshold: float = 40.0
    high_threshold: float = 60.0
    min_activation_interval_minutes: float = 30.0
    max_pump_runtime_minutes: float = 60.0


class RuleController:
    def __init__(self, config: ControllerConfig = ControllerConfig()) -> None:
        self.config = config
        self.pump_on = False
        self.last_activation_minute = float("-inf")
        self.activation_minute: float | None = None

    def decide(self, *, minute: float, moisture: float, rainfall: float = 0.0) -> bool:
        if self.pump_on:
            if moisture >= self.config.high_threshold or self._runtime(minute) >= self.config.max_pump_runtime_minutes:
                self.pump_on = False
        elif (
            moisture < self.config.low_threshold
            and rainfall <= 0
            and minute - self.last_activation_minute >= self.config.min_activation_interval_minutes
        ):
            self.pump_on = True
            self.last_activation_minute = minute
            self.activation_minute = minute
        return self.pump_on

    def _runtime(self, minute: float) -> float:
        return 0.0 if self.activation_minute is None else minute - self.activation_minute


class PredictiveController(RuleController):
    def decide(
        self,
        *,
        minute: float,
        moisture: float,
        predicted_moisture: float | None,
        rainfall: float = 0.0,
        prediction_fresh: bool = True,
    ) -> bool:
        signal = moisture
        if predicted_moisture is not None and prediction_fresh:
            signal = min(moisture, predicted_moisture)
        return super().decide(minute=minute, moisture=signal, rainfall=rainfall)
