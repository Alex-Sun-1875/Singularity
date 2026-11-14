$ErrorActionPreference='Stop'
& python (Join-Path $PSScriptRoot '.cli/install-urhox-runtime.py') --platform win32 --dest (Join-Path $PSScriptRoot '.runtime')
if ($LASTEXITCODE -ne 0) { throw 'Runtime installation failed.' }
foreach($relative in @('ResCache','Data/LuaScripts','Data/Fonts','CoreData','Res/Fonts')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot ".runtime/$relative") | Out-Null
}
$font=Join-Path $PSScriptRoot '.runtime/Res/Fonts/MiSans-Regular.ttf'
if (!(Test-Path -LiteralPath $font)) {
    $windowsFont=Join-Path $env:WINDIR 'Fonts/msyh.ttc'
    if (!(Test-Path -LiteralPath $windowsFont)) { throw 'A local Chinese font is required.' }
    Copy-Item -LiteralPath $windowsFont -Destination $font
}
Write-Output 'Local runtime ready. No login or cloud project required.'
