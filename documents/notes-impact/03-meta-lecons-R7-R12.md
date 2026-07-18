# Note d'impact mémoire — Méta : ajout des règles R7 à R12 dans `leçons.md`
**Commit :** `ec4bf22` — `docs(leçons): ajoute R7-R12 — leçons des phases P5b à P6-F1`
**Date :** 2026-05-04
**Fichier modifié :** `tâches/leçons.md` (+30 lignes)

---

## 1. Ce qui a été implémenté

Extension du fichier de référence méta-cognitive `tâches/leçons.md` avec six nouvelles règles consolidées à partir des erreurs et décisions des phases P5b → P6-F1.

| Règle | Origine | Domaine |
|---|---|---|
| **R7** Ne jamais effacer la DB au démarrage | P5b (`start.ps1`) | Persistance des données |
| **R8** Templates Jinja2 défensifs `\|default()` | P5c (`pdg/dashboard.html`) | Robustesse template |
| **R9** Contrôle d'accès par propriété, pas par rôle | P5d (`saisie/historique.html`) | Sécurité applicative |
| **R10** Séparer fonctions pures et fonctions à mutation | P6-F1 (`decompose_dpq` vs `calcule_trs`) | Architecture |
| **R11** Toute arithmétique en Python, jamais en Jinja2 | P6-F2 (matrice criticité) | Architecture |
| **R12** Cascade multiplicative D × P × Q : 1 barre stacked, pas 3 barres | P6-F1 (cascade m³) | Visualisation TRS |

---

## 2. Lien avec les objectifs du mémoire

Cet enrichissement n'est pas un livrable académique direct, mais il alimente la **section méthodologique du mémoire** : chaque règle est la trace d'une décision de conception ou d'une erreur évitée, ce qui constitue un matériau brut pour documenter la démarche réflexive (boucle action → erreur → règle → action améliorée).

R10, R11, R12 en particulier sont transférables au-delà du projet CUF — ce sont des règles d'architecture logicielle générales qui peuvent illustrer dans le mémoire la rigueur méthodologique appliquée à l'OS6 (conception de l'outil de pilotage).

---

## 3. Données et calculs mobilisés

Aucun calcul. Documentation pure.

---

## 4. Hypothèses testées ou confirmées

**Aucune contradiction avec les hypothèses existantes.**

R12 mérite d'être signalée : elle documente explicitement que l'erreur cognitive « 3 barres % juxtaposées » a été commise et corrigée. Cela renforce la crédibilité scientifique du dashboard final, car le piège représentationnel a été identifié et évité — ce qui sera utile à mentionner si un membre du jury interroge la pertinence du choix de visualisation.

---

## 5. Ce que ce module permet de montrer dans le mémoire

- L'existence d'un fichier `leçons.md` mis à jour à chaque correction est une preuve concrète de **pratique réflexive** au sens de Schön (1983) — réflexion-en-action et réflexion-sur-action.
- Les règles R7 à R12 illustrent que la conception de l'outil de pilotage n'a pas été linéaire : il y a eu des allers-retours entre intuition initiale et correction par la critique. Cela rend la méthodologie crédible et auditable.
- Le format « contexte → règle → date » permet une lecture chronologique de l'apprentissage du projet, exploitable directement dans la section Discussion du mémoire.

---

## 6. Limites actuelles

- Le fichier `leçons.md` est en français mais utilise un style technique (`SQLAlchemy`, `Jinja2`, `decompose_dpq`) qui ne sera pas accessible tel quel au jury. Il faudra produire une version simplifiée pour les annexes du mémoire, en traduisant les règles techniques en formulations méthodologiques générales.
- Les règles ne sont pas hiérarchisées par criticité — toutes sont au même niveau alors que R6 (Vibe Coding Protocol) et R10 (séparation pure/mutation) sont structurellement plus importantes que R2 (paramètre `use_reloader=False`).

---

## 7. Vérification de cohérence avec les notes précédentes

Chaque règle R7-R12 est explicitement rattachée à une note d'impact existante :
- R7 ↔ `P5b-seed-demo-et-stabilite-db.md`
- R8 ↔ `P5c-fix-jinja-defaults.md`
- R9 ↔ `P5d-alerte-brouillon-lien-pdg.md`
- R10, R12 ↔ `P6-F1-decomposition-cascade-m3.md`
- R11 ↔ `P6-F2-matrice-criticite.md`

Cette traçabilité bidirectionnelle (note d'impact détaillée → règle synthétique dans `leçons.md`) garantit qu'aucune décision documentée dans une note ne se perd au fil du temps.

Aucune contradiction.

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Schön (1983) — Le praticien réflexif | Le format itératif de `leçons.md` est l'opérationnalisation directe du concept de réflexion-sur-action |
| Argyris & Schön (1978) — Apprentissage organisationnel | Le passage erreur → règle → règle appliquée illustre l'apprentissage en double boucle |

(Ces références ne sont pas dans la revue de littérature actuelle du mémoire mais peuvent être ajoutées en annexe méthodologique si pertinent.)

---

## 9. Prochaines étapes

- **F5 — Scorecard 7 jours calendaire (lun–sam)** : prochaine fonctionnalité Chef à implémenter, suivant le Vibe Coding Protocol (R6) — plan écrit avant code.
- **À l'achèvement de P6 :** envisager de traduire `leçons.md` en français accessible pour les annexes méthodologiques du mémoire.
