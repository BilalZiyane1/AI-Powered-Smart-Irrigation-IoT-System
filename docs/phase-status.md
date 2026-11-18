# Statut réel des phases 1 à 6

## Vérifié

| Phase | Statut | Vérification |
|---|---|---|
| 1 Infrastructure | PASS | Mosquitto, InfluxDB, Node-RED et dashboard démarrés avec Podman |
| 2 Dataset | PASS | Secteur 1 chargé, 33 253 lignes inspectées, replay MQTT exécuté |
| 3 CoAP actionneur | PASS | Pompe ON vérifiée via HTTP/CoAP avec réponse réelle |
| 4 InfluxDB/ML | PARTIELLEMENT VÉRIFIÉ | Modèles +60/+120 entraînés; écriture InfluxDB vérifiée |
| 5 ML intégration | PARTIELLEMENT VÉRIFIÉ | MQTT prediction/anomaly implémentés et testés sur flux synthétique |
| 6 Expérience irrigation | PASS | 30 jours, 5 graines, règle et prédictif, CSV/Markdown/figure générés |

## Résultats exécutés

- 60 minutes: régression linéaire, MAE 1.1246.
- 120 minutes: régression linéaire, MAE 0.8324.
- Expérience fermée: règle 388.80 litres moyens, stress 540 minutes;
  prédictif 389.76 litres moyens, stress 0 minute.
- Ces résultats viennent du modèle simplifié `SoilEnv`, pas d'une validation
  agronomique sur terrain.
