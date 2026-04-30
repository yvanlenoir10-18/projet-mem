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
