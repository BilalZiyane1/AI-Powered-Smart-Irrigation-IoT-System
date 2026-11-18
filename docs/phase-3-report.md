# Rapport de phase 3 — Services AI, anomalies et évaluation

Cette phase ajoute:

- le service MQTT [`ml_service.py`](../src/irrigation/ml_service.py);
- la détection statistique, capteur bloqué, absence de réponse de pompe et
  Isolation Forest dans [`anomaly.py`](../src/irrigation/anomaly.py);
- la passerelle HTTP vers CoAP [`coap_gateway.py`](../src/irrigation/coap_gateway.py);
- l'expérience en boucle fermée [`run_experiment.py`](../bench/run_experiment.py);
- la base du benchmark [`protocol_bench.py`](../bench/protocol_bench.py);
- le smoke test réel [`smoke_test.sh`](../scripts/smoke_test.sh).

## Commandes

```bash
python -m src.irrigation.ml_service --broker-port 1884
python -m src.irrigation.coap_gateway
python -m bench.run_experiment --days 30 --seeds 3
MQTT_HOST_PORT=1884 bash scripts/smoke_test.sh
```

Le benchmark HTTP nécessite un récepteur HTTP réel sur `/bench`. Les mesures
indisponibles sont écrites comme échecs dans le CSV; elles ne sont jamais
présentées comme des succès. La mesure des octets réseau réels exige encore une
capture `tshark` ou `tcpdump`.

## Vérifications exécutées

- `python -m pytest -q`: **8 tests passés**.
- Smoke test Podman: **PASS**.
- Le service ML a publié une prédiction MQTT réelle:
  `predicted_soil_moisture = 42.9207` pour un flux de test de 12 mesures.
- La passerelle CoAP a retourné une commande réelle:
  `success = true`, latence observée `21.29 ms`.
- Un point MQTT a été écrit puis relu dans InfluxDB via l'API Flux.
- L'expérience fermée a produit 4 lignes CSV avec deux politiques et deux
  graines de simulation.
- Une expérience complète de 30 jours avec 5 graines a été exécutée.
  Les résultats agrégés sont dans `results/irrigation/comparison.md`.
