# P3.28 - Relance guidée après action machine inefficace

## Objectif

Transformer le rappel d'une action inefficace en décision immédiatement exploitable par le chef scierie.

## Changement livré

Dans la section `Terminées mais à revoir` du dashboard Chef, chaque rappel propose désormais :

- `Revoir` : retrouver l'action terminée et son historique ;
- `Nouvelle action` : préparer une nouvelle intervention avec la machine et le bilan déjà remplis ;
- `Analyser les causes` : ouvrir une analyse Ishikawa avec le phénomène, la machine et les durées avant/après déjà renseignés.

## Exemple métier

Une première intervention sur la Bicoupe ne suffit pas : le temps d'arrêt passe de `20 min` à `1h20`. Le chef peut :

1. créer une nouvelle action maintenance ciblée si la décision est déjà claire ;
2. lancer Ishikawa si le changement de lame ou de courroie n'explique pas réellement le problème.

Le second chemin évite de répéter mécaniquement une intervention inefficace. Il invite à explorer les branches `Machine`, `Méthode`, `Matière`, `Main d'oeuvre`, `Milieu` et `Mesure`.

## Vérifications

- compilation Python ;
- contrôle `git diff --check` ;
- test Flask avec une action Bicoupe temporaire inefficace ;
- vérification des boutons sur le dashboard ;
- vérification du formulaire `Nouvelle action` prérempli ;
- vérification du formulaire Ishikawa prérempli ;
- nettoyage des données temporaires.
