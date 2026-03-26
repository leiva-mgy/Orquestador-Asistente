$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pidFile = Join-Path $projectRoot "data/chroma_mcp.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "Servidor MCP no iniciado." -ForegroundColor Yellow
    exit 0
}

$serverPid = Get-Content $pidFile | Select-Object -First 1
if (-not $serverPid) {
    Write-Host "Archivo PID vacío; considera ejecutar start nuevamente." -ForegroundColor Yellow
    exit 0
}

$process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "Servidor MCP activo (PID $serverPid, $($process.Path))." -ForegroundColor Green
} else {
    Write-Host "Archivo PID encontrado pero el proceso $serverPid no existe." -ForegroundColor Yellow
}
