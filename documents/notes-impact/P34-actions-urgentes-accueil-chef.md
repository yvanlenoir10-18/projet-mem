# P34 — Actions urgentes sur l'accueil Chef

## Objectif

Transformer l'accueil Chef en console de pilotage plus utile.

Le chef ne doit pas ouvrir plusieurs pages pour savoir quelles décisions déjà prises sont en retard ou proches de l'échéance.

## Changement livré

La carte `Actions Chef` du dashboard affiche maintenant les 3 actions ouvertes les plus urgentes :

- actions en retard ;
- actions à traiter aujourd'hui ;
- actions prévues sous 3 jours.

Chaque ligne montre :

- le statut temporel ;
- le titre de l'action ;
- le type d'action ;
- le responsable ;
- le détail du délai ;
- un lien direct vers le suivi des actions.

Les actions lointaines ou sans délai restent dans la page complète `Actions Chef`, afin de ne pas surcharger l'accueil.

## Exemple d'utilisation

Situation terrain :

Une action `Appeler maintenance pour Bicoupe` devait être traitée hier.

1. Le chef ouvre `/dashboard/chef`.
2. La carte `Actions Chef à suivre` affiche immédiatement l'action en retard.
3. Il clique `Traiter`.
4. Il arrive sur la page Actions Chef filtrée sur cette action.
5. Il peut la démarrer ou la marquer comme faite.

## Aide à la décision

Cette fonctionnalité évite qu'une décision prise reste oubliée dans une liste.

Elle répond à la question : `qu'est-ce que je dois traiter maintenant ?`

## Vérifications

- Compilation Python : `python -m compileall app`
- Test serveur : dashboard Chef en HTTP 200.
- Test avec actions temporaires : retard, aujourd'hui et sous 3 jours visibles.
- Test anti-bruit : action à plus de 3 jours non affichée dans l'accueil.
