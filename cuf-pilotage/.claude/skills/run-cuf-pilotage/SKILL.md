---
name: run-cuf-pilotage
description: Run, start, launch, test, screenshot, smoke-test, verify the CUF Pilotage Flask web app (wood_pilot). Drive it with curl or Playwright. Check that login, saisie, dashboard chef, PDG, admin, anti-chevauchement all work. Take real screenshots of every view.
---

# run-cuf-pilotage

Application Flask de pilotage de la production (wood_pilot) pour la scierie CUF Ebolowa. Serveur web local, 100 % hors ligne, base SQLite.

Deux drivers disponibles selon le besoin :
- **`smoke.sh`** — curl + cookies : vérifie les routes serveur (16 checks, exit 0/1). Pas besoin de navigateur. Idéal pour valider une PR qui touche des routes Flask.
- **`screenshot.py`** — Playwright headless : prend de vraies screenshots de l'UI pour chaque rôle. Idéal pour vérifier des changements de template ou de CSS.

**Unit root :** `cuf-pilotage/` (tous les chemins ci-dessous sont relatifs à ce dossier).

---

## Prérequis

```bash
# Python 3.11+ requis (vérifié : Python 3.11.15)
python --version

# Dépendances app (déjà installées dans ce container — relancer si clean slate)
pip install -r requirements.txt

# Pour screenshot.py uniquement — Playwright + Chromium
pip install playwright
# Chromium déjà présent dans ce container :
# /opt/pw-browsers/chromium-1194/chrome-linux/chrome
```

Pas de venv, pas de `apt-get` supplémentaire : toutes les dépendances sont des packages Python purs.

---

## Build / initialisation

```bash
cd cuf-pilotage
python run.py   # crée instance/woodpilot.db + seed au premier démarrage
# Ctrl-C une fois "Running on http://127.0.0.1:5000" affiché
```

La base SQLite est créée automatiquement dans `instance/woodpilot.db` au premier `run.py`. Le seed crée 4 comptes (voir Comptes ci-dessous). `_repair_seed_roles()` s'exécute à chaque démarrage pour corriger d'éventuelles incohérences de rôle.

---

## Run — chemin agent (driver smoke.sh)

```bash
cd cuf-pilotage
bash .claude/skills/run-cuf-pilotage/smoke.sh            # lance + teste + arrête
bash .claude/skills/run-cuf-pilotage/smoke.sh --keep-running  # laisse le serveur actif
```

Sortie attendue (16 checks, exit 0) :
```
[smoke] serveur déjà actif sur :5000
--- Profil opérateur (saisie@cuf.cm) ---
[smoke] OK  accueil opérateur → 200
[smoke] OK  formulaire nouveau → 200
[smoke] OK  historique → 200
[smoke] OK  soumission fiche → 302 (brouillon créé)
--- Profil chef (chef@cuf.cm) ---
[smoke] OK  dashboard chef → 200
...
[smoke] OK  anti-chevauchement → bloqué (HTTP 200 + flash danger)

[smoke] ✓ Tous les tests passent.
```

### Piloter manuellement avec curl

```bash
# 1. Récupérer un CSRF et un cookie de session
COOKIE=$(mktemp)
CSRF=$(curl -s -c "$COOKIE" http://127.0.0.1:5000/login \
  | grep -o 'name="csrf_token" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')

# 2. Login (role: operateur | chef | pdg | admin)
curl -s -c "$COOKIE" -b "$COOKIE" \
  --data "email=chef%40cuf.cm&password=cuf2026&csrf_token=${CSRF}" \
  -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/login
# → 302 (redirection vers dashboard)

# 3. Appeler n'importe quelle route
curl -s -b "$COOKIE" http://127.0.0.1:5000/dashboard/chef | grep -o '<h1[^>]*>[^<]*</h1>'
curl -s -b "$COOKIE" http://127.0.0.1:5000/analyse/arrets | wc -c

# 4. Soumettre une fiche de saisie (rôle opérateur)
CSRF=$(curl -s -c "$COOKIE" -b "$COOKIE" http://127.0.0.1:5000/saisie/nouveau \
  | grep -o 'name="csrf_token" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')
curl -s -c "$COOKIE" -b "$COOKIE" \
  --data "csrf_token=${CSRF}&date=2026-05-28&poste=matin&numero_equipe=1&operateur_nom=Test&rempli_par_nom=Test&effectif=10&aucun_arret_confirme=1&prod_essence[]=Ayous&prod_heure_debut[]=06:00&prod_heure_fin[]=11:00&prod_volume_entree[]=8.0&prod_volume_conforme[]=5.0&prod_volume_declass[]=1.0" \
  -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/saisie/nouveau
# → 302 (brouillon créé)
```

---

## Screenshots — driver Playwright

```bash
cd cuf-pilotage

# Toutes les vues, tous les rôles (10 screenshots)
python .claude/skills/run-cuf-pilotage/screenshot.py
# → .claude/skills/run-cuf-pilotage/screenshots/*.png

# Un seul rôle
python .claude/skills/run-cuf-pilotage/screenshot.py operateur
python .claude/skills/run-cuf-pilotage/screenshot.py chef

# Vue ad-hoc (le rôle est déduit du chemin)
python .claude/skills/run-cuf-pilotage/screenshot.py /saisie/historique
# → /tmp/cuf-ss/saisie-historique.png
```

