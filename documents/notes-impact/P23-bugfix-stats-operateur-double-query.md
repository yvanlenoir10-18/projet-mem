# Note d'impact mémoire — P23 : Bugfix `_stats_operateur` — double requête DB et postes_semaine

> Générée le : 2026-05-27
> Commit : `0c11068` — fix(stats): supprime la double requête DB et corrige postes_semaine
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `app/routes/saisie.py`

---

## 1. Résumé de la fonctionnalité

Deux corrections ciblées dans `_stats_operateur(user_id)`, la fonction de calcul des statistiques de progression personnelle (partagée entre l'accueil et l'historique opérateur) :

**Correction 1 — suppression de la double requête DB.** La version initiale (F6, commit `6a8d9f0`) appelait `Equipe.query.filter_by(user_id=user_id).all()` deux fois : une première fois pour calculer les stats TRS (`soumises`), une seconde pour compter les postes de la semaine (`postes_semaine`). La seconde requête est désormais supprimée — on réutilise la liste `toutes` chargée en début de fonction.

**Correction 2 — inclusion des fiches `a_corriger` dans `postes_semaine`.** La version initiale du décompte hebdomadaire excluait les fiches au statut `a_corriger`. Or une fiche `a_corriger` est une fiche qui a été soumise par l'opérateur (passage par `a_verifier`) puis renvoyée en correction par le chef. Du point de vue de la régularité de collecte, l'opérateur A bien fourni un poste cette semaine. L'exclure du compteur était trompeur : un opérateur dont toutes les fiches de la semaine sont en correction voyait un décompte de zéro malgré son travail.

---

## 2. Décision d'architecture — une seule lecture DB, filtrage Python

La liste `toutes = Equipe.query.filter_by(user_id=user_id).all()` charge l'intégralité des équipes de l'opérateur une fois. Les trois sous-ensembles nécessaires (`soumises` pour TRS, filtre par date pour `postes_semaine`) sont dérivés en mémoire par compréhension de liste. C'est justifié ici parce que le volume de données est borné (un opérateur terrain CUF ne saisit pas des milliers de fiches) et parce que l'alternative — plusieurs requêtes SQL filtrées — ajouterait des allers-retours base inutiles pour ce volume.

**Décision sur `a_corriger` dans `postes_semaine` :** la règle retenue est « compte un poste si l'opérateur l'a soumis cette semaine, quelle que soit l'évolution ultérieure du statut ». Les statuts comptés sont donc `('soumis', 'a_verifier', 'a_corriger', 'verrouille', 'valide_chef')`. `brouillon` reste exclu : un brouillon non soumis ne représente pas une collecte complète.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Indirect.** Un compteur de régularité juste encourage mieux la saisie régulière. Un opérateur dont les fiches sont renvoyées en correction n'est plus pénalisé dans son décompte hebdomadaire, ce qui réduit le risque de découragement face aux retours du chef. |
| OS6 — Outil de pilotage adapté, vue opérateur | **Direct.** Le widget de progression (F6) est maintenant basé sur un compteur cohérent avec l'expérience de l'opérateur. |

---

## 4. Impact sur la validité scientifique des données

Ces corrections n'affectent aucune formule TRS, aucune mesure de production, aucune donnée terrain. Elles améliorent uniquement l'exactitude du compteur de régularité affiché à l'opérateur.

La correction de `postes_semaine` élimine un biais d'affichage : avant le fix, un opérateur corrigé pouvait croire avoir « perdu » ses postes de la semaine dans le compteur, ce qui était inexact et potentiellement démotivant. Après le fix, le compteur reflète fidèlement l'effort de soumission réel — cohérent avec le principe « récompenser l'acte de collecte » documenté en P20, section 4.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Correction purement algorithmique, aucune modification du schéma.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

**Cohérence avec P20 :** P20 documentait le choix de mesurer la régularité (nombre de postes) et non la performance (TRS), pour protéger H3. La présente correction renforce ce choix en assurant que tous les postes effectivement soumis comptent, y compris ceux renvoyés en correction — sans jamais toucher à la mesure TRS.

**Point d'attention :** la valeur de `postes_semaine` peut maintenant être légèrement supérieure à `nb_equipes` (stats TRS) pour un même opérateur, puisque `postes_semaine` inclut `a_corriger` (sans filtre TRS) et `nb_equipes` filtre sur `e.trs_global`. C'est attendu et cohérent : les deux métriques mesurent des choses distinctes (régularité vs performance documentée).

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| Variable `toutes` | `saisie.py`, `_stats_operateur()` | Chargement unique de toutes les équipes de l'opérateur, réutilisée pour `soumises` et `postes_semaine`. |
| `a_corriger` dans le filtre `postes_semaine` | `saisie.py`, `_stats_operateur()` | Inclut les fiches renvoyées en correction dans le décompte hebdomadaire. |

---

## 8. Utilisabilité terrain et adoption

- Un opérateur dont le chef renvoie systématiquement des fiches en correction ne voit plus son compteur hebdomadaire à zéro. Cela évite un signal négatif injustifié et potentiellement démotivant.
- La suppression de la double requête améliore le temps de réponse des pages accueil et historique opérateur (une seule lecture DB au lieu de deux), ce qui compte sur des connexions terrain lentes.

---

## 9. Ce que cela change pour le mémoire

Ces corrections sont de l'ordre du raffinement d'implémentation. Elles n'ajoutent aucun concept nouveau au mémoire. En revanche, si la section OS6 décrit le mécanisme de régularité (F6), il convient de préciser que le compteur mesure les postes soumis quelle que soit leur évolution dans le circuit de validation — et non uniquement les postes déjà validés par le chef. Ce détail est utile pour montrer que l'outil encourage la collecte de manière équitable, indépendamment de la rigueur du chef de production dans ses retours.

---

> **Vérification réalisée :** `python -c "from app import create_app; app = create_app(); print('OK')"` → OK. `_stats_operateur(op.id)` exécuté : une seule requête SQL observable (via `toutes`). Valeur `postes_semaine=0` conforme (semaine en cours sans fiche soumise par l'opérateur de test). Logique `a_corriger` vérifiée par relecture du code.
