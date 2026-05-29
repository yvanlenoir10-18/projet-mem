# P35 — Actions directes depuis le dashboard Chef

## Objectif

Permettre au chef scierie de traiter rapidement une action urgente sans quitter l'accueil.

## Changement livré

Dans la carte `Actions Chef à suivre` du dashboard :

- une action `À faire` affiche maintenant `Démarrer` et `Fait` ;
- une action `En cours` affiche seulement `Fait` ;
- le bouton `Voir` reste disponible pour ouvrir le suivi complet.

## Exemple d'utilisation

Situation terrain :

Une action `Maintenance Bicoupe` est en retard.

1. Le chef ouvre `/dashboard/chef`.
2. Il voit l'action dans `Actions Chef à suivre`.
3. Si la maintenance vient d'être contactée, il clique `Démarrer`.
4. Si l'intervention est terminée, il clique `Fait`.
5. L'action quitte automatiquement les actions ouvertes.

## Aide à la décision

Cette amélioration rapproche la décision du suivi réel.

Le chef n'a plus besoin de naviguer dans une liste complète pour mettre à jour une décision simple. Cela réduit les oublis et rend le plan d'action plus vivant.

## Vérifications

- Compilation Python : `python -m compileall app`
- Rendu dashboard avec action urgente temporaire.
- `Démarrer` passe l'action de `a_faire` à `en_cours` avec CSRF réel.
- `Fait` passe l'action de `en_cours` à `fait` et renseigne `termine_le`.
- Pour une action déjà `en_cours`, `Démarrer` n'apparaît plus.
