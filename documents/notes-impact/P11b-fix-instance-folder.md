# Note d'impact — P11b : Fix démarrage Windows (dossier instance/)
> Commit : e2fa696 — fix(start): créer instance/ automatiquement si absent après git clone
> Date : 2026-05-12
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Correction du script `start.ps1` pour créer automatiquement le dossier `instance/` s'il est absent. Sans ce dossier, SQLite ne peut pas créer le fichier `cuf.db` et Flask échoue au démarrage avec `sqlite3.OperationalError: unable to open database file`. Ce cas se produit systématiquement après un `git clone` car `instance/` est dans `.gitignore`.

---

## 2. Fichiers modifiés ou créés

| Fichier | Type | Action |
|---|---|---|
| `cuf-pilotage/start.ps1` | Script Windows | Ajout étape 3 : `New-Item instance/` si absent |

Aucune modification de code applicatif. Aucun impact sur la base de données.

---

## 3. Objectif spécifique du mémoire servi

**OS6 — Concevoir un outil de pilotage adapté** : l'outil doit pouvoir être installé et lancé sans intervention technique sur le site CUF. Ce fix garantit qu'un déploiement à partir d'un `git clone` fonctionne en une seule commande (`.\start.ps1`) sans connaissance de SQLite ou de Flask.

---

## 4. Lien avec les hypothèses de recherche

**Aucune hypothèse de recherche concernée.** Il s'agit d'un fix de déploiement pur. Aucune contradiction avec H1–H4.

---

## 5. Technique utilisée et choix architectural

SQLite crée le fichier `.db` mais pas le dossier parent. Flask ne crée pas non plus le dossier `instance/` automatiquement (contrairement à une idée reçue — il le fait uniquement si `instance_path` est explicitement configuré avec `instance_relative_config=True` et que l'app est créée via `Flask(__name__, instance_relative_config=True)`). La solution la plus simple et la plus robuste est de créer le dossier dans le script de démarrage, avant le lancement de Flask.

---

## 6. Contrainte respectée

**Règle R7** : aucune modification de schéma de base de données. Le fix ne touche qu'au script de démarrage.

---

## 7. Limites identifiées

- Le fix n'est actif que via `start.ps1`. Un utilisateur qui lance `python run.py` directement sans passer par le script verra encore l'erreur si `instance/` est absent. Solution future : ajouter un `os.makedirs` dans `create_app()` pour être totalement autonome.

---

## 8. Commandes Windows pour appliquer

```powershell
git pull origin claude/install-claude-excel-6MGzv
.\start.ps1
```

Le script crée maintenant `instance/` automatiquement avant de lancer Flask. Aucune autre action requise.

---

## 9. Références bibliographiques mobilisées

Aucune — fix d'infrastructure, pas de contenu académique.
