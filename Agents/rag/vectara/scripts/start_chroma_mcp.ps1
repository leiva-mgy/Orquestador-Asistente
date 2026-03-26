Param(
    [string]$BindHost,
    [int]$Port
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pidFile = Join-Path $projectRoot "data/chroma_mcp.pid"

if (Test-Path $pidFile) {
    $existingPid = Get-Content $pidFile | Select-Object -First 1
    if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
        Write-Host "El servidor ya está en ejecución (PID $existingPid). Usa stop_chroma_mcp.ps1 primero." -ForegroundColor Yellow
        exit 0
    }
    Remove-Item $pidFile -Force
}

$python = Join-Path $projectRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$arguments = @("scripts/chroma_mcp.py")
if ($BindHost) { $arguments += "--host"; $arguments += $BindHost }
if ($Port) { $arguments += "--port"; $arguments += $Port }

$process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
$process.Id | Set-Content -Path $pidFile
Write-Host "Servidor MCP iniciado en segundo plano (PID $($process.Id))." -ForegroundColor Green
