# P60 — Chef Scierie V2 · Vue 1 « LE POINT » + cascade économique réconciliée

> Branche `claude/install-claude-excel-6MGzv` · 2026-06-08
> Co-conception Claude ↔ Codex ↔ utilisateur (BWAME). Contrat verrouillé avant code.

## 1. Intention

Première vue du profil Chef Scierie V2 : un écran de premier regard qui répond
en 5 secondes à « est-ce que la chaîne va bien, où agir, combien ça coûte ».
Ordre validé par l'utilisateur : **ce qui ne va pas d'abord**, puis causes et
conséquences à la demande (dévoilement progressif).

## 2. Décision méthodologique centrale (verrouillée)

La cascade affichée est une **mesure économique réconciliée**, pas une
décomposition D/P/Q. Séparation assumée (Jonsson & Lesshammar, 1999) :

- **Cascade économique** = *combien on perd*. Réconcilie au FCFA près :
  `potentiel − perte_volume − perte_qualite = reel`.
- **Lecture des causes D/P/Q** = *pourquoi on perd probablement*. Attribution
  indicative, **non additive** au manque à gagner. Une note obligatoire le
  rappelle sous le bloc.

Raison : une cascade est perçue comme une équation. Si `D + P + Q` ne tombait
pas exactement sur la valeur réelle, le graphique mentirait — faute
méthodologique fatale devant un jury.

## 3. Garantie de réconciliation

`perte_volume` est calculé en **résiduel** (`manque − perte_qualite`) en
arithmétique entière. Il absorbe tout écart d'arrondi, donc l'équation affichée
tombe toujours juste. Vérifié sur scénario à décimales volontairement bruitées :
`2 500 000 − 442 857 − 137 143 = 1 920 000` exact.

## 4. Garde-fou cas limite

Si la production valorisée dépasse la capacité cible (`reel > potentiel`), la
vue affiche « Objectif de capacité atteint » au lieu de barres négatives. C'est
le cas actuel sur les données de seed (volumes 22–36 m³/poste, supérieurs à la
capacité 12,5 m³ — artefact de seed déjà signalé dans l'audit). Sur données
terrain réalistes (≤ 12,5 m³/poste), la cascade montrera de vraies pertes.

## 5. Fichiers

| Fichier | Nature |
|---|---|
| `app/services/trs.py` | **+** `cascade_economique(equipes)` — réagencement pur de `calcule_manque_gagner()`, aucun calcul métier nouveau |
| `app/routes/dashboard.py` | **+** route `/chef/v2` `vue_chef_v2()` + import |
| `app/templates/chef/v2.html` | **nouveau** — Vue 1 LE POINT |
| `app/templates/chef/_cascade_pertes.html` | **nouveau** — cascade éco + attribution D/P/Q + note |
| `.claude/skills/run-cuf-pilotage/smoke.sh` | **+** check `/dashboard/chef/v2` |

## 6. Non-régression

- `/chef` (vue_chef) **intact** comme fallback. Aucun template existant modifié.
- Aucune nouvelle table, aucune migration. 100 % hors ligne.
- Smoke : 17/17 verts (16 + nouveau check V2).

## 7. Reste à faire (vues suivantes, après validation)

- Vue 2 « Mes décisions » : actions en cours, Ishikawa, bilan avant/après FCFA.
- Vue 3 « Rapport PDG » : synthèse + export Excel existant.
- Point à trancher avec l'utilisateur : le `manque` de la cascade (agrégat net)
  diffère du `manque_a_gagner_agrege` du dashboard (somme des manques par poste,
  jamais négative). Confirmer lequel devient la référence affichée.
