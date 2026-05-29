# P31 — Suivi temporel des actions Chef

Date : 2026-05-29

## Objectif

Ameliorer le suivi des actions Chef en distinguant ce qui est en retard, a traiter aujourd'hui, a anticiper sous 3 jours et sans delai.

## Changement livre

La page `/dashboard/chef/actions` affiche maintenant un bloc `A traiter par delai` avec quatre entrees :

- `En retard` ;
- `Aujourd'hui` ;
- `Sous 3 jours` ;
- `Sans delai`.

Chaque carte est cliquable et applique un filtre correspondant.

## Logique metier

Le chef peut maintenant lire les actions comme une file de travail :

1. traiter d'abord les retards ;
2. verifier ce qui doit etre fait aujourd'hui ;
3. anticiper les actions proches ;
4. dater les actions sans delai si elles doivent rester suivies.

Cela rend le plan d'action plus exploitable au quotidien.

## Exemple d'utilisation

Un chef ouvre `Actions Chef` le matin :

- s'il voit `En retard : 2`, il traite ces actions en premier ;
- s'il voit `Aujourd'hui : 1`, il verifie ce point avant la fin du poste ;
- s'il voit `Sans delai : 4`, il peut ajouter des dates pour eviter que ces actions restent vagues.

## Verification

- `python -m compileall app` : OK.
- Filtres `retard`, `aujourd_hui`, `bientot`, `sans_delai` : HTTP 200.
- Scenarios temporaires avec 4 actions testees : OK.
- Donnees temporaires supprimees apres test.
- Chef/admin autorises.
- PDG redirige vers `/dashboard/pdg`.
- Operateur redirige vers `/saisie/accueil`.
