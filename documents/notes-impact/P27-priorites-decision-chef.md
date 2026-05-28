# P27 — Priorites de decision Chef

Date : 2026-05-28

## Objectif

Ajouter sur l'accueil Chef une synthese courte qui transforme les signaux deja calcules en decisions actionnables. Le chef ne doit pas seulement voir des chiffres : il doit comprendre quoi traiter en premier.

## Changement livre

Un bloc `Priorites du chef` est ajoute dans `/dashboard/chef`, au-dessus des actions immediates.

Il affiche au maximum cinq priorites, triees par gravite :

- actions Chef en retard ;
- fiche a verifier la plus risquee ;
- machine prioritaire sur les 7 derniers jours ;
- ecart a l'objectif du jour ;
- declassement proche ou au-dessus du seuil ;
- analyses Ishikawa / 5 Pourquoi encore ouvertes.

Chaque priorite indique :

- le signal observe ;
- la decision attendue ;
- le bouton d'acces direct vers l'ecran utile.

## Logique metier

Le bloc suit la logique du profil Chef :

1. Traiter d'abord ce qui est deja decide et en retard.
2. Controler la fiabilite des fiches avant exploitation.
3. Diagnostiquer la machine qui consomme le plus de temps d'arret.
4. Surveiller l'objectif de production.
5. Expliquer les pertes matiere si le declassement devient anormal.
6. Ne pas laisser les analyses causales ouvertes sans suite.

## Exemples d'utilisation

### Cas 1 — Action en retard

Si une action "Verifier Bicoupe" avait une echeance hier, le chef voit :

`Lever les actions en retard`

Il clique sur `Traiter les retards`, puis change le statut en `En cours` ou `Fait`.

### Cas 2 — Fiche risquee

Si une fiche contient des anomalies horaires ou des volumes incoherents, le chef voit :

`Controler la fiche la plus risquee`

Il ouvre la fiche, valide si les donnees sont acceptables ou renvoie avec un message precis.

### Cas 3 — Machine prioritaire

Si la Bicoupe cumule le plus d'arrets sur 7 jours, le chef voit :

`Regarder la machine prioritaire`

Il ouvre Machines & Arrets et decide entre maintenance, analyse Ishikawa ou action de reorganisation.

### Cas 4 — Objectif non atteint

Si l'objectif du jour est a 68 %, le chef voit :

`Suivre l'ecart a l'objectif`

Il ouvre Production & Objectifs pour comparer les postes et comprendre si le retard vient du volume, des arrets ou de la qualite.

## Impact memoire

Cette evolution renforce l'OS6 : l'application ne se contente plus d'afficher des KPI, elle aide le responsable a prioriser les decisions operationnelles.

Elle reste defendable car elle ne cree pas de nouveaux indicateurs arbitraires : elle reformule les signaux existants en priorites de pilotage.

## Verification

- `python -m compileall app` : OK.
- `/dashboard/chef` en chef : OK, bloc visible.
- `/dashboard/chef` en admin : OK, bloc visible.
- `/dashboard/chef` en PDG : redirection vers `/dashboard/pdg`.
- `/dashboard/chef` en operateur : redirection vers `/saisie/accueil`.
