param(
 [string]$TapAppId='',
 [switch]$AuditOnly,
 [switch]$WebPreview,
 [switch]$TestPackage,
 [switch]$GuestTest,
 [string]$PreviousVersion='',
 [string]$ArtifactDirectory='',
 [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_-]*$')][string]$OutputName='',
 [string]$EditorUserData=''
)
$ErrorActionPreference='Stop'
$project=$PSScriptRoot
if((@($AuditOnly,$WebPreview,$TestPackage)|Where-Object {$_}).Count -gt 1){throw 'Choose only one of AuditOnly, WebPreview or TestPackage.'}
if($GuestTest -and !$TestPackage){throw '-GuestTest requires -TestPackage; guest access is never enabled for release or audit builds.'}
if($AuditOnly -and ![string]::IsNullOrWhiteSpace($TapAppId)){throw '-AuditOnly must not bind a platform identity.'}
$editor='C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe'
if(!(Test-Path -LiteralPath $editor)){throw 'Cocos Creator 3.8.8 is not installed at the configured path.'}
$mode=if($WebPreview){'preview'}elseif($AuditOnly){'audit'}elseif($TestPackage){'test'}else{'release'}
$prepareArgs=@((Join-Path $project 'tools/taptap-config.cjs'),'--prepare','--json','--mode',$mode)
# Allocate one version per package invocation, before resource preparation or Creator retries.
if(!$WebPreview){$prepareArgs+=@('--version','patch')}
if($TapAppId){$prepareArgs+=@('--app-id',$TapAppId)}
if($PreviousVersion){$prepareArgs+=@('--previous-version',$PreviousVersion)}
$releaseJson=& node @prepareArgs
if($LASTEXITCODE -ne 0){throw 'TapTap release configuration validation failed.'}
$release=$releaseJson|ConvertFrom-Json
if(!$WebPreview){Write-Output ('TapTap package version auto-incremented to '+$release.version)}
if(!$AuditOnly){$TapAppId=$release.miniAppId}
if([string]::IsNullOrWhiteSpace($OutputName)){$OutputName=if($WebPreview){'taptap-preview'}elseif($AuditOnly){'taptap-audit'}elseif($GuestTest){'taptap-guest-test'}elseif($TestPackage){'taptap-test'}else{'taptap-release'}}
$platform=if($WebPreview){'web-mobile'}else{'wechatgame'}
& node (Join-Path $project 'tools/prepare-navigation-wasm.cjs') --prepare
if($LASTEXITCODE -ne 0){throw 'Navigation WASM source verification failed.'}
& python (Join-Path $project 'tools/prepare-taptap.py') --platform $platform --output-name $OutputName --mode $mode
if($LASTEXITCODE -ne 0){throw 'TapTap resource profile preparation failed.'}
& python (Join-Path $project 'tools/refresh-morph-build-cache.py') --project $project
if($LASTEXITCODE -ne 0){throw 'Mesh cache validation failed.'}
$configPath=Join-Path $project ('temp/build-'+$OutputName+'.json')
$outLog=Join-Path $project ('temp/build-'+$OutputName+'-out.log')
$errLog=Join-Path $project ('temp/build-'+$OutputName+'-err.log')
$arguments=@('--project',('"'+$project.Replace('\','/')+'"'),'--build',('"configPath='+$configPath.Replace('\','/')+'"'))
if($EditorUserData){
 $profilePath=[System.IO.Path]::GetFullPath($EditorUserData).Replace('\','/')
 $profileArgument=if($profilePath -match '\s'){'--user-data-dir="'+$profilePath+'"'}else{'--user-data-dir='+$profilePath}
 $arguments=@($profileArgument)+$arguments
}
$completion='build Task \('+[regex]::Escape($OutputName)+'\) Finished'
for($attempt=1;$attempt -le 2;$attempt++){
 $run=Start-Process -FilePath $editor -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
 Write-Output ('Cocos build PID '+$run.Id+'. Log: '+$outLog)
 $run.WaitForExit()
 $completed=($run.ExitCode -eq 36 -or $run.ExitCode -eq 0) -and (Select-String -LiteralPath $outLog -Pattern $completion -Quiet)
 if($completed){
  if(Select-String -LiteralPath @($outLog,$errLog) -Pattern 'Script .* attached to .* is missing or invalid|Missing class:' -Quiet){
   throw ('Cocos exported a scene with a missing script component. Inspect '+$outLog+' and '+$errLog)
  }
  break
 }
 # A transient Windows file-open failure can stop Creator before it starts building.
 $settingsOpenFailure='UNKNOWN: unknown error, open.*[\\/]settings[\\/]v2[\\/]packages[\\/]engine\.json'
 $retryable=@(Select-String -LiteralPath @($outLog,$errLog) -Pattern $settingsOpenFailure).Count -gt 0
 if($attempt -eq 1 -and $retryable){
  Copy-Item -LiteralPath $outLog -Destination ($outLog+'.attempt1') -Force
  Copy-Item -LiteralPath $errLog -Destination ($errLog+'.attempt1') -Force
  Write-Warning 'Creator could not open engine settings during startup; retrying once. First-attempt logs are preserved.'
  Start-Sleep -Seconds 1
  continue
 }
 throw ('Cocos build did not complete (exit '+$run.ExitCode+'). Inspect '+$outLog+' and '+$errLog)
}
$buildRoot=Join-Path $project ('build/'+$OutputName)
& node (Join-Path $project 'tools/render-policy.cjs') --build $buildRoot
if($LASTEXITCODE -ne 0){throw 'Generated rendering configuration violated the performance policy.'}
& node (Join-Path $project 'tools/prepare-navigation-wasm.cjs') --build $buildRoot
if($LASTEXITCODE -ne 0){throw 'Navigation WASM export failed.'}
$notices=Join-Path $project 'build-templates/web-desktop/THIRD_PARTY_NOTICES.txt'
if(Test-Path -LiteralPath $notices){Copy-Item -LiteralPath $notices -Destination (Join-Path $buildRoot 'THIRD_PARTY_NOTICES.txt') -Force}
if($WebPreview){
 $entry=Join-Path $buildRoot 'index.html'
 $html=Get-Content -LiteralPath $entry -Raw -Encoding UTF8
 $html=$html.Replace('<head>','<head><script>globalThis.__TAP_RELEASE__=true;</script>')
 [System.IO.File]::WriteAllText($entry,$html,[System.Text.UTF8Encoding]::new($false))
 & node (Join-Path $project 'tools/copy-branding.cjs') $buildRoot
 if($LASTEXITCODE -ne 0){throw 'Web game icon export failed.'}
 Write-Output ('Local browser verification build: '+$buildRoot)
}else{
 $packageRoot=Join-Path $project ('build/'+$OutputName+'-package')
 if([string]::IsNullOrWhiteSpace($ArtifactDirectory)){$ArtifactDirectory=Join-Path $project ('artifacts/'+$OutputName)}
 $ArtifactDirectory=[System.IO.Path]::GetFullPath($ArtifactDirectory)
 $version=$release.version
 $convertArgs=@((Join-Path $project 'tools/convert-taptap.cjs'),'--source',$buildRoot,'--target',$packageRoot,'--version',$version)
 if($AuditOnly){$convertArgs+='--audit-only'}else{$convertArgs+=@('--app-id',$TapAppId)}
 if($TestPackage){$convertArgs+='--test-package'}
 if($GuestTest){$convertArgs+='--guest-test'}
 & node @convertArgs
 if($LASTEXITCODE -ne 0){throw 'TapTap conversion failed.'}
 & python (Join-Path $project 'tools/report-taptap.py') $packageRoot --output $ArtifactDirectory
 if($LASTEXITCODE -ne 0){throw 'TapTap package verification failed.'}
 $settingsPath=Join-Path $ArtifactDirectory 'upload-settings.json'
 $settings=Get-Content -LiteralPath $settingsPath -Raw|ConvertFrom-Json
 Write-Output ''
 Write-Output ('TapTap package built: '+$release.title+' v'+$version)
 Write-Output ('MiniApp ID: '+$TapAppId)
 Write-Output ('ZIP: '+$settings.packageFilename)
 Write-Output ('Build information and SHA-256: '+(Split-Path -Parent $settings.packageFilename))
 Write-Output ('Size: '+[Math]::Round($settings.uploadZipBytes/1000000,2)+' MB')
 Write-Output ('Cocos WASM: '+$settings.wasm.engineTransport.wasmBytes+' bytes; '+$settings.wasm.engineTransport.wasmBytesInMainPackage+' bytes in main package; transport validation='+$settings.wasm.engineTransport.localValidationPassed)
 Write-Output 'Platform WASM function split: not verified; requires a compatible SDK export and console function collection.'
 Write-Output ('Upload settings: '+$settingsPath)
 if($settings.localBlockers.Count){Write-Warning ('Package generated; game integration still requires: '+($settings.localBlockers -join ' '))}
 if($TestPackage){Write-Output 'Upload-test package only. Complete the recorded integration and platform/device checks before release.'}
}
