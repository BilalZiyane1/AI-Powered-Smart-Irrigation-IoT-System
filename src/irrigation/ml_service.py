"""Online MQTT forecasting and anomaly service."""

from __future__ import annotations

import argparse
from collections import deque
import json
import logging
from pathlib import Path

import joblib
import pandas as pd
import paho.mqtt.client as mqtt

from .anomaly import OnlineAnomalyDetector
from .features import DEFAULT_FEATURES, add_forecasting_features, model_matrix

LOGGER = logging.getLogger(__name__)


class MLService:
    def __init__(
        self,
        *,
        broker_host: str,
        broker_port: int,
        model_path: str,
        topics: dict[str, str],
        horizon_minutes: int = 60,
    ) -> None:
        self.topics = topics
        self.model = joblib.load(Path(model_path))
        self.buffer: deque[dict[str, object]] = deque(maxlen=64)
        self.detector = OnlineAnomalyDetector()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="irrigation-ml")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.broker_host, self.broker_port = broker_host, broker_port
        self.horizon_minutes = horizon_minutes

    def _on_connect(self, client: mqtt.Client, _userdata: object, _flags: object, reason_code: object, _properties: object = None) -> None:
        if reason_code != 0:
            LOGGER.error("MQTT connection failed: %s", reason_code)
            return
        client.subscribe(self.topics["soil"], qos=1)
        client.subscribe(self.topics["weather"], qos=1)

    def _on_message(self, client: mqtt.Client, _userdata: object, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload)
            if message.topic == self.topics["weather"] and self.buffer:
                self.buffer[-1]["weather_temp"] = payload.get("air_temperature")
                self.buffer[-1]["weather_rain"] = payload.get("rainfall", 0.0)
                self._publish_prediction(client, payload)
                return
            if message.topic != self.topics["soil"]:
                return
            if payload.get("soil_moisture") is None:
                LOGGER.warning("Skipping missing soil-moisture reading")
                return
            self.buffer.append({
                "ts": payload["timestamp"],
                "soil_moisture": payload.get("soil_moisture"),
                "weather_temp": None,
                "weather_humidity": 0.0,
                "weather_rain": 0.0,
                "weather_wind_speed": 0.0,
                "weather_radiation": 0.0,
                "irrigation_duration_minutes": 0.0,
                "liters_total": 0.0,
            })
            anomalies = self.detector.update(float(payload["soil_moisture"]))
            for anomaly in anomalies:
                client.publish(self.topics["anomaly"], json.dumps({
                    "timestamp": payload["timestamp"],
                    "type": anomaly.kind,
                    "message": anomaly.message,
                }), qos=1)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.error("Invalid ML input: %s", exc)

    def _publish_prediction(self, client: mqtt.Client, payload: dict[str, object]) -> None:
        if len(self.buffer) < 8:
            return
        frame, _target = add_forecasting_features(
            pd.DataFrame(self.buffer), horizon_minutes=self.horizon_minutes
        )
        row = frame.dropna(subset=list(DEFAULT_FEATURES)).tail(1)
        if row.empty:
            return
        prediction = float(self.model.predict(model_matrix(row))[0])
        client.publish(self.topics["prediction"], json.dumps({
            "timestamp": payload["timestamp"],
            "horizon_minutes": self.horizon_minutes,
            "predicted_soil_moisture": prediction,
            "model": "linear_regression",
        }), qos=1)

    def run(self) -> None:
        self.client.connect(self.broker_host, self.broker_port, keepalive=30)
        self.client.loop_forever()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker-host", default="localhost")
    parser.add_argument("--broker-port", type=int, default=1883)
    parser.add_argument("--model", default="ml/models/linear_regression_60m.joblib")
    parser.add_argument("--horizon-minutes", type=int, default=60)
    args = parser.parse_args()
    topics = {
        "soil": "ferme/parcelle1/humidite_sol",
        "weather": "ferme/parcelle1/meteo",
        "prediction": "ferme/parcelle1/prediction",
        "anomaly": "ferme/parcelle1/anomalie",
    }
    logging.basicConfig(level=logging.INFO)
    MLService(
        broker_host=args.broker_host,
        broker_port=args.broker_port,
        model_path=args.model,
        topics=topics,
        horizon_minutes=args.horizon_minutes,
    ).run()


if __name__ == "__main__":
    main()
