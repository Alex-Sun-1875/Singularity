param([int]$Port=7469,[switch]$Build)
$ErrorActionPreference='Stop'
$target=Join-Path $PSScriptRoot 'build/concept-2d'
if($Build -or !(Test-Path -LiteralPath (Join-Path $target 'index.html'))){& (Join-Path $PSScriptRoot 'Build-Local.ps1') -Platform web-mobile -OutputName concept-2d}
$listener=Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if(!$listener){
 $server=Start-Process -FilePath 'python' -ArgumentList @(('"'+(Join-Path $PSScriptRoot 'tools/serve-web.py')+'"'),'--port',"$Port",'--directory',('"'+$target+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'temp/concept-2d-server-out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'temp/concept-2d-server-err.log')
 Write-Output ('Concept 2D server PID '+$server.Id)
}
Write-Output ('3D hero + painted world: http://127.0.0.1:'+$Port+'/?view=2d&player=3d')
