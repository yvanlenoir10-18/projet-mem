# P36 — Pilotage des actions par responsable

## Objectif

Aider le chef scierie à répondre rapidement à la question : `qui doit faire quoi ?`

Le responsable reste un texte libre pour le moment, afin de ne pas créer trop tôt un module de gestion RH ou de responsabilités formelles.

## Changement livré

La page `Actions Chef` affiche maintenant un bloc `Par responsable`.

Pour chaque responsable ayant des actions ouvertes, le chef voit :

- le nombre d'actions ouvertes ;
- le nombre d'actions en retard ;
- le nombre d'actions à traiter aujourd'hui ;
- le nombre d'actions déjà en cours.

Un clic sur un responsable filtre directement la liste des actions.

Le formulaire de filtre contient aussi un champ `Responsable`.

## Exemple d'utilisation

Situation terrain :

Le chef voit que `Maintenance` a 4 actions ouvertes, dont 2 en retard.

1. Il ouvre `Actions Chef`.
2. Il clique sur la carte `Maintenance`.
3. La liste se filtre sur les actions Maintenance ouvertes.
4. Il peut démarrer les actions en attente ou marquer celles qui sont terminées.

## Aide à la décision

Cette lecture évite que les actions restent dispersées.

Elle permet au chef de voir si le blocage vient :

- d'un responsable surchargé ;
- d'une action qui n'a pas été prise en charge ;
- d'un retard de maintenance, parc, qualité ou organisation.

## Vérifications

- Compilation Python : `python -m compileall app`
- Rendu de la page `Actions Chef` en HTTP 200.
- Bloc `Par responsable` visible avec données temporaires.
- Filtre `responsable=Maintenance` fonctionnel.
- Les actions terminées ne sont pas comptées dans les actions ouvertes.
