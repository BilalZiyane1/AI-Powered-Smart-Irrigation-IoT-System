# Rapport de phase 2 — Dataset et premier modèle de prévision

## Objectif

Utiliser le dataset agricole réel dans une première tâche d'intelligence
artificielle sans fuite de données temporelles.

## Implémentation

- Le chargeur réutilise la configuration du secteur 1.
- Les timestamps sont triés et convertis en UTC.
- Les variables disponibles avant l'instant prédit sont utilisées:
  humidité courante, retards, moyennes mobiles, tendance, météo, irrigation
  passée et encodage cyclique de l'heure.
- La cible est l'humidité future à l'horizon configurable, par défaut +60
  minutes, soit 6 pas de 10 minutes.
- La séparation entraînement/test est chronologique.
- Les modèles comparés sont:
  persistence, régression linéaire, Random Forest et Gradient Boosting.

## Exécution

```bash
python -m ml.train_forecaster --horizon-minutes 60
```

Le résultat est écrit dans `results/forecasting/metrics_60m.json` et les modèles
dans `ml/models/`. Ces sorties sont générées et ne doivent pas être considérées
comme des valeurs documentaires tant qu'une exécution locale ne les a pas
produites.

## Résultat exécuté

Une exécution réelle sur le secteur 1 a utilisé **7 861 lignes complètes**.
Les 15 variables d'entrée sont définies dans le fichier JSON généré. Les MAE
observées sont:

| Modèle | MAE |
|---|---:|
| Persistence | 0.2288 |
| Régression linéaire | 1.1246 |
| Random Forest | 1.1593 |
| Gradient Boosting | 1.2723 |

Ces métriques sont valables uniquement pour cette séparation temporelle et ce
secteur. Le meilleur modèle selon la MAE de cette exécution est la régression
linéaire. Les valeurs sont régénérables et ne constituent pas une validation
agronomique.

## Limites

Cette phase ne publie pas encore les prédictions par MQTT. Le service ML,
l'anomaly detection et l'intégration Node-RED seront ajoutés ensuite.

## Résultats +60 / +120 minutes

Des modèles ont été exécutés aux horizons 60 et 120 minutes:

| Horizon | Lignes | Modèle retenu | MAE |
|---:|---:|---|---:|
| 60 minutes | 7 861 | Régression linéaire | 1.1246 |
| 120 minutes | 7 661 | Régression linéaire | 0.8324 |

Les fichiers JSON détaillés sont conservés dans `results/forecasting/`.
