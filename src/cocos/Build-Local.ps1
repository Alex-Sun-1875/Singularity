param([ValidateSet('web-desktop','web-mobile','wechatgame')][string]$Platform='web-mobile',[string]$TapAppId='',[ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_-]*$')][string]$OutputName='',[string]$EditorUserData='')
$ErrorActionPreference='Stop'
$project=$PSScriptRoot
if([string]::IsNullOrWhiteSpace($OutputName)){$OutputName=$Platform}
$editor='C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe'
if(!(Test-Path -LiteralPath $editor)){throw 'Cocos Creator 3.8.8 is not installed at the configured path.'}
if($Platform -eq 'wechatgame'){
 & (Join-Path $project 'Build-TapTap.ps1') -TapAppId $TapAppId -OutputName $OutputName -EditorUserData $EditorUserData
 if($LASTEXITCODE -ne 0){throw 'TapTap release build failed.'}
 return
}
$buildLockDirectory=Join-Path $project 'temp'
New-Item -ItemType Directory -Force -Path $buildLockDirectory | Out-Null
try{$localBuildLock=[System.IO.File]::Open((Join-Path $buildLockDirectory 'taptap-build.lock'),[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)}catch{throw 'Another local or TapTap build is using this project; wait for it to finish.'}
try{
$releaseJson=& node (Join-Path $project 'tools/taptap-config.cjs') --prepare --json --mode preview
if($LASTEXITCODE -ne 0){throw 'Game release configuration validation failed.'}
$release=$releaseJson|ConvertFrom-Json
$temp=Join-Path $project 'temp'
New-Item -ItemType Directory -Force -Path $temp | Out-Null
& node (Join-Path $project 'tools/prepare-navigation-wasm.cjs') --prepare
if($LASTEXITCODE -ne 0){throw 'Navigation WASM source verification failed.'}
$config=@{platform=$Platform;name=$release.projectName;outputName=$OutputName;buildPath='project://build';debug=$false;useSplashScreen=$false;startScene='e0158e35-9bac-42ca-a8e1-16cdd7e71953';scenes=@(@{url='db://assets/FirstChapter.scene';uuid='e0158e35-9bac-42ca-a8e1-16cdd7e71953'});md5Cache=$true;mainBundleCompressionType='merge_dep';packages=@{}}
$configPath=Join-Path $temp ('build-'+$OutputName+'.json')
$config | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $configPath -Encoding utf8
# A restored library can leave release.json describing different mesh bytes.
& python (Join-Path $project 'tools/refresh-morph-build-cache.py') --project $project
if($LASTEXITCODE -ne 0){throw 'Mesh cache validation failed; rebuild stopped before packaging inconsistent geometry.'}
$arguments=@('--project',('"'+$project.Replace('\','/')+'"'),'--build',('"configPath='+$configPath.Replace('\','/')+'"'))
if($EditorUserData){
 $profilePath=[System.IO.Path]::GetFullPath($EditorUserData).Replace('\','/')
 $profileArgument=if($profilePath -match '\s'){'--user-data-dir="'+$profilePath+'"'}else{'--user-data-dir='+$profilePath}
 $arguments=@($profileArgument)+$arguments
}
$buildLog=Join-Path $temp ('build-'+$OutputName+'-out.log')
$buildErrorLog=Join-Path $temp ('build-'+$OutputName+'-err.log')
# Creator can exit 0 during engine startup failure while an old HTML remains.
# Require this invocation's build completion before advertising its output.
$completionPattern='build Task \('+[regex]::Escape($OutputName)+'\) Finished'
for($attempt=1;$attempt -le 2;$attempt++){
 $run=Start-Process -FilePath $editor -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrorLog
 Write-Output ('Cocos build PID '+$run.Id+'. Logs: '+$temp)
 $run.WaitForExit()
 $completed=($run.ExitCode -eq 36 -or $run.ExitCode -eq 0) -and (Select-String -LiteralPath $buildLog -Pattern $completionPattern -Quiet)
 if($completed){break}
 $retryable=@(Select-String -LiteralPath @($buildLog,$buildErrorLog) -Pattern 'UNKNOWN: unknown error, open.*[\\/]settings[\\/]v2[\\/]packages[\\/]engine\.json').Count -gt 0
 if($attempt -eq 1 -and $retryable){
  $suffix='.attempt1-'+(Get-Date -Format 'yyyyMMddTHHmmssfff')
  Copy-Item -LiteralPath $buildLog -Destination ($buildLog+$suffix)
  Copy-Item -LiteralPath $buildErrorLog -Destination ($buildErrorLog+$suffix)
  Write-Warning 'Creator could not open engine settings during startup; retrying once without preparing the project again.'
  Start-Sleep -Seconds 1
  continue
 }
 throw ('Cocos exited before completing '+$OutputName+' (exit '+$run.ExitCode+'). Inspect '+$buildLog)
}
& node (Join-Path $project 'tools/render-policy.cjs') --build (Join-Path $project ('build/'+$OutputName))
if($LASTEXITCODE -ne 0){throw 'Generated rendering configuration violated the performance policy.'}
& node (Join-Path $project 'tools/prepare-navigation-wasm.cjs') --build (Join-Path $project ('build/'+$OutputName))
if($LASTEXITCODE -ne 0){throw 'Navigation WASM export failed.'}
$entry=Join-Path $project ('build/'+$OutputName+'/index.html')
if($Platform -ne 'wechatgame' -and !(Test-Path -LiteralPath $entry)){throw 'Cocos exited without producing the expected HTML build.'}
if($OutputName -eq 'concept-2d' -or $OutputName.StartsWith('concept-2d-')){
 # 绘制场景默认使用3D主角；显式view/player参数仍可用于对比。
 $html=Get-Content -LiteralPath $entry -Raw
 $boot='<script>const u=new URL(location.href);let changed=false;if(!u.searchParams.has("view")){u.searchParams.set("view","2d");changed=true;}if(u.searchParams.get("view")==="2d"&&!u.searchParams.has("player")){u.searchParams.set("player","3d");changed=true;}if(changed)history.replaceState(null,"",u);</script>'
 $html=$html.Replace('<head>',('<head>'+[Environment]::NewLine+'  '+$boot))
 [System.IO.File]::WriteAllText($entry,$html,[System.Text.UTF8Encoding]::new($false))
}
$notices=Join-Path $project 'build-templates/web-desktop/THIRD_PARTY_NOTICES.txt'
& node (Join-Path $project 'tools/copy-branding.cjs') (Join-Path $project ('build/'+$OutputName))
if($LASTEXITCODE -ne 0){throw 'Web game icon export failed.'}
if(Test-Path -LiteralPath $notices){Copy-Item -LiteralPath $notices -Destination (Join-Path $project ('build/'+$OutputName+'/THIRD_PARTY_NOTICES.txt')) -Force}
Write-Output ('Built '+$Platform+' at '+(Join-Path $project ('build/'+$OutputName)))
}finally{$localBuildLock.Dispose()}
