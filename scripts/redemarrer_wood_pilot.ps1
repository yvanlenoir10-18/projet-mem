param(
    [int]$Port = 5000
)

$ErrorActionPreference = "SilentlyContinue"

$repoRoot = Split-Path -Parent $PSScriptRoot
$appDir = Join-Path $repoRoot "cuf-pilotage"
$pythonExe = Join-Path $appDir "venv\Scripts\python.exe"

Write-Host "Arret des anciens serveurs wood_pilot..."

$runPyProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match "python" -and
        $_.CommandLine -match "run\.py" -and
        $_.CommandLine -match [regex]::Escape($appDir)
    }

foreach ($proc in $runPyProcesses) {
    Write-Host " - stop PID $($proc.ProcessId)"
    Stop-Process -Id $proc.ProcessId -Force
}

Start-Sleep -Seconds 1

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen
foreach ($listener in $listeners) {
    $process = Get-Process -Id $listener.OwningProcess
    if ($process -and $process.ProcessName -match "python") {
        Write-Host " - libere port $Port via PID $($listener.OwningProcess)"
        Stop-Process -Id $listener.OwningProcess -Force
    }
}

Start-Sleep -Seconds 2

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERREUR: venv introuvable: $pythonExe"
    exit 1
}

Write-Host "Lancement de wood_pilot..."
$started = Start-Process -FilePath $pythonExe `
    -ArgumentList "run.py" `
    -WorkingDirectory $appDir `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/login" -UseBasicParsing -TimeoutSec 10
    Write-Host "OK: wood_pilot est lance. HTTP $($response.StatusCode)"
    Write-Host "Local: http://127.0.0.1:$Port/login"
    Write-Host "Reseau: http://192.168.1.132:$Port/login"
    Write-Host "PID parent: $($started.Id)"
} catch {
    Write-Host "ATTENTION: serveur lance mais test HTTP non confirme."
    Write-Host $_.Exception.Message
    exit 1
}
