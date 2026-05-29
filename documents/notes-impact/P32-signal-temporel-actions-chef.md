# P32 — Signal temporel par action Chef

Date : 2026-05-29

## Objectif

Rendre chaque action plus lisible dans la liste `Actions Chef` en indiquant immediatement son etat temporel.

## Changement livre

Chaque carte action affiche maintenant un badge de temps :

- `En retard` ;
- `Aujourd'hui` ;
- `Sous 3 jours` ;
- `Planifiee` ;
- `Sans delai` ;
- `Terminee`.

Un detail accompagne le badge, par exemple :

- `2 jour(s) de retard` ;
- `A verifier ce jour` ;
- `Echeance dans 2 jour(s)` ;
- `A dater si cette action doit rester suivie`.

## Valeur metier

Le chef comprend plus vite pourquoi une action est urgente ou non. La liste n'est plus seulement une suite de cartes : elle devient une file de suivi exploitable.

## Verification

- `python -m compileall app` : OK.
- Page Actions Chef : HTTP 200 pour chef/admin.
- PDG redirige vers `/dashboard/pdg`.
- Operateur redirige vers `/saisie/accueil`.
- Scenarios temporaires verifies : retard, aujourd'hui, sous 3 jours, planifiee, sans delai, terminee.
- Donnees temporaires supprimees apres test.
