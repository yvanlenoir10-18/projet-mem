# P3.26 - Bilan d'efficacité des actions machine

## Objectif

Aider le chef scierie à vérifier si une décision terminée a réellement réduit les arrêts de la machine concernée.

## Principe

Pour une action au statut `fait` rattachée à une machine, l'application compare les arrêts issus de fiches validées :

- jusqu'à 7 jours avant la clôture ;
- sur une fenêtre de même durée après la clôture ;
- sans inclure le jour de clôture, car une partie des arrêts de cette journée peut être antérieure à l'action.

Le bilan reste volontairement prudent :

- `À observer` si moins de 2 jours sont disponibles après la clôture ;
- `Amélioration visible` si le temps d'arrêt baisse d'au moins 20 % ;
- `À surveiller` si l'évolution est encore trop faible ;
- `À revoir` si les arrêts augmentent ou apparaissent après l'action.

## Exemple métier

Une action `Remplacer la courroie Bicoupe` est marquée comme faite. La Bicoupe avait cumulé `1h40` d'arrêt avant l'intervention et seulement `20 min` après. Le chef voit `Amélioration visible` et peut justifier que l'intervention a produit un effet mesurable.

## Limites assumées

- Il s'agit d'un signal d'aide à la décision, pas d'une preuve statistique définitive.
- Seules les fiches validées sont utilisées pour éviter de conclure depuis des données encore non contrôlées.
- Les actions sans machine restent consultables mais ne reçoivent pas ce bilan automatique.

## Vérifications

- compilation Python ;
- contrôle `git diff --check` ;
- test Flask avec fiches temporaires validées : `100 min` avant, `20 min` après ;
- test d'une action récente affichée `À observer` ;
- nettoyage des données temporaires après recette.
