$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot 'frontend'
$frontendEnvExample = Join-Path $frontendDir '.env.example'
$frontendEnv = Join-Path $frontendDir '.env'
$packageLock = Join-Path $frontendDir 'package-lock.json'
$packageJson = Join-Path $frontendDir 'package.json'
$nodeModules = Join-Path $frontendDir 'node_modules'
$dependenciesStamp = Join-Path $nodeModules '.package-lock.sha256'

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
  node .\scripts\check-node-version.mjs
  if ($LASTEXITCODE -ne 0) {
    throw "Frontend Node.js version check failed with exit code $LASTEXITCODE."
  }

  $manifestHashInput = if (Test-Path $packageLock) { "$((Get-FileHash $packageLock -Algorithm SHA256).Hash):$((Get-FileHash $packageJson -Algorithm SHA256).Hash)" } else { (Get-FileHash $packageJson -Algorithm SHA256).Hash }
  $installedHash = if (Test-Path $dependenciesStamp) { Get-Content $dependenciesStamp -Raw } else { '' }

  if ((-not (Test-Path $nodeModules)) -or ($manifestHashInput -ne $installedHash.Trim())) {
    Write-Host 'Installing frontend dependencies...'
    if (Test-Path $packageLock) {
      npm ci
    } else {
      npm install
    }
    if ($LASTEXITCODE -ne 0) {
      throw "Frontend dependency installation failed with exit code $LASTEXITCODE."
    }
    Set-Content -Path $dependenciesStamp -Value $manifestHashInput
  } else {
    Write-Host 'Frontend dependencies already present.'
  }
} finally {
  Pop-Location
}
