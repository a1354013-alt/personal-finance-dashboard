$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'
$venvDir = Join-Path $backendDir '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'

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

function Test-PortInUse {
  param([Parameter(Mandatory = $true)][int]$Port)

  if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
  }

  $listener = $null
  try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    $listener.Start()
    return $false
  } catch {
    return $true
  } finally {
    if ($listener) {
      $listener.Stop()
    }
  }
}

function Start-DevWindow {
  param(
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory,
    [Parameter(Mandatory = $true)][string]$Command
  )

  $escapedTitle = $Title.Replace("'", "''")
  $escapedDirectory = $WorkingDirectory.Replace("'", "''")
  $script = "Set-Location '$escapedDirectory'; `$Host.UI.RawUI.WindowTitle = '$escapedTitle'; $Command"
  Start-Process powershell.exe -ArgumentList @('-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $script)
}

Write-Host 'Checking prerequisites...'
Assert-Command python
Assert-Command node
Assert-Command npm

Ensure-EnvFile -ExamplePath (Join-Path $backendDir '.env.example') -TargetPath (Join-Path $backendDir '.env')
Ensure-EnvFile -ExamplePath (Join-Path $frontendDir '.env.example') -TargetPath (Join-Path $frontendDir '.env')

if (-not (Test-Path $venvPython)) {
  Write-Host 'Creating backend virtual environment...'
  python -m venv $venvDir
}

Write-Host 'Installing backend requirements...'
& $venvPython -m pip install -r (Join-Path $backendDir 'requirements.txt')

Write-Host 'Applying backend migrations...'
Push-Location $backendDir
try {
  & $venvPython -m alembic upgrade head
} finally {
  Pop-Location
}

Write-Host 'Installing frontend dependencies...'
Push-Location $frontendDir
try {
  if (Test-Path (Join-Path $frontendDir 'package-lock.json')) {
    npm ci
  } else {
    npm install
  }
} finally {
  Pop-Location
}

if (Test-PortInUse -Port 8000) {
  throw 'Port 8000 is already in use. Please close the existing backend server or change the port.'
}

if (Test-PortInUse -Port 5173) {
  throw 'Port 5173 is already in use. Please close the existing frontend server or change the port.'
}

Write-Host 'Starting backend and frontend dev servers...'
Start-DevWindow -Title 'Personal Finance API' -WorkingDirectory $backendDir -Command '.\.venv\Scripts\python.exe -m uvicorn main:app --reload'
Start-DevWindow -Title 'Personal Finance Frontend' -WorkingDirectory $frontendDir -Command 'npm run dev'

Write-Host ''
Write-Host 'Backend:  http://localhost:8000'
Write-Host 'Swagger:  http://localhost:8000/docs'
Write-Host 'Frontend: http://localhost:5173'
Write-Host ''
Write-Host 'Close the opened PowerShell windows to stop the dev servers.'
