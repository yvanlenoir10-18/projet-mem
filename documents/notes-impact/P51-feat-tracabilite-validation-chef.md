# Note d'impact mémoire — P51 : Ligne de traçabilité de la validation (tableau de bord chef)

> Générée le : 2026-06-03
> Commit : `889e9f1` — feat(chef): ligne de traçabilité de la validation sur le tableau de bord
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `cuf-pilotage/app/routes/dashboard.py`, `cuf-pilotage/app/templates/chef/dashboard.html`

---

## 1. Résumé de la fonctionnalité

Avant ce commit, le tableau de bord chef affichait un TRS, un manque à gagner et des dizaines d'indicateurs sans jamais préciser sur quelles fiches reposaient ces calculs. Seules les fiches validées ou verrouillées entrent dans les agrégats, mais le chef ne pouvait pas savoir combien de fiches avaient été comptabilisées ni combien restaient hors du calcul faute de validation. Devant un encadreur, il aurait été incapable de répondre à la question « ces 70 % de TRS, c'est sur combien de postes ? ».

Après ce commit, une ligne discrète apparaît sous le sélecteur de période. Elle indique le nombre de fiches validées comptabilisées sur la période affichée, le nombre de fiches non prises en compte ventilé par statut (à vérifier, à corriger, brouillon) avec un lien direct vers chaque sous-liste filtrée, la période analysée, et la date et l'heure de la dernière mise à jour. La fonction `_tracabilite_validation()` réalise un simple comptage par statut sur la même fenêtre temporelle que le tableau de bord, qu'il soit en mode mois ou en mode N derniers jours.

---

## 2. Décision d'architecture — comptage par statut sur la fenêtre du tableau de bord

Le calcul réutilise les constantes de statut existantes (`STATUTS_ANALYSES`, `STATUTS_NON_ANALYSES`) plutôt que de redéfinir une logique d'inclusion. Les bornes de période sont capturées dans chaque branche du sélecteur (mois civil ou fenêtre glissante) puis transmises au helper, ce qui garantit que la ligne de traçabilité décrit exactement le même périmètre que les indicateurs affichés. La date de dernière mise à jour s'appuie sur la soumission la plus récente parmi les fiches comptées, sans colonne ni table nouvelle. Les compteurs non nuls deviennent des liens vers la liste de fiches déjà filtrable, ce qui transforme un constat passif en point d'action sans créer de nouvelle route.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS1 — Production réelle, écart et TRS | **Direct.** La crédibilité scientifique d'un indicateur repose sur la transparence de sa base de calcul. Exposer le nombre de fiches comptées rend le TRS et l'écart vérifiables, donc défendables. |
| OS6 — Outil de pilotage adapté | **Direct.** Le chef passe d'une confiance aveugle dans les chiffres à une lecture éclairée : il sait quand ses indicateurs sont complets et quand ils reposent sur des données partielles. |

---

## 4. Impact sur la validité scientifique des données

Fort et positif. Cette fonctionnalité ne modifie aucun calcul mais rend explicite la frontière entre données incluses et exclues, frontière jusque-là invisible. Pour le mémoire, c'est un argument direct de rigueur : un indicateur de performance n'a de valeur que si l'on connaît son assiette. La ligne signale aussi, par le décompte des fiches non comptabilisées, le risque de sous-estimation ou de surestimation lié à des fiches en attente de validation, ce qui invite le chef à compléter la validation avant d'interpréter les chiffres.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Le helper effectue un comptage par statut et une requête de soumission la plus récente, sans modification du schéma ni nouvelle table.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** La fonctionnalité renforce indirectement la fiabilité du test de H3 (TRS réel insuffisant) en rendant visible le nombre de fiches sur lequel le TRS est calculé : un TRS établi sur peu de fiches doit être interprété avec prudence, ce que la ligne permet désormais de constater.

---

## 7. Nouveaux éléments introduits

| Élément | Fichier | Rôle |
|---|---|---|
| `_tracabilite_validation()` | `dashboard.py` | Compte les fiches comptabilisées vs non comptabilisées par statut sur la période |
| Capture des bornes `trace_debut`/`trace_fin` | `dashboard.py` (`vue_chef`) | Aligne le périmètre de traçabilité sur celui du tableau de bord |
| Variable `tracabilite` (2 render) | `dashboard.py` | Transmise aussi dans la branche sans données |
| Ligne de traçabilité | `dashboard.html` | Affiche comptes, liens vers sous-listes, période et dernière mise à jour |

---

## 8. Utilisabilité terrain et adoption

Avant, un chef confronté à un encadreur ne pouvait pas justifier la base de ses indicateurs. Après, il lit en une ligne « 60 fiches validées comptabilisées sur 30 derniers jours, 2 non prises en compte, dernière mise à jour le 03/06/2026 à 14:20 ». S'il voit des fiches non comptabilisées, il clique et accède directement à la liste pour les traiter. Cette transparence renforce la confiance dans l'outil et encourage la discipline de validation, condition d'indicateurs complets.

---

## 9. Ce que cela change pour le mémoire

La fonctionnalité matérialise un principe de gouvernance de la donnée que le mémoire peut revendiquer : la performance affichée est traçable jusqu'aux fiches sources. C'est l'ossature d'un système de mesure crédible, par opposition à un tableau de bord dont les chiffres tombent du ciel. Elle illustre aussi le M et le C de la démarche DMAIC — mesurer puis contrôler la qualité de la mesure elle-même — et soutient l'argument selon lequel l'absence préalable de système de mesure fiable justifiait la démarche.

---

> **Vérification réalisée :** helper contrôlé sur 30 jours (60 comptabilisées, 2 brouillons, dernière mise à jour 03/06/2026). Capture d'écran du tableau de bord chef confirmant la ligne sous le sélecteur de période. Smoke driver 16/16 OK.
