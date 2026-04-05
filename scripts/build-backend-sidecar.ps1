$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$distDir = Join-Path $backendDir "dist"

Push-Location $backendDir
try {
  py -m PyInstaller `
    --noconfirm `
    --clean `
    --name backend-sidecar `
    --onefile `
    --hidden-import app.models `
    --collect-all pydantic `
    --collect-all pydantic_settings `
    run_desktop.py
}
finally {
  Pop-Location
}

Write-Host "Backend sidecar built at $distDir"
