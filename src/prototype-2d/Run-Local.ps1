param([int]$Port=7468)
$ErrorActionPreference='Stop'
& node (Join-Path $PSScriptRoot 'build.cjs')
if($LASTEXITCODE -ne 0){throw '2D prototype build failed.'}
$listener=Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if($listener){Write-Output ('2D prototype: http://127.0.0.1:'+$Port+'/');exit 0}
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../cocos'))
$server=Start-Process -FilePath 'python' -ArgumentList @(('"'+(Join-Path $project 'tools/serve-web.py')+'"'),'--port',"$Port",'--directory',('"'+$PSScriptRoot+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'evidence/server-out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'evidence/server-err.log')
Write-Output ('2D prototype: http://127.0.0.1:'+$Port+'/ (PID '+$server.Id+')')
