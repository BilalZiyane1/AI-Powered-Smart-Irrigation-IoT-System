"""Dataset replay publisher for the soil and weather MQTT topics."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from .data_loader import load_config, load_sector_frame, replay_rows

LOGGER = logging.getLogger(__name__)


def publish_replay(
    *,
    config_path: str = "config.yaml",
    broker_host: str | None = None,
    broker_port: int | None = None,
    interval_seconds: float = 1.0,
    limit: int | None = None,
) -> int:
    config = load_config(config_path)
    frame = load_sector_frame(config)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="soil-replay")
    client.connect(broker_host or "localhost", broker_port or 1883, keepalive=30)
    client.loop_start()
    stopped = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    published = 0
    try:
        for row in replay_rows(frame, config):
            if stopped or (limit is not None and published >= limit):
                break
            timestamp = row["timestamp"]
            soil_payload = {
                "timestamp": timestamp,
                "device_id": "SUT00001",
                "sector": row["sector"],
                "soil_moisture": row["soil_moisture"],
                "unit": "%",
            }
            weather_payload = {
                "timestamp": timestamp,
                "device_id": "WEATHER_ERA5",
                "sector": row["sector"],
                "air_temperature": row["air_temperature"],
                "rainfall": row["rainfall"],
                "unit_temperature": "degC",
                "unit_rainfall": "mm",
            }
            client.publish(config_topic(config_path, "soil"), json.dumps(soil_payload), qos=1)
            client.publish(config_topic(config_path, "weather"), json.dumps(weather_payload), qos=1)
            published += 1
            time.sleep(max(0.0, interval_seconds))
    finally:
        client.loop_stop()
        client.disconnect()
    LOGGER.info("Published %d dataset rows", published)
    return published


def config_topic(config_path: str, name: str) -> str:
    import yaml
    with open(config_path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return raw["mqtt"]["topics"][name]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--broker-host", default=None)
    parser.add_argument("--broker-port", type=int, default=None)
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    publish_replay(
        config_path=args.config,
        broker_host=args.broker_host,
        broker_port=args.broker_port,
        interval_seconds=args.interval_seconds,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
