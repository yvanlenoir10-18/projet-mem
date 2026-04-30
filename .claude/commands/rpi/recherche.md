---
description: Recherche approfondie avant rédaction d'une section du mémoire — GO/NO-GO
argument-hint: "<section-slug>"
---

## Entrée utilisateur

```text
$ARGUMENTS
```

## Objectif

Analyser la faisabilité et les sources disponibles pour une section du mémoire **avant** de commencer à rédiger. Agit comme un verrou GO/NO-GO.

## Étapes

1. **Charger le contexte** : lire `contexte_memoire_CUF.md` et les fiches de revue de littérature existantes dans `documents/`
2. **Analyser la demande** : comprendre quelle section est visée (introduction, méthodologie, résultats, discussion, etc.)
3. **Rechercher les sources** :
   - Vérifier les articles déjà fichés (Thèmes 1–7)
   - Identifier les données terrain disponibles
   - Signaler les lacunes (données manquantes, articles non lus)
4. **Évaluer la faisabilité** :
   - Peut-on rédiger cette section avec les sources actuelles ?
   - Quelles données terrain sont nécessaires et disponibles ?
   - Y a-t-il des contradictions à résoudre ?
5. **Recommandation GO/NO-GO** avec justification claire

## Sortie

Rapport dans `documents/plans/<section-slug>-recherche.md` :
- Liste des sources disponibles par pertinence
- Lacunes identifiées
- Recommandation GO/NO-GO
- Plan de rédaction suggéré si GO
