# Note d'impact — Données de démonstration : éventail complet de statuts côté chef

> Branche `claude/install-claude-excel-6MGzv` · commit `af9ccd9` · 2026-07-18
> Type : données de démonstration (générateur) · aucun code applicatif, aucun modèle, aucune règle métier modifiés

## 1. Problème traité

Pour la soutenance, le chef doit pouvoir **montrer chaque cas** du cycle de contrôle des fiches : à corriger, à vérifier, bloqué (validation impossible), validé, verrouillé. Le jeu de données précédent était trop pauvre (2 à corriger, 2 à vérifier, 1 brouillon, 1 validée par opérateur) et surtout **ne contenait aucune fiche bloquée** — impossible de démontrer le garde-fou anti-chevauchement.

## 2. Cause racine

Le générateur `setup_demo.py` assignait un éventail minimal de statuts et ne créait volontairement aucune anomalie bloquante (au contraire, un correctif antérieur avait supprimé les chevauchements pour permettre la validation). Résultat : le workflow de blocage n'était pas démontrable.

## 3. Fonctionnalité apportée

Dans `generer_donnees()`, nouvel éventail par opérateur sur ses fiches les plus récentes :

| Statut | Nb / opérateur | Total (3 op.) |
|---|---|---|
| à corriger | 3 | 9 |
| à vérifier (propres, validables) | 3 | 9 |
| à vérifier **bloquée** (chevauchement essences) | 1 | 3 |
| brouillon | 2 | 6 |
| validée (valide_chef) | 2 | 6 |
| verrouillée | reste | ~87 |

La fiche « bloquée » est mise en statut `a_verifier` puis on force **deux créneaux d'essences qui se chevauchent** (helper `_forcer_chevauchement`) : cela déclenche l'anomalie R8 (niveau `danger`), qui **empêche la validation par le chef** tant qu'elle n'est pas corrigée.

## 4. Justification métier

L'anti-chevauchement sur la bicoupe (machine unique) est une règle physique verrouillée de la chaîne 4 : deux essences ne peuvent y passer simultanément. Disposer de fiches bloquées permet de **démontrer que l'application fait respecter cette contrainte** et matérialise le workflow opérateur → chef (contrôle) → correction. Cela sert l'argument de fiabilité de la saisie (OS1 et hypothèse H3 sur l'absence de système de mesure fiable).

## 5. Périmètre et fichiers touchés

| Fichier | Nature |
|---|---|
| `documents/outils/setup_demo.py` | `generer_donnees()` : `PLAN_STATUTS` enrichi + helper `_forcer_chevauchement` + compteur de fiches bloquées |

Aucun fichier applicatif (`app/`) modifié. La page Fiches chef gère déjà le filtre « Bloquantes » et le compteur correspondant.

## 6. Vérification

- `ast.parse(setup_demo.py)` → **valide**.
- Génération : `verrouille 87 · valide_chef 6 · brouillon 6 · a_verifier 12 (dont 3 bloquées) · a_corriger 9`.
- Serveur lancé, connexion `chef@cuf.cm` :
  - `/dashboard/chef/fiches?statut=tous&periode=tout` → **200** ;
  - tuiles compteurs : Chez le chef **12** · À corriger **9** · Brouillons **6** · Validées **93** · Bloquantes **3** ;
  - filtre `anomalies=bloquantes` → **3** fiches remontées avec le badge danger.

## 7. Cohérence avec les hypothèses et le cadre du mémoire

Aucune hypothèse (H1–H4) n'est contredite. Les fiches bloquées sont en statut `a_verifier`, **exclues des analyses** (`STATUTS_ANALYSES` = valide_chef + verrouille) : elles ne faussent donc ni le TRS, ni le manque à gagner, ni le Pareto. Le chevauchement forcé n'affecte que ces fiches de démonstration du blocage, pas les indicateurs. Cohérence app ↔ mémoire préservée.

## 8. Limites connues

- Ces données sont **fictives et déterministes** (seed 42) ; elles servent la démonstration, pas l'analyse réelle. À présenter comme telles au jury.
- Pour obtenir le nouvel éventail, il faut **régénérer les données** (`python setup_demo.py`), ce qui remplace la base de démonstration existante.

## 9. Prochaine étape

Aucune action bloquante. Le chef dispose d'un jeu de fiches couvrant tout le cycle. Pour la démonstration : montrer une fiche bloquée (validation refusée) → la corriger côté opérateur → la revalider côté chef, illustrant la boucle complète.
