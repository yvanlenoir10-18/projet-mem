# Note d'impact mémoire — Fiches en pool partagé entre opérateurs

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-18 · Commit `c2a655f`
> Changement de périmètre d'accès du rôle opérateur. Aucune table, aucun calcul modifié.

---

## 1. Ce qui a été implémenté

Le rôle `operateur` voit et traite désormais **toutes les fiches**, quel que soit le compte qui les a saisies. Auparavant, chaque opérateur était restreint à ses propres fiches (filtre `Equipe.user_id == current_user.id`), si bien qu'un second compte opérateur tombait sur des écrans vides alors que la base contenait 95 fiches (toutes rattachées à `saisie@cuf.cm`). Les points ouverts : liste (`historique`), accueil opérateur, détail de fiche, formulaire de correction, soumission et duplication.

La gouvernance est préservée : seules les fiches en statut `brouillon` et `à corriger` restent éditables par un opérateur ; les fiches `validées par le chef` et `verrouillées` demeurent non modifiables. La suppression reste réservée au propriétaire de la fiche.

## 2. Lien avec les objectifs du mémoire

Sert la démonstration terrain (usage multi-opérateurs, équipes A/B). L'application reflète l'organisation réelle de la chaîne 4 où ~10 opérateurs par poste se relaient : la fiche appartient au poste, pas à un individu. Renforce l'argument d'adoption (l'outil colle à l'organisation en équipes tournantes).

## 3. Données et calculs mobilisés

Aucun calcul modifié. Le changement porte uniquement sur les filtres d'accès (RBAC applicatif). Les indicateurs (TRS, rendement, manque à gagner) et les statuts comptabilisés (`valide_chef` + `verrouille`) sont inchangés.

## 4. Hypothèses testées ou confirmées

- **Confirmé par test** : un second compte opérateur (`op2`) voit les fiches du compte `saisie@cuf.cm` dans l'historique et l'accueil (HTTP 200), ouvre le détail (200) et corrige une fiche `à corriger` (200) ; une fiche verrouillée reste non éditable (redirection 302). Smoke 16/16.

## 5. Ce que ce module permet de montrer dans le mémoire

Que l'outil supporte le travail en équipes tournantes : n'importe quel opérateur de garde peut reprendre, compléter ou corriger une fiche du poste, sans blocage lié à l'identité du saisisseur initial.

## 6. Limites actuelles

- Le partage vaut pour tout le rôle opérateur (pas de cloisonnement par équipe A/B/C) : c'est un pool unique. Un cloisonnement fin par équipe nécessiterait un champ d'équipe sur l'utilisateur (non fait, hors périmètre).
- La suppression de fiche reste réservée au propriétaire (choix de prudence).

## 7. Vérification de cohérence avec les notes précédentes

- **⚠️ Contredit une décision antérieure de cette session.** La note `accueil-operateur-choix-fiche-corriger.md` et la réponse au QCM du 2026-07-17 retenaient « l'opérateur ne voit que ses propres fiches ». L'utilisateur a **explicitement révisé ce choix** le 2026-07-18 (« que les données fonctionnent chez tous les opérateurs peu importe l'opérateur »). Le pool partagé **remplace** donc la restriction « seulement les siennes ». Décision assumée et tracée ici.
- **Cohérent** avec la note `cockpit-repli-periode-auto.md` et `cockpit-chef-production.md` (périmètres disjoints).

## 8. Références bibliographiques mobilisées implicitement

Aucune. Adaptation de l'outil à l'organisation en équipes de poste (contexte terrain CUF).

## 9. Prochaines étapes

- Reporter le changement sur la copie Windows active via le patch combiné (v4 : cockpit prod + tuile opérateur + repli période + pool partagé).
- Vérifier en démo : se connecter avec n'importe quel compte opérateur → les fiches et le workflow de correction sont visibles et utilisables.
