# CUF Pilotage — Journal des erreurs et apprentissages

> Mis à jour automatiquement après chaque correction
> Lire en début de session avant toute action

---

## 📚 RÈGLES ACCUMULÉES

### R1 — Toujours supprimer cuf.db après un changement de schéma
**Contexte :** SQLAlchemy `db.create_all()` est non-destructif — il ne supprime pas les colonnes obsolètes.
**Règle :** Si un modèle change (ajout/suppression de colonne), le fichier `instance/cuf.db` doit être supprimé sur la machine cible avant redémarrage.
**Instruction utilisateur :** `del instance\cuf.db` (Windows) puis `python run.py`

### R2 — Windows : `use_reloader=False` obligatoire
**Contexte :** Flask debug mode avec watchdog sur Windows Store Python provoque une boucle de rechargement infinie — le processus se relance en boucle toutes les secondes.
**Règle :** `run.py` doit toujours avoir `use_reloader=False, debug=True`.

### R3 — Capturer toutes les exceptions dans les routes POST
**Contexte :** `except (ValueError, KeyError)` ne capture pas les erreurs SQLAlchemy (`OperationalError`, `IntegrityError`). Résultat : page 500 générique sans détail.
**Règle :** Les routes POST de saisie utilisent `except Exception as e` avec `flash(f'Erreur : {type(e).__name__} — {str(e)}', 'danger')`.

### R4 — Cadrage obligatoire avant implémentation
**Contexte :** P2 a été commencé sans cadrage préalable. L'utilisateur a dû stopper le développement et demander un cadrage en bonne et due forme.
**Règle :** Pour toute nouvelle phase ou fonctionnalité non triviale, présenter un document de cadrage et attendre la validation explicite avant tout code.

### R5 — volume_sorti ≠ volume_conforme
**Contexte :** L'ancien modèle avait `volume_sorti` ambigu. L'utilisateur a précisé que la production réelle se compose de trois catégories distinctes.
**Règle :** 
- `volume_conforme` = planches conformes (export, prix plein)
- `volume_declass` = bois déclassé vendu localement (prix ×0.30)
- `volume_dechets` = calculé par différence, jamais stocké en DB
- Pour le TRS Performance : `volume_sorti = conforme + declass` (tout ce qui sort de la scie utilisable)
- Pour le TRS Qualité : `conforme / (conforme + declass)` — les déchets sont exclus (pertes process, pas qualité)

### R6 — Ne jamais coder avant validation du plan (Vibe Coding Protocol)
**Contexte :** Instauré par l'utilisateur le 2026-04-30.
**Règle :** Toute tâche impliquant 3+ étapes requiert : plan écrit → explication → validation explicite → puis code.
**Commandes de validation :** `ok`, `vas-y`, `d'accord`, `go`, `✅`, `lance`, `continue`, `oui`

### R7 — Ne jamais effacer la DB au démarrage de l'application
**Contexte :** P5b — `start.ps1` supprimait `instance/cuf.db` à chaque lancement, laissant le dashboard vide à chaque redémarrage Windows. L'utilisateur ne voyait pas ses fonctionnalités P5.
**Règle :** Le script de démarrage ne doit jamais supprimer de données utilisateur. La suppression doit être manuelle et explicite (`del instance\cuf.db` documenté en cas de migration de schéma — voir R1). Le seed doit utiliser un guard idempotent (`if Equipe.query.first(): return`) pour ne s'exécuter qu'une fois sur base vide.

### R8 — Templates Jinja2 défensifs avec `|default()`
**Contexte :** P5c — un crash `UndefinedError: 'nb_brouillons' is undefined` est apparu côté Windows après un `git pull` partiellement échoué (DNS error). Le template avait été mis à jour mais pas la route → désynchronisation.
**Règle :** Toute variable de contexte référencée dans un template doit avoir un fallback `|default(valeur_neutre)`. Exemples : `{% if nb_brouillons|default(0) > 0 %}`, `{% if prix_manquants|default(false) %}`. Filet de sécurité contre les désynchronisations route/template, pas un substitut à la cohérence du code.

