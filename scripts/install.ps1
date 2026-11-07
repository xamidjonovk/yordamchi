param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$agentProject = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $uvInstaller = Join-Path ([IO.Path]::GetTempPath()) ('hpa-uv-' + [guid]::NewGuid().ToString() + '.ps1')
    Invoke-WebRequest 'https://astral.sh/uv/0.13.6/install.ps1' -OutFile $uvInstaller
    & $uvInstaller
    Remove-Item -LiteralPath $uvInstaller
    $env:PATH = (Join-Path $env:USERPROFILE '.local\bin') + [IO.Path]::PathSeparator + $env:PATH
}
$hermesCommand = Join-Path $env:LOCALAPPDATA 'hermes\bin\hermes.exe'
if (-not (Get-Command hermes -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $hermesCommand)) {
    $hermesInstaller = Join-Path ([IO.Path]::GetTempPath()) ('hpa-hermes-' + [guid]::NewGuid().ToString() + '.ps1')
    Invoke-WebRequest 'https://raw.githubusercontent.com/NousResearch/hermes-agent/bf0203a794a07aac3ff764972ab9087baa4e4f4e/scripts/install.ps1' -OutFile $hermesInstaller
    & $hermesInstaller -Commit 'bf0203a794a07aac3ff764972ab9087baa4e4f4e' -NonInteractive
    Remove-Item -LiteralPath $hermesInstaller
}
Push-Location -LiteralPath $agentProject
try {
    uv sync --frozen --python 3.11 --no-dev --extra calls
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
    if (-not $PrepareOnly) { & (Join-Path $agentProject '.venv\Scripts\hpa.exe') setup }
    else { Write-Host 'Setup skipped. Import your private transfer or run hpa setup manually.' }
} finally { Pop-Location }