Chromium utilisé : `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` (déjà présent, pas de download).
Chaque rôle utilise un contexte de navigateur isolé — pas de pollution de session entre les logins.

**Gotcha Playwright** : ne pas réutiliser `async_playwright()` entre deux `login()` du même contexte. Flask-Login redirige vers l'accueil si déjà connecté — `input[name="email"]` n'existe pas → `TimeoutError`. Solution : créer un nouveau contexte (`browser.new_context()`) par rôle.

---

## Run — chemin humain

```bash
cd cuf-pilotage
python run.py
# → ouvre http://127.0.0.1:5000 dans le navigateur
# Ctrl-C pour arrêter
```

---

## Comptes de test (tous mot de passe `cuf2026`)

| Rôle | Email | Accès |
|---|---|---|
| opérateur | `saisie@cuf.cm` | Saisie fiches, accueil, historique |
| chef | `chef@cuf.cm` | Dashboard, analyse, recommandations, problèmes |
| PDG | `pdg@cuf.cm` | Dashboard exécutif |
| admin | `admin@cuf.cm` | Paramètres, utilisateurs |

---

## Routes principales

```
GET  /                          → redirect login si non connecté
GET  /login                     → formulaire login (CSRF requis pour POST)
GET  /saisie/accueil            → accueil opérateur
GET  /saisie/nouveau            → formulaire nouvelle fiche
POST /saisie/nouveau            → créer fiche (champs: prod_essence[], prod_heure_debut[], prod_heure_fin[], prod_volume_entree[], prod_volume_conforme[], prod_volume_declass[])
GET  /saisie/historique         → liste fiches opérateur
GET  /dashboard/chef            → dashboard chef production
GET  /analyse/arrets            → pareto arrêts
GET  /recommandations/          → recommandations IA
GET  /problemes/                → liste problèmes Ishikawa
GET  /dashboard/pdg             → dashboard PDG
GET  /admin/parametres          → paramètres app
GET  /dashboard/export/excel    → export Excel
```

---

## Validation métier vérifiée

**Anti-chevauchement** : deux essences sur des créneaux qui se recouvrent → HTTP 200 + flash `danger` "Chevauchement horaire". Bornes jointives (fin=début) autorisées → HTTP 302.

```bash
# Test chevauchement (doit bloquer)
curl -s -b "$COOKIE" \
  --data "...prod_essence[]=Ayous&prod_heure_debut[]=06:00&prod_heure_fin[]=11:00&...
         &prod_essence[]=Azobe&prod_heure_debut[]=08:00&prod_heure_fin[]=14:00..." \
  -w "%{http_code}" http://127.0.0.1:5000/saisie/nouveau
# → 200 (bloqué)
```

---

## Gotchas

- **Port 5000 déjà occupé** : Flask refuse de démarrer. `lsof -i :5000` pour trouver le PID, ou utiliser un port alternatif avec `PORT=5001 python run.py` (nécessite de modifier `run.py` temporairement).
- **Chaque POST sur le formulaire nécessite un nouveau CSRF** : le token est à usage unique. Ne pas réutiliser le CSRF d'une requête précédente.
- **Noms de champs avec `[]`** : les champs multi-valeurs s'appellent `prod_essence[]`, pas `prod_essence`. Flask/Werkzeug lit `getlist('prod_essence[]')`.
- **Login retourne HTTP 200 au lieu de 302** : mot de passe incorrect, ou email URL-encodé manquant (`@` → `%40`).
- **`_repair_seed_roles()` s'exécute au démarrage** : si `saisie@cuf.cm` a le rôle `admin` en base, il sera automatiquement corrigé en `operateur` au prochain démarrage.
- **SQLite en mode WAL** : pas de lock reader/writer sur Linux. Pas de problème de concurrence en dev mono-process.
- **`use_reloader=False`** dans `run.py` : intentionnel — évite la boucle de rechargement Python Store sur Windows. Sur Linux n'a aucun effet.
- **Playwright `playwright install`** échoue dans ce container (pas d'accès réseau aux CDN). Utiliser le Chromium déjà présent via `executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'`.
- **`TimeoutError: Page.fill — waiting for input[name="email"]`** dans Playwright : login appelé sur un contexte déjà authentifié. Flask-Login redirige vers l'accueil — le formulaire login n'existe pas. Fix : nouveau `browser.new_context()` par rôle.

---

## Troubleshooting

| Symptôme | Cause | Fix |
|---|---|---|
| `Address already in use` | Processus Flask déjà actif | `kill $(lsof -ti :5000)` |
| `ModuleNotFoundError` | Dépendance manquante | `pip install -r requirements.txt` |
| Login → HTTP 200 (reste sur login) | Mauvais mot de passe ou email mal encodé | Vérifier `%40` pour `@`, password `cuf2026` |
| Route → HTTP 403 | Mauvais rôle pour cette route | Vérifier le rôle du compte connecté |
| Flash "Chevauchement horaire" | Deux créneaux qui se recouvrent | Corriger les horaires (bornes jointives OK) |
| `instance/woodpilot.db` absent | Premier démarrage, base non créée | Lancer `python run.py` une première fois |
| `playwright install` échoue | Pas d'accès réseau CDN dans ce container | Utiliser `executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'` — déjà dans `screenshot.py` |
