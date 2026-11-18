# Architecture (version de travail)

## Architecture à trois niveaux

```mermaid
flowchart LR
  D[Dataset agricole réel] --> R[Replay Python]
  S[SoilEnv Python] --> R
  R -->|MQTT QoS 1| M[Mosquitto]
  M --> N[Node-RED]
  N --> I[InfluxDB]
  N --> G[Passerelle CoAP]
  G -->|CoAP/UDP| P[Pompe virtuelle aiocoap]
  P -->|état MQTT| M
  M --> ML[Service ML]
  ML -->|prédictions/anomalies MQTT| N
  N --> DB[FlowFuse Dashboard]
```

## Cycle d'irrigation

```mermaid
sequenceDiagram
  participant R as Replay/Senseur
  participant B as Mosquitto
  participant N as Node-RED
  participant G as Gateway
  participant P as Pompe CoAP
  R->>B: mesure JSON humidité/météo
  B->>N: message MQTT QoS 1
  N->>N: validation, contexte, seuil ou prédiction
  N->>G: demande HTTP ON/OFF
  G->>P: POST CoAP /pump/on ou /pump/off
  P-->>G: réponse CoAP succès/erreur
  G-->>N: résultat et latence
  P->>B: état de pompe MQTT
  B->>N: retour d'état
  N->>DB: affichage et persistance
```

## Topics MQTT et ressources CoAP

| Topic | Usage |
|---|---|
| `ferme/parcelle1/humidite_sol` | mesure d'humidité |
| `ferme/parcelle1/meteo` | température et pluie |
| `ferme/parcelle1/prediction` | prévisions ML |
| `ferme/parcelle1/anomalie` | alertes d'anomalie |
| `ferme/parcelle1/pompe/etat` | état de l'actionneur |

La pompe expose `POST /pump/on`, `POST /pump/off` et `GET /pump/state` sur UDP
5683. MQTT est adapté à la télémétrie asynchrone; CoAP est conservé pour la
commande légère et explicite de l'actionneur.
