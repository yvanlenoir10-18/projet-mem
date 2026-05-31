# P3.27 - Rappel des actions machine inefficaces

## Objectif

Empêcher qu'une action machine marquée `Fait` disparaisse du pilotage alors que les arrêts continuent ou augmentent.

## Changement livré

L'accueil Chef affiche désormais une section `Terminées mais à revoir` lorsque le bilan P3.26 détecte une action machine inefficace :

- seules les actions terminées sur les 30 derniers jours sont analysées ;
- le compteur de l'accueil reflète toutes les actions récentes à revoir ;
- seules les trois premières sont affichées pour garder un écran lisible ;
- chaque rappel montre la machine, l'évolution, les durées avant/après et un lien direct vers le suivi.

## Exemple métier

Une action `Remplacer la courroie Bicoupe` est clôturée. Les fiches validées montrent `20 min` d'arrêt avant, puis `1h20` après. Le dashboard remonte cette action dans `Terminées mais à revoir`. Le chef sait immédiatement que la décision initiale n'a pas suffi et peut relancer un diagnostic.

## Vérifications

- compilation Python ;
- contrôle `git diff --check` ;
- test Flask avec fiches temporaires validées ;
- détection du bilan `À revoir` ;
- rendu dashboard avec hausse de `300 %`, `20min` avant et `1h20` après ;
- nettoyage des données temporaires après recette.
