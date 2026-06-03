# Note d'impact mémoire — P50 : Message d'attente quand aucune fiche du jour (cockpit chef)

> Générée le : 2026-06-03
> Commit : `8d3d3f4` — feat(chef): message d'attente quand aucune fiche du jour (cockpit)
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `cuf-pilotage/app/routes/dashboard.py`, `cuf-pilotage/app/templates/chef/_aujourdhui.html`

---

## 1. Résumé de la fonctionnalité

Avant ce commit, la section « Aujourd'hui » du tableau de bord chef affichait toujours sa grille d'indicateurs, même quand aucune fiche n'avait encore été saisie pour la journée. Le chef voyait alors une rangée de zéros : objectif réalisé 0 m³, arrêts 0 min, rendement 0 %, déclassement 0 %. Visuellement, cela ressemblait à un outil en panne ou à un prototype inachevé, alors que la cause réelle était simplement l'absence de saisie à cette heure.

Après ce commit, la fonction `_kpi_aujourdhui()` calcule deux informations supplémentaires : un drapeau `vide` (vrai lorsqu'aucune équipe du jour n'est en statut à vérifier ou analysé) et la date de la dernière activité analysée. Le partiel `_aujourdhui.html` teste ce drapeau : si la journée est vide, il affiche un encart « En attente de la première saisie du jour » rappelant la dernière période connue et offrant un lien vers celle-ci, au lieu de la grille de zéros. Les blocs « Priorités du chef » et « Actions immédiates », qui se calculent sur la période et non sur la seule journée, restent visibles dans tous les cas.

---

## 2. Décision d'architecture — drapeau backend plutôt que détection côté template

La vacuité de la journée aurait pu être devinée dans le template en inspectant la liste des postes du jour, mais cette liste contient toujours deux entrées (matin et après-midi) avec un indicateur d'existence, ce qui rend la condition fragile et peu lisible. Calculer le drapeau `vide` au plus près de la donnée, dans `_kpi_aujourdhui()`, le rend fiable et réutilisable, et garde le template déclaratif. La date de dernière activité est obtenue par une seule requête ordonnée, sans table ni colonne nouvelle, ce qui respecte la sobriété attendue d'un calcul d'affichage.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS6 — Outil de pilotage adapté | **Direct.** L'interface distingue désormais « pas encore de donnée » de « donnée nulle », ce qui est essentiel pour un outil utilisé en continu sur le terrain. Le chef comprend l'état réel du système sans interprétation erronée. |
| OS1 — Production réelle et écart | **Indirect.** En évitant d'afficher un faux zéro, on protège la lecture de l'écart capacité/réalité d'un artefact d'affichage trompeur. |

---

## 4. Impact sur la validité scientifique des données

Nul sur les calculs. Aucune formule de TRS, de pertes ou de rendement n'est modifiée. Le commit ne change que la présentation conditionnelle d'indicateurs déjà calculés. La validité des chiffres reste strictement identique ; seule leur lisibilité en situation d'absence de donnée progresse.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune modification du modèle de données. Deux clés ajoutées à un dictionnaire de retour et une requête de lecture supplémentaire.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** Le commit est purement présentationnel et n'affecte aucune mesure servant à tester les hypothèses.

---

## 7. Nouveaux éléments introduits

| Élément | Fichier | Rôle |
|---|---|---|
| Drapeau `vide` | `dashboard.py` (`_kpi_aujourdhui`) | Vrai si aucune fiche du jour à vérifier ou analysée |
| `derniere_activite` | `dashboard.py` (`_kpi_aujourdhui`) | Date de la dernière équipe analysée, pour contextualiser l'attente |
| Encart « En attente de la première saisie » | `_aujourdhui.html` | Remplace la grille de zéros quand la journée est vide |

---

## 8. Utilisabilité terrain et adoption

Avant, un chef ouvrant l'outil tôt le matin, avant toute saisie, voyait des zéros et pouvait croire à un dysfonctionnement. Après, il lit un message explicite qui le rassure sur le bon fonctionnement et l'oriente vers la dernière période documentée. Ce comportement compte particulièrement au démarrage de la collecte terrain, lorsque les premières journées peuvent rester partiellement vides. Il rend aussi les démonstrations plus crédibles si elles ont lieu avant la saisie du jour.

---

## 9. Ce que cela change pour le mémoire

Le détail illustre un principe d'ergonomie défendable en soutenance : un bon tableau de bord distingue l'absence d'information de l'information nulle. Cette distinction, banale en apparence, est exactement ce qui sépare un prototype d'un outil de terrain mûr, et soutient l'argument OS6 sur l'adéquation de l'outil aux conditions réelles d'usage.

---

> **Vérification réalisée :** signal contrôlé sur deux dates — demain (sans données) renvoie `vide=True` avec dernière activité 03/06/2026 ; aujourd'hui renvoie `vide=False` avec 20,55 m³ réalisés. Smoke driver 16/16 OK.
