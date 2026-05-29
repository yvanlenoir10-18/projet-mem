# P38 — Délais rapides dans les actions Chef

## Objectif

Accélérer la création d'une action par le chef scierie.

Le chef n'a pas toujours besoin de choisir une date précisément dans le calendrier. Souvent, il veut simplement dire : à faire aujourd'hui, demain, cette semaine, ou sans délai.

## Changement livré

Dans le formulaire `Nouvelle action`, le champ `Délai / date de suivi` propose maintenant :

- `Aujourd'hui`
- `Demain`
- `Dans 3 jours`
- `Dans 7 jours`
- `Sans délai`

Ces boutons remplissent ou vident le champ date automatiquement.

## Exemple d'utilisation

Situation terrain :

La Bicoupe a eu un arrêt long aujourd'hui.

1. Le chef crée une action `Contrôler Bicoupe`.
2. Il clique `Aujourd'hui` si la maintenance doit intervenir tout de suite.
3. Il clique `Dans 7 jours` si l'action est un contrôle de suivi après réparation.
4. L'action apparaîtra ensuite dans les alertes quand le délai approche ou est dépassé.

## Aide à la décision

Cette amélioration rend le plan d'action plus rapide à alimenter.

Elle réduit les actions sans délai oubliées, parce que le chef peut fixer un suivi en un clic.

## Vérifications

- Compilation Python : `python -m compileall app`
- Formulaire `Nouvelle action` en HTTP 200.
- Boutons visibles : aujourd'hui, demain, 3 jours, 7 jours, sans délai.
- Hooks JavaScript présents.
- Création d'une action avec date vérifiée avec CSRF réel.
