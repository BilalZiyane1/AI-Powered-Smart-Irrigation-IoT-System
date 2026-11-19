# Startup fixes — missing dataset readings and CoAP gateway

## Problem verified

Sector 1's first valid soil-moisture reading is not present in the first 228
dataset rows. The replay service previously counted and published rows even
when `soil_moisture` was `None`. With a 100-row replay limit, it could therefore
finish without publishing real moisture.

Node-RED also used `Number(null)`, whose JavaScript value is `0`. This could
cause a missing reading to activate irrigation as if the soil were extremely dry.

## Applied corrections

1. `sensor_sim.py` validates `soil_moisture` before publishing both sensor and
   weather records.
2. Missing, non-numeric, negative, and over-100 readings are ignored.
3. The replay limit counts valid published soil readings, not missing rows.
4. The Node-RED validation function rejects `null`, `NaN`, negative values,
   and values above 100.
5. The Node-RED irrigation decision repeats these null and range checks.
6. Dashboard gauge/chart formatting repeats the range check.
7. Automatic and manual pump commands use the internal Compose address:
   `http://coap-gateway:8081/pump`.
8. The host-specific `host.containers.internal` address was removed from flows.

## Verification

- 11 pytest tests pass.
- Node-RED JSON parses successfully.
- Node-RED starts and connects to Mosquitto.
- All Compose services are running.
- Automated unit/static tests cover missing readings and internal gateway URLs.

## Deployment

After updating an existing Node-RED persistent volume:

```bash
podman cp nodered/flows.json projet_nodered_1:/data/flows.json
podman restart projet_nodered_1
```

Or rebuild the stack:

```bash
MQTT_HOST_PORT=1884 podman-compose up -d --build
```
