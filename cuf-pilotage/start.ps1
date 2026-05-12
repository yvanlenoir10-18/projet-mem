# Script de démarrage CUF Pilotage — Windows
# Usage : clic droit sur start.ps1 > "Exécuter avec PowerShell"
# OU dans PowerShell : .\start.ps1

Write-Host "=== CUF Pilotage - Démarrage ===" -ForegroundColor Green

# 1. Aller dans le bon dossier (là où ce script se trouve)
Set-Location $PSScriptRoot

# 2. Récupérer les dernières modifications depuis GitHub
Write-Host "Mise à jour du code..." -ForegroundColor Yellow
git pull origin claude/install-claude-excel-6MGzv

# 3. Créer le dossier instance/ si absent (SQLite ne peut pas créer cuf.db sans ce dossier)
if (-not (Test-Path "instance")) {
    Write-Host "Création du dossier instance/..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "instance" | Out-Null
}

# 4. Créer l'environnement virtuel si absent
if (-not (Test-Path "venv")) {
    Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
    python -m venv venv
}

# 5. Activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 6. Installer les dépendances
Write-Host "Installation des dépendances..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# 7. Lancer Flask
Write-Host ""
Write-Host "Lancement de Flask sur http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Ouvre ce lien dans ton navigateur : http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Appuyez sur CTRL+C pour arrêter." -ForegroundColor Gray
python run.py
