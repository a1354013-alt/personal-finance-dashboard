$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot 'frontend'
$frontendEnvExample = Join-Path $frontendDir '.env.example'
$frontendEnv = Join-Path $frontendDir '.env'
$packageLock = Join-Path $frontendDir 'package-lock.json'
$nodeModules = Join-Path $frontendDir 'node_modules'

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

Assert-Command node
Assert-Command npm

Ensure-EnvFile -ExamplePath $frontendEnvExample -TargetPath $frontendEnv

Push-Location $frontendDir
try {
  if (-not (Test-Path $nodeModules)) {
    Write-Host 'Installing frontend dependencies...'
    if (Test-Path $packageLock) {
      npm ci
    } else {
      npm install
    }
  } else {
    Write-Host 'Frontend dependencies already present.'
  }
} finally {
  Pop-Location
}
