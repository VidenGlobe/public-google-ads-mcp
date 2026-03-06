[CmdletBinding()]
param(
    [switch]$SkipToolInstall,
    [switch]$SkipSync,
    [switch]$SkipEnvPrompt
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

    Write-Host "Installing $DisplayName with winget..."
    & winget install --id $PackageId -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget failed while installing $DisplayName."
    }
}

function Ensure-Command {
    param(
        [string]$Name,
        [string]$PackageId,
        [string]$DisplayName
    )

    if (Test-CommandInstalled $Name) {
        Write-Host "$DisplayName is already installed."
        return
    }

    if ($SkipToolInstall) {
        throw "$DisplayName is not installed. Re-run without -SkipToolInstall or install it manually."
    }

    Install-WithWinget -PackageId $PackageId -DisplayName $DisplayName
    Refresh-Path

    if (-not (Test-CommandInstalled $Name)) {
        throw "$DisplayName was installed, but the command is still not available in this terminal. Close PowerShell, reopen it, and run the script again."
    }
}

function Convert-ToClaudePath {
    param([string]$PathValue)
    return ($PathValue -replace "\\", "/")
}

if ($env:OS -ne "Windows_NT") {
    throw "This script is for Windows only."
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvExamplePath = Join-Path $RepoRoot ".env.example"
$EnvPath = Join-Path $RepoRoot ".env"
$ClaudeDir = Join-Path $env:APPDATA "Claude"
$ClaudeConfigPath = Join-Path $ClaudeDir "claude_desktop_config.json"

Write-Step "Checking required tools"
Ensure-Command -Name "git" -PackageId "Git.Git" -DisplayName "Git"
Ensure-Command -Name "uv" -PackageId "astral-sh.uv" -DisplayName "uv"

$uvCommand = Get-Command "uv" -ErrorAction Stop
$uvPath = $uvCommand.Source

Write-Step "Preparing .env"
if (-not (Test-Path $EnvPath)) {
    Copy-Item $EnvExamplePath $EnvPath
    Write-Host "Created .env from .env.example"
}
else {
    Write-Host ".env already exists."
}

$envContents = Get-Content -Path $EnvPath -Raw
$needsEnvEdit = $envContents -match "your-developer-token|your-client-id|your-client-secret|your-refresh-token"

if (-not $SkipEnvPrompt -and $needsEnvEdit) {
    Write-Host "Your .env still contains placeholder values. Notepad will open now."
    Start-Process notepad.exe $EnvPath
    Read-Host "Fill in your Google Ads credentials, save the file, then press Enter here"
}

Write-Step "Installing project dependencies"
Push-Location $RepoRoot
try {
    if (-not $SkipSync) {
        & $uvPath sync
        if ($LASTEXITCODE -ne 0) {
            throw "uv sync failed."
        }
    }
    else {
        Write-Host "Skipped uv sync."
    }
}
finally {
    Pop-Location
}

Write-Step "Updating Claude Desktop config"
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

$configObject = [pscustomobject]@{}
if (Test-Path $ClaudeConfigPath) {
    $rawConfig = Get-Content -Path $ClaudeConfigPath -Raw
    if (-not [string]::IsNullOrWhiteSpace($rawConfig)) {
        try {
            $configObject = $rawConfig | ConvertFrom-Json
        }
        catch {
            throw "Existing Claude config is not valid JSON: $ClaudeConfigPath"
        }
    }

    $backupPath = "$ClaudeConfigPath.bak"
    Copy-Item $ClaudeConfigPath $backupPath -Force
    Write-Host "Backup created: $backupPath"
}

if ($null -eq $configObject) {
    $configObject = [pscustomobject]@{}
}

if (-not (Get-Member -InputObject $configObject -Name "mcpServers" -MemberType NoteProperty -ErrorAction SilentlyContinue)) {
    $configObject | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([pscustomobject]@{})
}
elseif ($null -eq $configObject.mcpServers) {
    $configObject.mcpServers = [pscustomobject]@{}
}

$serverConfig = [pscustomobject]@{
    command = (Convert-ToClaudePath $uvPath)
    args = @(
        "--directory",
        (Convert-ToClaudePath $RepoRoot),
        "run",
        "google-ads-mcp"
    )
}

$configObject.mcpServers | Add-Member -NotePropertyName "google-ads" -NotePropertyValue $serverConfig -Force

$json = $configObject | ConvertTo-Json -Depth 10
Set-Content -Path $ClaudeConfigPath -Value $json -Encoding UTF8

Write-Step "Done"
Write-Host "Claude Desktop config updated: $ClaudeConfigPath" -ForegroundColor Green
Write-Host "Repo path: $RepoRoot"
Write-Host "uv path: $uvPath"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. If you have not filled in .env yet, open it and add your Google Ads credentials."
Write-Host "2. Fully quit Claude Desktop and open it again."
Write-Host "3. In Claude Desktop, look for the tools icon and test: Show me all campaigns for customer 1234567890"
