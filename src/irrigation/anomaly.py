"""Online anomaly detection for sensor and actuator telemetry."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass(frozen=True)
class Anomaly:
    kind: str
    score: float
    message: str


class OnlineAnomalyDetector:
    def __init__(self, *, window: int = 12, z_threshold: float = 3.0) -> None:
        self.values: deque[float] = deque(maxlen=window)
        self.z_threshold = z_threshold
        self._forest: IsolationForest | None = None
        self._feature_rows: deque[list[float]] = deque(maxlen=256)

    def update(
        self,
        moisture: float,
        *,
        pump_on: bool = False,
        irrigation_effect: float | None = None,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        if not math.isfinite(moisture) or not 0 <= moisture <= 100:
            return [Anomaly("invalid_reading", 1.0, "Moisture is outside 0-100%")]
        if len(self.values) >= 4:
            values = np.asarray(self.values)
            mean, std = float(values.mean()), float(values.std())
            if std > 0 and abs(moisture - mean) / std >= self.z_threshold:
                anomalies.append(Anomaly("statistical_spike", abs(moisture - mean) / std, "Sudden moisture change"))
            if len(set(round(value, 3) for value in self.values)) == 1:
                anomalies.append(Anomaly("stuck_sensor", 1.0, "Sensor value has not changed"))
        if pump_on and irrigation_effect is not None and irrigation_effect <= 0:
            anomalies.append(Anomaly("pump_no_response", 1.0, "Pump is on but moisture did not increase"))
        self.values.append(moisture)
        row = [moisture, float(self.values[-1] - self.values[-2]) if len(self.values) > 1 else 0.0]
        self._feature_rows.append(row)
        if len(self._feature_rows) >= 32:
            if self._forest is None:
                self._forest = IsolationForest(random_state=42, contamination="auto").fit(self._feature_rows)
            if self._forest.predict([row])[0] == -1:
                anomalies.append(Anomaly("isolation_forest", 1.0, "Engineered telemetry row is unusual"))
        return anomalies
