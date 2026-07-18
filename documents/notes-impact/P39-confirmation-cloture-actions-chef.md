# P39 — Confirmation avant clôture rapide d'une action

## Objectif

Éviter qu'une action Chef disparaisse du suivi après un clic involontaire.

## Changement livré

Les boutons rapides `Fait` demandent maintenant une confirmation :

`Marquer cette action comme faite ?`

Cette confirmation est présente :

- sur l'accueil Chef ;
- dans la page `Actions Chef`.

Le bouton `Démarrer` reste immédiat, car son effet est réversible et moins risqué.

## Exemple d'utilisation

Situation terrain :

Le chef veut démarrer une action `Contrôler Bicoupe`, mais touche accidentellement `Fait`.

1. L'application affiche une confirmation.
2. Le chef clique `Annuler`.
3. L'action reste ouverte.
4. Il peut ensuite cliquer `Démarrer`.

## Aide à la décision

Cette protection garde la liste des actions fiable.

Une action clôturée trop tôt peut donner l'impression qu'un problème est traité alors qu'aucune intervention n'a réellement eu lieu.

## Vérifications

- Compilation Python : `python -m compileall app`
- Confirmations visibles sur le dashboard Chef et dans Actions Chef.
- POST confirmé fonctionnel avec CSRF réel.
- Passage `en_cours -> fait` vérifié avec `termine_le`.
