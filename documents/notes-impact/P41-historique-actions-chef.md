# P41 — Historique métier des actions Chef

## Objectif

Permettre au chef scierie de reconstituer simplement le cycle de vie d'une action.

Le plan d'action doit être traçable sans afficher un journal technique illisible.

## Changement livré

Une table `action_chef_evenement` conserve maintenant les transitions métier :

- création ;
- démarrage ;
- clôture ;
- réouverture ;
- changement avancé de statut.

Chaque événement contient :

- l'ancien statut ;
- le nouveau statut ;
- l'auteur ;
- la date ;
- une note éventuelle, notamment le résultat obtenu.

Dans `Actions Chef`, chaque carte contient un bloc repliable `Historique de l'action`.

## Exemple d'utilisation

Situation terrain :

Une action `Contrôler Bicoupe` revient en discussion pendant une réunion.

Le chef peut ouvrir son historique et expliquer :

1. `Créée · À faire` par le chef ;
2. `À faire → En cours` quand maintenance est intervenue ;
3. `En cours → Fait` avec le résultat `Courroie retendue, essai conforme` ;
4. `Fait → À faire` si le problème réapparaît.

## Aide à la décision

La timeline aide à distinguer :

- un problème réellement traité ;
- une action seulement déclarée ;
- un problème récurrent après intervention ;
- un retard de prise en charge.

## Vérifications

- Compilation Python : `python -m compileall app`
- Nouvelle table créée automatiquement par `db.create_all()`.
- Création d'action tracée.
- Transitions `a_faire -> en_cours -> fait -> a_faire` tracées.
- Auteur et résultat conservés.
- Timeline repliable affichée dans Actions Chef.
- Réouverture : résultat courant nettoyé, historique conservé.
