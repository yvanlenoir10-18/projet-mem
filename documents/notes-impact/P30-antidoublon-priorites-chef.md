# P30 — Anti-doublon priorites Chef

Date : 2026-05-29

## Objectif

Eviter que le chef cree plusieurs actions ou analyses ouvertes pour le meme signal. Une priorite doit pousser a agir, mais pas a multiplier les tickets inutiles.

## Changement livre

Le bloc `Priorites du chef` detecte maintenant les suivis deja ouverts :

- machine prioritaire : si une action ouverte existe deja pour cette machine, le bouton devient `Suivre action existante` ;
- objectif non atteint : si une action ouverte existe deja pour `Objectif du jour non atteint`, le bouton devient `Suivre action existante` ;
- declassement eleve : si une analyse ouverte existe deja avec `DECLASS_EXCESSIF` ou `Declassement eleve`, le bouton devient `Suivre analyse ouverte`.

## Valeur metier

Le chef evite les doublons et garde une file d'actions plus lisible.

Exemple :

1. La Bicoupe est prioritaire.
2. Le chef cree une action maintenance.
3. Le lendemain, si la Bicoupe reste prioritaire, l'application propose de suivre l'action existante au lieu d'en creer une deuxieme.

## Valeur technique

Le changement ne cree aucune nouvelle table. Il interroge les actions ouvertes (`a_faire`, `en_cours`) et les problemes ouverts (`ouvert`, `en_analyse`, `cause_identifiee`).

Un import `or_` SQLAlchemy est ajoute dans `dashboard.py`, car la recherche de la page Actions Chef l'utilisait deja.

## Verification

- `python -m compileall app` : OK.
- Dashboard Chef : HTTP 200 pour chef/admin.
- PDG redirige vers `/dashboard/pdg`.
- Operateur redirige vers `/saisie/accueil`.
- Recherche Actions Chef `?q=Bicoupe` : HTTP 200.
- Scenario temporaire anti-doublon : OK, puis nettoyage des donnees de test.
