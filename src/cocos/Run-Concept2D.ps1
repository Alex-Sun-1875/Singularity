param([Parameter(Position=0)][ValidateSet('dev','test')][string]$Profile='test',[ValidateRange(0,65535)][int]$Port=0,[switch]$Build)
$ErrorActionPreference='Stop'
$Profile=$Profile.ToLowerInvariant()
if(!$Port){$Port=if($Profile -eq 'dev'){7470}else{7469}}
$outputName=if($Profile -eq 'dev'){'concept-2d-dev'}else{'concept-2d'}
$target=Join-Path $PSScriptRoot ('build/'+$outputName)
$manifestPath=Join-Path $target 'local-preview.json'
# Hash text inputs because Creator can touch unchanged settings and import metadata.
# Large binary art uses file metadata; BuildProfile is verified in the output.
function Get-PreviewFingerprint {
 $inputs=@(foreach($directory in @('assets','settings','build-templates','tools')){
  Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot $directory) -File -Recurse | Where-Object {$_.FullName -notmatch '[\\/]__pycache__[\\/]' -and $_.FullName -ne (Join-Path $PSScriptRoot 'assets/scripts/shared/BuildProfile.ts')}
 })
 $inputs+=Get-Item -LiteralPath @((Join-Path $PSScriptRoot '../../package.json'),(Join-Path $PSScriptRoot 'Build-Local.ps1'),(Join-Path $PSScriptRoot 'Run-Concept2D.ps1'),(Join-Path $PSScriptRoot 'release/taptap.json'),(Join-Path $PSScriptRoot 'release/taptap-project.json'),(Join-Path $PSScriptRoot 'release/taptap-auth.json'))
 $textExtensions=@('.ts','.json','.meta','.ps1','.py','.cjs','.js','.mjs','.html','.scene','.prefab','.effect','.glsl','.txt','.yaml','.yml','.xml','.svg')
 $description=($inputs | Sort-Object FullName | ForEach-Object {
  $stamp=if($_.Extension -in $textExtensions){(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}else{[string]$_.Length+'|'+$_.LastWriteTimeUtc.Ticks}
  $_.FullName+'|'+$stamp
 }) -join "`n"
 return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($description)))
}
$fingerprint=Get-PreviewFingerprint
$cached=if(Test-Path -LiteralPath $manifestPath){try{Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json}catch{$null}}else{$null}
$needsBuild=$Build -or !(Test-Path -LiteralPath (Join-Path $target 'index.html')) -or !$cached -or $cached.profile -ne $Profile -or $cached.fingerprint -ne $fingerprint
if(!$needsBuild){
 & node (Join-Path $PSScriptRoot 'tools/build-profile.cjs') --verify-build $target --profile $Profile | Out-Null
 $needsBuild=$LASTEXITCODE -ne 0
}
if($needsBuild){
 Write-Output ('Building local '+$Profile+' Web preview...')
 & (Join-Path $PSScriptRoot 'Build-Local.ps1') -Platform web-mobile -OutputName $outputName -Profile $Profile
 # Keep the pre-export stamp: concurrent edits must invalidate the next launch.
}else{Write-Output ('Using current '+$Profile+' Web preview.')}
@{schemaVersion=1;profile=$Profile;fingerprint=$fingerprint;buildDirectory=$target}|ConvertTo-Json|Set-Content -LiteralPath $manifestPath -Encoding utf8
$listener=Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
$url='http://127.0.0.1:'+$Port+'/'
if($listener){
 try{$served=Invoke-RestMethod -Uri ($url+'local-preview.json') -TimeoutSec 3}catch{throw ('Port '+$Port+' is occupied by another service. Choose a different -Port.')}
 if($served.profile -ne $Profile -or $served.buildDirectory -ne $target){throw ('Port '+$Port+' serves a different preview. Choose a different -Port.')}
}else{
 $temp=Join-Path $PSScriptRoot 'temp';New-Item -ItemType Directory -Force -Path $temp | Out-Null
 $server=Start-Process -FilePath 'python' -ArgumentList @(('"'+(Join-Path $PSScriptRoot 'tools/serve-web.py')+'"'),'--port',"$Port",'--directory',('"'+$target+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $temp ($outputName+'-server-out.log')) -RedirectStandardError (Join-Path $temp ($outputName+'-server-err.log'))
 for($attempt=0;$attempt -lt 20;$attempt++){
  try{$served=Invoke-RestMethod -Uri ($url+'local-preview.json') -TimeoutSec 1;break}catch{if($server.HasExited){throw 'Local preview server exited; inspect its server logs.'};Start-Sleep -Milliseconds 200}
 }
 if(!$served -or $served.profile -ne $Profile -or $served.buildDirectory -ne $target){throw 'Local preview server did not become ready.'}
 Write-Output ('Concept 2D server PID '+$server.Id)
}
Write-Output ('Local '+$Profile+' (browser preview; '+$(if($Profile -eq 'dev'){'independent dev saves; accelerated rules'}else{'normal saves and rules'})+'): '+$url+'?view=2d&player=3d')
