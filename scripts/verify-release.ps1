$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'
$backendPython = Join-Path $backendDir '.venv\Scripts\python.exe'

function Assert-Command {
  param([Parameter(Mandatory = $true)][string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
  }
}

function Invoke-Step {
  param(
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][scriptblock]$Command
  )

  Write-Host "==> $Label"
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "Step failed: $Label (exit code $LASTEXITCODE)"
  }
}

Assert-Command npm

Invoke-Step -Label 'bootstrap: backend virtual environment' -Command { & (Join-Path $PSScriptRoot 'bootstrap-backend.ps1') }
if (-not (Test-Path $backendPython)) {
  throw "Expected backend virtual environment Python at $backendPython."
}

Push-Location $backendDir
try {
  Invoke-Step -Label 'backend: python -m compileall .' -Command { & $backendPython -m compileall . }
  Invoke-Step -Label 'backend: python -m alembic upgrade head' -Command { & $backendPython -m alembic upgrade head }
  Invoke-Step -Label 'backend: python -m alembic check' -Command { & $backendPython -m alembic check }
  Invoke-Step -Label 'backend: python -m pytest -q' -Command { & $backendPython -m pytest -q }
  Invoke-Step -Label 'backend: python -m pip check' -Command { & $backendPython -m pip check }
  Invoke-Step -Label 'backend: python seed_data.py --reset' -Command { & $backendPython seed_data.py --reset }
} finally {
  Pop-Location
}

Push-Location $frontendDir
try {
  Invoke-Step -Label 'frontend: npm run check:node' -Command { npm run check:node }
  Invoke-Step -Label 'frontend: npm ci' -Command { npm ci }
  Invoke-Step -Label 'frontend: npm run lint' -Command { npm run lint }
  Invoke-Step -Label 'frontend: npm run test:run' -Command { npm run test:run }
  Invoke-Step -Label 'frontend: npm run build' -Command { npm run build }
  Invoke-Step -Label 'frontend: npm audit --audit-level=moderate' -Command { npm audit --audit-level=moderate }
  Invoke-Step -Label 'frontend: npm run test:e2e-config' -Command { npm run test:e2e-config }
  Invoke-Step -Label 'frontend: npm run e2e:seeded' -Command { npm run e2e:seeded }
} finally {
  Pop-Location
}
