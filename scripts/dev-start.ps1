$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'
$venvPython = Join-Path $backendDir '.venv\Scripts\python.exe'

function Assert-Command {
  param([Parameter(Mandatory = $true)][string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
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

Write-Host 'Preparing backend...'
& (Join-Path $PSScriptRoot 'bootstrap-backend.ps1')
if ($LASTEXITCODE -ne 0) {
  throw "Backend bootstrap failed with exit code $LASTEXITCODE."
}

Write-Host 'Preparing frontend...'
& (Join-Path $PSScriptRoot 'bootstrap-frontend.ps1')
if ($LASTEXITCODE -ne 0) {
  throw "Frontend bootstrap failed with exit code $LASTEXITCODE."
}

if (Test-PortInUse -Port 8000) {
  throw 'Port 8000 is already in use. Please close the existing backend server or change the port.'
}

if (Test-PortInUse -Port 5173) {
  throw 'Port 5173 is already in use. Please close the existing frontend server or change the port.'
}

Write-Host 'Starting backend and frontend dev servers...'
Start-DevWindow -Title 'Personal Finance API' -WorkingDirectory $backendDir -Command '.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000'
Start-DevWindow -Title 'Personal Finance Frontend' -WorkingDirectory $frontendDir -Command 'npm run dev -- --host 127.0.0.1 --port 5173'
Start-Process 'http://127.0.0.1:5173'

Write-Host ''
Write-Host 'Backend:  http://127.0.0.1:8000'
Write-Host 'Swagger:  http://127.0.0.1:8000/docs'
Write-Host 'Frontend: http://127.0.0.1:5173'
Write-Host ''
Write-Host 'Close the opened PowerShell windows to stop the dev servers.'
