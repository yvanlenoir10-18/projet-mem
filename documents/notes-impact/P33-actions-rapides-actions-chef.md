# P33 — Actions rapides sur les actions Chef

## Objectif

Réduire les clics dans le suivi des actions du chef scierie.

Avant, le chef devait ouvrir la liste déroulante de statut, choisir une valeur, puis valider. Pour les deux gestes les plus fréquents, ce flux était trop lent.

## Changement livré

Sur la page `Actions Chef`, chaque action ouverte affiche maintenant :

- `Démarrer` si l'action est encore à faire ;
- `Marquer fait` si l'action est à faire ou en cours ;
- `Statut avancé` pour les cas moins fréquents : abandonner, classer sans action, revenir à un autre statut.

## Exemple d'utilisation

Situation terrain :

Une action existe : `Appeler maintenance pour la Bicoupe`.

1. Le chef ouvre `Actions Chef`.
2. Il clique `Démarrer` quand la maintenance est contactée.
3. L'action passe en `En cours`.
4. Une fois l'intervention terminée, il clique `Marquer fait`.
5. L'action passe en `Fait` et reçoit une date de fin.

## Intérêt métier

Cette amélioration transforme la page Actions Chef en outil de suivi quotidien, pas seulement en registre administratif.

Le chef peut mettre à jour rapidement les décisions prises pendant le poste, sans perdre du temps dans un formulaire complet.

## Vérifications

- Compilation Python : `python -m compileall app`
- Rendu de la page Actions Chef : boutons visibles.
- Test serveur avec CSRF réel : `a_faire -> en_cours -> fait`.
- Nettoyage automatique des données de test.
