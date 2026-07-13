$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$targets = @(
  'backend/finance.db',
  'backend/playwright-e2e.db',
  'backend/playwright-e2e.db-*',
  'backend/test_smoke.db',
  'backend/*.db',
  'backend/*.db-*',
  'backend/*.db-journal',
  'backend/pytest-cache-files-*',
  'backend/__pycache__',
  'backend/.pytest_cache',
  'frontend/node_modules',
  'frontend/dist',
  'frontend/.vite',
  'frontend/coverage',
  'frontend/playwright-report',
  'frontend/test-results'
)

foreach ($relativePath in $targets) {
  $targetPath = Join-Path $repoRoot $relativePath
  Get-ChildItem -Path $targetPath -Force -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Removed: $relativePath"
  }
}

Write-Host 'Delivery cleanup complete.'
