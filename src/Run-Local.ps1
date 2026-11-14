param([int]$Width=1280,[int]$Height=720)
$ErrorActionPreference='Stop'
$runtime=Join-Path $PSScriptRoot '.runtime/UrhoXRuntime.exe'
if (!(Test-Path -LiteralPath $runtime)) { & (Join-Path $PSScriptRoot 'Setup-Local.ps1') }
# This is the interactive game requested by the user; its window is intentional.
Start-Process -FilePath $runtime -WorkingDirectory (Split-Path $runtime) -ArgumentList @('main.lua',"-tapcode_dir=`"$PSScriptRoot`"",'-tool_mode','-w',"-width=$Width","-height=$Height") | Out-Null
