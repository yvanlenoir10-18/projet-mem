# P3.30 - Efficacité des actions par machine

## Objectif

Montrer au chef scierie quelles machines concentrent les interventions efficaces, incertaines ou à revoir.

## Changement livré

La page `Actions Chef` affiche désormais une section `Effets par machine` :

- regroupement des actions machine terminées depuis 30 jours ;
- compteurs `efficace`, `à observer`, `à surveiller`, `à revoir` ;
- tri par gravité : les machines ayant des actions à revoir remontent en premier ;
- carte cliquable pour isoler les actions terminées de la machine.

## Complémentarité avec l'existant

- `Par machine` montre la charge actuelle : actions encore ouvertes ;
- `Effets par machine` montre le résultat des interventions terminées.

Cette séparation évite de confondre ce qu'il reste à faire avec ce qui a réellement fonctionné.

## Exemple métier

Le chef voit :

- `Bicoupe · 1 efficace · 2 à revoir`
- `Déligneuse · 2 efficaces`

La Bicoupe remonte en premier. Un clic ouvre uniquement les actions terminées liées à cette machine.

## Vérifications

- compilation Python ;
- contrôle `git diff --check` ;
- test Flask avec plusieurs machines temporaires ;
- vérification du regroupement et du tri par gravité ;
- vérification du rendu de la section ;
- vérification du filtre machine ;
- nettoyage des données temporaires.
