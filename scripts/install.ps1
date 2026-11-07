param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$agentProject = Split-Path -Parent $PSScriptRoot
Write-Host "1/3: Python va barcha kerakli kutubxonalar tayyorlanmoqda. Oynani yopmang."
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $uvInstaller = Join-Path ([IO.Path]::GetTempPath()) ('hpa-uv-' + [guid]::NewGuid().ToString() + '.ps1')
    Invoke-WebRequest 'https://astral.sh/uv/0.13.6/install.ps1' -OutFile $uvInstaller
    & $uvInstaller
    Remove-Item -LiteralPath $uvInstaller
    $env:PATH = (Join-Path $env:USERPROFILE '.local\bin') + [IO.Path]::PathSeparator + $env:PATH
}
Push-Location -LiteralPath $agentProject
try {
    uv sync --frozen --python 3.11 --no-dev --extra calls
    if ($LASTEXITCODE -ne 0) { throw "Kutubxonalar o'rnatilmadi. Internet va disk joyini tekshiring." }
    $agentPython = Join-Path $agentProject '.venv\Scripts\python.exe'
    $hermesProfile = (& $agentPython -c 'from hermes_personal_agent.voice_common import HERMES_HOME; print(HERMES_HOME)').Trim()
    if ($LASTEXITCODE -ne 0 -or -not $hermesProfile) { throw "Shaxsiy papkani tayyorlab bo'lmadi." }
    $hermesCommand = Join-Path $hermesProfile 'bin\hermes.exe'
    $env:HERMES_HOME = $hermesProfile
    Write-Host "2/3: Hermes shaxsiy nusxangiz uchun avtomatik o'rnatilmoqda. Bu bir necha daqiqa olishi mumkin."
    $hermesHealthy = $false
    if (Test-Path -LiteralPath $hermesCommand) {
        & $agentPython (Join-Path $PSScriptRoot 'check-hermes.py') $hermesCommand
        $hermesHealthy = $LASTEXITCODE -eq 0
    }
    if (-not $hermesHealthy) {
        $hermesInstaller = Join-Path ([IO.Path]::GetTempPath()) ('hpa-hermes-' + [guid]::NewGuid().ToString() + '.ps1')
        try {
            Invoke-WebRequest 'https://raw.githubusercontent.com/NousResearch/hermes-agent/bf0203a794a07aac3ff764972ab9087baa4e4f4e/scripts/install.ps1' -OutFile $hermesInstaller
            & $hermesInstaller -Commit 'bf0203a794a07aac3ff764972ab9087baa4e4f4e' -HermesHome $hermesProfile -InstallDir (Join-Path $hermesProfile 'hermes-agent') -NonInteractive
            if ($LASTEXITCODE -ne 0) { throw "Hermes o'rnatilmadi. Internetni tekshirib install.cmd ni qayta oching." }
        } finally { if (Test-Path -LiteralPath $hermesInstaller) { Remove-Item -LiteralPath $hermesInstaller } }
    }
    if (-not (Test-Path -LiteralPath $hermesCommand)) { throw "Hermes topilmadi. Installer oynasidagi xatoni tekshiring." }
    & $agentPython (Join-Path $PSScriptRoot 'check-hermes.py') $hermesCommand
    if ($LASTEXITCODE -ne 0) { throw "Hermes muhiti tayyor bo'lmadi. Internetni tekshiring va install.cmd ni qayta oching." }
    $env:HERMES_BIN = $hermesCommand
    $env:PATH = (Join-Path $hermesProfile 'bin') + [IO.Path]::PathSeparator + $env:PATH
    & $agentPython -c "import os; from hermes_personal_agent.voice_common import save_config; save_config({'hermes_bin':os.environ['HERMES_BIN'],'hermes_home':os.environ['HERMES_HOME']})"
    if ($LASTEXITCODE -ne 0) { throw "Hermes manzilini saqlab bo'lmadi." }
    if (-not $PrepareOnly) {
        Write-Host "3/3: O'zbekcha sozlash ustasi brauzerda ochiladi. Keyingi qadamlarni o'sha yerda bajaring."
        & (Join-Path $agentProject '.venv\Scripts\hpa.exe') web --setup
    } else { Write-Host "Tayyor. Sozlash uchun start-web.cmd faylini oching va Sozlash ustasiga o'ting." }
} finally { Pop-Location }
