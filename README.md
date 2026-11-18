# Smart Irrigation IoT System

*Résumé français : ce projet met en place une chaîne IoT locale pour surveiller
l'humidité du sol, prévoir son évolution et commander une pompe virtuelle.*

This repository implements a local smart-irrigation demonstrator for the
Mendeley agricultural dataset supplied in the workspace. It uses MQTT for
telemetry, CoAP for pump commands, Node-RED for orchestration, InfluxDB for
time-series storage, and Python for replay, simulation and machine learning.

## Current verified foundation

- Dataset schema inspected from `README.md` and `DATA_DICTIONARY.md`.
- Sector 1 is configured as the initial sector (`TOMATO_SOIL`, 10-minute grid).
- Timestamp normalization is explicit: source Europe/Rome naive timestamps are
  converted to UTC.
- `SoilEnv` provides seeded day/night temperature, rainfall, evaporation,
  irrigation and anomaly injection.
- Rule and predictive controllers enforce hysteresis, rainfall suppression,
  minimum activation interval and maximum runtime.
- Dataset replay publishes JSON soil and weather messages with MQTT QoS 1.
- A Python aiocoap pump exposes `/pump/on`, `/pump/off` and `/pump/state`.
- Podman Compose definitions are present for Mosquitto, InfluxDB and Node-RED.

## Prerequisites

Python 3.11+ and Podman Compose are recommended. Docker-compatible Compose
files are used, but the verified runtime for this project is Podman 5.8.9 with
podman-compose 1.6.0.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

## Start the local infrastructure with Podman

```bash
podman-compose config
podman-compose up -d --build
podman-compose ps
```

If host port `1883` is already occupied, use:

```bash
MQTT_HOST_PORT=1884 podman-compose up -d --build
```

Node-RED editor: http://localhost:1880  
FlowFuse Dashboard: http://localhost:1880/dashboard  
InfluxDB: http://localhost:8086

The flow file is copied into the Node-RED data volume. If the volume already
contains a deployment, import [`nodered/flows.json`](nodered/flows.json) from
the editor or remove only the named `nodered-data` volume and recreate it.

## Run the Python components

From the project root:

```bash
python -m src.irrigation.pump_sim --mqtt-host localhost
python -m src.irrigation.sensor_sim --interval-seconds 1 --limit 100
```

The pump simulator must be running before a CoAP command is sent. The sensor
replay uses the preserved processed sector-1 dataset and does not modify it.

## Dataset and configuration

The source is the *Soil Moisture, Irrigation Actuator and Weather Dataset from
a Multi-Sector Precision-Irrigation* (CC BY 4.0). See
[`docs/PLAN.md`](docs/PLAN.md) and the original
[`README.md`](Soil%20Moisture%2C%20Irrigation%20Actuator%20and%20Weather%20Dat/README.md)
for provenance and the column dictionary. Change `dataset.sector` and the
template in [`config.yaml`](config.yaml) to replay another processed sector.

## Current implementation status

- ML forecasting service and online anomaly detection are implemented.
- HTTP-to-CoAP gateway and safe Node-RED decision path are implemented.
- Closed-loop policy experiment and protocol benchmark scaffolds are
  implemented.
- The Podman smoke test passes against the running Mosquitto, InfluxDB and
  Node-RED services.
- Dashboard widgets and full InfluxDB write nodes remain the next integration
  refinement; the current dashboard URL is reserved by the installed FlowFuse
  package and must not be mistaken for populated analytics until those nodes
  are deployed.
