---
description: Rédiger une section du mémoire à partir du plan validé
argument-hint: "<section-slug>"
---

## Entrée utilisateur

```text
$ARGUMENTS
```

## Prérequis

- `documents/plans/<section-slug>-recherche.md` (statut GO)
- `documents/plans/<section-slug>-plan.md` (plan validé par l'étudiant)

## Objectif

Produire le texte académique final de la section, conforme au style établi.

## Règles de rédaction obligatoires

- Phrases complètes, connecteurs logiques — zéro liste à tirets dans le corps du texte
- Ton académique + terrain : ancrer chaque argument dans la réalité de la chaîne 4 CUF
- Citations APA strictes : (Auteur, année) ou (Auteur, année, p. X) pour citations directes
- Données chiffrées : toujours sourcer (article, relevé terrain, ou "donnée à collecter")
- Jamais de tournures IA détectables
- Paragraphes de 5 à 8 lignes maximum

## Étapes

1. Lire le plan et les sources mobilisées
2. Rédiger paragraphe par paragraphe selon le plan
3. Vérifier chaque paragraphe : idée centrale claire ? données chiffrées ? lien CUF ?
4. Relire l'ensemble pour fluidité et cohérence
5. Signaler toutes les données terrain manquantes avec `[DONNÉE MANQUANTE : ...]`

## Sortie

Texte final dans `documents/<section-slug>.md` prêt à copier-coller dans Word.
