# Note d'impact mémoire — P5c : Correction défense Jinja2 (UndefinedError)
**Commit :** `90db8e3` — `fix(pdg): défaut Jinja sur nb_brouillons et prix_manquants`
**Date :** 2026-05-03
**Fichiers modifiés :** `app/templates/pdg/dashboard.html` (2 lignes)

---

## 1. Ce qui a été implémenté

Deux filtres `|default()` ajoutés dans le template PDG pour empêcher un crash `jinja2.exceptions.UndefinedError` lorsqu'une variable de contexte est absente :

| Ligne | Avant | Après |
|---|---|---|
| 7 | `{% if prix_manquants %}` | `{% if prix_manquants\|default(false) %}` |
| 17 | `{% if nb_brouillons > 0 %}` | `{% if nb_brouillons\|default(0) > 0 %}` |

Ces deux variables sont passées par la route P5 depuis le commit `2332173`. Le crash survient uniquement si le template et la route sont désynchronisés — typiquement un `git pull` ayant échoué partiellement côté Windows (DNS : "Could not resolve host: github.com").

---

## 2. Lien avec les objectifs du mémoire

Correctif de robustesse sans impact académique direct. Améliore la fiabilité du déploiement Windows pour les démonstrations en soutenance — un crash UndefinedError devant le jury lors d'une démo en direct serait pénalisant.

---

## 3. Données et calculs mobilisés

Aucun. Le filtre `|default(false)` retourne `False` si la variable est absente → le bloc `{% if %}` ne s'exécute pas → pas de crash.

---

## 4. Hypothèses testées ou confirmées

Aucune contradiction avec les hypothèses existantes. Test automatisé : status 200 confirmé via Flask test client avec les données de démonstration P5b.

---

## 5. Ce que ce module permet de montrer dans le mémoire

Néant pour la rédaction académique. Correctif technique pur.

---

## 6. Limites actuelles

La cause racine (désynchronisation git sur Windows) reste à résoudre par un `git reset --hard origin/claude/install-claude-excel-6MGzv` côté Windows. Le `|default()` est un filet de sécurité, pas un substitut à la mise à jour du code.

---

## 7. Vérification de cohérence avec les notes précédentes

Aucune contradiction.

---

## 8. Références bibliographiques mobilisées implicitement

Aucune.

---

## 9. Prochaines étapes

- Résoudre la synchronisation git côté Windows (git fetch + reset --hard)
- P6 Dashboard Chef enrichi
