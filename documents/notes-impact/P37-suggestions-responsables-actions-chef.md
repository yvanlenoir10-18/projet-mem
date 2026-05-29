# P37 — Suggestions dynamiques de responsables

## Objectif

Faciliter la création d'une action Chef sans imposer une gestion complexe des responsables.

Le responsable reste un texte libre, mais l'interface aide le chef avec des suggestions utiles.

## Changement livré

Le champ `Responsable` du formulaire `Nouvelle action` utilise maintenant :

- des responsables terrain par défaut ;
- les responsables déjà utilisés dans les actions existantes ;
- le responsable prérempli si l'action vient d'une priorité, machine ou recommandation.

## Exemple d'utilisation

Situation terrain :

Le chef a déjà créé une action avec le responsable `Chef affûtage`.

1. Il crée une nouvelle action.
2. Dans le champ `Responsable`, il commence à saisir `Chef...`.
3. L'application propose `Chef affûtage`.
4. Il évite de créer une variante inutile comme `chef affutage`, `Affuteur`, ou `Responsable affûtage`.

## Aide à la décision

Cette amélioration stabilise progressivement les responsables sans bloquer le terrain.

Elle prépare une future étape où les responsables pourront devenir une vraie liste paramétrable, mais sans forcer cette complexité maintenant.

## Vérifications

- Compilation Python : `python -m compileall app`
- Rendu du formulaire `Nouvelle action` en HTTP 200.
- Suggestions par défaut visibles : `Maintenance`, `Chef parc`.
- Responsable déjà utilisé visible dans les suggestions.
- Création d'une action avec ce responsable validée avec CSRF réel.
