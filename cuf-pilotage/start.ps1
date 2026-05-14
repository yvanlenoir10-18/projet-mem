# Script de démarrage CUF Pilotage — Windows
# Usage : clic droit sur start.ps1 > "Exécuter avec PowerShell"
# OU dans PowerShell : .\start.ps1

Write-Host "=== CUF Pilotage - Démarrage ===" -ForegroundColor Green
Write-Host ""
Write-Host " Pour activer le module IA (recommandations P14) :" -ForegroundColor Gray
Write-Host "   1. Créez un fichier .env dans ce dossier" -ForegroundColor Gray
Write-Host "   2. Ajoutez UNE des clés suivantes :" -ForegroundColor Gray
Write-Host "        GROQ_API_KEY=gsk_xxxxx   (console.groq.com — GRATUIT, recommandé)" -ForegroundColor Green
Write-Host "        ANTHROPIC_API_KEY=sk-ant-xxxxx   (console.anthropic.com — payant)" -ForegroundColor Gray
Write-Host "   + optionnel : TAVILY_API_KEY=tvly-xxxxx  (app.tavily.com — recherche web)" -ForegroundColor Gray
Write-Host "   Sans clé IA : l'application fonctionne, le bouton IA est désactivé." -ForegroundColor Gray
Write-Host ""

# 1. Aller dans le bon dossier (là où ce script se trouve)
Set-Location $PSScriptRoot

# 2. Récupérer les dernières modifications depuis GitHub
Write-Host "Mise à jour du code..." -ForegroundColor Yellow
git pull origin claude/install-claude-excel-6MGzv

# 2b. Charger les variables d'environnement depuis .env si le fichier existe
#     Requis pour le module IA (Recommandations P14) : ANTHROPIC_API_KEY et TAVILY_API_KEY
if (Test-Path ".env") {
    Write-Host "Chargement des variables depuis .env..." -ForegroundColor Yellow
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $key   = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Host "Info : aucun fichier .env trouvé. L'enrichissement IA sera désactivé." -ForegroundColor Gray
    Write-Host "       Copiez .env.example → .env et renseignez vos clés pour l'activer." -ForegroundColor Gray
}

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
