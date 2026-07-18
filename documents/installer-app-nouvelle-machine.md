# Installer et lancer l'app CUF Pilotage sur une nouvelle machine (Windows)

> Deux méthodes : **A. via Git** (télécharge depuis GitHub, nécessite l'accès au dépôt) · **B. via clé USB** (aucune connexion). La méthode B est la plus sûre pour une machine de secours le jour de la soutenance.

---

## Prérequis (à installer une seule fois sur la nouvelle machine)

1. **Python 3.11 ou plus** — depuis https://www.python.org/downloads/ ou le Microsoft Store.
   - À l'installation python.org : cocher **« Add Python to PATH »**.
   - Vérifier ensuite dans PowerShell : `python --version` → doit afficher `Python 3.11.x` (ou plus).
2. **Git** (méthode A uniquement) — depuis https://git-scm.com/download/win. Vérifier : `git --version`.

---

## Méthode A — via Git (nécessite l'accès au dépôt GitHub)

Coller ligne par ligne dans PowerShell :

```powershell
cd $HOME\Desktop
git clone https://github.com/yvanlenoir10-18/projet-mem.git
cd projet-mem\cuf-pilotage
git checkout claude/install-claude-excel-6MGzv
python -m pip install -r requirements.txt
Copy-Item ..\documents\outils\setup_demo.py .
python setup_demo.py
python run.py
```

- `git clone` demandera peut-être ton identifiant GitHub (le dépôt est privé).
- `setup_demo.py` crée la base de données **et** les données de démonstration (opérateurs Edgar/Messi/Gervé, éventail complet de fiches, prix FOB).
- `python run.py` démarre le serveur. Laisser la fenêtre **ouverte**.

---

## Méthode B — via clé USB (aucune connexion internet)

Sur **ta machine actuelle**, copie tout le dossier `cuf-pilotage` sur une clé USB **avec** son sous-dossier `instance\` (il contient la base de données et donc toutes les données déjà saisies).

Sur la **nouvelle machine**, colle le dossier (ex. sur le Bureau), puis dans PowerShell :

```powershell
cd "$HOME\Desktop\cuf-pilotage"
python -m pip install -r requirements.txt
python run.py
```

- Comme la base de données est déjà dans `instance\`, **pas besoin** de relancer `setup_demo.py` : les données sont là.
- Si tu veux **régénérer** des données fraîches (ou obtenir le dernier éventail de fiches), copie aussi `setup_demo.py` dans `cuf-pilotage` et lance `python setup_demo.py` avant `python run.py`.

---

## Ouvrir l'application dans le navigateur

Au démarrage, PowerShell affiche deux adresses, par exemple :

```
 * Running on http://127.0.0.1:5000        (cette machine)
 * Running on http://192.168.x.x:5000      (autres appareils du même réseau)
```

- **Sur la machine qui fait tourner l'app** : ouvre `http://127.0.0.1:5000`.
- **Depuis un autre appareil (téléphone, PC projecteur) sur le même Wi-Fi** : ouvre l'adresse `http://192.168.x.x:5000` affichée.
- Au premier lancement, **Windows peut demander d'autoriser Python sur le réseau** → cliquer **« Autoriser l'accès »**.

**Comptes de démonstration** (mot de passe `cuf2026`) : `edgar@cuf.cm` (opérateur) · `chef@cuf.cm` · `prod@cuf.cm` · `pdg@cuf.cm` · `admin@cuf.cm`.

---

## Arrêter / relancer

- **Arrêter** : dans la fenêtre PowerShell du serveur, faire `Ctrl + C`.
- **Relancer** (données déjà en place) :
  ```powershell
  cd "$HOME\Desktop\cuf-pilotage"; python run.py
  ```

---

## Dépannage rapide

| Symptôme | Cause | Solution |
|---|---|---|
| `python` n'est pas reconnu | Python pas installé ou pas dans le PATH | Réinstaller Python en cochant « Add to PATH » |
| `py` n'est pas reconnu | Python vient du Microsoft Store | Utiliser `python` (pas `py`) |
| `git` n'est pas reconnu | Git non installé | Installer Git, ou utiliser la méthode B (USB) |
| `ModuleNotFoundError` | Dépendances non installées | `python -m pip install -r requirements.txt` |
| `Address already in use` (port 5000) | Une app tourne déjà | Fermer l'autre fenêtre, ou `Get-NetTCPConnection -LocalPort 5000 \| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }` |
| « Ce site est inaccessible » | Serveur arrêté (fenêtre fermée) | Relancer `python run.py`, garder la fenêtre ouverte |
| Autre appareil ne voit pas l'app | Pare-feu Windows / réseau différent | Autoriser Python au pare-feu ; vérifier même Wi-Fi |
