$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$targets = @(
  'backend/finance.db',
  'backend/test_smoke.db',
  'backend/__pycache__',
  'backend/.pytest_cache',
  'frontend/node_modules',
  'frontend/dist',
  'frontend/.vite'
)

foreach ($relativePath in $targets) {
  $targetPath = Join-Path $repoRoot $relativePath
  if (Test-Path -LiteralPath $targetPath) {
    Remove-Item -LiteralPath $targetPath -Recurse -Force
    Write-Host "Removed: $relativePath"
  }
}

Write-Host 'Delivery cleanup complete.'
