$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'

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

Assert-Command python
Assert-Command npm

Push-Location $backendDir
try {
  Invoke-Step -Label 'backend: python -m compileall .' -Command { python -m compileall . }
  Invoke-Step -Label 'backend: python -m alembic upgrade head' -Command { python -m alembic upgrade head }
  Invoke-Step -Label 'backend: python -m pytest -q' -Command { python -m pytest -q }
  Invoke-Step -Label 'backend: python seed_data.py --reset' -Command { python seed_data.py --reset }
} finally {
  Pop-Location
}

Push-Location $frontendDir
try {
  Invoke-Step -Label 'frontend: npm ci' -Command { npm ci }
  Invoke-Step -Label 'frontend: npm run lint' -Command { npm run lint }
  Invoke-Step -Label 'frontend: npm run test:run' -Command { npm run test:run }
  Invoke-Step -Label 'frontend: npm run build' -Command { npm run build }
  Invoke-Step -Label 'frontend: npm audit --audit-level=moderate' -Command { npm audit --audit-level=moderate }
} finally {
  Pop-Location
}
