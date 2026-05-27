# Note d'impact mémoire — P21 : Bugfix garde défensive `_progression.html`

> Générée le : 2026-05-27
> Commit : `59b0031` — fix(template): garde défensive is defined dans _progression.html
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `_progression.html`

---

## 1. Résumé de la fonctionnalité

Correction d'un crash `jinja2.exceptions.UndefinedError: 'stats_operateur' is undefined` qui se produisait sur la page d'accueil opérateur (`/saisie/accueil`) lorsque le composant `_progression.html` était inclus depuis un contexte de template qui ne passait pas la variable `stats_operateur`.

**Cause racine :** La garde `{% if stats_operateur is not none %}` passe silencieusement quand `stats_operateur` est absent du contexte Jinja2. Jinja2 instancie alors un objet `Undefined` (pas `None`), la condition `is not none` est évaluée à `True`, et l'accès ultérieur aux attributs (`s.trs_moyen`, etc.) lève `UndefinedError`.

**Correction :** La ligne 3 de `_progression.html` passe de `{% if stats_operateur is not none %}` à `{% if stats_operateur is defined and stats_operateur is not none %}`. Le composant se cache silencieusement si la variable est absente du contexte, au lieu de planter.

---

## 2. Décision d'architecture — compatibilité ascendante du composant partagé

Le composant `_progression.html` est conçu pour être inclus dans plusieurs templates (`accueil_operateur.html`, `historique.html`). Pour un composant partagé, la robustesse face à un contexte incomplet est une propriété de qualité fondamentale : une route qui n'a pas encore été mise à jour pour passer `stats_operateur` ne doit pas faire planter toute la page.

**Décision :** Le comportement dégradé correct est le silence (le bloc n'est pas rendu), pas une erreur 500. C'est le pattern standard pour les composants Jinja2 optionnels : tester `is defined` avant de tester la valeur.

Ce bug est apparu en production Windows parce que la copie locale avait un `saisie.py` de version antérieure (pre-F1) qui ne passait pas `stats_operateur`, mais un `accueil_operateur.html` de version récente (post-F1) qui inclut le composant.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS6 — Outil de pilotage adapté | **Indirect (stabilité).** Le composant de progression (OS6) est maintenant résilient aux désalignements de version. L'outil peut être déployé sur des postes avec des états de synchronisation différents sans crash. |

---

## 4. Impact sur la validité scientifique des données

Aucun impact direct. Ce fix est purement de robustesse d'interface. Il ne modifie aucune logique de calcul, aucune formule TRS, aucune règle de collecte.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune modification du modèle de données.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

Ce commit est un bugfix défensif, sans impact sur les hypothèses de recherche.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| Test `is defined` | `_progression.html`, ligne 3 | Garde défensive : le composant se masque si `stats_operateur` est absent du contexte Jinja2 |

---

## 8. Utilisabilité terrain et adoption

- **Avant le fix :** une erreur 500 s'affichait sur l'accueil opérateur si la copie locale avait un `saisie.py` non synchronisé — bloquant totalement l'accès à la page.
- **Après le fix :** l'accueil opérateur se charge. Si `stats_operateur` est absent (copie `saisie.py` ancienne), le bloc de progression est simplement absent ; les autres sections (carte priorité, grille postes) fonctionnent normalement.

---

## 9. Ce que cela change pour le mémoire

Ce bugfix n'a pas d'impact direct sur le contenu du mémoire. Il assure la stabilité du prototype lors des démonstrations terrain, ce qui est une condition nécessaire pour la validité des observations relatives à l'OS6 (outil de pilotage adapté).

---

> **Vérification réalisée :** Correction unitaire de la ligne 3 de `_progression.html`. Le composant est rendu si `stats_operateur` est un dict valide, masqué silencieusement si `None` ou absent du contexte. Fix poussé sur `origin/claude/install-claude-excel-6MGzv` — l'utilisateur peut faire `git pull` pour récupérer la correction immédiatement.
