param([switch]$PrepareOnly)
# Compatibility entry: all components are installed by one unified installer.
& (Join-Path $PSScriptRoot 'install.ps1') -PrepareOnly:$PrepareOnly
exit $LASTEXITCODE
