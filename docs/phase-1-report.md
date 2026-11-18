# Rapport de phase 1 — Fondation et infrastructure

## Objectif

Construire une base exécutable et reproductible avant d'ajouter la décision
d'irrigation et l'intelligence artificielle.

## Réalisé

- Inspection du `README.md` et du `DATA_DICTIONARY.md` fournis avec le dataset.
- Sélection initiale du secteur 1, tomate en plein champ (`TOMATO_SOIL`).
- Configuration des colonnes réelles dans [`config.yaml`](../config.yaml).
- Normalisation explicite des timestamps Europe/Rome vers UTC.
- Modèle déterministe [`SoilEnv`](../src/irrigation/env_model.py) avec:
  température jour/nuit, pluie, évaporation, irrigation, bruit et anomalies.
- Contrôleurs règle et prédictif avec hystérésis, pluie, intervalle minimal et
  durée maximale de fonctionnement.
- Relecture chronologique du dataset vers MQTT avec QoS 1.
- Pompe virtuelle aiocoap avec:
  - `POST /pump/on`
  - `POST /pump/off`
  - `GET /pump/state`
- Configuration Podman Compose pour Mosquitto, InfluxDB et Node-RED.
- Premier flow Node-RED d'ingestion et validation MQTT.
- Documentation de l'architecture et du plan d'implémentation.

## Tests exécutés

La commande suivante a été exécutée avec succès:

```bash
python -m pytest -q
```

Résultat observé: **6 tests passés**.

Le chargeur a aussi lu le fichier réel du secteur 1:

```text
02_processed_data/merged/dataset_zone_1.csv
33 253 lignes
```

Le JSON Node-RED a été analysé avec Python et sa structure est valide.

## Validation Podman

Le runtime disponible est:

```text
Podman 5.8.9
podman-compose 1.6.0
```

La validation runtime doit être lancée avec:

```bash
podman-compose config
podman-compose up -d --build
podman-compose ps
```

If port `1883` is already used by a host Mosquitto installation, use another
host port without changing the container protocol port:

```bash
MQTT_HOST_PORT=1884 podman-compose up -d --build
```

Python clients launched on the host must then use `--broker-port 1884` (the
current replay CLI will receive this option in the next service refinement).

Puis vérifier:

- Node-RED: http://localhost:1880
- Dashboard: http://localhost:1881
- InfluxDB: http://localhost:8086
- MQTT: port `1883`

Cette validation ne doit être considérée comme réussie qu'après lecture de
`podman-compose ps` et des logs, pas uniquement après le lancement de la
commande.

## Limites de la phase

- Le flow Node-RED actuel valide et conserve les messages, mais ne contient pas
  encore la décision complète ni l'écriture InfluxDB.
- Le dashboard n'est pas encore finalisé.
- Le service ML et les benchmarks appartiennent aux phases suivantes.
- `SoilEnv` est un modèle de contrôle expérimental simplifié, pas un modèle
  agronomique validé.
