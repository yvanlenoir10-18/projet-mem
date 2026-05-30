# P40 — Résultat obligatoire à la clôture d'une action Chef

## Objectif

Faire du plan d'action un véritable outil de suivi terrain.

Une action ne doit pas être considérée comme terminée uniquement parce que le chef a cliqué sur `Fait`. L'application doit conserver une courte preuve du résultat obtenu.

## Changement livré

Le modèle `ActionChef` contient maintenant `note_resultat`.

Quand une action passe à `Fait` :

- une note de résultat d'au moins 5 caractères est obligatoire ;
- les boutons rapides demandent cette note dans une fenêtre simple ;
- le changement avancé de statut propose un champ visible si `Fait` est choisi ;
- la règle est vérifiée côté serveur ;
- le résultat est affiché dans la liste des actions terminées.

Les bases SQLite existantes reçoivent automatiquement la nouvelle colonne au démarrage.

## Exemple d'utilisation

Situation terrain :

Une action existe : `Contrôler la courroie de la Bicoupe`.

1. Le chef clique `Fait`.
2. L'application demande le résultat.
3. Il saisit : `Courroie retendue, essai concluant, surveiller pendant 7 jours.`
4. L'action est clôturée.
5. Le résultat reste visible dans l'historique.

## Aide à la décision

Cette note permet de distinguer :

- une action réellement réalisée ;
- une action seulement annoncée ;
- une réparation provisoire à surveiller ;
- une intervention qui doit produire une nouvelle action de contrôle.

## Vérifications

- Compilation Python : `python -m compileall app`
- Migration légère SQLite : colonne `action_chef.note_resultat` présente.
- Clôture sans résultat refusée côté serveur.
- Clôture avec résultat acceptée avec CSRF réel.
- Résultat affiché dans la liste des actions terminées.
- Création directe en `Fait` sans résultat refusée.
- Création directe en `Fait` avec résultat acceptée.
