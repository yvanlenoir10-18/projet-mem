# P3.25 - Actions Chef par machine

## Objectif

Permettre au chef scierie de retrouver rapidement les décisions encore ouvertes liées à une machine précise.

## Changement livré

- synthèse cliquable des actions ouvertes par machine ;
- tri prioritaire des machines ayant des actions en retard ou à traiter aujourd'hui ;
- filtre exact par machine dans la page Actions Chef ;
- maintien des actions sans machine dans la liste générale.

## Exemple métier

Avant une réunion maintenance, le chef clique sur `Bicoupe`. Il retrouve immédiatement les actions ouvertes liées à cette machine, par exemple le contrôle d'une courroie en retard et la vérification d'un alignement déjà en cours. Les actions terminées restent consultables via les statuts historiques mais ne polluent pas la vue opérationnelle ouverte.

## Vérifications

- compilation Python ;
- contrôle `git diff --check` ;
- test Flask avec actions temporaires `Bicoupe` et `Déligneuse` ;
- vérification du filtre exact `machine=Bicoupe` ;
- vérification navigateur du rendu du champ Machine et de l'absence d'erreur Flask.
