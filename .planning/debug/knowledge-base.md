# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## profil-operateur-bugs — Profil opérateur inaccessible : rôle DB erroné + garde Jinja2 manquante
- **Date:** 2026-05-27
- **Error patterns:** UndefinedError, stats_operateur, operateur, role, accueil, progression, _progression.html
- **Root cause:** (1) Agent Saisie (saisie@cuf.cm) seedé avec role='admin' au lieu de 'operateur' — aucun utilisateur operateur en base, profil opérateur inatteignable. (2) _progression.html manquait le test `is defined` sur stats_operateur — Jinja2 renvoie Undefined (pas None) pour une variable absente, la condition `is not none` passait et plantait sur l'accès aux attributs.
- **Fix:** (1) Ajout de `_repair_seed_roles()` dans `__init__.py` — corrige le rôle au démarrage de façon idempotente, crée admin@cuf.cm si absent. (2) `_progression.html` ligne 3 : `{% if stats_operateur is defined and stats_operateur is not none %}`. (3) `_stats_operateur()` : suppression double requête DB + inclusion de `a_corriger` dans `postes_semaine`.
- **Files changed:** app/__init__.py, app/routes/saisie.py, app/templates/saisie/_progression.html
---

