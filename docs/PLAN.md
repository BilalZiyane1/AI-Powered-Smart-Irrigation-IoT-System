# Smart Irrigation Implementation Plan

## Verified starting point

The supplied Mendeley dataset is available locally under the original extracted
directory. The initial demonstration uses processed sector 1:

- `ts`: local Europe/Rome naive timestamp in the source; normalized to UTC at load time.
- `soil_moisture`: relative soil moisture percentage.
- `weather_temp`: ERA5 air temperature in °C.
- `weather_rain`: ERA5 interval rainfall in mm.
- `irrigation_duration_minutes`: reconstructed valve-open duration.
- `liters_total`: applied water in litres.
- Sector 1 is open-field tomato (`TOMATO_SOIL`) with PWP 20, MADP 40, FC 60 and SP 80.
- The processed tables use a regular 10-minute grid. The raw sensor exports are event/minute based.

The original extracted dataset remains unmodified. Application copies and generated
outputs belong under `data/` and `results/`.

## Architectural decisions

1. MQTT carries telemetry and asynchronous state/prediction events.
2. CoAP carries pump commands; an HTTP gateway is used only when Node-RED cannot
   reliably act as an aiocoap client.
3. Node-RED remains the orchestration and dashboard layer, not a replacement for
   the Python ML service.
4. Rule-based irrigation is always available as a safety fallback.
5. Historical replay is used for training and pipeline demonstrations. Closed-loop
   controller comparisons use the seeded `SoilEnv` model because recorded future
   moisture cannot react to new commands.
6. Configuration holds dataset mappings, thresholds, broker addresses and timing.

## Dependencies and compatibility risks

- Python 3.11+; pandas, NumPy, scikit-learn, joblib, paho-mqtt, aiocoap and
  aiohttp are used by Python components.
- Podman Compose is the verified container runtime for Mosquitto, Node-RED and
  InfluxDB. The compose file remains Docker-compatible.
- FlowFuse Dashboard package names and Node-RED node configuration can change;
  flows will be validated after deployment rather than treated as generated code.
- CoAP UDP connectivity must be tested separately from MQTT TCP connectivity.
- The source timestamps have no timezone or DST correction. The loader makes the
  Europe/Rome assumption explicit and converts to UTC.

## Implementation phases

1. **Foundation:** repository configuration, verified dataset mapping, deterministic
   environment model, controllers, and focused unit tests.
2. **Infrastructure:** Mosquitto, InfluxDB, Node-RED and persistent service
   configuration.
3. **Dataset pipeline:** loader, preprocessing, replay publisher, and ingestion flow.
4. **Actuation:** CoAP pump, gateway, reusable Node-RED decision subflow, and logs.
5. **Machine learning:** leakage-safe features, chronological forecasting, anomaly
   detection, model card, and MQTT service.
6. **Evaluation:** closed-loop controller experiment and protocol benchmark.
7. **Finalization:** integration smoke test, dashboard verification, report
   generation, French documentation, and troubleshooting.

## Known uncertainties

- Docker and external package availability must be verified in the target machine.
- Actual network overhead requires packet capture; without it, benchmarks report
  estimated protocol overhead separately from measured latency.
- The simplified environment model is calibrated only for controlled comparison,
  not as an agronomic validation model.
- The supplied dataset README identifies the source release as version 1.0; the
  application records the local files and their observed schemas rather than
  silently asserting a remote archive version.

## Verification rule

Each phase is validated with the smallest relevant tests and runtime checks before
the next phase is started. No generated metric is reported until it is produced by
an executed command.
