# Generate a Google Ads refresh token and save it to .env.
# This is a thin wrapper around scripts/get_refresh_token.py.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\generate-refresh-token-windows.ps1
#
[CmdletBinding()]
param(
    [string]$EnvPath
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$uvCommand = Get-Command "uv" -ErrorAction SilentlyContinue
if ($null -eq $uvCommand) {
    Write-Host "ERROR: uv is not installed." -ForegroundColor Red
    Write-Host "Install it: winget install --id astral-sh.uv -e"
    exit 1
}

$scriptArgs = @("run", "scripts/get_refresh_token.py")
if (-not [string]::IsNullOrWhiteSpace($EnvPath)) {
    $scriptArgs += "--env-file"
    $scriptArgs += $EnvPath
}

Push-Location $repoRoot
try {
    & $uvCommand.Source @scriptArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
