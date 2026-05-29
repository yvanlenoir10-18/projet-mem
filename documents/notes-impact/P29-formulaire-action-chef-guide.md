# P29 — Formulaire Action Chef guide

Date : 2026-05-29

## Objectif

Rendre le formulaire `Action Chef` plus simple a comprendre lorsque le chef arrive depuis une priorite, une machine, une fiche ou une analyse.

## Changement livre

Le formulaire affiche maintenant :

- l'origine claire de l'action quand elle existe ;
- une aide decisionnelle selon le type d'action ;
- des libelles plus directs : decision a suivre, nature de l'action, description concrete, responsable, delai/date de suivi ;
- une aide qui se met a jour si le chef change le type d'action.

## Valeur metier

Le chef comprend mieux :

1. d'ou vient le signal ;
2. ce qu'il doit decider ;
3. qui doit suivre l'action ;
4. pour quand l'action doit etre revue.

Cela evite les actions vagues comme "voir probleme" ou "faire suivi", qui sont difficiles a exploiter ensuite.

## Exemples d'utilisation

### Depuis une machine

Depuis `Priorites du chef`, le chef clique `Creer action maintenance`.

Le formulaire indique l'origine, par exemple `Bicoupe - panne`, et affiche l'aide maintenance :

`Reduire les arrets machine et eviter que la panne revienne.`

### Depuis l'objectif

Depuis `Priorites du chef`, le chef clique `Creer action organisation`.

Le formulaire explique que l'action sert a reduire l'ecart a l'objectif par l'organisation du poste.

### Depuis la qualite

Si le declassement est eleve, le chef peut lancer une analyse. Si une action qualite est creee, l'aide rappelle de verifier matiere, sciage, dimensions et tri.

## Verification

- `python -m compileall app` : OK.
- Formulaire action en chef : HTTP 200.
- Formulaire action en admin : HTTP 200.
- PDG redirige vers `/dashboard/pdg`.
- Operateur redirige vers `/saisie/accueil`.
- Bloc origine visible quand `origine_label` est present.
- Bloc aide decision visible dans tous les cas.
