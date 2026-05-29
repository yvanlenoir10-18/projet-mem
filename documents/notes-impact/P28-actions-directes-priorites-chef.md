# P28 — Actions directes sur priorites Chef

Date : 2026-05-29

## Objectif

Reduire le temps entre le constat et l'action dans le profil Chef. Le bloc `Priorites du chef` ne doit pas seulement orienter vers une page : il doit proposer une decision directe quand le contexte est suffisamment clair.

## Changement livre

Certaines priorites affichent maintenant deux boutons :

- un bouton de consultation, par exemple `Voir machines` ou `Voir production` ;
- un bouton d'action directe, par exemple `Creer action maintenance`, `Creer action organisation` ou `Lancer analyse`.

Les formulaires sont pre-remplis avec le contexte utile : origine, machine, titre, responsable, type d'action et description.

## Cas couverts

### Machine prioritaire

Si une machine cumule au moins 60 minutes d'arrets sur 7 jours, le chef voit :

- `Voir machines` ;
- `Creer action maintenance`.

Exemple : la Bicoupe cumule 2h10 d'arrets. Le chef peut ouvrir le detail machine ou creer directement une action de maintenance liee a la Bicoupe.

### Objectif non atteint

Si l'objectif du jour n'est pas atteint, le chef voit :

- `Voir production` ;
- `Creer action organisation`.

Exemple : objectif a 68 %. Le chef peut consulter les ecarts ou creer une action de reorganisation du poste.

### Declassement eleve

Si le declassement atteint 80 % du seuil ou le depasse, le chef voit :

- `Voir qualite` ;
- `Lancer analyse`.

Exemple : declassement a 35 % pour un seuil de 30 %. Le chef peut lancer une analyse Ishikawa / 5 Pourquoi pre-remplie avec le signal.

## Valeur metier

Cette evolution renforce l'aide a la decision : le chef n'est plus seulement dirige vers un tableau de bord, il dispose d'un chemin d'action pret a utiliser.

L'approche reste prudente : seules les situations suffisamment actionnables obtiennent un second bouton. Les autres priorites restent en consultation simple.

## Verification

- `python -m compileall app` : OK.
- `/dashboard/chef` en chef : OK.
- `/dashboard/chef` en admin : OK.
- PDG redirige vers `/dashboard/pdg`.
- Operateur redirige vers `/saisie/accueil`.
- Boutons directs maintenance et organisation visibles avec les donnees actuelles.
- Bouton direct `Lancer analyse` verifie par simulation KPI declassement eleve.