### R9 — Contrôle d'accès par propriété, pas seulement par rôle
**Contexte :** P5d — l'alerte brouillon devait mener à une vue lecture seule pour le PDG. Plutôt que d'ajouter `if role == 'pdg': hide_buttons`, on a constaté que le template existant `historique.html` masquait déjà les boutons via `if p.user_id == current_user.id`.
**Règle :** Préférer un contrôle d'accès basé sur la propriété de l'objet (`obj.user_id == current_user.id`) à un contrôle basé sur le rôle. Plus robuste, plus testable, fonctionne même si un nouveau rôle est ajouté plus tard sans modifier les templates.

### R10 — Fonctions pures vs fonctions à mutation : séparer
**Contexte :** P6-F1 — `calcule_trs(equipe)` mute l'objet (assigne `equipe.trs_disponibilite`, etc.). Pour le dashboard en lecture seule, il fallait un (D, P, Q) sans dirtyfier la session SQLAlchemy.
**Règle :** Quand un calcul est utilisé dans un contexte read-only (dashboard, export, stats), créer un helper pur séparé (ex. `decompose_dpq(equipe)` retourne `(d, p, q)` sans rien modifier). Garder la version à mutation pour les routes de soumission/écriture. Ne jamais appeler la version mutante depuis une route GET.

### R11 — Toute arithmétique côté Python, jamais en Jinja2
**Contexte :** P6-F2 — la matrice criticité affiche des durées formatées (`1h30`, `45min`). Tenté de faire la conversion minutes → format en Jinja2 : impossible (pas de `divmod`). 
**Règle :** Pré-calculer toutes les valeurs d'affichage côté route Python (formats, pourcentages, couleurs CSS) et passer au template un dict prêt à l'emploi. Jinja2 ne doit faire que de l'itération et de l'affichage. Bénéfice secondaire : les valeurs sont testables sans lancer Flask.

### R12 — Cascade multiplicative D × P × Q : jamais 3 barres de pourcentage juxtaposées
**Contexte :** P6-F1 — réflexe initial : afficher D=89 %, P=86 %, Q=87 % comme trois barres côte à côte. Erreur cognitive : suggère une additivité fausse alors que TRS = D × P × Q (multiplicatif). La critique utilisateur a corrigé : afficher la cascade en m³ perdus.
**Règle :** Pour toute visualisation TRS, utiliser la décomposition cascade `(1−D)·cap + D·(1−P)·cap + D·P·(1−Q)·cap + D·P·Q·cap = cap`. Une seule barre stacked à 4 segments, pas 3 barres distinctes. L'identité algébrique garantit qu'aucune perte n'est comptée deux fois.

---

## 📅 HISTORIQUE DES CORRECTIONS

| Date | Correction | Règle créée |
|------|-----------|-------------|
| 2026-04-30 | Schéma DB incompatible → 500 | R1 |
| 2026-04-30 | Flask reload infini Windows | R2 |
| 2026-04-30 | Exceptions trop étroites | R3 |
| 2026-04-30 | P2 sans cadrage | R4 |
| 2026-04-30 | Modèle matière ambigu | R5 |
| 2026-04-30 | Vibe Coding Protocol instauré | R6 |
| 2026-05-03 | DB effacée à chaque lancement | R7 |
| 2026-05-03 | UndefinedError sur désync template/route | R8 |
| 2026-05-03 | Contrôle PDG basé sur rôle au lieu de propriété | R9 |
| 2026-05-04 | Mutation d'équipe dans contexte read-only | R10 |
| 2026-05-04 | Tentative de divmod en Jinja2 | R11 |
| 2026-05-04 | TRS affiché comme 3 barres % juxtaposées | R12 |
