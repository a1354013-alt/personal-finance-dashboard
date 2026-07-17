$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$venvDir = Join-Path $backendDir '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$backendEnvExample = Join-Path $backendDir '.env.example'
$backendEnv = Join-Path $backendDir '.env'
$requirementsPath = Join-Path $backendDir 'requirements.txt'
$requirementsStamp = Join-Path $venvDir '.requirements.sha256'
$pythonVersionStamp = Join-Path $venvDir '.python-version'

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

function Get-CompatiblePython {
  $candidates = @()
  if (Get-Command py -ErrorAction SilentlyContinue) {
    $pyRuntimes = & py -0p 2>$null
    if ($pyRuntimes -match '-V:3\.12') {
      $candidates += ,@('py', '-3.12')
    }
    if ($pyRuntimes -match '-V:3\.11') {
      $candidates += ,@('py', '-3.11')
    }
  }
  $candidates += ,@('python')

  foreach ($candidate in $candidates) {
    $command = $candidate[0]
    $arguments = @()
    if ($candidate.Count -gt 1) {
      $arguments = $candidate[1..($candidate.Count - 1)]
    }
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
      continue
    }
    $version = & $command @arguments -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ($LASTEXITCODE -eq 0 -and $version -in @('3.11', '3.12')) {
      $executable = & $command @arguments -c "import sys; print(sys.executable)" 2>$null
      if ($LASTEXITCODE -eq 0 -and $executable) {
        return @{ Path = $executable.Trim(); Version = $version.Trim() }
      }
    }
  }

  throw "Unsupported Python runtime. Install Python 3.11 or 3.12 before bootstrapping the backend."
}

Ensure-EnvFile -ExamplePath $backendEnvExample -TargetPath $backendEnv

$compatiblePython = Get-CompatiblePython
$pythonExe = $compatiblePython.Path
$selectedPythonVersion = $compatiblePython.Version

if (Test-Path $venvPython) {
  $venvVersion = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
  if ($LASTEXITCODE -ne 0 -or $venvVersion.Trim() -notin @('3.11', '3.12')) {
    $resolvedVenv = (Resolve-Path $venvDir).Path
    $resolvedBackend = (Resolve-Path $backendDir).Path
    if (-not $resolvedVenv.StartsWith($resolvedBackend, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing to recreate unexpected virtual environment path: $resolvedVenv"
    }
    Write-Host "Recreating backend virtual environment because it uses unsupported Python $($venvVersion.Trim())."
    Remove-Item -LiteralPath $resolvedVenv -Recurse -Force
  } else {
    Write-Host "Using existing backend virtual environment with Python $($venvVersion.Trim())."
  }
}

if (-not (Test-Path $venvPython)) {
  Write-Host "Creating backend virtual environment with Python $selectedPythonVersion..."
  & $pythonExe -m venv $venvDir
}

$pythonVersion = (& $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
if ($pythonVersion -notin @('3.11', '3.12')) {
  throw "Backend virtual environment uses unsupported Python $pythonVersion. Recreate backend\.venv with Python 3.11 or 3.12."
}

$requirementsHash = (Get-FileHash $requirementsPath -Algorithm SHA256).Hash
$stampInput = "$pythonVersion`:$requirementsHash"
$installedHash = if (Test-Path $requirementsStamp) { Get-Content $requirementsStamp -Raw } else { '' }
$installedPythonVersion = if (Test-Path $pythonVersionStamp) { Get-Content $pythonVersionStamp -Raw } else { '' }

if (($stampInput -ne $installedHash.Trim()) -or ($pythonVersion -ne $installedPythonVersion.Trim())) {
  Write-Host 'Installing backend requirements...'
  & $venvPython -m pip install -r $requirementsPath
  if ($LASTEXITCODE -ne 0) {
    throw "Backend dependency installation failed with exit code $LASTEXITCODE."
  }
  Set-Content -Path $requirementsStamp -Value $stampInput
  Set-Content -Path $pythonVersionStamp -Value $pythonVersion
} else {
  Write-Host 'Backend requirements already installed.'
}

Write-Host 'Applying backend migrations...'
Push-Location $backendDir
try {
  & $venvPython -m alembic upgrade head
  if ($LASTEXITCODE -ne 0) {
    throw "Backend migration failed with exit code $LASTEXITCODE."
  }
} finally {
  Pop-Location
}
