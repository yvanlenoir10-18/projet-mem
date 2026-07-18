# P3.29 - Synthèse de la boucle d'amélioration

## Objectif

Permettre au chef scierie de comprendre rapidement où en sont les décisions terrain et si les interventions terminées produisent un effet observable.

## Changement livré

La page `Actions Chef` affiche désormais une bande `Boucle d'amélioration` avec cinq compteurs cliquables :

- `Ouvertes` : décisions encore à mener ;
- `Efficaces` : réduction visible des arrêts ou absence d'arrêt observé ;
- `À observer` : action trop récente pour conclure ;
- `À surveiller` : évolution encore trop faible ;
- `À revoir` : arrêts en hausse ou apparition de nouveaux arrêts.

Un filtre manuel `Efficacité` permet également d'isoler ces catégories dans la liste.

## Périmètre

- seules les actions `Fait` liées à une machine sont évaluées automatiquement ;
- la synthèse porte sur les actions terminées depuis 30 jours ;
- les actions ouvertes restent comptées séparément ;
- le calcul utilise uniquement les fiches validées.

## Exemple métier

Le chef ouvre `Actions Chef` et voit :

`5 ouvertes · 3 efficaces · 2 à observer · 1 à surveiller · 1 à revoir`

Il clique `À revoir` pour isoler l'intervention Bicoupe qui n'a pas produit l'effet attendu, puis utilise la relance guidée P3.28.

## Vérifications

- compilation Python ;
- contrôle `git diff --check` ;
- test Flask avec cinq cas temporaires : ouverte, efficace, observation, surveillance, échec ;
- vérification des compteurs ;
- vérification des filtres `efficaces` et `a_revoir` ;
- nettoyage des données temporaires.
