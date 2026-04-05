$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"
$tauriDir = Join-Path $repoRoot "src-tauri"

& "$PSScriptRoot\\build-backend-sidecar.ps1"

Push-Location $frontendDir
try {
  npm.cmd run build
}
finally {
  Pop-Location
}

Push-Location $tauriDir
try {
  cargo tauri build
}
finally {
  Pop-Location
}
