# Note d'impact — Infrastructure notes mémoire

> Commit : 8a000b3
> Date : 2026-04-30
> Type : Infrastructure / outillage (pas une fonctionnalité applicative)

---

## Nature du commit

Ce commit ne concerne pas une fonctionnalité de l'application CUF Pilotage. Il met en place :

1. **Le hook `post-commit-memoir.sh`** — script automatique qui injecte un rappel après chaque `git commit` pour produire la note d'impact mémoire.
2. **La note de cadrage global** (`00-cadrage-global-P1-P2-P3.md`) — base de référence couvrant l'ensemble de l'application au stade P1/P2/P3.

## Impact sur le mémoire

Aucun impact sur les données, les indicateurs ou la méthodologie. L'infrastructure mise en place garantit simplement qu'aucune fonctionnalité future ne sera commitée sans que la note d'impact correspondante soit produite et sauvegardée dans `documents/notes-impact/`.

## Pas de contradiction avec les hypothèses précédentes

Ce commit n'introduit aucune décision de conception qui remettrait en cause les hypothèses H1–H4 ni les limites identifiées dans la note de cadrage global.

## Prochaine note attendue

La prochaine note incrémentale sera produite lors du commit de la Phase P4 (Export Excel enrichi).
