$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$venvDir = Join-Path $backendDir '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$backendEnvExample = Join-Path $backendDir '.env.example'
$backendEnv = Join-Path $backendDir '.env'
$requirementsPath = Join-Path $backendDir 'requirements.txt'

function Assert-Command {
  param([Parameter(Mandatory = $true)][string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
  }
}

function Ensure-EnvFile {
  param(
    [Parameter(Mandatory = $true)][string]$ExamplePath,
    [Parameter(Mandatory = $true)][string]$TargetPath
  )

  if ((-not (Test-Path $TargetPath)) -and (Test-Path $ExamplePath)) {
    Copy-Item $ExamplePath $TargetPath
    Write-Host "Created $(Split-Path -Leaf $TargetPath) from $(Split-Path -Leaf $ExamplePath)."
  }
}

Assert-Command python

Ensure-EnvFile -ExamplePath $backendEnvExample -TargetPath $backendEnv

if (-not (Test-Path $venvPython)) {
  Write-Host 'Creating backend virtual environment...'
  python -m venv $venvDir
}

Write-Host 'Installing backend requirements...'
& $venvPython -m pip install -r $requirementsPath

Write-Host 'Applying backend migrations...'
Push-Location $backendDir
try {
  & $venvPython -m alembic upgrade head
} finally {
  Pop-Location
}
