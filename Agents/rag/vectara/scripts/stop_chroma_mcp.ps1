$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pidFile = Join-Path $projectRoot "data/chroma_mcp.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "No se encontró PID; el servidor no está en ejecución." -ForegroundColor Yellow
    exit 0
}

$serverPid = Get-Content $pidFile | Select-Object -First 1
if (-not $serverPid) {
    Remove-Item $pidFile -Force
    Write-Host "PID vacío; limpiado." -ForegroundColor Yellow
    exit 0
}

$process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item $pidFile -Force
    Write-Host "El proceso $serverPid no existe; nada que detener." -ForegroundColor Yellow
    exit 0
}

Stop-Process -Id $serverPid -Force
Remove-Item $pidFile -Force
Write-Host "Servidor MCP detenido (PID $serverPid)." -ForegroundColor Green
