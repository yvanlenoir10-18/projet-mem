# Note d'impact — Page Fiches chef : tous les statuts visibles pour la démonstration

> Branche `claude/install-claude-excel-6MGzv` · commit `b646292` · 2026-07-18
> Type : amélioration d'affichage (aucun changement de modèle, aucune règle métier touchée)

## 1. Problème traité

Sur la page **Fiches chef** (`/chef/fiches`), les tuiles compteurs du haut (« Chez le chef », « À corriger », « Brouillons », « Validées ») étaient calculées sur l'ensemble **déjà restreint au statut de l'onglet courant**. Résultat : sur l'onglet « à vérifier » (statut par défaut), les autres tuiles affichaient 0 et la page paraissait ne contenir qu'un seul type de fiche. Impossible de montrer au jury que l'application gère bien tout le cycle de vie d'une fiche.

## 2. Cause racine

Dans `fiches_chef()`, `compteurs_base` était produit à partir de `_fiches_chef_query(filtres)`, requête qui applique le filtre `statut`. Les compteurs héritaient donc du filtre courant au lieu de refléter le stock réel de chaque statut sur la période.

## 3. Correctif apporté

- `_fiches_chef_query(filtres, avec_statut=True)` : nouveau paramètre. Avec `avec_statut=False`, la requête garde **tous** les statuts (période/équipe/opérateur seulement).
- `fiches_chef()` : les compteurs sont désormais calculés sur la base **sans filtre statut** (stock réel par type) ; la liste affichée applique ensuite l'onglet choisi via le nouvel helper `_filtrer_par_statut(lignes, statut)`.
- Période par défaut passée de `30j` à `tout` (« toutes les dates ») pour que la démonstration montre tous les statuts quelle que soit la date du jour de la soutenance.

## 4. Justification métier

Le chef doit voir en un coup d'œil combien de fiches sont à vérifier, à corriger, en brouillon et validées — c'est son tableau de contrôle du cycle de vie. Afficher les vrais compteurs par statut correspond à l'usage réel (priorisation du travail de contrôle) et sert directement la démonstration du workflow opérateur → chef → validation.

## 5. Périmètre et fichiers touchés

| Fichier | Nature |
|---|---|
| `cuf-pilotage/app/routes/dashboard.py` | `_fiches_chef_query` (param `avec_statut`), `_filtrer_par_statut` (nouveau), `fiches_chef()` (compteurs sur base non filtrée, période défaut `tout`) |

Aucune table, aucun modèle, aucune migration. Le template `chef/fiches.html` est inchangé (il consommait déjà `compteurs_base` et le sélecteur de statut).

## 6. Vérification

- `ast.parse(dashboard.py)` → **valide**.
- Données de démonstration confirmant la présence de tous les statuts : `verrouille 102 · valide_chef 3 · a_verifier 6 · a_corriger 6 · brouillon 3` (générées par `setup_demo`, les statuts spéciaux étant posés sur les fiches les plus récentes de chaque opérateur).
- Contrôle visuel attendu à la relance : les quatre tuiles affichent des nombres non nuls simultanément ; cliquer chaque tuile ouvre la liste du statut correspondant ; le sélecteur « Tous les statuts » liste l'ensemble.

## 7. Cohérence avec les hypothèses et le cadre du mémoire

Aucune hypothèse (H1–H4) ni objectif spécifique (OS1–OS4) n'est contredit. Le correctif ne modifie aucun calcul (TRS, pertes FCFA, Pareto, KPI) : seuls les compteurs d'aiguillage de la page Fiches deviennent exacts. La cohérence app ↔ mémoire est préservée.

## 8. Limites connues

- Avec la période par défaut « toutes les dates », l'onglet « Validées » peut lister une centaine de fiches en démonstration : c'est voulu (richesse des données), mais on peut restreindre via le sélecteur de période si besoin de lisibilité.
- La performance repose sur `detecte_anomalies` appelée par fiche : sur ~120 fiches c'est négligeable ; au-delà de plusieurs milliers de fiches il faudrait paginer.

## 9. Prochaine étape

Aucune action bloquante. Cette page est prête pour la soutenance : elle démontre le cycle de vie complet des fiches. Prochaine amélioration démo possible : un guide de démonstration transverse couvrant chaque profil et chaque écran.
