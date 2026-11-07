param([string]$InstanceHome = $env:HPA_HOME, [switch]$Launch)
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$pythonwPath = Join-Path $repositoryRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Avval scripts/install.ps1 orqali dasturni ornating.' }
& $pythonPath -c 'import webview'
if ($LASTEXITCODE -ne 0) {
    Push-Location $repositoryRoot
    try { uv sync --frozen --extra calls --extra desktop --extra semantic; if ($LASTEXITCODE -ne 0) { throw 'Desktop kutubxonasi ornatilmadi.' } }
    finally { Pop-Location }
}
if (-not $InstanceHome) { $InstanceHome = (& $pythonPath -c 'from hermes_personal_agent.voice_common import APP_HOME; print(APP_HOME)').Trim() }
$resolvedHome = [IO.Path]::GetFullPath($InstanceHome)
if (-not (Test-Path -LiteralPath (Join-Path $resolvedHome 'config.json'))) { throw 'Tanlangan nusxaning config.json fayli topilmadi.' }
function Quote-Vbs([string]$value) { return '"' + $value.Replace('"','""') + '"' }
$command = '"' + $pythonwPath + '" -m hermes_personal_agent.cli desktop'
$launcher = Join-Path $resolvedHome 'desktop.vbs'
$script = 'Set shell = CreateObject("WScript.Shell")' + "`r`n"
$script += 'shell.Environment("PROCESS")("HPA_HOME") = ' + (Quote-Vbs $resolvedHome) + "`r`n"
$script += 'shell.CurrentDirectory = ' + (Quote-Vbs $repositoryRoot) + "`r`n"
$script += 'shell.Run ' + (Quote-Vbs $command) + ', 0, False' + "`r`n"
[IO.File]::WriteAllText($launcher, $script, [Text.UTF8Encoding]::new($false))
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcutPath = Join-Path $desktopPath 'Shaxsiy yordamchi.lnk'
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments = '"' + $launcher + '"'
$shortcut.WorkingDirectory = $repositoryRoot
$shortcut.Description = 'Yordamchi: local va VPS boshqaruvi, vazifalar, kalendar va xotira'
$shortcut.IconLocation = (Join-Path $repositoryRoot 'src\hermes_personal_agent\desktop\app.ico') + ',0'
$shortcut.Save()
# Only the two shortcuts explicitly replaced by the owner are removed.
foreach ($name in @('Yordamchini ishga tushirish.lnk', 'Yordamchini toxtatish.lnk')) {
    $oldShortcut = Join-Path $desktopPath $name
    if (Test-Path -LiteralPath $oldShortcut) { Remove-Item -LiteralPath $oldShortcut }
}
Write-Output "Desktop ilova tayyor: $shortcutPath"
if ($Launch) { Start-Process -FilePath $shortcut.TargetPath -ArgumentList $shortcut.Arguments -WindowStyle Hidden }
