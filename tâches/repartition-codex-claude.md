# Répartition Codex / Claude Code

Objectif : éviter que Codex et Claude Code travaillent sur les mêmes tâches en même temps.

## Rôle de Codex

- Corriger les bugs bloquants dans le code local.
- Implémenter les fonctionnalités validées.
- Travailler en priorité sur le profil Chef Scierie.
- Vérifier les routes et scénarios après chaque changement.
- Donner la commande PowerShell et un exemple de test utilisateur après chaque fonctionnalité.

## Rôle de Claude Code

- Auditer, critiquer et proposer des améliorations.
- Debugger conceptuellement et signaler les risques.
- Proposer de nouvelles fonctionnalités ou variantes UX/métier.
- Ne pas modifier les mêmes fichiers que Codex sans coordination explicite.

## Règle de coordination

Avant chaque nouveau développement, vérifier :

- si la tâche concerne le profil Chef Scierie : Codex implémente ;
- si la tâche concerne une proposition ou un audit : Claude Code analyse ;
- si un bug bloque toute l'application : Codex corrige d'abord ;
- si Claude propose une fonctionnalité, Codex ne la code qu'après validation utilisateur.

## Tâche en cours côté Codex

- Stabiliser la saisie des fiches tous profils.
- Puis reprendre le profil Chef Scierie.
