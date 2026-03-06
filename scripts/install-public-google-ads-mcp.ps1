[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/VidenGlobe/public-google-ads-mcp",
    [string]$InstallDir = (Join-Path $HOME "google-ads-mcp")
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-CommandInstalled {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $combined = @($machinePath, $userPath, $env:Path) -join ";"
    $env:Path = $combined
}

function Install-WithWinget {
    param(
        [string]$PackageId,
        [string]$DisplayName
    )

    if (-not (Test-CommandInstalled "winget")) {
        throw "winget is not available. Install $DisplayName manually and run this script again."
    }

    & winget install --id $PackageId -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget failed while installing $DisplayName."
    }
}

if ($env:OS -ne "Windows_NT") {
    throw "This script is for Windows only."
}

Write-Step "Checking required tools"
if (-not (Test-CommandInstalled "git")) {
    Install-WithWinget -PackageId "Git.Git" -DisplayName "Git"
    Refresh-Path
}

if (-not (Test-CommandInstalled "git")) {
    throw "Git is not available in this terminal. Close PowerShell, reopen it, and run the script again."
}

if (-not (Test-Path $InstallDir)) {
    Write-Step "Cloning repository"
    & git clone $RepoUrl $InstallDir
    if ($LASTEXITCODE -ne 0) {
        throw "git clone failed."
    }
}
else {
    Write-Step "Updating repository"
    Push-Location $InstallDir
    try {
        & git pull
        if ($LASTEXITCODE -ne 0) {
            throw "git pull failed."
        }
    }
    finally {
        Pop-Location
    }
}

$setupScript = Join-Path $InstallDir "scripts\setup-windows-claude-desktop.ps1"
if (-not (Test-Path $setupScript)) {
    throw "Setup script not found: $setupScript"
}

Write-Step "Running Windows Claude Desktop setup"
& powershell -ExecutionPolicy Bypass -File $setupScript
if ($LASTEXITCODE -ne 0) {
    throw "Windows setup script failed."
}
