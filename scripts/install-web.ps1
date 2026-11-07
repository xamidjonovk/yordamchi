param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $installer = Join-Path ([IO.Path]::GetTempPath()) ('hpa-uv-' + [guid]::NewGuid().ToString() + '.ps1')
    Invoke-WebRequest 'https://astral.sh/uv/0.13.6/install.ps1' -OutFile $installer
    & $installer
    Remove-Item -LiteralPath $installer
    $env:PATH = (Join-Path $env:USERPROFILE '.local\bin') + [IO.Path]::PathSeparator + $env:PATH
}
Push-Location -LiteralPath $project
try {
    uv sync --frozen --python 3.11 --no-dev
    if ($LASTEXITCODE -ne 0) { throw 'Ornatish tugamadi. Internet va disk joyini tekshiring.' }
    if (-not $PrepareOnly) { & (Join-Path $project '.venv\Scripts\hpa.exe') web }
} finally { Pop-Location }
