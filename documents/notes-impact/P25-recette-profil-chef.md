# P25 — Recette profil Chef Scierie

Date : 2026-05-28

## Objectif

Verifier que le profil Chef Scierie fonctionne comme une console de pilotage operationnel apres les modules Fiches, Machines & Arrets, Production & Objectifs, Qualite / Matiere, Resolution guidee et Actions Chef.

## Perimetre verifie

- Dashboard Chef : actions immediates, KPI du jour, alertes et liens vers les vues metier.
- Fiches Chef : acces liste et liens internes.
- Machines & Arrets : diagnostic machine, recurrence et lien vers action.
- Production & Objectifs : suivi objectif, ecarts et lien vers analyse.
- Qualite / Matiere : rendement, declasses, dechets et lien vers analyse.
- Resolution : acces au module Ishikawa / 5 Pourquoi.
- Actions Chef : creation, filtre retard, changement de statut et classement sans action.
- Permissions : chef/admin autorises, PDG et operateur rediriges hors des ecrans Chef.

## Resultats techniques

- Compilation Python : OK avec `python -m compileall app`.
- JavaScript du formulaire de saisie operateur : OK, le script rendu est syntaxiquement valide.
- Pages Chef principales : OK.
- Liens internes des pages Chef testees : 172 liens verifies, 0 echec.
- Action en retard : creee temporairement, visible dans le dashboard, puis supprimee.
- Changement de statut action : `a_faire -> en_cours -> fait` OK.
- `classe_sans_action` : refuse sans motif, accepte avec motif.
- Donnees temporaires de recette : nettoyees.

## Resultats metier

Le profil Chef tient maintenant un flux coherent :

1. Voir ce qui demande une action immediate.
2. Controler les fiches terrain.
3. Diagnostiquer les blocages machines et arrets.
4. Suivre les objectifs de production.
5. Comprendre les pertes matiere et le declassement.
6. Lancer une resolution guidee si le probleme exige une cause racine.
7. Creer une action suivie avec responsable, delai et statut.

Cette logique est defendable devant un encadreur, car elle relie la donnee terrain a une decision operationnelle suivie.

## Exemples de tests utilisateur

1. Se connecter comme chef, ouvrir `/dashboard/chef`, verifier que les cartes de pilotage et les actions en attente sont visibles.
2. Aller dans `Machines & Arrets`, cliquer sur une action liee a une machine, verifier que le formulaire d'action est pre-rempli.
3. Creer une action avec une date limite depassee, revenir au dashboard Chef, verifier qu'elle ressort comme action en retard.
4. Dans `Actions Chef`, passer une action en `En cours`, puis en `Fait`.
5. Tenter `Classer sans action` sans motif : l'application doit refuser. Ajouter un motif : l'application doit accepter.
6. Se connecter comme PDG et ouvrir `/dashboard/chef/actions` : l'application doit rediriger vers le dashboard PDG.
7. Se connecter comme operateur et ouvrir `/dashboard/chef/actions` : l'application doit rediriger vers l'accueil operateur.

## Decision

Le profil Chef est pret pour une recette manuelle utilisateur. Les prochaines ameliorations doivent viser la simplicite visuelle, les libelles metier et la qualite des exemples de decision, plutot qu'ajouter de nouvelles pages.
