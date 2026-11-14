param([int]$Port=7458,[switch]$Build,[ValidateSet('web-mobile','web-desktop')][string]$Platform='web-mobile')
$ErrorActionPreference='Stop'
$project=$PSScriptRoot
$buildDir=Join-Path $project ('build/'+$Platform)
if($Build -or !(Test-Path -LiteralPath (Join-Path $buildDir 'index.html'))){& (Join-Path $project 'Build-Local.ps1') -Platform $Platform}
$listener=Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if($listener){Write-Output ('A local server is already listening at http://127.0.0.1:'+$Port+'/');exit 0}
$temp=Join-Path $project 'temp';New-Item -ItemType Directory -Force -Path $temp | Out-Null
$server=Start-Process -FilePath 'python' -ArgumentList @(('"'+(Join-Path $project 'tools/serve-web.py')+'"'),'--port',"$Port",'--directory',('"'+$buildDir+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $temp 'web-server-out.log') -RedirectStandardError (Join-Path $temp 'web-server-err.log')
Write-Output ('Local game: http://127.0.0.1:'+$Port+'/ (PID '+$server.Id+')')
