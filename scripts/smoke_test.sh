#!/usr/bin/env bash
set -euo pipefail

MQTT_HOST_PORT="${MQTT_HOST_PORT:-1884}"
fail() { echo "FAIL: $1" >&2; exit 1; }

command -v podman >/dev/null || fail "podman is not installed"
podman-compose ps >/dev/null || fail "Podman Compose is not available"
curl -fsS http://localhost:8086/health >/dev/null || fail "InfluxDB is unavailable"
curl -fsS http://localhost:1880/ >/dev/null || fail "Node-RED is unavailable"
timeout 5 bash -c "</dev/tcp/127.0.0.1/${MQTT_HOST_PORT}" || fail "MQTT is unavailable"

python -m src.irrigation.sensor_sim \
  --broker-host localhost \
  --broker-port "${MQTT_HOST_PORT}" \
  --interval-seconds 0 \
  --limit 1 >/dev/null || fail "sensor replay failed"

echo "PASS: Podman infrastructure, MQTT connectivity, and dataset replay"
